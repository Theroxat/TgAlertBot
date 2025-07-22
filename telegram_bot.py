import logging
import asyncio
from typing import Dict

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.constants import ParseMode

from database import Database
from starknet_monitor import StarknetMonitor


class TelegramBot:
    def __init__(self, token: str, db_path: str = "./bot_data.db"):
        self.token = token
        self.db = Database(db_path)
        self.application = None
        self.monitor = None
        
    def start_bot(self):
        """Initialize and start the bot"""
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        handlers = [
            CommandHandler('start', self.start_command),
            CommandHandler('help', self.help_command),
            CommandHandler('setup', self.fast_setup_command),
            CommandHandler('status', self.status_command),
            CommandHandler('pause', self.pause_command),
            CommandHandler('resume', self.resume_command),
            CommandHandler('edit', self.edit_command),
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
        
        # Specific message handlers
        self.application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_member_handler))
        
        logging.info("Bot started successfully!")
        
        # Add post_init hook to start monitoring after bot is running
        self.application.post_init = self._post_init_hook
        
        # Run the bot using the standard method
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def _post_init_hook(self, application):
        """Hook called after the application starts"""
        logging.info("Starting monitoring in background...")
        application.create_task(self.start_monitoring())
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(help_message)
    
    async def new_member_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot being added to a new group"""
        new_members = update.message.new_chat_members
        bot_user = await context.bot.get_me()
        
        if any(member.id == bot_user.id for member in new_members):
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
            await update.message.reply_text(welcome_message)
    
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current group configuration"""
        chat_id = update.effective_chat.id
        config = self.db.get_group_config(chat_id)
        
        if not config:
            await update.message.reply_text("❌ No configuration found. Use `/setup` to configure monitoring.")
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
        
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause alerts for this group"""
        chat_id = update.effective_chat.id
        
        if self.db.toggle_group_active(chat_id, False):
            await update.message.reply_text("⏸️ Alerts paused for this group.")
        else:
            await update.message.reply_text("❌ No configuration found or error occurred.")
    
    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resume alerts for this group"""
        chat_id = update.effective_chat.id
        
        if self.db.toggle_group_active(chat_id, True):
            await update.message.reply_text("▶️ Alerts resumed for this group!")
        else:
            await update.message.reply_text("❌ No configuration found or error occurred.")
    
    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit configuration (restart setup)"""
        await update.message.reply_text(
            "🔧 To edit your configuration, please run `/setup` again.\n\n"
            "**Format:** `/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def fast_setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fast setup command - all parameters in one line"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Check admin status for groups
        if update.effective_chat.type in ['group', 'supergroup']:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            if chat_member.status not in ['creator', 'administrator']:
                await update.message.reply_text("❌ Only group admins can setup the bot.")
                return
        
        # Parse arguments
        args = context.args
        if len(args) < 5:
            await update.message.reply_text(
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
            await update.message.reply_text(f"❌ **Error:** {str(e)}\n\nPlease check your inputs and try again.")
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
            await update.message.reply_text(success_message, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ Error saving configuration. Please try again.")
    
    
    async def send_buy_alert(self, chat_id: int, metrics: Dict):
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
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=alert_message,
                parse_mode=ParseMode.MARKDOWN
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
                        await monitor.monitor_token_purchases(
                            active_groups, 
                            self.send_buy_alert
                        )
                    else:
                        # No active groups, wait a bit longer
                        logging.info("No active groups configured, waiting 60 seconds...")
                        await asyncio.sleep(60)
                        
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(30)
    
    
    async def stop_bot(self):
        """Stop the bot gracefully"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        logging.info("Bot stopped")