from __future__ import annotations

import json
import math

import pytest

from microbenchmark import BenchmarkResult, Scenario


def make_result(
    durations: tuple[float, ...],
    scenario: Scenario | None = None,
    is_primary: bool = True,
) -> BenchmarkResult:
    if scenario is None:
        scenario = Scenario(lambda: None, name='test', number=len(durations) or 1)
    return BenchmarkResult(scenario=scenario, durations=durations, is_primary=is_primary)


class TestBenchmarkResultFields:
    def test_all_fields_stored(self) -> None:
        scenario = Scenario(lambda: None, name='s', number=3)
        result = BenchmarkResult(
            scenario=scenario,
            durations=(0.1, 0.2, 0.3),
            is_primary=True,
        )
        assert result.scenario is scenario
        assert result.durations == (0.1, 0.2, 0.3)
        assert result.is_primary is True

    def test_durations_is_tuple(self) -> None:
        result = make_result((0.1, 0.2, 0.3))
        assert isinstance(result.durations, tuple)

    def test_empty_durations_raises(self) -> None:
        # BenchmarkResult does not validate durations length;
        # creating with empty tuple causes ZeroDivisionError in __post_init__
        s = Scenario(lambda: None, name='s', number=1)
        with pytest.raises(ZeroDivisionError):
            BenchmarkResult(scenario=s, durations=(), is_primary=True)

    def test_inf_durations_fields(self) -> None:
        result = make_result((float('inf'), 1.0, 2.0))
        assert math.isinf(result.worst)
        assert math.isinf(result.mean)
        assert result.best == 1.0

    def test_nan_durations_fields(self) -> None:
        result = make_result((float('nan'),))
        assert math.isnan(result.mean)
        assert math.isnan(result.best)
        assert math.isnan(result.worst)

    def test_mean_computed_correctly(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        expected = math.fsum([1.0, 2.0, 3.0]) / 3
        assert result.mean == expected

    def test_mean_uses_fsum_precision(self) -> None:
        # fsum handles cancellation correctly; plain sum loses precision
        # for (1e20, 1.0, -1e20): fsum=1.0 (exact), but sum=0.0 (catastrophic cancellation)
        durations = (1e20, 1.0, -1e20)
        result = make_result(durations)
        assert result.mean == 1.0 / 3  # exact: fsum gives 1.0, divided by 3

    def test_best_is_min(self) -> None:
        result = make_result((3.0, 1.0, 2.0))
        assert result.best == 1.0

    def test_worst_is_max(self) -> None:
        result = make_result((3.0, 1.0, 2.0))
        assert result.worst == 3.0

    def test_is_primary_true_by_default(self) -> None:
        result = make_result((1.0,))
        assert result.is_primary is True

    def test_is_primary_false(self) -> None:
        result = make_result((1.0,), is_primary=False)
        assert result.is_primary is False

    def test_single_duration(self) -> None:
        result = make_result((0.5,))
        assert result.best == 0.5
        assert result.worst == 0.5
        assert result.mean == 0.5

    def test_all_equal_durations(self) -> None:
        result = make_result((0.1, 0.1, 0.1))
        assert result.best == 0.1
        assert result.worst == 0.1
        assert result.mean == pytest.approx(0.1)

    def test_scenario_identity(self) -> None:
        scenario = Scenario(lambda: None, name='check')
        result = BenchmarkResult(scenario=scenario, durations=(0.1,), is_primary=True)
        assert result.scenario is scenario

    def test_scenario_none(self) -> None:
        result = BenchmarkResult(scenario=None, durations=(0.1,), is_primary=True)
        assert result.scenario is None


class TestPercentile:
    def test_percentile_returns_benchmark_result(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 11)))
        trimmed = result.percentile(90)
        assert isinstance(trimmed, BenchmarkResult)

    def test_percentile_is_primary_false(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 11)))
        trimmed = result.percentile(90)
        assert trimmed.is_primary is False

    def test_percentile_count_nearest_rank(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        trimmed = result.percentile(95)
        expected_count = math.ceil(100 * 95 / 100)
        assert len(trimmed.durations) == expected_count

    def test_percentile_contains_fastest(self) -> None:
        result = make_result((5.0, 1.0, 3.0, 2.0, 4.0))
        trimmed = result.percentile(60)
        k = math.ceil(5 * 60 / 100)
        assert len(trimmed.durations) == k
        # should be the smallest k values in sorted order
        sorted_original = sorted(result.durations)
        assert trimmed.durations == tuple(sorted_original[:k])

    def test_percentile_100_returns_all(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        trimmed = result.percentile(100)
        assert len(trimmed.durations) == 3
        assert trimmed.is_primary is False
        assert trimmed.durations == tuple(sorted(result.durations))

    def test_percentile_small_number(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        trimmed = result.percentile(50)
        expected = math.ceil(3 * 50 / 100)
        assert len(trimmed.durations) == expected

    def test_percentile_very_small_positive(self) -> None:
        result = make_result((1.0, 2.0, 3.0, 4.0, 5.0))
        trimmed = result.percentile(0.001)
        # ceil(5 * 0.001 / 100) = ceil(0.00005) = 1
        assert len(trimmed.durations) == 1
        assert trimmed.durations == (1.0,)

    def test_percentile_99(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        trimmed = result.percentile(99)
        assert len(trimmed.durations) == math.ceil(100 * 99 / 100)

    def test_percentile_mean_recomputed(self) -> None:
        result = make_result((1.0, 2.0, 3.0, 4.0, 10.0))
        trimmed = result.percentile(80)
        expected_durations = sorted(result.durations)[:4]
        expected_mean = math.fsum(expected_durations) / 4
        assert trimmed.mean == pytest.approx(expected_mean)

    def test_percentile_on_derived_result(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        derived = result.percentile(90).percentile(50)
        assert isinstance(derived, BenchmarkResult)
        assert derived.is_primary is False
        # 100 → p90 → 90 elements → p50 → ceil(90 * 50/100) = 45
        assert len(derived.durations) == 45

    def test_percentile_scenario_preserved(self) -> None:
        scenario = Scenario(lambda: None, name='s')
        result = BenchmarkResult(scenario=scenario, durations=(1.0, 2.0, 3.0), is_primary=True)
        trimmed = result.percentile(100)
        assert trimmed.scenario is scenario

    def test_percentile_0_raises(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(0)

    def test_percentile_negative_raises(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(-5)

    def test_percentile_above_100_raises(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(101)

    def test_percentile_nan_raises(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(float('nan'))

    def test_percentile_inf_raises(self) -> None:
        result = make_result((1.0, 2.0, 3.0))
        with pytest.raises(ValueError, match='percentile'):
            result.percentile(float('inf'))

    def test_percentile_preserves_fsum_mean(self) -> None:
        durations = tuple(0.1 * i for i in range(1, 11))
        result = make_result(durations)
        trimmed = result.percentile(80)
        sorted_d = sorted(durations)
        k = math.ceil(10 * 80 / 100)
        expected = math.fsum(sorted_d[:k]) / k
        assert trimmed.mean == pytest.approx(expected)


class TestCachedProperties:
    def test_p95_returns_benchmark_result(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert isinstance(result.p95, BenchmarkResult)

    def test_p99_returns_benchmark_result(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert isinstance(result.p99, BenchmarkResult)

    def test_p95_is_cached(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert result.p95 is result.p95

    def test_p99_is_cached(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert result.p99 is result.p99

    def test_p95_count(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert len(result.p95.durations) == math.ceil(100 * 95 / 100)

    def test_p99_count(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert len(result.p99.durations) == math.ceil(100 * 99 / 100)

    def test_p95_is_primary_false(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert result.p95.is_primary is False

    def test_p99_is_primary_false(self) -> None:
        result = make_result(tuple(float(i) for i in range(1, 101)))
        assert result.p99.is_primary is False


class TestSerialization:
    def test_to_json_returns_string(self) -> None:
        result = make_result((0.1, 0.2))
        assert isinstance(result.to_json(), str)

    def test_to_json_valid_json(self) -> None:
        result = make_result((0.1, 0.2))
        data = json.loads(result.to_json())
        assert isinstance(data, dict)
        assert isinstance(data['durations'], list)
        assert isinstance(data['is_primary'], bool)
        assert 'scenario' in data

    def test_to_json_contains_durations(self) -> None:
        result = make_result((0.1, 0.2, 0.3))
        data = json.loads(result.to_json())
        assert 'durations' in data

    def test_to_json_contains_is_primary(self) -> None:
        result = make_result((0.1,))
        data = json.loads(result.to_json())
        assert 'is_primary' in data

    def test_to_json_contains_scenario_metadata(self) -> None:
        s = Scenario(lambda: None, name='myname', doc='mydoc', number=42)
        result = BenchmarkResult(scenario=s, durations=(0.1,), is_primary=True)
        data = json.loads(result.to_json())
        assert data['scenario']['name'] == 'myname'
        assert data['scenario']['doc'] == 'mydoc'
        assert data['scenario']['number'] == 42

    def test_to_json_derived_is_primary_false(self) -> None:
        result = make_result((1.0, 2.0, 3.0), is_primary=False)
        data = json.loads(result.to_json())
        assert data['is_primary'] is False

    def test_from_json_round_trip_durations(self) -> None:
        result = make_result((0.1, 0.2, 0.3))
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.durations == result.durations

    def test_from_json_round_trip_mean(self) -> None:
        result = make_result((0.1, 0.2, 0.3))
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.mean == result.mean

    def test_from_json_round_trip_best_worst(self) -> None:
        result = make_result((0.1, 0.2, 0.3))
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.best == result.best
        assert restored.worst == result.worst

    def test_from_json_scenario_is_none(self) -> None:
        result = make_result((0.1, 0.2))
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.scenario is None

    def test_from_json_preserves_is_primary(self) -> None:
        result = make_result((0.1,), is_primary=False)
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.is_primary is False

    def test_from_json_primary_preserved(self) -> None:
        result = make_result((0.1,), is_primary=True)
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.is_primary is True

    def test_from_json_fp_precision(self) -> None:
        durations = tuple(0.1 * i for i in range(1, 6))
        result = make_result(durations)
        restored = BenchmarkResult.from_json(result.to_json())
        assert restored.mean == pytest.approx(result.mean)

    def test_from_json_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            BenchmarkResult.from_json('{not valid json}')

    def test_from_json_missing_fields_raises(self) -> None:
        with pytest.raises(ValueError, match='required fields'):
            BenchmarkResult.from_json('{}')

    def test_from_json_missing_durations_raises(self) -> None:
        data = json.dumps({'is_primary': True, 'scenario': {'name': 'x', 'doc': '', 'number': 1}})
        with pytest.raises(ValueError, match='required fields'):
            BenchmarkResult.from_json(data)

    def test_to_json_scenario_none_is_null(self) -> None:
        result = BenchmarkResult(scenario=None, durations=(0.1,), is_primary=True)
        data = json.loads(result.to_json())
        assert data['scenario'] is None

    def test_from_json_with_scenario_field_ignored(self) -> None:
        payload = json.dumps({
            'durations': [0.1, 0.2],
            'is_primary': True,
            'scenario': {'name': 'x', 'doc': '', 'number': 1},
        })
        restored = BenchmarkResult.from_json(payload)
        assert restored.scenario is None
        assert restored.durations == (0.1, 0.2)

    def test_from_json_durations_not_list_raises(self) -> None:
        payload = json.dumps({'durations': 'not a list', 'is_primary': True})
        with pytest.raises(ValueError, match='durations'):
            BenchmarkResult.from_json(payload)

    def test_from_json_is_primary_not_bool_raises(self) -> None:
        payload = json.dumps({'durations': [0.1], 'is_primary': 'true'})
        with pytest.raises(ValueError, match='is_primary'):
            BenchmarkResult.from_json(payload)

    def test_from_json_is_primary_int_raises(self) -> None:
        # int 1 is not a bool even though bool is a subclass of int
        payload = json.dumps({'durations': [0.1], 'is_primary': 1})
        with pytest.raises(ValueError, match='is_primary'):
            BenchmarkResult.from_json(payload)

    def test_from_json_durations_with_invalid_element_raises(self) -> None:
        payload = '{"durations": [0.1, "not_a_number"], "is_primary": true}'
        with pytest.raises(ValueError, match='could not convert'):
            BenchmarkResult.from_json(payload)

    def test_from_json_durations_with_null_element_raises(self) -> None:
        payload = json.dumps({'durations': [0.1, None], 'is_primary': True})
        with pytest.raises(TypeError):
            BenchmarkResult.from_json(payload)

    def test_from_json_empty_durations_list_raises(self) -> None:
        payload = json.dumps({'durations': [], 'is_primary': True})
        with pytest.raises(ZeroDivisionError):
            BenchmarkResult.from_json(payload)

    def test_to_json_inf_produces_non_standard_json(self) -> None:
        # Python's json module allows_nan=True by default: inf/nan → Infinity/NaN
        result = make_result((float('inf'), 1.0))
        j = result.to_json()
        assert 'Infinity' in j

    def test_to_json_nan_round_trips_in_python(self) -> None:
        # NaN round-trips through Python's json module (non-standard JSON)
        result = make_result((float('nan'),))
        restored = BenchmarkResult.from_json(result.to_json())
        assert math.isnan(restored.mean)

    def test_percentile_single_element(self) -> None:
        result = make_result((5.0,))
        trimmed = result.percentile(50)
        assert trimmed.durations == (5.0,)
        assert trimmed.is_primary is False

    def test_percentile_100_single_element(self) -> None:
        result = make_result((5.0,))
        trimmed = result.percentile(100)
        assert trimmed.durations == (5.0,)
        assert trimmed.is_primary is False

    def test_from_json_missing_is_primary_raises(self) -> None:
        payload = json.dumps({'durations': [0.1, 0.2]})
        with pytest.raises(ValueError, match='required fields'):
            BenchmarkResult.from_json(payload)
