# Polymarket Data

A comprehensive data pipeline for fetching, processing, and analyzing Polymarket trading data. This system collects market information, order-filled events, and processes them into a structured, partitioned Parquet datalake.

## Quick Download

**First-time users**: Download the [latest data snapshot](https://polydata-archive.s3.us-east-1.amazonaws.com/archive.tar.xz) and extract it in the main repository directory before your first run. This will save you over 2 days of initial data collection time.

## Overview

This pipeline performs three main operations, storing all data in a partitioned Parquet datalake for high performance and memory efficiency:

1.  **Market Data Collection** - Fetches all Polymarket markets with metadata.
2.  **Order Event Scraping** - Collects order-filled events from the Goldsky subgraph.
3.  **Trade Processing** - Transforms raw order events into structured trade data.

## Installation

This project uses [UV](https://docs.astral.sh/uv/) for fast, reliable package management.

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Install Dependencies

```bash
# Install all dependencies
uv sync

# Install with development dependencies (Jupyter, etc.)
uv sync --extra dev
```

## Quick Start

```bash
# Run with UV (recommended)
uv run python update_all.py

# Or activate the virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python update_all.py
```

This will sequentially run all three pipeline stages:
- Update markets from Polymarket API
- Update order-filled events from Goldsky
- Process new orders into trades

## Project Structure

```
poly_data/
├── update_all.py              # Main orchestrator script
├── update_utils/              # Data collection modules
│   ├── update_markets.py      # Fetch markets from Polymarket API
│   ├── update_goldsky.py      # Scrape order events from Goldsky
│   └── process_live.py        # Process orders into trades
├── poly_utils/                # Utility functions
│   └── utils.py               # Market loading and other helpers
├── markets_partitioned/       # Raw market data (partitioned by year/month)
│   └── ...
├── goldsky/                   # Raw order-filled events (partitioned by year/month)
│   └── orderFilled/
│       └── ...
└── processed/                 # Processed trade data (partitioned by year/month)
    └── trades/
        └── ...
```

## Data Datalake

All data is stored in a partitioned Parquet format to allow for efficient querying and to minimize memory usage, especially on resource-constrained systems.

### `markets_partitioned/`
Contains market metadata including questions, outcomes, tokens, creation/close times, and volume. Partitioned by the market creation date.

### `goldsky/orderFilled/`
Contains raw order-filled events from the Goldsky subgraph, including maker/taker addresses, amounts, and transaction hashes. Partitioned by the event timestamp.

### `processed/trades/`
Contains structured and enriched trade data, ready for analysis. This includes market IDs, trade direction, price, and USD amounts. Partitioned by the trade timestamp.

## Pipeline Stages

### 1. Update Markets (`update_markets.py`)

Fetches all markets from the Polymarket API and stores them in the `markets_partitioned` dataset.

**Features**:
- Automatic resume from last offset (idempotent)
- Rate limiting and error handling
- Batch fetching (500 markets per request)

### 2. Update Goldsky (`update_goldsky.py`)

Scrapes order-filled events from the Goldsky subgraph API and saves them to the `goldsky/orderFilled` dataset.

**Features**:
- Resumes automatically from the last recorded timestamp in the dataset.
- Handles GraphQL queries with pagination.
- Deduplicates events.

### 3. Process Live Trades (`process_live.py`)

Processes raw order events from `goldsky/orderFilled` into structured trades in `processed/trades`.

**Features**:
- Maps asset IDs to markets using a token lookup.
- Calculates prices and trade directions.
- Handles missing markets by discovering them from trades.
- Incremental processing from the last checkpoint.

## Dependencies

Dependencies are managed via `pyproject.toml` and installed automatically with `uv sync`.

**Key Libraries**:
- `polars` - Fast DataFrame operations for the Parquet datalake.
- `pandas` - Data manipulation.
- `gql` - GraphQL client for Goldsky.
- `requests` - HTTP requests to Polymarket API.

**Development Dependencies** (optional, installed with `--extra dev`):
- `jupyter` - Interactive notebooks
- `notebook` - Jupyter notebook interface
- `ipykernel` - Python kernel for Jupyter.

## Analysis

### Loading Data

The partitioned Parquet format allows for very efficient data loading and filtering using Polars' `scan_parquet` function.

```python
import polars as pl
from poly_utils import get_markets

# Load markets (helper function handles partitioned data)
markets_df = get_markets()

# Scan the processed trades dataset
# This is a lazy scan, no data is loaded into memory yet
df = pl.scan_parquet("processed/trades/**/*.parquet")

# You can now apply filters or transformations before collecting the data
# For example, filter for trades in a specific time range
df = df.filter(pl.col("timestamp").is_between(
    "2023-01-01T00:00:00", "2023-02-01T00:00:00"
))

# Only when you call .collect() is the data actually read and processed
results = df.collect()
```

### Filtering Trades by User

**Important**: When filtering for a specific user's trades, filter by the `maker` column. This is how Polymarket generates events at the contract level. The `maker` column shows trades from that user's perspective, including price.

```python
USERS = {
    'domah': '0x9d84ce0306f8551e02efef1680475fc0f1dc1344',
    '50pence': '0x3cf3e8d5427aed066a7a5926980600f6c3cf87b3',
}

# Scan the trades dataset
trades_df = pl.scan_parquet("processed/trades/**/*.parquet")

# Get all trades for a specific user (lazy operation)
trader_lazy_df = trades_df.filter(pl.col("maker") == USERS['domah'])

# Collect the results into a DataFrame
trader_df = trader_lazy_df.collect()
```

## License

Go wild with it