# microbenchmark

A minimal Python library for writing and running benchmarks.

`microbenchmark` gives you simple building blocks — `Scenario`, `ScenarioGroup`, and `BenchmarkResult` — that you can embed directly into your project or call from CI. There is no CLI tool to install and no configuration to manage. You write a Python file, call `.run()` or `.cli()`, and you're done.

**Key features:**

- A `Scenario` wraps any callable with a fixed argument list and runs it `n` times, collecting per-run timings.
- A `ScenarioGroup` lets you combine scenarios and run them together.
- `BenchmarkResult` holds every individual duration and gives you mean, best, worst, and percentile views.
- Results can be serialised to and restored from JSON.
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

print(result.mean)
#> 0.000012  (example value, actual result will vary)
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
- `args` — a list of positional arguments to pass on each call. `None` (the default) means the function is called with no arguments. The list is copied on construction, so mutating it afterwards has no effect.
- `name` — a short label for this scenario (required).
- `doc` — an optional longer description.
- `number` — how many times to call `function` per run. Must be at least `1`.
- `timer` — a callable that returns the current time as a `float`. Defaults to `time.perf_counter`. Useful for injecting a controlled clock in tests.

```python
scenario = Scenario(
    sorted,
    args=[[3, 1, 2]],
    name='sort_three_items',
    doc='Sort a list of three integers.',
    number=10000,
)
```

### `run(warmup=0)`

Runs the benchmark and returns a `BenchmarkResult`.

The optional `warmup` argument specifies how many calls to make before timing begins. Warm-up calls execute the function and consume timer ticks, but their timings are not included in the result.

```python
result = scenario.run(warmup=100)
print(len(result.durations))
#> 10000
```

### `cli()`

Turns the scenario into a small command-line programme. Call `scenario.cli()` as the entry point of a script and it will parse `sys.argv`, run the benchmark, and print the result.

Supported arguments:

- `--number N` — override the scenario's `number` for this run.
- `--max-mean THRESHOLD` — exit with code `1` if the mean time (in seconds) exceeds `THRESHOLD`. Useful in CI.

```python
# benchmark.py
from microbenchmark import Scenario

def build_list():
    return list(range(1000))

scenario = Scenario(build_list, name='build_list', number=500)

if __name__ == '__main__':
    scenario.cli()
```

```
$ python benchmark.py --number 1000
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
```

```
$ python benchmark.py --max-mean 0.001
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
```

```
$ python benchmark.py --max-mean 0.000001
benchmark: build_list
mean:  0.000012s
best:  0.000010s
worst: 0.000018s
$ echo $?
#> 1
```

---

## ScenarioGroup

A `ScenarioGroup` holds a flat collection of scenarios and lets you run them together.

### Creating a group

There are four ways to create a group.

**Direct construction** — pass any number of scenarios to the constructor:

```python
from microbenchmark import Scenario, ScenarioGroup

s1 = Scenario(lambda: None, name='s1')
s2 = Scenario(lambda: None, name='s2')

group = ScenarioGroup(s1, s2)
```

**The `+` operator between scenarios** — adding two or more `Scenario` objects produces a `ScenarioGroup`:

```python
group = s1 + s2
```

**Adding a scenario to a group** — the result is always a flat group:

```python
s3 = Scenario(lambda: None, name='s3')
group = s1 + s2 + s3
print(type(group).__name__)
#> ScenarioGroup
```

**Adding two groups together** — the result is a single flat group containing the scenarios from both:

```python
g1 = ScenarioGroup(s1)
g2 = ScenarioGroup(s2, s3)
combined = g1 + g2
print(len(combined.run()))
#> 3
```

### `run(warmup=0)`

Runs every scenario in order and returns a list of `BenchmarkResult` objects. The order in the list matches the order the scenarios were added.

```python
results = group.run(warmup=50)
for result in results:
    print(result.scenario.name, result.mean)
#> s1 ...
#> s2 ...
#> s3 ...
```

### `cli()`

Runs all scenarios and prints their results separated by dividers.

Supported arguments:

- `--number N` — passed to every scenario.
- `--max-mean THRESHOLD` — exits with code `1` if any scenario's mean exceeds the threshold.

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

- `scenario` — the `Scenario` that produced this result, or `None` if the result was restored from JSON.
- `durations` — a tuple of per-call timings in seconds, one entry per call.
- `mean` — arithmetic mean of `durations`, computed with `math.fsum` to minimise floating-point error.
- `best` — the shortest individual timing.
- `worst` — the longest individual timing.
- `is_primary` — `True` for results returned directly by `run()`, `False` for results derived via `percentile()`.

```python
result = Scenario(lambda: None, name='noop', number=100).run()
print(len(result.durations))
#> 100
print(result.is_primary)
#> True
```

### `percentile(p)`

Returns a new `BenchmarkResult` containing only the fastest `ceil(len(durations) * p / 100)` timings. The returned result has `is_primary=False`.

```python
trimmed = result.percentile(95)
print(trimmed.is_primary)
#> False
print(len(trimmed.durations) <= len(result.durations))
#> True
```

`p` must be in the range `(0, 100]`. Passing `0` or a value above `100` raises `ValueError`.

### `p95` and `p99`

Convenient cached properties that return `percentile(95)` and `percentile(99)` respectively. The value is computed once and cached for the lifetime of the result object.

```python
print(result.p95.mean <= result.mean)
#> True
```

### `to_json()` and `from_json()`

`to_json()` serialises the result to a JSON string. It stores all individual `durations`, `is_primary`, and the scenario's `name`, `doc`, and `number`.

`from_json()` restores a `BenchmarkResult` from a JSON string produced by `to_json()`. Because the original callable cannot be serialised, the restored result has `scenario=None`.

```python
json_str = result.to_json()
restored = BenchmarkResult.from_json(json_str)

print(restored.scenario)
#> None
print(restored.mean == result.mean)
#> True
print(restored.durations == result.durations)
#> True
```

---

## Comparison with alternatives

| Feature | `microbenchmark` | `timeit` (stdlib) | `pytest-benchmark` |
|---|---|---|---|
| Per-call timings | yes | no | yes |
| Percentile views | yes | no | yes |
| JSON serialisation | yes | no | no |
| CI integration (`--max-mean`) | yes | no | via plugins |
| `+` operator for grouping | yes | no | no |
| External dependencies | none | none | several |
| Embeddable in your own code | yes | yes | test suite only |

`timeit` from the standard library is great for interactive exploration but gives you only a single aggregate number. `pytest-benchmark` is powerful but is tightly coupled to the `pytest` runner and brings its own dependencies. `microbenchmark` occupies the space between: richer than `timeit`, lighter than `pytest-benchmark`, and not tied to any test framework.
