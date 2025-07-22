# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Telegram bot that monitors Starknet token purchases and sends styled alerts to Telegram groups. The bot is designed for token creators who want to track buying activity on their tokens across various DEXs (Ekubo, JediSwap, etc.).

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see Configuration section)
# Then start the bot
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
```

## Architecture

The codebase follows a modular architecture with these core components:

### Core Modules

- **main.py**: Entry point that loads environment variables, sets up logging, and starts the bot
- **telegram_bot.py**: Main bot logic handling Telegram interactions, conversation flows, and message formatting
- **starknet_monitor.py**: Blockchain monitoring service that fetches token data from DexScreener API
- **database.py**: SQLite database wrapper managing group configurations, transaction tracking, and admin permissions

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
- **Telegram Bot API**: Message sending and group management

## File Structure

```
AlertBot/
├── main.py              # Application entry point
├── telegram_bot.py      # Telegram bot logic and handlers
├── starknet_monitor.py  # Blockchain monitoring
├── database.py          # SQLite database management
├── requirements.txt     # Python dependencies
├── bot_config.json      # Runtime configuration storage
├── bot_data.db          # SQLite database file
└── bot.log             # Application logs
```

## Development Notes

- The bot supports multi-group operation with independent configurations per group
- Uses async/await pattern for API calls and database operations
- Simple single-command setup without conversation state management
- Includes error handling and automatic retry mechanisms
- Features customizable alert thresholds and formatting

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