import os
import json
import requests
import time
from typing import List
import polars as pl

PLATFORM_WALLETS = ['0xc5d563a36ae78145c45a50134d48a1215220f80a', '0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e']


def get_markets(main_dir: str = "markets_partitioned", missing_file: str = "missing_markets.parquet"):
    """
    Load and combine markets from the partitioned parquet dataset and the missing markets parquet file.
    Deduplicates and sorts by createdAt.
    Returns combined Polars DataFrame sorted by creation date.
    """
    import polars as pl
    
    dfs = []
    
    # Load main markets from partitioned parquet dataset
    if os.path.exists(main_dir) and any(os.scandir(main_dir)):
        files = sorted([os.path.join(root, f) for root, _, files in os.walk(main_dir) for f in files if f.endswith('.parquet')])
        if files:
            scans = [pl.scan_parquet(f) for f in files]
            main_df = pl.concat(scans, how='diagonal').collect(streaming=True)
            dfs.append(main_df)
            print(f"Loaded {len(main_df)} markets from {main_dir}")
    
    # Load missing markets file
    if os.path.exists(missing_file):
        missing_df = pl.read_parquet(missing_file)
        dfs.append(missing_df)
        print(f"Loaded {len(missing_df)} markets from {missing_file}")
    
    if not dfs:
        print("No market files found!")
        return pl.DataFrame()
    
    # Combine, deduplicate, and sort
    combined_df = (
        pl.concat(dfs)
        .unique(subset=['id'], keep='first')
        .sort('createdAt')
    )
    
    print(f"Combined total: {len(combined_df)} unique markets (sorted by createdAt)")
    return combined_df


def update_missing_tokens(missing_token_ids: List[str], parquet_filename: str = "missing_markets.parquet"):
    """
    Fetch market data for missing token IDs and save to a parquet file.
    
    Args:
        missing_token_ids: List of token IDs to fetch
        parquet_filename: Parquet file to save missing markets (default: missing_markets.parquet)
    """
    if not missing_token_ids:
        print("No missing tokens to fetch")
        return
    
    print(f"Fetching {len(missing_token_ids)} missing tokens...")
    
    new_markets_data = []
    processed_market_ids = set()
    
    # If file exists, read existing market IDs to avoid duplicates
    if os.path.exists(parquet_filename):
        try:
            existing_df = pl.read_parquet(parquet_filename)
            processed_market_ids.update(existing_df['id'].to_list())
            print(f"Found {len(processed_market_ids)} existing markets in {parquet_filename}")
        except Exception as e:
            print(f"Error reading existing file: {e}")

    for token_id in missing_token_ids:
        print(f"Fetching market for token: {token_id}")
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                response = requests.get(
                    'https://gamma-api.polymarket.com/markets',
                    params={'clob_token_ids': token_id},
                    timeout=30
                )
                
                if response.status_code == 429:
                    print(f"Rate limited - waiting 10 seconds...")
                    time.sleep(10)
                    continue
                elif response.status_code != 200:
                    print(f"API error {response.status_code} for token {token_id}")
                    retry_count += 1
                    time.sleep(2)
                    continue
                
                markets = response.json()
                
                if not markets:
                    print(f"No market found for token {token_id}")
                    break
                
                market = markets[0]
                market_id = market.get('id', '')
                
                if market_id in processed_market_ids:
                    print(f"Market {market_id} already exists - skipping")
                    break
                
                clob_tokens_str = market.get('clobTokenIds', '[]')
                clob_tokens = json.loads(clob_tokens_str) if isinstance(clob_tokens_str, str) else clob_tokens_str
                
                if len(clob_tokens) < 2:
                    print(f"Invalid token data for {token_id}")
                    break
                
                outcomes_str = market.get('outcomes', '[]')
                outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                
                new_markets_data.append({
                    'createdAt': market.get('createdAt', ''),
                    'id': market_id,
                    'question': market.get('question', '') or market.get('title', ''),
                    'answer1': outcomes[0] if len(outcomes) > 0 else 'YES',
                    'answer2': outcomes[1] if len(outcomes) > 1 else 'NO',
                    'neg_risk': market.get('negRiskAugmented', False) or market.get('negRiskOther', False),
                    'market_slug': market.get('slug', ''),
                    'token1': clob_tokens[0],
                    'token2': clob_tokens[1],
                    'condition_id': market.get('conditionId', ''),
                    'volume': market.get('volume', ''),
                    'ticker': market['events'][0].get('ticker', '') if market.get('events') else '',
                    'closedTime': market.get('closedTime', '')
                })
                
                processed_market_ids.add(market_id)
                print(f"Successfully fetched market {market_id} for token {token_id}")
                break
                
            except Exception as e:
                print(f"Error fetching token {token_id}: {e}")
                retry_count += 1
                time.sleep(2)
        
        if retry_count >= max_retries:
            print(f"Failed to fetch token {token_id} after {max_retries} retries")
        
        time.sleep(0.5)
    
    if not new_markets_data:
        print("No new markets to add")
        return
    
    new_markets_df = pl.DataFrame(new_markets_data)
    
    if os.path.exists(parquet_filename):
        existing_df = pl.read_parquet(parquet_filename)
        combined_df = pl.concat([existing_df, new_markets_df]).unique(subset=['id'], keep='last')
    else:
        combined_df = new_markets_df
        
    combined_df.write_parquet(parquet_filename)
    
    print(f"Added {len(new_markets_data)} new markets to {parquet_filename}")
    print(f"Total markets now in file: {len(combined_df)}")

