# Active Context

### Current Status
- **Pipeline Optimized**: Implemented "Tail Scanning" in `get_latest_timestamp()`. Startup reduced from 10+ minutes to ~2 seconds.
- **Infrastructure Ready**: Dual-server architecture fully operational.
- **Next Step**: Begin data analysis in Jupyter notebooks.

### Related Repo: poly-strategies
- **Contains:** Analysis notebooks, trading strategies, `start/stop-analysis.sh` scripts
- **Memory bank:** `/root/poly-strategies/memory-bank/`
- **Deployed on:** `poly-analyzer` (on-demand server)
- **Handoff note:** Pipeline optimization complete. Ready for analysis workflow verification.

### Recent Changes:
- **Safety Mechanism:** Updated `run_update.sh` to create and manage an external lock file (`/tmp/poly-fetcher.lock`). This signals to `start-analysis.sh` that a fetch is in progress, preventing accidental server shutdown.
- **Structural Refactor:** Flattened the project structure. Moved files from `fetcher/` and `shared/poly_utils` back to the project root. The `poly-data` repo is now a standard, single-level Python project.
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
1.  ~~**Optimize Pipeline Startup:**~~ ✅ Done. Tail scanning implemented.
2.  **Verify Workflow:** Run `./start-analysis.sh` to spin up the environment, perform a basic check, and then run `./stop-analysis.sh` to confirm the safety checks and teardown process work as expected.
3.  **Begin Data Analysis:** Proceed with the original goal of exploring the processed trade data in the Jupyter notebooks.

**Important Patterns and Preferences:**
- **Develop Local, Run Remote:** The workflow is strictly: edit code locally -> push to GitHub -> start analyzer (auto-pulls) -> run analysis. Direct editing on the analyzer is permitted but requires manual committing before shutdown.
- **Memory Efficiency:** Despite having a powerful server, continue to use memory-efficient coding practices (`polars` lazy scanning) to handle the growing dataset.
