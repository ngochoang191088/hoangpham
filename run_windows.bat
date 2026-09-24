@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Aff Pages: cai dat va chay thu (DEMO) ===
where python >nul 2>nul || (echo Chua co Python. Tai Python 3.11+ tai https://www.python.org/downloads/ va tick "Add python.exe to PATH". & pause & exit /b)
if not exist .venv (python -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q || (echo Cai thu vien loi & pause & exit /b)
if not exist .env copy .env.example .env >nul
if not exist data\app.db (echo Dang tao du lieu mau, mat khoang 1-2 phut... & python -m app.demo)
echo.
echo Mo trinh duyet: http://localhost:8000   (mat khau demo: xem ADMIN_PASSWORD trong file .env)
start "" http://localhost:8000
python -m uvicorn app.main:app --port 8000
pause
