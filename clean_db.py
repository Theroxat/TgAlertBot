#!/usr/bin/env python3
"""
Script pour nettoyer la base de données
"""

import sqlite3
import os

def clean_database():
    """Nettoie toutes les tables de la base de données"""
    db_path = "./bot_data.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Supprimer toutes les données des tables
            cursor.execute("DELETE FROM group_configs")
            cursor.execute("DELETE FROM last_transactions") 
            cursor.execute("DELETE FROM group_admins")
            
            conn.commit()
            
            print("Base de donnees nettoyee avec succes!")
            print("Toutes les configurations de groupes ont ete supprimees")
            print("Toutes les transactions suivies ont ete supprimees")
            print("Toutes les permissions admin ont ete supprimees")
            
    except Exception as e:
        print(f"Erreur lors du nettoyage: {e}")

if __name__ == "__main__":
    clean_database()