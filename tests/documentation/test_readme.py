from __future__ import annotations

import math

import pytest
from full_match import match

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup, a, arguments

# ---------------------------------------------------------------------------
# Quick start
# ---------------------------------------------------------------------------


def test_quick_start_auto_name():
    def build_list():
        return list(range(1000))

    scenario = Scenario(build_list, number=500)

    assert scenario.name == 'build_list'


def test_quick_start_run_produces_correct_count():
    def build_list():
        return list(range(1000))

    scenario = Scenario(build_list, number=500)
    result = scenario.run()

    assert len(result.durations) == 500


def test_quick_start_result_fields_are_floats():
    def build_list():
        return list(range(1000))

    scenario = Scenario(build_list, number=500)
    result = scenario.run()

    assert isinstance(result.mean, float)
    assert isinstance(result.best, float)
    assert isinstance(result.worst, float)


# ---------------------------------------------------------------------------
# arguments class
# ---------------------------------------------------------------------------


def test_arguments_positional():
    args = arguments(3, 1, 2)

    assert args.args == (3, 1, 2)
    assert args.kwargs == {}


def test_arguments_keyword():
    args_with_kw = arguments(3, 1, 2, key=str)

    assert args_with_kw.args == (3, 1, 2)
    assert args_with_kw.kwargs == {'key': str}


def test_arguments_repr_with_keyword():
    assert repr(arguments(1, 2, key='value')) == "arguments(1, 2, key='value')"


def test_arguments_repr_empty():
    assert repr(arguments()) == 'arguments()'


def test_a_alias_is_same_class():
    assert a is arguments


def test_a_alias_creates_arguments():
    instance = a(1, 2, key='v')

    assert isinstance(instance, arguments)


def test_a_alias_usage_in_scenario():
    scenario = Scenario(sorted, a([3, 1, 2]), name='sort')
    result = scenario.run()

    assert isinstance(result, BenchmarkResult)


# ---------------------------------------------------------------------------
# arguments — no-args scenario
# ---------------------------------------------------------------------------


def test_arguments_none_default_calls_with_no_args():
    call_log: list[tuple[object, ...]] = []

    def fn(*args: object) -> None:
        call_log.append(args)

    Scenario(fn, None, name='s', number=1).run()

    assert call_log == [()]


# ---------------------------------------------------------------------------
# Scenario constructor
# ---------------------------------------------------------------------------


def test_full_constructor_with_arguments():
    scenario = Scenario(
        sorted,
        arguments([3, 1, 2]),
        name='sort_three_items',
        doc='Sort a list of three integers.',
        number=10000,
    )

    assert scenario.name == 'sort_three_items'
    assert scenario.doc == 'Sort a list of three integers.'
    assert scenario.number == 10000


def test_auto_name_from_function():
    def my_function():
        return list(range(100))

    scenario = Scenario(my_function)

    assert scenario.name == 'my_function'


def test_lambda_auto_name():
    scenario = Scenario(lambda: None)

    assert scenario.name == '<lambda>'


def test_number_default_is_1000():
    scenario = Scenario(lambda: None, name='s')

    assert scenario.number == 1000


def test_arguments_with_kwargs_in_scenario():
    scenario = Scenario(
        sorted,
        arguments([3, 1, 2], key=lambda x: -x),
        name='sort_descending',
    )
    result = scenario.run()

    assert isinstance(result, BenchmarkResult)


def test_arguments_multiple_positional():
    scenario = Scenario(pow, arguments(2, 10), name='power')
    result = scenario.run()

    assert isinstance(result.mean, float)


def test_custom_timer_deterministic_mean():
    tick = [0.0]

    def fake_timer():
        tick[0] += 0.001
        return tick[0]

    result = Scenario(lambda: None, name='noop', number=5, timer=fake_timer).run()

    assert result.mean == pytest.approx(0.001)


# ---------------------------------------------------------------------------
# Scenario.run()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_run_with_warmup_duration_count():
    scenario = Scenario(lambda: list(range(100)), name='build', number=1000)
    result = scenario.run(warmup=100)

    assert len(result.durations) == 1000


def test_run_with_warmup_total_calls():
    call_count = [0]

    def fn() -> None:
        call_count[0] += 1

    scenario = Scenario(fn, name='counter', number=100)
    scenario.run(warmup=50)

    assert call_count[0] == 150


# ---------------------------------------------------------------------------
# Scenario number validation
# ---------------------------------------------------------------------------


def test_number_zero_raises():
    with pytest.raises(ValueError, match=match('number must be at least 1, got 0')):
        Scenario(lambda: None, name='s', number=0)


def test_number_negative_raises():
    with pytest.raises(ValueError, match=match('number must be at least 1, got -1')):
        Scenario(lambda: None, name='s', number=-1)


# ---------------------------------------------------------------------------
# ScenarioGroup construction
# ---------------------------------------------------------------------------


def test_direct_construction():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    group = ScenarioGroup(s1, s2)

    assert isinstance(group, ScenarioGroup)


def test_empty_group():
    empty = ScenarioGroup()

    assert len(empty.run()) == 0


def test_plus_operator_two_scenarios():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    group = s1 + s2

    assert type(group).__name__ == 'ScenarioGroup'


def test_scenario_plus_group():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    s3 = Scenario(lambda: None, name='s3')
    group = ScenarioGroup(s1, s2)
    extended = group + s3

    assert len(extended.run()) == 3


def test_scenario_plus_group_also_ok():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    s3 = Scenario(lambda: None, name='s3')
    group = ScenarioGroup(s1, s2)
    also_ok = s3 + group

    assert len(also_ok.run()) == 3


def test_group_plus_group():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    s3 = Scenario(lambda: None, name='s3')
    g1 = ScenarioGroup(s1)
    g2 = ScenarioGroup(s2, s3)
    combined = g1 + g2

    assert len(combined.run()) == 3


# ---------------------------------------------------------------------------
# ScenarioGroup.run()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_run_order_preserved():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    group = ScenarioGroup(s1, s2)
    results = group.run(warmup=50)

    assert results[0].scenario is not None
    assert results[1].scenario is not None
    assert results[0].scenario.name == 's1'
    assert results[1].scenario.name == 's2'


# ---------------------------------------------------------------------------
# BenchmarkResult fields
# ---------------------------------------------------------------------------


def test_benchmark_result_fields_basic():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert len(result.durations) == 100
    assert result.is_primary is True


def test_benchmark_result_durations_is_tuple():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert isinstance(result.durations, tuple)


def test_benchmark_result_median_is_float():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert isinstance(result.median, float)


# ---------------------------------------------------------------------------
# percentile()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_percentile_documentation_example():
    result = Scenario(lambda: None, name='noop', number=100).run()
    trimmed = result.percentile(95)

    assert trimmed.is_primary is False
    assert len(trimmed.durations) == 95


def test_percentile_chaining():
    result = Scenario(lambda: None, name='noop', number=100).run()
    chained = result.percentile(90).percentile(50)

    assert len(chained.durations) == math.ceil(math.ceil(100 * 90 / 100) * 50 / 100)


def test_percentile_zero_raises():
    result = Scenario(lambda: None, name='noop', number=10).run()

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(0)


def test_percentile_above_100_raises():
    result = Scenario(lambda: None, name='noop', number=10).run()

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(101)


# ---------------------------------------------------------------------------
# p95 and p99
# ---------------------------------------------------------------------------


def test_p95_duration_count():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert len(result.p95.durations) == math.ceil(100 * 95 / 100)


def test_p95_is_not_primary():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert result.p95.is_primary is False


def test_p95_is_cached():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert result.p95 is result.p95


def test_p99_duration_count():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert len(result.p99.durations) == math.ceil(100 * 99 / 100)


def test_p99_is_not_primary():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert result.p99.is_primary is False


def test_p99_is_cached():
    result = Scenario(lambda: None, name='noop', number=100).run()

    assert result.p99 is result.p99


# ---------------------------------------------------------------------------
# to_json() and from_json()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_json_round_trip_scenario_is_none():
    result = Scenario(lambda: None, name='noop', number=100).run()
    json_str = result.to_json()
    restored = BenchmarkResult.from_json(json_str)

    assert restored.scenario is None


def test_json_round_trip_mean_preserved():
    result = Scenario(lambda: None, name='noop', number=100).run()
    json_str = result.to_json()
    restored = BenchmarkResult.from_json(json_str)

    assert restored.mean == result.mean


def test_json_round_trip_durations_preserved():
    result = Scenario(lambda: None, name='noop', number=100).run()
    json_str = result.to_json()
    restored = BenchmarkResult.from_json(json_str)

    assert restored.durations == result.durations


def test_json_round_trip_is_primary_preserved():
    result = Scenario(lambda: None, name='noop', number=100).run()
    json_str = result.to_json()
    restored = BenchmarkResult.from_json(json_str)

    assert restored.is_primary == result.is_primary


def test_json_round_trip_median_preserved():
    result = Scenario(lambda: None, name='noop', number=100).run()
    json_str = result.to_json()
    restored = BenchmarkResult.from_json(json_str)

    assert restored.median == result.median
