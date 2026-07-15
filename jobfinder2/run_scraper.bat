@echo off
REM Scraping automatique des offres d'emploi
REM Exécute le script scrape_automatically.py chaque jour

echo.
echo ========================================
echo JOBFINDER - SCRAPING AUTOMATIQUE
echo ========================================
echo.

REM Aller au répertoire du projet
cd /d e:\jobfinder_ai_v2.1\jobfinder2

REM Exécuter le scraping via le venv
e:/jobfinder_ai_v2.1/.venv/Scripts/python.exe scrape_automatically.py

REM Log en fichier
echo %date% %time% >> scraping_log.txt
e:/jobfinder_ai_v2.1/.venv/Scripts/python.exe scrape_automatically.py >> scraping_log.txt 2>&1

echo.
echo Scraping complété!
echo.
pause
