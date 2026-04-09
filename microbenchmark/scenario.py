from __future__ import annotations

import argparse
import sys
import time
from typing import TYPE_CHECKING, Callable

from microbenchmark.benchmark_result import BenchmarkResult

if TYPE_CHECKING:
    from microbenchmark.scenario_group import ScenarioGroup


class _CliArgs:
    def __init__(self) -> None:
        self.number: int | None = None
        self.max_mean: float | None = None


class Scenario:
    def __init__(  # noqa: PLR0913
        self,
        function: object,
        args: list[object] | None = None,
        *,
        name: str,
        doc: str = '',
        number: int = 1000,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        if number < 1:
            raise ValueError(f'number must be at least 1, got {number}')
        self.function: object = function
        self._args: list[object] = list(args) if args is not None else []
        self.name = name
        self.doc = doc
        self.number = number
        self._timer = timer

    def _call_once(self) -> None:
        self.function(*self._args)  # type: ignore[operator]

    def run(self, warmup: int = 0) -> BenchmarkResult:
        timer = self._timer
        for _ in range(warmup):
            timer()
            self._call_once()
            timer()
        durations: list[float] = []
        for _ in range(self.number):
            start = timer()
            self._call_once()
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
        cli_args = _CliArgs()
        parser.parse_args(namespace=cli_args)

        scenario = self
        if cli_args.number is not None:
            scenario = Scenario(
                self.function,
                self._args,
                name=self.name,
                doc=self.doc,
                number=cli_args.number,
                timer=self._timer,
            )

        result = scenario.run()
        _print_result(result)

        if cli_args.max_mean is not None and result.mean > cli_args.max_mean:
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
    scenario = result.scenario
    assert scenario is not None
    sys.stdout.write(f'benchmark: {scenario.name}\n')
    sys.stdout.write(f'mean:  {result.mean:.6f}s\n')
    sys.stdout.write(f'best:  {result.best:.6f}s\n')
    sys.stdout.write(f'worst: {result.worst:.6f}s\n')
