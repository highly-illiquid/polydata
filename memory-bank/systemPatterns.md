# System Patterns

**Architecture:** Client-Server Model
- **Client:** Local machine (user's workstation) for development, analysis, and initiating data pulls.
- **Server:** Virtual Private Server (VPS) for hosting the data pipeline, continuous data collection, and processing.

**Data Flow:**
1.  **Code Deployment:** Local machine (Git push) -> GitHub/GitLab (remote repository) -> VPS (Git clone/pull).
2.  **Data Collection/Processing:** VPS (executes Python pipeline).
3.  **Data Synchronization:** VPS (processed data) -> Local machine (rsync pull).

**Key Components:**
- **Local Machine:** Development environment, Git client, rsync client.
- **VPS:** Linux OS, Python environment, Git client, uv package manager, rsync server (implicitly via SSH).
- **External Services:** Polymarket API, Goldsky subgraph API, GitHub/GitLab (for code hosting).