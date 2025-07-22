#!/usr/bin/env python3
"""
Script pour vérifier le contenu de la base de données
"""

import sqlite3

def check_database():
    """Vérifie le contenu de la base de données"""
    db_path = "./bot_data.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier les configs de groupes
            cursor.execute("SELECT * FROM group_configs")
            configs = cursor.fetchall()
            
            print(f"=== CONFIGURATIONS DE GROUPES ({len(configs)} trouvées) ===")
            for config in configs:
                print(f"Chat ID: {config[0]}")
                print(f"Token: {config[1]}")
                print(f"Symbol: {config[2]}")
                print(f"DEX: {config[3]}")
                print(f"Supply: {config[4]}")
                print(f"Threshold: {config[5]}")
                print(f"Active: {config[7]}")
                print("---")
            
            # Vérifier les transactions
            cursor.execute("SELECT * FROM last_transactions")
            transactions = cursor.fetchall()
            
            print(f"=== TRANSACTIONS SUIVIES ({len(transactions)} trouvées) ===")
            for tx in transactions:
                print(f"Chat ID: {tx[0]}, TX Hash: {tx[1]}")
            
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_database()