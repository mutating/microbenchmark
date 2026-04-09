from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from microbenchmark.scenario import Scenario


class _ScenarioMeta(TypedDict):
    name: str
    doc: str
    number: int


class _ResultJson(TypedDict):
    durations: list[float]
    is_primary: bool
    scenario: _ScenarioMeta | None


@dataclass
class BenchmarkResult:
    scenario: Scenario | None
    durations: tuple[float, ...]
    is_primary: bool = True

    mean: float = field(init=False)
    best: float = field(init=False)
    worst: float = field(init=False)

    def __post_init__(self) -> None:
        self.mean = math.fsum(self.durations) / len(self.durations)
        self.best = min(self.durations)
        self.worst = max(self.durations)

    def percentile(self, p: float) -> BenchmarkResult:
        if p <= 0 or p > 100:
            raise ValueError(f'percentile must be in (0, 100], got {p}')
        k = math.ceil(len(self.durations) * p / 100)
        trimmed = tuple(sorted(self.durations)[:k])
        return BenchmarkResult(
            scenario=self.scenario,
            durations=trimmed,
            is_primary=False,
        )

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
        return cls(
            scenario=None,
            durations=tuple(float(d) for d in raw_durations),
            is_primary=raw_is_primary,
        )
