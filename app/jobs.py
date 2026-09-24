"""Chạy việc tự động từ dòng lệnh (dùng cho cron).

    python -m app.jobs hunt       # săn sản phẩm (1 lần/ngày)
    python -m app.jobs media      # tạo bộ ảnh + video cho sản phẩm mới (trước khi tạo bài)
    python -m app.jobs drafts     # tạo bài nháp cho ngày mai (1 lần/ngày)
    python -m app.jobs publish    # đăng bài đến giờ (mỗi 5 phút)
    python -m app.jobs sync       # cập nhật số liệu (mỗi 1-3 giờ)
    python -m app.jobs pages      # đồng bộ danh sách page từ Meta Business
"""
import sys

from app import db
from app.services import pipeline

JOBS = {
    "hunt": pipeline.hunt_products,
    "media": pipeline.build_media,
    "drafts": pipeline.generate_drafts,
    "publish": pipeline.publish_due,
    "sync": pipeline.sync_metrics,
    "pages": pipeline.import_pages,
}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in JOBS:
        print(__doc__)
        sys.exit(1)
    db.init_db()
    with db.get_conn() as conn:
        print(JOBS[sys.argv[1]](conn))


if __name__ == "__main__":
    main()
