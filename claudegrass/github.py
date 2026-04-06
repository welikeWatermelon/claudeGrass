"""GitHub API 모듈: Contents API를 사용한 파일 push"""

import base64
import datetime

import requests

API_BASE = "https://api.github.com"


def validate_pat(pat: str) -> bool:
    """PAT 유효성을 검증한다."""
    resp = _api_request("GET", f"{API_BASE}/user", pat)
    return resp.status_code == 200


def push_file(config: dict, filepath: str, content: str,
              message: str | None = None) -> bool:
    """GitHub 레포에 파일을 push(생성 또는 업데이트)한다.

    Returns:
        성공 여부
    """
    pat = config["github_pat"]
    repo = config["repo"]
    if message is None:
        today = datetime.date.today().isoformat()
        message = f"chore: update token heatmap {today}"

    url = f"{API_BASE}/repos/{repo}/contents/{filepath}"

    # 기존 파일 SHA 조회
    sha = None
    resp = _api_request("GET", url, pat)
    if resp.status_code == 200:
        sha = resp.json().get("sha")

    # base64 인코딩
    b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

    data = {
        "message": message,
        "content": b64_content,
    }
    if sha:
        data["sha"] = sha

    resp = _api_request("PUT", url, pat, data)
    if resp.status_code in (200, 201):
        print(f"[ok] {filepath} push 완료")
        return True
    else:
        print(f"[error] push 실패 ({resp.status_code}): {resp.text}")
        return False


def create_readme(config: dict) -> bool:
    """README.md를 생성한다 (이미 존재하면 스킵)."""
    pat = config["github_pat"]
    repo = config["repo"]
    url = f"{API_BASE}/repos/{repo}/contents/README.md"

    resp = _api_request("GET", url, pat)
    if resp.status_code == 200:
        print("[info] README.md가 이미 존재합니다. 스킵합니다.")
        return True

    content = "# Claude Token Usage\n\n![Claude Token Usage](./token-heatmap.svg)\n"
    return push_file(config, "README.md", content,
                     message="chore: add README with token heatmap")


def _api_request(method: str, url: str, pat: str,
                 data: dict | None = None) -> requests.Response:
    """GitHub API 요청 헬퍼."""
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
    }
    return requests.request(method, url, headers=headers, json=data, timeout=30)
