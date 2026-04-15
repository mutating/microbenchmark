from __future__ import annotations

import pytest

from microbenchmark import Scenario, ScenarioGroup

# ---------------------------------------------------------------------------
# Positive: ScenarioGroup construction
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_empty_construction():
    ScenarioGroup()


@pytest.mark.mypy_testing
def test_single_scenario():
    scenario = Scenario(lambda: None, name='s')
    ScenarioGroup(scenario)


@pytest.mark.mypy_testing
def test_multiple_scenarios():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    ScenarioGroup(s1, s2)


# ---------------------------------------------------------------------------
# Positive: ScenarioGroup.run() return type
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_run_returns_list():
    group = ScenarioGroup()
    result = group.run()
    reveal_type(result)  # N: Revealed type is "builtins.list[microbenchmark.benchmark_result.BenchmarkResult]"


@pytest.mark.mypy_testing
def test_run_with_scenarios_returns_list_of_benchmark_results():
    scenario = Scenario(lambda: None, name='s', number=1)
    group = ScenarioGroup(scenario)
    results = group.run()
    for item in results:
        reveal_type(item)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


# ---------------------------------------------------------------------------
# Positive: ScenarioGroup + operator  # noqa: ERA001
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_group_add_scenario_returns_group():
    group = ScenarioGroup()
    scenario = Scenario(lambda: None, name='s')
    combined = group + scenario
    reveal_type(combined)  # N: Revealed type is "microbenchmark.scenario_group.ScenarioGroup"


@pytest.mark.mypy_testing
def test_group_add_group_returns_group():
    g1 = ScenarioGroup()
    g2 = ScenarioGroup()
    combined = g1 + g2
    reveal_type(combined)  # N: Revealed type is "microbenchmark.scenario_group.ScenarioGroup"


@pytest.mark.mypy_testing
def test_scenario_radd_group_returns_group():
    """Covers Scenario.__radd__ path: group + scenario."""
    scenario = Scenario(lambda: None, name='s')
    group = ScenarioGroup()
    combined = group + scenario
    reveal_type(combined)  # N: Revealed type is "microbenchmark.scenario_group.ScenarioGroup"


# ---------------------------------------------------------------------------
# Positive: ScenarioGroup.cli() return type
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_group_cli_method_type():
    group = ScenarioGroup()
    reveal_type(group.cli)  # N: Revealed type is "def (argv: Union[builtins.list[builtins.str], None] =)"


# ---------------------------------------------------------------------------
# Negative: ScenarioGroup construction with wrong type
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_group_int_rejected():
    try:
        ScenarioGroup(42)  # E: Argument 1 to "ScenarioGroup" has incompatible type "int"; expected "Scenario"  [arg-type]
    except TypeError:
        pass
