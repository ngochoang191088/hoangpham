@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tai anh san pham Shopee
echo === Tai anh san pham Shopee: moi san pham 1 thu muc ===
echo.

set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [LOI] Chua cai Python. Tai tai https://www.python.org/downloads/
  echo Khi cai nho tick o "Add python.exe to PATH".
  pause
  exit /b
)

if not exist .venv (
  echo Tao moi truong Python rieng lan dau...
  %PY% -m venv .venv || (echo [LOI] Khong tao duoc moi truong Python & pause & exit /b)
)
call .venv\Scripts\activate.bat
python -c "import httpx, PIL, openpyxl, docx" >nul 2>nul || (
  echo Cai thu vien lan dau, co the mat vai phut...
  pip install -r requirements.txt --disable-pip-version-check || goto :loi
)

rem Che do trinh duyet (--browser) can them thu vien playwright, dung Edge / Chrome co san tren may
echo %* | find /i "--browser" >nul && (
  python -c "import playwright" >nul 2>nul || (
    echo Cai thu vien dieu khien trinh duyet lan dau...
    pip install playwright --disable-pip-version-check || goto :loi
  )
)

if not exist danh_sach_link.txt (
  python -m app.scan_images danh_sach_link.txt >nul
  echo Da tao file danh_sach_link.txt va mo bang Notepad.
  echo Dan link san pham Shopee vao ^(moi dong 1 link^), LUU file, dong Notepad
  echo roi nhay dup lai file tai_anh_shopee.bat.
  start "" notepad danh_sach_link.txt
  goto :ketthuc
)

python -m app.scan_images danh_sach_link.txt %* || goto :loi
echo.
echo Mo thu muc anh...
start "" explorer anh_san_pham
goto :ketthuc

:loi
echo.
echo ============================================================
echo [LOI] Co loi o tren. CHUP MAN HINH cua so nay gui lai.
echo ============================================================

:ketthuc
pause
