# Product Context

This project involves a Python data pipeline designed to interact with Polymarket trading data. Its primary functions include:

- **Market Data Collection:** Fetching market information and metadata from Polymarket.
- **Order Event Scraping:** Collecting order-filled events from the Goldsky subgraph.
- **Trade Processing:** Transforming raw order events into structured trade data.

The user's objective is to run this pipeline on a VPS to ensure continuous data collection and processing, and then to periodically pull the generated, processed data back to their local machine for analysis, likely using Jupyter notebooks as indicated by the project structure.