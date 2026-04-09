from __future__ import annotations

import json

import pytest

from microbenchmark import BenchmarkResult, Scenario


def make_result() -> BenchmarkResult:
    return Scenario(lambda: None, name='s', number=10).run()


class TestBenchmarkResultPositiveTypes:
    def test_percentile_returns_benchmark_result(self) -> None:
        result = make_result()
        trimmed = result.percentile(50)
        assert isinstance(trimmed, BenchmarkResult)

    def test_p95_returns_benchmark_result(self) -> None:
        result = make_result()
        assert isinstance(result.p95, BenchmarkResult)

    def test_p99_returns_benchmark_result(self) -> None:
        result = make_result()
        assert isinstance(result.p99, BenchmarkResult)

    def test_to_json_returns_str(self) -> None:
        result = make_result()
        assert isinstance(result.to_json(), str)

    def test_from_json_returns_benchmark_result(self) -> None:
        result = make_result()
        restored = BenchmarkResult.from_json(result.to_json())
        assert isinstance(restored, BenchmarkResult)

    def test_mean_is_float(self) -> None:
        result = make_result()
        assert isinstance(result.mean, float)

    def test_best_is_float(self) -> None:
        result = make_result()
        assert isinstance(result.best, float)

    def test_worst_is_float(self) -> None:
        result = make_result()
        assert isinstance(result.worst, float)

    def test_is_primary_is_bool(self) -> None:
        result = make_result()
        assert isinstance(result.is_primary, bool)

    def test_durations_is_tuple(self) -> None:
        result = make_result()
        assert isinstance(result.durations, tuple)


class TestBenchmarkResultNegativeTypes:
    def test_percentile_zero_raises(self) -> None:
        result = make_result()
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(0)

    def test_percentile_negative_raises(self) -> None:
        result = make_result()
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(-1)

    def test_percentile_above_100_raises(self) -> None:
        result = make_result()
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(101)

    def test_from_json_invalid_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            BenchmarkResult.from_json('{not valid}')

    def test_from_json_empty_object_raises(self) -> None:
        with pytest.raises(ValueError, match='required fields'):
            BenchmarkResult.from_json('{}')
