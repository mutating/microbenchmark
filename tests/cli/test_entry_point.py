from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent.parent)


def run_entry(
    *args: str,
    timeout: int = 30,
    env_path: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, 'PYTHONUTF8': '1'}
    if env_path is not None:
        env['PYTHONPATH'] = env_path
    return subprocess.run(
        [sys.executable, '-m', 'microbenchmark', *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=timeout,
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
    )


# ---------------------------------------------------------------------------
# Scenario target
# ---------------------------------------------------------------------------


def test_entry_scenario_exit_0():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3')

    assert proc.returncode == 0


def test_entry_scenario_output_has_benchmark_name():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3')

    assert 'sample' in proc.stdout


def test_entry_scenario_output_has_mean():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3')

    assert 'mean:' in proc.stdout


# ---------------------------------------------------------------------------
# ScenarioGroup target
# ---------------------------------------------------------------------------


def test_entry_group_exit_0():
    proc = run_entry('tests.cli.fixtures.sample:group', '--number', '3')

    assert proc.returncode == 0


def test_entry_group_output_not_empty():
    proc = run_entry('tests.cli.fixtures.sample:group', '--number', '3')

    assert proc.stdout.strip() != ''


# ---------------------------------------------------------------------------
# Error: bad target format
# ---------------------------------------------------------------------------


def test_entry_no_args_exit_3():
    proc = run_entry()

    assert proc.returncode == 3


def test_entry_no_args_writes_to_stderr():
    proc = run_entry()

    assert proc.stderr.strip() != ''


def test_entry_bad_format_no_colon_exit_3():
    proc = run_entry('my_module_no_colon')

    assert proc.returncode == 3


def test_entry_bad_format_multiple_colons_is_ok():
    # module.path:attr — extra dots in module are fine but colon must exist once
    proc = run_entry('nonexistent.module:attr')

    assert proc.returncode == 3


def test_entry_empty_module_exit_3():
    proc = run_entry(':some_attr')

    assert proc.returncode == 3


def test_entry_empty_module_writes_to_stderr():
    proc = run_entry(':some_attr')

    assert proc.stderr.strip() != ''


def test_entry_empty_attr_exit_3():
    proc = run_entry('some.module:')

    assert proc.returncode == 3


def test_entry_empty_attr_writes_to_stderr():
    proc = run_entry('some.module:')

    assert proc.stderr.strip() != ''


# ---------------------------------------------------------------------------
# Error: nonexistent module
# ---------------------------------------------------------------------------


def test_entry_nonexistent_module_exit_3():
    proc = run_entry('nonexistent_module_xyz:scenario')

    assert proc.returncode == 3


def test_entry_nonexistent_module_writes_to_stderr():
    proc = run_entry('nonexistent_module_xyz:scenario')

    assert proc.stderr.strip() != ''


# ---------------------------------------------------------------------------
# Error: nonexistent attribute
# ---------------------------------------------------------------------------


def test_entry_nonexistent_attr_exit_3():
    proc = run_entry('tests.cli.fixtures.sample:does_not_exist')

    assert proc.returncode == 3


def test_entry_nonexistent_attr_writes_to_stderr():
    proc = run_entry('tests.cli.fixtures.sample:does_not_exist')

    assert proc.stderr.strip() != ''


# ---------------------------------------------------------------------------
# Attribute is not Scenario or ScenarioGroup
# ---------------------------------------------------------------------------


def test_entry_not_scenario_exit_3():
    proc = run_entry('tests.cli.fixtures.sample:not_a_scenario')

    assert proc.returncode == 3


def test_entry_not_scenario_writes_to_stderr():
    proc = run_entry('tests.cli.fixtures.sample:not_a_scenario')

    assert proc.stderr.strip() != ''


# ---------------------------------------------------------------------------
# --number forwarding
# ---------------------------------------------------------------------------


def test_entry_number_forwarded():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '5')

    assert proc.returncode == 0
    assert '5' in proc.stdout


# ---------------------------------------------------------------------------
# --max-mean forwarding
# ---------------------------------------------------------------------------


def test_entry_max_mean_pass():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3', '--max-mean', '9999')

    assert proc.returncode == 0


def test_entry_max_mean_fail_exit_1():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3', '--max-mean', '0.0000001')

    assert proc.returncode == 1


# ---------------------------------------------------------------------------
# python -m microbenchmark (no args)
# ---------------------------------------------------------------------------


def test_entry_no_args_via_module_invocation():
    proc = subprocess.run(
        [sys.executable, '-m', 'microbenchmark'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=30,
        check=False,
        cwd=PROJECT_ROOT,
    )

    assert proc.returncode == 3


# ---------------------------------------------------------------------------
# --histogram forwarding
# ---------------------------------------------------------------------------


def test_entry_histogram_scenario_produces_block_chars():
    proc = run_entry('tests.cli.fixtures.sample:scenario', '--number', '3', '--histogram')

    assert proc.returncode == 0
    assert '█' in proc.stdout


def test_entry_histogram_group_produces_block_chars():
    proc = run_entry('tests.cli.fixtures.sample:group', '--number', '3', '--histogram')

    assert proc.returncode == 0
    assert '█' in proc.stdout
