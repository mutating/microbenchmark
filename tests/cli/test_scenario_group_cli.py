from __future__ import annotations

import os
import subprocess
import sys
import textwrap

from microbenchmark import Scenario, ScenarioGroup

_UTF8_ENV = {**os.environ, 'PYTHONUTF8': '1'}


def run_script(script: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-c', script, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=timeout,
        check=False,
        env=_UTF8_ENV,
    )


def group_script(extra: str = '') -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s1 = Scenario(lambda: None, name='first', number=5, timer=fake_timer)
        s2 = Scenario(lambda: None, name='second', number=5, timer=fake_timer)
        group = s1 + s2
        {extra}
        group.cli()
    ''')


def empty_group_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import ScenarioGroup

        group = ScenarioGroup()
        group.cli()
    ''')


def single_scenario_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s1 = Scenario(lambda: None, name='only', number=5, timer=fake_timer)
        group = ScenarioGroup(s1)
        group.cli()
    ''')


def three_scenario_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s1 = Scenario(lambda: None, name='a', number=5, timer=fake_timer)
        s2 = Scenario(lambda: None, name='b', number=5, timer=fake_timer)
        s3 = Scenario(lambda: None, name='c', number=5, timer=fake_timer)
        group = ScenarioGroup(s1, s2, s3)
        group.cli()
    ''')


def mixed_speed_group_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        slow_tick = [0.0]
        def slow_timer():
            slow_tick[0] += 1.0
            return slow_tick[0]

        fast_tick = [0.0]
        def fast_timer():
            fast_tick[0] += 0.001
            return fast_tick[0]

        s1 = Scenario(lambda: None, name='slow', number=5, timer=slow_timer)
        s2 = Scenario(lambda: None, name='fast', number=5, timer=fast_timer)
        group = s1 + s2
        group.cli()
    ''')


def doc_group_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, ScenarioGroup

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s1 = Scenario(lambda: None, name='alpha', doc='First scenario.', number=5, timer=fake_timer)
        s2 = Scenario(lambda: None, name='beta', number=5, timer=fake_timer)
        group = s1 + s2
        group.cli()
    ''')


# ---------------------------------------------------------------------------
# Border output
# ---------------------------------------------------------------------------


def test_group_cli_has_outer_border():
    proc = run_script(group_script())

    assert '╭' in proc.stdout
    assert '╰' in proc.stdout


def test_group_cli_has_nested_inner_borders():
    proc = run_script(group_script())

    # outer border + 2 inner borders = at least 3 of each
    assert proc.stdout.count('╭') >= 3
    assert proc.stdout.count('╰') >= 3


# ---------------------------------------------------------------------------
# Basic output
# ---------------------------------------------------------------------------


def test_outputs_both_scenario_names():
    proc = run_script(group_script())

    assert 'benchmark: first' in proc.stdout
    assert 'benchmark: second' in proc.stdout


def test_results_separated_by_inner_boxes():
    proc = run_script(group_script())

    # Two scenarios produce two inner boxes plus one outer box = at least 3 ╭
    assert proc.stdout.count('╭') >= 3


def test_outer_box_present():
    proc = run_script(group_script())

    # Output ends with the outer bottom border
    lines = proc.stdout.strip().splitlines()
    assert lines[-1].startswith('╰')


def test_exit_code_0_by_default():
    proc = run_script(group_script())

    assert proc.returncode == 0


def test_outputs_mean_best_worst_for_each():
    proc = run_script(group_script())
    lines = proc.stdout.splitlines()
    mean_lines = [line for line in lines if 'mean:' in line and 'p95' not in line and 'p99' not in line]
    best_lines = [line for line in lines if 'best:' in line]
    worst_lines = [line for line in lines if 'worst:' in line]

    assert len(mean_lines) == 2
    assert len(best_lines) == 2
    assert len(worst_lines) == 2


def test_writes_to_stdout():
    proc = run_script(group_script())

    assert proc.stdout.strip() != ''
    assert proc.stderr == ''


# ---------------------------------------------------------------------------
# New output fields (TDD — will pass after Stage 8 implementation)
# ---------------------------------------------------------------------------


def test_cli_shows_call_line_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('call:') == 2


def test_cli_shows_runs_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('runs:') == 2


def test_cli_shows_median_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('median:') == 2


def test_cli_shows_p95_mean_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('p95 mean:') == 2


def test_cli_shows_p99_mean_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('p99 mean:') == 2


def test_cli_shows_total_for_each():
    proc = run_script(group_script())
    total_lines = [line for line in proc.stdout.splitlines() if 'total:' in line and 'fn total:' not in line]

    assert len(total_lines) == 2


def test_cli_shows_fn_total_for_each():
    proc = run_script(group_script())

    assert proc.stdout.count('fn total:') == 2


def test_cli_shows_doc_when_present():
    proc = run_script(doc_group_script())

    assert 'doc:' in proc.stdout
    assert 'First scenario.' in proc.stdout


def test_cli_omits_doc_when_empty():
    proc = run_script(group_script())

    assert 'doc:' not in proc.stdout


# ---------------------------------------------------------------------------
# FAIL message for --max-mean
# ---------------------------------------------------------------------------


def test_max_mean_fail_message_shown():
    proc = run_script(group_script(), '--max-mean', '0.000001')

    assert 'FAIL:' in proc.stdout


def test_max_mean_fail_message_shows_exceeds():
    proc = run_script(group_script(), '--max-mean', '0.000001')

    assert 'exceeds' in proc.stdout


# ---------------------------------------------------------------------------
# --number argument
# ---------------------------------------------------------------------------


def test_number_arg_accepted():
    proc = run_script(group_script(), '--number', '3')

    assert proc.returncode == 0
    assert 'benchmark: first' in proc.stdout


def test_number_zero_fails():
    proc = run_script(group_script(), '--number', '0')

    assert proc.returncode != 0


def test_number_negative_fails():
    proc = run_script(group_script(), '--number', '-1')

    assert proc.returncode != 0


# ---------------------------------------------------------------------------
# --max-mean argument
# ---------------------------------------------------------------------------


def test_max_mean_passes_when_below():
    proc = run_script(group_script(), '--max-mean', '10.0')

    assert proc.returncode == 0


def test_max_mean_fails_when_any_exceeds():
    proc = run_script(group_script(), '--max-mean', '0.000001')

    assert proc.returncode == 1


def test_max_mean_still_prints_output_on_failure():
    proc = run_script(group_script(), '--max-mean', '0.000001')

    assert 'benchmark:' in proc.stdout


def test_max_mean_and_number_combined():
    proc = run_script(group_script(), '--number', '3', '--max-mean', '10.0')

    assert proc.returncode == 0
    assert 'benchmark: first' in proc.stdout
    assert 'benchmark: second' in proc.stdout


def test_max_mean_fails_when_only_one_exceeds():
    proc = run_script(mixed_speed_group_script(), '--max-mean', '0.5')

    assert proc.returncode == 1
    assert 'benchmark: slow' in proc.stdout
    assert 'benchmark: fast' in proc.stdout


# ---------------------------------------------------------------------------
# --help
# ---------------------------------------------------------------------------


def test_help_exits_0():
    proc = run_script(group_script(), '--help')

    assert proc.returncode == 0


def test_help_mentions_number():
    proc = run_script(group_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert 'number' in combined.lower()


def test_help_mentions_max_mean():
    proc = run_script(group_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert '--max-mean' in combined


def test_help_does_not_run_benchmark():
    proc = run_script(group_script(), '--help')

    assert 'benchmark:' not in proc.stdout


def test_help_mentions_histogram():
    proc = run_script(group_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert '--histogram' in combined


# ---------------------------------------------------------------------------
# Empty group
# ---------------------------------------------------------------------------


def test_empty_group_exits_0():
    proc = run_script(empty_group_script())

    assert proc.returncode == 0


def test_empty_group_no_output():
    proc = run_script(empty_group_script())

    assert proc.stdout == ''
    assert proc.stderr == ''


# ---------------------------------------------------------------------------
# Dividers
# ---------------------------------------------------------------------------


def test_single_scenario_three_boxes():
    proc = run_script(single_scenario_script())

    # 1 inner box + 1 outer box = 2 ╭ chars
    assert proc.stdout.count('╭') == 2


def test_three_scenarios_four_boxes():
    proc = run_script(three_scenario_script())

    # 3 inner boxes + 1 outer box = 4 ╭ chars
    assert proc.stdout.count('╭') == 4


# ---------------------------------------------------------------------------
# cli(argv=...) parameter
# ---------------------------------------------------------------------------


def test_group_cli_argv_number_forwarded():
    tick = [0.0]

    def fake_timer() -> float:
        tick[0] += 0.001
        return tick[0]

    s = Scenario(lambda: None, name='g_test', number=10, timer=fake_timer)
    grp = ScenarioGroup(s)

    captured: list[str] = []
    original_write = sys.stdout.write

    def capture_write(text: str) -> int:
        captured.append(text)
        return len(text)

    sys.stdout.write = capture_write  # type: ignore[method-assign]
    try:
        grp.cli(argv=['--number', '3'])
    finally:
        sys.stdout.write = original_write  # type: ignore[method-assign]

    combined = ''.join(captured)
    assert 'g_test' in combined


# ---------------------------------------------------------------------------
# --histogram argument
# ---------------------------------------------------------------------------


def test_group_histogram_flag_produces_block_chars():
    proc = run_script(group_script(), '--histogram')

    assert '█' in proc.stdout


def test_group_histogram_flag_still_shows_names():
    proc = run_script(group_script(), '--histogram')

    assert 'benchmark: first' in proc.stdout
    assert 'benchmark: second' in proc.stdout


def test_group_histogram_flag_exit_0():
    proc = run_script(group_script(), '--histogram')

    assert proc.returncode == 0


def test_group_histogram_and_max_mean_combined():
    proc = run_script(group_script(), '--histogram', '--max-mean', '10.0')

    assert proc.returncode == 0
    assert '█' in proc.stdout
