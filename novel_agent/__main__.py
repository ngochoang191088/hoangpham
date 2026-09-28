"""Dòng lệnh:

  python -m novel_agent new "ý tưởng truyện" --parts 3 --chapters 8 --words 3000 --genre "trinh thám"
  python -m novel_agent write <thư-mục-truyện> [--count 2 | --all]
  python -m novel_agent status <thư-mục-truyện>
  python -m novel_agent review <thư-mục-truyện> <số-chương>
  python -m novel_agent export <thư-mục-truyện>
  python -m novel_agent list

Kịch bản phim:
  python -m novel_agent script new "ý tưởng phim" --minutes 15 --genre "tâm lý"   (dừng ở danh sách cảnh để bạn duyệt)
  python -m novel_agent script plan <tên> --note "đổi kết: ..."                  (sửa danh sách cảnh theo ý bạn)
  python -m novel_agent script write <tên>                                        (viết + hội đồng chấm + sửa)
  python -m novel_agent script revise <tên> [--rounds 1]                          (chấm và sửa thêm)
  python -m novel_agent script status|export <tên>
  python -m novel_agent script list

Thêm --mock để chạy giả lập (không gọi API, không tốn tiền).
"""
import argparse
import sys
from pathlib import Path

from novel_agent import config, prompts, screenplay
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


def _script_project(name: str) -> screenplay.ScriptProject:
    path = Path(name)
    if not (path / "project.json").exists():
        path = config.SCRIPT_DIR / name
    if not (path / "project.json").exists():
        sys.exit(f"Không tìm thấy kịch bản '{name}'. Xem danh sách: python -m novel_agent script list")
    return screenplay.ScriptProject(path)


def _script(args, studio: "screenplay.ScriptStudio") -> None:
    if args.scmd == "list":
        for d in sorted(config.SCRIPT_DIR.glob("*/project.json")):
            print(screenplay.status(screenplay.ScriptProject(d.parent)).splitlines()[0])
        return
    if args.scmd == "new":
        idea = Path(args.idea[1:]).read_text(encoding="utf-8") if args.idea.startswith("@") else args.idea
        project = studio.create(idea, minutes=args.minutes, genre=args.genre, notes=args.notes)
        print(screenplay.status(project))
        if not args.auto:
            print(f"\n👉 Đọc danh sách cảnh ở trên (và {project.path / 'story-bible.md'}).\n"
                  f"   Muốn sửa:  python -m novel_agent script plan {project.path.name} --note \"yêu cầu của bạn\"\n"
                  f"   Ưng rồi:   python -m novel_agent script write {project.path.name}")
            return
        args.scmd = "write"
    else:
        project = _script_project(args.project)
    if args.scmd == "plan":
        studio.plan(project, note=args.note)
        print(screenplay.status(project))
    elif args.scmd == "write":
        studio.draft(project)
        studio.revise(project)
        for f in screenplay.export(project):
            print(f"Đã xuất: {f}")
    elif args.scmd == "revise":
        studio.revise(project, args.rounds)
        for f in screenplay.export(project):
            print(f"Đã xuất: {f}")
    elif args.scmd == "status":
        print(screenplay.status(project))
    elif args.scmd == "export":
        for f in screenplay.export(project):
            print(f"Đã xuất: {f}")


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

    sc = sub.add_parser("script", help="viết kịch bản phim").add_subparsers(dest="scmd", required=True)
    sn = sc.add_parser("new", help="phát triển dự án phim tới danh sách cảnh")
    sn.add_argument("idea", help="ý tưởng phim, hoặc @file.txt")
    sn.add_argument("--minutes", type=int, default=15, help="thời lượng phim (mặc định 15 phút)")
    sn.add_argument("--genre", default="tự chọn cho hợp ý tưởng")
    sn.add_argument("--notes", default="không", help="yêu cầu thêm: bối cảnh, số diễn viên, ngân sách...")
    sn.add_argument("--auto", action="store_true", help="không dừng duyệt danh sách cảnh, viết luôn")
    sp = sc.add_parser("plan", help="sửa danh sách cảnh theo yêu cầu của bạn")
    sp.add_argument("project")
    sp.add_argument("--note", required=True)
    sc.add_parser("write", help="viết kịch bản + hội đồng chấm + sửa").add_argument("project")
    sr = sc.add_parser("revise", help="hội đồng chấm và sửa thêm")
    sr.add_argument("project")
    sr.add_argument("--rounds", type=int, default=None, help="số vòng sửa tối đa (0 = chỉ chấm)")
    for name in ("status", "export"):
        sc.add_parser(name).add_argument("project")
    sc.add_parser("list")

    args = ap.parse_args(argv)
    llm = make_llm(args.mock)
    studio = NovelStudio(llm)
    try:
        if args.cmd == "script":
            _script(args, screenplay.ScriptStudio(llm))
        elif args.cmd == "new":
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
