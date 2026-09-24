"""Dựng video ngắn 9:16 (Reels / video Facebook) từ bộ ảnh đã thiết kế, bằng ffmpeg.

Mỗi ảnh hiện ~2,8 giây với hiệu ứng phóng to chậm, chuyển cảnh mềm giữa các ảnh, nhạc nền tuỳ chọn
(file .mp3 bạn có quyền sử dụng, đặt trong MUSIC_DIR). Video 10-15 giây, H.264, phát được trên mọi điện thoại.
"""
import random
import shutil
import subprocess
from pathlib import Path

from app import config

FPS = 30
TRANSITIONS = ["fade", "smoothleft", "slideup", "circleopen", "wipeleft", "smoothup"]


def ffmpeg_exe() -> str:
    """ffmpeg của hệ thống, hoặc bản đóng gói sẵn trong thư viện imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def pick_music(seed: int = 0) -> str | None:
    folder = Path(config.MUSIC_DIR)
    tracks = sorted(folder.glob("*.mp3")) + sorted(folder.glob("*.m4a")) if folder.exists() else []
    return str(random.Random(seed).choice(tracks)) if tracks else None


def make_video(slides: list[str], out_path: str, variant: int = 0, seconds: float = 2.8, fade: float = 0.5,
               music: str | None = None, min_total: float = 10.0) -> str:
    """Ghép các ảnh 1080x1920 thành video mp4 (tối thiểu ~10 giây). Trả về đường dẫn video."""
    if not slides:
        raise ValueError("Không có ảnh để dựng video")
    n = len(slides)
    seconds = max(seconds, (min_total + fade * (n - 1)) / n)   # ít ảnh thì mỗi ảnh hiện lâu hơn
    frames = int(seconds * FPS)
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error"]
    for path in slides:
        cmd += ["-i", path]
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    parts = []
    for i in range(len(slides)):
        # phóng to chậm 0% -> 6%, lần lượt tâm / lệch để chuyển động tự nhiên
        zoom = "min(zoom+0.0007,1.06)" if i % 2 == 0 else "if(eq(on,0),1.06,max(zoom-0.0007,1.0))"
        parts.append(
            f"[{i}:v]scale=1188:2112,zoompan=z='{zoom}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":s=1080x1920:fps={FPS},setsar=1,format=yuv420p[v{i}]")
    last, offset = "v0", 0.0
    for i in range(1, len(slides)):
        offset += seconds - fade
        transition = TRANSITIONS[(variant + i) % len(TRANSITIONS)]
        parts.append(f"[{last}][v{i}]xfade=transition={transition}:duration={fade}:offset={offset:.2f}[x{i}]")
        last = f"x{i}"
    total = seconds * len(slides) - fade * (len(slides) - 1)
    audio_idx = len(slides)
    parts.append(f"[{audio_idx}:a]volume=0.6,afade=t=out:st={max(0, total - 1):.2f}:d=1,"
                 f"atrim=0:{total:.2f}[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{last}]", "-map", "[a]",
            "-t", f"{total:.2f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Dựng video lỗi: {result.stderr.strip()[-400:]}")
    return out_path


def probe_duration(path: str) -> float:
    """Độ dài video (giây), dùng để kiểm tra."""
    result = subprocess.run([ffmpeg_exe(), "-i", path], capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def has_audio(path: str) -> bool:
    result = subprocess.run([ffmpeg_exe(), "-i", path], capture_output=True, text=True)
    return "Audio:" in result.stderr


def animate_still(image: str, out_path: str, seconds: float = 8.0) -> str:
    """Chuyển động nhẹ 1 ảnh tĩnh (dùng giả lập Veo ở chế độ DEMO)."""
    frames = int(seconds * FPS)
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", image,
           "-vf", f"scale=1188:2112,zoompan=z='min(zoom+0.0009,1.1)':d={frames}:x='iw/2-(iw/zoom/2)'"
                  f":y='ih/2-(ih/zoom/2)+on*0.15':s=720x1280:fps={FPS},format=yuv420p",
           "-t", f"{seconds}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Dựng video lỗi: {result.stderr.strip()[-300:]}")
    return out_path


def compose_ad(clip: str, overlay_png: str, end_card: str, out_path: str, keep_audio: bool = False,
               music: str | None = None, end_seconds: float = 3.0, fade: float = 0.5) -> str:
    """Video quảng cáo hoàn chỉnh: clip AI (Veo) + lớp chữ (tiêu đề, giá) + cảnh cuối kêu gọi mua."""
    clip_len = probe_duration(clip)
    if clip_len <= 0:
        raise RuntimeError("Không đọc được video từ AI")
    total = clip_len + end_seconds - fade
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", clip, "-i", overlay_png,
           "-loop", "1", "-t", f"{end_seconds}", "-i", end_card]
    use_clip_audio = keep_audio and has_audio(clip)
    if not use_clip_audio:
        if music:
            cmd += ["-stream_loop", "-1", "-i", music]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    graph = [
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[c]",
        "[c][1:v]overlay=0:0,format=yuv420p[v0]",
        "[2:v]scale=1080:1920,fps=30,setsar=1,format=yuv420p[v1]",
        f"[v0][v1]xfade=transition=fade:duration={fade}:offset={clip_len - fade:.2f}[v]",
    ]
    audio_in = "0:a" if use_clip_audio else "3:a"
    graph.append(f"[{audio_in}]apad,atrim=0:{total:.2f},afade=t=out:st={max(0, total - 1):.2f}:d=1[a]")
    cmd += ["-filter_complex", ";".join(graph), "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Ghép video lỗi: {result.stderr.strip()[-400:]}")
    return out_path
