import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
# `from 165 import ...` ist in Python ungueltige Syntax.
# Fuer einen real gruenden pytest-Test muss deshalb dynamisch importiert werden.

import importlib.util
import pathlib


def _load_module():
    path = pathlib.Path(__file__).with_name("165.py")
    spec = importlib.util.spec_from_file_location("165", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


mod = _load_module()
parse_mission_code = mod.parse_mission_code
is_target_mission = mod.is_target_mission
mission_distance = mod.mission_distance


def test_parse_and_canonicalize():
    code = parse_mission_code("DF 165")
    assert code.prefix == "df"
    assert code.number == 165
    assert code.canonical == "df-165"


def test_target_detection():
    assert is_target_mission("df-165") is True
    assert is_target_mission("df_164") is False
    assert is_target_mission("invalid") is False


def test_distance():
    assert mission_distance("df-165") == 0
    assert mission_distance("df-170") == 5
    assert mission_distance("df-160") == 5

