from __future__ import annotations

import time

import pytest

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup

# ---------------------------------------------------------------------------
# Positive type checks (runtime — confirm valid usage works)
# ---------------------------------------------------------------------------

class TestScenarioPositiveTypes:
    def test_callable_function(self) -> None:
        s = Scenario(lambda: None, name='s')
        assert isinstance(s, Scenario)

    def test_args_none(self) -> None:
        s = Scenario(lambda: None, args=None, name='s')
        assert isinstance(s, Scenario)

    def test_args_list(self) -> None:
        s = Scenario(sum, args=[[1, 2, 3]], name='s')
        assert isinstance(s, Scenario)

    def test_number_int(self) -> None:
        s = Scenario(lambda: None, name='s', number=100)
        assert isinstance(s, Scenario)

    def test_timer_callable(self) -> None:
        s = Scenario(lambda: None, name='s', timer=time.perf_counter)
        assert isinstance(s, Scenario)

    def test_run_returns_benchmark_result(self) -> None:
        result = Scenario(lambda: None, name='s', number=1).run()
        assert isinstance(result, BenchmarkResult)

    def test_run_with_warmup_returns_benchmark_result(self) -> None:
        result = Scenario(lambda: None, name='s', number=1).run(warmup=0)
        assert isinstance(result, BenchmarkResult)

    def test_add_scenario_returns_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        group = s1 + s2
        assert isinstance(group, ScenarioGroup)

    def test_add_group_returns_group(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        g = ScenarioGroup()
        group = s1 + g
        assert isinstance(group, ScenarioGroup)


# ---------------------------------------------------------------------------
# Negative type checks (runtime ValueError/TypeError for invalid inputs)
# ---------------------------------------------------------------------------

class TestScenarioNegativeTypes:
    def test_number_zero_raises(self) -> None:
        with pytest.raises(ValueError, match='number'):
            Scenario(lambda: None, name='s', number=0)

    def test_number_negative_raises(self) -> None:
        with pytest.raises(ValueError, match='number'):
            Scenario(lambda: None, name='s', number=-5)

    def test_add_int_returns_not_implemented(self) -> None:
        s = Scenario(lambda: None, name='s')
        result = s.__add__(42)  # type: ignore[arg-type]
        assert result is NotImplemented
