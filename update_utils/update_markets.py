import requests
import json
import os
from typing import List, Dict
import polars as pl
import pyarrow.parquet as pq

def update_markets(base_dir: str = "markets_partitioned", batch_size: int = 500):
    """
    Fetch markets ordered by creation date and save to a partitioned parquet dataset.
    Automatically resumes from the last fetched market.

    Args:
        base_dir: The base directory to store the partitioned parquet dataset.
        batch_size: Number of markets to fetch per request.
    """
    base_url = "https://gamma-api.polymarket.com/markets"
    
    os.makedirs(base_dir, exist_ok=True)

    latest_created_at = None
    if os.path.exists(base_dir) and any(os.scandir(base_dir)):
        try:
            latest_created_at = pl.scan_parquet(f"{base_dir}/**/*.parquet") \
                                    .select(pl.max("createdAt")) \
                                    .collect() \
                                    .item()
            if latest_created_at:
                print(f"Found existing data. Resuming from after: {latest_created_at}")
        except Exception as e:
            print(f"Could not read existing parquet data to find latest timestamp: {e}")

    total_saved = 0
    current_offset = 0
    found_overlap = False

    while True:
        print(f"Fetching batch of newest markets (offset: {current_offset})...")
        
        try:
            params = {
                'order': 'createdAt',
                'ascending': 'false',  # Fetch newest first
                'limit': batch_size,
                'offset': current_offset,
            }

            response = requests.get(base_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"API error {response.status_code}: {response.text}")
                import time
                time.sleep(5)
                continue
            
            markets_batch_raw = response.json()
            num_received = len(markets_batch_raw)

            if not markets_batch_raw:
                print("No more markets found on API. Completed!")
                break

            new_markets_to_process = []
            for market in markets_batch_raw:
                if latest_created_at and market['createdAt'] <= latest_created_at:
                    found_overlap = True
                    break  # Stop processing this batch, we've found markets we already have
                new_markets_to_process.append(market)

            if not new_markets_to_process:
                if found_overlap or num_received < batch_size:
                    print("All new markets have been processed.")
                    break
                else:
                    # This case is unlikely but possible if a whole page is somehow bad data
                    current_offset += num_received
                    continue

            # --- Start Processing the new markets from this batch ---
            df = pl.from_dicts(new_markets_to_process)
            expressions = []

            # The 'outcomes' and 'clobTokenIds' columns are JSON strings, so we parse them first.
            if 'outcomes' in df.columns:
                df = df.with_columns(pl.col('outcomes').str.json_decode(dtype=pl.List(pl.Utf8)).alias('outcomes_parsed'))
                expressions.extend([
                    pl.col("outcomes_parsed").list.get(0).alias("answer1"),
                    pl.col("outcomes_parsed").list.get(1).alias("answer2"),
                ])
            else:
                expressions.extend([pl.lit(None, dtype=pl.Utf8).alias("answer1"), pl.lit(None, dtype=pl.Utf8).alias("answer2")])

            if 'clobTokenIds' in df.columns:
                df = df.with_columns(pl.col('clobTokenIds').str.json_decode(dtype=pl.List(pl.Utf8)).alias('clobTokenIds_parsed'))
                expressions.extend([
                    pl.col("clobTokenIds_parsed").list.get(0).alias("token1"),
                    pl.col("clobTokenIds_parsed").list.get(1).alias("token2"),
                ])
            else:
                expressions.extend([pl.lit(None, dtype=pl.Utf8).alias("token1"), pl.lit(None, dtype=pl.Utf8).alias("token2")])

            if 'negRiskAugmented' in df.columns and 'negRiskOther' in df.columns:
                expressions.append((pl.col('negRiskAugmented') | pl.col('negRiskOther')).alias('neg_risk'))
            elif 'negRiskAugmented' in df.columns:
                expressions.append(pl.col('negRiskAugmented').alias('neg_risk'))
            elif 'negRiskOther' in df.columns:
                expressions.append(pl.col('negRiskOther').alias('neg_risk'))
            else:
                expressions.append(pl.lit(False).alias('neg_risk'))

            if 'question' in df.columns and 'title' in df.columns:
                expressions.append(pl.coalesce(pl.col('question'), pl.col('title')).alias('question_text'))
            elif 'question' in df.columns:
                expressions.append(pl.col('question').alias('question_text'))
            elif 'title' in df.columns:
                expressions.append(pl.col('title').alias('question_text'))
            else:
                expressions.append(pl.lit('').alias('question_text'))

            if 'events' in df.columns and df["events"].dtype == pl.List:
                expressions.append(pl.col('events').list.get(0).struct.field('ticker').alias('ticker'))
            else:
                expressions.append(pl.lit('').alias('ticker'))

            df = df.with_columns(expressions)
            
            df = df.with_columns([
                pl.col("createdAt").str.to_datetime(time_zone="UTC").dt.year().alias("year"),
                pl.col("createdAt").str.to_datetime(time_zone="UTC").dt.month().alias("month"),
            ])

            final_columns_ideal = [
                'createdAt', 'id', 'question_text', 'answer1', 'answer2', 'neg_risk',
                'slug', 'token1', 'token2', 'conditionId', 'volume', 'ticker', 'closedTime',
                'year', 'month'
            ]
            
            columns_to_select = [col for col in final_columns_ideal if col in df.columns]
            df = df.select(columns_to_select)
            
            pq.write_to_dataset(
                table=df.to_arrow(),
                root_path=base_dir,
                partition_cols=["year", "month"],
                existing_data_behavior='overwrite_or_ignore'
            )

            total_saved += len(df)
            print(f"Saved {len(df)} new markets. Total saved in this run: {total_saved}")
            # --- End Processing ---

            if found_overlap or num_received < batch_size:
                print("Finished fetching all new markets.")
                break
            
            current_offset += num_received

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            import time
            time.sleep(5)
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
            import time
            time.sleep(3)
            continue
        
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            import time
            time.sleep(5)
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
            import time
            time.sleep(3)
            continue

    print(f"\nCompleted! Saved a total of {total_saved} new markets.")

if __name__ == "__main__":
    update_markets(batch_size=500)
