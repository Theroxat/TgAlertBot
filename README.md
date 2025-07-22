# 🤖 Starknet Token Alert Bot

Un bot Telegram qui permet aux créateurs de tokens sur Starknet de surveiller automatiquement les achats de leurs tokens et d'envoyer des alertes stylisées dans leurs groupes Telegram.

## 🚀 Fonctionnalités

- **Multi-groupes** : Un seul bot peut gérer plusieurs groupes indépendamment
- **Setup rapide** : Configuration en une seule commande
- **Monitoring en temps réel** : Surveillance des achats sur Starknet (Ekubo, JediSwap, etc.)
- **Alertes stylisées** : Messages formatés avec toutes les métriques importantes
- **Seuils personnalisables** : Filtrage par montant minimum d'achat
- **Commandes admin** : Contrôle complet via commandes Telegram

## 📋 Prérequis

- Python 3.8+
- Un bot Telegram (créé via @BotFather)
- Accès aux APIs Starknet (DexScreener, Voyager, etc.)

## 🛠️ Installation

1. **Cloner le projet**
```bash
git clone <repo-url>
cd AlertBot
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

4. **Variables d'environnement (.env)**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_PATH=./bot_data.db
LOG_LEVEL=INFO
MONITORING_INTERVAL=15
```

## 🚀 Lancement

```bash
python main.py
```

## 📱 Utilisation

### 1. Ajouter le bot dans un groupe

1. Invitez votre bot dans le groupe Telegram
2. Le bot se présente automatiquement et propose la configuration

### 2. Configuration rapide

Utilisez la commande setup avec tous les paramètres :

```
/setup TOKEN_ADDRESS SYMBOL DEX SUPPLY THRESHOLD
```

**Exemple :**
```
/setup 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7 ETH Ekubo 1000000 50
```

**Paramètres :**
- `TOKEN_ADDRESS`: Adresse du token sur Starknet
- `SYMBOL`: Symbole du token (ex: ETH, USDC)
- `DEX`: Nom du DEX (Ekubo, JediSwap, etc.)
- `SUPPLY`: Supply totale du token
- `THRESHOLD`: Montant minimum d'achat en USD (0 pour tous)

### 3. Alertes automatiques

Une fois configuré, le bot surveille automatiquement et envoie des alertes comme :

```
🗡🗡🗡🗡🗡🗡🗡🗡

👊 SLAY BUY 👊

💸 Spent: $524.84 (711.9707 STRK)  
💰 Bought: 551.0K / 0.6199% of the supply  
📊 Price: $0.00096689  
🏦 Market Cap: $85,868.39  
💯 Total supply : 88,888,888  
🦶 Holders : 143  

🗡🗡🗡🗡🗡🗡🗡🗡
```

## 🎛️ Commandes

| Commande | Description |
|----------|-------------|
| `/start` | Affiche le message de bienvenue |
| `/setup` | Configure ou reconfigure le monitoring |
| `/status` | Affiche la configuration actuelle |
| `/pause` | Met en pause les alertes |
| `/resume` | Reprend les alertes |
| `/edit` | Édite la configuration (= `/setup`) |

## 🏗️ Architecture

```
AlertBot/
├── main.py              # Point d'entrée principal
├── telegram_bot.py      # Logique du bot Telegram
├── starknet_monitor.py  # Monitoring blockchain
├── database.py          # Gestion base de données
├── requirements.txt     # Dépendances Python
├── .env.example        # Template de configuration
└── README.md           # Documentation
```

### Composants principaux

- **TelegramBot** : Gère les interactions Telegram et l'onboarding
- **StarknetMonitor** : Surveille la blockchain et les APIs
- **Database** : Stockage SQLite des configurations par groupe
- **Main** : Orchestration et point d'entrée

## 🔧 Configuration avancée

### Base de données

Le bot utilise SQLite avec 3 tables principales :
- `group_configs` : Configurations par groupe
- `last_transactions` : Éviter les doublons
- `group_admins` : Gestion des permissions

### APIs supportées

- **DexScreener** : API principale pour les données de prix/volume
- **Voyager** : API Starknet pour les transactions (optionnel)
- **APIs DEX** : Intégration directe (en développement)

### Personnalisation des alertes

Modifiez `telegram_bot.py:send_buy_alert()` pour personnaliser le format des messages.

## 📊 Monitoring et logs

- Logs dans `bot.log`
- Nettoyage automatique des anciennes transactions
- Gestion d'erreurs et retry automatique

## 🚀 Déploiement

### Heroku
```bash
# Ajouter les fichiers Heroku
echo "python-3.11.0" > runtime.txt
echo "web: python main.py" > Procfile

# Déployer
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
git push heroku main
```

### VPS/Server
```bash
# Avec systemd
sudo cp alertbot.service /etc/systemd/system/
sudo systemctl enable alertbot
sudo systemctl start alertbot
```

### Railway
```bash
# Deploy to Railway
railway login
railway init
railway add
railway deploy
```

## 🔍 Troubleshooting

### Erreurs courantes

**Bot ne répond pas**
- Vérifiez le token Telegram
- Vérifiez les permissions du bot dans le groupe

**Pas d'alertes**
- Vérifiez la configuration avec `/status`
- Vérifiez les logs pour erreurs API
- Vérifiez le seuil minimum configuré

**Erreurs de permission**
- Le bot doit être admin ou avoir permission d'écrire
- Commandes setup réservées aux admins du groupe

### Debug

```bash
# Lancer en mode debug
LOG_LEVEL=DEBUG python main.py

# Vérifier la base de données
sqlite3 bot_data.db ".tables"
sqlite3 bot_data.db "SELECT * FROM group_configs;"
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

- Issues GitHub : [Lien vers repo]
- Documentation : Ce README
- Contact : [Votre contact]

## 🎯 Roadmap

- [ ] Support de plus de DEX
- [ ] Alertes pour les ventes importantes
- [ ] Dashboard web administrateur
- [ ] Intégration WhatsApp/Discord
- [ ] Alertes par webhook
- [ ] Système de référral pour créateurs

---

**Fait avec ❤️ pour la communauté Starknet**