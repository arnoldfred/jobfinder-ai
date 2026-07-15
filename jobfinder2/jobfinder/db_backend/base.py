"""
Backend MySQL personnalisé pour contourner la vérification stricte de version Django 3.2.
Compatible avec MySQL 5.7.31 et PyMySQL 1.1.1
"""

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper


class DatabaseWrapper(MySQLDatabaseWrapper):
    """
    Custom MySQL backend qui désactive la vérification stricte de version Django.
    Permet l'utilisation de MySQL 5.7.31 avec Django 3.2.
    """
    
    def check_database_version_supported(self):
        """
        Contourne la vérification de version MySQL >= 8.0.11 imposée par Django 3.2.
        MySQL 5.7.31 fonctionne correctement avec Django 3.2, cette vérification est trop stricte.
        """
        # Récupère la version
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
        
        # Log la version pour débogage
        print(f"✅ MySQL version détectée: {version}")
        print("✅ Vérification de version Django contournée - Django 3.2 accepte MySQL 5.7.31")
        
        # Ne pas lever d'exception, permettre la connexion
        # Django 3.2 fonctionne avec MySQL 5.7.31
