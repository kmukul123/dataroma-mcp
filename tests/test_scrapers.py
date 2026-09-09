import unittest
from dataroma_scraper import (
    scrape_homepage,
    get_all_managers,
    get_manager_holdings,
    get_insider_trades,
    get_stock_owners,
    get_realtime_activity
)

class TestDataromaScrapers(unittest.TestCase):
    def test_scrape_homepage(self):
        data = scrape_homepage()
        self.assertNotIn("error", data)
        self.assertIn("market_intelligence", data)
        self.assertIn("managers", data)
        
        # Verify it successfully parsed at least one intelligence list
        self.assertGreater(len(data["market_intelligence"]), 0)
        # Verify managers were extracted
        self.assertGreater(len(data["managers"]), 0)

    def test_get_all_managers(self):
        data = get_all_managers()
        self.assertNotIn("error", data)
        self.assertGreater(data.get("count", 0), 0)
        self.assertGreater(len(data.get("managers", [])), 0)
        
        # Verify first manager has required fields
        first_manager = data["managers"][0]
        self.assertIn("id", first_manager)
        self.assertIn("name", first_manager)

    def test_get_manager_holdings(self):
        # Testing with Warren Buffett (BRK)
        data = get_manager_holdings("BRK")
        self.assertNotIn("error", data)
        self.assertEqual(data.get("manager_id"), "BRK")
        self.assertGreater(len(data.get("holdings", [])), 0)
        
        # Verify first holding format
        first_holding = data["holdings"][0]
        self.assertIn("symbol", first_holding)
        self.assertIn("portfolio_percent", first_holding)
        self.assertIn("amount_invested_millions", first_holding)

    def test_get_insider_trades(self):
        # Testing with a highly traded stock (META)
        data = get_insider_trades("META")
        self.assertNotIn("error", data)
        self.assertEqual(data.get("symbol"), "META")
        
        # It's possible for there to be no recent trades, but the structure should be a list
        self.assertIsInstance(data.get("transactions"), list)
        
        if len(data["transactions"]) > 0:
            first_trade = data["transactions"][0]
            self.assertIn("insider_name", first_trade)
            self.assertIn("transaction_type", first_trade)
            self.assertIn("value", first_trade)

    def test_get_stock_owners(self):
        # Testing with AAPL
        data = get_stock_owners("AAPL")
        self.assertNotIn("error", data)
        self.assertEqual(data.get("symbol"), "AAPL")
        self.assertGreater(len(data.get("owners", [])), 0)
        
        # Verify first owner structure
        first_owner = data["owners"][0]
        self.assertIn("manager_name", first_owner)
        self.assertIn("portfolio_percent", first_owner)

    def test_get_realtime_activity(self):
        data = get_realtime_activity()
        self.assertNotIn("error", data)
        self.assertIsInstance(data.get("items"), list)
        
        if len(data["items"]) > 0:
            first_activity = data["items"][0]
            self.assertIn("reporting_name", first_activity)
            self.assertIn("security", first_activity)
            self.assertIn("activity", first_activity)

if __name__ == '__main__':
    unittest.main()
