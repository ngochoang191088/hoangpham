@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem Chay ca 2 tool, dung cho lich hang ngay (cai bang cai_lich_hang_ngay.bat)
echo [%date% %time%] Bat dau >> nhat_ky_hang_ngay.txt
call san_aff_shopee.bat --tu-dong >> nhat_ky_hang_ngay.txt 2>&1
call tai_video_viral.bat --tu-dong >> nhat_ky_hang_ngay.txt 2>&1
echo [%date% %time%] Xong >> nhat_ky_hang_ngay.txt
