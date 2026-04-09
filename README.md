# microbenchmark

A minimal Python library for writing and running benchmarks.

`microbenchmark` gives you simple building blocks — `Scenario`, `ScenarioGroup`, and `BenchmarkResult` — that you can embed directly into your project or call from CI. No separate CLI package to install; `.cli()` is built in. You write a Python file, call `.run()` or `.cli()`, and you are done.

**Key features:**

- A `Scenario` wraps any callable with a fixed argument list and runs it `n` times, collecting per-run timings.
- A `ScenarioGroup` lets you combine scenarios and run them together with a single call.
- `BenchmarkResult` holds every individual duration and gives you mean, best, worst, and percentile views.
- Results can be serialized to and restored from JSON.
- No external dependencies beyond the Python standard library.

---

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Scenario](#scenario)
- [ScenarioGroup](#scenariogroup)
- [BenchmarkResult](#benchmarkresult)
- [Comparison with alternatives](#comparison-with-alternatives)

---

## Installation

```
pip install microbenchmark
```

---

## Quick start

```python
from microbenchmark import Scenario

def build_list():
    return list(range(1000))

scenario = Scenario(build_list, name='build_list', number=500)
result = scenario.run()

print(len(result.durations))
#> 500
print(result.mean)   # example — actual value depends on your hardware
#> 0.000012
print(result.best)
#> 0.000010
print(result.worst)
#> 0.000018
```

---

## Scenario

A `Scenario` describes a single benchmark: the function to call, what arguments to pass, and how many times to run it.

### Constructor

```python
Scenario(
    function,
    args=None,
    *,
    name,
    doc='',
    number=1000,
    timer=time.perf_counter,
)
```

- `function` — the callable to benchmark.
- `args` — a list of positional arguments passed to `function` on every call as `function(*args)`. `None` (the default) and `[]` both mean the function is called with no arguments. The list is shallow-copied on construction, so appending to your original list afterward has no effect. Keyword arguments are not supported; wrap your callable in a `functools.partial` or a lambda if you need them.
- `name` — a short label for this scenario (required).
- `doc` — an optional longer description.
- `number` — how many times to call `function` per run. Must be at least `1`; passing `0` or a negative value raises `ValueError`.
- `timer` — a zero-argument callable that returns the current time as a `float`. Defaults to `time.perf_counter`. Supply a custom clock to get deterministic measurements in tests.

```python
import time
from microbenchmark import Scenario

scenario = Scenario(
    sorted,
    args=[[3, 1, 2]],
    name='sort_three_items',
    doc='Sort a list of three integers.',
    number=10000,
)
```

For keyword arguments, use `functools.partial`:

```python
from functools import partial
from microbenchmark import Scenario

scenario = Scenario(
    partial(sorted, key=lambda x: -x),
    args=[[3, 1, 2]],
    name='sort_descending',
)
```

For functions that take multiple positional arguments, list all of them in `args`:

```python
from microbenchmark import Scenario

scenario = Scenario(pow, args=[2, 10], name='power')
result = scenario.run()
print(result.mean)
#> 0.000000  # example — very fast operation
```

### `run(warmup=0)`

Runs the benchmark and returns a `BenchmarkResult`.

The optional `warmup` argument specifies how many calls to make before timing begins. Warm-up calls execute the function but are not timed and their results are discarded.

```python
from microbenchmark import Scenario

scenario = Scenario(lambda: list(range(100)), name='build', number=1000)
result = scenario.run(warmup=100)
print(len(result.durations))
#> 1000
```

### `cli()`

Turns the scenario into a small command-line program. Call `scenario.cli()` as the entry point of a script and it will parse `sys.argv`, run the benchmark, and print the result to stdout.

Supported arguments:

- `--number N` — override the scenario's `number` for this run.
- `--max-mean THRESHOLD` — exit with code `1` if the mean time (in seconds) exceeds `THRESHOLD`. Useful in CI.
- `--help` — print usage information and exit.

Output format:

```
benchmark: <name>
mean:  <mean>s
best:  <best>s
worst: <worst>s
```

Values are in seconds. The `mean`, `best`, and `worst` labels are padded to the same width. If `--max-mean` is supplied and the actual mean exceeds the threshold, the same output is printed but the process exits with code `1`.

```python
# benchmark.py
import time
from microbenchmark import Scenario

def build_list():
    return list(range(1000))

scenario = Scenario(build_list, name='build_list', number=500)

if __name__ == '__main__':
    scenario.cli()
```

```
$ python benchmark.py
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
```

```
$ python benchmark.py --number 100
benchmark: build_list
mean:  0.000013s
best:  0.000010s
worst: 0.000020s
```

```
$ python benchmark.py --max-mean 0.001
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
$ echo $?
0
```

```
$ python benchmark.py --max-mean 0.000001
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
$ echo $?
1
```

---

## ScenarioGroup

A `ScenarioGroup` holds a flat collection of scenarios and lets you run them together.

### Creating a group

There are four ways to create a group.

**Direct construction** — pass any number of scenarios to the constructor. Passing no scenarios creates an empty group:

```python
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')

group = ScenarioGroup(s1, s2)
empty = ScenarioGroup()
print(len(empty.run()))
#> 0
```

**The `+` operator between two scenarios** produces a `ScenarioGroup`:

```python
from microbenchmark import Scenario

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')
group = s1 + s2
print(type(group).__name__)
#> ScenarioGroup
```

**Adding a scenario to an existing group**, or vice versa — the result is always a new flat group with no nesting:

```python
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')
s3 = Scenario(lambda: None, name='s3')
group = ScenarioGroup(s1, s2)
extended = group + s3     # ScenarioGroup + Scenario
also_ok  = s3 + group     # Scenario + ScenarioGroup
print(len(extended.run()))
#> 3
```

**Adding two groups together** produces a single flat group:

```python
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')
s3 = Scenario(lambda: None, name='s3')
g1 = ScenarioGroup(s1)
g2 = ScenarioGroup(s2, s3)
combined = g1 + g2
print(len(combined.run()))
#> 3
```

### `run(warmup=0)`

Runs every scenario in order and returns a list of `BenchmarkResult` objects. The order of results matches the order the scenarios were added. The `warmup` argument is forwarded to each scenario individually.

```python
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')
group = ScenarioGroup(s1, s2)
results = group.run(warmup=50)
for result in results:
    print(result.scenario.name)
#> s1
#> s2
```

### `cli()`

Runs all scenarios and prints their results to stdout. Each scenario block follows the same format as `Scenario.cli()`, and blocks are separated by a `---` line. The separator appears only between blocks, not after the last one.

Supported arguments:

- `--number N` — passed to every scenario.
- `--max-mean THRESHOLD` — exits with code `1` if any scenario's mean exceeds the threshold.
- `--help` — print usage information and exit.

```python
# benchmarks.py
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: list(range(100)), name='range_100')
s2 = Scenario(lambda: list(range(1000)), name='range_1000')

group = s1 + s2

if __name__ == '__main__':
    group.cli()
```

```
$ python benchmarks.py
benchmark: range_100
mean:  0.000003s
best:  0.000002s
worst: 0.000005s
---
benchmark: range_1000
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
```

---

## BenchmarkResult

`BenchmarkResult` is a dataclass that holds the outcome of a single benchmark run.

### Fields

- `scenario: Scenario | None` — the `Scenario` that produced this result, or `None` if the result was restored from JSON.
- `durations: tuple[float, ...]` — per-call timings in seconds, one entry per call, in the order they were measured.
- `mean: float` — arithmetic mean of `durations`, computed with `math.fsum` to minimize floating-point error. Computed automatically from `durations`.
- `best: float` — the shortest individual timing. Computed automatically.
- `worst: float` — the longest individual timing. Computed automatically.
- `is_primary: bool` — `True` for results returned directly by `run()`, `False` for results derived via `percentile()`. Preserved during JSON round-trips.

The `mean`, `best`, and `worst` fields are read-only computed values; they are not accepted as constructor arguments.

```python
from microbenchmark import Scenario

result = Scenario(lambda: None, name='noop', number=100).run()
print(len(result.durations))
#> 100
print(result.is_primary)
#> True
```

### `percentile(p)`

Returns a new `BenchmarkResult` containing only the `ceil(len(durations) * p / 100)` fastest timings, sorted by duration ascending. The returned result has `is_primary=False`. `p` must be in the range `(0, 100]`; passing `0` or a value above `100` raises `ValueError`.

```python
from microbenchmark import Scenario

result = Scenario(lambda: None, name='noop', number=100).run()
trimmed = result.percentile(95)
print(trimmed.is_primary)
#> False
print(len(trimmed.durations))
#> 95
```

You can call `percentile()` on a derived result too:

```python
from microbenchmark import Scenario

result = Scenario(lambda: None, name='noop', number=100).run()
print(len(result.percentile(90).percentile(50).durations))
#> 45
```

### `p95` and `p99`

Convenient cached properties that return `percentile(95)` and `percentile(99)` respectively. The value is computed once and cached for the lifetime of the result object.

```python
from microbenchmark import Scenario

result = Scenario(lambda: None, name='noop', number=100).run()
print(len(result.p95.durations))
#> 95
print(result.p95.is_primary)
#> False
print(result.p95 is result.p95)   # cached — same object returned each time
#> True
```

### `to_json()` and `from_json()`

`to_json()` serializes the result to a JSON string. It stores `durations`, `is_primary`, and the scenario's `name`, `doc`, and `number`.

`from_json()` is a class method that restores a `BenchmarkResult` from a JSON string produced by `to_json()`. Because the original callable cannot be serialized, the restored result has `scenario=None`. The `mean`, `best`, and `worst` fields are recomputed from `durations` on restoration.

```python
from microbenchmark import Scenario, BenchmarkResult

result = Scenario(lambda: None, name='noop', number=100).run()

json_str = result.to_json()
restored = BenchmarkResult.from_json(json_str)

print(restored.scenario)
#> None
print(restored.mean == result.mean)
#> True
print(restored.durations == result.durations)
#> True
print(restored.is_primary == result.is_primary)
#> True
```

---

## Comparison with alternatives

| Feature | `microbenchmark` | `timeit` (stdlib) | `pytest-benchmark` |
|---|---|---|---|
| Per-call timings | yes | via `repeat(number=1)` | yes |
| Percentile views | yes | no | yes |
| JSON serialization | yes | no | yes |
| Inject custom timer | yes | yes | no |
| Warmup support | yes | no | yes (calibration) |
| CI integration (`--max-mean`) | yes | no | via configuration |
| `+` operator for grouping | yes | no | no |
| External dependencies | none | none | several |
| Embeddable in your own code | yes | yes | pytest plugin required |

`timeit` from the standard library is great for interactive exploration, but it gives only a single aggregate number per call — you can get a list by using `repeat(number=1)`, though the interface is not designed around it. `pytest-benchmark` is powerful and well-integrated into the `pytest` ecosystem, but it is tightly coupled to the test runner and brings its own dependencies. `microbenchmark` sits between the two: richer than `timeit`, lighter and more portable than `pytest-benchmark`, and not tied to any test framework.
