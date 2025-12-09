# Active Context

### Current Status
- **Restructure Complete**: Project separated into `fetcher/`, `analysis/`, and `shared/`.
- **Imports Fixed**: All scripts and notebooks updated to use `shared.poly_utils` and correct paths.
- **Verification**: `update_all.py` verified on fetcher. Imports are valid.
- **Next Step**: User to run `start-analysis.sh` to switch to Analyzer and begin data analysis.

### Recent Changes:
- **Repository Split:** Separated the project into two repositories:
    - `poly-data`: Public infrastructure and fetcher code.
    - `poly-strategies`: Private analysis notebooks and automation scripts.
- **Migration:** Moved all analysis files and `start/stop-analysis.sh` scripts to the new private repo and cleaned them from `poly-data`.
- **Cleanup:** Removed `connect_jupyter.sh` as the user has switched to VS Code Remote for development.
- **Automation Scripts:** Created `start-analysis.sh` and `stop-analysis.sh` (now in `poly-strategies`) to fully automate the dual-server lifecycle with dual-repo support.
    - **Auto-Update:** `start-analysis.sh` now pulls the latest code from GitHub on boot.
    - **Safety Check:** `stop-analysis.sh` aborts if there are unsaved Git changes on the analyzer.
- **Tmux Persistence:** Configured the `poly-fetcher` server with `tmux-resurrect` and `tmux-continuum` to automatically save and restore sessions across reboots.

**Next Steps:**
1.  **Optimize Pipeline Startup:** Implement the "Tail Scanning" logic (scanning only the latest year/month partitions) to reduce the `update_all.py` startup time from ~10 minutes to seconds.
2.  **Verify Workflow:** Run `./start-analysis.sh` to spin up the environment, perform a basic check, and then run `./stop-analysis.sh` to confirm the safety checks and teardown process work as expected.
3.  **Begin Data Analysis:** Once verified, proceed with the original goal of exploring the processed trade data in the Jupyter notebooks.

**Important Patterns and Preferences:**
- **Develop Local, Run Remote:** The workflow is strictly: edit code locally -> push to GitHub -> start analyzer (auto-pulls) -> run analysis. Direct editing on the analyzer is permitted but requires manual committing before shutdown.
- **Memory Efficiency:** Despite having a powerful server, continue to use memory-efficient coding practices (`polars` lazy scanning) to handle the growing dataset.
