from __future__ import annotations

import time

import pytest

from microbenchmark import Scenario, ScenarioGroup, arguments

# ---------------------------------------------------------------------------
# Positive: Scenario construction
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_no_name_no_args():
    Scenario(lambda: None)


@pytest.mark.mypy_testing
def test_scenario_with_name():
    Scenario(lambda: None, name='s')


@pytest.mark.mypy_testing
def test_scenario_with_arguments_positional():
    Scenario(sorted, arguments([3, 1, 2]))


@pytest.mark.mypy_testing
def test_scenario_with_arguments_and_name():
    Scenario(sorted, arguments([3, 1, 2]), name='sort')


@pytest.mark.mypy_testing
def test_scenario_arguments_none_explicit():
    Scenario(lambda: None, None, name='s')


@pytest.mark.mypy_testing
def test_scenario_number_int():
    Scenario(lambda: None, name='s', number=100)


@pytest.mark.mypy_testing
def test_scenario_timer_callable():
    Scenario(lambda: None, name='s', timer=time.perf_counter)


@pytest.mark.mypy_testing
def test_scenario_doc_str():
    Scenario(lambda: None, name='s', doc='a description')


# ---------------------------------------------------------------------------
# Positive: Scenario attribute types
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_name_is_str_or_none():
    scenario = Scenario(lambda: None)
    reveal_type(scenario.name)  # N: Revealed type is "Union[builtins.str, None]"


@pytest.mark.mypy_testing
def test_scenario_doc_is_str():
    scenario = Scenario(lambda: None, name='s')
    reveal_type(scenario.doc)  # N: Revealed type is "builtins.str"


@pytest.mark.mypy_testing
def test_scenario_number_is_int():
    scenario = Scenario(lambda: None, name='s')
    reveal_type(scenario.number)  # N: Revealed type is "builtins.int"


# ---------------------------------------------------------------------------
# Positive: Scenario.run() return type
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_run_returns_benchmark_result():
    result = Scenario(lambda: None, name='s', number=1).run()
    reveal_type(result)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


@pytest.mark.mypy_testing
def test_scenario_run_with_warmup_returns_benchmark_result():
    result = Scenario(lambda: None, name='s', number=1).run(warmup=5)
    reveal_type(result)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


# ---------------------------------------------------------------------------
# Positive: Scenario + operator  # noqa: ERA001
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_add_scenario_returns_group():
    s1 = Scenario(lambda: None, name='s1')
    s2 = Scenario(lambda: None, name='s2')
    group = s1 + s2
    reveal_type(group)  # N: Revealed type is "microbenchmark.scenario_group.ScenarioGroup"


@pytest.mark.mypy_testing
def test_scenario_add_group_returns_group():
    s = Scenario(lambda: None, name='s')
    g = ScenarioGroup()
    group = s + g
    reveal_type(group)  # N: Revealed type is "microbenchmark.scenario_group.ScenarioGroup"


@pytest.mark.mypy_testing
def test_scenario_cli_method_type():
    scenario = Scenario(lambda: None, name='s')
    reveal_type(scenario.cli)  # N: Revealed type is "def (argv: Union[builtins.list[builtins.str], None] =)"


# ---------------------------------------------------------------------------
# Negative: Scenario construction with wrong types
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_number_str_rejected():
    try:
        Scenario(lambda: None, name='s', number='bad')  # E: Argument "number" to "Scenario" has incompatible type "str"; expected "int"  [arg-type]
    except (ValueError, TypeError):
        pass


@pytest.mark.mypy_testing
def test_scenario_timer_int_rejected():
    try:
        Scenario(lambda: None, name='s', timer=42)  # E: Argument "timer" to "Scenario" has incompatible type "int"; expected "Callable[[], float]"  [arg-type]
    except TypeError:
        pass


@pytest.mark.mypy_testing
def test_scenario_second_arg_str_rejected():
    try:
        Scenario(lambda: None, 'not_arguments', name='s')  # E: [arg-type]
    except TypeError:
        pass


# ---------------------------------------------------------------------------
# cli(argv=...) signature
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_scenario_cli_default_call():
    s = Scenario(lambda: None, name='s')
    s.cli()


@pytest.mark.mypy_testing
def test_scenario_cli_with_argv():
    s = Scenario(lambda: None, name='s')
    s.cli(argv=['--number', '5'])


@pytest.mark.mypy_testing
def test_scenario_cli_with_none():
    s = Scenario(lambda: None, name='s')
    s.cli(argv=None)
