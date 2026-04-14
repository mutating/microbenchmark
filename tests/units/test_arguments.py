from __future__ import annotations

import ctypes

from microbenchmark import a, arguments

# ---------------------------------------------------------------------------
# match
# ---------------------------------------------------------------------------


def test_match_positional_compatible():
    assert arguments(1, 2).match(lambda _a, _b: None) is True


def test_match_positional_too_many():
    assert arguments(1, 2, 3).match(lambda _a, _b: None) is False


def test_match_positional_too_few():
    assert arguments(1).match(lambda _a, _b: None) is False


def test_match_empty_arguments_no_params():
    assert arguments().match(lambda: None) is True


def test_match_empty_arguments_with_params():
    assert arguments().match(lambda _a: None) is False


def test_match_keyword_compatible():
    assert arguments(key='value').match(lambda *, key: None) is True  # noqa: ARG005


def test_match_keyword_wrong_name():
    assert arguments(other='value').match(lambda *, key: None) is False  # noqa: ARG005


def test_match_keyword_against_positional():
    assert arguments(key='value').match(lambda key: None) is True  # noqa: ARG005


def test_match_defaults_short_call():
    def f(a: object, b: object = 1) -> None: ...
    assert arguments(1).match(f) is True


def test_match_defaults_full_call():
    def f(a: object, b: object = 1) -> None: ...
    assert arguments(1, 2).match(f) is True


def test_match_varargs_any_count():
    def f(*args: object) -> None: ...
    assert arguments(1, 2, 3).match(f) is True


def test_match_varargs_empty():
    def f(*args: object) -> None: ...
    assert arguments().match(f) is True


def test_match_kwargs_any_name():
    def f(**kwargs: object) -> None: ...
    assert arguments(foo=1, bar=2).match(f) is True


def test_match_bound_method():
    class C:
        def m(self, a: object) -> None: ...
    assert arguments(1).match(C().m) is True


def test_match_bound_method_wrong_args():
    class C:
        def m(self, a: object) -> None: ...
    assert arguments(1, 2).match(C().m) is False


def test_match_class_callable():
    class D:
        def __init__(self, a: object, b: object) -> None: ...
    assert arguments(1, 2).match(D) is True


def test_match_class_callable_wrong_args():
    class D:
        def __init__(self, a: object, b: object) -> None: ...
    assert arguments(1).match(D) is False


def test_match_builtin_correct_args():
    # len accepts exactly one positional argument
    assert arguments('hello').match(len) is True


def test_match_builtin_too_many_args():
    # len only accepts one arg, so two args → False
    assert arguments(1, 2).match(len) is False


def test_match_builtin_no_args():
    # len requires one arg, so zero args → False
    assert arguments().match(len) is False


def test_match_unintrospectable_skips_returns_true():
    # ctypes.ArgumentError has no inspectable signature; check is skipped → True
    assert arguments(1).match(ctypes.ArgumentError) is True


def test_match_callable_object():
    class Callable:
        def __call__(self, a: object, b: object) -> None: ...
    assert arguments(1, 2).match(Callable()) is True


def test_match_callable_object_wrong_args():
    class Callable:
        def __call__(self, a: object, b: object) -> None: ...
    assert arguments(1).match(Callable()) is False


def test_match_returns_bool_true():
    result = arguments(1).match(lambda _a: None)
    assert isinstance(result, bool)
    assert result is True


def test_match_returns_bool_false():
    result = arguments(1, 2).match(lambda _a: None)
    assert isinstance(result, bool)
    assert result is False

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_arguments_empty():
    args = arguments()

    assert args.args == ()
    assert args.kwargs == {}


def test_arguments_positional_only():
    args = arguments(1, 2, 3)

    assert args.args == (1, 2, 3)
    assert args.kwargs == {}


def test_arguments_keyword_only():
    args = arguments(key='value', other=42)

    assert args.args == ()
    assert args.kwargs == {'key': 'value', 'other': 42}


def test_arguments_mixed():
    args = arguments(1, 2, key='value')

    assert args.args == (1, 2)
    assert args.kwargs == {'key': 'value'}


def test_arguments_single_positional():
    args = arguments(99)

    assert args.args == (99,)
    assert args.kwargs == {}


def test_arguments_single_keyword():
    args = arguments(x=7)

    assert args.args == ()
    assert args.kwargs == {'x': 7}


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------


def test_arguments_args_is_tuple():
    args = arguments(1, 2, 3)

    assert isinstance(args.args, tuple)


def test_arguments_kwargs_is_dict():
    args = arguments(key='value')

    assert isinstance(args.kwargs, dict)


def test_arguments_kwargs_not_mutated_by_external_dict():
    source = {'x': 1}
    args = arguments(**source)
    source['x'] = 999

    assert args.kwargs['x'] == 1


def test_arguments_accepts_any_object_type():
    lst = [1, 2, 3]
    args = arguments(lst, key=None)

    assert args.args == ([1, 2, 3],)
    assert args.kwargs == {'key': None}


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_arguments_repr_empty():
    args = arguments()

    assert repr(args) == 'arguments()'


def test_arguments_repr_positional_only():
    args = arguments(1, 2)

    assert repr(args) == 'arguments(1, 2)'


def test_arguments_repr_keyword_only():
    args = arguments(key='value')

    assert repr(args) == "arguments(key='value')"


def test_arguments_repr_mixed():
    args = arguments(1, 2, key='value')

    assert repr(args) == "arguments(1, 2, key='value')"


def test_arguments_repr_is_str():
    args = arguments(1, key='x')

    assert isinstance(repr(args), str)


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_arguments_eq_same_positional():
    assert arguments(1, 2) == arguments(1, 2)


def test_arguments_eq_same_keyword():
    assert arguments(key='v') == arguments(key='v')


def test_arguments_eq_same_mixed():
    assert arguments(1, key='v') == arguments(1, key='v')


def test_arguments_eq_empty():
    assert arguments() == arguments()


def test_arguments_eq_different_positional():
    assert arguments(1, 2) != arguments(1, 3)


def test_arguments_eq_different_keyword():
    assert arguments(key='a') != arguments(key='b')


def test_arguments_eq_different_arg_count():
    assert arguments(1) != arguments(1, 2)


def test_arguments_eq_non_arguments_returns_not_implemented():
    result = arguments(1).__eq__(42)

    assert result is NotImplemented


def test_arguments_eq_non_arguments_via_operator():
    assert arguments(1) != 42


# ---------------------------------------------------------------------------
# __hash__
# ---------------------------------------------------------------------------


def test_arguments_hashable():
    args = arguments(1, 2, key='v')

    assert isinstance(hash(args), int)


def test_arguments_hash_equal_objects():
    assert hash(arguments(1, 2)) == hash(arguments(1, 2))


def test_arguments_usable_in_set():
    arg1 = arguments(1, 2)
    arg2 = arguments(1, 2)
    arg3 = arguments(3)

    result = {arg1, arg2, arg3}

    assert len(result) == 2


def test_arguments_usable_as_dict_key():
    mapping = {arguments(1): 'one', arguments(2): 'two'}

    assert mapping[arguments(1)] == 'one'
    assert mapping[arguments(2)] == 'two'


# ---------------------------------------------------------------------------
# a alias
# ---------------------------------------------------------------------------


def test_a_is_arguments():
    assert a is arguments


def test_a_creates_arguments_instance():
    instance = a(1, 2, key='v')

    assert isinstance(instance, arguments)
    assert instance.args == (1, 2)
    assert instance.kwargs == {'key': 'v'}


def test_a_alias_produces_same_repr():
    assert repr(a(1, 2)) == repr(arguments(1, 2))
