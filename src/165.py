from __future__ import annotations

from typing import Iterable, List, Sequence


def _validate_positive_integers(values: Iterable[int], *, name: str) -> List[int]:
    normalized = list(values)
    if not normalized:
        raise ValueError(f"{name} darf nicht leer sein")
    for value in normalized:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} muss nur positive ganze Zahlen enthalten")
    return normalized


def plan_batches(capacities: Sequence[int], jobs: Sequence[int]) -> list[list[int]]:
    """
    Verteilt Job-Groessen greedily auf Fabrik-Batches.

    Jede Kapazitaet beschreibt einen Batch mit fixer Obergrenze.
    Jeder Job muss vollstaendig in genau einen Batch passen.
    Rueckgabe: Liste von Batches; jeder Batch ist eine Liste der zugewiesenen Jobs.
    """
    caps = _validate_positive_integers(capacities, name="capacities")
    work = _validate_positive_integers(jobs, name="jobs")

    batches: list[list[int]] = [[] for _ in caps]
    remaining = caps[:]

    for job in sorted(work, reverse=True):
        for index, free in enumerate(remaining):
            if job <= free:
                batches[index].append(job)
                remaining[index] -= job
                break
        else:
            raise ValueError("jobs koennen mit den gegebenen capacities nicht verteilt werden")

    return batches


def factory_load(batches: Sequence[Sequence[int]]) -> list[int]:
    return [sum(batch) for batch in batches]
# [CRUX-MK]
