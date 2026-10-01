@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Cai lich chay tu dong moi ngay (san link aff + tai video viral) ===
echo.
set "GIO=07:00"
set /p "GIO=Chay luc may gio moi ngay? (Enter = 07:00, vi du 06:30): "
schtasks /create /tn "hwangzada - chay hang ngay" /tr "\"%~dp0chay_hang_ngay.bat\"" /sc daily /st %GIO% /f
if errorlevel 1 (
  echo [LOI] Khong cai duoc lich. Thu chuot phai file nay, chon "Run as administrator".
) else (
  echo.
  echo Da cai: moi ngay luc %GIO% may tu chay. May phai dang bat va dang dang nhap Windows.
  echo Ket qua: thu muc san_pham_aff va video_viral, nhat ky: nhat_ky_hang_ngay.txt
  echo Muon go lich: mo Task Scheduler, xoa muc "hwangzada - chay hang ngay".
)
pause
