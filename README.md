# Universal Dataroma MCP Server

A high-performance Model Context Protocol (MCP) server for extracting superinvestor portfolios and financial intelligence from Dataroma.com. This server is compatible with any MCP-enabled AI client, including **Claude Desktop**, **Cursor**, **Cline**, and **ZeroClaw**.

## Features
- **One-Shot Homepage Scraper**: Extracts all 10+ market lists and the manager directory in a single request for maximum efficiency.
- **Aggressive 24h Caching**: Uses an in-memory cache with disk persistence (dataroma_cache.json) to provide instant responses and avoid rate limits.
- **Enriched Portfolio Data**: 13F holdings automatically include recent insider transaction (Form 4) summaries.
- **Full Market Intelligence**: Direct access to Big Bets, 52-Week Lows, Most Owned Stocks, and Real-time Activity.

## Available Tools
- get_investor_holdings(manager_id): Get full 13F holdings for a specific manager (e.g., 'BRK' for Buffett).
- get_realtime_insider_trades(symbol): Get the 10 most recent insider transactions for a stock ticker.
- get_market_intelligence(list_type): Access Latest Insider Buys, Most Owned, Big Bets, Q1/Q2 Buying Trends, High Conviction Lows, and Insider Concentration.
- list_superinvestors(): Full directory of all 80+ tracked superinvestors and their IDs.
- invalidate_cache(key): Manually clear specific keys or the entire cache to force a fresh scrape.

## Installation
The recommended way to run this server is using `uvx` (which acts like `npx` for Python). This allows you to run it directly from PyPI without manually installing dependencies or cloning the repository.

```bash
uvx dataroma-mcp
```

## Configuration

### Claude Desktop
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "dataroma": {
      "command": "uvx",
      "args": ["dataroma-mcp"]
    }
  }
}
```

### Cursor / Windsurf / Cline
1. Open your AI settings/MCP configuration.
2. Add a new MCP server.
3. Type: `command`
4. Configuration:
   - Command: `uvx`
   - Arguments: `dataroma-mcp`

### ZeroClaw
Add to your `config.toml`:
```toml
[[mcp.servers]]
name = "Dataroma"
transport = "stdio"
command = "uvx"
args = ["dataroma-mcp"]
```

### Hermes
Hermes fully supports MCP. You can add the server by running this command in your Hermes terminal:
```bash
hermes mcp add dataroma-mcp uvx -- dataroma-mcp
```
*(Or, configure it directly in your Hermes MCP settings using the `uvx` command and `dataroma-mcp` argument).*

## Credits
Data sourced from [Dataroma.com](https://www.dataroma.com). This project is for educational and research purposes only.
