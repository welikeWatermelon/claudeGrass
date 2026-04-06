"""claudeGrass CLI 진입점: 초기 설정(setup) 및 메인 실행(run)"""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

from claudegrass import github, parser, generator, scheduler
from claudegrass.generator import COLOR_THEMES

CONFIG_DIR = Path.home() / ".claudegrass"
CONFIG_PATH = CONFIG_DIR / "config.json"


def main():
    args = _parse_args()

    if args.command == "setup":
        cmd_setup()
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

    hour_input = input("자동 실행 시간 (0-23, 기본값 18): ").strip()
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

    config = {
        "github_pat": pat.strip(),
        "repo": repo,
        "schedule_hour": hour,
        "theme": theme,
    }
    save_config(config)
    print(f"[ok] 설정 저장 완료: {CONFIG_PATH}\n")

    # Windows 작업 스케줄러 등록
    scheduler.register_task(hour)

    # README 생성
    github.create_readme(config)

    print("\n설정이 완료되었습니다!")


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
    """설정 파일을 읽어 반환한다."""
    if not CONFIG_PATH.exists():
        print(f"[error] 설정 파일이 없습니다: {CONFIG_PATH}")
        print("'claudegrass setup'을 먼저 실행해주세요.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    """설정을 JSON 파일로 저장한다."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
