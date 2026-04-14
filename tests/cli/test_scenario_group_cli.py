from __future__ import annotations

import subprocess
import sys
import textwrap


def run_script(script: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-c', script, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=timeout,
        check=False,
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
# Basic output
# ---------------------------------------------------------------------------


def test_outputs_both_scenario_names():
    proc = run_script(group_script())

    assert 'benchmark: first' in proc.stdout
    assert 'benchmark: second' in proc.stdout


def test_results_separated_by_divider():
    proc = run_script(group_script())

    assert '---' in proc.stdout


def test_divider_between_not_after_last():
    proc = run_script(group_script())

    assert proc.stdout.count('---\n') == 1
    lines = proc.stdout.strip().splitlines()
    assert lines[-1] != '---'


def test_exit_code_0_by_default():
    proc = run_script(group_script())

    assert proc.returncode == 0


def test_outputs_mean_best_worst_for_each():
    proc = run_script(group_script())
    lines = proc.stdout.splitlines()
    mean_lines = [line for line in lines if line.startswith('mean:')]
    best_lines = [line for line in lines if line.startswith('best:')]
    worst_lines = [line for line in lines if line.startswith('worst:')]

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


def test_single_scenario_no_divider():
    proc = run_script(single_scenario_script())

    assert '---' not in proc.stdout


def test_three_scenarios_two_dividers():
    proc = run_script(three_scenario_script())

    assert proc.stdout.count('---') == 2
