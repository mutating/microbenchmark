from __future__ import annotations

import pytest

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


class TestScenarioConstruction:
    def test_minimal_construction(self) -> None:
        s = Scenario(lambda: None, name='minimal')
        assert s.name == 'minimal'

    def test_full_construction(self) -> None:
        timer_calls = [0.0]

        def fake_timer() -> float:
            timer_calls[0] += 0.001
            return timer_calls[0]

        s = Scenario(
            sum,
            args=[[1, 2, 3]],
            name='full',
            doc='A full scenario',
            number=50,
            timer=fake_timer,
        )
        assert s.name == 'full'
        assert s.doc == 'A full scenario'

    def test_name_stored(self) -> None:
        s = Scenario(lambda: None, name='myname')
        assert s.name == 'myname'

    def test_doc_stored(self) -> None:
        s = Scenario(lambda: None, name='s', doc='my doc')
        assert s.doc == 'my doc'

    def test_doc_default_empty(self) -> None:
        s = Scenario(lambda: None, name='s')
        assert s.doc == ''

    def test_number_default(self) -> None:
        s = Scenario(lambda: None, name='s')
        assert s.number == 1000

    def test_number_custom(self) -> None:
        s = Scenario(lambda: None, name='s', number=42)
        assert s.number == 42

    def test_args_none_default(self) -> None:
        call_log: list[tuple[object, ...]] = []

        def fn(*a: object) -> None:
            call_log.append(a)

        s = Scenario(fn, name='s', number=1)
        s.run()
        assert call_log == [()]

    def test_args_empty_list(self) -> None:
        call_log: list[tuple[object, ...]] = []

        def fn(*a: object) -> None:
            call_log.append(a)

        s = Scenario(fn, args=[], name='s', number=1)
        s.run()
        assert call_log == [()]

    def test_args_with_values(self) -> None:
        call_log: list[tuple[object, ...]] = []

        def fn(*a: object) -> None:
            call_log.append(a)

        s = Scenario(fn, args=[1, 2, 3], name='s', number=1)
        s.run()
        assert call_log == [(1, 2, 3)]

    def test_args_copied_on_construction(self) -> None:
        call_log: list[tuple[object, ...]] = []

        def fn(*a: object) -> None:
            call_log.append(a)

        original = [10, 20]
        s = Scenario(fn, args=original, name='s', number=1)
        original.append(30)  # mutate after construction
        s.run()
        assert call_log == [(10, 20)]  # should not include 30

    def test_number_zero_raises(self) -> None:
        with pytest.raises(ValueError, match='number'):
            Scenario(lambda: None, name='s', number=0)

    def test_number_negative_raises(self) -> None:
        with pytest.raises(ValueError, match='number'):
            Scenario(lambda: None, name='s', number=-1)

    def test_name_required_raises(self) -> None:
        with pytest.raises(TypeError, match='required keyword-only argument'):
            Scenario(lambda: None)  # type: ignore[call-arg]

    def test_run_negative_warmup_acts_as_zero(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=3)
        result = s.run(warmup=-5)
        assert len(result.durations) == 3
        assert counter[0] == 3  # negative warmup = range(-5) = empty, silently ignored


class TestScenarioRun:
    def test_run_returns_benchmark_result(self) -> None:
        s = Scenario(lambda: None, name='s', number=5)
        result = s.run()
        assert isinstance(result, BenchmarkResult)

    def test_run_calls_function_number_times(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=7)
        s.run()
        assert counter[0] == 7

    def test_run_durations_length_equals_number(self) -> None:
        s = Scenario(lambda: None, name='s', number=10)
        result = s.run()
        assert len(result.durations) == 10

    def test_run_with_warmup_total_calls(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=5)
        s.run(warmup=3)
        assert counter[0] == 8

    def test_run_warmup_not_in_durations(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=5)
        result = s.run(warmup=10)
        assert len(result.durations) == 5
        assert counter[0] == 15  # 10 warmup + 5 measured

    def test_run_warmup_zero(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=5)
        s.run(warmup=0)
        assert counter[0] == 5

    def test_run_uses_custom_timer(self) -> None:
        # timer produces: 0.000, 0.001, 0.002, 0.003, 0.004, 0.005, ...
        # each measured interval: end - start = 0.001
        values = iter(t * 0.001 for t in range(200))

        def fake_timer() -> float:
            return next(values)

        s = Scenario(lambda: None, name='s', number=3, timer=fake_timer)
        result = s.run()
        assert result.durations == pytest.approx((0.001, 0.001, 0.001))

    def test_custom_timer_stateful(self) -> None:
        # timer is called before and after each run; warmup also consumes timer calls
        tick = [0]

        def fake_timer() -> float:
            tick[0] += 1
            return float(tick[0])

        s = Scenario(lambda: None, name='s', number=3, timer=fake_timer)
        result = s.run(warmup=2)
        # 2 warmup * 2 timer calls + 3 measured * 2 timer calls = 10 total timer calls
        assert tick[0] == 10
        # only the 3 measured durations should be stored
        assert len(result.durations) == 3

    def test_run_result_scenario_is_self(self) -> None:
        s = Scenario(lambda: None, name='s', number=5)
        result = s.run()
        assert result.scenario is s

    def test_run_twice_independent(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1

        s = Scenario(fn, name='s', number=5)
        r1 = s.run()
        r2 = s.run()
        assert len(r1.durations) == 5
        assert len(r2.durations) == 5
        assert r1 is not r2

    def test_run_propagates_exception(self) -> None:
        def bad() -> None:
            raise RuntimeError('oops')

        s = Scenario(bad, name='s', number=1)
        with pytest.raises(RuntimeError, match='oops'):
            s.run()

    def test_run_result_is_primary(self) -> None:
        s = Scenario(lambda: None, name='s', number=5)
        result = s.run()
        assert result.is_primary is True

    def test_run_args_incompatible_raises_type_error(self) -> None:
        s = Scenario(lambda: None, args=[1, 2], name='s', number=1)
        with pytest.raises(TypeError, match='positional argument'):
            s.run()

    def test_run_exception_mid_iteration(self) -> None:
        counter = [0]

        def fn() -> None:
            counter[0] += 1
            if counter[0] == 3:
                raise RuntimeError('fail on 3rd call')

        s = Scenario(fn, name='s', number=5)
        with pytest.raises(RuntimeError, match='fail on 3rd call'):
            s.run()
        assert counter[0] == 3


class TestScenarioAdd:
    def test_add_scenario_returns_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        group = s1 + s2
        assert isinstance(group, ScenarioGroup)

    def test_add_scenario_group_returns_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        g = ScenarioGroup(s2)
        group = s1 + g
        assert isinstance(group, ScenarioGroup)

    def test_add_unknown_type_returns_not_implemented(self) -> None:
        s = Scenario(lambda: None, name='s')
        result = s.__add__(42)  # type: ignore[arg-type]
        assert result is NotImplemented

    def test_radd_group_scenario(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        g = ScenarioGroup(s1)
        # s2.__radd__(g) = ScenarioGroup(*g._scenarios, s2) = [s1, s2]
        group = s2.__radd__(g)
        assert isinstance(group, ScenarioGroup)
        results = group.run()
        assert results[0].scenario is s1
        assert results[1].scenario is s2
