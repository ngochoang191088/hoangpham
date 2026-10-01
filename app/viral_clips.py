"""Tool săn video viral: quét các kênh TikTok / Douyin / YouTube Shorts, chấm điểm, tải video viral về máy.

Cách dùng (Windows: nháy đúp tai_video_viral.bat):
    python -m app.viral_clips kenh.txt                  # quét + tải 80 clip viral nhất
    python -m app.viral_clips kenh.txt --so-clip 40     # số clip mỗi lần
    python -m app.viral_clips kenh.txt --chi-quet       # chỉ chấm điểm, ghi danh sách, không tải

File kenh.txt: mỗi dòng 1 link kênh, dòng [Tên nhóm] để chia thư mục:
    [Thú cưng]
    https://www.tiktok.com/@ten_kenh
    https://www.douyin.com/user/MS4wLjABAAAA...
    https://www.tiktok.com/tag/meocute
    [Nấu ăn]
    https://www.youtube.com/@ten_kenh/shorts

Cách chấm "viral": so lượt xem của từng video với lượt xem điển hình (trung vị) của chính kênh đó.
Video gấp 5 lần mức thường của kênh là đang viral, dù kênh nhỏ hay lớn. Có cộng điểm khi tỷ lệ
thích / bình luận / chia sẻ cao. Douyin không công khai lượt xem nên dùng lượt thích.

Kết quả: video_viral/<ngày>/<nhóm>/01_tiktok_<tác giả>_<id>.mp4 ... và video_viral/<ngày>/danh_sach.csv
(link gốc, tác giả, lượt xem, điểm). Video đã tải sẽ không tải lại vào các ngày sau (video_viral/da_tai.txt).
"""
import argparse
import csv
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path


DOUYIN_USER_RE = re.compile(r"douyin\.com/user/([\w-]+)", re.I)
VIDEO_EXT = ".mp4"


# ---------------------------------------------------------------- đọc danh sách kênh

def read_channels(path: Path) -> list[tuple[str, str]]:
    """[(nhóm, link kênh)] theo thứ tự trong file. Dòng # là ghi chú."""
    group, channels = "Chung", []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            group = m.group(1).strip()
            continue
        url = line.split()[0]
        if url.startswith("@"):                                   # gõ tắt @ten_kenh = kênh TikTok
            url = f"https://www.tiktok.com/{url}"
        if url.startswith("http"):
            channels.append((group, url))
    return list(dict.fromkeys(channels))


def platform_of(url: str) -> str:
    u = url.lower()
    if "douyin.com" in u:
        return "douyin"
    if "tiktok.com" in u:
        return "tiktok"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    return "khac"


def safe_name(text: str, limit: int = 40) -> str:
    text = re.sub(r'[\\/:*?"<>|\r\n\t#]+', " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()[:limit]
    return text.rstrip(". ") or "video"


# ---------------------------------------------------------------- lấy danh sách video của kênh

def _normalize(entry: dict, platform: str, channel: str, group: str) -> dict | None:
    vid = str(entry.get("id") or "")
    url = entry.get("webpage_url") or entry.get("url") or ""
    if not vid or not url.startswith("http"):
        return None
    return {
        "platform": platform, "id": vid, "url": url, "group": group, "channel": channel,
        "author": entry.get("uploader") or entry.get("channel") or entry.get("creator") or "",
        "title": (entry.get("description") or entry.get("title") or "").replace("\n", " ")[:300],
        "views": entry.get("view_count") or 0, "likes": entry.get("like_count") or 0,
        "comments": entry.get("comment_count") or 0, "shares": entry.get("repost_count") or 0,
        "timestamp": entry.get("timestamp") or 0, "duration": entry.get("duration") or 0,
    }


def list_ytdlp(url: str, group: str, limit: int, cookiefile: str | None) -> list[dict]:
    """Video mới nhất của kênh TikTok / YouTube (hoặc hashtag, âm thanh...) qua yt-dlp."""
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": "in_playlist",
            "playlistend": limit, "ignoreerrors": True}
    if cookiefile:
        opts["cookiefile"] = cookiefile
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False) or {}
    entries = info.get("entries") or ([info] if info.get("id") else [])
    platform = platform_of(url)
    return [v for e in entries if e for v in [_normalize(e, platform, url, group)] if v][:limit]


class DouyinBrowser:
    """Mở kênh Douyin bằng Edge / Chrome có sẵn trên máy, đọc danh sách video Douyin trả về cho trang.

    Dùng hồ sơ trình duyệt riêng (data/douyin_profile): lần đầu Douyin đòi đăng nhập / xác minh thì
    làm ngay trong cửa sổ đó, các lần sau dùng lại.
    """

    def __init__(self, profile_dir: Path, interactive: bool = True):
        self.interactive = interactive
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise SystemExit("Quét Douyin cần thư viện playwright: pip install playwright")
        self._pw = sync_playwright().start()
        last_error = None
        for channel in ("msedge", "chrome", None):
            try:
                self.ctx = self._pw.chromium.launch_persistent_context(
                    str(profile_dir), channel=channel, headless=False, locale="zh-CN",
                    viewport={"width": 1280, "height": 900})
                break
            except Exception as e:  # noqa: BLE001 - không có Edge thì thử Chrome
                last_error = e
        else:
            raise SystemExit(f"Không mở được Edge / Chrome: {last_error}")
        self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
        self.download_urls: dict[str, list[str]] = {}

    def list_videos(self, url: str, group: str, limit: int) -> list[dict]:
        items: list[dict] = []

        def on_response(resp):
            if "/aweme/v1/web/aweme/post" in resp.url:
                try:
                    items.extend(resp.json().get("aweme_list") or [])
                except Exception:  # noqa: BLE001
                    pass

        self.page.on("response", on_response)
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            for _ in range(8):                                    # cuộn để Douyin tải thêm video
                if len(items) >= limit:
                    break
                self.page.wait_for_timeout(2500)
                self.page.mouse.wheel(0, 3000)
            if not items and self.interactive:
                print("   Douyin chưa trả danh sách video. Nếu cửa sổ trình duyệt đòi đăng nhập / xác minh,"
                      " hãy làm xong rồi bấm Enter ở đây (bỏ qua kênh này: gõ s rồi Enter)...")
                if input().strip().lower() != "s":
                    self.page.reload(wait_until="domcontentloaded")
                    self.page.wait_for_timeout(5000)
        finally:
            self.page.remove_listener("response", on_response)
        return [v for a in items[:limit] for v in [self._normalize(a, url, group)] if v]

    def _normalize(self, aweme: dict, channel: str, group: str) -> dict | None:
        vid = str(aweme.get("aweme_id") or "")
        if not vid or aweme.get("images"):                       # bỏ bài dạng ảnh
            return None
        stats = aweme.get("statistics") or {}
        video = aweme.get("video") or {}
        self.download_urls[vid] = [u for k in ("play_addr", "download_addr")
                                   for u in (video.get(k) or {}).get("url_list") or []]
        duration = video.get("duration") or aweme.get("duration") or 0
        return {
            "platform": "douyin", "id": vid, "url": f"https://www.douyin.com/video/{vid}", "group": group,
            "channel": channel, "author": (aweme.get("author") or {}).get("nickname", ""),
            "title": (aweme.get("desc") or "").replace("\n", " ")[:300],
            "views": stats.get("play_count") or 0, "likes": stats.get("digg_count") or 0,
            "comments": stats.get("comment_count") or 0, "shares": stats.get("share_count") or 0,
            "timestamp": aweme.get("create_time") or 0,
            "duration": duration / 1000 if duration > 1000 else duration,
        }

    def download(self, video: dict, dest: Path) -> bool:
        for src in self.download_urls.get(video["id"], []):
            try:
                resp = self.ctx.request.get(src, headers={"Referer": "https://www.douyin.com/"}, timeout=120000)
                body = resp.body() if resp.ok else b""
                if len(body) > 50_000:
                    dest.write_bytes(body)
                    return True
            except Exception:  # noqa: BLE001 - thử link dự phòng
                continue
        return False

    def close(self):
        self.ctx.close()
        self._pw.stop()


# ---------------------------------------------------------------- chấm điểm viral

def metric(v: dict) -> int:
    """Chỉ số so sánh: lượt xem; Douyin (không công khai lượt xem) dùng lượt thích x 10."""
    return v["views"] or v["likes"] * 10


def score_videos(videos: list[dict], now: float, days: int, min_views: int, max_seconds: int) -> list[dict]:
    """Gắn điểm viral cho từng video, bỏ video quá cũ / quá ít xem / quá dài."""
    by_channel: dict[str, list[int]] = {}
    for v in videos:
        by_channel.setdefault(v["channel"], []).append(metric(v))
    scored = []
    for v in videos:
        value = metric(v)
        if v["timestamp"] and now - v["timestamp"] > days * 86400:
            continue
        if value < min_views or (max_seconds and v["duration"] and v["duration"] > max_seconds):
            continue
        typical = statistics.median(by_channel[v["channel"]]) or 1
        ratio = value / typical
        base = v["views"] or v["likes"] * 10 or 1
        engagement = (v["likes"] + 2 * v["comments"] + 3 * v["shares"]) / base
        age_hours = max((now - v["timestamp"]) / 3600, 1) if v["timestamp"] else 24 * days
        scored.append({**v, "ratio": round(ratio, 2), "engagement": round(engagement, 4),
                       "per_hour": int(value / age_hours),
                       "score": round(ratio * (1 + min(engagement, 0.5) * 4), 2)})
    return sorted(scored, key=lambda v: (v["score"], metric(v)), reverse=True)


def pick(scored: list[dict], total: int, per_channel: int, done: set[str]) -> list[dict]:
    """Chọn video điểm cao nhất, mỗi kênh tối đa `per_channel` video, bỏ video đã tải."""
    chosen, count = [], {}
    for v in scored:
        key = f"{v['platform']}:{v['id']}"
        if key in done or count.get(v["channel"], 0) >= per_channel:
            continue
        chosen.append(v)
        count[v["channel"]] = count.get(v["channel"], 0) + 1
        if len(chosen) >= total:
            break
    return chosen


# ---------------------------------------------------------------- tải video

def download_ytdlp(video: dict, dest: Path, cookiefile: str | None) -> bool:
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "no_warnings": True, "outtmpl": str(dest.with_suffix(".%(ext)s")),
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b", "merge_output_format": "mp4",
            "noplaylist": True, "retries": 3}
    try:
        import imageio_ffmpeg

        opts["ffmpeg_location"] = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001 - không có ffmpeg vẫn tải được định dạng đơn
        pass
    if cookiefile:
        opts["cookiefile"] = cookiefile
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([video["url"]])
    except Exception:  # noqa: BLE001
        return False
    return any(dest.parent.glob(dest.stem + ".*"))


def load_done(path: Path) -> set[str]:
    return set(path.read_text(encoding="utf-8").split()) if path.exists() else set()


def run(channels: list[tuple[str, str]], out_dir: Path, total: int = 80, days: int = 7, per_scan: int = 30,
        per_channel: int = 5, min_views: int = 10000, max_seconds: int = 0, cookiefile: str | None = None,
        scan_only: bool = False, now: float | None = None, log=print, douyin=None,
        interactive: bool = True) -> list[dict]:
    """Quét tất cả kênh, chấm điểm, tải `total` video viral nhất. Trả về danh sách video đã chọn."""
    now = now or time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    done_file = out_dir / "da_tai.txt"
    done = load_done(done_file)
    videos: list[dict] = []
    try:
        for i, (group, url) in enumerate(channels, 1):
            log(f"[{i}/{len(channels)}] Quét {url}")
            try:
                if platform_of(url) == "douyin" and DOUYIN_USER_RE.search(url):
                    if douyin is None:
                        douyin = DouyinBrowser(out_dir.parent / "data" / "douyin_profile", interactive)
                    found = douyin.list_videos(url, group, per_scan)
                else:
                    found = list_ytdlp(url, group, per_scan, cookiefile)
            except SystemExit:
                raise
            except Exception as e:  # noqa: BLE001 - 1 kênh lỗi không làm dừng cả lượt
                log(f"   LỖI: {e}")
                continue
            log(f"   {len(found)} video")
            videos += found

        chosen = pick(score_videos(videos, now, days, min_views, max_seconds), total, per_channel, done)
        day_dir = out_dir / datetime.fromtimestamp(now).strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        log(f"\nChọn {len(chosen)} video viral nhất trong {len(videos)} video đã quét.")
        for rank, v in enumerate(chosen, 1):
            folder = day_dir / safe_name(v["group"])
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / f"{rank:02d}_{v['platform']}_{safe_name(v['author'], 20)}_{v['id']}{VIDEO_EXT}"
            v["file"] = ""
            if scan_only:
                continue
            ok = douyin.download(v, dest) if (v["platform"] == "douyin" and douyin) else \
                download_ytdlp(v, dest, cookiefile)
            if ok:
                v["file"] = str(next(dest.parent.glob(dest.stem + ".*"), dest))
                with done_file.open("a", encoding="utf-8") as fh:
                    fh.write(f"{v['platform']}:{v['id']}\n")
            log(f"   {rank:02d}. {'OK ' if ok else 'LỖI'} x{v['ratio']} | {metric(v):,} | {v['author']} | {v['url']}")
            time.sleep(1)
    finally:
        if douyin is not None and hasattr(douyin, "close"):
            douyin.close()
    _write_csv(day_dir / "danh_sach.csv", chosen)
    return chosen


def _write_csv(path: Path, videos: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Hạng", "Nhóm", "Nền tảng", "Tác giả", "Link gốc", "Lượt xem", "Lượt thích", "Bình luận",
                    "Chia sẻ", "Gấp x lần mức thường của kênh", "Điểm", "Ngày đăng", "Giây", "Nội dung", "File"])
        for rank, v in enumerate(videos, 1):
            posted = datetime.fromtimestamp(v["timestamp"]).strftime("%Y-%m-%d %H:%M") if v["timestamp"] else ""
            w.writerow([rank, v["group"], v["platform"], v["author"], v["url"], v["views"], v["likes"],
                        v["comments"], v["shares"], v["ratio"], v["score"], posted, int(v["duration"] or 0),
                        v["title"], v.get("file", "")])


SAMPLE = """# Mỗi dòng 1 kênh (TikTok, Douyin, YouTube Shorts) hoặc hashtag TikTok.
# Dòng [Tên nhóm] để chia video vào thư mục theo nhóm. Dòng bắt đầu bằng # là ghi chú.
[Thú cưng]
# https://www.tiktok.com/@ten_kenh
# https://www.tiktok.com/tag/meocute
# https://www.douyin.com/user/MS4wLjABAAAA...
[Nấu ăn]
# https://www.youtube.com/@ten_kenh/shorts
"""


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Quét kênh TikTok / Douyin / YouTube Shorts, tải video viral.")
    p.add_argument("file", nargs="?", default="kenh.txt", help="file danh sách kênh (mặc định kenh.txt)")
    p.add_argument("--out", default="video_viral", help="thư mục lưu video (mặc định video_viral)")
    p.add_argument("--so-clip", type=int, default=80, help="số clip tải mỗi lần (mặc định 80)")
    p.add_argument("--ngay", type=int, default=7, help="chỉ lấy video đăng trong N ngày gần đây (mặc định 7)")
    p.add_argument("--moi-kenh", type=int, default=30, help="số video mới nhất xem ở mỗi kênh (mặc định 30)")
    p.add_argument("--toi-da-moi-kenh", type=int, default=5, help="tối đa bao nhiêu clip mỗi kênh (mặc định 5)")
    p.add_argument("--min-view", type=int, default=10000, help="bỏ video dưới số lượt xem này (mặc định 10000)")
    p.add_argument("--max-giay", type=int, default=0, help="bỏ video dài hơn N giây (0 = không giới hạn)")
    p.add_argument("--cookies", default="", help="file cookies.txt (mặc định tự dùng cookies.txt nếu có)")
    p.add_argument("--chi-quet", action="store_true", help="chỉ chấm điểm và ghi danh sách, không tải video")
    p.add_argument("--tu-dong", action="store_true", help="chạy theo lịch: không dừng chờ đăng nhập Douyin")
    args = p.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        path.write_text(SAMPLE, encoding="utf-8")
        print(f"Đã tạo file {path}. Mở file, dán link các kênh vào (mỗi dòng 1 kênh), lưu lại rồi chạy lại.")
        return 1
    channels = read_channels(path)
    if not channels:
        print(f"Chưa có kênh nào trong {path} (dòng bắt đầu bằng # là ghi chú, hãy bỏ dấu # đi).")
        return 1
    cookiefile = args.cookies or ("cookies.txt" if Path("cookies.txt").exists() else None)
    print(f"Quét {len(channels)} kênh, tải tối đa {args.so_clip} clip viral...\n")
    chosen = run(channels, Path(args.out), args.so_clip, args.ngay, args.moi_kenh, args.toi_da_moi_kenh,
                 args.min_view, args.max_giay, cookiefile, args.chi_quet, interactive=not args.tu_dong)
    ok = sum(1 for v in chosen if v.get("file"))
    if args.chi_quet:
        print(f"\nXong: đã chấm điểm, danh sách {len(chosen)} video trong {args.out}/<ngày>/danh_sach.csv")
    else:
        print(f"\nXong: tải được {ok}/{len(chosen)} clip vào {args.out}/<ngày>/ (xem danh_sach.csv)")
    if len(chosen) < args.so_clip:
        print(f"Chỉ tìm được {len(chosen)} clip đạt chuẩn. Thêm kênh vào {path}, hoặc nới điều kiện"
              f" (--ngay 14, --min-view 5000, --toi-da-moi-kenh 8).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
