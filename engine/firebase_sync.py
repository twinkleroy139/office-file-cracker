import os
import time
import json
import urllib.request
import urllib.parse


def _db_url() -> str:
    env_url = os.environ.get("FIREBASE_DB_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    return "https://officecracker-history-default-rtdb.firebaseio.com"


def _auth_query() -> str:
    secret = os.environ.get("FIREBASE_DB_SECRET", "").strip()
    if secret:
        return "?auth=" + urllib.parse.quote(secret, safe="")
    return ""


def sync_job_result(
    job_id: str,
    status: str,
    progress: int = 100,
    cracked_password=None,
    outcome=None,
    engine=None,
    last_line_index=None,
    resumable: bool = False,
) -> bool:
    clean_id = "".join(ch for ch in (job_id or "").strip() if ch.isalnum() or ch in ("_", "-"))
    if not clean_id:
        return False

    payload = {
        "job_id": clean_id,
        "status": status,
        "progress": int(progress),
        "resumable": bool(resumable),
        "updated_at": int(time.time()),
    }
    if cracked_password is not None:
        payload["cracked_password"] = cracked_password
        payload["password_found"] = True
    if outcome is not None:
        payload["outcome"] = outcome
    if engine is not None:
        payload["engine"] = engine
    if last_line_index is not None:
        payload["last_line_index"] = int(last_line_index)

    url = f"{_db_url()}/jobs/{clean_id}.json{_auth_query()}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False