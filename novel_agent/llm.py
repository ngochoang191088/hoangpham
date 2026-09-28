"""Gọi Claude API: văn bản tự do (viết chương) và JSON có cấu trúc (dàn ý, phê bình, ghi chép)."""
import copy
import json
import re
import threading
from collections import defaultdict

from pydantic import BaseModel

from novel_agent import config

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMError(RuntimeError):
    pass


def strict_schema(model: type[BaseModel]) -> dict:
    """JSON schema từ Pydantic cho structured outputs: gộp $ref, bỏ title, cấm trường thừa."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(copy.deepcopy(defs[node["$ref"].split("/")[-1]]))
            node = {k: ({name: walk(p) for name, p in v.items()} if k == "properties" else walk(v))
                    for k, v in node.items() if k != "title"}
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            return node
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


class Usage:
    """Cộng dồn token theo model để báo chi phí."""

    def __init__(self):
        self._lock = threading.Lock()
        self.by_model = defaultdict(lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "calls": 0})

    def add(self, model: str, usage) -> None:
        with self._lock:
            row = self.by_model[model]
            row["calls"] += 1
            row["input"] += usage.input_tokens or 0
            row["output"] += usage.output_tokens or 0
            row["cache_read"] += getattr(usage, "cache_read_input_tokens", 0) or 0
            row["cache_write"] += getattr(usage, "cache_creation_input_tokens", 0) or 0

    def report(self) -> str:
        lines = [f"- {m}: {r['calls']} lần gọi, vào {r['input']:,} (+cache đọc {r['cache_read']:,}, "
                 f"cache ghi {r['cache_write']:,}), ra {r['output']:,} token" for m, r in self.by_model.items()]
        return "\n".join(lines) or "- (chưa gọi API)"


class ClaudeLLM:
    def __init__(self, client=None):
        import anthropic

        self.client = client or anthropic.Anthropic()
        self.usage = Usage()

    def _run(self, *, system: str, content: list[dict], model: str, effort: str, max_tokens: int,
             output_format: dict | None = None) -> str:
        params = dict(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],
            thinking={"type": "adaptive"},
            output_config={"effort": effort, **({"format": output_format} if output_format else {})},
        )
        if config.FALLBACKS:
            stream = self.client.beta.messages.stream(betas=[FALLBACK_BETA], fallbacks="default", **params)
        else:
            stream = self.client.messages.stream(**params)
        with stream as s:
            message = s.get_final_message()
        self.usage.add(message.model, message.usage)
        if message.stop_reason == "refusal":
            details = getattr(message, "stop_details", None)
            raise LLMError(f"Model từ chối yêu cầu ({getattr(details, 'category', None)}). "
                           "Hãy điều chỉnh ý tưởng / dàn ý chương rồi chạy lại.")
        if message.stop_reason == "max_tokens":
            raise LLMError(f"Hết max_tokens={max_tokens} trước khi viết xong. Tăng max_tokens hoặc giảm độ dài chương.")
        return "".join(b.text for b in message.content if b.type == "text").strip()

    def text(self, *, system: str, content: list[dict], model: str = None, effort: str = None,
             max_tokens: int = 64000) -> str:
        return self._run(system=system, content=content, model=model or config.MODEL,
                         effort=effort or config.WRITER_EFFORT, max_tokens=max_tokens)

    def parse(self, schema: type[BaseModel], *, system: str, content: list[dict], model: str = None,
              effort: str = None, max_tokens: int = 32000) -> BaseModel:
        raw = self._run(system=system, content=content, model=model or config.MODEL,
                        effort=effort or config.WRITER_EFFORT, max_tokens=max_tokens,
                        output_format={"type": "json_schema", "schema": strict_schema(schema)})
        try:
            return schema.model_validate_json(raw)
        except ValueError as e:
            raise LLMError(f"AI trả về JSON không hợp lệ cho {schema.__name__}: {e}") from e


class MockLLM:
    """Giả lập để chạy thử toàn bộ quy trình mà không gọi API."""

    def __init__(self):
        self.usage = Usage()
        self._seen_reviews = set()

    def text(self, *, system: str, content: list[dict], **_) -> str:
        prompt = content[-1]["text"]
        scenes = re.search(r"BIÊN KỊCH: Viết kịch bản cho các cảnh (\d+)-(\d+)", prompt)
        if scenes:
            return "\n\n".join(f"CẢNH {n}. NỘI. NHÀ BÀ NGOẠI - ĐÊM\n\nMưa gõ lên mái tôn. LAN (20) đếm tiền lẻ.\n\n"
                                 f"LAN: Mai con đi sớm." for n in range(int(scenes[1]), int(scenes[2]) + 1))
        if "TÓM TẮT PHẦN" in prompt:
            return "Tóm tắt phần (giả lập): các nhân vật chính vượt qua thử thách đầu tiên và bí ẩn lớn dần."
        paragraph = ("Gió lùa qua con hẻm nhỏ, mang theo mùi mưa đầu mùa. Anh đứng lặng rất lâu trước cánh cửa gỗ, "
                     "nghe tim mình đập từng nhịp chậm rãi như tiếng đồng hồ cũ trong nhà ngoại. ")
        return "\n\n".join(paragraph * 3 for _ in range(4))

    def parse(self, schema: type[BaseModel], *, content: list[dict] = (), **_) -> BaseModel:
        data = _fake(strict_schema(schema))
        if schema.__name__.endswith("Review"):
            task = content[-1]["text"] if content else ""
            first_time = task not in self._seen_reviews   # lần chấm đầu của mỗi nhiệm vụ chưa đạt -> chạy thử vòng sửa
            self._seen_reviews.add(task)
            data["score"] = 7.0 if first_time else 8.5
            if not first_time:
                data["issues"] = []
        return schema.model_validate(data)


def _fake(node, key=""):
    kind = node.get("type")
    if "enum" in node:
        return node["enum"][-1]
    if kind == "object":
        return {k: _fake(v, k) for k, v in node["properties"].items()}
    if kind == "array":
        return [_fake(node["items"], key) for _ in range(2)]
    if kind == "integer":
        return 1
    if kind == "number":
        return 8.5
    return f"({key} giả lập)"


def make_llm(mock: bool = False):
    return MockLLM() if (mock or config.MOCK) else ClaudeLLM()


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
