"""Bộ nhớ truyện: lưu trên đĩa và dựng "hồ sơ truyện" (ngữ cảnh) cho từng chương.

Truyện dài không nhét vừa ngữ cảnh, nên bộ nhớ nén theo tầng:
- Phần đã xong      -> 1 bản tóm tắt phần.
- Chương cũ phần này -> sự kiện chính.
- N chương gần nhất  -> tóm tắt đầy đủ + chương dừng ở đâu.
- Chương ngay trước  -> nguyên văn đoạn cuối.
Cộng với kinh thánh truyện (nhân vật kèm trạng thái hiện tại), sự thật cần giữ nhất quán và tuyến truyện đang mở.
"""
import json
import os
import re
import unicodedata
from pathlib import Path

from novel_agent import config
from novel_agent.schemas import ChapterPlan, ChapterRecord, StoryBible


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60] or "truyen"


class Project:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.state = json.loads((self.path / "project.json").read_text(encoding="utf-8"))

    # ---------- lưu trữ ----------
    @classmethod
    def create(cls, idea: str, settings: dict, bible: StoryBible, base: Path = None) -> "Project":
        base = Path(base or config.NOVEL_DIR)
        slug, n = slugify(bible.title), 1
        while (base / (slug if n == 1 else f"{slug}-{n}")).exists():
            n += 1
        path = base / (slug if n == 1 else f"{slug}-{n}")
        (path / "chapters").mkdir(parents=True)
        (path / "reviews").mkdir()
        state = {"idea": idea, "settings": settings, "bible": bible.model_dump(), "part_plans": {},
                 "records": {}, "part_summaries": {}, "facts": [], "open_threads": []}
        _write(path / "project.json", json.dumps(state, ensure_ascii=False, indent=2))
        return cls(path)

    def save(self) -> None:
        _write(self.path / "project.json", json.dumps(self.state, ensure_ascii=False, indent=2))

    @property
    def bible(self) -> StoryBible:
        return StoryBible.model_validate(self.state["bible"])

    def chapter_file(self, number: int) -> Path:
        return self.path / "chapters" / f"chuong-{number:03d}.md"

    def chapter_text(self, number: int) -> str:
        f = self.chapter_file(number)
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def save_chapter(self, plan: ChapterPlan, text: str) -> None:
        _write(self.chapter_file(plan.number), text)

    def save_reviews(self, number: int, rounds: list) -> None:
        _write(self.path / "reviews" / f"chuong-{number:03d}.json", json.dumps(rounds, ensure_ascii=False, indent=2))

    # ---------- dàn ý ----------
    def parts(self) -> list[int]:
        return [p["number"] for p in self.state["bible"]["parts"]]

    def part_plan(self, part_no: int) -> list[ChapterPlan] | None:
        plan = self.state["part_plans"].get(str(part_no))
        return [ChapterPlan.model_validate(c) for c in plan] if plan is not None else None

    def set_part_plan(self, part_no: int, chapters: list[ChapterPlan]) -> None:
        self.state["part_plans"][str(part_no)] = [c.model_dump() for c in chapters]
        self.save()

    def first_chapter_of(self, part_no: int) -> int:
        """Số chương đầu tiên của phần; phần chưa lập dàn ý thì ước theo số chương mỗi phần."""
        start = 1
        for p in self.parts():
            if p == part_no:
                return start
            plan = self.part_plan(p)
            start += len(plan) if plan is not None else self.state["settings"]["chapters_per_part"]
        raise KeyError(part_no)

    def part_of(self, number: int) -> int | None:
        for p in self.parts():
            if any(c.number == number for c in self.part_plan(p) or []):
                return p
        return None

    def plan_of(self, number: int) -> ChapterPlan:
        part = self.part_of(number)
        return next(c for c in self.part_plan(part) if c.number == number)

    def written(self) -> list[int]:
        return sorted(int(n) for n in self.state["records"])

    def next_chapter(self) -> tuple[int, int] | None:
        """(phần, chương) tiếp theo cần viết; None khi đã xong toàn truyện."""
        done = set(self.written())
        for p in self.parts():
            plan = self.part_plan(p)
            if plan is None:
                return p, self.first_chapter_of(p)
            for c in plan:
                if c.number not in done:
                    return p, c.number
        return None

    # ---------- ghi nhớ sau mỗi chương ----------
    def apply_record(self, number: int, record: ChapterRecord) -> None:
        bible = self.state["bible"]
        chars = {c["name"].lower(): c for c in bible["characters"]}
        for up in record.character_updates:
            if up.name.lower() in chars:
                chars[up.name.lower()]["current_state"] = up.current_state
        for c in record.new_characters:
            if c.name.lower() not in chars:
                bible["characters"].append(c.model_dump())
        self.state["facts"].extend(record.new_facts)
        resolved = {t.strip().lower() for t in record.threads_resolved}
        self.state["open_threads"] = [t for t in self.state["open_threads"] if t.strip().lower() not in resolved]
        self.state["open_threads"].extend(record.threads_opened)
        self.state["records"][str(number)] = record.model_dump()
        self.save()

    def record(self, number: int) -> ChapterRecord | None:
        r = self.state["records"].get(str(number))
        return ChapterRecord.model_validate(r) if r else None

    # ---------- hồ sơ truyện (ngữ cảnh cho AI) ----------
    def bible_text(self) -> str:
        b = self.bible
        chars = "\n".join(f"- {c.name} ({c.role}): {c.description}\n  Mục tiêu: {c.goal}\n  Hành trình: {c.arc}\n"
                          f"  TRẠNG THÁI HIỆN TẠI: {c.current_state}" for c in b.characters)
        parts = "\n".join(f"- Phần {p.number} \"{p.title}\": {p.arc} | Kết phần: {p.ending_hook}" for p in b.parts)
        return (f"# KINH THÁNH TRUYỆN: {b.title}\nThể loại: {b.genre}\nÝ tưởng: {b.premise}\n"
                f"Chủ đề: {', '.join(b.themes)}\n\n## Hướng dẫn văn phong\n{b.style_guide}\n\n## Thế giới\n{b.world}\n\n"
                f"## Nhân vật\n{chars}\n\n## Mạch các phần\n{parts}\n\n## Kết cục dự kiến\n{b.ending}")

    def story_so_far(self, before: int) -> str:
        """Diễn biến trước chương `before`, nén theo tầng."""
        current_part = self.part_of(before)
        written = [n for n in self.written() if n < before]
        recent = set(written[-config.RECENT_CHAPTERS:])
        lines = []
        for p in self.parts():
            if current_part is not None and p >= current_part:
                break
            summary = self.state["part_summaries"].get(str(p))
            if summary:
                lines.append(f"## Phần {p} (đã xong)\n{summary}")
            else:   # phần chưa có tóm tắt: liệt kê sự kiện
                for c in self.part_plan(p) or []:
                    if c.number in written and c.number not in recent:
                        lines.append(f"- Chương {c.number}: " + "; ".join(self.record(c.number).key_events))
        older = [n for n in written if n not in recent and self.part_of(n) == current_part]
        if older:
            lines.append(f"## Phần {current_part} (các chương trước)")
            lines += [f"- Chương {n}: " + "; ".join(self.record(n).key_events) for n in older]
        if recent:
            lines.append("## Các chương gần nhất")
            for n in sorted(recent):
                r = self.record(n)
                lines.append(f"### Chương {n}: {self.plan_of(n).title}\n{r.summary}\nDừng ở: {r.ending_state}")
        return "\n".join(lines) or "(Chưa có chương nào - đây là mở đầu truyện.)"

    def chapter_context(self, number: int) -> str:
        part_no = self.part_of(number)
        part = next(p for p in self.bible.parts if p.number == part_no)
        plan = self.plan_of(number)
        outline = "\n".join(f"- Chương {c.number}: {c.title} - {c.goal}" for c in self.part_plan(part_no))
        facts = "\n".join(f"- {f}" for f in self.state["facts"]) or "(chưa có)"
        threads = "\n".join(f"- {t}" for t in self.state["open_threads"]) or "(chưa có)"
        prev_tail = self.chapter_text(number - 1)[-config.TAIL_CHARS:] if number > 1 else ""
        beats = "\n".join(f"{i}. {b}" for i, b in enumerate(plan.beats, 1))
        return "\n\n".join([
            self.bible_text(),
            f"# SỰ THẬT ĐÃ THIẾT LẬP (phải giữ nhất quán)\n{facts}",
            f"# DIỄN BIẾN ĐÃ XẢY RA\n{self.story_so_far(number)}",
            f"# TUYẾN TRUYỆN ĐANG MỞ\n{threads}",
            f"# PHẦN {part_no}: {part.title}\nMạch: {part.arc}\nKết phần: {part.ending_hook}\nDàn ý các chương của phần:\n{outline}",
            f"# DÀN Ý CHƯƠNG {plan.number}: {plan.title}\nGóc nhìn: {plan.pov}\nMục tiêu: {plan.goal}\n"
            f"Diễn biến:\n{beats}\nTuyến truyện: {'; '.join(plan.threads)}\nKết chương: {plan.ending_hook}",
            f"# ĐOẠN CUỐI CHƯƠNG TRƯỚC (nguyên văn)\n{prev_tail}" if prev_tail else "# ĐÂY LÀ CHƯƠNG MỞ ĐẦU",
        ])

    def planning_context(self) -> str:
        """Ngữ cảnh cho kiến trúc sư khi lập dàn ý phần tiếp theo."""
        after = (self.written() or [0])[-1] + 1
        threads = "\n".join(f"- {t}" for t in self.state["open_threads"]) or "(chưa có)"
        facts = "\n".join(f"- {f}" for f in self.state["facts"]) or "(chưa có)"
        so_far = self.story_so_far(after) if self.written() else "(Chưa viết chương nào.)"
        return (f"{self.bible_text()}\n\n# SỰ THẬT ĐÃ THIẾT LẬP\n{facts}\n\n# DIỄN BIẾN ĐÃ XẢY RA\n{so_far}\n\n"
                f"# TUYẾN TRUYỆN ĐANG MỞ\n{threads}")


def _write(path: Path, text: str) -> None:
    """Ghi an toàn: ghi file tạm rồi đổi tên, tránh hỏng file khi đang chạy bị ngắt."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
