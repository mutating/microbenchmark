from __future__ import annotations

import pytest

from microbenchmark._render import (
    draw_box,
    draw_histogram,
    draw_histogram_axis,
    draw_nested,
    histogram_bounds,
    terminal_width,
)


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


@pytest.mark.mypy_testing
def test_histogram_bounds_returns_tuple():
    result = histogram_bounds([0.001, 0.002])
    reveal_type(result)  # N: Revealed type is "tuple[builtins.float, builtins.float]"


@pytest.mark.mypy_testing
def test_draw_histogram_axis_returns_str():
    result = draw_histogram_axis(0.000005, 0.000006, 40)
    reveal_type(result)  # N: Revealed type is "builtins.str"
