@echo off
chcp 65001 >nul
cd /d "%~dp0"
title San san pham aff Shopee
echo === San san pham Shopee hoa hong cao, ban chay va lay link aff ===
echo.
call _chuan_bi.bat || goto :loi

if not exist tu_khoa.txt (
  python -m app.aff_hunter tu_khoa.txt --demo >nul
  echo Da tao file tu_khoa.txt ^(tu khoa mau theo nganh hang^) va mo bang Notepad.
  echo Sua tu khoa cho dung nganh ban chay, LUU file, roi nhay dup lai file nay.
  start "" notepad tu_khoa.txt
  goto :ketthuc
)

python -m app.aff_hunter tu_khoa.txt %*
if errorlevel 1 goto :loi
echo %* | find /i "--tu-dong" >nul && exit /b 0
start "" explorer san_pham_aff
goto :ketthuc

:loi
echo.
echo Xem huong dan / loi o tren.
echo %* | find /i "--tu-dong" >nul && exit /b 1

:ketthuc
pause
