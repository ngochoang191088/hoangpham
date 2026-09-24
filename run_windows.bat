@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Aff Pages
echo === Aff Pages: cai dat va chay thu (DEMO) ===
echo.

rem ---- Tim Python that (bo qua ban "gia" cua Microsoft Store) ----
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
  python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [LOI] Chua cai Python.
  echo Tai Python 3.11 tro len tai https://www.python.org/downloads/
  echo Khi cai nho tick o "Add python.exe to PATH", cai xong chay lai file nay.
  pause
  exit /b
)
for /f "delims=" %%v in ('%PY% --version') do echo Da tim thay %%v
echo.

if not exist .venv (
  echo [1/4] Tao moi truong Python rieng cho app...
  %PY% -m venv .venv || (echo [LOI] Khong tao duoc moi truong Python & pause & exit /b)
)
call .venv\Scripts\activate.bat

echo [2/4] Cai thu vien (lan dau mat 3-10 phut tuy mang, co thanh tien do ben duoi)...
python -m pip install --upgrade pip --disable-pip-version-check
pip install -r requirements.txt --disable-pip-version-check || goto :loi

if not exist .env copy .env.example .env >nul
if not exist data\demo_ok.txt (
  echo [3/4] Tao du lieu mau 82 page, anh va video mau: mat 1-3 phut...
  python -m app.demo || goto :loi
  echo ok> data\demo_ok.txt
)

echo.
echo [4/4] App dang chay tai: http://localhost:8000
echo       Mat khau demo: admin123  (doi trong file .env)
echo       Dong cua so nay = tat app.
echo.
start "" cmd /c "timeout /t 5 >nul & start http://localhost:8000"
python -m uvicorn app.main:app --port 8000
echo.
echo App da dung.
goto :ketthuc

:loi
echo.
echo ============================================================
echo [LOI] Co loi o tren. CHUP MAN HINH cua so nay gui lai
echo       TRUOC KHI bam phim (bam phim la cua so se dong).
echo ============================================================

:ketthuc
pause
