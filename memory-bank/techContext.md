# Tech Context

**Programming Language:** Python (version >= 3.8)

**Package Management:**
- `uv`: Primary package installer and resolver for Python dependencies.
- `pip`: Used for initial installation of `uv` if not installed via `curl` script.
- `requirements.txt`: A file listing all the necessary Python libraries for the project.

**Version Control & Deployment:**
- `git`: For managing source code. All new work and bug fixes are done on feature branches before being merged into `master`.

**Data Storage: Partitioned Parquet on a Cloud Volume**
- The entire data pipeline is built around partitioned Parquet datasets.
- **Physical Storage:** All data now resides on a Hetzner Cloud Volume, which is mounted on the VPS at `/mnt/HC_Volume_103996558/`. This separates data storage from the compute server.
- **Data Access:** The project accesses the data via symbolic links. The `markets_partitioned`, `goldsky/orderFilled`, and `processed` directories within the project folder are symlinks pointing to the corresponding directories on the mounted Volume. This allows the code to operate without needing to know the physical path of the volume.
- **Raw Zone:** Data is stored in `markets_partitioned/` and `goldsky/orderFilled/`.
- **Processed Zone:** `processed/trades/` stores the final, enriched output.

**Key Data Pipeline Patterns & Learnings:**
- **Schema Drift:** The `goldsky/orderFilled` raw data has significant schema drift. The `timestamp` column has inconsistent data types (`String` vs. `Int64`) across historical files. Any function that processes this data must be robust to this inconsistency.
- **Inefficient Startup:** The current, functional version of `get_latest_timestamp` works by scanning all historical files. This is known to be slow and causes a significant delay (10+ minutes) on script startup.
    - **Optimization Plan:** Implement "Tail Scanning". Instead of reading the whole dataset, the script will list the `year=YYYY` and `month=MM` directories to find the latest partition, and then `polars` will scan only that specific subset to find the last timestamp.

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



**Analyzer Server & Automation Workflow:**



- **On-Demand Creation:** The `poly-analyzer` server is not persistent. It is created on-demand from a snapshot (e.g., `poly-analyzer-base-v1`) for cost-efficiency.



- **Pre-configured Snapshot:** The snapshot image is pre-configured with a custom environment, including tools like `eza`, `oh-my-posh`, `zoxide`, `nvm`, and the `gemini-cli`.



- **Python Environment:** The analyzer uses a Python virtual environment located at `/root/poly-data/.venv`. This must be activated (`source .venv/bin/activate`) in a new session before running analysis scripts.



- **Automation Tooling:** The entire start/stop workflow is automated via shell scripts (`start-analysis.sh`, `stop-analysis.sh`) that wrap the `hcloud` CLI.



    - **Auto-Update:** `start-analysis.sh` automatically pulls the latest code from GitHub upon creating the server.



    - **Safety Check:** `stop-analysis.sh` checks for uncommitted changes before deleting the server to prevent data loss.



- **Fetcher Persistence:** The persistent `poly-fetcher` server uses `tmux` with the `tmux-resurrect` and `tmux-continuum` plugins to automatically save and restore terminal sessions across the reboots required by the volume switching process.