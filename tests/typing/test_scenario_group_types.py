from __future__ import annotations

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


class TestScenarioGroupPositiveTypes:
    def test_empty_construction(self) -> None:
        g = ScenarioGroup()
        assert isinstance(g, ScenarioGroup)

    def test_single_scenario(self) -> None:
        s = Scenario(lambda: None, name='s')
        g = ScenarioGroup(s)
        assert isinstance(g, ScenarioGroup)

    def test_multiple_scenarios(self) -> None:
        s1 = Scenario(lambda: None, name='s1')
        s2 = Scenario(lambda: None, name='s2')
        g = ScenarioGroup(s1, s2)
        assert isinstance(g, ScenarioGroup)

    def test_run_returns_list(self) -> None:
        g = ScenarioGroup()
        result = g.run()
        assert isinstance(result, list)

    def test_run_returns_list_of_benchmark_results(self) -> None:
        s = Scenario(lambda: None, name='s', number=1)
        g = ScenarioGroup(s)
        results = g.run()
        for r in results:
            assert isinstance(r, BenchmarkResult)

    def test_add_scenario_returns_group(self) -> None:
        g = ScenarioGroup()
        s = Scenario(lambda: None, name='s')
        result = g + s
        assert isinstance(result, ScenarioGroup)

    def test_add_group_returns_group(self) -> None:
        g1 = ScenarioGroup()
        g2 = ScenarioGroup()
        result = g1 + g2
        assert isinstance(result, ScenarioGroup)


class TestScenarioGroupNegativeTypes:
    def test_add_int_returns_not_implemented(self) -> None:
        g = ScenarioGroup()
        result = g.__add__(42)  # type: ignore[arg-type]
        assert result is NotImplemented
