import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
# [CRUX-MK]
from importlib import import_module

_mod = import_module("165")
plan_batches = _mod.plan_batches
factory_load = _mod.factory_load


def test_plan_batches_assigns_all_jobs_without_exceeding_capacity():
    capacities = [10, 8, 6]
    jobs = [6, 4, 3, 3, 2, 2]

    batches = plan_batches(capacities, jobs)

    assert sorted(job for batch in batches for job in batch) == sorted(jobs)
    assert factory_load(batches) == [10, 8, 2]
    assert all(load <= capacity for load, capacity in zip(factory_load(batches), capacities))


def test_plan_batches_rejects_impossible_distribution():
    capacities = [5, 5]
    jobs = [6, 2]

    try:
        plan_batches(capacities, jobs)
    except ValueError as exc:
        assert "nicht verteilt" in str(exc)
    else:
        raise AssertionError("ValueError wurde erwartet")
