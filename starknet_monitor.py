import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List

class StarknetMonitor:
    def __init__(self):
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_token_data(self, token_address: str, dex_name: str = "ekubo") -> Optional[Dict]:
        """Get token data from DexScreener API"""
        try:
            # Clean token address - remove any extra data after first dash
            clean_address = token_address.split('-')[0] if '-' in token_address else token_address
            logging.info(f"Cleaned token address: {token_address} -> {clean_address}")
            
            url = f"{self.dexscreener_base}/tokens/{clean_address}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('pairs'):
                        # Find the pair for the specified DEX
                        for pair in data['pairs']:
                            if dex_name.lower() in pair.get('dexId', '').lower():
                                return self._format_token_data(pair)
                        
                        # If no specific DEX found, use the first pair
                        return self._format_token_data(data['pairs'][0])
                    
                return None
        except Exception as e:
            logging.error(f"Error fetching token data: {e}")
            return None
    
    def _format_token_data(self, pair_data: Dict) -> Dict:
        """Format pair data into standardized token data"""
        try:
            return {
                'token_address': pair_data.get('baseToken', {}).get('address', ''),
                'token_symbol': pair_data.get('baseToken', {}).get('symbol', ''),
                'price_usd': float(pair_data.get('priceUsd', 0)),
                'market_cap': float(pair_data.get('marketCap', 0)),
                'volume_24h': float(pair_data.get('volume', {}).get('h24', 0)),
                'price_change_24h': float(pair_data.get('priceChange', {}).get('h24', 0)),
                'liquidity_usd': float(pair_data.get('liquidity', {}).get('usd', 0)),
                'dex_id': pair_data.get('dexId', ''),
                'pair_address': pair_data.get('pairAddress', ''),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error formatting token data: {e}")
            return {}
    
    async def get_recent_transactions(self, token_address: str, dex_name: str = "ekubo") -> List[Dict]:
        """Get recent transactions for a token using Voyager API"""
        try:
            # Clean token address
            clean_address = token_address.split('-')[0] if '-' in token_address else token_address
            logging.info(f"Fetching real transactions for token {clean_address[:10]}... on {dex_name}")
            
            # Try multiple APIs
            transactions = []
            
            # Try StarkScan API first
            transactions = await self._fetch_starkscan_transactions(clean_address)
            if transactions:
                logging.info(f"Found {len(transactions)} real transactions from StarkScan")
                return transactions
            
            # Fallback to Voyager API
            transactions = await self._fetch_voyager_transactions(clean_address)
            if transactions:
                logging.info(f"Found {len(transactions)} real transactions from Voyager")
                return transactions
            
            # Fallback: Return empty list instead of mock data
            # This way we won't spam fake alerts
            logging.info("No recent transactions found")
            return []
            
        except Exception as e:
            logging.error(f"Error fetching transactions: {e}")
            return []

    async def _fetch_starkscan_transactions(self, token_address: str) -> List[Dict]:
        """Fetch transactions from StarkScan API"""
        try:
            # StarkScan API endpoint - trying public endpoints
            url = f"https://api.starkscan.co/api/v0/contracts/{token_address}/events"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    transactions = []
                    for event in data.get('data', []):
                        # Parse event data and convert to our format
                        parsed_tx = self._parse_starkscan_event(event, token_address)
                        if parsed_tx:
                            transactions.append(parsed_tx)
                    
                    return transactions[:10]  # Limit to recent 10
                else:
                    logging.warning(f"StarkScan API returned status {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"Error fetching from StarkScan API: {e}")
            return []

    def _parse_starkscan_event(self, event_data: Dict, token_address: str) -> Optional[Dict]:
        """Parse StarkScan event data into our format"""
        try:
            # This is speculative - adjust based on actual StarkScan API response
            event_name = event_data.get('name', '').lower()
            
            if 'transfer' in event_name:
                # Extract transfer amount (this is simplified)
                keys = event_data.get('keys', [])
                data = event_data.get('data', [])
                
                if len(data) >= 3:
                    # Typical ERC20 transfer: from, to, amount
                    from_addr = data[0] if len(data) > 0 else ''
                    to_addr = data[1] if len(data) > 1 else ''
                    amount_hex = data[2] if len(data) > 2 else '0x0'
                    
                    try:
                        amount = int(amount_hex, 16) if amount_hex.startswith('0x') else int(amount_hex)
                        amount_tokens = amount / 1e18  # Assuming 18 decimals
                        
                        # Rough USD conversion (would need real price data)
                        amount_usd = amount_tokens * 3700  # Assuming ETH price
                        
                        return {
                            'tx_hash': event_data.get('transaction_hash', ''),
                            'type': 'buy',  # Simplified logic
                            'amount_usd': amount_usd,
                            'amount_token': amount_tokens,
                            'amount_base': amount_usd / 3700,
                            'base_currency': 'ETH',
                            'timestamp': datetime.now().isoformat(),
                            'buyer': to_addr
                        }
                    except ValueError:
                        logging.warning(f"Could not parse amount: {amount_hex}")
            
            return None
            
        except Exception as e:
            logging.error(f"Error parsing StarkScan event: {e}")
            return None

    async def _fetch_voyager_transactions(self, token_address: str) -> List[Dict]:
        """Fetch transactions from Voyager API"""
        try:
            # Voyager API endpoint for token transfers
            # This is a simplified example - actual implementation might need more complex querying
            url = f"https://voyager.online/api/txns?contract={token_address}&type=transfer&ps=10"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    transactions = []
                    for tx in data.get('items', []):
                        # Parse transaction data and convert to our format
                        parsed_tx = self._parse_voyager_transaction(tx, token_address)
                        if parsed_tx:
                            transactions.append(parsed_tx)
                    
                    return transactions
                else:
                    logging.warning(f"Voyager API returned status {response.status}")
                    return []
                    
        except Exception as e:
            logging.error(f"Error fetching from Voyager API: {e}")
            return []

    def _parse_voyager_transaction(self, tx_data: Dict, token_address: str) -> Optional[Dict]:
        """Parse Voyager transaction data into our format"""
        try:
            # This is a simplified parser - actual Voyager API structure might be different
            # You'd need to adjust this based on the actual API response format
            
            if tx_data.get('type') == 'transfer':
                amount = tx_data.get('amount', 0)
                # Convert amount to USD (this would need real price data)
                amount_usd = amount * 0.001  # Placeholder conversion
                
                return {
                    'tx_hash': tx_data.get('hash', ''),
                    'type': 'buy',  # Simplified - would need logic to determine buy vs sell
                    'amount_usd': amount_usd,
                    'amount_token': amount,
                    'amount_base': amount_usd / 3700,  # Rough ETH conversion
                    'base_currency': 'ETH',
                    'timestamp': tx_data.get('timestamp', datetime.now().isoformat()),
                    'buyer': tx_data.get('from_address', 'unknown')
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error parsing transaction: {e}")
            return None
    
    async def calculate_buy_metrics(self, transaction: Dict, token_config: Dict) -> Dict:
        """Calculate buy metrics for alert formatting"""
        try:
            logging.info(f"Calculating metrics for token {token_config.get('token_address', 'unknown')}")
            
            token_data = await self.get_token_data(
                token_config['token_address'], 
                token_config['dex_name']
            )
            
            logging.info(f"Token data received: {token_data}")
            
            if not token_data:
                logging.warning("No token data received from API")
                return {}
            
            # Calculate percentage of supply bought
            total_supply = token_config['total_supply']
            amount_bought = transaction.get('amount_token', 0)
            supply_percentage = (amount_bought / total_supply) * 100 if total_supply > 0 else 0
            
            # Mock holder count (would need real blockchain data)
            holder_count = 143  # This should come from actual blockchain indexing
            
            metrics = {
                'spent_usd': transaction.get('amount_usd', 0),
                'spent_base': transaction.get('amount_base', 0),
                'base_currency': transaction.get('base_currency', 'STRK'),
                'bought_amount': amount_bought,
                'supply_percentage': supply_percentage,
                'current_price': token_data.get('price_usd', 0),
                'market_cap': token_data.get('market_cap', 0),
                'total_supply': total_supply,
                'holder_count': holder_count,
                'tx_hash': transaction.get('tx_hash', ''),
                'timestamp': transaction.get('timestamp', ''),
                'token_symbol': token_config['token_symbol']
            }
            
            logging.info(f"Calculated metrics: {metrics}")
            return metrics
            
        except Exception as e:
            logging.error(f"Error calculating buy metrics: {e}")
            return {}
    
    async def monitor_token_purchases(self, token_configs: List[Dict], callback_func):
        """Monitor multiple tokens for purchases and call callback with alerts"""
        logging.info(f"Starting monitoring loop for {len(token_configs)} token configs")
        
        while True:
            try:
                if not token_configs:
                    logging.info("No active token configs, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                for config in token_configs:
                    if not config.get('is_active', True):
                        logging.debug(f"Skipping inactive config for chat {config.get('chat_id')}")
                        continue
                    
                    logging.info(f"Monitoring token {config.get('token_symbol')} for chat {config.get('chat_id')}")
                        
                    # Get recent transactions
                    transactions = await self.get_recent_transactions(
                        config['token_address'],
                        config['dex_name']
                    )
                    
                    for transaction in transactions:
                        if transaction.get('type') == 'buy':
                            # Check minimum threshold
                            min_threshold = config.get('min_buy_threshold', 0)
                            amount_usd = transaction.get('amount_usd', 0)
                            
                            logging.info(f"Buy found: ${amount_usd} (threshold: ${min_threshold})")
                            
                            if amount_usd >= min_threshold:
                                logging.info("Threshold met, calculating metrics...")
                                
                                # Calculate metrics for alert
                                metrics = await self.calculate_buy_metrics(transaction, config)
                                if metrics:
                                    logging.info(f"Sending alert to chat {config['chat_id']}")
                                    # Call the callback with chat_id and metrics
                                    await callback_func(config['chat_id'], metrics)
                                else:
                                    logging.warning("Failed to calculate metrics")
                            else:
                                logging.info("Threshold not met, skipping alert")
                
                # Wait before next check
                logging.debug("Waiting 15 seconds before next check...")
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error