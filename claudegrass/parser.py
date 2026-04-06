"""JSONL 파싱 모듈: ~/.claude/projects/ 하위 JSONL 파일에서 토큰 사용량 추출"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))


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


def _parse_jsonl_file_detailed(path: Path) -> list[tuple[str, int, int, int, int]]:
    """단일 JSONL 파일에서 assistant 엔트리의 (날짜, input, output, cache_creation, cache_read) 목록을 추출한다."""
    results = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
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
                # UTC → KST 변환
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    date_str = dt.astimezone(KST).strftime("%Y-%m-%d")
                except ValueError:
                    date_str = timestamp[:10]

                usage = entry.get("message", {}).get("usage", {})
                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cc = usage.get("cache_creation_input_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)

                if inp + out + cc + cr > 0:
                    results.append((date_str, inp, out, cc, cr))
    except (OSError, UnicodeDecodeError) as e:
        print(f"[warn] 파일 읽기 실패 {path}: {e}", file=sys.stderr)

    return results


def _parse_jsonl_file(path: Path) -> list[tuple[str, int]]:
    """단일 JSONL 파일에서 assistant 엔트리의 (날짜, 토큰수) 목록을 추출한다."""
    return [(d, i + o + cc + cr) for d, i, o, cc, cr in _parse_jsonl_file_detailed(path)]


def parse_detailed_tokens() -> dict[str, dict[str, int]]:
    """모든 JSONL 파일에서 날짜별 상세 토큰 사용량을 집계한다.

    Returns:
        {"YYYY-MM-DD": {"input": N, "output": N, "cache_creation": N, "cache_read": N, "total": N}}
    """
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return {}

    daily: dict[str, dict[str, int]] = defaultdict(lambda: {
        "input": 0, "output": 0, "cache_creation": 0, "cache_read": 0, "total": 0,
    })

    for jsonl_path in projects_dir.rglob("*.jsonl"):
        for date_str, inp, out, cc, cr in _parse_jsonl_file_detailed(jsonl_path):
            d = daily[date_str]
            d["input"] += inp
            d["output"] += out
            d["cache_creation"] += cc
            d["cache_read"] += cr
            d["total"] += inp + out + cc + cr

    return dict(daily)


def parse_project_tokens() -> dict[str, dict[str, dict[str, int]]]:
    """프로젝트별 날짜별 상세 토큰 사용량을 집계한다.

    Returns:
        {"project_name": {"YYYY-MM-DD": {"input": N, "output": N, "cache_creation": N, "cache_read": N, "total": N}}}
    """
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return {}

    data: dict[str, dict[str, dict[str, int]]] = {}

    for jsonl_path in projects_dir.rglob("*.jsonl"):
        try:
            project_name = jsonl_path.relative_to(projects_dir).parts[0]
        except (ValueError, IndexError):
            continue

        if project_name not in data:
            data[project_name] = defaultdict(lambda: {
                "input": 0, "output": 0, "cache_creation": 0, "cache_read": 0, "total": 0,
            })

        for date_str, inp, out, cc, cr in _parse_jsonl_file_detailed(jsonl_path):
            d = data[project_name][date_str]
            d["input"] += inp
            d["output"] += out
            d["cache_creation"] += cc
            d["cache_read"] += cr
            d["total"] += inp + out + cc + cr

    return {k: dict(v) for k, v in data.items()}
