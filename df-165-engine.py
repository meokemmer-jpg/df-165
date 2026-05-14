"""DF-165 engine for LexVance-DBA-Position-Tracker."""

import re
import os
import json
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone


DF_DIR = Path(__file__).parent
LOCK_DIR = Path("/tmp/df-165.lock")
DF_ID = "165"
DECISION_KEYWORDS_REGEX = re.compile(
    r"\b(entscheid[a-z]*|empfehl(?:e|en|t|st)|sollt(?:e|en|est)|recommend[a-z]*|decid[a-z]*|advis[a-z]*|propos[a-z]*)\b",
    re.IGNORECASE,
)

_LOCK_OWNER_FILE = LOCK_DIR / "owner.json"


@dataclass
class TrackerOutput:
    welle: str = "25"
    df: str = "DF-165"
    iso_timestamp: str = ""
    source: str = "mock"
    clients_with_us_residence: int = 0
    dba_positions_active: int = 0
    dba_optimizations_pending: list = field(default_factory=list)
    treaty_changes_24m: list = field(default_factory=list)
    mandant_review_due: dict = field(default_factory=dict)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_stable(path, min_age_sec=300) -> bool:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return False
    try:
        age = time.time() - p.stat().st_mtime
    except OSError:
        return False
    return age >= min_age_sec


def acquire_lock_with_identity() -> bool:
    stale_after_sec = 6 * 60 * 60

    try:
        LOCK_DIR.mkdir(mode=0o700)
    except FileExistsError:
        try:
            age = time.time() - LOCK_DIR.stat().st_mtime
        except OSError:
            return False

        if age < stale_after_sec:
            return False

        try:
            for child in LOCK_DIR.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
            LOCK_DIR.rmdir()
            LOCK_DIR.mkdir(mode=0o700)
        except OSError:
            return False
    except OSError:
        return False

    identity = {
        "df_id": DF_ID,
        "pid": os.getpid(),
        "created_at": iso_now(),
        "cwd": os.getcwd(),
    }

    try:
        _LOCK_OWNER_FILE.write_text(json.dumps(identity, indent=2, sort_keys=True), encoding="utf-8")
    except OSError:
        release_lock()
        return False

    return True


def release_lock() -> None:
    try:
        if _LOCK_OWNER_FILE.exists():
            _LOCK_OWNER_FILE.unlink()
    except OSError:
        pass

    try:
        LOCK_DIR.rmdir()
    except OSError:
        pass


def k17_pre_action_verification(anchors) -> dict:
    missing = []

    for anchor in anchors or []:
        text = str(anchor)
        if text.startswith("env:"):
            key = text.split(":", 1)[1]
            if not os.environ.get(key):
                missing.append(text)
        elif text.startswith("file:"):
            path = Path(text.split(":", 1)[1])
            if not path.exists():
                missing.append(text)
        elif text.startswith("dir:"):
            path = Path(text.split(":", 1)[1])
            if not path.exists() or not path.is_dir():
                missing.append(text)
        else:
            path = Path(text)
            if not path.exists():
                missing.append(text)

    return {
        "ok": len(missing) == 0,
        "missing_anchors": missing,
        "env_tag": "real-api" if _is_real_api_enabled() else "mock",
    }


def _is_real_api_enabled() -> bool:
    raw = os.environ.get("DF_165_REAL_API_ENABLED", "false")
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def scan_output_for_decision_keywords(text) -> list:
    if text is None:
        return []
    found = []
    seen = set()
    for match in DECISION_KEYWORDS_REGEX.finditer(str(text)):
        token = match.group(0)
        key = token.lower()
        if key not in seen:
            seen.add(key)
            found.append(token)
    return found


def assert_no_decision_keywords(output) -> None:
    hits = scan_output_for_decision_keywords(output)
    if hits:
        raise ValueError("Q_0/K_0 blocked decision keyword(s): " + ", ".join(hits))


def _load_real_api_payload() -> dict:
    raw = os.environ.get("DF_165_REAL_API_PAYLOAD", "").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("DF_165_REAL_API_PAYLOAD must be a JSON object")
    return data


def _as_int(data, key, default=0) -> int:
    value = data.get(key, default)
    if value in ("", None):
        return default
    return int(value)


def _as_list(data, key) -> list:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(key + " must be a list")
    return value


def _as_dict(data, key) -> dict:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(key + " must be a dict")
    return value


def collect_tracker_output() -> TrackerOutput:
    output = TrackerOutput(iso_timestamp=iso_now())

    if not _is_real_api_enabled():
        return output

    data = _load_real_api_payload()
    output.source = "real_api"
    output.clients_with_us_residence = _as_int(data, "clients_with_us_residence")
    output.dba_positions_active = _as_int(data, "dba_positions_active")
    output.dba_optimizations_pending = _as_list(data, "dba_optimizations_pending")
    output.treaty_changes_24m = _as_list(data, "treaty_changes_24m")
    output.mandant_review_due = _as_dict(data, "mandant_review_due")
    return output


def _write_report(output: TrackerOutput) -> Path:
    report_dir = DF_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = report_dir / f"df-165-{date_tag}.json"

    payload = json.dumps(asdict(output), indent=2, sort_keys=True, ensure_ascii=False)
    assert_no_decision_keywords(payload)

    tmp_path = report_path.with_suffix(".json.tmp")
    tmp_path.write_text(payload + "\n", encoding="utf-8")
    os.replace(tmp_path, report_path)
    return report_path


def main() -> int:
    if not acquire_lock_with_identity():
        return 3

    try:
        pav = k17_pre_action_verification([f"dir:{DF_DIR}"])
        if not pav.get("ok"):
            return 3

        output = collect_tracker_output()
        _write_report(output)
        return 0
    except Exception as exc:
        print(f"DF-165 failed: {exc}", file=sys.stderr)
        return 3
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())