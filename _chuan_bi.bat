@echo off
rem Dung chung cho cac tool: tim Python, tao moi truong rieng .venv, cai thu vien neu thieu.
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [LOI] Chua cai Python. Tai tai https://www.python.org/downloads/
  echo Khi cai nho tick o "Add python.exe to PATH".
  exit /b 1
)
if not exist .venv (
  echo Tao moi truong Python rieng lan dau...
  %PY% -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat
python -c "import httpx, PIL, openpyxl, docx, yt_dlp, imageio_ffmpeg" >nul 2>nul || (
  echo Cai thu vien lan dau, co the mat vai phut...
  pip install -r requirements.txt --disable-pip-version-check || exit /b 1
)
if not exist .env if exist .env.example copy .env.example .env >nul
exit /b 0
