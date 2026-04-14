from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:  # pragma: no cover
    from microbenchmark.scenario import Scenario


class _ScenarioMeta(TypedDict):
    name: str | None
    doc: str
    number: int


class _ResultJson(TypedDict):
    durations: list[float]
    total_duration: float
    is_primary: bool
    scenario: _ScenarioMeta | None


@dataclass
class BenchmarkResult:
    scenario: Scenario | None
    durations: tuple[float, ...]
    total_duration: float
    is_primary: bool = True

    mean: float = field(init=False)
    best: float = field(init=False)
    worst: float = field(init=False)
    functions_duration: float = field(init=False)

    def __post_init__(self) -> None:
        self.mean = math.fsum(self.durations) / len(self.durations)
        self.best = min(self.durations)
        self.worst = max(self.durations)
        self.functions_duration = math.fsum(self.durations)

    def percentile(self, p: float) -> BenchmarkResult:
        if not (0 < p <= 100):
            raise ValueError(f'percentile must be in (0, 100], got {p}')
        keep_count = math.ceil(len(self.durations) * p / 100)
        trimmed = tuple(sorted(self.durations)[:keep_count])
        return BenchmarkResult(
            scenario=self.scenario,
            durations=trimmed,
            total_duration=0.0,
            is_primary=False,
        )

    @cached_property
    def median(self) -> float:
        return statistics.median(self.durations)

    @cached_property
    def p95(self) -> BenchmarkResult:
        return self.percentile(95)

    @cached_property
    def p99(self) -> BenchmarkResult:
        return self.percentile(99)

    def to_json(self) -> str:
        scenario_meta: _ScenarioMeta | None
        if self.scenario is not None:
            scenario_meta = _ScenarioMeta(
                name=self.scenario.name,
                doc=self.scenario.doc,
                number=self.scenario.number,
            )
        else:
            scenario_meta = None
        data: _ResultJson = _ResultJson(
            durations=list(self.durations),
            total_duration=self.total_duration,
            is_primary=self.is_primary,
            scenario=scenario_meta,
        )
        return json.dumps(data)

    @classmethod
    def from_json(cls, data: str) -> BenchmarkResult:
        raw: object = json.loads(data)
        if not isinstance(raw, dict):
            raise ValueError('JSON must be an object')
        if 'durations' not in raw or 'is_primary' not in raw:
            raise ValueError('JSON is missing required fields: durations, is_primary')
        raw_durations = raw['durations']
        raw_is_primary = raw['is_primary']
        if not isinstance(raw_durations, list):
            raise ValueError('durations must be a list')
        if not isinstance(raw_is_primary, bool):
            raise ValueError('is_primary must be a bool')
        raw_total: object = raw.get('total_duration')
        if raw_total is None:
            total_duration = math.fsum(float(d) for d in raw_durations)
        else:
            total_duration = float(raw_total)  # type: ignore[arg-type]
        return cls(
            scenario=None,
            durations=tuple(float(d) for d in raw_durations),
            total_duration=total_duration,
            is_primary=raw_is_primary,
        )
