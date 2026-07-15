#!/usr/bin/env python
"""
Script pour migrer les données de SQLite vers MySQL
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobfinder.settings')
django.setup()

from django.db import connections
from django.apps import apps

# Sources et destination
SOURCE_DB = 'sqlite'
TARGET_DB = 'mysql'

# Configurer les deux bases de données
DATABASES = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jobfinder_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Mettre à jour settings
from django.conf import settings
if hasattr(settings, 'DATABASES'):
    settings.DATABASES[SOURCE_DB] = DATABASES['sqlite']
    settings.DATABASES[TARGET_DB] = DATABASES['mysql']

# Récupérer les modèles et copier les données
from django.apps import apps

def copy_app_data(app_name):
    """Copier les donnees d'une app particulière"""
    print(f"\n=== Copie de l'app '{app_name}' ===")
    app_config = apps.get_app_config(app_name)
    
    for model in app_config.get_models():
        # Lire depuis SQLite
        sqlite_connection = connections[SOURCE_DB]
        with sqlite_connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM {model._meta.db_table}')
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        if not rows:
            print(f"  • {model._meta.verbose_name}: 0 enregistrements")
            continue
        
        # Écrire dans MySQL
        mysql_connection = connections[TARGET_DB]
        cursor_mysql = mysql_connection.cursor()
        
        placeholders = ', '.join(['%s'] * len(columns))
        column_names = ', '.join([f'`{col}`' for col in columns])
        sql = f'INSERT INTO {model._meta.db_table} ({column_names}) VALUES ({placeholders})'
        
        try:
            cursor_mysql.executemany(sql, rows)
            mysql_connection.commit()
            print(f"  • {model._meta.verbose_name}: {len(rows)} enregistrements copiés")
        except Exception as e:
            mysql_connection.rollback()
            print(f"  ✗ Erreur: {e}")
        finally:
            cursor_mysql.close()

if __name__ == '__main__':
    print("🔄 Début de la migration SQLite → MySQL...")
    
    # Apps à copier
    APPS = ['accounts', 'jobs', 'employers', 'applications', 'core']
    
    for app in APPS:
        try:
            copy_app_data(app)
        except Exception as e:
            print(f"Erreur pour {app}: {e}")
    
    print("\n✅ Migration terminée!")
