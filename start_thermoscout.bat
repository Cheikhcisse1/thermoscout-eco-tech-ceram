@echo off
rem Lance ThermoScout en continu: redemarre automatiquement s'il s'arrete.
cd /d "%~dp0"
title ThermoScout - http://127.0.0.1:8780
start "" http://127.0.0.1:8780
:loop
echo [%date% %time%] Demarrage de ThermoScout...
".venv\Scripts\python.exe" -m uvicorn server:app --host 127.0.0.1 --port 8780
echo [%date% %time%] Arret, redemarrage dans 5 s... (Ctrl+C pour quitter)
timeout /t 5 /nobreak >nul
goto loop
