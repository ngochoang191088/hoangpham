"""Dựng video theo nhạc: bạn tải clip tự quay + 1 bài nhạc, app tự nghe nhạc và cắt ghép khớp nhịp.

Quy trình (chạy hoàn toàn trên máy, 0 token; AI chấm cảnh là tuỳ chọn):
  1. Nghe nhạc: tách nhịp (beat), tính tempo (BPM) và độ "sôi" (năng lượng) từng nhịp.
     Chọn đoạn nhạc sôi nhất (điệp khúc / đoạn drop) có độ dài bằng video cần dựng.
  2. Xem clip: lấy mẫu 4 khung hình/giây, chấm điểm độ nét, độ sáng, độ tương phản, chuyển động;
     bỏ đoạn mờ, tối, rung lắc, cảnh chuyển đột ngột. (Tuỳ chọn) Claude xem ảnh thu nhỏ và chấm thêm.
  3. Lên kịch bản cắt: đoạn nhạc sôi cắt mỗi 1 nhịp, đoạn êm cắt mỗi 2-4 nhịp; mỗi cảnh lấy
     đoạn clip đẹp nhất chưa dùng, cảnh sôi ưu tiên đoạn nhiều chuyển động.
  4. Dựng: cắt đúng số khung hình để điểm cắt rơi đúng nhịp, crop theo khổ (9:16, 1:1, 4:5, 16:9),
     chỉnh màu, nháy sáng nhẹ ở nhịp mạnh, ghép nhạc (fade vào / ra), xuất mp4 H.264.

Chạy từ dòng lệnh:
    python -m app.services.beat_editor clip1.mp4 clip2.mov --music bai_hat.mp3 --out video.mp4 \\
        --seconds 30 --aspect 9:16 --pace auto
"""
import base64
import io
import json
import random
import subprocess
from pathlib import Path

import numpy as np

from app import config
from app.services import video_maker

SR = 22050                 # tần số lấy mẫu khi phân tích nhạc
HOP = 512                  # ~23 ms mỗi bước phân tích
N_FFT = 1024
SAMPLE_FPS = 4             # số khung hình/giây lấy mẫu để chấm điểm clip
THUMB = 160                # cạnh ảnh xám thu nhỏ dùng để chấm điểm
FPS = 30
MIN_SHOT = 0.4             # cảnh ngắn nhất (giây), ngắn hơn mắt không kịp nhìn
MAX_SHOT = 4.0

MUSIC_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"}
ASPECTS = {"9:16": (1080, 1920), "4:5": (1080, 1350), "1:1": (1080, 1080), "16:9": (1920, 1080)}
ASPECT_LABELS = {"9:16": "9:16 dọc (TikTok, Reels, Shorts)", "4:5": "4:5 (bảng tin Facebook / Instagram)",
                 "1:1": "1:1 vuông", "16:9": "16:9 ngang (YouTube)"}
PACES = {"auto": "Tự động theo nhạc (sôi cắt nhanh, êm cắt chậm)", "fast": "Nhanh: mỗi nhịp 1 cảnh",
         "medium": "Vừa: 2 nhịp 1 cảnh", "slow": "Chậm: 4 nhịp 1 cảnh"}
GRADES = {
    "natural": ("Tự nhiên (tăng nhẹ độ tươi)", "eq=contrast=1.06:saturation=1.15,unsharp=5:5:0.4"),
    "warm": ("Ấm áp", "eq=contrast=1.05:saturation=1.1,colorbalance=rs=0.06:gs=0.02:bs=-0.05:rm=0.04:bm=-0.03"),
    "cinematic": ("Điện ảnh (xanh - cam)",
                  "eq=contrast=1.12:saturation=1.05,colorbalance=rs=-0.06:bs=0.08:rh=0.08:bh=-0.07,vignette=PI/5"),
    "bw": ("Đen trắng", "hue=s=0,eq=contrast=1.15"),
    "none": ("Giữ nguyên màu gốc", ""),
}


# ---------------- 1. Nghe nhạc ----------------

def load_audio(path: str, max_seconds: float = 600) -> np.ndarray:
    """Giải mã file nhạc thành mảng mono float32 (bằng ffmpeg, đọc được mp3/m4a/wav…)."""
    cmd = [video_maker.ffmpeg_exe(), "-v", "error", "-i", path, "-t", str(max_seconds),
           "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Không đọc được file nhạc: {result.stderr.decode('utf-8', 'replace')[-300:]}")
    y = np.frombuffer(result.stdout, dtype=np.float32)
    if len(y) < SR * 3:
        raise RuntimeError("File nhạc quá ngắn (cần ít nhất vài giây)")
    return y


def onset_envelope(y: np.ndarray) -> np.ndarray:
    """Độ "bật" của âm thanh theo thời gian (spectral flux): đỉnh cao ở tiếng trống, tiếng nhấn."""
    n_frames = 1 + max(0, len(y) - N_FFT) // HOP
    window = np.hanning(N_FFT).astype(np.float32)
    prev = None
    env = np.zeros(n_frames, dtype=np.float32)
    for start in range(0, n_frames, 2048):                # xử lý từng khối để không tốn RAM
        idx = np.arange(start, min(start + 2048, n_frames))
        frames = np.stack([y[i * HOP: i * HOP + N_FFT] for i in idx]) * window
        mag = np.log1p(100 * np.abs(np.fft.rfft(frames, axis=1)))
        if prev is None:
            prev = mag[:1]
        diff = np.diff(np.vstack([prev, mag]), axis=0)
        env[idx] = np.maximum(diff, 0).mean(axis=1)
        prev = mag[-1:]
    env -= np.convolve(env, np.ones(16) / 16, mode="same")     # bỏ nền, giữ phần nhấn
    env = np.maximum(env, 0)
    return env / (env.std() + 1e-9)


def estimate_tempo(env: np.ndarray, fps: float) -> float:
    """Tempo (BPM) bằng tự tương quan, ưu tiên khoảng 90-140 BPM hay gặp trong nhạc phổ thông."""
    env = env - env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    bpms = np.arange(60, 181, 0.5)
    lags = 60 * fps / bpms
    strength = np.interp(lags, np.arange(len(ac)), ac)
    # nhịp đôi / nhịp nửa cũng góp điểm để không bị nhầm gấp đôi tempo
    strength = strength + 0.5 * np.interp(lags * 2, np.arange(len(ac)), ac)
    prior = np.exp(-0.5 * (np.log2(bpms / 115) / 0.9) ** 2)
    return float(bpms[np.argmax(strength * prior)])


def track_beats(env: np.ndarray, fps: float, bpm: float, tightness: float = 100) -> np.ndarray:
    """Dò vị trí từng nhịp bằng quy hoạch động (Ellis 2007): nhịp rơi vào chỗ nhấn và cách đều nhau."""
    period = 60 * fps / bpm
    n = len(env)
    prange = np.arange(-round(2 * period), -round(period / 2) + 1)
    txcost = -tightness * np.log(-prange / period) ** 2
    score = env.astype(np.float64).copy()
    backlink = np.full(n, -1)
    for i in range(n):
        lo = i + prange
        ok = lo >= 0
        if not ok.any():
            continue
        cand = score[lo[ok]] + txcost[ok]
        j = int(np.argmax(cand))
        score[i] = env[i] + cand[j]
        backlink[i] = lo[ok][j]
    tail = max(0, n - round(period))
    i = tail + int(np.argmax(score[tail:]))
    beats = []
    while i >= 0:
        beats.append(i)
        i = backlink[i]
    return np.array(beats[::-1], dtype=np.float64)


def analyze_music(path: str) -> dict:
    """-> {bpm, beats (giây), energy (0-1, mỗi nhịp), duration}."""
    y = load_audio(path)
    fps = SR / HOP
    env = onset_envelope(y)
    bpm = estimate_tempo(env, fps)
    beats = (track_beats(env, fps, bpm) * HOP + N_FFT / 2) / SR       # mốc thời gian = tâm cửa sổ phân tích
    beats = beats[beats > 0.05]
    duration = len(y) / SR
    energy = []
    edges = list(beats) + [duration]
    for a, b in zip(edges[:-1], edges[1:]):
        seg = y[int(a * SR): max(int(b * SR), int(a * SR) + 1)]
        energy.append(float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0)
    energy = np.array(energy)
    if len(energy):
        lo, hi = np.percentile(energy, 10), np.percentile(energy, 95)
        energy = np.clip((energy - lo) / (hi - lo + 1e-9), 0, 1)
        energy = np.convolve(energy, np.ones(4) / 4, mode="same")       # mượt theo ô nhịp
    return {"bpm": round(bpm, 1), "beats": [round(float(b), 3) for b in beats],
            "energy": [round(float(e), 3) for e in energy], "duration": round(duration, 2)}


def pick_window(music: dict, seconds: float, mode: str = "auto") -> tuple[float, float]:
    """Chọn đoạn nhạc dùng cho video: 'auto' = đoạn sôi nhất (thường là điệp khúc), 'start' = từ đầu bài."""
    beats, energy, duration = music["beats"], music["energy"], music["duration"]
    seconds = min(seconds, duration)
    if mode != "auto" or len(beats) < 8:
        start = beats[0] if beats and beats[0] < 2 else 0.0
        return start, min(duration, start + seconds)
    best, best_score = beats[0], -1.0
    for i in range(0, len(beats), 4):                   # bắt đầu ở đầu ô nhịp (4 nhịp)
        start = beats[i]
        if start + seconds > duration:
            break
        inside = [e for b, e in zip(beats, energy) if start <= b < start + seconds]
        score = float(np.mean(inside)) if inside else 0.0
        if score > best_score + 1e-6:
            best, best_score = start, score
    return best, min(duration, best + seconds)


def plan_cuts(music: dict, start: float, end: float, pace: str = "auto") -> list[dict]:
    """Các cảnh [{start, end, energy}] tính theo giây trên video (0 = đầu video), mọi điểm cắt rơi đúng nhịp."""
    beats = [b for b in music["beats"] if start <= b < end]
    energy = dict(zip(music["beats"], music["energy"]))
    period = float(np.median(np.diff(music["beats"]))) if len(music["beats"]) > 1 else 0.5
    fixed = {"fast": 1, "medium": 2, "slow": 4}
    points, i = [start], 0
    while i < len(beats):
        e = energy.get(beats[i], 0.5)
        step = fixed.get(pace) or (1 if e > 0.72 else 2 if e > 0.4 else 4)
        while step * period < MIN_SHOT:
            step *= 2
        i += step
        if i < len(beats):
            points.append(beats[i])
    points.append(end)
    shots = []
    for a, b in zip(points[:-1], points[1:]):
        if b - a < MIN_SHOT and shots:                  # cảnh cuối quá ngắn: gộp vào cảnh trước
            shots[-1]["end"] = b - start
            continue
        while b - a > MAX_SHOT * 1.5:                   # đoạn êm quá dài: chia theo nhịp
            mid = next((x for x in beats if a + MAX_SHOT * 0.5 <= x <= a + MAX_SHOT), a + MAX_SHOT)
            shots.append({"start": a - start, "end": mid - start, "energy": energy.get(a, 0.5)})
            a = mid
        shots.append({"start": a - start, "end": b - start, "energy": energy.get(a, 0.5)})
    for s in shots:
        s["start"], s["end"] = round(s["start"], 3), round(s["end"], 3)
    return shots


# ---------------- 2. Xem clip ----------------

def sample_frames(path: str) -> np.ndarray:
    """Khung hình xám thu nhỏ, SAMPLE_FPS khung/giây -> mảng (n, THUMB, THUMB)."""
    cmd = [video_maker.ffmpeg_exe(), "-v", "error", "-i", path, "-an",
           "-vf", f"fps={SAMPLE_FPS},scale={THUMB}:{THUMB}", "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    result = subprocess.run(cmd, capture_output=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Không đọc được clip {Path(path).name}: "
                           f"{result.stderr.decode('utf-8', 'replace')[-200:]}")
    data = np.frombuffer(result.stdout, dtype=np.uint8)
    n = len(data) // (THUMB * THUMB)
    return data[: n * THUMB * THUMB].reshape(n, THUMB, THUMB).astype(np.float32)


def score_frames(frames: np.ndarray) -> dict:
    """Điểm từng khung (0-1): nét, đủ sáng, có tương phản, chuyển động vừa phải."""
    if not len(frames):
        return {k: np.zeros(0) for k in ("sharp", "bright", "contrast", "motion")}
    lap = (frames[:, 1:-1, 1:-1] * 4 - frames[:, :-2, 1:-1] - frames[:, 2:, 1:-1]
           - frames[:, 1:-1, :-2] - frames[:, 1:-1, 2:])
    sharp = np.log1p(lap.var(axis=(1, 2)))
    bright = frames.mean(axis=(1, 2))
    contrast = frames.std(axis=(1, 2))
    motion = np.zeros(len(frames))
    motion[1:] = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    return {"sharp": sharp, "bright": bright, "contrast": contrast, "motion": motion}


def analyze_clip(path: str) -> dict:
    duration = video_maker.probe_duration(path)
    if duration <= 0:
        raise RuntimeError(f"Không đọc được clip {Path(path).name}")
    m = score_frames(sample_frames(path))
    return {"path": path, "duration": duration, **{k: v for k, v in m.items()}}


def finalize_scores(clips: list[dict]) -> None:
    """Chuẩn hoá điểm trên toàn bộ clip (clip nét nhất = mốc), gắn 'quality', 'motion_n', 'cut'."""
    sharp_all = np.concatenate([c["sharp"] for c in clips if len(c["sharp"])] or [np.zeros(1)])
    motion_all = np.concatenate([c["motion"] for c in clips if len(c["motion"])] or [np.zeros(1)])
    s_lo, s_hi = np.percentile(sharp_all, 5), np.percentile(sharp_all, 95)
    m_hi = max(np.percentile(motion_all, 90), 1e-6)
    shake = max(np.percentile(motion_all, 97), 25.0)
    for c in clips:
        sharp = np.clip((c["sharp"] - s_lo) / (s_hi - s_lo + 1e-9), 0, 1)
        exposure = 1 - np.clip(np.abs(c["bright"] - 125) / 110, 0, 1) ** 2      # quá tối / cháy sáng bị trừ
        contrast = np.clip(c["contrast"] / 45, 0, 1)
        motion_n = np.clip(c["motion"] / m_hi, 0, 1)
        q = 0.5 * sharp + 0.25 * exposure + 0.15 * contrast + 0.1 * (1 - np.abs(motion_n - 0.4))
        q = np.where(c["motion"] > shake, q * 0.4, q)                              # rung lắc mạnh
        c["quality"] = q * c.get("ai", np.ones_like(q))
        c["motion_n"] = motion_n
        c["cut"] = c["motion"] > max(3 * np.median(c["motion"]) if len(c["motion"]) else 0, 35)   # chuyển cảnh


def choose_segments(clips: list[dict], shots: list[dict], keep_order: bool = False, seed: int = 0) -> list[dict]:
    """Mỗi cảnh lấy 1 đoạn clip đẹp nhất chưa dùng. Cảnh sôi ưu tiên đoạn nhiều chuyển động.

    keep_order: giữ thứ tự thời gian như lúc quay (hợp vlog, du lịch); không thì chọn cảnh đẹp nhất trước.
    """
    rng = random.Random(seed)
    used: list[tuple[int, float, float]] = []
    out, last_clip, cursor = [], -1, 0.0
    total_need = sum(s["end"] - s["start"] for s in shots)
    total_have = sum(c["duration"] for c in clips)
    offsets = np.cumsum([0.0] + [c["duration"] for c in clips])     # vị trí clip trên "dòng thời gian quay"
    video_len = shots[-1]["end"] if shots else 1.0
    allow_reuse = total_have < total_need * 1.1
    for shot in shots:
        need = shot["end"] - shot["start"] + 0.05
        best, best_score = None, -1e9
        for ci, c in enumerate(clips):
            n = len(c["quality"])
            w = max(1, int(round(need * SAMPLE_FPS)))
            if c["duration"] < need or n == 0:
                continue
            for si in range(0, max(1, n - w + 1)):
                start = si / SAMPLE_FPS
                if start + need > c["duration"]:
                    break
                win = slice(si, min(n, si + w))
                if c["cut"][win][1:].any():                  # không cắt ngang cảnh chuyển trong clip
                    continue
                overlap = any(u == ci and start < b and start + need > a for u, a, b in used)
                if overlap and not allow_reuse:
                    continue
                score = float(c["quality"][win].mean())
                score += 0.25 * shot["energy"] * float(c["motion_n"][win].mean())
                score -= 0.6 if overlap else 0
                score -= 0.15 if ci == last_clip else 0
                if keep_order:                                # bám theo tiến độ: cảnh đầu video lấy từ đầu buổi quay
                    pos = offsets[ci] + start
                    expected = shot["start"] / video_len * total_have
                    score -= 3.0 * abs(pos - expected) / max(total_have, 1e-6)
                    score -= 1.0 if pos < cursor - 0.5 else 0
                score += rng.uniform(0, 0.03)                 # mỗi lần dựng lại ra bản hơi khác
                if score > best_score:
                    best, best_score = (ci, start), score
        if best is None:                                      # clip quá ngắn: lấy clip dài nhất, lặp lại
            ci = max(range(len(clips)), key=lambda k: clips[k]["duration"])
            best = (ci, 0.0)
        ci, start = best
        used.append((ci, start, start + need))
        last_clip, cursor = ci, offsets[ci] + start + need
        out.append({**shot, "clip": ci, "src_start": round(start, 3)})
    return out


# ---------------- (tuỳ chọn) AI chấm cảnh ----------------

AI_SCHEMA = {
    "type": "object",
    "properties": {"scores": {"type": "array", "items": {"type": "integer"},
                              "description": "Điểm 0-10 cho từng ảnh theo đúng thứ tự"}},
    "required": ["scores"], "additionalProperties": False,
}
AI_SYSTEM = """Bạn là biên tập viên video mạng xã hội. Chấm điểm 0-10 từng khung hình trích từ clip người dùng tự quay,
để chọn cảnh đưa vào video ngắn. Điểm cao: chủ thể rõ, bố cục đẹp, ánh sáng tốt, cảm xúc / hành động hấp dẫn.
Điểm thấp: mờ, rung, ngón tay che ống kính, quay sàn nhà / trần nhà, cảnh trống vô nghĩa, lộ thông tin cá nhân."""


def ai_rate(clips: list[dict], record_usage=None, every: float = 2.0, max_frames: int = 40) -> None:
    """Claude xem khung hình thu nhỏ (mỗi ~2 giây 1 khung) và chấm điểm; gắn hệ số c['ai'] (0,3-1,15)."""
    import anthropic
    from PIL import Image

    from app.services import ai_models

    picks = []
    for ci, c in enumerate(clips):
        for t in np.arange(0, c["duration"], every):
            picks.append((ci, float(t)))
    if len(picks) > max_frames:
        picks = [picks[int(i)] for i in np.linspace(0, len(picks) - 1, max_frames)]
    content = []
    for k, (ci, t) in enumerate(picks):
        cmd = [video_maker.ffmpeg_exe(), "-v", "error", "-ss", f"{t:.2f}", "-i", clips[ci]["path"],
               "-frames:v", "1", "-vf", "scale=384:-2", "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
        jpg = subprocess.run(cmd, capture_output=True, timeout=60).stdout
        if not jpg:
            continue
        im = Image.open(io.BytesIO(jpg)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        content += [{"type": "text", "text": f"Ảnh {k}:"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                 "data": base64.standard_b64encode(buf.getvalue()).decode()}}]
    if not content:
        return
    content.append({"type": "text", "text": f"Chấm điểm {len(picks)} ảnh trên, trả về mảng scores đúng thứ tự."})
    model = ai_models.model_for("creative")
    params = {"model": model, "max_tokens": 1000, "system": AI_SYSTEM,
              "messages": [{"role": "user", "content": content}],
              "output_config": {"format": {"type": "json_schema", "schema": AI_SCHEMA}}}
    params["output_config"].update(ai_models.request_options(model).get("output_config", {}))
    msg = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(**params)
    if record_usage:
        record_usage(msg.model, msg.usage.input_tokens, msg.usage.output_tokens, False)
    text = next((b.text for b in msg.content if b.type == "text"), "{}")
    scores = json.loads(text).get("scores", [])
    for c in clips:
        c["ai"] = np.ones(len(c["sharp"]))
    for (ci, t), s in zip(picks, scores):
        c = clips[ci]
        a, b = int(t * SAMPLE_FPS), int((t + every) * SAMPLE_FPS)
        c["ai"][a:b] = 0.3 + 0.85 * min(max(int(s), 0), 10) / 10


# ---------------- 4. Dựng ----------------

def _run(cmd: list[str], what: str, timeout: int = 600) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"{what} lỗi: {result.stderr.strip()[-400:]}")


def render(clips: list[dict], shots: list[dict], music_path: str, music_start: float, out_path: str,
           aspect: str = "9:16", grade: str = "natural", flash: bool = True, original_audio: float = 0.0,
           work_dir: str | None = None) -> str:
    """Cắt từng cảnh đúng số khung hình, ghép lại, lồng nhạc. Trả về đường dẫn video."""
    w, h = ASPECTS[aspect]
    grade_filter = GRADES.get(grade, GRADES["natural"])[1]
    work = Path(work_dir or Path(out_path).parent / f"_parts_{aspect.replace(':', 'x')}")
    work.mkdir(parents=True, exist_ok=True)
    ffmpeg = video_maker.ffmpeg_exe()
    parts, lengths, frame_pos = [], [], 0
    for i, shot in enumerate(shots):
        end_frame = round(shot["end"] * FPS)
        n_frames = max(1, end_frame - frame_pos)          # cộng dồn để điểm cắt không trôi khỏi nhịp
        frame_pos += n_frames
        lengths.append(n_frames / FPS)
        clip = clips[shot["clip"]]
        vf = [f"scale={w}:{h}:force_original_aspect_ratio=increase", f"crop={w}:{h}", f"fps={FPS}", "setsar=1"]
        if grade_filter:
            vf.append(grade_filter)
        if flash and shot["energy"] > 0.72 and i > 0:     # nháy sáng nhẹ đầu cảnh ở nhịp mạnh
            vf.append("eq=brightness=0.18:enable='lt(t,0.07)'")
        vf.append("tpad=stop_mode=clone:stop=-1")        # clip ngắn hơn cảnh: giữ khung cuối cho đủ độ dài
        vf.append("format=yuv420p")
        part = work / f"{i:04d}.mp4"
        # chỉ lấy hình: tiếng ghép riêng ở bước cuối, nếu không mỗi đoạn dư vài ms tiếng làm điểm cắt trôi nhịp
        _run([ffmpeg, "-y", "-v", "error", "-ss", f"{shot['src_start']:.3f}", "-i", clip["path"], "-an",
              "-vf", ",".join(vf), "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "veryfast",
              "-crf", "20", "-r", str(FPS), str(part)], f"Cắt cảnh {i + 1}")
        parts.append(part)
    total = frame_pos / FPS
    listing = work / "list.txt"
    listing.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in parts), encoding="utf-8")
    joined = work / "joined.mp4"
    _run([ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)],
         "Ghép cảnh")
    fade_out = min(1.5, total / 4)
    inputs = ["-i", str(joined), "-i", music_path]
    graph = [f"[1:a]aresample=44100,aformat=channel_layouts=stereo,"
             f"atrim=start={music_start:.3f}:duration={total:.3f},asetpts=PTS-STARTPTS,"
             f"afade=t=in:d=0.3,afade=t=out:st={total - fade_out:.3f}:d={fade_out:.3f}[m]"]
    if original_audio > 0:                                # tiếng gốc của từng cảnh, cắt chính xác theo mẫu
        labels = []
        for k, (shot, length) in enumerate(zip(shots, lengths)):
            path = clips[shot["clip"]]["path"]
            if video_maker.has_audio(path):
                inputs += ["-ss", f"{shot['src_start']:.3f}", "-t", f"{length + 0.2:.3f}", "-i", path]
            else:
                inputs += ["-f", "lavfi", "-t", f"{length:.3f}", "-i",
                           "anullsrc=channel_layout=stereo:sample_rate=44100"]
            graph.append(f"[{k + 2}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{length:.4f},"
                         f"apad=whole_dur={length:.4f},asetpts=PTS-STARTPTS[o{k}]")
            labels.append(f"[o{k}]")
        graph.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1,volume={original_audio:.2f}[o]")
        graph.append("[m]volume=0.9[m2];[m2][o]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        graph.append("[m]anull[a]")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    _run([ffmpeg, "-y", "-v", "error", *inputs, "-filter_complex", ";".join(graph),
          "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
          "-movflags", "+faststart", out_path], "Lồng nhạc")
    for p in [*parts, listing, joined]:
        p.unlink(missing_ok=True)
    try:
        work.rmdir()
    except OSError:
        pass
    return out_path


def make_edit(clip_paths: list[str], music_path: str, out_dir: str, seconds: float = 30, aspects=("9:16",),
              pace: str = "auto", grade: str = "natural", music_mode: str = "auto", keep_order: bool = False,
              flash: bool = True, original_audio: float = 0.0, use_ai: bool = False, seed: int = 0,
              progress=None, record_usage=None) -> dict:
    """Toàn bộ quy trình. Trả về {outputs: {khổ: đường dẫn}, bpm, shots, music_start, seconds}."""
    say = progress or (lambda msg: None)
    if not clip_paths:
        raise ValueError("Chưa có clip nào")
    say("Đang nghe nhạc, dò nhịp…")
    music = analyze_music(music_path)
    start, end = pick_window(music, seconds, music_mode)
    shots = plan_cuts(music, start, end, pace)
    say(f"Nhạc {music['bpm']:.0f} BPM, {len(shots)} cảnh. Đang xem và chấm điểm {len(clip_paths)} clip…")
    clips = [analyze_clip(p) for p in clip_paths]
    if use_ai and config.AI_ENABLED:
        say("AI đang xem cảnh quay…")
        try:
            ai_rate(clips, record_usage)
        except Exception as e:  # noqa: BLE001 - AI lỗi thì vẫn dựng bằng điểm tự chấm
            say(f"AI chấm cảnh lỗi ({str(e)[:80]}), dùng điểm tự chấm")
    finalize_scores(clips)
    plan = choose_segments(clips, shots, keep_order=keep_order, seed=seed)
    outputs = {}
    for aspect in aspects:
        say(f"Đang dựng bản {aspect} ({len(plan)} cảnh)…")
        out = str(Path(out_dir) / f"video_{aspect.replace(':', 'x')}.mp4")
        outputs[aspect] = render(clips, plan, music_path, start, out, aspect=aspect, grade=grade, flash=flash,
                                 original_audio=original_audio)
    return {"outputs": outputs, "bpm": music["bpm"], "music_start": round(start, 2),
            "seconds": round(end - start, 2), "shots": [
                {**s, "clip_name": Path(clips[s["clip"]]["path"]).name} for s in plan]}


# ---------------- Việc dựng trong web app (mỗi việc 1 thư mục trong MEDIA_DIR/beatcut) ----------------

def jobs_dir() -> Path:
    path = Path(config.MEDIA_DIR) / "beatcut"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_path(job_id: str) -> Path:
    if not job_id.isalnum():
        raise ValueError("Mã việc không hợp lệ")
    return jobs_dir() / job_id / "job.json"


def load_job(job_id: str) -> dict | None:
    try:
        return json.loads(_job_path(job_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save_job(job: dict) -> None:
    path = _job_path(job["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def list_jobs(limit: int = 30) -> list[dict]:
    jobs = [j for j in (load_job(p.name) for p in jobs_dir().iterdir() if p.is_dir()) if j]
    return sorted(jobs, key=lambda j: j["created_at"], reverse=True)[:limit]


def new_job(clips: list[str], music: str, options: dict) -> dict:
    from app import db

    job_id = db.now().strftime("%Y%m%d%H%M%S") + f"{random.randrange(16 ** 4):04x}"
    job = {"id": job_id, "created_at": db.now_iso(), "status": "queued", "step": "Đang chờ…", "error": "",
           "clips": clips, "music": music, "options": options, "outputs": {}, "result": {}, "version": 0}
    save_job(job)
    return job


def job_folder(job_id: str) -> Path:
    return _job_path(job_id).parent


def run_job(job_id: str, record_usage=None) -> None:
    """Chạy nền: dựng video cho 1 việc, cập nhật tiến độ vào job.json."""
    job = load_job(job_id)
    if not job:
        return
    opts = job["options"]
    job.update(status="running", step="Bắt đầu…", error="")
    save_job(job)

    def progress(msg: str) -> None:
        job["step"] = msg
        save_job(job)

    try:
        version = job.get("version", 0) + 1
        out_dir = job_folder(job_id) / f"v{version}"
        result = make_edit(job["clips"], job["music"], str(out_dir), seconds=float(opts.get("seconds", 30)),
                           aspects=opts.get("aspects") or ["9:16"], pace=opts.get("pace", "auto"),
                           grade=opts.get("grade", "natural"), music_mode=opts.get("music_mode", "auto"),
                           keep_order=bool(opts.get("keep_order")), flash=bool(opts.get("flash", True)),
                           original_audio=float(opts.get("original_audio", 0)), use_ai=bool(opts.get("use_ai")),
                           seed=version, progress=progress, record_usage=record_usage)
        job.update(status="done", step="Xong", outputs=result.pop("outputs"), result=result, version=version)
    except Exception as e:  # noqa: BLE001
        job.update(status="error", step="Lỗi", error=str(e)[:500])
    save_job(job)


def delete_job(job_id: str) -> None:
    import shutil

    folder = job_folder(job_id)
    if folder.is_dir() and folder.parent == jobs_dir():
        shutil.rmtree(folder, ignore_errors=True)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Dựng video khớp nhịp nhạc từ clip tự quay")
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--music", required=True)
    ap.add_argument("--out", default="data/media/beatcut/cli")
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--aspect", action="append", choices=list(ASPECTS))
    ap.add_argument("--pace", default="auto", choices=list(PACES))
    ap.add_argument("--grade", default="natural", choices=list(GRADES))
    ap.add_argument("--from-start", action="store_true", help="dùng nhạc từ đầu bài thay vì đoạn sôi nhất")
    ap.add_argument("--keep-order", action="store_true", help="giữ thứ tự quay")
    ap.add_argument("--ai", action="store_true", help="Claude chấm cảnh (cần ANTHROPIC_API_KEY)")
    args = ap.parse_args()
    result = make_edit(args.clips, args.music, args.out, args.seconds, args.aspect or ["9:16"], args.pace,
                       args.grade, "start" if args.from_start else "auto", args.keep_order, use_ai=args.ai,
                       progress=print)
    print(json.dumps({k: v for k, v in result.items() if k != "shots"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
