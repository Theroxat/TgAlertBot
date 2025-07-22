import sqlite3
import logging
from typing import Optional, Dict, List

class Database:
    def __init__(self, db_path: str = "./bot_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for group configurations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_configs (
                    chat_id INTEGER PRIMARY KEY,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT NOT NULL,
                    dex_name TEXT NOT NULL,
                    total_supply INTEGER NOT NULL,
                    min_buy_threshold REAL DEFAULT 0,
                    alert_frequency TEXT DEFAULT 'every_buy',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for tracking last transactions to avoid duplicates
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS last_transactions (
                    chat_id INTEGER,
                    tx_hash TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, tx_hash)
                )
            ''')
            
            # Table for admin users per group
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_admins (
                    chat_id INTEGER,
                    user_id INTEGER,
                    is_owner BOOLEAN DEFAULT 0,
                    PRIMARY KEY (chat_id, user_id)
                )
            ''')
            
            conn.commit()
            logging.info("Database initialized successfully")
    
    def save_group_config(self, chat_id: int, config: Dict) -> bool:
        """Save or update group configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO group_configs 
                    (chat_id, token_address, token_symbol, dex_name, total_supply, 
                     min_buy_threshold, alert_frequency, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    chat_id,
                    config['token_address'],
                    config['token_symbol'],
                    config['dex_name'],
                    config['total_supply'],
                    config.get('min_buy_threshold', 0),
                    config.get('alert_frequency', 'every_buy'),
                    config.get('is_active', True)
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving group config: {e}")
            return False
    
    def get_group_config(self, chat_id: int) -> Optional[Dict]:
        """Get group configuration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT token_address, token_symbol, dex_name, total_supply,
                           min_buy_threshold, alert_frequency, is_active
                    FROM group_configs WHERE chat_id = ?
                ''', (chat_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'token_address': result[0],
                        'token_symbol': result[1],
                        'dex_name': result[2],
                        'total_supply': result[3],
                        'min_buy_threshold': result[4],
                        'alert_frequency': result[5],
                        'is_active': bool(result[6])
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting group config: {e}")
            return None
    
    def get_all_active_groups(self) -> List[Dict]:
        """Get all active group configurations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, token_address, token_symbol, dex_name, 
                           total_supply, min_buy_threshold, alert_frequency
                    FROM group_configs WHERE is_active = 1
                ''')
                
                results = cursor.fetchall()
                return [{
                    'chat_id': row[0],
                    'token_address': row[1],
                    'token_symbol': row[2],
                    'dex_name': row[3],
                    'total_supply': row[4],
                    'min_buy_threshold': row[5],
                    'alert_frequency': row[6]
                } for row in results]
        except Exception as e:
            logging.error(f"Error getting active groups: {e}")
            return []
    
    def toggle_group_active(self, chat_id: int, is_active: bool) -> bool:
        """Toggle group active status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE group_configs SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                ''', (is_active, chat_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error toggling group status: {e}")
            return False
    
    def add_transaction(self, chat_id: int, tx_hash: str) -> bool:
        """Add transaction to prevent duplicates"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO last_transactions (chat_id, tx_hash)
                    VALUES (?, ?)
                ''', (chat_id, tx_hash))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error adding transaction: {e}")
            return False
    
    def is_transaction_processed(self, chat_id: int, tx_hash: str) -> bool:
        """Check if transaction was already processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 1 FROM last_transactions 
                    WHERE chat_id = ? AND tx_hash = ?
                ''', (chat_id, tx_hash))
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking transaction: {e}")
            return False
    
    def cleanup_old_transactions(self, days: int = 7):
        """Clean up old transactions to prevent database bloat"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM last_transactions 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                conn.commit()
                logging.info(f"Cleaned up {cursor.rowcount} old transactions")
        except Exception as e:
            logging.error(f"Error cleaning up transactions: {e}")