import polars as pl

def inspect_file_dtype(file_path):
    """Reads a parquet file and prints the dtype of the timestamp column."""
    if not file_path:
        print("File path is empty.")
        return

    print(f"\nInspecting file: {file_path}")
    try:
        df = pl.read_parquet(file_path)
        ts_dtype = df['timestamp'].dtype
        print(f"  -> Timestamp dtype: {ts_dtype}")
    except Exception as e:
        print(f"  -> Failed to read or process the file: {e}")

if __name__ == "__main__":
    # A file from October that we know has string timestamps
    october_file = 'goldsky/orderFilled/year=2025/month=10/day=30/3fdd0fdfd995469eba866058d73f6759-0.parquet'
    
    # A file from September that is causing the new error
    september_file = 'goldsky/orderFilled/year=2025/month=9/day=26/9f84a90099a44e518576b00aa15d6cd7-0.parquet'

    inspect_file_dtype(october_file)
    inspect_file_dtype(september_file)