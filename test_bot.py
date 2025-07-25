#!/usr/bin/env python3
"""
Script de test pour vérifier les fonctionnalités du bot avec HTTP API
"""

import requests
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_bot_connection():
    """Test la connexion au bot via l'API HTTP"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN non trouvé dans .env")
        return False
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        bot_info = response.json()
        
        if bot_info['ok']:
            result = bot_info['result']
            print(f"✅ Bot connecté avec succès!")
            print(f"   Nom: {result['first_name']}")
            print(f"   Username: @{result['username']}")
            print(f"   ID: {result['id']}")
            return True
        else:
            print(f"❌ Erreur API: {bot_info}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_send_message(chat_id, message):
    """Test l'envoi d'un message via HTTP API"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result['ok']:
            print(f"✅ Message envoyé avec succès au chat {chat_id}")
            return True
        else:
            print(f"❌ Erreur envoi message: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur envoi message: {e}")
        return False

def simulate_webhook_update():
    """Simule une mise à jour webhook pour tester les handlers"""
    sample_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1234,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1640995200,
            "text": "/start"
        }
    }
    
    print("📝 Exemple de mise à jour webhook:")
    print(json.dumps(sample_update, indent=2))
    return sample_update

def main():
    """Fonction principale de test"""
    print("🤖 Test du Bot Telegram avec HTTP API")
    print("=" * 50)
    
    # Test 1: Connexion au bot
    print("\n1. Test de connexion au bot...")
    if not test_bot_connection():
        print("❌ Impossible de continuer les tests")
        return
    
    # Test 2: Structure webhook
    print("\n2. Test de structure webhook...")
    simulate_webhook_update()
    
    # Test 3: Envoi de message (optionnel - nécessite un chat_id)
    chat_id = input("\n3. Entrez un chat_id pour tester l'envoi de message (ou appuyez sur Entrée pour ignorer): ")
    if chat_id.strip():
        try:
            chat_id = int(chat_id.strip())
            test_send_message(chat_id, "🧪 **Test Message**\n\nCeci est un message de test du bot HTTP API!")
        except ValueError:
            print("❌ Chat ID invalide")
    
    print("\n✅ Tests terminés!")
    print("\n📚 Pour démarrer le bot:")
    print("   python main.py")
    print("\n🔗 Pour configurer le webhook:")
    print(f"   curl -X POST https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN')}/setWebhook \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"url\": \"https://your-domain.com/webhook\"}'")

if __name__ == "__main__":
    main()