import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

BASE_URL = "https://www.dataroma.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def parse_generic_table(table):
    items = []
    if not table: return items
    
    # Try to find rows in tbody, otherwise use all trs excluding the first
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
    
    for row in rows:
        cols = row.find_all('td')
        if not cols: continue
        
        # Parse Symbol and Company
        full_text = cols[0].text.strip()
        match = re.match(r"^([A-Z0-9\.]+)\s*-\s*(.*)$", full_text)
        if match:
            symbol = match.group(1).strip()
            company = match.group(2).strip()
        else:
            symbol = full_text
            company = ""
            
        item = {"symbol": symbol, "company": company}
        
        # Add metric from the second column if it exists
        if len(cols) > 1:
            item["metric"] = cols[1].text.strip()
        
        # Add extra metrics from further columns (used in some lists)
        if len(cols) > 2:
            item["metric_extra"] = cols[2].text.strip()
            
        items.append(item)
    return items

def scrape_homepage():
    """Scrapes the entire Dataroma homepage to extract all 10 lists and the manager directory."""
    url = BASE_URL
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": "Failed to fetch Dataroma homepage"}

    soup = BeautifulSoup(response.text, 'html.parser')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "date_updated": timestamp,
        "market_intelligence": {},
        "managers": []
    }

    # Helper to parse lists that are groups of links in a TD
    def parse_links_list(header_text):
        td = soup.find('div', string=re.compile(header_text, re.I))
        if not td:
            td = soup.find('p', string=re.compile(header_text, re.I))
        if not td: return []
        
        parent_td = td.parent
        items = []
        for a in parent_td.find_all('a'):
            if 'stock.php' not in a.get('href', ''): continue
            full_text = a.text.strip()
            match = re.match(r"^([A-Z0-9\.]+)\s*-\s*(.*)$", full_text)
            if match:
                items.append({"symbol": match.group(1).strip(), "company": match.group(2).strip()})
            else:
                items.append({"symbol": full_text, "company": ""})
        return items

    # 1. Parse using Table IDs (most reliable)
    table_mapping = {
        'bigbets': 'big_bets',
        'low_52': 'high_conviction_lows',
        'ins_con': 'insider_concentration'
    }

    for table_id, key in table_mapping.items():
        table = soup.find('table', id=table_id)
        if table:
            data["market_intelligence"][key] = {"date_updated": timestamp, "items": parse_generic_table(table)}

    # 2. Parse using Headers (for the lists without IDs)
    list_mapping = {
        'latest_insider_buys': 'Latest significant',
        'most_owned_stocks': 'Top 10 most owned',
        'top_10_stocks_pct': 'Top 10 stocks by %',
        'top_buys_last_qtr': 'Top 10 buys last qtr',
        'top_buys_last_qtr_pct': 'Top 10 buys last qtr by %',
        'top_buys_last_2_qtrs': 'Top 10 buys last 2 qtrs',
        'top_buys_last_2_qtrs_pct': 'Top 10 buys last 2 qtrs by %'
    }

    for key, header in list_mapping.items():
        if key not in data["market_intelligence"]:
            data["market_intelligence"][key] = {"date_updated": timestamp, "items": parse_links_list(header)}

    # 3. Parse Manager Directory
    manager_links = soup.find_all('a', href=re.compile(r"m/holdings\.php\?m="))
    seen_ids = set()
    for link in manager_links:
        manager_id = link['href'].split('=')[-1]
        if manager_id not in seen_ids:
            data["managers"].append({"id": manager_id, "name": link.text.strip()})
            seen_ids.add(manager_id)

    return data


def get_manager_holdings(manager_id):
    url = f"{BASE_URL}/m/holdings.php?m={manager_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": f"Failed to fetch holdings for {manager_id}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    holdings = []
    
    table = soup.find('table', id='grid')
    if not table:
        return {"error": "Table not found"}

    rows = table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 11:
            continue
            
        stock_td = cols[1]
        full_text = stock_td.text.strip()
        match = re.match(r"^([A-Z0-9\.]+)\s*-\s*(.*)$", full_text)
        if match:
            symbol = match.group(1).strip()
            company = match.group(2).strip()
        else:
            symbol = full_text
            company = ""
        
        holding = {
            "symbol": symbol,
            "company": company,
            "portfolio_percent": cols[2].text.strip(),
            "amount_invested_millions": cols[6].text.strip(),
            "recent_activity": cols[3].text.strip(),
            "shares_held": cols[4].text.strip(),
            "insider_sentiment_3mo": None 
        }
        holdings.append(holding)
        
    return {
        "manager_id": manager_id,
        "manager_name": soup.find('div', id='m_name').text.strip() if soup.find('div', id='m_name') else manager_id,
        "date_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "holdings": holdings
    }

def get_insider_trades(symbol):
    url = f"{BASE_URL}/m/ins/ins.php?sym={symbol}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": f"Failed to fetch insider trades for {symbol}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    trades = []
    
    table = soup.find('table', id='grid')
    if not table:
        return {"symbol": symbol, "transactions": [], "date_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    rows = table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 6:
            continue
            
        trades.append({
            "date": cols[0].text.strip(),
            "insider_name": cols[1].text.strip(),
            "transaction_type": cols[3].text.strip(),
            "shares": cols[4].text.strip(),
            "price": cols[5].text.strip(),
            "value": cols[6].text.strip() if len(cols) > 6 else ""
        })
        
    return {
        "symbol": symbol,
        "date_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transactions": trades[:10]
    }

def get_all_managers():
    url = f"{BASE_URL}/m/managers.php"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": "Failed to fetch managers list"}

    soup = BeautifulSoup(response.text, 'html.parser')
    managers = []
    table = soup.find('table', id='grid')
    if not table: return {"error": "Managers table not found"}

    rows = table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 2: continue
        a_tag = cols[0].find('a')
        if a_tag:
            managers.append({
                "id": a_tag['href'].split('=')[-1],
                "name": a_tag.text.strip(),
                "firm": cols[1].text.strip()
            })
            
    return {
        "count": len(managers),
        "date_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "managers": managers
    }

def get_realtime_activity():
    """Scrapes the Real Time Superinvestor Activity page (/m/rt.php)."""
    url = f"{BASE_URL}/m/rt.php"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"error": "Failed to fetch Real-Time activity page"}

    soup = BeautifulSoup(response.text, 'html.parser')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = []
    
    table = soup.find('table', id='grid')
    if not table:
        return {"error": "Real-time activity table not found"}

    rows = table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 8:
            continue
            
        items.append({
            "transaction_date": cols[0].text.strip(),
            "reporting_name": cols[2].text.strip(),
            "activity": cols[3].text.strip(),
            "security": cols[4].text.strip(),
            "shares": cols[5].text.strip(),
            "price": cols[6].text.strip(),
            "total_value": cols[7].text.strip()
        })
        
    return {
        "date_updated": timestamp,
        "items": items
    }
