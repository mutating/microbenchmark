from __future__ import annotations

import argparse
import sys

from microbenchmark._render import (
    draw_box,
    draw_histogram,
    draw_histogram_axis,
    draw_nested,
    histogram_bounds,
    terminal_width,
)
from microbenchmark.benchmark_result import BenchmarkResult
from microbenchmark.scenario import Scenario, _render_result


class _CliArgs:
    def __init__(self) -> None:
        self.number: int | None = None
        self.max_mean: float | None = None
        self.histogram: bool = False


class ScenarioGroup:
    def __init__(self, *scenarios: Scenario) -> None:
        self._scenarios: list[Scenario] = list(scenarios)

    def run(self, warmup: int = 0) -> list[BenchmarkResult]:
        return [s.run(warmup=warmup) for s in self._scenarios]

    def cli(self, argv: list[str] | None = None) -> None:
        parser = argparse.ArgumentParser(description='Run benchmark group')
        parser.add_argument('--number', type=int, default=None, help='Number of iterations')
        parser.add_argument('--max-mean', type=float, default=None, dest='max_mean',
                            help='Fail if any scenario mean time (seconds) exceeds this threshold')
        parser.add_argument('--histogram', action='store_true', default=False,
                            help='Append an ASCII histogram of per-call timings')
        cli_args = _CliArgs()
        parser.parse_args(argv, namespace=cli_args)

        scenarios = self._scenarios
        if cli_args.number is not None:
            scenarios = [
                _make_scenario_with_number(s, cli_args.number)
                for s in self._scenarios
            ]

        if not scenarios:
            return

        width = terminal_width()
        inner_width = width - 4  # inner blocks are width-4 wide
        inner_blocks: list[list[str]] = []
        results: list[BenchmarkResult] = []
        for scenario in scenarios:
            result = scenario.run()
            results.append(result)
            lines = _render_result(result)
            if cli_args.histogram:
                hist_width = inner_width - 4
                lines.append('')
                lines.extend(draw_histogram(list(result.durations), hist_width, 8))
                lo, hi = histogram_bounds(result.durations)
                lines.append(draw_histogram_axis(lo, hi, hist_width))
            inner_blocks.append(draw_box(lines, inner_width))

        nested = draw_nested(inner_blocks, [], width)
        sys.stdout.write('\n'.join(nested) + '\n')

        failed = False
        for result in results:
            if cli_args.max_mean is not None and result.mean > cli_args.max_mean:
                sys.stdout.write(
                    f'FAIL: mean {result.mean:.6f}s exceeds --max-mean {cli_args.max_mean:.6f}s\n',
                )
                failed = True

        if failed:
            sys.exit(1)

    def __add__(self, other: object) -> ScenarioGroup:
        if isinstance(other, Scenario):
            return ScenarioGroup(*self._scenarios, other)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*self._scenarios, *other._scenarios)
        return NotImplemented

    def __radd__(self, other: object) -> ScenarioGroup:
        if isinstance(other, Scenario):
            return ScenarioGroup(other, *self._scenarios)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*other._scenarios, *self._scenarios)
        return NotImplemented


def _make_scenario_with_number(s: Scenario, number: int) -> Scenario:
    return Scenario(
        s.function,
        s._arguments,
        name=s.name,
        doc=s.doc,
        number=number,
        timer=s._timer,
    )
