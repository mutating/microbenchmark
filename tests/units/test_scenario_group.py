from __future__ import annotations

import pytest
from full_match import match

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


def _make_scenario(name: str = 's', number: int = 5) -> Scenario:
    return Scenario(lambda: None, name=name, number=number)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_empty_group():
    group = ScenarioGroup()

    assert isinstance(group, ScenarioGroup)


def test_single_scenario():
    scenario = _make_scenario('s1')
    group = ScenarioGroup(scenario)
    results = group.run()

    assert len(results) == 1


def test_multiple_scenarios():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = ScenarioGroup(s1, s2, s3)
    results = group.run()

    assert len(results) == 3


# ---------------------------------------------------------------------------
# + operator
# ---------------------------------------------------------------------------


def test_scenario_plus_scenario():
    s1, s2 = _make_scenario('s1'), _make_scenario('s2')
    group = s1 + s2

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 2
    assert results[0].scenario is s1
    assert results[1].scenario is s2


def test_group_plus_scenario():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = ScenarioGroup(s1, s2) + s3

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 3
    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_scenario_plus_group():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = s1 + ScenarioGroup(s2, s3)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 3
    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_group_plus_group():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = ScenarioGroup(s1) + ScenarioGroup(s2, s3)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 3
    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_triple_sum_is_flat():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = s1 + s2 + s3

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 3
    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_add_returns_new_group():
    s1, s2 = _make_scenario('s1'), _make_scenario('s2')
    original_group = ScenarioGroup(s1)
    new_group = original_group + s2

    assert new_group is not original_group
    assert len(original_group._scenarios) == 1
    assert new_group._scenarios[0] is s1
    assert new_group._scenarios[1] is s2


def test_add_unknown_type_returns_not_implemented():
    group = ScenarioGroup()
    result = group.__add__(42)  # type: ignore[arg-type]

    assert result is NotImplemented


def test_radd_unknown_type_returns_not_implemented():
    group = ScenarioGroup()
    result = group.__radd__(42)  # type: ignore[arg-type]

    assert result is NotImplemented


def test_radd_scenario_to_group():
    s1, s2 = _make_scenario('s1'), _make_scenario('s2')
    group_input = ScenarioGroup(s1)
    group = group_input.__radd__(s2)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 2
    assert results[0].scenario is s2
    assert results[1].scenario is s1


def test_radd_group_to_group():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    g1 = ScenarioGroup(s1, s2)
    g2 = ScenarioGroup(s3)
    group = g2.__radd__(g1)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert len(results) == 3
    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_duplicate_scenarios():
    scenario = _make_scenario('s')
    group = scenario + scenario
    results = group.run()

    assert len(results) == 2


def test_multiple_groups_flat():
    scenarios = [_make_scenario(f's{i}') for i in range(5)]
    g1 = ScenarioGroup(scenarios[0], scenarios[1])
    g2 = ScenarioGroup(scenarios[2], scenarios[3])
    g3 = ScenarioGroup(scenarios[4])
    combined = g1 + g2 + g3

    assert len(combined.run()) == 5


# ---------------------------------------------------------------------------
# run()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_run_returns_list():
    group = ScenarioGroup()
    result = group.run()

    assert isinstance(result, list)


def test_empty_group_returns_empty_list():
    group = ScenarioGroup()

    assert group.run() == []


def test_empty_group_run_with_warmup():
    group = ScenarioGroup()

    assert group.run(warmup=10) == []


def test_run_negative_warmup_acts_as_zero():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=3)
    group = ScenarioGroup(scenario)
    results = group.run(warmup=-5)

    assert len(results) == 1
    assert len(results[0].durations) == 3
    assert counter[0] == 3


def test_run_returns_benchmark_results():
    scenario = _make_scenario()
    group = ScenarioGroup(scenario)
    results = group.run()

    for result in results:
        assert isinstance(result, BenchmarkResult)


def test_run_order_preserved():
    s1, s2, s3 = _make_scenario('s1'), _make_scenario('s2'), _make_scenario('s3')
    group = ScenarioGroup(s1, s2, s3)
    results = group.run()

    assert results[0].scenario is s1
    assert results[1].scenario is s2
    assert results[2].scenario is s3


def test_run_with_warmup():
    counters = [0, 0]

    def make_fn(idx: int) -> object:
        def fn() -> None:
            counters[idx] += 1
        return fn

    s1 = Scenario(make_fn(0), name='a', number=5)  # type: ignore[arg-type]
    s2 = Scenario(make_fn(1), name='b', number=5)  # type: ignore[arg-type]
    group = ScenarioGroup(s1, s2)
    results = group.run(warmup=3)

    assert counters[0] == 8
    assert counters[1] == 8
    for result in results:
        assert len(result.durations) == 5


def test_run_correct_scenario_reference():
    s1, s2 = _make_scenario('s1'), _make_scenario('s2')
    group = ScenarioGroup(s1, s2)
    results = group.run()

    assert results[0].scenario is s1
    assert results[1].scenario is s2


def test_run_warmup_different_numbers():
    s1 = Scenario(lambda: None, name='a', number=3)
    s2 = Scenario(lambda: None, name='b', number=7)
    group = ScenarioGroup(s1, s2)
    results = group.run(warmup=2)

    assert len(results[0].durations) == 3
    assert len(results[1].durations) == 7


def test_run_propagates_exception_from_scenario():
    def bad() -> None:
        raise RuntimeError('scenario failed')

    s1 = _make_scenario('s1')
    s2 = Scenario(bad, name='s2', number=1)
    group = ScenarioGroup(s1, s2)

    with pytest.raises(RuntimeError, match=match('scenario failed')):
        group.run()
