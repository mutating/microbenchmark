from __future__ import annotations

import pytest

from microbenchmark import BenchmarkResult, Scenario


def _make_result() -> BenchmarkResult:
    return Scenario(lambda: None, name='s', number=10).run()


# ---------------------------------------------------------------------------
# Positive: BenchmarkResult field types
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_durations_is_tuple_of_float():
    result = _make_result()
    reveal_type(result.durations)  # N: Revealed type is "builtins.tuple[builtins.float, ...]"


@pytest.mark.mypy_testing
def test_mean_is_float():
    result = _make_result()
    reveal_type(result.mean)  # N: Revealed type is "builtins.float"


@pytest.mark.mypy_testing
def test_best_is_float():
    result = _make_result()
    reveal_type(result.best)  # N: Revealed type is "builtins.float"


@pytest.mark.mypy_testing
def test_worst_is_float():
    result = _make_result()
    reveal_type(result.worst)  # N: Revealed type is "builtins.float"


@pytest.mark.mypy_testing
def test_median_is_float():
    result = _make_result()
    reveal_type(result.median)  # N: Revealed type is "builtins.float"


@pytest.mark.mypy_testing
def test_is_primary_is_bool():
    result = _make_result()
    reveal_type(result.is_primary)  # N: Revealed type is "builtins.bool"


@pytest.mark.mypy_testing
def test_scenario_field_is_scenario_or_none():
    result = _make_result()
    reveal_type(result.scenario)  # N: Revealed type is "Union[microbenchmark.scenario.Scenario, None]"


# ---------------------------------------------------------------------------
# Positive: BenchmarkResult.percentile / p95 / p99  # noqa: ERA001
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_percentile_returns_benchmark_result():
    result = _make_result()
    trimmed = result.percentile(95)
    reveal_type(trimmed)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


@pytest.mark.mypy_testing
def test_p95_returns_benchmark_result():
    result = _make_result()
    reveal_type(result.p95)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


@pytest.mark.mypy_testing
def test_p99_returns_benchmark_result():
    result = _make_result()
    reveal_type(result.p99)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


# ---------------------------------------------------------------------------
# Positive: JSON serialization
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_to_json_returns_str():
    result = _make_result()
    reveal_type(result.to_json())  # N: Revealed type is "builtins.str"


@pytest.mark.mypy_testing
def test_from_json_returns_benchmark_result():
    result = _make_result()
    restored = BenchmarkResult.from_json(result.to_json())
    reveal_type(restored)  # N: Revealed type is "microbenchmark.benchmark_result.BenchmarkResult"


# ---------------------------------------------------------------------------
# Negative: percentile with wrong type
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_percentile_str_rejected():
    result = _make_result()
    try:
        result.percentile('bad')  # E: Argument 1 to "percentile" of "BenchmarkResult" has incompatible type "str"; expected "float"  [arg-type]
    except TypeError:
        pass
