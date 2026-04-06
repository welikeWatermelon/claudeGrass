"""토큰 사용 효율 분석 리포트 생성 모듈"""

import datetime
import json
from collections import defaultdict
from pathlib import Path

from claudegrass import parser

REPORT_DIR = Path.home() / ".claudegrass" / "reports"
SUMMARY_DATA_PATH = REPORT_DIR / "summary_data.json"


def generate_report(days: int = 7, today: datetime.date | None = None) -> str:
    """전체 마크다운 분석 리포트를 생성한다."""
    if today is None:
        today = datetime.date.today()

    detailed = parser.parse_detailed_tokens()
    project_data = parser.parse_project_tokens()

    sections = [
        f"# Claude Code 사용 분석 리포트 ({today.isoformat()})\n",
        _today_week_summary(detailed, days, today),
        _efficiency_score(detailed, days, today),
        _project_breakdown(project_data, days, today),
        _anomaly_detection(detailed, project_data, days, today),
        _daily_usage(detailed, days, today),
    ]

    return "\n---\n\n".join(sections)


def save_report(report: str, today: datetime.date | None = None) -> Path:
    """리포트를 ~/.claudegrass/reports/YYYY-MM-DD.md에 저장한다."""
    if today is None:
        today = datetime.date.today()

    month_dir = REPORT_DIR / today.strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)
    path = month_dir / f"{today.isoformat()}.md"
    path.write_text(report, encoding="utf-8")
    return path


def _fmt(n: int) -> str:
    """천 단위 쉼표 포맷"""
    return f"{n:,}"


def _date_range(days: int, today: datetime.date) -> list[datetime.date]:
    """today 포함 최근 days일의 날짜 리스트"""
    return [today - datetime.timedelta(days=i) for i in range(days - 1, -1, -1)]


def _sum_tokens_in_range(detailed: dict, dates: list[datetime.date]) -> dict[str, int]:
    """날짜 범위의 토큰을 합산한다."""
    totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0, "total": 0}
    for d in dates:
        key = d.isoformat()
        if key in detailed:
            for k in totals:
                totals[k] += detailed[key].get(k, 0)
    return totals


def _today_week_summary(detailed: dict, days: int, today: datetime.date) -> str:
    """섹션 1: 오늘/이번 주 사용량 요약"""
    current_dates = _date_range(days, today)
    prev_end = today - datetime.timedelta(days=days)
    prev_dates = _date_range(days, prev_end)

    today_key = today.isoformat()
    today_total = detailed.get(today_key, {}).get("total", 0)

    current_sum = _sum_tokens_in_range(detailed, current_dates)
    prev_sum = _sum_tokens_in_range(detailed, prev_dates)

    week_total = current_sum["total"]
    days_with_data = sum(1 for d in current_dates if d.isoformat() in detailed)
    daily_avg = week_total // days_with_data if days_with_data > 0 else 0

    prev_days_with_data = sum(1 for d in prev_dates if d.isoformat() in detailed)
    prev_daily_avg = prev_sum["total"] // prev_days_with_data if prev_days_with_data > 0 else 0

    if prev_daily_avg > 0:
        pct = today_total / prev_daily_avg * 100
        pct_str = f"오늘 평소 대비 **{pct:.0f}%** 사용 중"
        if pct >= 120:
            pct_str += " ⚠️"
    else:
        pct_str = "이전 기간 데이터 없음"

    lines = [
        "## 오늘 / 이번 주 사용량 요약\n",
        f"- 오늘 사용: **{_fmt(today_total)}** 토큰",
        f"- 최근 {days}일: **{_fmt(week_total)}** 토큰",
        f"- 일평균: **{_fmt(daily_avg)}** 토큰",
        f"- {pct_str}",
    ]
    return "\n".join(lines)


def _efficiency_score(detailed: dict, days: int, today: datetime.date) -> str:
    """섹션 2: 효율 스코어"""
    current_dates = _date_range(days, today)
    prev_end = today - datetime.timedelta(days=days)
    prev_dates = _date_range(days, prev_end)

    def calc_score(token_sum: dict) -> float:
        inp = token_sum["input"]
        cc = token_sum["cache_creation"]
        cr = token_sum["cache_read"]
        out = token_sum["output"]
        denom = inp + cc + cr
        if denom == 0 or inp == 0:
            return 0.0
        cache_hit = cr / denom
        return cache_hit * (out / inp) * 100

    current_sum = _sum_tokens_in_range(detailed, current_dates)
    prev_sum = _sum_tokens_in_range(detailed, prev_dates)

    score = calc_score(current_sum)
    prev_score = calc_score(prev_sum)

    if prev_score > 0:
        change = (score - prev_score) / prev_score * 100
        change_str = f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"
        compare = f" (이전 {days}일: {prev_score:.1f}, {change_str})"
    else:
        compare = ""

    lines = [
        "## 효율 스코어\n",
        f"- 효율 스코어: **{score:.1f}**{compare}",
        f"- 계산식: cache_hit율 × (output / input) × 100",
    ]
    return "\n".join(lines)


def _project_breakdown(project_data: dict, days: int, today: datetime.date) -> str:
    """섹션 3: 프로젝트별 분석"""
    current_dates = _date_range(days, today)
    date_keys = {d.isoformat() for d in current_dates}

    projects = []
    for name, daily in project_data.items():
        totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0, "total": 0}
        for dk in date_keys:
            if dk in daily:
                for k in totals:
                    totals[k] += daily[dk].get(k, 0)
        if totals["total"] == 0:
            continue
        denom = totals["input"] + totals["cache_creation"] + totals["cache_read"]
        cache_hit = (totals["cache_read"] / denom * 100) if denom > 0 else 0
        projects.append((name, totals["total"], cache_hit))

    projects.sort(key=lambda x: x[1], reverse=True)

    lines = [
        f"## 프로젝트별 분석 (최근 {days}일)\n",
    ]
    if not projects:
        lines.append("프로젝트 데이터 없음")
    else:
        for name, total, ch in projects:
            lines.append(f"- **{name}**: {_fmt(total)} 토큰 | cache hit {ch:.0f}%")

    return "\n".join(lines)


def _anomaly_detection(detailed: dict, project_data: dict, days: int, today: datetime.date) -> str:
    """섹션 4: 이상 감지"""
    current_dates = _date_range(days, today)

    # 일평균 계산
    day_totals = []
    for d in current_dates:
        key = d.isoformat()
        day_totals.append(detailed.get(key, {}).get("total", 0))

    non_zero = [t for t in day_totals if t > 0]
    avg = sum(non_zero) / len(non_zero) if non_zero else 0

    lines = ["## 이상 감지\n"]

    # 2배 이상 사용일
    anomaly_days = []
    if avg > 0:
        for d, t in zip(current_dates, day_totals):
            if t >= avg * 2:
                anomaly_days.append((d, t))

    if anomaly_days:
        lines.append("**평소 대비 2배 이상 사용일:**")
        for d, t in anomaly_days:
            lines.append(f"- {d.isoformat()}: {_fmt(t)} 토큰 ({t / avg:.1f}x)")
    else:
        lines.append("- 이상 사용일 없음")

    # 낮은 cache hit 프로젝트
    date_keys = {d.isoformat() for d in current_dates}
    project_cache_hits = []
    for name, daily in project_data.items():
        totals = {"input": 0, "cache_creation": 0, "cache_read": 0, "total": 0}
        for dk in date_keys:
            if dk in daily:
                for k in totals:
                    totals[k] += daily[dk].get(k, 0)
        if totals["total"] == 0:
            continue
        denom = totals["input"] + totals["cache_creation"] + totals["cache_read"]
        ch = (totals["cache_read"] / denom * 100) if denom > 0 else 0
        project_cache_hits.append((name, ch))

    if project_cache_hits:
        overall_avg_ch = sum(c for _, c in project_cache_hits) / len(project_cache_hits)
        low_ch = [(n, c) for n, c in project_cache_hits if c < overall_avg_ch * 0.5]
        if low_ch:
            lines.append("\n**cache hit율 경고 (평균의 50% 이하):**")
            for n, c in low_ch:
                lines.append(f"- {n}: cache hit {c:.0f}% ⚠️")

    return "\n".join(lines)


def _daily_usage(detailed: dict, days: int, today: datetime.date) -> str:
    """섹션 5: 일별 사용량 (분석 기간 내 날짜별)"""
    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    current_dates = _date_range(days, today)

    day_data = []
    for d in current_dates:
        total = detailed.get(d.isoformat(), {}).get("total", 0)
        day_data.append((d, total))

    max_total = max((t for _, t in day_data), default=1) or 1
    bar_max = 20

    lines = [f"## 일별 사용량 (최근 {days}일)\n"]
    for d, total in day_data:
        wd = day_names[d.weekday()]
        bar_len = round(total / max_total * bar_max) if max_total > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{d.month}/{d.day}({wd}) {bar} {_fmt(total)}\n")

    return "\n".join(lines)


# === 월간 요약 (latest.md) ===


def _week_label(today: datetime.date) -> str:
    """주차 라벨 생성: '4/1~4/7' 형태"""
    start = today - datetime.timedelta(days=6)
    return f"{start.month}/{start.day}~{today.month}/{today.day}"


def _calc_week_row(days: int, today: datetime.date) -> dict:
    """이번 주 요약 데이터 1행분을 계산한다."""
    detailed = parser.parse_detailed_tokens()
    project_data = parser.parse_project_tokens()

    current_dates = _date_range(days, today)
    current_sum = _sum_tokens_in_range(detailed, current_dates)

    # 주간 총 토큰
    week_total = current_sum["total"]

    # 일평균
    days_with_data = sum(1 for d in current_dates if d.isoformat() in detailed)
    daily_avg = week_total // days_with_data if days_with_data > 0 else 0

    # 효율 스코어
    inp = current_sum["input"]
    cc = current_sum["cache_creation"]
    cr = current_sum["cache_read"]
    out = current_sum["output"]
    denom = inp + cc + cr
    if denom > 0 and inp > 0:
        cache_hit = cr / denom
        score = cache_hit * (out / inp) * 100
    else:
        score = 0.0

    # 최다 프로젝트
    date_keys = {d.isoformat() for d in current_dates}
    top_project = "-"
    top_tokens = 0
    for name, daily in project_data.items():
        proj_total = sum(daily.get(dk, {}).get("total", 0) for dk in date_keys)
        if proj_total > top_tokens:
            top_tokens = proj_total
            top_project = name

    return {
        "date": today.isoformat(),
        "month": today.strftime("%Y-%m"),
        "label": _week_label(today),
        "week_total": week_total,
        "daily_avg": daily_avg,
        "score": round(score, 1),
        "top_project": top_project,
    }


def _load_summary_data() -> list[dict]:
    """로컬에 저장된 주간 요약 데이터를 불러온다."""
    if SUMMARY_DATA_PATH.exists():
        return json.loads(SUMMARY_DATA_PATH.read_text(encoding="utf-8"))
    return []


def _save_summary_data(data: list[dict]):
    """주간 요약 데이터를 로컬에 저장한다."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_latest(days: int = 7, today: datetime.date | None = None) -> str:
    """이번 달 월간 요약 마크다운(latest.md)을 생성한다.

    매주 실행 시 새 행이 추가되고, 월이 바뀌면 새로 시작한다.
    """
    if today is None:
        today = datetime.date.today()

    current_month = today.strftime("%Y-%m")

    # 기존 데이터 불러오기
    all_data = _load_summary_data()

    # 이번 주 데이터 계산
    row = _calc_week_row(days, today)

    # 같은 날짜 행이 이미 있으면 덮어쓰기
    all_data = [d for d in all_data if d["date"] != today.isoformat()]
    all_data.append(row)
    all_data.sort(key=lambda x: x["date"])

    # 저장
    _save_summary_data(all_data)

    # 이번 달 데이터만 필터
    month_rows = [d for d in all_data if d["month"] == current_month]

    # 마크다운 생성
    month_label = today.strftime("%Y년 %m월")
    lines = [
        f"# Claude Code 월간 요약 ({month_label})\n",
        "| 주간 | 총 토큰 | 일평균 | 효율 스코어 | 변화 | 최다 프로젝트 |",
        "|------|---------|--------|------------|------|-------------|",
    ]

    prev_score = None
    for r in month_rows:
        # 변화율 계산
        if prev_score is not None and prev_score > 0:
            change = (r["score"] - prev_score) / prev_score * 100
            change_str = f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"
        elif prev_score is not None:
            change_str = "-"
        else:
            change_str = "-"

        lines.append(
            f"| {r['label']} "
            f"| {_fmt(r['week_total'])} "
            f"| {_fmt(r['daily_avg'])} "
            f"| {r['score']} "
            f"| {change_str} "
            f"| {r['top_project']} |"
        )
        prev_score = r["score"]

    # 월간 합계
    total = sum(r["week_total"] for r in month_rows)
    avg_score = sum(r["score"] for r in month_rows) / len(month_rows) if month_rows else 0
    lines.append("")
    lines.append(f"**월 누적**: {_fmt(total)} 토큰 | 평균 효율: {avg_score:.1f}")

    return "\n".join(lines)


def save_month_summary(month: str) -> Path | None:
    """지난 달 요약을 summary.md로 보관한다. 해당 월 데이터가 없으면 None."""
    all_data = _load_summary_data()
    month_rows = [d for d in all_data if d["month"] == month]
    if not month_rows:
        return None

    # 해당 월의 latest를 생성 (마지막 날짜 기준)
    last_date = datetime.date.fromisoformat(month_rows[-1]["date"])
    # 임시로 해당 월 데이터만으로 마크다운 생성
    month_label_str = last_date.strftime("%Y년 %m월")
    lines = [
        f"# Claude Code 월간 요약 ({month_label_str})\n",
        "| 주간 | 총 토큰 | 일평균 | 효율 스코어 | 변화 | 최다 프로젝트 |",
        "|------|---------|--------|------------|------|-------------|",
    ]

    prev_score = None
    for r in month_rows:
        if prev_score is not None and prev_score > 0:
            change = (r["score"] - prev_score) / prev_score * 100
            change_str = f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"
        elif prev_score is not None:
            change_str = "-"
        else:
            change_str = "-"
        lines.append(
            f"| {r['label']} "
            f"| {_fmt(r['week_total'])} "
            f"| {_fmt(r['daily_avg'])} "
            f"| {r['score']} "
            f"| {change_str} "
            f"| {r['top_project']} |"
        )
        prev_score = r["score"]

    total = sum(r["week_total"] for r in month_rows)
    avg_score = sum(r["score"] for r in month_rows) / len(month_rows) if month_rows else 0
    lines.append("")
    lines.append(f"**월 누적**: {_fmt(total)} 토큰 | 평균 효율: {avg_score:.1f}")

    summary_content = "\n".join(lines)
    month_dir = REPORT_DIR / month
    month_dir.mkdir(parents=True, exist_ok=True)
    path = month_dir / "summary.md"
    path.write_text(summary_content, encoding="utf-8")
    return path
