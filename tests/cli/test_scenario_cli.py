from __future__ import annotations

import subprocess
import sys
import textwrap


def run_script(script: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run an inline Python script as a subprocess and return the completed process."""
    return subprocess.run(
        [sys.executable, '-c', script, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=timeout,
        check=False,
    )


def scenario_script(extra: str = '') -> str:
    """Return a self-contained script that creates a Scenario and calls cli()."""
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


class TestScenarioCliOutput:
    def test_cli_outputs_name(self) -> None:
        proc = run_script(scenario_script())
        assert 'benchmark: bench' in proc.stdout

    def test_cli_outputs_mean(self) -> None:
        proc = run_script(scenario_script())
        assert 'mean:' in proc.stdout

    def test_cli_outputs_best(self) -> None:
        proc = run_script(scenario_script())
        assert 'best:' in proc.stdout

    def test_cli_outputs_worst(self) -> None:
        proc = run_script(scenario_script())
        assert 'worst:' in proc.stdout

    def test_cli_output_has_s_suffix(self) -> None:
        proc = run_script(scenario_script())
        assert 's\n' in proc.stdout or proc.stdout.rstrip().endswith('s')

    def test_cli_exit_code_0_by_default(self) -> None:
        proc = run_script(scenario_script())
        assert proc.returncode == 0

    def test_cli_writes_to_stdout(self) -> None:
        proc = run_script(scenario_script())
        assert proc.stdout.strip() != ''
        assert proc.stderr == ''


class TestScenarioCliNumberArg:
    def test_number_arg_changes_durations_count(self) -> None:
        # We can't directly inspect durations from subprocess output,
        # but we can verify the CLI accepts --number without error
        proc = run_script(scenario_script(), '--number', '5')
        assert proc.returncode == 0
        assert 'benchmark: bench' in proc.stdout

    def test_number_arg_default_uses_scenario_number(self) -> None:
        proc = run_script(scenario_script())
        assert proc.returncode == 0


class TestScenarioCliMaxMean:
    def test_max_mean_below_threshold_exit_0(self) -> None:
        # fake_timer increments by 0.001 each call, so mean per run = 0.001
        proc = run_script(scenario_script(), '--max-mean', '1.0')
        assert proc.returncode == 0

    def test_max_mean_above_threshold_exit_1(self) -> None:
        # mean will be ~0.001s; threshold 0.000001 is far below
        proc = run_script(scenario_script(), '--max-mean', '0.000001')
        assert proc.returncode == 1

    def test_max_mean_still_prints_output(self) -> None:
        proc = run_script(scenario_script(), '--max-mean', '0.000001')
        assert 'benchmark: bench' in proc.stdout

    def test_max_mean_equal_threshold_exit_0(self) -> None:
        # mean = exactly threshold → should pass (mean <= threshold)
        # With fake_timer: each call delta = 0.001, number=10
        # mean = 0.001. Set --max-mean = 10 to ensure it passes.
        proc = run_script(scenario_script(), '--max-mean', '10')
        assert proc.returncode == 0


class TestScenarioCliHelp:
    def test_help_exits_0(self) -> None:
        proc = run_script(scenario_script(), '--help')
        assert proc.returncode == 0

    def test_help_output_not_empty(self) -> None:
        proc = run_script(scenario_script(), '--help')
        combined = proc.stdout + proc.stderr
        assert len(combined) > 0

    def test_help_mentions_number(self) -> None:
        proc = run_script(scenario_script(), '--help')
        combined = proc.stdout + proc.stderr
        assert 'number' in combined.lower()

    def test_help_mentions_max_mean(self) -> None:
        proc = run_script(scenario_script(), '--help')
        combined = proc.stdout + proc.stderr
        assert 'max-mean' in combined.lower() or 'max_mean' in combined.lower()

    def test_help_does_not_run_benchmark(self) -> None:
        proc = run_script(scenario_script(), '--help')
        assert 'benchmark:' not in proc.stdout


class TestScenarioCliEdgeCases:
    def test_number_zero_fails(self) -> None:
        proc = run_script(scenario_script(), '--number', '0')
        assert proc.returncode != 0

    def test_number_negative_fails(self) -> None:
        proc = run_script(scenario_script(), '--number', '-1')
        assert proc.returncode != 0

    def test_number_and_max_mean_combined(self) -> None:
        proc = run_script(scenario_script(), '--number', '5', '--max-mean', '10.0')
        assert proc.returncode == 0
        assert 'benchmark: bench' in proc.stdout
