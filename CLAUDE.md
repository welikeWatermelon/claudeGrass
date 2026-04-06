# claudeGrass

Claude Code 토큰 사용량을 GitHub 잔디(히트맵) SVG로 시각화하는 Python CLI 도구.

## 프로젝트 구조

```
claudeGrass/
├── claudegrass/
│   ├── __init__.py      # 버전 정보
│   ├── cli.py           # 진입점, 초기 설정(setup), 메인 실행(run)
│   ├── parser.py        # ~/.claude/projects/ JSONL 파싱
│   ├── generator.py     # GitHub 스타일 SVG 히트맵 생성
│   ├── github.py        # GitHub Contents API로 SVG push
│   └── scheduler.py     # Windows 작업 스케줄러(schtasks) 등록
├── tests/
├── README.md
├── CLAUDE.md
├── setup.py
└── pyproject.toml
```

## 데이터 흐름

`cli.py` → `parser.py` → `generator.py` → `github.py`

1. parser가 JSONL 파일에서 날짜별 토큰 합산
2. generator가 합산 데이터로 SVG 히트맵 생성
3. github가 SVG를 GitHub 레포에 push

## 설정 파일

- 위치: `~/.claudegrass/config.json`
- 필드: `github_pat`, `repo`, `schedule_hour`

## 컨벤션

- 외부 라이브러리: `requests`만 허용, 나머지는 표준 라이브러리
- Windows 전용 (작업 스케줄러는 `schtasks` 명령어 사용)
- JSONL 파일 읽기 시 반드시 `encoding='utf-8'` 명시
- 토큰 데이터 경로: `entry["message"]["usage"]`
- 타입 필터: `entry["type"] == "assistant"`
