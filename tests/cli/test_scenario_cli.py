from __future__ import annotations

import subprocess
import sys
import textwrap

from microbenchmark import Scenario


def run_script(script: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, '-c', script, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=timeout,
        check=False,
    )


def scenario_script(extra: str = '') -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s = Scenario(lambda: None, name='bench', number=10, timer=fake_timer)
        {extra}
        s.cli()
    ''')


def named_fn_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        def my_function():
            pass

        s = Scenario(my_function, name='bench', number=5, timer=fake_timer)
        s.cli()
    ''')


def doc_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        s = Scenario(lambda: None, name='bench', doc='My benchmark doc.', number=5, timer=fake_timer)
        s.cli()
    ''')


def args_script() -> str:
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario, arguments

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        def add(x, y):
            return x + y

        s = Scenario(add, arguments(1, 2), name='bench', number=5, timer=fake_timer)
        s.cli()
    ''')


def callable_class_script() -> str:
    """Script with a callable class instance (no __name__) to cover superrepr path."""
    return textwrap.dedent(f'''
        import sys
        sys.path.insert(0, {str(__import__('pathlib').Path(__file__).parent.parent.parent)!r})
        from microbenchmark import Scenario

        tick = [0.0]
        def fake_timer():
            tick[0] += 0.001
            return tick[0]

        class MyCallable:
            def __call__(self):
                pass

        s = Scenario(MyCallable(), name='bench', number=3, timer=fake_timer)
        s.cli()
    ''')


# ---------------------------------------------------------------------------
# Border output
# ---------------------------------------------------------------------------


def test_cli_output_has_top_border():
    proc = run_script(scenario_script())

    assert '╭' in proc.stdout


def test_cli_output_has_bottom_border():
    proc = run_script(scenario_script())

    assert '╰' in proc.stdout


def test_cli_output_has_side_borders():
    proc = run_script(scenario_script())

    assert '│' in proc.stdout


# ---------------------------------------------------------------------------
# Basic output
# ---------------------------------------------------------------------------


def test_cli_callable_without_name_shows_call():
    proc = run_script(callable_class_script())

    assert 'call:' in proc.stdout
    assert 'benchmark: bench' in proc.stdout


def test_cli_outputs_name():
    proc = run_script(scenario_script())

    assert 'benchmark: bench' in proc.stdout


def test_cli_outputs_mean():
    proc = run_script(scenario_script())

    assert 'mean:' in proc.stdout


def test_cli_outputs_best():
    proc = run_script(scenario_script())

    assert 'best:' in proc.stdout


def test_cli_outputs_worst():
    proc = run_script(scenario_script())

    assert 'worst:' in proc.stdout


def test_cli_exit_code_0_by_default():
    proc = run_script(scenario_script())

    assert proc.returncode == 0


def test_cli_writes_to_stdout():
    proc = run_script(scenario_script())

    assert proc.stdout.strip() != ''
    assert proc.stderr == ''


# ---------------------------------------------------------------------------
# New output fields (TDD — will pass after Stage 8 implementation)
# ---------------------------------------------------------------------------


def test_cli_shows_call_line():
    proc = run_script(scenario_script())

    assert 'call:' in proc.stdout


def test_cli_shows_runs_count():
    proc = run_script(scenario_script())

    assert 'runs:' in proc.stdout


def test_cli_shows_median():
    proc = run_script(scenario_script())

    assert 'median:' in proc.stdout


def test_cli_shows_p95_mean():
    proc = run_script(scenario_script())

    assert 'p95 mean:' in proc.stdout


def test_cli_shows_p99_mean():
    proc = run_script(scenario_script())

    assert 'p99 mean:' in proc.stdout


def test_cli_shows_total():
    proc = run_script(scenario_script())
    total_lines = [line for line in proc.stdout.splitlines() if 'total:' in line and 'fn total:' not in line]

    assert len(total_lines) == 1


def test_cli_shows_fn_total():
    proc = run_script(scenario_script())

    assert 'fn total:' in proc.stdout


def test_cli_shows_function_name():
    proc = run_script(named_fn_script())

    assert 'my_function' in proc.stdout


def test_cli_shows_doc_when_present():
    proc = run_script(doc_script())

    assert 'doc:' in proc.stdout
    assert 'My benchmark doc.' in proc.stdout


def test_cli_omits_doc_when_empty():
    proc = run_script(scenario_script())

    assert 'doc:' not in proc.stdout


def test_cli_shows_runs_value():
    proc = run_script(scenario_script())
    runs_lines = [line for line in proc.stdout.splitlines() if 'runs:' in line]

    assert len(runs_lines) == 1
    assert '10' in runs_lines[0]


def test_cli_shows_arguments_when_present():
    proc = run_script(args_script())

    assert 'call:' in proc.stdout
    assert 'add(1, 2)' in proc.stdout


# ---------------------------------------------------------------------------
# FAIL message for --max-mean
# ---------------------------------------------------------------------------


def test_cli_max_mean_fail_message():
    proc = run_script(scenario_script(), '--max-mean', '0.000001')

    assert 'FAIL:' in proc.stdout


def test_cli_max_mean_fail_message_shows_mean():
    proc = run_script(scenario_script(), '--max-mean', '0.000001')

    assert 'mean' in proc.stdout
    assert 'exceeds' in proc.stdout


def test_cli_max_mean_fail_message_shows_threshold():
    proc = run_script(scenario_script(), '--max-mean', '0.000001')

    assert '0.000001' in proc.stdout


# ---------------------------------------------------------------------------
# --number argument
# ---------------------------------------------------------------------------


def test_number_arg_accepted():
    proc = run_script(scenario_script(), '--number', '5')

    assert proc.returncode == 0
    assert 'benchmark: bench' in proc.stdout


def test_number_arg_default_uses_scenario_number():
    proc = run_script(scenario_script())

    assert proc.returncode == 0


# ---------------------------------------------------------------------------
# --max-mean argument
# ---------------------------------------------------------------------------


def test_max_mean_below_threshold_exit_0():
    proc = run_script(scenario_script(), '--max-mean', '1.0')

    assert proc.returncode == 0


def test_max_mean_above_threshold_exit_1():
    proc = run_script(scenario_script(), '--max-mean', '0.000001')

    assert proc.returncode == 1


def test_max_mean_still_prints_output():
    proc = run_script(scenario_script(), '--max-mean', '0.000001')

    assert 'benchmark: bench' in proc.stdout


def test_max_mean_just_above_mean_exit_0():
    # fake_timer: mean ≈ 0.001; threshold 0.002 is above mean → passes
    proc = run_script(scenario_script(), '--max-mean', '0.002')

    assert proc.returncode == 0


# ---------------------------------------------------------------------------
# --help
# ---------------------------------------------------------------------------


def test_help_exits_0():
    proc = run_script(scenario_script(), '--help')

    assert proc.returncode == 0


def test_help_output_not_empty():
    proc = run_script(scenario_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert len(combined) > 0


def test_help_mentions_number():
    proc = run_script(scenario_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert 'number' in combined.lower()


def test_help_mentions_max_mean():
    proc = run_script(scenario_script(), '--help')
    combined = proc.stdout + proc.stderr

    assert '--max-mean' in combined


def test_help_does_not_run_benchmark():
    proc = run_script(scenario_script(), '--help')

    assert 'benchmark:' not in proc.stdout


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_number_zero_fails():
    proc = run_script(scenario_script(), '--number', '0')

    assert proc.returncode != 0


def test_number_negative_fails():
    proc = run_script(scenario_script(), '--number', '-1')

    assert proc.returncode != 0


def test_number_and_max_mean_combined():
    proc = run_script(scenario_script(), '--number', '5', '--max-mean', '10.0')

    assert proc.returncode == 0
    assert 'benchmark: bench' in proc.stdout


# ---------------------------------------------------------------------------
# cli(argv=...) parameter
# ---------------------------------------------------------------------------


def test_cli_argv_overrides_sysargv():
    tick = [0.0]

    def fake_timer() -> float:
        tick[0] += 0.001
        return tick[0]

    s = Scenario(lambda: None, name='argv_test', number=10, timer=fake_timer)

    original_write = sys.stdout.write
    captured: list[str] = []

    def capture_write(text: str) -> int:
        captured.append(text)
        return len(text)

    sys.stdout.write = capture_write  # type: ignore[method-assign]
    try:
        s.cli(argv=['--number', '3'])
    finally:
        sys.stdout.write = original_write  # type: ignore[method-assign]

    combined = ''.join(captured)
    assert 'argv_test' in combined
    assert '3' in combined


def test_cli_argv_empty_list_uses_defaults():
    tick = [0.0]

    def fake_timer() -> float:
        tick[0] += 0.001
        return tick[0]

    s = Scenario(lambda: None, name='default_test', number=5, timer=fake_timer)

    captured: list[str] = []
    original_write = sys.stdout.write

    def capture_write(text: str) -> int:
        captured.append(text)
        return len(text)

    sys.stdout.write = capture_write  # type: ignore[method-assign]
    try:
        s.cli(argv=[])
    finally:
        sys.stdout.write = original_write  # type: ignore[method-assign]

    combined = ''.join(captured)
    assert 'default_test' in combined


# ---------------------------------------------------------------------------
# --histogram argument
# ---------------------------------------------------------------------------


def test_histogram_flag_produces_block_chars():
    proc = run_script(scenario_script(), '--histogram')

    assert '█' in proc.stdout


def test_histogram_flag_still_shows_name():
    proc = run_script(scenario_script(), '--histogram')

    assert 'benchmark: bench' in proc.stdout


def test_histogram_flag_exit_0():
    proc = run_script(scenario_script(), '--histogram')

    assert proc.returncode == 0


def test_histogram_and_max_mean_combined():
    proc = run_script(scenario_script(), '--histogram', '--max-mean', '10.0')

    assert proc.returncode == 0
    assert '█' in proc.stdout
