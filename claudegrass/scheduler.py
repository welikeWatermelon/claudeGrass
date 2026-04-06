"""Windows 작업 스케줄러 등록 모듈"""

import subprocess
import sys

TASK_NAME = "ClaudeGrass"


def register_task(hour: int) -> bool:
    """매일 지정 시간에 claudegrass run을 실행하는 작업을 등록한다."""
    python_exe = sys.executable
    command = f'"{python_exe}" -m claudegrass run'
    time_str = f"{hour:02d}:00"

    try:
        result = subprocess.run(
            [
                "schtasks", "/create",
                "/tn", TASK_NAME,
                "/tr", command,
                "/sc", "daily",
                "/st", time_str,
                "/f",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"[ok] 작업 스케줄러 등록 완료 (매일 {time_str})")
            return True
        else:
            print(f"[error] 스케줄러 등록 실패: {result.stderr}")
            return False
    except FileNotFoundError:
        print("[error] schtasks를 찾을 수 없습니다. Windows에서만 지원됩니다.")
        return False


def unregister_task() -> bool:
    """등록된 작업을 삭제한다."""
    try:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_task_exists() -> bool:
    """작업이 등록되어 있는지 확인한다."""
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
