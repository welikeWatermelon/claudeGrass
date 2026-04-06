"""Windows 작업 스케줄러 등록 모듈"""

import subprocess
import sys

TASK_NAME_RUN = "ClaudeGrass"
TASK_NAME_ANALYZE = "ClaudeGrassAnalyze"

WEEKDAY_NAMES = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}
WEEKDAY_KR = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}


def register_run_task(hour: int) -> bool:
    """매일 지정 시간에 claudegrass run을 실행하는 작업을 등록한다."""
    python_exe = sys.executable
    command = f'"{python_exe}" -m claudegrass run'
    time_str = f"{hour:02d}:00"

    return _create_task(
        TASK_NAME_RUN, command,
        ["/sc", "daily", "/st", time_str],
        f"잔디 업데이트: 매일 {time_str}",
    )


def register_analyze_task(analyze_schedule: dict, hour: int) -> bool:
    """분석 리포트를 주기적으로 실행하는 작업을 등록한다."""
    python_exe = sys.executable
    command = f'"{python_exe}" -m claudegrass analyze --upload'
    time_str = f"{hour:02d}:00"
    mode = analyze_schedule.get("mode", "weekly")

    if mode == "weekly":
        weekday = analyze_schedule.get("weekday", 4)
        day_name = WEEKDAY_NAMES.get(weekday, "FRI")
        schedule_args = ["/sc", "weekly", "/d", day_name, "/st", time_str]
        desc = f"분석 리포트: 매주 {WEEKDAY_KR.get(weekday, '금')}요일 {time_str}"
    else:
        interval_days = analyze_schedule.get("interval_days", 7)
        schedule_args = ["/sc", "daily", "/st", time_str]
        if interval_days > 1:
            schedule_args.extend(["/mo", str(interval_days)])
            desc = f"분석 리포트: {interval_days}일마다 {time_str}"
        else:
            desc = f"분석 리포트: 매일 {time_str}"

    return _create_task(TASK_NAME_ANALYZE, command, schedule_args, desc)


def _create_task(task_name: str, command: str, schedule_args: list, desc: str) -> bool:
    """schtasks로 작업을 등록한다."""
    schtasks_args = [
        "schtasks", "/create",
        "/tn", task_name,
        "/tr", command,
        *schedule_args,
        "/f",
    ]
    try:
        result = subprocess.run(schtasks_args, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[ok] 스케줄러 등록 완료 ({desc})")
            return True
        else:
            print(f"[error] 스케줄러 등록 실패 ({task_name}): {result.stderr}")
            return False
    except FileNotFoundError:
        print("[error] schtasks를 찾을 수 없습니다. Windows에서만 지원됩니다.")
        return False


def unregister_task(task_name: str = TASK_NAME_RUN) -> bool:
    """등록된 작업을 삭제한다."""
    try:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_task_exists(task_name: str = TASK_NAME_RUN) -> bool:
    """작업이 등록되어 있는지 확인한다."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
