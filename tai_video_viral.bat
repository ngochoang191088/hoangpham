@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tai video viral TikTok / Douyin
echo === Quet kenh TikTok / Douyin / YouTube Shorts, tai video viral ===
echo.
call _chuan_bi.bat || goto :loi

rem TikTok hay doi cach chong tai: cap nhat yt-dlp moi lan chay
pip install -U -q yt-dlp --disable-pip-version-check

if not exist kenh.txt (
  python -m app.viral_clips kenh.txt >nul
  echo Da tao file kenh.txt va mo bang Notepad.
  echo Dan link cac kenh vao ^(moi dong 1 kenh^), LUU file, dong Notepad
  echo roi nhay dup lai file tai_video_viral.bat.
  start "" notepad kenh.txt
  goto :ketthuc
)
findstr /i "douyin.com" kenh.txt >nul && (
  python -c "import playwright" >nul 2>nul || (
    echo Cai thu vien dieu khien trinh duyet cho Douyin lan dau...
    pip install playwright --disable-pip-version-check || goto :loi
  )
)

python -m app.viral_clips kenh.txt %* || goto :loi
echo %* | find /i "--tu-dong" >nul && exit /b 0
start "" explorer video_viral
goto :ketthuc

:loi
echo.
echo [LOI] Co loi o tren. CHUP MAN HINH cua so nay gui lai.
echo %* | find /i "--tu-dong" >nul && exit /b 1

:ketthuc
pause
