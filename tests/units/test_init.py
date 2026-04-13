from __future__ import annotations

import microbenchmark
from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


class TestPublicImports:
    def test_scenario_importable(self) -> None:
        assert Scenario is not None

    def test_scenario_group_importable(self) -> None:
        assert ScenarioGroup is not None

    def test_benchmark_result_importable(self) -> None:
        assert BenchmarkResult is not None

    def test_all_defined(self) -> None:
        assert hasattr(microbenchmark, '__all__')

    def test_all_contains_scenario(self) -> None:
        assert 'Scenario' in microbenchmark.__all__

    def test_all_contains_scenario_group(self) -> None:
        assert 'ScenarioGroup' in microbenchmark.__all__

    def test_all_contains_benchmark_result(self) -> None:
        assert 'BenchmarkResult' in microbenchmark.__all__

    def test_all_contains_exactly_five_items(self) -> None:
        assert set(microbenchmark.__all__) == {'Scenario', 'ScenarioGroup', 'BenchmarkResult', 'a', 'arguments'}
