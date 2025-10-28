# Active Context

**Current Focus:** Git repository restoration (in-place, preserving data lake), then debugging Jupyter Lab kernel crash during PnL analysis.

**Recent Changes:**
- **Git Repository Lost:** The local Git repository (the `.git` directory) was lost during a migration, necessitating a full restoration of history.
- **`replace` Tool Unreliability:** The `replace` tool proved unreliable for complex, multi-line JSON modifications within Jupyter notebooks, leading to file corruption. This highlighted the need for extreme caution or alternative methods for such changes.
- **`tmux` Configuration:** Addressed issues with `tmux` keybindings and ensuring `uv` was in PATH for SSH sessions within the `connect_jupyter.sh` script.
- **`matplotlib` Installation:** Diagnosed and fixed `ModuleNotFoundError` for `matplotlib` by ensuring all dependencies were correctly installed in the virtual environment.
- **Jupyter Lab Kernel Crash:** The Jupyter Lab kernel is crashing when running the PnL analysis notebook, likely due to Out-of-Memory (OOM) errors or complex Polars query execution.

**Next Steps:**
1.  Execute the revised Git restoration plan (in-place, preserving the data lake).
2.  Debug and fix the Jupyter Lab kernel crash in `Example 1 Trader Analysis.ipynb`.
3.  Complete the data analysis phase.

**Important Patterns and Preferences:**
- **Memory First:** All data processing must be designed with low memory usage as a primary constraint. Prefer streaming, chunking, or lazy operations where possible.
- **Defensive Coding:** Assume all external data sources and historical data are unstable or inconsistent. Code must be resilient to schema changes and data type drift.
- **Verify, then run:** For long-running processes, perform a test run on a small subset of the data to verify correctness before launching the full run.
- **`replace` Tool Caution:** Avoid using the `replace` tool for large, multi-line JSON modifications within files like Jupyter notebooks. Prefer manual edits or `write_file` with carefully constructed and validated JSON content.
- **Git Recovery Strategy:** When `.git` is lost but the working directory (including large data assets) must be preserved, use an in-place Git recovery strategy involving temporary cloning and `.git` directory transfer.
- **User Communication:** Explicitly confirm understanding of critical steps, especially those involving data deletion, storage constraints, or potential data loss. Ensure clarity and address user concerns proactively.
- **Environment Setup:** Always verify that all necessary dependencies are installed and the correct Python environment is activated for any script or application execution.