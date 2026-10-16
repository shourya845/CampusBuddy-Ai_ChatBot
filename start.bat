@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist .env copy .env.example .env >nul
.venv\Scripts\python -m database.seed
if errorlevel 1 goto fail
.venv\Scripts\python -m streamlit run app.py
goto :eof
:fail
echo Setup failed. Check Python installation and internet access.
pause
