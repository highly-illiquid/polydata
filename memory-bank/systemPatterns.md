# System Patterns

**Architecture: Dual-Server with Detachable Volume**

This architecture is designed for cost-efficiency and separation of concerns. It uses two servers with distinct roles and a shared, detachable storage volume.

- **Fetcher Server (`poly-fetcher`):** A small, cheap, and permanent VPS that runs 24/7. Its sole responsibility is to run the data collection pipeline (`update_all.py`) via a cron job.

- **Analyzer Server (`poly-analyzer`):** A large, powerful, on-demand VPS used for heavy data analysis. This server does not run 24/7. To save costs, it is created from a pre-configured snapshot when needed and deleted immediately after analysis is complete.

- **Storage (`poly-data-volume`):** A persistent Hetzner Cloud Volume that stores all project data. This volume is moved between the two servers.

### 3. Folder Structure (Simplified)
The project follows a standard, flat Python structure:
- **`update_all.py`**: The main entry point for the data pipeline.
- **`run_update.sh`**: The wrapper script for cron execution.
- **`poly_utils/`**: Core utility library (formerly shared).
- **`update_utils/`**: Modules for specific update tasks (markets, goldsky, processing).
- **`processed/`**: Data output directory (Parquet files).
- **`markets_partitioned/`**: Market metadata (Parquet files).

### 4. Repository Structure (Split Model)
The project is split into two Git repositories to separate public infrastructure from private trading strategies ("Alpha").

- **Repo 1: `poly-data` (Public/Shared Infrastructure)**
    - Contains: The data pipeline code (`update_all.py`, `poly_utils`, etc.).
    - Role: The "engine" that collects data.
    - Layout: Flat, standard Python project.

- **Repo 2: `poly-strategies` (Private Analysis)**
    - Contains: Jupyter notebooks, backtests, specific research, and automation scripts (`start-analysis.sh`, `stop-analysis.sh`).
    - Role: The private lab for analysis and strategy development.
    - Deployment: Deployed ONLY on `poly-analyzer`.

### 5. Agent "Memory" Persistence

**Automated Workflow:**

The switching process is handled by automation scripts (`start-analysis.sh`, `stop-analysis.sh`) run from the user's local machine using the `hcloud` CLI.

1.  **`start-analysis.sh`:**
    *   Powers down the `poly-fetcher` server (for safe volume detachment).
    *   Detaches the `poly-data-volume`.
    *   Creates a new `poly-analyzer` server from the pre-configured snapshot.
    *   Attaches the `poly-data-volume` to the new analyzer.
    *   Mounts the volume inside the analyzer's filesystem.
    *   **Auto-Update:** Automatically runs `git pull` to fetch the latest code from GitHub, ensuring the environment is always up-to-date.
    *   Outputs the IP address and SSH command.

2.  **`stop-analysis.sh`:**
    *   **Safety Check:** Checks for uncommitted Git changes on the analyzer. If found, aborts the shutdown to prevent data loss.
    *   Deletes the `poly-analyzer` server (stopping costs).
    *   Attaches the `poly-data-volume` back to the `poly-fetcher` server.
    *   Powers the `poly-fetcher` back on to resume data collection.

**Key Components:**
- **`poly-fetcher`:** A permanent, low-cost Hetzner Cloud VPS.
- **`poly-analyzer`:** An ephemeral, high-cost Hetzner Cloud VPS created from a snapshot.
- **`poly-data-volume`:** A network-attached persistent storage disk.
- **`hcloud` CLI:** The command-line tool used to automate the infrastructure management.