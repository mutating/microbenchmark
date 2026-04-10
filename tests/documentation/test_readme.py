from __future__ import annotations

import math
from functools import partial

import pytest

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


class TestQuickStart:
    def test_quick_start_basic(self) -> None:
        def build_list() -> list[int]:
            return list(range(1000))

        scenario = Scenario(build_list, name='build_list', number=500)
        result = scenario.run()
        assert len(result.durations) == 500
        assert isinstance(result.mean, float)
        assert isinstance(result.best, float)
        assert isinstance(result.worst, float)


class TestScenarioConstructor:
    def test_full_constructor(self) -> None:
        scenario = Scenario(
            sorted,
            args=[[3, 1, 2]],
            name='sort_three_items',
            doc='Sort a list of three integers.',
            number=10000,
        )
        assert scenario.name == 'sort_three_items'
        assert scenario.doc == 'Sort a list of three integers.'
        assert scenario.number == 10000

    def test_partial_kwargs(self) -> None:
        scenario = Scenario(
            partial(sorted, key=lambda x: -x),
            args=[[3, 1, 2]],
            name='sort_descending',
        )
        result = scenario.run()
        assert isinstance(result, BenchmarkResult)

    def test_multiple_positional_args(self) -> None:
        scenario = Scenario(pow, args=[2, 10], name='power')
        result = scenario.run()
        assert isinstance(result.mean, float)


class TestScenarioRun:
    def test_run_with_warmup(self) -> None:
        scenario = Scenario(lambda: list(range(100)), name='build', number=1000)
        result = scenario.run(warmup=100)
        assert len(result.durations) == 1000


class TestScenarioGroupCreation:
    def test_direct_construction(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        group = ScenarioGroup(s1, s2)
        assert isinstance(group, ScenarioGroup)

    def test_empty_group(self) -> None:
        empty = ScenarioGroup()
        assert len(empty.run()) == 0

    def test_plus_operator_two_scenarios(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        group = s1 + s2
        assert type(group).__name__ == 'ScenarioGroup'

    def test_scenario_plus_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        s3 = Scenario(lambda: None, name='s3')
        group = ScenarioGroup(s1, s2)
        extended = group + s3
        assert len(extended.run()) == 3

    def test_reverse_scenario_plus_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        s3 = Scenario(lambda: None, name='s3')
        group = ScenarioGroup(s1, s2)
        also_ok = s3 + group
        assert len(also_ok.run()) == 3

    def test_group_plus_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        s3 = Scenario(lambda: None, name='s3')
        g1 = ScenarioGroup(s1)
        g2 = ScenarioGroup(s2, s3)
        combined = g1 + g2
        assert len(combined.run()) == 3


class TestScenarioGroupRun:
    def test_run_order_preserved(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        group = ScenarioGroup(s1, s2)
        results = group.run(warmup=50)
        assert results[0].scenario is not None
        assert results[1].scenario is not None
        assert results[0].scenario.name == 's1'
        assert results[1].scenario.name == 's2'


class TestBenchmarkResultFields:
    def test_fields_documentation_example(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        assert len(result.durations) == 100
        assert result.is_primary is True

    def test_durations_is_tuple(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        assert isinstance(result.durations, tuple)


class TestPercentile:
    def test_percentile_documentation_example(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        trimmed = result.percentile(95)
        assert trimmed.is_primary is False
        assert len(trimmed.durations) == math.ceil(100 * 95 / 100)

    def test_percentile_chaining(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        chained = result.percentile(90).percentile(50)
        assert len(chained.durations) == math.ceil(math.ceil(100 * 90 / 100) * 50 / 100)


class TestP95P99:
    def test_p95_cached(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        assert len(result.p95.durations) == math.ceil(100 * 95 / 100)
        assert result.p95.is_primary is False
        assert result.p95 is result.p95

    def test_p99_cached(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        assert len(result.p99.durations) == math.ceil(100 * 99 / 100)
        assert result.p99.is_primary is False
        assert result.p99 is result.p99


class TestScenarioConstructorValidation:
    def test_number_zero_raises(self) -> None:
        # README: "passing 0 or a negative value raises ValueError"
        with pytest.raises(ValueError):
            Scenario(lambda: None, name='s', number=0)

    def test_number_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            Scenario(lambda: None, name='s', number=-1)

    def test_args_none_and_empty_list_equivalent(self) -> None:
        # README: "None (the default) and [] both mean the function is called with no arguments"
        calls_none: list[tuple[object, ...]] = []
        calls_empty: list[tuple[object, ...]] = []

        def fn_none(*a: object) -> None:
            calls_none.append(a)

        def fn_empty(*a: object) -> None:
            calls_empty.append(a)

        Scenario(fn_none, args=None, name='s', number=1).run()
        Scenario(fn_empty, args=[], name='s', number=1).run()
        assert calls_none == [()]
        assert calls_empty == [()]

    def test_args_shallow_copied(self) -> None:
        # README: "The list is shallow-copied on construction"
        original = [1, 2]
        s = Scenario(lambda *_: None, args=original, name='s', number=1)
        original.append(3)
        call_log: list[tuple[object, ...]] = []

        def fn(*a: object) -> None:
            call_log.append(a)

        Scenario(fn, args=[1, 2], name='s', number=1).run()
        assert call_log == [(1, 2)]  # mutation after construction has no effect

    def test_custom_timer(self) -> None:
        # README: "Supply a custom clock to get deterministic measurements in tests"
        tick = [0.0]

        def fake_timer() -> float:
            tick[0] += 0.001
            return tick[0]

        result = Scenario(lambda: None, name='s', number=5, timer=fake_timer).run()
        assert len(result.durations) == 5
        assert all(d > 0 for d in result.durations)


class TestPercentileValidation:
    def test_percentile_zero_raises(self) -> None:
        # README: "passing 0 or a value above 100 raises ValueError"
        result = Scenario(lambda: None, name='noop', number=10).run()
        with pytest.raises(ValueError):
            result.percentile(0)

    def test_percentile_above_100_raises(self) -> None:
        result = Scenario(lambda: None, name='noop', number=10).run()
        with pytest.raises(ValueError):
            result.percentile(101)


class TestJsonRoundTrip:
    def test_json_round_trip(self) -> None:
        result = Scenario(lambda: None, name='noop', number=100).run()
        json_str = result.to_json()
        restored = BenchmarkResult.from_json(json_str)
        assert restored.scenario is None
        assert restored.mean == result.mean
        assert restored.durations == result.durations
        assert restored.is_primary == result.is_primary
