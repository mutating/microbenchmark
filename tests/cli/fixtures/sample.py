from __future__ import annotations

from microbenchmark import Scenario, ScenarioGroup


class _FakeTimer:
    def __init__(self) -> None:
        self._tick: float = 0.0

    def __call__(self) -> float:
        self._tick += 0.001
        return self._tick


scenario = Scenario(lambda: None, name='sample', number=3, timer=_FakeTimer())
group = ScenarioGroup(scenario, scenario)

not_a_scenario: int = 42
