# claudeGrass

Claude Code의 토큰 사용량을 GitHub 잔디(히트맵) SVG로 시각화하고, 사용 효율 분석 리포트를 자동 생성하는 Python CLI 도구입니다.

## 미리보기

GitHub 레포지토리에 아래와 같은 히트맵이 자동으로 생성됩니다:

![Claude Token Usage](./example.png)

## 주요 기능

| 기능 | 설명 | 자동 주기 |
|------|------|----------|
| **잔디 히트맵** | 토큰 사용량을 GitHub 스타일 SVG로 시각화 | 매일 |
| **주간 분석 리포트** | 사용량 요약, 효율 스코어, 프로젝트별 분석, 이상 감지 | 매주 (설정 가능) |
| **월간 요약** | 주간 데이터를 누적한 월간 요약표 (`latest.md`) | 매주 자동 갱신 |

## 요구사항

| 항목 | 조건 |
|---|---|
| OS | **Windows 전용** (작업 스케줄러 `schtasks` 사용) |
| Python | >= 3.9 |
| Claude Code | 설치 및 사용 이력 필요 (`~/.claude/projects/` 에 JSONL 데이터가 있어야 함) |
| GitHub | Personal Access Token (PAT) 필요, **repo** 스코프 권한 |
| 네트워크 | GitHub API 접근 가능해야 함 |

## 설치

### PyPI에서 설치 (권장)

```bash
pip install claudegrass
```

### 소스에서 설치

```bash
git clone https://github.com/welikeWatermelon/claudeGrass.git
cd claudeGrass
pip install -e .
```

> **참고**: `claudegrass` 명령어가 인식되지 않는 경우, `python -m claudegrass` 로 대체할 수 있습니다.

## 사용법

### 1. 초기 설정

```bash
python -m claudegrass setup
```

아래 항목을 순서대로 입력합니다:

```
=== claudeGrass 초기 설정 ===

GitHub Personal Access Token (PAT): ← ghp_xxxx 붙여넣기 (입력 시 화면에 표시되지 않음)
GitHub 레포지토리 (owner/repo): ← 예: username/claude-usage

잔디 업데이트 시간 (0-23, 기본값 18): ← 매일 잔디 SVG가 push되는 시간

분석 리포트 주기를 선택하세요:
  1) weekly - 매주 특정 요일 (기본값)
  2) daily_interval - N일마다
모드 (1 또는 2, 기본값 1): ← 리포트 생성 주기

요일 번호 (0-6, 기본값 4/금): ← weekly 선택 시 요일 지정 (0=월 ~ 6=일)

잔디 색상 테마를 선택하세요:
  1) green  2) orange  3) blue  4) purple  5) pink
테마 번호 (1-5, 기본값 2/orange):
```

설정 완료 시:
- `~/.claudegrass/config.json` 에 설정이 저장됩니다
- Windows 작업 스케줄러에 **2개 태스크**가 등록됩니다:
  - `ClaudeGrass` — 매일 잔디 SVG 업데이트
  - `ClaudeGrassAnalyze` — 설정한 주기로 분석 리포트 생성 및 push

### 2. 수동 실행

#### 잔디 히트맵 업데이트

```bash
python -m claudegrass run
```

```
[1/3] 토큰 데이터 파싱 중...
  → 36일, 총 460,619,002 토큰
[2/3] SVG 히트맵 생성 중...
  → SVG 생성 완료 (41,431 bytes)
[3/3] GitHub push 중...
[ok] token-heatmap.svg push 완료
```

#### 분석 리포트 생성 (콘솔 출력 + 로컬 저장)

```bash
python -m claudegrass analyze
```

#### 분석 리포트 생성 + GitHub push

```bash
python -m claudegrass analyze --upload
```

#### 분석 기간 변경 (기본 7일)

```bash
python -m claudegrass analyze --days 14
```

### 3. 자동 실행

setup에서 설정한 스케줄에 따라 Windows 작업 스케줄러가 자동 실행합니다:

- **매일**: `claudegrass run` → 잔디 SVG push
- **매주** (또는 설정한 주기): `claudegrass analyze --upload` → 리포트 push

## 분석 리포트 구성

`claudegrass analyze` 실행 시 아래 5개 섹션으로 구성된 리포트가 생성됩니다.

### 1. 오늘 / 이번 주 사용량 요약

```
- 오늘 사용: 234,567 토큰
- 최근 7일: 1,234,567 토큰
- 일평균: 176,367 토큰
- 오늘 평소 대비 133% 사용 중 ⚠️
```

- 이전 동일 기간의 일평균 대비 오늘 사용량을 % 로 표시
- **120% 이상**이면 경고 표시

### 2. 효율 스코어

```
- 효율 스코어: 42.3 (이전 7일: 37.1, +14%)
```

**계산식**:

```
효율 스코어 = cache_hit율 × (output_tokens / input_tokens) × 100
```

- **cache_hit율** = `cache_read_input_tokens / (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)`
- cache_hit율이 높을수록 (캐시 재활용이 많을수록) 효율적
- output/input 비율이 높을수록 (적은 입력으로 많은 출력) 효율적
- 이전 동일 기간 대비 변화율도 함께 표시

### 3. 프로젝트별 분석

```
- KEEPING: 523,421 토큰 | cache hit 43%
- MelloMe: 312,908 토큰 | cache hit 12%
- REPTOPIA: 98,234 토큰 | cache hit 67%
```

- `~/.claude/projects/` 하위 폴더명 기준으로 프로젝트 구분
- 프로젝트별 총 토큰 사용량 및 cache hit율 표시

### 4. 이상 감지

- **일평균의 2배 이상** 사용한 날을 하이라이트
- **전체 평균 cache hit율의 50% 이하**인 프로젝트에 경고 표시

### 5. 일별 사용량

```
4/1(수)                  0
4/2(목) ████████         3,234,567
4/3(금) ████████████████ 6,789,012
4/4(토)                  0
4/5(일) ██               1,234,567
4/6(월) ████████████     5,432,100
4/7(화) ████████████████████ 8,901,234
```

- 분석 기간 내 일별 토큰 사용량을 막대 그래프로 표시
- 날짜와 요일 함께 표시

## 월간 요약 (latest.md)

매주 리포트가 생성될 때 `latest.md`에 한 행씩 추가됩니다:

| 주간 | 총 토큰 | 일평균 | 효율 스코어 | 변화 | 최다 프로젝트 |
|------|---------|--------|------------|------|-------------|
| 4/1~4/7 | 18,134,484 | 2,590,640 | 42.3 | - | my-project |
| 4/8~4/14 | 15,234,567 | 2,176,366 | 45.1 | +7% | my-project |
| 4/15~4/21 | 20,456,789 | 2,922,398 | 38.9 | -14% | other-app |

**월 누적**: 53,825,840 토큰 | 평균 효율: 42.1

- 월이 바뀌면 이전 달 요약이 `summary.md`로 자동 보관되고, `latest.md`는 새 달로 초기화됩니다

## GitHub 레포 구조

스케줄러가 자동으로 아래 파일들을 push합니다:

```
your-repo/
├── token-heatmap.svg              ← 잔디 히트맵 (매일 갱신)
├── README.md
└── reports/
    ├── latest.md                  ← 이번 달 월간 요약 (매주 갱신)
    ├── 2026-04/
    │   ├── 2026-04-07.md          ← 주간 상세 리포트
    │   ├── 2026-04-14.md
    │   └── summary.md             ← 4월 최종 요약 (월말 자동 보관)
    └── 2026-05/
        ├── 2026-05-05.md
        └── ...
```

## 토큰 집계 방식

`~/.claude/projects/` 하위의 모든 JSONL 파일을 순회하며, 각 항목에서 아래 4가지 토큰을 합산합니다:

| 토큰 종류 | 설명 |
|---|---|
| `input_tokens` | 사용자 입력에 사용된 토큰 |
| `output_tokens` | Claude 응답에 사용된 토큰 |
| `cache_creation_input_tokens` | 캐시 생성 시 사용된 토큰 |
| `cache_read_input_tokens` | 캐시 읽기 시 사용된 토큰 |

**날짜별 총 토큰** = `input_tokens` + `output_tokens` + `cache_creation_input_tokens` + `cache_read_input_tokens`

> **시간대**: 모든 날짜는 JSONL의 UTC timestamp를 **한국 시간(KST, UTC+9)** 으로 변환하여 집계합니다.

## 캐시 히트율 (Cache Hit Rate)

캐시 히트율은 전체 입력 토큰 중 캐시에서 읽어온 토큰의 비율입니다:

```
cache_hit율 = cache_read_input_tokens / (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)
```

- **높을수록 토큰 비용 효율적**: 이전 대화 컨텍스트가 캐시에서 재활용되어 토큰 소비가 줄어듦
- **낮다고 나쁜 것은 아님**: 캐시 히트율이 낮은 프로젝트는 다양한 작업을 위해 새 대화를 자주 시작한 것일 수 있음. 새로운 방향의 작업에는 오히려 새 대화가 정확도 면에서 유리함
- 프로젝트별로 cache hit율이 다를 수 있으며, 이는 작업 패턴(긴 대화 vs 짧은 대화 여러 개)의 차이를 반영

## 효율 스코어 해석

```
효율 스코어 = cache_hit율 × (output_tokens / input_tokens) × 100
```

| 요소 | 의미 |
|------|------|
| cache_hit율 높음 | 캐시 재활용이 잘 되고 있음 (반복 입력 감소) |
| output/input 비율 높음 | 적은 입력으로 많은 응답을 얻고 있음 |
| 스코어 높음 | 두 요소가 모두 양호, 토큰을 효율적으로 사용 중 |

> 스코어는 상대적 지표이므로, 절대적인 "좋은 점수"보다는 **주간 변화 추이**를 확인하는 데 활용하세요.

## 색상 테마

5가지 색상 테마를 지원합니다. setup 시 선택할 수 있습니다.

| 테마 | 0단계 (없음) | 1단계 | 2단계 | 3단계 | 4단계 | 5단계 |
|---|---|---|---|---|---|---|
| **green** | ![#ebedf0](https://placehold.co/12x12/ebedf0/ebedf0) `#ebedf0` | ![#c6e48b](https://placehold.co/12x12/c6e48b/c6e48b) `#c6e48b` | ![#7bc96f](https://placehold.co/12x12/7bc96f/7bc96f) `#7bc96f` | ![#239a3b](https://placehold.co/12x12/239a3b/239a3b) `#239a3b` | ![#196127](https://placehold.co/12x12/196127/196127) `#196127` | ![#0e3d16](https://placehold.co/12x12/0e3d16/0e3d16) `#0e3d16` |
| **orange** | ![#ebedf0](https://placehold.co/12x12/ebedf0/ebedf0) `#ebedf0` | ![#fdd8b0](https://placehold.co/12x12/fdd8b0/fdd8b0) `#fdd8b0` | ![#fdae6b](https://placehold.co/12x12/fdae6b/fdae6b) `#fdae6b` | ![#f47a20](https://placehold.co/12x12/f47a20/f47a20) `#f47a20` | ![#d94f00](https://placehold.co/12x12/d94f00/d94f00) `#d94f00` | ![#8b2f00](https://placehold.co/12x12/8b2f00/8b2f00) `#8b2f00` |
| **blue** | ![#ebedf0](https://placehold.co/12x12/ebedf0/ebedf0) `#ebedf0` | ![#c0d6f9](https://placehold.co/12x12/c0d6f9/c0d6f9) `#c0d6f9` | ![#73a8f0](https://placehold.co/12x12/73a8f0/73a8f0) `#73a8f0` | ![#3b7dd8](https://placehold.co/12x12/3b7dd8/3b7dd8) `#3b7dd8` | ![#1b5eb5](https://placehold.co/12x12/1b5eb5/1b5eb5) `#1b5eb5` | ![#0a3d7a](https://placehold.co/12x12/0a3d7a/0a3d7a) `#0a3d7a` |
| **purple** | ![#ebedf0](https://placehold.co/12x12/ebedf0/ebedf0) `#ebedf0` | ![#d5c8f0](https://placehold.co/12x12/d5c8f0/d5c8f0) `#d5c8f0` | ![#a88de0](https://placehold.co/12x12/a88de0/a88de0) `#a88de0` | ![#7b4fcf](https://placehold.co/12x12/7b4fcf/7b4fcf) `#7b4fcf` | ![#5a2da8](https://placehold.co/12x12/5a2da8/5a2da8) `#5a2da8` | ![#3b1278](https://placehold.co/12x12/3b1278/3b1278) `#3b1278` |
| **pink** | ![#ebedf0](https://placehold.co/12x12/ebedf0/ebedf0) `#ebedf0` | ![#f9c0d6](https://placehold.co/12x12/f9c0d6/f9c0d6) `#f9c0d6` | ![#f073a8](https://placehold.co/12x12/f073a8/f073a8) `#f073a8` | ![#d83b7d](https://placehold.co/12x12/d83b7d/d83b7d) `#d83b7d` | ![#b51b5e](https://placehold.co/12x12/b51b5e/b51b5e) `#b51b5e` | ![#7a0a3d](https://placehold.co/12x12/7a0a3d/7a0a3d) `#7a0a3d` |

## 색상 단계 기준

색상 단계는 **고정된 토큰 수가 아니라, 사용자의 실제 데이터를 기반으로 자동 계산**됩니다.

활동이 있는 날의 토큰 사용량을 정렬한 뒤, **백분위수(percentile)** 로 5단계를 나눕니다:

| 단계 | 기준 | 설명 |
|---|---|---|
| 0단계 | 0 토큰 | 해당 날짜에 Claude Code 사용 기록 없음 |
| 1단계 | 하위 ~20% | 가벼운 사용 |
| 2단계 | 하위 ~40% | 보통 사용 |
| 3단계 | 하위 ~60% | 활발한 사용 |
| 4단계 | 하위 ~80% | 매우 활발한 사용 |
| 5단계 | 상위 ~20% | 최고 사용량 |

## 설정 파일

설정은 `~/.claudegrass/config.json` 에 저장됩니다:

```json
{
  "github_pat": "ghp_xxxx...",
  "repo": "username/claude-usage",
  "schedule": {
    "hour": 18,
    "analyze": {
      "mode": "weekly",
      "interval_days": 7,
      "weekday": 4
    }
  },
  "theme": "orange"
}
```

| 필드 | 설명 |
|------|------|
| `github_pat` | GitHub Personal Access Token |
| `repo` | 대상 GitHub 레포지토리 (owner/repo) |
| `schedule.hour` | 잔디 SVG 자동 push 시간 (0-23) |
| `schedule.analyze.mode` | 리포트 주기: `weekly` 또는 `daily_interval` |
| `schedule.analyze.weekday` | weekly 모드에서 실행 요일 (0=월 ~ 6=일) |
| `schedule.analyze.interval_days` | daily_interval 모드에서 실행 간격 (일) |
| `theme` | 잔디 색상 테마 |

설정을 변경하려면 `python -m claudegrass setup`을 다시 실행하면 됩니다.

> **하위 호환**: 이전 버전의 `schedule_hour` 형식 config도 자동으로 새 구조로 마이그레이션됩니다.

## GitHub PAT 발급 방법

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token (classic)** 클릭
3. Note: 아무 이름 (예: `claudegrass`)
4. Expiration: 원하는 만료 기간 선택
5. Scopes: **`repo`** 체크 (전체 저장소 접근 권한)
6. **Generate token** 클릭
7. 생성된 `ghp_xxxx...` 토큰을 복사 (이후 다시 볼 수 없음)

## 프로젝트 구조

```
claudeGrass/
├── claudegrass/
│   ├── __init__.py      # 버전 정보
│   ├── cli.py           # CLI 진입점, 초기 설정 및 메인 실행
│   ├── parser.py        # JSONL 토큰 데이터 파싱 (UTC→KST 변환)
│   ├── analyzer.py      # 사용 효율 분석 리포트 생성
│   ├── generator.py     # GitHub 스타일 SVG 히트맵 생성
│   ├── github.py        # GitHub Contents API 연동
│   └── scheduler.py     # Windows 작업 스케줄러 등록 (2개 태스크)
├── tests/               # 유닛 테스트
├── pyproject.toml       # 패키지 설정
└── setup.py
```

## 제한사항

- **Windows 전용**: 작업 스케줄러 자동 등록이 `schtasks` 명령어를 사용하므로 Windows에서만 동작합니다. macOS/Linux에서는 수동 실행(`python -m claudegrass run`)은 가능하지만, 자동 스케줄링은 지원하지 않습니다.
- **Claude Code 필수**: `~/.claude/projects/` 디렉토리에 JSONL 파일이 있어야 합니다. Claude Code를 사용한 적이 없으면 데이터가 없습니다.
- **PAT 만료**: GitHub PAT에 만료 기간이 설정되어 있으면, 만료 후 push가 실패합니다. 이 경우 새 PAT를 발급받고 `setup`을 다시 실행하세요.
- **외부 의존성**: `requests` 라이브러리만 사용합니다.

## 라이선스

MIT
