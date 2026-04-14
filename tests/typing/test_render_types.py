from __future__ import annotations

import pytest

from microbenchmark._render import draw_box, draw_histogram, draw_nested, terminal_width


@pytest.mark.mypy_testing
def test_terminal_width_returns_int():
    reveal_type(terminal_width())  # N: Revealed type is "builtins.int"


@pytest.mark.mypy_testing
def test_draw_box_returns_list_of_str():
    result = draw_box(['hello'], 20)
    reveal_type(result)  # N: Revealed type is "builtins.list[builtins.str]"


@pytest.mark.mypy_testing
def test_draw_nested_returns_list_of_str():
    inner = draw_box(['hello'], 20)
    result = draw_nested([inner], [], 24)
    reveal_type(result)  # N: Revealed type is "builtins.list[builtins.str]"


@pytest.mark.mypy_testing
def test_draw_histogram_returns_list_of_str():
    result = draw_histogram([0.001, 0.002], 10, 4)
    reveal_type(result)  # N: Revealed type is "builtins.list[builtins.str]"
