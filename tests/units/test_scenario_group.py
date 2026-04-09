from __future__ import annotations

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup


def make_scenario(name: str = 's', number: int = 5) -> Scenario:
    return Scenario(lambda: None, name=name, number=number)


class TestScenarioGroupConstruction:
    def test_empty_group(self) -> None:
        g = ScenarioGroup()
        assert isinstance(g, ScenarioGroup)

    def test_single_scenario(self) -> None:
        s = make_scenario('s1')
        g = ScenarioGroup(s)
        results = g.run()
        assert len(results) == 1

    def test_multiple_scenarios(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        g = ScenarioGroup(s1, s2, s3)
        results = g.run()
        assert len(results) == 3


class TestScenarioGroupOperator:
    def test_scenario_plus_scenario(self) -> None:
        s1, s2 = make_scenario('s1'), make_scenario('s2')
        group = s1 + s2
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 2

    def test_group_plus_scenario(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        group = ScenarioGroup(s1, s2) + s3
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 3

    def test_scenario_plus_group(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        group = s1 + ScenarioGroup(s2, s3)
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 3

    def test_group_plus_group(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        group = ScenarioGroup(s1) + ScenarioGroup(s2, s3)
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 3

    def test_triple_sum_is_flat(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        group = s1 + s2 + s3
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 3

    def test_add_returns_new_group(self) -> None:
        s1, s2 = make_scenario('s1'), make_scenario('s2')
        g = ScenarioGroup(s1)
        new_g = g + s2
        assert new_g is not g
        assert len(g._scenarios) == 1  # original not mutated

    def test_add_unknown_type_returns_not_implemented(self) -> None:
        g = ScenarioGroup()
        result = g.__add__(42)  # type: ignore[arg-type]
        assert result is NotImplemented

    def test_radd_unknown_type_returns_not_implemented(self) -> None:
        g = ScenarioGroup()
        result = g.__radd__(42)  # type: ignore[arg-type]
        assert result is NotImplemented

    def test_radd_scenario_to_group(self) -> None:
        s1, s2 = make_scenario('s1'), make_scenario('s2')
        g = ScenarioGroup(s1)
        group = g.__radd__(s2)
        assert isinstance(group, ScenarioGroup)
        assert len(group.run()) == 2

    def test_duplicate_scenarios(self) -> None:
        s = make_scenario('s')
        group = s + s
        results = group.run()
        assert len(results) == 2

    def test_multiple_groups_flat(self) -> None:
        scenarios = [make_scenario(f's{i}') for i in range(5)]
        g1 = ScenarioGroup(scenarios[0], scenarios[1])
        g2 = ScenarioGroup(scenarios[2], scenarios[3])
        g3 = ScenarioGroup(scenarios[4])
        combined = g1 + g2 + g3
        assert len(combined.run()) == 5


class TestScenarioGroupRun:
    def test_run_returns_list(self) -> None:
        g = ScenarioGroup()
        result = g.run()
        assert isinstance(result, list)

    def test_empty_group_returns_empty_list(self) -> None:
        g = ScenarioGroup()
        assert g.run() == []

    def test_empty_group_run_with_warmup(self) -> None:
        g = ScenarioGroup()
        assert g.run(warmup=10) == []

    def test_run_returns_benchmark_results(self) -> None:
        s = make_scenario()
        g = ScenarioGroup(s)
        results = g.run()
        for r in results:
            assert isinstance(r, BenchmarkResult)

    def test_run_order_preserved(self) -> None:
        s1, s2, s3 = make_scenario('s1'), make_scenario('s2'), make_scenario('s3')
        g = ScenarioGroup(s1, s2, s3)
        results = g.run()
        assert results[0].scenario is s1
        assert results[1].scenario is s2
        assert results[2].scenario is s3

    def test_run_with_warmup(self) -> None:
        counters = [0, 0]

        def make_fn(idx: int) -> object:
            def fn() -> None:
                counters[idx] += 1
            return fn

        s1 = Scenario(make_fn(0), name='a', number=5)  # type: ignore[arg-type]
        s2 = Scenario(make_fn(1), name='b', number=5)  # type: ignore[arg-type]
        g = ScenarioGroup(s1, s2)
        results = g.run(warmup=3)
        # each scenario: 3 warmup + 5 measured = 8 calls
        assert counters[0] == 8
        assert counters[1] == 8
        for r in results:
            assert len(r.durations) == 5

    def test_run_correct_scenario_reference(self) -> None:
        s1, s2 = make_scenario('s1'), make_scenario('s2')
        g = ScenarioGroup(s1, s2)
        results = g.run()
        assert results[0].scenario is s1
        assert results[1].scenario is s2
