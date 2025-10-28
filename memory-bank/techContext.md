# Tech Context

**Programming Language:** Python (version >= 3.8)

**Package Management:**
- `uv`: Primary package installer and resolver for Python dependencies.
- `pip`: Used for initial installation of `uv` if not installed via `curl` script.
- `requirements.txt`: A file listing all the necessary Python libraries for the project.

**Version Control & Deployment:**
- `git`: For managing source code, pushing local changes to a remote repository (e.g., GitHub), and cloning/pulling updates on the VPS. Feature branches are used for new development.

**Data Storage: Partitioned Parquet Datalake**
- The entire data pipeline is built around partitioned Parquet datasets, creating a simple but powerful file-based datalake.
- **Raw Zone:** `markets_partitioned/` and `goldsky/orderFilled/` store raw data partitioned by date.
- **Processed Zone:** `processed/trades/` stores the final, enriched output, also as a partitioned dataset.
- This approach was chosen for high performance and memory efficiency on a resource-constrained VPS.
- The pipeline scripts are designed to be resilient to schema inconsistencies from the source APIs (e.g., missing columns, incorrect data types), which proved to be a major challenge.
- **Schema Drift Handling:** During development, significant schema drift was identified in the `goldsky/orderFilled` raw data. Specifically, the `timestamp` column had inconsistent data types (`String` vs. `Int64`) across historical files. This discovery necessitated a shift from using a single `polars.scan_parquet` operation (which fails on type mismatch) to a more robust, iterative approach. The pipeline now reads each parquet file individually, casts columns to a consistent schema on-the-fly, and then aggregates the results. This defensive pattern is critical for ensuring the pipeline's long-term stability.

**Data Transfer:**
- `rsync`: For efficient synchronization of processed data files from the VPS to the local machine.

**VPS Access & Management:**
- `ssh`: Secure shell for remote access to the VPS.
- `tmux` (or `screen`): Terminal multiplexer on the VPS to run long-duration processes in the background, allowing detachment and re-attachment.

**Key Python Libraries (from `requirements.txt`):**
- `polars`
- `pandas`
- `matplotlib`
- `jupyter`
- `requests`

**Operating System:**
- Local: macOS (darwin)
- VPS: Assumed to be a Linux distribution (e.g., Ubuntu, Debian) for `apt` commands.