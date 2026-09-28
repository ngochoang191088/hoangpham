"""Kiểm thử hệ thống viết tiểu thuyết bằng LLM giả lập (không gọi API)."""
from types import SimpleNamespace

import pytest

from novel_agent import config
from novel_agent.llm import ClaudeLLM, LLMError, MockLLM, strict_schema
from novel_agent.memory import Project
from novel_agent.pipeline import NovelStudio, export
from novel_agent.schemas import ChapterRecord, Review, StoryBible


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_strict_schema_inlines_refs_and_forbids_extra_fields():
    schema = strict_schema(StoryBible)
    assert "title" in schema["properties"]            # trường tên "title" không bị xoá nhầm
    for node in _walk(schema):
        assert "$ref" not in node
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])


def test_full_novel_with_review_loop_and_memory(tmp_path):
    studio = NovelStudio(MockLLM(), log=lambda _: None)
    project = studio.create("Cô gái nhận thư từ người mẹ đã mất", parts=2, chapters_per_part=2, base=tmp_path)
    results = studio.write(project)

    assert [r["number"] for r in results] == [1, 2, 3, 4]
    assert results[0]["rounds"] == 2 and all(r["passed"] for r in results)   # chương 1 bị trả về sửa 1 lần
    assert project.next_chapter() is None
    assert set(project.state["part_summaries"]) == {"1", "2"}
    assert all(project.chapter_text(n) for n in range(1, 5))
    assert "Phần 1 (đã xong)" in project.story_so_far(4)
    assert "ĐOẠN CUỐI CHƯƠNG TRƯỚC" in project.chapter_context(4)
    md, docx = export(project)
    assert "Chương 4" in md.read_text(encoding="utf-8") and docx.exists()


def test_resume_after_interruption(tmp_path):
    studio = NovelStudio(MockLLM(), log=lambda _: None)
    project = studio.create("ý tưởng", parts=2, chapters_per_part=2, base=tmp_path)
    studio.write(project, 1)
    reopened = Project(project.path)
    assert reopened.next_chapter() == (1, 2)
    assert [r["number"] for r in studio.write(reopened, 2)] == [2, 3]


def test_record_updates_characters_and_threads(tmp_path):
    bible = MockLLM().parse(StoryBible)
    bible.characters[1].name = "Minh"
    p = Project.create("x", {"parts": 2, "chapters_per_part": 2, "words": 100}, bible, base=tmp_path)
    p.state["open_threads"] = ["Ai gửi lá thư?"]
    name = p.bible.characters[0].name
    p.apply_record(1, ChapterRecord(summary="s", key_events=["e"], new_characters=[], new_facts=["Nhà ở Huế"],
                                    character_updates=[{"name": name.upper(), "current_state": "bị thương"}],
                                    threads_opened=["Chiếc chìa khoá lạ"], threads_resolved=["ai gửi lá thư?"],
                                    ending_state="đêm"))
    assert p.bible.characters[0].current_state == "bị thương"
    assert p.state["open_threads"] == ["Chiếc chìa khoá lạ"]
    assert p.state["facts"] == ["Nhà ở Huế"]


class _StubStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.message


def _stub_client(message, calls):
    def stream(**kw):
        calls.append(kw)
        return _StubStream(message)
    return SimpleNamespace(messages=SimpleNamespace(stream=stream),
                           beta=SimpleNamespace(messages=SimpleNamespace(stream=stream)))


def _message(text, stop="end_turn"):
    usage = SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    return SimpleNamespace(model="claude-opus-5", usage=usage, stop_reason=stop, stop_details=None,
                           content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)])


def test_claude_request_shape(monkeypatch):
    monkeypatch.setattr(config, "FALLBACKS", True)
    calls = []
    llm = ClaudeLLM(_stub_client(_message('{"score": 9, "strengths": [], "issues": [], "summary": "ok"}'), calls))
    review = llm.parse(Review, system="s", content=[{"type": "text", "text": "t"}], effort="medium")
    assert review.score == 9
    kw = calls[0]
    assert kw["fallbacks"] == "default" and kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["thinking"] == {"type": "adaptive"}
    assert kw["output_config"]["effort"] == "medium"
    assert kw["output_config"]["format"]["type"] == "json_schema"
    assert llm.usage.by_model["claude-opus-5"]["calls"] == 1


def test_refusal_raises():
    llm = ClaudeLLM(_stub_client(_message("", stop="refusal"), []))
    with pytest.raises(LLMError):
        llm.text(system="s", content=[{"type": "text", "text": "t"}])
