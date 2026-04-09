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


class TestScenarioGroupCliOutput:
    def test_outputs_both_scenario_names(self) -> None:
        proc = run_script(group_script())
        assert 'benchmark: first' in proc.stdout
        assert 'benchmark: second' in proc.stdout

    def test_results_separated_by_divider(self) -> None:
        proc = run_script(group_script())
        assert '---' in proc.stdout

    def test_divider_between_not_after_last(self) -> None:
        proc = run_script(group_script())
        # group_script() has 2 scenarios → exactly 1 divider between them
        assert proc.stdout.count('---\n') == 1
        lines = proc.stdout.strip().splitlines()
        assert lines[-1] != '---'

    def test_exit_code_0_by_default(self) -> None:
        proc = run_script(group_script())
        assert proc.returncode == 0

    def test_outputs_mean_best_worst_for_each(self) -> None:
        proc = run_script(group_script())
        assert proc.stdout.count('mean:') == 2
        assert proc.stdout.count('best:') == 2
        assert proc.stdout.count('worst:') == 2

    def test_writes_to_stdout(self) -> None:
        proc = run_script(group_script())
        assert proc.stdout.strip() != ''
        assert proc.stderr == ''


class TestScenarioGroupCliNumberArg:
    def test_number_arg_accepted(self) -> None:
        proc = run_script(group_script(), '--number', '3')
        assert proc.returncode == 0
        assert 'benchmark: first' in proc.stdout


class TestScenarioGroupCliMaxMean:
    def test_max_mean_passes_when_below(self) -> None:
        proc = run_script(group_script(), '--max-mean', '10.0')
        assert proc.returncode == 0

    def test_max_mean_fails_when_any_exceeds(self) -> None:
        proc = run_script(group_script(), '--max-mean', '0.000001')
        assert proc.returncode == 1

    def test_max_mean_still_prints_output_on_failure(self) -> None:
        proc = run_script(group_script(), '--max-mean', '0.000001')
        assert 'benchmark:' in proc.stdout

    def test_max_mean_and_number_combined(self) -> None:
        proc = run_script(group_script(), '--number', '3', '--max-mean', '10.0')
        assert proc.returncode == 0
        assert 'benchmark: first' in proc.stdout
        assert 'benchmark: second' in proc.stdout


class TestScenarioGroupCliHelp:
    def test_help_exits_0(self) -> None:
        proc = run_script(group_script(), '--help')
        assert proc.returncode == 0

    def test_help_mentions_number(self) -> None:
        proc = run_script(group_script(), '--help')
        combined = proc.stdout + proc.stderr
        assert 'number' in combined.lower()


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


class TestScenarioGroupCliDividers:
    def test_single_scenario_no_divider(self) -> None:
        proc = run_script(single_scenario_script())
        assert '---' not in proc.stdout

    def test_three_scenarios_two_dividers(self) -> None:
        proc = run_script(three_scenario_script())
        assert proc.stdout.count('---') == 2
