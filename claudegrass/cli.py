"""claudeGrass CLI 진입점: 초기 설정(setup), 메인 실행(run), 분석(analyze)"""

import argparse
import datetime
import getpass
import json
import os
import sys
from pathlib import Path

from claudegrass import github, parser, generator, scheduler, analyzer
from claudegrass.generator import COLOR_THEMES

CONFIG_DIR = Path.home() / ".claudegrass"
CONFIG_PATH = CONFIG_DIR / "config.json"


def main():
    args = _parse_args()

    if args.command == "setup":
        cmd_setup()
    elif args.command == "analyze":
        if not CONFIG_PATH.exists():
            print("설정 파일이 없습니다. 초기 설정을 시작합니다.\n")
            cmd_setup()
        cmd_analyze(args)
    else:
        # run (기본값)
        if not CONFIG_PATH.exists():
            print("설정 파일이 없습니다. 초기 설정을 시작합니다.\n")
            cmd_setup()
        cmd_run()


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="claudegrass",
        description="Claude Code 토큰 사용량 GitHub 잔디 시각화 도구",
    )
    sub = ap.add_subparsers(dest="command")
    sub.add_parser("setup", help="초기 설정 (PAT, 레포, 스케줄 시간)")
    sub.add_parser("run", help="토큰 파싱 → SVG 생성 → GitHub push")

    analyze_parser = sub.add_parser("analyze", help="토큰 사용 분석 리포트 생성")
    analyze_parser.add_argument("--upload", action="store_true", help="리포트를 GitHub에 업로드")
    analyze_parser.add_argument("--days", type=int, default=7, help="분석 기간 (기본값: 7일)")

    return ap.parse_args()


def cmd_setup():
    """대화형 초기 설정"""
    print("=== claudeGrass 초기 설정 ===\n")

    pat = getpass.getpass("GitHub Personal Access Token (PAT): ")
    if not pat.strip():
        print("[error] PAT를 입력해야 합니다.")
        sys.exit(1)

    if not github.validate_pat(pat.strip()):
        print("[error] PAT가 유효하지 않습니다. 확인 후 다시 시도해주세요.")
        sys.exit(1)
    print("[ok] PAT 검증 완료")

    repo = input("GitHub 레포지토리 (owner/repo): ").strip()
    # https://github.com/ 접두사 제거
    for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
        if repo.startswith(prefix):
            repo = repo[len(prefix):]
    repo = repo.rstrip("/")
    if repo.endswith(".git"):
        repo = repo[:-4]
    if "/" not in repo:
        print("[error] 'owner/repo' 형식으로 입력해주세요.")
        sys.exit(1)

    # 잔디 SVG 스케줄 (매일)
    hour_input = input("\n잔디 업데이트 시간 (0-23, 기본값 18): ").strip()
    if hour_input == "":
        hour = 18
    else:
        try:
            hour = int(hour_input)
            if not 0 <= hour <= 23:
                raise ValueError
        except ValueError:
            print("[error] 0~23 사이의 숫자를 입력해주세요.")
            sys.exit(1)

    # 분석 리포트 스케줄
    print("\n분석 리포트 주기를 선택하세요:")
    print("  1) weekly - 매주 특정 요일 (기본값)")
    print("  2) daily_interval - N일마다")
    analyze_mode_input = input("모드 (1 또는 2, 기본값 1): ").strip()
    if analyze_mode_input in ("", "1"):
        analyze_mode = "weekly"
    elif analyze_mode_input == "2":
        analyze_mode = "daily_interval"
    else:
        print("[error] 1 또는 2를 입력해주세요.")
        sys.exit(1)

    analyze_interval = 7
    analyze_weekday = 4
    if analyze_mode == "weekly":
        day_names = ["월(0)", "화(1)", "수(2)", "목(3)", "금(4)", "토(5)", "일(6)"]
        print(f"요일 선택: {', '.join(day_names)}")
        wd_input = input("요일 번호 (0-6, 기본값 4/금): ").strip()
        if wd_input == "":
            analyze_weekday = 4
        else:
            try:
                analyze_weekday = int(wd_input)
                if not 0 <= analyze_weekday <= 6:
                    raise ValueError
            except ValueError:
                print("[error] 0~6 사이의 숫자를 입력해주세요.")
                sys.exit(1)
    else:
        interval_input = input("리포트 간격 (일 단위, 기본값 7): ").strip()
        if interval_input == "":
            analyze_interval = 7
        else:
            try:
                analyze_interval = int(interval_input)
                if analyze_interval < 1:
                    raise ValueError
            except ValueError:
                print("[error] 1 이상의 숫자를 입력해주세요.")
                sys.exit(1)

    # 색상 테마 선택
    theme_names = list(COLOR_THEMES.keys())
    print("\n잔디 색상 테마를 선택하세요:")
    for i, name in enumerate(theme_names, 1):
        preview = " ".join(COLOR_THEMES[name][1:])
        print(f"  {i}) {name} ({preview})")
    theme_input = input(f"테마 번호 (1-{len(theme_names)}, 기본값 2/orange): ").strip()
    if theme_input == "":
        theme = "orange"
    else:
        try:
            idx = int(theme_input)
            if not 1 <= idx <= len(theme_names):
                raise ValueError
            theme = theme_names[idx - 1]
        except ValueError:
            print("[error] 올바른 번호를 입력해주세요.")
            sys.exit(1)
    print(f"[ok] 테마 선택: {theme}")

    schedule = {
        "hour": hour,
        "analyze": {
            "mode": analyze_mode,
            "interval_days": analyze_interval,
            "weekday": analyze_weekday,
        },
    }

    config = {
        "github_pat": pat.strip(),
        "repo": repo,
        "schedule": schedule,
        "theme": theme,
    }
    save_config(config)
    print(f"[ok] 설정 저장 완료: {CONFIG_PATH}\n")

    # Windows 작업 스케줄러 등록 (잔디: 매일, 리포트: 설정대로)
    scheduler.register_run_task(hour)
    scheduler.register_analyze_task(schedule["analyze"], hour)

    # README 생성
    github.create_readme(config)

    print("\n설정이 완료되었습니다!")


def cmd_analyze(args):
    """토큰 사용 분석 리포트를 생성하고 출력한다."""
    today = datetime.date.today()
    days = args.days
    month_str = today.strftime("%Y-%m")

    # Windows cp949 콘솔에서 유니코드 출력 보장
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # 1) 주간 상세 리포트
    print(f"[1/3] 주간 리포트 생성 중 (최근 {days}일)...")
    report = analyzer.generate_report(days=days, today=today)
    print(report)
    report_path = analyzer.save_report(report, today=today)
    print(f"\n리포트 저장: {report_path}")

    # 2) 월간 요약 (latest.md) 업데이트
    print(f"\n[2/3] 월간 요약 업데이트 중...")

    # 월이 바뀌었으면 이전 달 summary.md 보관
    prev_month_date = today.replace(day=1) - datetime.timedelta(days=1)
    prev_month = prev_month_date.strftime("%Y-%m")
    if prev_month != month_str:
        summary_path = analyzer.save_month_summary(prev_month)
        if summary_path:
            print(f"  → 이전 달 요약 보관: {summary_path}")

    latest = analyzer.generate_latest(days=days, today=today)
    print(latest)

    # 3) GitHub push
    if args.upload:
        config = load_config()
        date_str = today.isoformat()
        msg = f"chore: update analysis report [{date_str}]"

        print(f"\n[3/3] GitHub push 중...")
        github.push_file(config, f"reports/{month_str}/{date_str}.md", report, message=msg)
        github.push_file(config, "reports/latest.md", latest, message=msg)

        # 이전 달 summary도 push
        prev_summary_path = analyzer.REPORT_DIR / prev_month / "summary.md"
        if prev_summary_path.exists():
            summary_content = prev_summary_path.read_text(encoding="utf-8")
            github.push_file(config, f"reports/{prev_month}/summary.md", summary_content,
                             message=f"chore: archive {prev_month} summary")

        print("업로드 완료!")
    else:
        print("\n(--upload 플래그로 GitHub에 업로드 가능)")


def cmd_run():
    """메인 파이프라인: 파싱 → SVG 생성 → push"""
    config = load_config()

    print("[1/3] 토큰 데이터 파싱 중...")
    token_data = parser.parse_all_tokens()
    if not token_data:
        print("[warn] 토큰 데이터가 없습니다.")

    total_days = len(token_data)
    total_tokens = sum(token_data.values())
    print(f"  → {total_days}일, 총 {total_tokens:,} 토큰")

    print("[2/3] SVG 히트맵 생성 중...")
    svg_content = generator.generate_svg(token_data, theme=config.get("theme"))
    print(f"  → SVG 생성 완료 ({len(svg_content):,} bytes)")

    print("[3/3] GitHub push 중...")
    github.push_file(config, "token-heatmap.svg", svg_content)

    print("\n완료!")


def load_config() -> dict:
    """설정 파일을 읽어 반환한다. 구버전 설정은 자동 마이그레이션한다."""
    if not CONFIG_PATH.exists():
        print(f"[error] 설정 파일이 없습니다: {CONFIG_PATH}")
        print("'claudegrass setup'을 먼저 실행해주세요.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    # 구버전 schedule_hour → 새 schedule 구조 마이그레이션
    if "schedule_hour" in config and "schedule" not in config:
        config["schedule"] = {
            "hour": config.pop("schedule_hour"),
            "analyze": {
                "mode": "weekly",
                "interval_days": 7,
                "weekday": 4,
            },
        }
    return config


def save_config(config: dict):
    """설정을 JSON 파일로 저장한다."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
