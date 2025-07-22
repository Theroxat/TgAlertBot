#!/usr/bin/env python3
"""
Starknet Token Alert Bot
Main entry point for the Telegram bot that monitors token purchases on Starknet
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

from telegram_bot import TelegramBot

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress some noisy loggers but keep telegram.ext at INFO for debugging
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram.bot').setLevel(logging.WARNING)
    logging.getLogger('telegram.ext.updater').setLevel(logging.INFO)

def main():
    """Main function to start the bot"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Get database path
    db_path = os.getenv('DATABASE_PATH', './bot_data.db')
    
    # Create and start bot
    bot = TelegramBot(bot_token, db_path)
    
    try:
        logging.info("Starting Starknet Token Alert Bot...")
        bot.start_bot()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        logging.info("Shutting down bot...")

if __name__ == "__main__":
    # Run the bot
    main()