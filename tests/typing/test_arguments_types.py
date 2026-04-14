from __future__ import annotations

import pytest

from microbenchmark import a, arguments

# ---------------------------------------------------------------------------
# Positive: arguments construction
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_arguments_empty():
    arguments()


@pytest.mark.mypy_testing
def test_arguments_positional():
    arguments(1, 2, 3)


@pytest.mark.mypy_testing
def test_arguments_keyword():
    arguments(key='value')


@pytest.mark.mypy_testing
def test_arguments_mixed():
    arguments(1, 2, key='value')


# ---------------------------------------------------------------------------
# Positive: arguments field types
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_arguments_instance_type():
    args = arguments(1, 2, 3)
    reveal_type(args)  # N: Revealed type is "microbenchmark.arguments.arguments"


@pytest.mark.mypy_testing
def test_arguments_args_is_tuple():
    args = arguments(1, 2, 3)
    reveal_type(args.args)  # N: Revealed type is "builtins.tuple[builtins.object, ...]"


@pytest.mark.mypy_testing
def test_arguments_kwargs_is_dict():
    args = arguments(key='value')
    reveal_type(args.kwargs)  # N: Revealed type is "builtins.dict[builtins.str, builtins.object]"


# ---------------------------------------------------------------------------
# Positive: a is an alias for arguments
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_a_alias_is_arguments_type():
    reveal_type(a)  # N: Revealed type is "def (*args: builtins.object, **kwargs: builtins.object) -> microbenchmark.arguments.arguments"


@pytest.mark.mypy_testing
def test_a_creates_arguments_instance():
    instance = a(1, 2)
    reveal_type(instance)  # N: Revealed type is "microbenchmark.arguments.arguments"


# ---------------------------------------------------------------------------
# Positive: repr returns str
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_arguments_repr_is_str():
    args = arguments(1, 2, key='value')
    reveal_type(repr(args))  # N: Revealed type is "builtins.str"
