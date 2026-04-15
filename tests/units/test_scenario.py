from __future__ import annotations

import ctypes
import itertools
from unittest.mock import patch

import pytest
from full_match import match
from sigmatch import SignatureMismatchError

from microbenchmark import BenchmarkResult, Scenario, ScenarioGroup, arguments
from microbenchmark.scenario import _fn_call_str, _render_result

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_minimal_construction_with_name():
    scenario = Scenario(lambda: None, name='minimal')

    assert scenario.name == 'minimal'


def test_name_auto_derived_from_function():
    def my_function():
        return list(range(100))

    scenario = Scenario(my_function)

    assert scenario.name == 'my_function'


def test_name_auto_derived_lambda_is_lambda():
    scenario = Scenario(lambda: None)

    assert scenario.name == '<lambda>'


def test_name_explicit_overrides_auto():
    def my_function():
        pass

    scenario = Scenario(my_function, name='custom')

    assert scenario.name == 'custom'


def test_name_stored():
    scenario = Scenario(lambda: None, name='myname')

    assert scenario.name == 'myname'


def test_doc_stored():
    scenario = Scenario(lambda: None, name='s', doc='my doc')

    assert scenario.doc == 'my doc'


def test_doc_default_empty():
    scenario = Scenario(lambda: None, name='s')

    assert scenario.doc == ''


def test_number_default():
    scenario = Scenario(lambda: None, name='s')

    assert scenario.number == 1000


def test_number_custom():
    scenario = Scenario(lambda: None, name='s', number=42)

    assert scenario.number == 42


def test_full_construction():
    timer_calls = [0.0]

    def fake_timer() -> float:
        timer_calls[0] += 0.001
        return timer_calls[0]

    scenario = Scenario(
        sum,
        arguments([1, 2, 3]),
        name='full',
        doc='A full scenario',
        number=50,
        timer=fake_timer,
    )

    assert scenario.name == 'full'
    assert scenario.doc == 'A full scenario'
    assert scenario.number == 50


def test_arguments_none_default():
    call_log: list[tuple[object, ...]] = []

    def fn(*a: object) -> None:
        call_log.append(a)

    scenario = Scenario(fn, name='s', number=1)
    scenario.run()

    assert call_log == [()]


def test_arguments_none_explicit():
    call_log: list[tuple[object, ...]] = []

    def fn(*a: object) -> None:
        call_log.append(a)

    scenario = Scenario(fn, None, name='s', number=1)
    scenario.run()

    assert call_log == [()]


def test_arguments_with_positional():
    call_log: list[tuple[object, ...]] = []

    def fn(*a: object) -> None:
        call_log.append(a)

    scenario = Scenario(fn, arguments(1, 2, 3), name='s', number=1)
    scenario.run()

    assert call_log == [(1, 2, 3)]


def test_arguments_with_keyword():
    call_log: list[dict[str, object]] = []

    def fn(**kw: object) -> None:
        call_log.append(dict(kw))

    scenario = Scenario(fn, arguments(key='value'), name='s', number=1)
    scenario.run()

    assert call_log == [{'key': 'value'}]


def test_arguments_with_mixed():
    call_log: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fn(*a: object, **kw: object) -> None:
        call_log.append((a, dict(kw)))

    scenario = Scenario(fn, arguments(1, 2, key='v'), name='s', number=1)
    scenario.run()

    assert call_log == [((1, 2), {'key': 'v'})]


def test_arguments_not_mutated_after_construction():
    call_log: list[tuple[object, ...]] = []

    def fn(*a: object) -> None:
        call_log.append(a)

    original = arguments(1, 2)
    scenario = Scenario(fn, original, name='s', number=1)
    scenario.run()

    assert call_log == [(1, 2)]


def test_number_zero_raises():
    with pytest.raises(ValueError, match=match('number must be at least 1, got 0')):
        Scenario(lambda: None, name='s', number=0)


def test_number_negative_raises():
    with pytest.raises(ValueError, match='number'):
        Scenario(lambda: None, name='s', number=-1)


# ---------------------------------------------------------------------------
# Signature validation
# ---------------------------------------------------------------------------


def test_signature_compatible_arguments_accepted():
    Scenario(lambda _a, _b: None, arguments(1, 2), name='s')


def test_signature_incompatible_raises():
    with pytest.raises(SignatureMismatchError):
        Scenario(lambda _a: None, arguments(1, 2), name='s')


def test_signature_too_few_raises():
    with pytest.raises(SignatureMismatchError):
        Scenario(lambda _a, _b: None, arguments(1), name='s')


def test_signature_no_args_compatible():
    Scenario(lambda: None, name='s')


def test_signature_no_args_with_none_arguments():
    Scenario(lambda: None, None, name='s')


def test_signature_builtin_correct_args():
    Scenario(len, arguments('hello'), name='s')


def test_signature_builtin_no_args_raises():
    # len requires one arg; Scenario(len) with no arguments should fail
    with pytest.raises(SignatureMismatchError):
        Scenario(len, name='s')


def test_signature_keyword_compatible():
    Scenario(lambda *, key: None, arguments(key='value'), name='s')  # noqa: ARG005


def test_signature_keyword_incompatible_raises():
    with pytest.raises(SignatureMismatchError):
        Scenario(lambda *, key: None, arguments('positional'), name='s')  # noqa: ARG005


def test_signature_defaults_short_call():
    Scenario(lambda _a, _b=1: None, arguments(1), name='s')


def test_signature_varargs_accepted():
    Scenario(lambda *_args: None, arguments(1, 2, 3), name='s')


def test_signature_unintrospectable_skips():
    # ctypes.ArgumentError has no inspectable signature; validation is skipped
    Scenario(ctypes.ArgumentError, arguments(1), name='s')


def test_signature_none_arguments_fn_needs_arg_raises():
    # lambda needs 1 arg but arguments=None → empty Arguments() → mismatch
    with pytest.raises(SignatureMismatchError):
        Scenario(lambda _a: None, None, name='s')


def test_signature_builtin_incompatible_raises():
    # len takes 1 arg; passing 2 should raise
    with pytest.raises(SignatureMismatchError):
        Scenario(len, arguments(1, 2), name='s')


# ---------------------------------------------------------------------------
# run()  # noqa: ERA001
# ---------------------------------------------------------------------------


def test_run_returns_benchmark_result():
    scenario = Scenario(lambda: None, name='s', number=5)
    result = scenario.run()

    assert isinstance(result, BenchmarkResult)


def test_run_calls_function_number_times():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=7)
    scenario.run()

    assert counter[0] == 7


def test_run_durations_length_equals_number():
    scenario = Scenario(lambda: None, name='s', number=10)
    result = scenario.run()

    assert len(result.durations) == 10


def test_run_with_warmup_total_calls():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=5)
    scenario.run(warmup=3)

    assert counter[0] == 8


def test_run_warmup_not_in_durations():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=5)
    result = scenario.run(warmup=10)

    assert len(result.durations) == 5
    assert counter[0] == 15


def test_run_warmup_zero():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=5)
    scenario.run(warmup=0)

    assert counter[0] == 5


def test_run_negative_warmup_acts_as_zero():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=3)
    result = scenario.run(warmup=-5)

    assert len(result.durations) == 3
    assert counter[0] == 3


def test_run_uses_custom_timer():
    counter = itertools.count(0)

    def fake_timer() -> float:
        return next(counter) * 0.001

    scenario = Scenario(lambda: None, name='s', number=3, timer=fake_timer)
    result = scenario.run()

    assert result.durations == pytest.approx((0.001, 0.001, 0.001))


def test_custom_timer_stateful():
    tick = [0]

    def fake_timer() -> float:
        tick[0] += 1
        return float(tick[0])

    scenario = Scenario(lambda: None, name='s', number=3, timer=fake_timer)
    result = scenario.run(warmup=2)

    assert tick[0] == 8  # loop_start: 1, run: 3*2=6, loop_end: 1 → 8 (warmup has no timer calls)
    assert len(result.durations) == 3
    assert result.durations == pytest.approx((1.0, 1.0, 1.0))


def test_run_result_scenario_is_self():
    scenario = Scenario(lambda: None, name='s', number=5)
    result = scenario.run()

    assert result.scenario is scenario


def test_run_twice_independent():
    counter = [0]

    def fn() -> None:
        counter[0] += 1

    scenario = Scenario(fn, name='s', number=5)
    result1 = scenario.run()
    result2 = scenario.run()

    assert len(result1.durations) == 5
    assert len(result2.durations) == 5
    assert result1 is not result2


def test_run_propagates_exception():
    def bad() -> None:
        raise RuntimeError('oops')

    scenario = Scenario(bad, name='s', number=1)

    with pytest.raises(RuntimeError, match=match('oops')):
        scenario.run()


def test_run_result_is_primary():
    scenario = Scenario(lambda: None, name='s', number=5)
    result = scenario.run()

    assert result.is_primary is True


def test_run_populates_total_duration():
    tick = [0.0]

    def fake_timer() -> float:
        tick[0] += 0.001
        return tick[0]

    scenario = Scenario(lambda: None, name='t', number=3, timer=fake_timer)
    result = scenario.run()

    assert isinstance(result.total_duration, float)
    assert result.total_duration > 0.0


def test_run_total_duration_spans_loop():
    ticks: list[float] = []

    def recording_timer() -> float:
        ticks.append(len(ticks) * 0.001)
        return ticks[-1]

    scenario = Scenario(lambda: None, name='t', number=3, timer=recording_timer)
    result = scenario.run()

    # total_duration should be loop_end - loop_start (first two timer calls after warmup)
    assert result.total_duration >= 0.0


def test_run_exception_mid_iteration():
    counter = [0]

    def fn() -> None:
        counter[0] += 1
        if counter[0] == 3:
            raise RuntimeError('fail on 3rd call')

    scenario = Scenario(fn, name='s', number=5)

    with pytest.raises(RuntimeError, match=match('fail on 3rd call')):
        scenario.run()

    assert counter[0] == 3


def test_run_exception_during_warmup_propagates():
    counter = [0]

    def fn() -> None:
        counter[0] += 1
        if counter[0] == 2:
            raise RuntimeError('fail in warmup')

    scenario = Scenario(fn, name='s', number=5)

    with pytest.raises(RuntimeError, match=match('fail in warmup')):
        scenario.run(warmup=3)

    assert counter[0] == 2


def test_run_number_one():
    tick = [0]

    def fake_timer() -> float:
        tick[0] += 1
        return float(tick[0])

    scenario = Scenario(lambda: None, name='s', number=1, timer=fake_timer)
    result = scenario.run()

    assert len(result.durations) == 1
    assert result.durations[0] == pytest.approx(1.0)


def test_run_arguments_positional_passed_correctly():
    received = []

    def fn(x: object, y: object) -> None:
        received.append((x, y))

    scenario = Scenario(fn, arguments(10, 20), name='s', number=3)
    scenario.run()

    assert received == [(10, 20), (10, 20), (10, 20)]


def test_run_arguments_keyword_passed_correctly():
    received = []

    def fn(key: object = None) -> None:
        received.append(key)

    scenario = Scenario(fn, arguments(key='hello'), name='s', number=2)
    scenario.run()

    assert received == ['hello', 'hello']


# ---------------------------------------------------------------------------
# __add__ and __radd__
# ---------------------------------------------------------------------------


def test_add_scenario_returns_group():
    scenario1 = Scenario(lambda: None, name='s1')
    scenario2 = Scenario(lambda: None, name='s2')
    group = scenario1 + scenario2

    assert isinstance(group, ScenarioGroup)


def test_add_scenario_group_returns_group():
    scenario1 = Scenario(lambda: None, name='s1')
    scenario2 = Scenario(lambda: None, name='s2')
    group_input = ScenarioGroup(scenario2)
    group = scenario1 + group_input

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert results[0].scenario is scenario1
    assert results[1].scenario is scenario2


def test_add_int_raises_type_error():
    scenario = Scenario(lambda: None, name='s')

    with pytest.raises(TypeError):
        _ = 42 + scenario  # type: ignore[operator]


def test_add_unknown_type_returns_not_implemented():
    scenario = Scenario(lambda: None, name='s')
    result = scenario.__add__(42)  # type: ignore[arg-type]

    assert result is NotImplemented


def test_radd_unknown_type_returns_not_implemented():
    scenario = Scenario(lambda: None, name='s')
    result = scenario.__radd__(42)  # type: ignore[arg-type]

    assert result is NotImplemented


def test_radd_scenario_scenario():
    scenario1 = Scenario(lambda: None, name='s1')
    scenario2 = Scenario(lambda: None, name='s2')
    group = scenario2.__radd__(scenario1)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert results[0].scenario is scenario1
    assert results[1].scenario is scenario2


def test_radd_group_scenario():
    scenario1 = Scenario(lambda: None, name='s1')
    scenario2 = Scenario(lambda: None, name='s2')
    group_input = ScenarioGroup(scenario1)
    group = scenario2.__radd__(group_input)

    assert isinstance(group, ScenarioGroup)
    results = group.run()
    assert results[0].scenario is scenario1
    assert results[1].scenario is scenario2


# ---------------------------------------------------------------------------
# _fn_call_str — OSError fallback (platform-specific getsources behavior)
# ---------------------------------------------------------------------------


def test_fn_call_str_oserror_fallback_uses_dunder_name():
    # On some platforms/versions getsources raises OSError instead of
    # UncertaintyWithLambdasError, which propagates through superrepr.
    # When dunder_name is '<lambda>' it is used as the fallback fn_name.
    fn = lambda: None

    with patch('microbenchmark.scenario.superrepr', side_effect=OSError):
        result = _fn_call_str(fn, None)

    assert result == '<lambda>()'


def test_fn_call_str_oserror_fallback_uses_repr_when_no_name():
    # When the callable has no __name__ attribute, repr() is used as fallback.
    class _NoName:
        def __call__(self) -> None:
            pass

        def __repr__(self) -> str:
            return 'my_custom_repr'

    with patch('microbenchmark.scenario.superrepr', side_effect=OSError):
        result = _fn_call_str(_NoName(), None)

    assert result == 'my_custom_repr()'


def test_fn_call_str_non_oserror_propagates():
    # Only OSError is caught; other exceptions from superrepr must propagate.
    fn = lambda: None

    with pytest.raises(ValueError, match='unexpected'), patch('microbenchmark.scenario.superrepr', side_effect=ValueError('unexpected')):
        _fn_call_str(fn, None)


def test_render_result_raises_when_scenario_is_none():
    result = BenchmarkResult.from_json('{"durations":[0.001,0.002],"is_primary":true,"scenario":null}')
    with pytest.raises(ValueError, match='scenario must not be None'):
        _render_result(result)
