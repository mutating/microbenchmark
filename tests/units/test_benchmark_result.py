from __future__ import annotations

import json
import math

import pytest
from full_match import match

from microbenchmark import BenchmarkResult, Scenario


def _make_result(
    durations: tuple[float, ...],
    scenario: Scenario | None = None,
    is_primary: bool = True,
) -> BenchmarkResult:
    if scenario is None:
        scenario = Scenario(lambda: None, name='test', number=len(durations) or 1)
    return BenchmarkResult(scenario=scenario, durations=durations, is_primary=is_primary)


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------


def test_all_fields_stored():
    scenario = Scenario(lambda: None, name='s', number=3)
    result = BenchmarkResult(
        scenario=scenario,
        durations=(0.1, 0.2, 0.3),
        is_primary=True,
    )

    assert result.scenario is scenario
    assert result.durations == (0.1, 0.2, 0.3)
    assert result.is_primary is True


def test_durations_is_tuple():
    result = _make_result((0.1, 0.2, 0.3))

    assert isinstance(result.durations, tuple)


def test_empty_durations_raises():
    scenario = Scenario(lambda: None, name='s', number=1)

    with pytest.raises(ZeroDivisionError):
        BenchmarkResult(scenario=scenario, durations=(), is_primary=True)


def test_inf_durations_fields():
    result = _make_result((float('inf'), 1.0, 2.0))

    assert math.isinf(result.worst)
    assert math.isinf(result.mean)
    assert result.best == 1.0


def test_nan_durations_fields():
    result = _make_result((float('nan'),))

    assert math.isnan(result.mean)
    assert math.isnan(result.best)
    assert math.isnan(result.worst)


def test_mean_computed_correctly():
    result = _make_result((1.0, 2.0, 3.0))
    expected = math.fsum([1.0, 2.0, 3.0]) / 3

    assert result.mean == expected


def test_mean_uses_fsum_precision():
    durations = (1e20, 1.0, -1e20)
    result = _make_result(durations)

    assert result.mean == 1.0 / 3


def test_best_is_min():
    result = _make_result((3.0, 1.0, 2.0))

    assert result.best == 1.0


def test_worst_is_max():
    result = _make_result((3.0, 1.0, 2.0))

    assert result.worst == 3.0


def test_is_primary_true_by_default():
    result = _make_result((1.0,))

    assert result.is_primary is True


def test_is_primary_false():
    result = _make_result((1.0,), is_primary=False)

    assert result.is_primary is False


def test_single_duration():
    result = _make_result((0.5,))

    assert result.best == 0.5
    assert result.worst == 0.5
    assert result.mean == 0.5


def test_all_equal_durations():
    result = _make_result((0.1, 0.1, 0.1))

    assert result.best == 0.1
    assert result.worst == 0.1
    assert result.mean == pytest.approx(0.1)


def test_scenario_identity():
    scenario = Scenario(lambda: None, name='check')
    result = BenchmarkResult(scenario=scenario, durations=(0.1,), is_primary=True)

    assert result.scenario is scenario


def test_scenario_none():
    result = BenchmarkResult(scenario=None, durations=(0.1,), is_primary=True)

    assert result.scenario is None


# ---------------------------------------------------------------------------
# median (cached property — TDD, will pass after benchmark_result.py update)
# ---------------------------------------------------------------------------


def test_median_single_duration():
    result = _make_result((3.0,))

    assert result.median == 3.0


def test_median_odd_count():
    result = _make_result((3.0, 1.0, 2.0))

    assert result.median == 2.0


def test_median_even_count():
    result = _make_result((1.0, 2.0, 3.0, 4.0))

    assert result.median == pytest.approx(2.5)


def test_median_is_float():
    result = _make_result((1.0, 2.0, 3.0))

    assert isinstance(result.median, float)


def test_median_is_cached_property():
    result = _make_result((1.0, 2.0, 3.0))

    assert result.median is result.median


def test_median_json_round_trip():
    result = _make_result((1.0, 2.0, 3.0))
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.median == result.median


# ---------------------------------------------------------------------------
# percentile
# ---------------------------------------------------------------------------


def test_percentile_returns_benchmark_result():
    result = _make_result(tuple(float(i) for i in range(1, 11)))
    trimmed = result.percentile(90)

    assert isinstance(trimmed, BenchmarkResult)


def test_percentile_is_primary_false():
    result = _make_result(tuple(float(i) for i in range(1, 11)))
    trimmed = result.percentile(90)

    assert trimmed.is_primary is False


def test_percentile_count_nearest_rank():
    result = _make_result(tuple(float(i) for i in range(1, 101)))
    trimmed = result.percentile(95)
    expected_count = math.ceil(100 * 95 / 100)

    assert len(trimmed.durations) == expected_count


def test_percentile_contains_fastest():
    result = _make_result((5.0, 1.0, 3.0, 2.0, 4.0))
    trimmed = result.percentile(60)
    keep_count = math.ceil(5 * 60 / 100)

    assert len(trimmed.durations) == keep_count
    assert trimmed.durations == tuple(sorted(result.durations)[:keep_count])


def test_percentile_100_returns_all():
    result = _make_result((1.0, 2.0, 3.0))
    trimmed = result.percentile(100)

    assert len(trimmed.durations) == 3
    assert trimmed.is_primary is False
    assert trimmed.durations == tuple(sorted(result.durations))


def test_percentile_small_number():
    result = _make_result((1.0, 2.0, 3.0))
    trimmed = result.percentile(50)
    expected = math.ceil(3 * 50 / 100)

    assert len(trimmed.durations) == expected


def test_percentile_very_small_positive():
    result = _make_result((1.0, 2.0, 3.0, 4.0, 5.0))
    trimmed = result.percentile(0.001)

    assert len(trimmed.durations) == 1
    assert trimmed.durations == (1.0,)


def test_percentile_99():
    result = _make_result(tuple(float(i) for i in range(1, 101)))
    trimmed = result.percentile(99)

    assert len(trimmed.durations) == math.ceil(100 * 99 / 100)


def test_percentile_mean_recomputed():
    result = _make_result((1.0, 2.0, 3.0, 4.0, 10.0))
    trimmed = result.percentile(80)
    expected_durations = sorted(result.durations)[:4]
    expected_mean = math.fsum(expected_durations) / 4

    assert trimmed.mean == pytest.approx(expected_mean)


def test_percentile_on_derived_result():
    result = _make_result(tuple(float(i) for i in range(1, 101)))
    derived = result.percentile(90).percentile(50)

    assert isinstance(derived, BenchmarkResult)
    assert derived.is_primary is False
    assert len(derived.durations) == 45


def test_percentile_scenario_preserved():
    scenario = Scenario(lambda: None, name='s')
    result = BenchmarkResult(scenario=scenario, durations=(1.0, 2.0, 3.0), is_primary=True)
    trimmed = result.percentile(100)

    assert trimmed.scenario is scenario


def test_percentile_0_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match=match('percentile must be in (0, 100], got 0')):
        result.percentile(0)


def test_percentile_negative_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(-5)


def test_percentile_above_100_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(101)


def test_percentile_nan_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(float('nan'))


def test_percentile_inf_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(float('inf'))


def test_percentile_neg_inf_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(float('-inf'))


def test_percentile_zero_float_raises():
    result = _make_result((1.0, 2.0, 3.0))

    with pytest.raises(ValueError, match='percentile'):
        result.percentile(0.0)


def test_percentile_preserves_fsum_mean():
    durations = tuple(0.1 * i for i in range(1, 11))
    result = _make_result(durations)
    trimmed = result.percentile(80)
    sorted_durations = sorted(durations)
    keep_count = math.ceil(10 * 80 / 100)
    expected = math.fsum(sorted_durations[:keep_count]) / keep_count

    assert trimmed.mean == pytest.approx(expected)


def test_percentile_single_element():
    result = _make_result((5.0,))
    trimmed = result.percentile(50)

    assert trimmed.durations == (5.0,)
    assert trimmed.is_primary is False


def test_percentile_100_single_element():
    result = _make_result((5.0,))
    trimmed = result.percentile(100)

    assert trimmed.durations == (5.0,)
    assert trimmed.is_primary is False


# ---------------------------------------------------------------------------
# p95 and p99 cached properties
# ---------------------------------------------------------------------------


def test_p95_returns_benchmark_result():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert isinstance(result.p95, BenchmarkResult)


def test_p99_returns_benchmark_result():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert isinstance(result.p99, BenchmarkResult)


def test_p95_is_cached():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert result.p95 is result.p95


def test_p99_is_cached():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert result.p99 is result.p99


def test_p95_count():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert len(result.p95.durations) == math.ceil(100 * 95 / 100)


def test_p99_count():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert len(result.p99.durations) == math.ceil(100 * 99 / 100)


def test_p95_is_primary_false():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert result.p95.is_primary is False


def test_p99_is_primary_false():
    result = _make_result(tuple(float(i) for i in range(1, 101)))

    assert result.p99.is_primary is False


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------


def test_to_json_returns_string():
    result = _make_result((0.1, 0.2))

    assert isinstance(result.to_json(), str)


def test_to_json_valid_json():
    result = _make_result((0.1, 0.2))
    data = json.loads(result.to_json())

    assert isinstance(data, dict)
    assert isinstance(data['durations'], list)
    assert isinstance(data['is_primary'], bool)
    assert 'scenario' in data


def test_to_json_contains_durations():
    result = _make_result((0.1, 0.2, 0.3))
    data = json.loads(result.to_json())

    assert 'durations' in data


def test_to_json_contains_is_primary():
    result = _make_result((0.1,))
    data = json.loads(result.to_json())

    assert 'is_primary' in data


def test_to_json_contains_scenario_metadata():
    scenario = Scenario(lambda: None, name='myname', doc='mydoc', number=42)
    result = BenchmarkResult(scenario=scenario, durations=(0.1,), is_primary=True)
    data = json.loads(result.to_json())

    assert data['scenario']['name'] == 'myname'
    assert data['scenario']['doc'] == 'mydoc'
    assert data['scenario']['number'] == 42


def test_to_json_derived_is_primary_false():
    result = _make_result((1.0, 2.0, 3.0), is_primary=False)
    data = json.loads(result.to_json())

    assert data['is_primary'] is False


def test_to_json_scenario_none_is_null():
    result = BenchmarkResult(scenario=None, durations=(0.1,), is_primary=True)
    data = json.loads(result.to_json())

    assert data['scenario'] is None


def test_from_json_round_trip_durations():
    result = _make_result((0.1, 0.2, 0.3))
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.durations == result.durations


def test_from_json_round_trip_mean():
    result = _make_result((0.1, 0.2, 0.3))
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.mean == result.mean


def test_from_json_round_trip_best_worst():
    result = _make_result((0.1, 0.2, 0.3))
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.best == result.best
    assert restored.worst == result.worst


def test_from_json_scenario_is_none():
    result = _make_result((0.1, 0.2))
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.scenario is None


def test_from_json_preserves_is_primary():
    result = _make_result((0.1,), is_primary=False)
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.is_primary is False


def test_from_json_primary_preserved():
    result = _make_result((0.1,), is_primary=True)
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.is_primary is True


def test_from_json_fp_precision():
    durations = tuple(0.1 * i for i in range(1, 6))
    result = _make_result(durations)
    restored = BenchmarkResult.from_json(result.to_json())

    assert restored.mean == pytest.approx(result.mean)


def test_from_json_with_scenario_field_ignored():
    payload = json.dumps({
        'durations': [0.1, 0.2],
        'is_primary': True,
        'scenario': {'name': 'x', 'doc': '', 'number': 1},
    })
    restored = BenchmarkResult.from_json(payload)

    assert restored.scenario is None
    assert restored.durations == (0.1, 0.2)


def test_from_json_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        BenchmarkResult.from_json('{not valid json}')


def test_from_json_missing_fields_raises():
    with pytest.raises(ValueError, match='required fields'):
        BenchmarkResult.from_json('{}')


def test_from_json_missing_durations_raises():
    data = json.dumps({'is_primary': True, 'scenario': {'name': 'x', 'doc': '', 'number': 1}})

    with pytest.raises(ValueError, match='required fields'):
        BenchmarkResult.from_json(data)


def test_from_json_missing_is_primary_raises():
    payload = json.dumps({'durations': [0.1, 0.2]})

    with pytest.raises(ValueError, match='required fields'):
        BenchmarkResult.from_json(payload)


def test_from_json_not_dict_raises():
    payload = json.dumps([1, 2, 3])

    with pytest.raises(ValueError, match='JSON must be an object'):
        BenchmarkResult.from_json(payload)


def test_from_json_durations_not_list_raises():
    payload = json.dumps({'durations': 'not a list', 'is_primary': True})

    with pytest.raises(ValueError, match='durations'):
        BenchmarkResult.from_json(payload)


def test_from_json_is_primary_not_bool_raises():
    payload = json.dumps({'durations': [0.1], 'is_primary': 'true'})

    with pytest.raises(ValueError, match='is_primary'):
        BenchmarkResult.from_json(payload)


def test_from_json_is_primary_int_raises():
    payload = json.dumps({'durations': [0.1], 'is_primary': 1})

    with pytest.raises(ValueError, match='is_primary'):
        BenchmarkResult.from_json(payload)


def test_from_json_durations_with_invalid_element_raises():
    payload = '{"durations": [0.1, "not_a_number"], "is_primary": true}'

    with pytest.raises(ValueError, match='could not convert'):
        BenchmarkResult.from_json(payload)


def test_from_json_durations_with_null_element_raises():
    payload = json.dumps({'durations': [0.1, None], 'is_primary': True})

    with pytest.raises(TypeError):
        BenchmarkResult.from_json(payload)


def test_from_json_empty_durations_list_raises():
    payload = json.dumps({'durations': [], 'is_primary': True})

    with pytest.raises(ZeroDivisionError):
        BenchmarkResult.from_json(payload)


def test_to_json_inf_produces_non_standard_json():
    result = _make_result((float('inf'), 1.0))
    json_str = result.to_json()

    assert 'Infinity' in json_str


def test_to_json_nan_round_trips_in_python():
    result = _make_result((float('nan'),))
    restored = BenchmarkResult.from_json(result.to_json())

    assert math.isnan(restored.mean)


def test_from_json_inf_round_trip():
    result = _make_result((float('inf'), 1.0))
    restored = BenchmarkResult.from_json(result.to_json())

    assert math.isinf(restored.durations[0])
    assert restored.durations[1] == 1.0


def test_from_json_bool_duration_converts_to_float():
    payload = json.dumps({'durations': [True, False], 'is_primary': True})
    restored = BenchmarkResult.from_json(payload)

    assert restored.durations == (1.0, 0.0)


def test_from_json_negative_durations_accepted():
    payload = json.dumps({'durations': [-0.1, 0.2], 'is_primary': True})
    restored = BenchmarkResult.from_json(payload)

    assert restored.mean == pytest.approx(0.05)
    assert restored.best == -0.1
