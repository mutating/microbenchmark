from __future__ import annotations

import argparse
import sys
import time
from typing import TYPE_CHECKING, Callable

from printo import describe_data_object
from printo.reprs import superrepr
from sigmatch import SignatureMismatchError

from microbenchmark._render import draw_box, draw_histogram, terminal_width
from microbenchmark.arguments import arguments as Arguments  # noqa: N812
from microbenchmark.benchmark_result import BenchmarkResult

if TYPE_CHECKING:  # pragma: no cover
    from microbenchmark.scenario_group import ScenarioGroup


class _CliArgs:
    def __init__(self) -> None:
        self.number: int | None = None
        self.max_mean: float | None = None
        self.histogram: bool = False


class Scenario:
    def __init__(  # noqa: PLR0913
        self,
        function: object,
        arguments: Arguments | None = None,
        *,
        name: str | None = None,
        doc: str = '',
        number: int = 1000,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        if number < 1:
            raise ValueError(f'number must be at least 1, got {number}')
        checker: Arguments = arguments if isinstance(arguments, Arguments) else Arguments()
        if not checker.match(function):
            fn_name: object = getattr(function, '__name__', repr(function))
            raise SignatureMismatchError(
                f'Scenario arguments {checker!r} are incompatible with the '
                f'signature of {fn_name}',
            )
        self.function: object = function
        self._arguments: Arguments | None = arguments
        if name is None and hasattr(function, '__name__'):
            name = function.__name__
        self.name: str | None = name
        self.doc = doc
        self.number = number
        self._timer = timer

    def _call_once(self) -> None:
        if self._arguments is not None:
            self.function(*self._arguments.args, **self._arguments.kwargs)  # type: ignore[operator]
        else:
            self.function()  # type: ignore[operator]

    def run(self, warmup: int = 0) -> BenchmarkResult:
        timer = self._timer
        for _ in range(max(warmup, 0)):
            timer()
            self._call_once()
            timer()
        durations: list[float] = []
        loop_start = timer()
        for _ in range(self.number):
            start = timer()
            self._call_once()
            end = timer()
            durations.append(end - start)
        loop_end = timer()
        return BenchmarkResult(
            scenario=self,
            durations=tuple(durations),
            total_duration=loop_end - loop_start,
            is_primary=True,
        )

    def cli(self, argv: list[str] | None = None) -> None:
        parser = argparse.ArgumentParser(description=self.doc or f'Benchmark: {self.name}')
        parser.add_argument('--number', type=int, default=None, help='Number of iterations')
        parser.add_argument('--max-mean', type=float, default=None, dest='max_mean',
                            help='Fail if mean time (seconds) exceeds this threshold')
        parser.add_argument('--histogram', action='store_true', default=False,
                            help='Append an ASCII histogram of per-call timings')
        cli_args = _CliArgs()
        parser.parse_args(argv, namespace=cli_args)

        scenario = self
        if cli_args.number is not None:
            scenario = Scenario(
                self.function,
                self._arguments,
                name=self.name,
                doc=self.doc,
                number=cli_args.number,
                timer=self._timer,
            )

        result = scenario.run()
        width = terminal_width()
        lines = _render_result(result)
        if cli_args.histogram:
            lines.append('')
            lines.extend(draw_histogram(list(result.durations), width - 4, 8))
        box = draw_box(lines, width)
        sys.stdout.write('\n'.join(box) + '\n')

        if cli_args.max_mean is not None and result.mean > cli_args.max_mean:
            sys.stdout.write(
                f'FAIL: mean {result.mean:.6f}s exceeds --max-mean {cli_args.max_mean:.6f}s\n',
            )
            sys.exit(1)

    def __add__(self, other: object) -> ScenarioGroup:
        from microbenchmark.scenario_group import ScenarioGroup  # noqa: PLC0415
        if isinstance(other, Scenario):
            return ScenarioGroup(self, other)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(self, *other._scenarios)
        return NotImplemented

    def __radd__(self, other: object) -> ScenarioGroup:
        from microbenchmark.scenario_group import ScenarioGroup  # noqa: PLC0415
        if isinstance(other, Scenario):
            return ScenarioGroup(other, self)
        if isinstance(other, ScenarioGroup):
            return ScenarioGroup(*other._scenarios, self)
        return NotImplemented


def _fn_call_str(function: object, arguments: Arguments | None) -> str:
    dunder_name: str | None = None
    if hasattr(function, '__name__'):
        dunder_name = str(function.__name__)  # type: ignore[misc]
    if dunder_name is not None and dunder_name != '<lambda>':
        fn_name: str = dunder_name
    else:
        try:
            fn_name = superrepr(function)
        except OSError:
            fn_name = dunder_name if dunder_name is not None else repr(function)
    args = arguments.args if arguments is not None else ()
    kwargs = arguments.kwargs if arguments is not None else {}
    return describe_data_object(fn_name, args, kwargs)


def _render_result(result: BenchmarkResult) -> list[str]:
    scenario = result.scenario
    assert scenario is not None
    call_str = _fn_call_str(scenario.function, scenario._arguments)
    label_width = len('p95 mean:')
    lines: list[str] = []
    lines.append(f'benchmark: {scenario.name}')
    lines.append(f'{"call:".ljust(label_width)} {call_str}')
    if scenario.doc:
        lines.append(f'{"doc:".ljust(label_width)} {scenario.doc}')
    lines.append(f'{"runs:".ljust(label_width)} {scenario.number}')
    lines.append(f'{"mean:".ljust(label_width)} {result.mean:.6f}s')
    lines.append(f'{"median:".ljust(label_width)} {result.median:.6f}s')
    lines.append(f'{"best:".ljust(label_width)} {result.best:.6f}s')
    lines.append(f'{"worst:".ljust(label_width)} {result.worst:.6f}s')
    lines.append(f'{"p95 mean:".ljust(label_width)} {result.p95.mean:.6f}s')
    lines.append(f'{"p99 mean:".ljust(label_width)} {result.p99.mean:.6f}s')
    lines.append(f'{"total:".ljust(label_width)} {result.total_duration:.6f}s')
    lines.append(f'{"fn total:".ljust(label_width)} {result.functions_duration:.6f}s')
    return lines
