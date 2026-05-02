import os
import json
import time
import atexit
import signal
import sys
from mcp.server.fastmcp import FastMCP
from dataroma_scraper import (
    get_manager_holdings, 
    get_insider_trades,
    get_all_managers,
    scrape_homepage,
    get_realtime_activity
)

# Initialize MCP Server
mcp = FastMCP("DataromaLocal")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "dataroma_cache.json")
CACHE = {}

def load_cache():
    global CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                CACHE = json.load(f)
        except Exception:
            CACHE = {}

def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(CACHE, f, indent=2)
    except Exception:
        pass

# Load cache immediately on module load
load_cache()

# Persistence on exit
atexit.register(save_cache)
def handle_signal(sig, frame):
    save_cache()
    sys.exit(0)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def populate_homepage_cache():
    """Fetches the homepage and populates all relevant aggregate caches at once."""
    print("Performing One-Shot homepage scrape...")
    data = scrape_homepage()
    if "error" in data:
        return
    
    timestamp = time.time()
    
    # 1. Populate Market Intelligence Lists
    for key, result in data["market_intelligence"].items():
        CACHE[key] = {
            'timestamp': timestamp,
            'data': result
        }
        
    # 2. Populate Manager List
    CACHE["all_managers"] = {
        'timestamp': timestamp,
        'data': {
            "count": len(data["managers"]),
            "date_updated": data["date_updated"],
            "managers": data["managers"]
        }
    }
    save_cache()

def get_cached_data(key, scraper_func, ttl_hours, *args):
    now = time.time()
    ttl_seconds = ttl_hours * 3600
    
    if key in CACHE:
        entry = CACHE[key]
        if now - entry['timestamp'] < ttl_seconds:
            return entry['data']
            
    # One-Shot trigger: If we are missing a homepage list, scrape the whole homepage
    homepage_keys = ['top_buys', 'big_bets', 'high_conviction_lows', 'all_managers']
    if key in homepage_keys:
        populate_homepage_cache()
        if key in CACHE:
            return CACHE[key]['data']

    # Refresh specific cache (Lazy Load for holdings/insiders)
    print(f"Cache miss for {key}. Scraping...")
    data = scraper_func(*args)
    if "error" not in data:
        CACHE[key] = {
            'timestamp': now,
            'data': data
        }
    return data

@mcp.tool()
def get_investor_holdings(manager_id: str):
    """
    Get the portfolio holdings for a specific superinvestor (e.g. 'BRK' for Buffett).
    Includes percentage weights and amount invested.
    """
    key = f"holdings_{manager_id}"
    holdings_data = get_cached_data(key, get_manager_holdings, 24, manager_id)
    
    # Enrich with insider summary if not errored
    if isinstance(holdings_data, dict) and "holdings" in holdings_data:
        for holding in holdings_data["holdings"][:10]: # Limit enrichment to top 10 for performance
            symbol = holding["symbol"]
            insider_key = f"insider_{symbol}"
            insider_data = get_cached_data(insider_key, get_insider_trades, 24, symbol)
            
            if isinstance(insider_data, dict) and "transactions" in insider_data:
                txs = insider_data["transactions"]
                buys = [t for t in txs if "Buy" in t["transaction_type"]]
                sells = [t for t in txs if "Sell" in t["transaction_type"]]
                holding["insider_sentiment_3mo"] = {
                    "total_buys": len(buys),
                    "total_sells": len(sells),
                    "recent_transactions": txs[:5]
                }
    return holdings_data

@mcp.tool()
def get_realtime_insider_trades(symbol: str):
    """Get the 10 most recent insider transactions for a specific stock ticker."""
    key = f"insider_{symbol}"
    return get_cached_data(key, get_insider_trades, 24, symbol)

@mcp.tool()
def get_market_intelligence(list_type: str):
    """
    Get aggregate market data from Dataroma.
    Supported list_type values:
    - 'latest_insider_buys': Recent significant Form 4 purchases.
    - 'most_owned_stocks': Stocks held by the most superinvestors.
    - 'top_10_stocks_pct': Stocks with highest portfolio concentration.
    - 'big_bets': High-conviction positions across all managers.
    - 'top_buys_last_qtr': Most bought stocks by volume in the recent quarter.
    - 'top_buys_last_qtr_pct': Most bought stocks by portfolio weight in the recent quarter.
    - 'top_buys_last_2_qtrs': Most bought stocks over the last 6 months.
    - 'top_buys_last_2_qtrs_pct': Most bought stocks by weight over the last 6 months.
    - 'high_conviction_lows': 5% or greater holdings trading near 52-week lows.
    - 'insider_concentration': Stocks with most distinct insider buyers in last 3 months.
    - 'realtime_activity': Live feed of superinvestor buys and sells.
    """
    # Trigger one-shot homepage scrape if cache is missing
    homepage_keys = [
        'latest_insider_buys', 'most_owned_stocks', 'top_10_stocks_pct', 
        'big_bets', 'top_buys_last_qtr', 'top_buys_last_qtr_pct', 
        'top_buys_last_2_qtrs', 'top_buys_last_2_qtrs_pct', 
        'high_conviction_lows', 'insider_concentration'
    ]
    
    if list_type == 'realtime_activity':
        return get_cached_data('realtime_activity', get_realtime_activity, 24)

    now = time.time()
    if list_type not in CACHE or (now - CACHE[list_type]['timestamp'] > 24 * 3600):
        if list_type in homepage_keys:
            populate_homepage_cache()

    if list_type in CACHE:
        return CACHE[list_type]['data']
    
    return {"error": f"Invalid list type. Supported: {homepage_keys}"}


@mcp.tool()
def list_superinvestors():
    """Get a list of all superinvestors tracked on Dataroma, including their IDs and firm names."""
    return get_cached_data("all_managers", get_all_managers, 24)

@mcp.tool()
def invalidate_cache(key: str = "all"):
    """
    Manually clear the cache to force a fresh scrape.
    Use 'all' to clear everything, or provide a specific key (e.g. 'holdings_BRK', 'big_bets').
    """
    global CACHE
    if key == "all":
        CACHE = {}
        message = "Entire cache cleared."
    elif key in CACHE:
        del CACHE[key]
        message = f"Cache key '{key}' cleared."
    else:
        message = f"Key '{key}' not found in cache."
    
    save_cache()
    return {"status": "success", "message": message}

if __name__ == "__main__":
    load_cache()
    mcp.run()
