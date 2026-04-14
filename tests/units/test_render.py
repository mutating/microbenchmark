from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap

from microbenchmark._render import draw_box, draw_histogram, draw_nested, terminal_width

_UTF8_ENV = {**os.environ, 'PYTHONUTF8': '1'}

# ---------------------------------------------------------------------------
# terminal_width
# ---------------------------------------------------------------------------


def test_terminal_width_returns_int():
    assert isinstance(terminal_width(), int)


def test_terminal_width_at_least_20():
    assert terminal_width() >= 20


def test_terminal_width_clamped_to_minimum(monkeypatch):
    monkeypatch.setattr(shutil, 'get_terminal_size', lambda _: shutil.os.terminal_size((5, 24)))
    assert terminal_width() == 20


def test_terminal_width_normal(monkeypatch):
    monkeypatch.setattr(shutil, 'get_terminal_size', lambda _: shutil.os.terminal_size((80, 24)))
    assert terminal_width() == 80


# ---------------------------------------------------------------------------
# draw_box
# ---------------------------------------------------------------------------


def test_draw_box_returns_list_of_strings():
    result = draw_box(['hello'], 20)

    assert isinstance(result, list)
    assert all(isinstance(line, str) for line in result)


def test_draw_box_three_lines_for_one_content():
    result = draw_box(['x'], 10)

    assert len(result) == 3


def test_draw_box_width_matches():
    width = 20
    result = draw_box(['hello'], width)

    assert all(len(line) == width for line in result)


def test_draw_box_top_border():
    result = draw_box(['x'], 10)

    assert result[0][0] == '╭'
    assert result[0][-1] == '╮'
    assert result[0][1:-1] == '─' * 8


def test_draw_box_bottom_border():
    result = draw_box(['x'], 10)

    assert result[-1][0] == '╰'
    assert result[-1][-1] == '╯'
    assert result[-1][1:-1] == '─' * 8


def test_draw_box_side_borders():
    result = draw_box(['hello'], 15)

    assert result[1][0] == '│'
    assert result[1][-1] == '│'


def test_draw_box_content_padded():
    result = draw_box(['hi'], 10)

    # inner content is 10-4=6 chars, 'hi' padded to 6
    assert result[1] == '│ hi     │'


def test_draw_box_content_truncated_if_too_long():
    result = draw_box(['hello world this is very long'], 10)

    # inner content is 10-4=6 chars, truncated
    assert result[1] == '│ hello  │'


def test_draw_box_multiple_content_lines():
    result = draw_box(['line1', 'line2', 'line3'], 15)

    assert len(result) == 5


def test_draw_box_border_chars():
    result = draw_box(['x'], 10)
    all_text = '\n'.join(result)

    assert '╭' in all_text
    assert '╮' in all_text
    assert '╰' in all_text
    assert '╯' in all_text
    assert '│' in all_text
    assert '─' in all_text


def test_draw_box_minimum_width():
    result = draw_box(['x'], 5)

    assert len(result) == 3
    assert all(len(line) == 5 for line in result)


def test_draw_box_empty_content_line():
    result = draw_box([''], 10)

    assert result[1] == '│        │'


# ---------------------------------------------------------------------------
# draw_nested
# ---------------------------------------------------------------------------


def test_draw_nested_returns_list():
    inner = draw_box(['hello'], 20)
    result = draw_nested([inner], [], 26)

    assert isinstance(result, list)


def test_draw_nested_outer_border_present():
    inner = draw_box(['x'], 16)
    result = draw_nested([inner], [], 20)
    all_text = '\n'.join(result)

    assert '╭' in all_text
    assert '╰' in all_text


def test_draw_nested_width_consistent():
    inner = draw_box(['content'], 20)
    width = 24
    result = draw_nested([inner], [], width)

    assert all(len(line) == width for line in result)


def test_draw_nested_with_two_inner_blocks():
    inner1 = draw_box(['first'], 20)
    inner2 = draw_box(['second'], 20)
    result = draw_nested([inner1, inner2], [], 24)

    all_text = '\n'.join(result)
    assert 'first' in all_text
    assert 'second' in all_text


def test_draw_nested_empty_inner_blocks():
    result = draw_nested([], [], 20)

    assert all(len(line) == 20 for line in result)


def test_draw_nested_long_inner_line_truncated():
    very_long_line = 'x' * 100
    inner = [very_long_line]
    width = 20
    result = draw_nested([inner], [], width)

    assert all(len(line) == width for line in result)


def test_draw_nested_with_extras():
    inner = draw_box(['content'], 20)
    extras = ['extra line']
    width = 24
    result = draw_nested([inner], extras, width)
    all_text = '\n'.join(result)

    assert 'extra line' in all_text


# ---------------------------------------------------------------------------
# Smoke: Scenario.cli outputs border chars
# ---------------------------------------------------------------------------


def test_scenario_cli_output_has_top_border():
    script = textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s = Scenario(lambda: None, name='box_test', number=3, timer=fake_timer)
        s.cli()
    ''')
    proc = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
        check=False,
        env=_UTF8_ENV,
    )

    assert '╭' in proc.stdout
    assert '╰' in proc.stdout


def test_scenario_group_cli_output_has_nested_borders():
    script = textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s1 = Scenario(lambda: None, name='a', number=3, timer=fake_timer)
        s2 = Scenario(lambda: None, name='b', number=3, timer=fake_timer)
        group = s1 + s2
        group.cli()
    ''')
    proc = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
        check=False,
        env=_UTF8_ENV,
    )

    assert proc.stdout.count('╭') >= 3  # outer + 2 inner
    assert proc.stdout.count('╰') >= 3


# ---------------------------------------------------------------------------
# draw_histogram
# ---------------------------------------------------------------------------


def test_draw_histogram_returns_list():
    result = draw_histogram([0.001, 0.002, 0.003], 10, 4)

    assert isinstance(result, list)


def test_draw_histogram_height_matches():
    result = draw_histogram([0.001, 0.002, 0.003], 10, 4)

    assert len(result) == 4


def test_draw_histogram_width_matches():
    result = draw_histogram([0.001, 0.002, 0.003], 10, 4)

    assert all(len(row) == 10 for row in result)


def test_draw_histogram_contains_block_chars():
    result = draw_histogram([0.001, 0.001, 0.002, 0.003, 0.003], 10, 4)
    all_text = ''.join(result)

    assert '█' in all_text


def test_draw_histogram_empty_durations_returns_empty():
    result = draw_histogram([], 10, 4)

    assert result == []


def test_draw_histogram_zero_width_returns_empty():
    result = draw_histogram([0.001, 0.002], 0, 4)

    assert result == []


def test_draw_histogram_zero_height_returns_empty():
    result = draw_histogram([0.001, 0.002], 10, 0)

    assert result == []


def test_draw_histogram_uniform_distribution_all_columns_nonempty():
    # Uniformly spaced values → each bucket should have at least one sample
    durations = [i * 0.001 for i in range(1, 21)]
    result = draw_histogram(durations, 20, 4)

    # Every column should have at least one '█' somewhere
    for col in range(20):
        col_chars = [row[col] for row in result]
        assert '█' in col_chars


def test_draw_histogram_all_equal_single_column_filled():
    # When hi == lo, only the middle column should be filled
    result = draw_histogram([0.001] * 10, 11, 4)
    mid = 5  # width // 2

    for row in result:
        assert row[mid] == '█'


def test_draw_histogram_all_equal_non_center_empty():
    result = draw_histogram([0.001] * 10, 11, 4)
    mid = 5

    for col in range(11):
        if col != mid:
            for row in result:
                assert row[col] == ' '


def test_draw_histogram_all_equal_height_matches():
    result = draw_histogram([0.001] * 10, 11, 8)

    assert len(result) == 8
    assert all(len(row) == 11 for row in result)


def test_draw_histogram_only_block_or_space():
    result = draw_histogram([0.001, 0.002, 0.003], 10, 4)

    for row in result:
        for ch in row:
            assert ch in ('█', ' ')


def test_draw_histogram_strings_in_list():
    result = draw_histogram([0.001, 0.002], 10, 4)

    assert all(isinstance(row, str) for row in result)


def test_draw_histogram_negative_width_returns_empty():
    result = draw_histogram([0.001, 0.002], -1, 4)

    assert result == []


def test_draw_histogram_negative_height_returns_empty():
    result = draw_histogram([0.001, 0.002], 10, -1)

    assert result == []


def test_draw_histogram_single_duration_all_equal():
    # Single value: hi == lo, same as all-equal case
    result = draw_histogram([0.005], 10, 4)
    mid = 5

    assert len(result) == 4
    for row in result:
        assert row[mid] == '█'


# ---------------------------------------------------------------------------
# Smoke: Scenario.cli --histogram outputs block chars
# ---------------------------------------------------------------------------


def test_scenario_cli_histogram_output_has_block_chars():
    script = textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s = Scenario(lambda: None, name='hist_test', number=10, timer=fake_timer)
        s.cli(['--histogram'])
    ''')
    proc = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
        check=False,
        env=_UTF8_ENV,
    )

    assert '█' in proc.stdout
    assert '╭' in proc.stdout
