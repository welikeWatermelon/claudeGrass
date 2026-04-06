"""SVG 히트맵 생성 모듈: GitHub contribution graph 스타일 잔디 SVG"""

import datetime

COLOR_THEMES = {
    "green": ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127", "#0e3d16"],
    "orange": ["#ebedf0", "#fdd8b0", "#fdae6b", "#f47a20", "#d94f00", "#8b2f00"],
    "blue": ["#ebedf0", "#c0d6f9", "#73a8f0", "#3b7dd8", "#1b5eb5", "#0a3d7a"],
    "purple": ["#ebedf0", "#d5c8f0", "#a88de0", "#7b4fcf", "#5a2da8", "#3b1278"],
    "pink": ["#ebedf0", "#f9c0d6", "#f073a8", "#d83b7d", "#b51b5e", "#7a0a3d"],
}
DEFAULT_THEME = "orange"
COLORS = COLOR_THEMES[DEFAULT_THEME]
CELL_SIZE = 11
CELL_GAP = 2
CELL_PITCH = CELL_SIZE + CELL_GAP
LEFT_MARGIN = 35
TOP_MARGIN = 20
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # row index → label


def generate_svg(token_data: dict[str, int], theme: str | None = None) -> str:
    """날짜별 토큰 데이터를 받아 GitHub 스타일 히트맵 SVG를 반환한다."""
    colors = COLOR_THEMES.get(theme or DEFAULT_THEME, COLOR_THEMES[DEFAULT_THEME])
    today = datetime.date.today()
    dates, num_weeks = _build_date_list(today)
    thresholds = _calculate_thresholds([token_data.get(d.isoformat(), 0)
                                        for d in dates])

    width = LEFT_MARGIN + num_weeks * CELL_PITCH + 10
    legend_y = TOP_MARGIN + 7 * CELL_PITCH + 10
    height = legend_y + 20

    parts = [
        f'<svg width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">',
        '<style>',
        '  text { font-size: 9px; fill: #767676; '
        'font-family: -apple-system, BlinkMacSystemFont, sans-serif; }',
        '</style>',
    ]

    # 요일 라벨 (Mon, Wed, Fri)
    for row, label in DAY_LABELS.items():
        y = TOP_MARGIN + row * CELL_PITCH + CELL_SIZE - 1
        parts.append(f'<text x="0" y="{y}">{label}</text>')

    # 월 라벨 및 셀 렌더링
    month_labels_added: set[tuple[int, int]] = set()
    for d in dates:
        col = _week_offset(dates[0], d)
        row = _day_row(d)
        x = LEFT_MARGIN + col * CELL_PITCH
        y = TOP_MARGIN + row * CELL_PITCH

        # 월 라벨: 각 월의 첫 번째 등장 주에 표시
        month_key = (d.year, d.month)
        if month_key not in month_labels_added and row == 0:
            month_labels_added.add(month_key)
            parts.append(
                f'<text x="{x}" y="{TOP_MARGIN - 5}">'
                f'{MONTH_NAMES[d.month - 1]}</text>'
            )

        count = token_data.get(d.isoformat(), 0)
        cell_color = _token_to_color(count, thresholds, colors)
        tooltip = f"{d.isoformat()}: {count:,} tokens"
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="2" fill="{cell_color}"><title>{tooltip}</title></rect>'
        )

    # 범례
    num_colors = len(colors)
    legend_width = 30 + num_colors * (CELL_SIZE + 3) + 30
    legend_x = width - legend_width
    parts.append(f'<text x="{legend_x}" y="{legend_y + 10}">Less</text>')
    for i, c in enumerate(colors):
        lx = legend_x + 30 + i * (CELL_SIZE + 3)
        parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL_SIZE}" '
            f'height="{CELL_SIZE}" rx="2" fill="{c}"/>'
        )
    more_x = legend_x + 30 + num_colors * (CELL_SIZE + 3) + 4
    parts.append(f'<text x="{more_x}" y="{legend_y + 10}">More</text>')

    parts.append('</svg>')
    return '\n'.join(parts)


def _build_date_list(today: datetime.date) -> tuple[list[datetime.date], int]:
    """오늘 기준 약 1년치 날짜 리스트를 반환한다.
    시작일은 52주 전의 일요일."""
    # 오늘이 속한 주의 일요일 찾기 (일요일=0)
    days_since_sunday = today.isoweekday() % 7
    this_sunday = today - datetime.timedelta(days=days_since_sunday)
    start_sunday = this_sunday - datetime.timedelta(weeks=52)

    dates = []
    current = start_sunday
    while current <= today:
        dates.append(current)
        current += datetime.timedelta(days=1)

    num_weeks = _week_offset(start_sunday, today) + 1
    return dates, num_weeks


def _week_offset(start_sunday: datetime.date, d: datetime.date) -> int:
    """시작 일요일로부터의 주 오프셋을 반환한다."""
    return (d - start_sunday).days // 7


def _day_row(d: datetime.date) -> int:
    """날짜의 요일을 행 인덱스로 변환한다 (일요일=0, 토요일=6)."""
    return d.isoweekday() % 7


def _calculate_thresholds(values: list[int]) -> list[int]:
    """non-zero 값들의 20/40/60/80 백분위수 임계값을 반환한다 (5단계용)."""
    non_zero = sorted(v for v in values if v > 0)
    if len(non_zero) == 0:
        return [1, 2, 3, 4, 5]
    if len(non_zero) < 5:
        mx = max(non_zero)
        step = max(mx // 5, 1)
        return [step, step * 2, step * 3, step * 4, mx]

    n = len(non_zero)
    return [
        non_zero[n // 5],
        non_zero[2 * n // 5],
        non_zero[3 * n // 5],
        non_zero[4 * n // 5],
        non_zero[-1],
    ]


def _token_to_color(count: int, thresholds: list[int],
                    colors: list[str] | None = None) -> str:
    """토큰 수를 6단계(0~5) 색상으로 변환한다."""
    c = colors or COLORS
    if count == 0:
        return c[0]
    if count <= thresholds[0]:
        return c[1]
    if count <= thresholds[1]:
        return c[2]
    if count <= thresholds[2]:
        return c[3]
    if count <= thresholds[3]:
        return c[4]
    return c[5]
