import polars as pl

# Define paths
orders_filled_path = "goldsky/orderFilled/"
processed_trades_path = "processed/trades/"

# Suppress warnings for demonstration
import warnings
warnings.filterwarnings("ignore")

print("--- Last 5 rows of ordersFilled ---")
try:
    # scan_parquet will automatically discover partitions
    df_orders = pl.scan_parquet(orders_filled_path).tail(5).collect()
    print(df_orders)
except Exception as e:
    print(f"Could not read {orders_filled_path}: {e}")


print("\n--- Last 5 rows of processed/trades ---")
try:
    # scan_parquet will automatically discover partitions
    df_trades = pl.scan_parquet(processed_trades_path).tail(5).collect()
    print(df_trades)
except Exception as e:
    print(f"Could not read {processed_trades_path}: {e}")
