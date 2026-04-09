from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from microbenchmark.scenario import Scenario


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
        scenario_data: dict[str, Any] | None
        if self.scenario is not None:
            scenario_data = {
                'name': self.scenario.name,
                'doc': self.scenario.doc,
                'number': self.scenario.number,
            }
        else:
            scenario_data = None
        return json.dumps({
            'durations': list(self.durations),
            'is_primary': self.is_primary,
            'scenario': scenario_data,
        })

    @classmethod
    def from_json(cls, data: str) -> BenchmarkResult:
        parsed = json.loads(data)
        if 'durations' not in parsed or 'is_primary' not in parsed:
            raise ValueError('JSON is missing required fields: durations, is_primary')
        return cls(
            scenario=None,
            durations=tuple(float(d) for d in parsed['durations']),
            is_primary=bool(parsed['is_primary']),
        )
