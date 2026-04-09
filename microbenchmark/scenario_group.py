from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from microbenchmark.benchmark_result import BenchmarkResult
from microbenchmark.scenario import Scenario, _print_result

if TYPE_CHECKING:
    pass


class ScenarioGroup:
    def __init__(self, *scenarios: Scenario) -> None:
        self._scenarios: list[Scenario] = list(scenarios)

    def run(self, warmup: int = 0) -> list[BenchmarkResult]:
        return [s.run(warmup=warmup) for s in self._scenarios]

    def cli(self) -> None:
        parser = argparse.ArgumentParser(description='Run benchmark group')
        parser.add_argument('--number', type=int, default=None, help='Number of iterations')
        parser.add_argument('--max-mean', type=float, default=None, dest='max_mean',
                            help='Fail if any scenario mean time (seconds) exceeds this threshold')
        parsed = parser.parse_args()

        scenarios = self._scenarios
        if parsed.number is not None:
            scenarios = [
                _make_scenario_with_number(s, parsed.number)
                for s in self._scenarios
            ]

        failed = False
        for i, scenario in enumerate(scenarios):
            result = scenario.run()
            _print_result(result)
            if i < len(scenarios) - 1:
                sys.stdout.write('---\n')
            if parsed.max_mean is not None and result.mean > parsed.max_mean:
                failed = True

        if failed:
            sys.exit(1)

    def __add__(self, other: object) -> ScenarioGroup:
        if isinstance(other, Scenario):
            return ScenarioGroup(*self._scenarios, other)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*self._scenarios, *other._scenarios)
        return NotImplemented  # type: ignore[return-value]

    def __radd__(self, other: object) -> ScenarioGroup:
        if isinstance(other, Scenario):
            return ScenarioGroup(other, *self._scenarios)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*other._scenarios, *self._scenarios)
        return NotImplemented  # type: ignore[return-value]


def _make_scenario_with_number(s: Scenario, number: int) -> Scenario:
    return Scenario(
        s.function,
        s._args,
        name=s.name,
        doc=s.doc,
        number=number,
        timer=s._timer,
    )
