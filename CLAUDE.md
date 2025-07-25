# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Telegram bot that monitors Starknet token purchases and sends styled alerts to Telegram groups. The bot is designed for token creators who want to track buying activity on their tokens across various DEXs (Ekubo, JediSwap, etc.).

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see Configuration section)
# Test the bot connection
python test_bot.py

# Start the bot (HTTP webhook mode)
python main.py

# For debugging
LOG_LEVEL=DEBUG python main.py
```

## Configuration

The bot requires a `.env` file with these variables:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_PATH=./bot_data.db
LOG_LEVEL=INFO
MONITORING_INTERVAL=15
WEBHOOK_PORT=5000
```

### Webhook Configuration

The bot now uses HTTP webhooks instead of polling. To configure the webhook:

```bash
# Set webhook URL (replace with your domain)
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
     -H 'Content-Type: application/json' \
     -d '{"url": "https://your-domain.com/webhook"}'

# Or for local testing with ngrok:
# 1. Install ngrok: https://ngrok.com/
# 2. Start ngrok: ngrok http 5000
# 3. Use the ngrok URL for webhook
```

## Architecture

The codebase follows a modular architecture with these core components:

### Core Modules

- **main.py**: Entry point that loads environment variables, sets up logging, and starts the bot
- **telegram_bot.py**: Main bot logic using HTTP API directly with Flask webhook server for Telegram interactions
- **starknet_monitor.py**: Blockchain monitoring service that fetches token data from DexScreener API
- **database.py**: SQLite database wrapper managing group configurations, transaction tracking, and admin permissions
- **test_bot.py**: Testing script to verify HTTP API connectivity and functionality

### Database Schema

SQLite database with three main tables:
- `group_configs`: Per-group configuration (token_address, symbol, DEX, thresholds)
- `last_transactions`: Transaction deduplication tracking
- `group_admins`: Permission management for bot commands

### Bot Setup Flow

The bot uses a simple fast setup approach:
- Single command setup with all parameters in one line
- No multi-step conversation flow
- Immediate configuration and activation

### Key Commands

- `/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD`: Fast setup with all parameters
- `/status`: Show current group configuration
- `/pause`/`/resume`: Control alert monitoring
- `/edit`: Shows setup format for reconfiguration

## External APIs

- **DexScreener API**: Primary data source for token prices and transaction data
- **Telegram Bot HTTP API**: Direct HTTP requests for message sending and group management (using curl/requests instead of python-telegram-bot library)

## File Structure

```
AlertBot/
├── main.py              # Application entry point
├── telegram_bot.py      # Telegram bot logic with HTTP API and Flask webhook
├── starknet_monitor.py  # Blockchain monitoring
├── database.py          # SQLite database management
├── test_bot.py          # HTTP API testing script
├── requirements.txt     # Python dependencies (Flask + requests)
├── .env                 # Environment variables (token, etc.)
├── bot_data.db          # SQLite database file
└── bot.log             # Application logs
```

## Development Notes

- The bot supports multi-group operation with independent configurations per group
- **NEW**: Uses HTTP API directly with requests library instead of python-telegram-bot
- **NEW**: Flask webhook server for receiving Telegram updates
- Uses async/await pattern for blockchain monitoring (with sync HTTP calls for Telegram)
- Simple single-command setup without conversation state management
- Includes error handling and automatic retry mechanisms
- Features customizable alert thresholds and formatting

## HTTP API Implementation

The bot now uses direct HTTP calls to the Telegram Bot API:

```python
# Example: Send message
response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                        json={'chat_id': chat_id, 'text': message})

# Example: Get bot info  
response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
```

## Fast Setup Example

```bash
/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50
```

Parameters:
- TOKEN_ADDRESS: Starknet token contract address
- SYMBOL: Token symbol (e.g., ETH, USDC)  
- DEX: DEX name (Ekubo, JediSwap, etc.)
- SUPPLY: Total token supply
- THRESHOLD: Minimum buy amount in USD (0 for all buys)