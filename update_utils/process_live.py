import warnings
warnings.filterwarnings('ignore')

import sys
import os
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import polars as pl
from poly_utils.utils import get_markets, update_missing_tokens

def get_processed_df(df, markets_long):

    # 2) Identify the non-USDC asset for each trade (the one that isn't 0)
    df = df.with_columns(
        pl.when(pl.col("makerAssetId") != "0")
        .then(pl.col("makerAssetId"))
        .otherwise(pl.col("takerAssetId"))
        .alias("nonusdc_asset_id")
    )

    # 3) Join once on that non-USDC asset to recover the market + side ("token1" or "token2")
    df = df.join(
        markets_long,
        left_on="nonusdc_asset_id",
        right_on="asset_id",
        how="left",
    )

    # 4) label columns and keep market_id
    df = df.with_columns([
        pl.when(pl.col("makerAssetId") == "0").then(pl.lit("USDC")).otherwise(pl.col("side")).alias("makerAsset"),
        pl.when(pl.col("takerAssetId") == "0").then(pl.lit("USDC")).otherwise(pl.col("side")).alias("takerAsset"),
        pl.col("market_id"),
    ])

    df = df.select(['timestamp', 'market_id', 'maker', 'makerAsset', 'makerAmountFilled', 'taker', 'takerAsset', 'takerAmountFilled', 'transactionHash'])

    df = df.with_columns([
        (pl.col("makerAmountFilled") / 10**6).alias("makerAmountFilled"),
        (pl.col("takerAmountFilled") / 10**6).alias("takerAmountFilled"),
    ])

    df = df.with_columns([
        pl.when(pl.col("takerAsset") == "USDC")
        .then(pl.lit("BUY"))
        .otherwise(pl.lit("SELL"))
        .alias("taker_direction"),

        # reverse of taker_direction
        pl.when(pl.col("takerAsset") == "USDC")
        .then(pl.lit("SELL"))
        .otherwise(pl.lit("BUY"))
        .alias("maker_direction"),
    ])

    df = df.with_columns([
        pl.when(pl.col("makerAsset") != "USDC")
        .then(pl.col("makerAsset"))
        .otherwise(pl.col("takerAsset"))
        .alias("nonusdc_side"),

        pl.when(pl.col("takerAsset") == "USDC")
        .then(pl.col("takerAmountFilled"))
        .otherwise(pl.col("makerAmountFilled"))
        .alias("usd_amount"),

        pl.when(pl.col("takerAsset") != "USDC")
        .then(pl.col("takerAmountFilled"))
        .otherwise(pl.col("makerAmountFilled"))
        .alias("token_amount"),

        pl.when(pl.col("takerAsset") == "USDC")
        .then(pl.col("takerAmountFilled") / pl.col("makerAmountFilled"))
        .otherwise(pl.col("makerAmountFilled") / pl.col("takerAmountFilled"))
        .cast(pl.Float64)
        .alias("price")
    ])

    df = df.select(['timestamp', 'market_id', 'maker', 'taker', 'nonusdc_side', 'maker_direction', 'taker_direction', 'price', 'usd_amount', 'token_amount', 'transactionHash'])
    return df

def process_live():
    processed_dir = os.path.abspath('processed/trades')
    print("=" * 60)
    print("🔄 Processing Live Trades")
    print("=" * 60)

    last_processed_timestamp = 0
    if os.path.exists(processed_dir):
        print(f"✓ Found existing processed directory: {processed_dir}")
        try:
            # Scan for the max timestamp in the *output* directory
            latest_output_ts = pl.scan_parquet(f"{processed_dir}/**/*.parquet").select(pl.max('timestamp')).collect().item()
            if latest_output_ts:
                # Convert polars datetime to python datetime if necessary
                if isinstance(latest_output_ts, datetime.datetime):
                    last_processed_timestamp = latest_output_ts
                else:
                    # Assuming it's already a suitable datetime object or parsable string
                    last_processed_timestamp = pl.from_epoch(latest_output_ts, time_unit='us')

                print(f"📍 Resuming from after: {last_processed_timestamp}")
        except Exception as e:
            print(f"Could not read last processed timestamp, processing from beginning: {e}")

    import glob
    print(f"\n📂 Reading: goldsky/orderFilled")
    all_files = sorted(glob.glob("goldsky/orderFilled/**/*.parquet", recursive=True))

    if not all_files:
        print("No orderFilled parquet files found. Exiting.")
        return

    FILE_CHUNK_SIZE = 10  # Process 10 files at a time to keep memory low
    total_processed_rows = 0

    print("\n🚀 Loading markets data once...")
    markets_df = get_markets()
    markets_df = markets_df.rename({'id': 'market_id'})
    markets_long = (
        markets_df
        .select(["market_id", "token1", "token2"])
        .melt(id_vars="market_id", value_vars=["token1", "token2"],
            variable_name="side", value_name="asset_id")
    )
    print("✅ Markets data loaded and prepared.")

    for i in range(0, len(all_files), FILE_CHUNK_SIZE):
        file_chunk = all_files[i:i + FILE_CHUNK_SIZE]
        print(f"\n--- Processing file chunk {i//FILE_CHUNK_SIZE + 1} of {len(all_files)//FILE_CHUNK_SIZE + 1} ---")

        lazy_frames = []
        for file_path in file_chunk:
            try:
                lf = pl.scan_parquet(file_path).with_columns([
                    pl.col("timestamp").cast(pl.Int64),
                    pl.col("takerAssetId").cast(pl.Utf8),
                    pl.col("makerAssetId").cast(pl.Utf8),
                    pl.col("makerAmountFilled").cast(pl.Int64),
                    pl.col("takerAmountFilled").cast(pl.Int64),
                ])
                lazy_frames.append(lf)
            except Exception as e:
                print(f"Could not process file {file_path}: {e}")
                continue

        if not lazy_frames:
            continue

        chunk_df_lazy = pl.concat(lazy_frames)
        
        # Convert timestamp and filter
        chunk_df_lazy = chunk_df_lazy.with_columns(
            pl.from_epoch(pl.col('timestamp'), time_unit='s').alias('timestamp')
        )
        if last_processed_timestamp:
            chunk_df_lazy = chunk_df_lazy.filter(pl.col('timestamp') > last_processed_timestamp)

        # Collect only the small, filtered chunk
        collected_chunk = chunk_df_lazy.collect()
        if collected_chunk.is_empty():
            print("No new rows in this chunk.")
            continue
            
        print(f"📦 Processing batch of {len(collected_chunk):,} rows...")
        
        # Get the fully processed dataframe
        new_df = get_processed_df(collected_chunk, markets_long)
        if new_df.is_empty():
            print("No processable trades in this chunk after joining with markets.")
            continue

        # Add year/month for partitioning
        new_df = new_df.with_columns([
            pl.col('timestamp').dt.year().alias('year'),
            pl.col('timestamp').dt.month().alias('month'),
        ])
        
        # Manually partition and write the chunk to avoid pyarrow issues
        for (year, month), group in new_df.group_by(['year', 'month'], maintain_order=True):
            partition_dir = os.path.join(processed_dir, f"year={year}", f"month={month}")
            os.makedirs(partition_dir, exist_ok=True)
            file_path = os.path.join(partition_dir, f"trades_chunk_{i//FILE_CHUNK_SIZE}.parquet")
            group.write_parquet(file_path)

        print(f"✓ Appended {len(new_df):,} rows")
        total_processed_rows += len(new_df)

    print(f"\n✅ Total processed: {total_processed_rows:,} new rows")
    print("=" * 60)
    print("✅ Processing complete!")
    print("=" * 60)

if __name__ == "__main__":
    process_live()

