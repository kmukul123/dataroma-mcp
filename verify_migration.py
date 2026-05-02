import sys
import os
import time
import json
from datetime import datetime

# Add the current directory to sys.path so we can import our scripts
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

import dataroma_scraper
import dataroma_mcp

def test_stage_1_scraper():
    print("--- Stage 1: Testing Scraper & Parsing from NEW Folder ---")
    brk = dataroma_scraper.get_manager_holdings("BRK")
    if "error" in brk:
        print(f"FAILED: {brk['error']}")
        return False
    
    holding = brk['holdings'][0]
    print(f"Scraped Manager: {brk['manager_name']}")
    print(f"Verify Parsing: Symbol='{holding['symbol']}', Company='{holding['company']}'")
    
    if "-" in holding['symbol'] or not holding['company']:
        print("FAILED: Symbol and Company name not correctly separated.")
        return False
        
    print("SUCCESS: Scraper working correctly in new folder.\n")
    return True

def test_stage_2_one_shot():
    print("--- Stage 2: Testing One-Shot Homepage Logic ---")
    # This should populate multiple keys
    dataroma_mcp.CACHE = {}
    dataroma_mcp.populate_homepage_cache()
    
    keys = list(dataroma_mcp.CACHE.keys())
    print(f"Keys found in one-shot cache: {keys}")
    
    required_keys = ['big_bets', 'high_conviction_lows', 'all_managers']
    for k in required_keys:
        if k not in keys:
            print(f"FAILED: Missing key '{k}' in one-shot results.")
            return False
            
    print("SUCCESS: One-Shot logic is fully operational.\n")
    return True

def test_stage_3_persistence():
    print("--- Stage 3: Testing File Persistence in NEW Folder ---")
    cache_path = dataroma_mcp.CACHE_FILE
    print(f"Expected Cache Path: {cache_path}")
    
    dataroma_mcp.CACHE["folder_test"] = {"timestamp": time.time(), "data": "success"}
    dataroma_mcp.save_cache()
    
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            data = json.load(f)
            if "folder_test" in data:
                print("SUCCESS: Cache file correctly saved in the new folder.\n")
                return True
                
    print("FAILED: Cache file not found or data missing in new folder.")
    return False

if __name__ == "__main__":
    success = True
    if not test_stage_1_scraper(): success = False
    if success and not test_stage_2_one_shot(): success = False
    if success and not test_stage_3_persistence(): success = False
    
    if success:
        print("====================================")
        print("NEW FOLDER VERIFICATION SUCCESSFUL")
        print("====================================")
    else:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("VERIFICATION FAILED")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)
