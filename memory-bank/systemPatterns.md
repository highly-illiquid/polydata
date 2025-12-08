# System Patterns

**Architecture: Dual-Server with Detachable Volume**

This architecture is designed for cost-efficiency and separation of concerns. It uses two servers with distinct roles and a shared, detachable storage volume.

- **Fetcher Server (`poly-fetcher`):** A small, cheap, and permanent VPS that runs 24/7. Its sole responsibility is to run the data collection pipeline (`update_all.py`) via a cron job.

- **Analyzer Server (`poly-analyzer`):** A large, powerful, on-demand VPS used for heavy data analysis. This server does not run 24/7. To save costs, it is created from a pre-configured snapshot when needed and deleted immediately after analysis is complete.

- **Storage (`poly-data-volume`):** A persistent Hetzner Cloud Volume that stores all project data. This volume is moved between the two servers.

### 3. Folder Structure (Refactored)
To ensure separation of concerns and prevent cross-contamination:
- **`fetcher/`**: Scripts running on the `poly-fetcher` VPS (e.g., `update_all.py`, `run_update.sh`). Optimized for low memory.
- **`analysis/`**: Jupyter notebooks running on the `poly-analyzer` VPS. Heavy processing allowed.
- **`shared/`**: Common utilities (`poly_utils/`) used by both.
- **`processed/`**: Data output directory (Parquet files).
- **`markets_partitioned/`**: Market metadata (Parquet files).

### 4. Agent "Memory" Persistence

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