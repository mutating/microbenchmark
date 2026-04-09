from __future__ import annotations

import argparse
import sys
import time
from typing import TYPE_CHECKING, Any, Callable

from microbenchmark.benchmark_result import BenchmarkResult

if TYPE_CHECKING:
    from microbenchmark.scenario_group import ScenarioGroup


class Scenario:
    def __init__(
        self,
        function: Callable[..., Any],
        args: list[Any] | None = None,
        *,
        name: str,
        doc: str = '',
        number: int = 1000,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        if number < 1:
            raise ValueError(f'number must be at least 1, got {number}')
        self.function = function
        self._args: list[Any] = list(args) if args is not None else []
        self.name = name
        self.doc = doc
        self.number = number
        self._timer = timer

    def run(self, warmup: int = 0) -> BenchmarkResult:
        function = self.function
        args = self._args
        timer = self._timer
        for _ in range(warmup):
            timer()
            function(*args)
            timer()
        durations: list[float] = []
        for _ in range(self.number):
            start = timer()
            function(*args)
            end = timer()
            durations.append(end - start)
        return BenchmarkResult(
            scenario=self,
            durations=tuple(durations),
            is_primary=True,
        )

    def cli(self) -> None:
        parser = argparse.ArgumentParser(description=self.doc or f'Benchmark: {self.name}')
        parser.add_argument('--number', type=int, default=None, help='Number of iterations')
        parser.add_argument('--max-mean', type=float, default=None, dest='max_mean',
                            help='Fail if mean time (seconds) exceeds this threshold')
        parsed = parser.parse_args()

        scenario = self
        if parsed.number is not None:
            scenario = Scenario(
                self.function,
                self._args,
                name=self.name,
                doc=self.doc,
                number=parsed.number,
                timer=self._timer,
            )

        result = scenario.run()
        _print_result(result)

        if parsed.max_mean is not None and result.mean > parsed.max_mean:
            sys.exit(1)

    def __add__(self, other: object) -> ScenarioGroup:
        from microbenchmark.scenario_group import ScenarioGroup  # noqa: PLC0415
        if isinstance(other, Scenario):
            return ScenarioGroup(self, other)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(self, *other._scenarios)
        return NotImplemented  # type: ignore[return-value]

    def __radd__(self, other: object) -> ScenarioGroup:
        from microbenchmark.scenario_group import ScenarioGroup  # noqa: PLC0415
        if isinstance(other, Scenario):
            return ScenarioGroup(other, self)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*other._scenarios, self)
        return NotImplemented  # type: ignore[return-value]


def _print_result(result: BenchmarkResult) -> None:
    sys.stdout.write(f'benchmark: {result.scenario.name}\n')  # type: ignore[union-attr]
    sys.stdout.write(f'mean:  {result.mean:.6f}s\n')
    sys.stdout.write(f'best:  {result.best:.6f}s\n')
    sys.stdout.write(f'worst: {result.worst:.6f}s\n')
