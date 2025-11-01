# Tech Context

**Programming Language:** Python (version >= 3.8)

**Package Management:**
- `uv`: Primary package installer and resolver for Python dependencies.
- `pip`: Used for initial installation of `uv` if not installed via `curl` script.
- `requirements.txt`: A file listing all the necessary Python libraries for the project.

**Version Control & Deployment:**
- `git`: For managing source code. All new work and bug fixes are done on feature branches before being merged into `master`.

**Data Storage: Partitioned Parquet Datalake**
- The entire data pipeline is built around partitioned Parquet datasets, creating a simple but powerful file-based datalake.
- **Raw Zone:** `markets_partitioned/` and `goldsky/orderFilled/` store raw data partitioned by date.
- **Processed Zone:** `processed/trades/` stores the final, enriched output, also as a partitioned dataset.
- This approach was chosen for high performance and memory efficiency on a resource-constrained VPS.

**Key Data Pipeline Patterns & Learnings:**
- **Schema Drift:** The `goldsky/orderFilled` raw data has significant schema drift. The `timestamp` column has inconsistent data types (`String` vs. `Int64`) across historical files. Any function that processes this data must be robust to this inconsistency.
- **Inefficient Startup:** The current, functional version of `get_latest_timestamp` works by scanning all historical files. This is known to be slow and can cause a significant delay on script startup.

**Cron Job Execution:**
- A wrapper script (`run_update.sh`) is used to execute the main python script.
- **Critical:** The wrapper script **must** `cd` into the project directory (`/root/poly-data`) before execution to ensure all relative paths are resolved correctly.
- A lock file (`update_all.lock`) is used within the wrapper to prevent multiple instances of the job from running simultaneously.

**Troubleshooting:**
- **CRITICAL - Stale Python Cache:** When debugging issues where the code's behavior does not match the source file, the **first step** should be to suspect and delete stale `.pyc` files. This is done by removing all `__pycache__` directories (`find . -type d -name "__pycache__" -exec rm -r {} +`). This was the root cause of a major, multi-hour debugging session where reverted code was not actually being executed.

**Key Python Libraries (from `requirements.txt`):**
- `polars`
- `pandas`
- `matplotlib`
- `jupyter`
- `requests`