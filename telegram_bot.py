import logging
import asyncio
import json
import requests
from typing import Dict, Optional
from flask import Flask, request, jsonify
import threading
import time

from database import Database
from starknet_monitor import StarknetMonitor


class TelegramBot:
    def __init__(self, token: str, db_path: str = "./bot_data.db", webhook_port: int = 5000, use_polling: bool = True):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.db = Database(db_path)
        self.webhook_port = webhook_port
        self.use_polling = use_polling
        self.running = True
        self.last_update_id = 0
        
        if not use_polling:
            self.app = Flask(__name__)
            self.setup_webhook_routes()
        
        self.monitor = None
    
    def setup_webhook_routes(self):
        """Setup Flask routes for webhook"""
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            update = request.get_json()
            self.handle_update(update)
            return jsonify({'status': 'ok'})
    
    def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = None):
        """Send message using HTTP API"""
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text
        }
        if parse_mode:
            data['parse_mode'] = parse_mode
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message: {e}")
            return None
    
    def get_me(self):
        """Get bot info using HTTP API"""
        url = f"{self.base_url}/getMe"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()['result']
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting bot info: {e}")
            return None
    
    def get_chat_member(self, chat_id: int, user_id: int):
        """Get chat member info using HTTP API"""
        url = f"{self.base_url}/getChatMember"
        data = {
            'chat_id': chat_id,
            'user_id': user_id
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()['result']
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting chat member: {e}")
            return None
    
    def handle_update(self, update: dict):
        """Handle incoming update from webhook"""
        try:
            if 'message' in update:
                message = update['message']
                chat = message['chat']
                user = message['from']
                text = message.get('text', '')
                
                chat_id = chat['id']
                user_id = user['id']
                
                # Handle new chat members
                if 'new_chat_members' in message:
                    self.new_member_handler(chat_id, user_id, text, message)
                    return
                
                # Handle commands
                if text.startswith('/'):
                    command = text.split()[0][1:]  # Remove the '/'
                    
                    if command == 'start':
                        self.start_command(chat_id, user_id, text, message)
                    elif command == 'help':
                        self.help_command(chat_id, user_id, text, message)
                    elif command == 'setup':
                        self.fast_setup_command(chat_id, user_id, text, message)
                    elif command == 'status':
                        self.status_command(chat_id, user_id, text, message)
                    elif command == 'pause':
                        self.pause_command(chat_id, user_id, text, message)
                    elif command == 'resume':
                        self.resume_command(chat_id, user_id, text, message)
                    elif command == 'edit':
                        self.edit_command(chat_id, user_id, text, message)
        
        except Exception as e:
            logging.error(f"Error handling update: {e}")
    
    def get_updates(self, offset=None, timeout=30):
        """Get updates using HTTP API polling"""
        url = f"{self.base_url}/getUpdates"
        params = {
            'timeout': timeout
        }
        if offset:
            params['offset'] = offset
        
        try:
            response = requests.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting updates: {e}")
            return {'ok': False, 'result': []}
    
    def start_polling(self):
        """Start polling for updates"""
        logging.info("Starting polling mode...")
        
        while self.running:
            try:
                # Get updates from Telegram
                result = self.get_updates(offset=self.last_update_id + 1 if self.last_update_id > 0 else None)
                
                if result.get('ok') and result.get('result'):
                    updates = result['result']
                    
                    for update in updates:
                        # Update offset
                        self.last_update_id = max(self.last_update_id, update['update_id'])
                        
                        # Handle the update
                        self.handle_update(update)
                
                time.sleep(1)  # Small delay between requests
                
            except KeyboardInterrupt:
                logging.info("Received shutdown signal")
                self.running = False
                break
            except Exception as e:
                logging.error(f"Error in polling loop: {e}")
                time.sleep(5)  # Wait before retrying
        
    def start_bot(self):
        """Initialize and start the bot"""
        logging.info("Bot started successfully!")
        
        # Start monitoring in a separate thread
        monitoring_thread = threading.Thread(target=self._start_monitoring_thread, daemon=True)
        monitoring_thread.start()
        
        if self.use_polling:
            # Start polling mode
            self.start_polling()
        else:
            # Start Flask webhook server
            self.app.run(host='0.0.0.0', port=self.webhook_port, debug=False)
    
    def _start_monitoring_thread(self):
        """Start monitoring in a separate thread"""
        logging.info("Starting monitoring in background...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_monitoring())
        
    def start_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Handle /start command"""
        welcome_message = """
🤖 **Starknet Token Alert Bot**

Welcome! I help you monitor token purchases on Starknet and send stylized alerts to your group.

**Commands:**
• `/setup` - Fast setup with one command
• `/status` - Show current configuration
• `/pause` - Pause alerts
• `/resume` - Resume alerts
• `/edit` - Edit configuration

**Fast Setup Format:**
`/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD`

**Example:**
`/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50`
        """
        self.send_message(chat_id, welcome_message, parse_mode='Markdown')
    
    def help_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Handle /help command"""
        help_message = """🤖 Bot de Surveillance Starknet - Aide

📋 COMMANDES DISPONIBLES :

🚀 /setup - Configuration rapide en une commande
   Format: /setup ADRESSE_TOKEN SYMBOLE DEX SUPPLY SEUIL
   
📊 /status - Afficher la configuration actuelle du groupe
⏸️ /pause - Mettre en pause les alertes
▶️ /resume - Reprendre les alertes
✏️ /edit - Modifier la configuration (affiche le format setup)

📝 EXEMPLE DE CONFIGURATION :
/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50

📋 PARAMÈTRES :
• ADRESSE_TOKEN : Adresse du contrat token sur Starknet
• SYMBOLE : Symbole du token (ex: ETH, USDC)
• DEX : Nom de la plateforme (Ekubo, JediSwap, etc.)
• SUPPLY : Supply totale du token
• SEUIL : Montant minimum d'achat en USD (0 = tous les achats)

ℹ️ Le bot surveille les achats en temps réel et envoie des alertes stylisées dans ce groupe pour chaque transaction qui dépasse votre seuil configuré."""
        self.send_message(chat_id, help_message)
    
    def new_member_handler(self, chat_id: int, user_id: int, text: str, message: dict):
        """Handle bot being added to a new group"""
        new_members = message.get('new_chat_members', [])
        bot_user = self.get_me()
        
        if bot_user and any(member.get('id') == bot_user['id'] for member in new_members):
            welcome_message = """🎉 Salut ! Merci de m'avoir ajouté à votre groupe !

Je suis un bot de surveillance de tokens Starknet qui vous aide à :
• Surveiller les achats de tokens en temps réel  
• Envoyer des alertes stylisées dans ce groupe
• Filtrer par montants minimum d'achat
• Supporter plusieurs plateformes DEX

Pour commencer, configurez-moi avec cette commande :
/setup ADRESSE_TOKEN SYMBOLE DEX SUPPLY SEUIL

Exemple :
/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50

Tapez /help pour voir toutes les commandes disponibles !"""
            self.send_message(chat_id, welcome_message)
    
    
    def status_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Show current group configuration"""
        config = self.db.get_group_config(chat_id)
        
        if not config:
            self.send_message(chat_id, "❌ No configuration found. Use `/setup` to configure monitoring.")
            return
        
        status_icon = "✅" if config['is_active'] else "⏸️"
        status_text = "Active" if config['is_active'] else "Paused"
        
        status_message = f"""
{status_icon} **Bot Status: {status_text}**

**Token:** {config['token_symbol']}
**Address:** `{config['token_address'][:10]}...{config['token_address'][-8:]}`
**DEX:** {config['dex_name']}
**Total Supply:** {config['total_supply']:,}
**Min. Threshold:** ${config['min_buy_threshold']}
**Alert Frequency:** {config['alert_frequency'].replace('_', ' ').title()}

Use `/pause` or `/resume` to control alerts.
Use `/edit` to modify configuration.
        """
        
        self.send_message(chat_id, status_message, parse_mode='Markdown')
    
    def pause_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Pause alerts for this group"""
        if self.db.toggle_group_active(chat_id, False):
            self.send_message(chat_id, "⏸️ Alerts paused for this group.")
        else:
            self.send_message(chat_id, "❌ No configuration found or error occurred.")
    
    def resume_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Resume alerts for this group"""
        if self.db.toggle_group_active(chat_id, True):
            self.send_message(chat_id, "▶️ Alerts resumed for this group!")
        else:
            self.send_message(chat_id, "❌ No configuration found or error occurred.")
    
    def edit_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Edit configuration (restart setup)"""
        self.send_message(
            chat_id,
            "🔧 To edit your configuration, please run `/setup` again.\n\n"
            "**Format:** `/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD`",
            parse_mode='Markdown'
        )
    
    def fast_setup_command(self, chat_id: int, user_id: int, text: str, message: dict):
        """Fast setup command - all parameters in one line"""
        # Check admin status for groups
        chat = message['chat']
        if chat['type'] in ['group', 'supergroup']:
            chat_member = self.get_chat_member(chat_id, user_id)
            if chat_member and chat_member['status'] not in ['creator', 'administrator']:
                self.send_message(chat_id, "❌ Only group admins can setup the bot.")
                return
        
        # Parse arguments
        args = text.split()[1:]  # Remove command itself
        if len(args) < 5:
            self.send_message(
                chat_id,
                "❌ Fast Setup Usage:\n"
                "/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD\n\n"
                "Parameters:\n"
                "• TOKEN_ADDRESS: Your token address on Starknet\n"
                "• SYMBOL: Token symbol (e.g., ETH, USDC)\n"
                "• DEX: DEX name (Ekubo, JediSwap, etc.)\n"
                "• SUPPLY: Total token supply\n"
                "• THRESHOLD: Minimum buy amount in USD (0 for all)\n\n"
                "Example:\n"
                "/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50"
            )
            return
        
        token_address, symbol, dex, supply, threshold = args[0], args[1], args[2], args[3], args[4]
        
        # Validate inputs
        try:
            if not token_address.startswith('0x') or len(token_address) < 60:
                raise ValueError("Invalid token address format")
            
            if len(symbol) < 1 or len(symbol) > 10:
                raise ValueError("Token symbol must be 1-10 characters")
            
            supply = int(supply.replace(',', ''))
            threshold = float(threshold)
            
            if supply <= 0:
                raise ValueError("Supply must be greater than 0")
            if threshold < 0:
                raise ValueError("Threshold must be 0 or higher")
                
        except ValueError as e:
            self.send_message(chat_id, f"❌ **Error:** {str(e)}\n\nPlease check your inputs and try again.")
            return
        
        # Create config
        config = {
            'token_address': token_address,
            'token_symbol': symbol.upper(),
            'dex_name': dex.title(),
            'total_supply': supply,
            'min_buy_threshold': threshold,
            'alert_frequency': 'every_buy',
            'is_active': True
        }
        
        # Save to database
        if self.db.save_group_config(chat_id, config):
            success_message = f"""
🎉 **Setup Complete!**

Your token monitoring is now active:

**Token:** {config['token_symbol']} 
**Address:** `{config['token_address'][:10]}...{config['token_address'][-8:]}`
**DEX:** {config['dex_name']}
**Supply:** {config['total_supply']:,}
**Min. Threshold:** ${config['min_buy_threshold']}
**Frequency:** Every Buy

I'll start monitoring purchases and send alerts here! 🚀

**Commands:**
• `/status` - View current config
• `/pause` - Pause alerts  
• `/resume` - Resume alerts
• `/setup` - Change config
            """
            self.send_message(chat_id, success_message, parse_mode='Markdown')
        else:
            self.send_message(chat_id, "❌ Error saving configuration. Please try again.")
    
    
    def send_buy_alert(self, chat_id: int, metrics: Dict):
        """Send a formatted buy alert to the group"""
        try:
            # Check if transaction was already processed
            tx_hash = metrics.get('tx_hash', '')
            if tx_hash and self.db.is_transaction_processed(chat_id, tx_hash):
                return
            
            # Format the alert message
            alert_message = f"""
🗡🗡🗡🗡🗡🗡🗡🗡

👊 **SLAY BUY** 👊

💸 **Spent:** ${metrics['spent_usd']:.2f} ({metrics['spent_base']:.4f} {metrics['base_currency']})
💰 **Bought:** {metrics['bought_amount']/1000:.1f}K / {metrics['supply_percentage']:.4f}% of the supply
📊 **Price:** ${metrics['current_price']:.8f}
🏦 **Market Cap:** ${metrics['market_cap']:,.2f}
💯 **Total supply:** {metrics['total_supply']:,}
🦶 **Holders:** {metrics['holder_count']}

🗡🗡🗡🗡🗡🗡🗡🗡
            """
            
            self.send_message(
                chat_id=chat_id,
                text=alert_message,
                parse_mode='Markdown'
            )
            
            # Mark transaction as processed
            if tx_hash:
                self.db.add_transaction(chat_id, tx_hash)
                
            logging.info(f"Sent buy alert to chat {chat_id}")
            
        except Exception as e:
            logging.error(f"Error sending buy alert: {e}")
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        logging.info("Initializing monitoring system...")
        
        async with StarknetMonitor() as monitor:
            self.monitor = monitor
            logging.info("Monitor initialized successfully")
            
            while True:
                try:
                    # Get all active group configurations
                    active_groups = self.db.get_all_active_groups()
                    logging.info(f"Found {len(active_groups)} active group configurations")
                    
                    if active_groups:
                        # Monitor tokens and send alerts
                        # Créer un wrapper async pour send_buy_alert
                        async def async_send_alert(chat_id, metrics):
                            self.send_buy_alert(chat_id, metrics)
                        
                        await monitor.monitor_token_purchases(
                            active_groups, 
                            async_send_alert
                        )
                    else:
                        # No active groups, wait a bit longer
                        logging.info("No active groups configured, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(30)
    
    
    def stop_bot(self):
        """Stop the bot gracefully"""
        self.running = False
        logging.info("Bot stopped")