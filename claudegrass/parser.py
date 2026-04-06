"""JSONL 파싱 모듈: ~/.claude/projects/ 하위 JSONL 파일에서 토큰 사용량 추출"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def parse_all_tokens() -> dict[str, int]:
    """모든 JSONL 파일에서 날짜별 총 토큰 사용량을 집계한다.

    Returns:
        {"YYYY-MM-DD": total_tokens, ...}
    """
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        print(f"[warn] 디렉토리가 존재하지 않습니다: {projects_dir}", file=sys.stderr)
        return {}

    daily_tokens: dict[str, int] = defaultdict(int)

    for jsonl_path in projects_dir.rglob("*.jsonl"):
        for date_str, tokens in _parse_jsonl_file(jsonl_path):
            daily_tokens[date_str] += tokens

    return dict(daily_tokens)


def _parse_jsonl_file(path: Path) -> list[tuple[str, int]]:
    """단일 JSONL 파일에서 assistant 엔트리의 (날짜, 토큰수) 목록을 추출한다."""
    results = []
    try:
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry.get("type") != "assistant":
                    continue

                timestamp = entry.get("timestamp", "")
                if len(timestamp) < 10:
                    continue
                date_str = timestamp[:10]

                usage = entry.get("message", {}).get("usage", {})
                total = (
                    usage.get("input_tokens", 0)
                    + usage.get("output_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )

                if total > 0:
                    results.append((date_str, total))
    except (OSError, UnicodeDecodeError) as e:
        print(f"[warn] 파일 읽기 실패 {path}: {e}", file=sys.stderr)

    return results
