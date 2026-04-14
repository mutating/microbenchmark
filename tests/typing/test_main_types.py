from __future__ import annotations

import pytest

from microbenchmark.__main__ import main

# ---------------------------------------------------------------------------
# Positive: main() signature
# ---------------------------------------------------------------------------


@pytest.mark.mypy_testing
def test_main_return_type():
    reveal_type(main)  # N: Revealed type is "def (argv: Union[builtins.list[builtins.str], None] =)"


@pytest.mark.mypy_testing
def test_main_accepts_argv_list():
    argv: list[str] = ['tests.cli.fixtures.sample:scenario']
    reveal_type(argv)  # N: Revealed type is "builtins.list[builtins.str]"


@pytest.mark.mypy_testing
def test_main_accepts_none():
    none_argv: list[str] | None = None
    reveal_type(none_argv)  # N: Revealed type is "Union[builtins.list[builtins.str], None]"
