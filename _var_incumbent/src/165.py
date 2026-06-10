"""
Eigenstaendiges Kernmodul fuer die Mission "df-165".

Hinweis:
Ein Dateiname wie `165.py` ist als Python-Modul ladbar, aber die Syntax
`from 165 import ...` ist in Python selbst ungueltig. Das Modul unten ist
trotzdem lauffaehig; der Import im Test muss daher dynamisch erfolgen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CODE_RE = re.compile(r"^\s*df[-_\s]?(\d+)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class MissionCode:
    prefix: str
    number: int

    @property
    def canonical(self) -> str:
        return f"{self.prefix}-{self.number:03d}"


def parse_mission_code(raw: str) -> MissionCode:
    """
    Parst Missionscodes wie 'df-165', 'DF 165' oder 'df_165'.

    >>> parse_mission_code("df-165").canonical
    'df-165'
    """
    if not isinstance(raw, str):
        raise TypeError("raw must be a string")

    match = _CODE_RE.match(raw)
    if not match:
        raise ValueError(f"invalid mission code: {raw!r}")

    number = int(match.group(1))
    return MissionCode(prefix="df", number=number)


def is_target_mission(raw: str, target: int = 165) -> bool:
    """
    True genau dann, wenn `raw` auf die Zielmission zeigt.
    """
    try:
        code = parse_mission_code(raw)
    except (TypeError, ValueError):
        return False
    return code.number == target


def mission_distance(raw: str, target: int = 165) -> int:
    """
    Abstand der Missionsnummer zum Ziel.
    """
    code = parse_mission_code(raw)
    return abs(code.number - target)
# [CRUX-MK]
