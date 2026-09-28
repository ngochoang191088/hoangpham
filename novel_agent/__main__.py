"""Dòng lệnh:

  python -m novel_agent new "ý tưởng truyện" --parts 3 --chapters 8 --words 3000 --genre "trinh thám"
  python -m novel_agent write <thư-mục-truyện> [--count 2 | --all]
  python -m novel_agent status <thư-mục-truyện>
  python -m novel_agent review <thư-mục-truyện> <số-chương>
  python -m novel_agent export <thư-mục-truyện>
  python -m novel_agent list

Thêm --mock để chạy giả lập (không gọi API, không tốn tiền).
"""
import argparse
import sys
from pathlib import Path

from novel_agent import config, prompts
from novel_agent.llm import LLMError, make_llm
from novel_agent.memory import Project
from novel_agent.pipeline import NovelStudio, export, status


def _project(name: str) -> Project:
    path = Path(name)
    if not (path / "project.json").exists():
        path = config.NOVEL_DIR / name
    if not (path / "project.json").exists():
        sys.exit(f"Không tìm thấy truyện '{name}'. Xem danh sách: python -m novel_agent list")
    return Project(path)


def main(argv=None) -> None:
    for stream in (sys.stdout, sys.stderr):   # in được tiếng Việt / emoji trên Windows
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="novel_agent", description="Hệ thống AI Agent viết tiểu thuyết")
    ap.add_argument("--mock", action="store_true", help="chạy giả lập, không gọi API")
    sub = ap.add_subparsers(dest="cmd", required=True)

    new = sub.add_parser("new", help="tạo truyện mới từ ý tưởng")
    new.add_argument("idea", help="ý tưởng truyện, hoặc @file.txt để đọc từ file")
    new.add_argument("--parts", type=int, default=3, help="số phần (mặc định 3)")
    new.add_argument("--chapters", type=int, default=8, help="số chương mỗi phần (mặc định 8)")
    new.add_argument("--words", type=int, default=3000, help="số chữ mỗi chương (mặc định 3000)")
    new.add_argument("--genre", default="tự chọn cho hợp ý tưởng")
    new.add_argument("--notes", default="không", help="yêu cầu thêm: đối tượng đọc, giọng văn, cấm kỵ...")
    new.add_argument("--write", type=int, default=0, help="viết luôn N chương đầu")

    wr = sub.add_parser("write", help="viết tiếp")
    wr.add_argument("project")
    g = wr.add_mutually_exclusive_group()
    g.add_argument("--count", type=int, default=1, help="số chương viết thêm (mặc định 1)")
    g.add_argument("--all", action="store_true", help="viết tới hết truyện")

    for name in ("status", "export"):
        sub.add_parser(name).add_argument("project")
    rv = sub.add_parser("review", help="hội đồng đọc lại 1 chương (vd. sau khi bạn sửa tay)")
    rv.add_argument("project")
    rv.add_argument("chapter", type=int)
    sub.add_parser("list", help="liệt kê các truyện")

    args = ap.parse_args(argv)
    llm = make_llm(args.mock)
    studio = NovelStudio(llm)
    try:
        if args.cmd == "new":
            idea = Path(args.idea[1:]).read_text(encoding="utf-8") if args.idea.startswith("@") else args.idea
            project = studio.create(idea, parts=args.parts, chapters_per_part=args.chapters, words=args.words,
                                    genre=args.genre, notes=args.notes)
            if args.write:
                studio.write(project, args.write)
            print(status(project))
        elif args.cmd == "write":
            project = _project(args.project)
            studio.write(project, None if args.all else args.count)
            print(status(project))
        elif args.cmd == "status":
            print(status(_project(args.project)))
        elif args.cmd == "review":
            project = _project(args.project)
            for key, r in studio.review_only(project, args.chapter).items():
                print(f"\n## {prompts.CRITICS[key]['name']}: {r.score:g}/10\n{r.summary}")
                for i in r.issues:
                    print(f"- [{i.severity}] {i.location}: {i.problem}\n  -> {i.suggestion}")
        elif args.cmd == "export":
            for f in export(_project(args.project)):
                print(f"Đã xuất: {f}")
        elif args.cmd == "list":
            for d in sorted(config.NOVEL_DIR.glob("*/project.json")):
                print(status(Project(d.parent)).splitlines()[0])
    except LLMError as e:
        sys.exit(f"Lỗi AI: {e}")
    if llm.usage.by_model:
        print("\nToken đã dùng:\n" + llm.usage.report())


if __name__ == "__main__":
    main()
