import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from flatten_json import flatten
from datetime import datetime, timezone
import time
import polars as pl
import pyarrow.parquet as pq
import pyarrow.dataset as ds

# Global runtime timestamp - set once when program starts
RUNTIME_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Columns to save
COLUMNS_TO_SAVE = ['timestamp', 'maker', 'makerAssetId', 'makerAmountFilled', 'taker', 'takerAssetId', 'takerAmountFilled', 'transactionHash']

if not os.path.isdir('goldsky'):
    os.mkdir('goldsky')

def get_latest_timestamp():
    """Get the latest timestamp by scanning only the most recent partition (tail scan)."""
    cache_dir = 'goldsky/orderFilled'
    if not os.path.isdir(cache_dir):
        print("No existing data found, starting from timestamp 0")
        return 0

    try:
        # Step 1: Find latest year
        years = sorted([d for d in os.listdir(cache_dir) if d.startswith('year=')], reverse=True)
        if not years:
            print("No year partitions found. Starting from timestamp 0.")
            return 0
        latest_year_dir = os.path.join(cache_dir, years[0])

        # Step 2: Find latest month in that year
        months = sorted([d for d in os.listdir(latest_year_dir) if d.startswith('month=')],
                        key=lambda x: int(x.split('=')[1]), reverse=True)
        if not months:
            print("No month partitions found. Starting from timestamp 0.")
            return 0
        latest_month_dir = os.path.join(latest_year_dir, months[0])

        # Step 3: Find latest day in that month
        days = sorted([d for d in os.listdir(latest_month_dir) if d.startswith('day=')],
                      key=lambda x: int(x.split('=')[1]), reverse=True)
        if not days:
            print("No day partitions found. Starting from timestamp 0.")
            return 0
        latest_day_dir = os.path.join(latest_month_dir, days[0])

        # Step 4: Scan only the parquet files in the latest day partition
        import glob
        files = glob.glob(os.path.join(latest_day_dir, '*.parquet'))
        if not files:
            print("No parquet files in latest partition. Starting from timestamp 0.")
            return 0

        max_ts = (
            pl.scan_parquet(files)
            .select(pl.col('timestamp').cast(pl.Int64).max())
            .collect()
            .item()
        )

        if max_ts:
            readable = datetime.fromtimestamp(int(max_ts), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f'Resuming from timestamp {max_ts} ({readable})')
            return int(max_ts)
        
        print("No timestamps found. Starting from timestamp 0.")
        return 0
    except Exception as e:
        print(f"Error in tail scan: {e}. Starting from timestamp 0.")
        return 0

def scrape(at_once=1000):
    QUERY_URL = "https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn"
    print(f"Query URL: {QUERY_URL}")
    print(f"Runtime timestamp: {RUNTIME_TIMESTAMP}")

    last_value = get_latest_timestamp()
    count = 0
    total_records = 0

    print(f"\nStarting scrape for orderFilledEvents")

    output_dir = 'goldsky/orderFilled'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Output directory: {output_dir}")
    print(f"Saving columns: {COLUMNS_TO_SAVE}")

    while True:
        q_string = '''query MyQuery {
                        orderFilledEvents(orderBy: timestamp
                                             first: ''' + str(at_once) + '''
                                             where: {timestamp_gt: "''' + str(last_value) + '''"}) {
                            fee
                            id
                            maker
                            makerAmountFilled
                            makerAssetId
                            orderHash
                            taker
                            takerAmountFilled
                            takerAssetId
                            timestamp
                            transactionHash
                        }
                    }
                '''

        query = gql(q_string)
        transport = RequestsHTTPTransport(url=QUERY_URL, verify=True, retries=3)
        client = Client(transport=transport)

        try:
            res = client.execute(query)
        except Exception as e:
            print(f"Query error: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            continue

        if not res['orderFilledEvents'] or len(res['orderFilledEvents']) == 0:
            print(f"No more data for orderFilledEvents")
            break

        df = pl.DataFrame([flatten(x) for x in res['orderFilledEvents']])

        if df.height == 0:
            break
            
        df = df.sort('timestamp')
        last_value = df.select(pl.col('timestamp')).tail(1).item()

        readable_time = datetime.fromtimestamp(int(last_value), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"Batch {count + 1}: Last timestamp {last_value} ({readable_time}), Records: {len(df)}")

        count += 1
        total_records += len(df)

        df = df.unique()

        df_to_save = df.select(COLUMNS_TO_SAVE)
        
        df_to_save = df_to_save.with_columns([
            pl.from_epoch(pl.col('timestamp'), time_unit='s').dt.year().alias('year'),
            pl.from_epoch(pl.col('timestamp'), time_unit='s').dt.month().alias('month'),
            pl.from_epoch(pl.col('timestamp'), time_unit='s').dt.day().alias('day'),
        ])
        
        table = df_to_save.to_arrow()

        pq.write_to_dataset(
            table,
            root_path=output_dir,
            partition_cols=['year', 'month', 'day'],
            existing_data_behavior='overwrite_or_ignore'
        )

        if len(df) < at_once:
            break

    print(f"Finished scraping orderFilledEvents")
    print(f"Total new records: {total_records}")

def update_goldsky():
    """Run scraping for orderFilledEvents"""
    print(f"\n{'='*50}")
    print(f"Starting to scrape orderFilledEvents")
    print(f"Runtime: {RUNTIME_TIMESTAMP}")
    print(f"{'='*50}")
    try:
        scrape()
        print(f"Successfully completed orderFilledEvents")
    except Exception as e:
        print(f"Error scraping orderFilledEvents: {str(e)}")
