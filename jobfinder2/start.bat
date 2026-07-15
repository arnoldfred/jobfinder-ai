@echo off
echo ============================================================
echo  JobFinder AI — Demarrage
echo ============================================================

:: Activer le venv si present
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Installer setuptools EN PREMIER (fix distutils Python 3.12)
echo [1/4] Installation de setuptools (fix Python 3.12)...
pip install setuptools --quiet

:: Installer les autres dependances
echo [2/4] Installation des dependances...
pip install -r requirements.txt --quiet

:: Migrations
echo [3/4] Migrations base de donnees...
python manage.py migrate

:: Donnees de demo (si besoin)
:: python manage.py seed_data

echo [4/4] Demarrage du serveur...
echo  Acces : http://127.0.0.1:8000
python manage.py runserver
