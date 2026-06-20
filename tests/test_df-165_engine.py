"""Test for DF-165 Familiencockpit Engine [CRUX-MK]"""
import importlib.util, sys, os, re
from pathlib import Path

DF_DIR = Path(__file__).parent.parent
DF_NAME = "df-165"
ENGINE = DF_DIR / f"{DF_NAME}-engine.py"


def _load():
    spec = importlib.util.spec_from_file_location("engine", str(ENGINE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["engine"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_engine_imports():
    """Engine kann ohne Fehler geladen werden."""
    mod = _load()
    assert hasattr(mod, "collect_family_status")


def test_iso_now():
    mod = _load()
    assert hasattr(mod, "iso_now")
    ts = mod.iso_now()
    assert "T" in ts and ":" in ts


def test_family_metrics_defaults():
    mod = _load()
    metrics = mod.FamilyMetrics()
    assert metrics.df == "DF-165"
    assert metrics.offene_entscheidungen == 0


def test_collect_family_status_parses_board():
    """Testet ob das Board korrekt geparst wird."""
    mod = _load()
    # Mock data dir
    data_dir = DF_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    board_path = data_dir / "FAMILIENBOARD.md"
    board_path.write_text("## Offene Entscheidungen\n- [ ] Eine Entscheidung\n- [ ] Noch eine")
    
    metrics = mod.collect_family_status()
    assert metrics.offene_entscheidungen == 2


def test_k12_provenance():
    mod = _load()
    res = mod.k12_provenance(b"hello world")
    assert "payload_hash" in res
    assert "hmac_sha256" in res


def test_write_report():
    mod = _load()
    metrics = mod.FamilyMetrics(iso_timestamp=mod.iso_now())
    report_path = mod.write_report(metrics)
    assert report_path.exists()
    assert "df-165-cockpit" in report_path.name


def test_main_execution():
    """main() returns 0 on success."""
    mod = _load()
    # Mock data for board
    board_path = DF_DIR / "data" / "FAMILIENBOARD.md"
    board_path.write_text("## Offene Entscheidungen\n- [ ] Item")
    
    rc = mod.main()
    assert rc == 0


def test_no_auto_decision_in_source():
    """Source darf keine Auto-Decision-Patterns enthalten."""
    src = ENGINE.read_text(encoding="utf-8").lower()
    forbidden = ["def auto_decide", "def auto_recommend", "def auto_apply", "def execute_decision"]
    for f in forbidden:
        assert f not in src, f"Forbidden auto-decision: {f}"
