#!/usr/bin/env bash
# Aff Pages: cài đặt và chạy thử (DEMO). Chạy: bash run_mac_linux.sh
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Chưa có Python 3.11+: https://www.python.org/downloads/"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
[ -f .env ] || cp .env.example .env
[ -f data/app.db ] || { echo "Đang tạo dữ liệu mẫu (1-2 phút)..."; python -m app.demo; }
echo "Mở trình duyệt: http://localhost:8000  (mật khẩu demo: ADMIN_PASSWORD trong file .env)"
( sleep 2; (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null) ) &
python -m uvicorn app.main:app --port 8000
