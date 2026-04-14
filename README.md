# microbenchmark

A minimal Python library for writing and running benchmarks.

`microbenchmark` gives you simple building blocks — `Scenario`, `ScenarioGroup`, and `BenchmarkResult` — that you can embed directly into your project or call from CI. No separate CLI package to install; `.cli()` is built in. You write a Python file, call `.run()` or `.cli()`, and you are done.

**Key features:**

- A `Scenario` wraps any callable with an optional argument list and runs it `n` times, collecting per-run timings.
- The `arguments()` helper captures both positional and keyword arguments for the benchmarked function.
- A `ScenarioGroup` lets you combine scenarios and run them together with a single call.
- `BenchmarkResult` holds every individual duration and gives you mean, median, best, worst, and percentile views.
- Results can be serialized to and restored from JSON.
- One dependency: `printo` (from the [mutating](https://github.com/mutating) organization), used for argument and function display in CLI output.

---

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [arguments](#arguments)
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

scenario = Scenario(build_list, number=500)  # name auto-derived as 'build_list'
result = scenario.run()

print(len(result.durations))
#> 500
print(result.mean)   # example — actual value depends on your hardware
#> 0.000012
print(result.median)
#> 0.000011
print(result.best)
#> 0.000010
print(result.worst)
#> 0.000018
```

---

## arguments

The `arguments` class (lowercase by design) captures positional and keyword arguments for the benchmarked function. Import it directly:

```python
from microbenchmark import arguments
```

Or use the short alias `a` — handy when writing compact benchmark scripts:

```python
from microbenchmark import a
```

Both `arguments` and `a` refer to the same class. Create an instance by calling it like a function:

```python
from microbenchmark import arguments

args = arguments(3, 1, 2)
print(args.args)
#> (3, 1, 2)
print(args.kwargs)
#> {}

args_with_kw = arguments(3, 1, 2, key=str)
print(args_with_kw.args)
#> (3, 1, 2)
print(args_with_kw.kwargs)
#> {'key': <class 'str'>}
```

The `a` alias is particularly useful when combining many scenarios inline:

```python
from microbenchmark import Scenario, a

scenario = Scenario(sorted, a([3, 1, 2]), name='sort')
result = scenario.run()
```

`arguments` has a readable `repr`:

```python
from microbenchmark import arguments

print(arguments(1, 2, key='value'))
#> arguments(1, 2, key='value')

print(arguments())
#> arguments()
```

### `match(function)`

Checks whether `function` can be called with the arguments captured in this `arguments` instance. Returns `True` if the call is compatible with the function's signature, `False` otherwise.

```python
from microbenchmark import arguments

args = arguments(1, 2)
print(args.match(lambda a, b: None))
#> True

print(args.match(lambda a: None))
#> False
```

Works with keyword arguments too:

```python
from microbenchmark import arguments

args = arguments(key='value')
print(args.match(lambda *, key: None))
#> True

print(args.match(lambda: None))
#> False
```

**Note on unintrospectable callables:** For some exotic C-extension functions whose signatures Python cannot inspect at all, the check is silently skipped and `True` is returned. The function will be validated at runtime when the benchmark actually runs. Most common callables — including standard built-in functions like `len` — have introspectable signatures and are checked normally.

---

## Scenario

A `Scenario` describes a single benchmark: the function to call, what arguments to pass, and how many times to run it.

### Constructor

```python
Scenario(
    function,
    arguments=None,
    *,
    name=None,
    doc='',
    number=1000,
    timer=time.perf_counter,
)
```

- `function` — the callable to benchmark.
- `arguments` — an `arguments` instance that holds the positional and keyword arguments passed to `function` on every call. `None` (the default) means the function is called with no arguments. Supports both positional and keyword arguments.
- `name` — a short label for this scenario. If omitted, the name is derived automatically from `function.__name__`. For lambdas, the derived name will be `'<lambda>'`.
- `doc` — an optional longer description.
- `number` — how many times to call `function` per run. Must be at least `1`; passing `0` or a negative value raises `ValueError`.
- `timer` — a zero-argument callable that returns the current time as a `float`. Defaults to `time.perf_counter`. Supply a custom clock to get deterministic measurements in tests:

**Signature validation:** The constructor automatically checks that `function` can be called with the provided `arguments`. If the signatures are incompatible, a `sigmatch.SignatureMismatchError` is raised immediately — before the benchmark runs:

```python
from microbenchmark import Scenario, arguments
from sigmatch import SignatureMismatchError

try:
    Scenario(lambda a: None, arguments(1, 2))
except SignatureMismatchError as e:
    print('caught:', e)
#> caught: Scenario arguments arguments(1, 2) are incompatible with the signature of <lambda>
```

For the rare callables whose signatures Python cannot introspect at all, the validation is silently skipped. See [`arguments.match()`](#matchfunction) for details.

```python
from microbenchmark import Scenario

tick = [0.0]
def fake_timer():
    tick[0] += 0.001
    return tick[0]

scenario = Scenario(lambda: None, name='noop', number=5, timer=fake_timer)
result = scenario.run()
print(result.mean)
#> 0.001
```

```python
from microbenchmark import Scenario, arguments

scenario = Scenario(
    sorted,
    arguments([3, 1, 2]),
    name='sort_three_items',
    doc='Sort a list of three integers.',
    number=10000,
)
print(scenario.name)
#> sort_three_items
print(scenario.doc)
#> Sort a list of three integers.
print(scenario.number)
#> 10000
```

When `name` is omitted, it is derived from the function:

```python
from microbenchmark import Scenario

def my_function():
    return list(range(100))

scenario = Scenario(my_function)
print(scenario.name)
#> my_function
```

For keyword arguments, pass them through `arguments`:

```python
from microbenchmark import Scenario, arguments

scenario = Scenario(
    sorted,
    arguments([3, 1, 2], key=lambda x: -x),
    name='sort_descending',
)
result = scenario.run()
```

For functions that take multiple positional arguments:

```python
from microbenchmark import Scenario, arguments

scenario = Scenario(pow, arguments(2, 10), name='power')
result = scenario.run()
print(result.mean)
#> 0.000001  # example — very fast operation
```

### `run(warmup=0)`

Runs the benchmark and returns a `BenchmarkResult`.

The optional `warmup` argument specifies how many calls to make before timing begins. Warm-up calls execute the function but are not timed and their results are discarded. Warmup is useful when your function has one-time initialization costs — cache warming, lazy imports, JIT compilation — that you do not want to measure. Without warmup, the first few runs may be outliers that skew the mean.

```python
from microbenchmark import Scenario

scenario = Scenario(lambda: list(range(100)), name='build', number=1000)
result = scenario.run(warmup=100)
print(len(result.durations))
#> 1000
```

### `cli(argv=None)`

Turns the scenario into a small command-line program. Call `scenario.cli()` as the entry point of a script and it will parse `sys.argv`, run the benchmark, and print the result to stdout.

Pass `argv` as a list of strings to override `sys.argv` — useful when calling `.cli()` programmatically or from the `microbenchmark` command-line tool.

Supported arguments:

- `--number N` — override the scenario's `number` for this run.
- `--max-mean THRESHOLD` — exit with code `1` if the mean time (in seconds) exceeds `THRESHOLD`. Useful in CI.
- `--histogram` — append an ASCII histogram of per-call timings inside the border. The histogram is 8 rows tall and fills the available inner width.
- `--help` — print usage information and exit.

Output format (each scenario is wrapped in a Unicode border):

```
╭──────────────────────────────────╮
│ benchmark: <name>                │
│ call:      <function>(<args>)    │
│ doc:       <doc>                 │
│ runs:      <number>              │
│ mean:      <mean>s               │
│ median:    <median>s             │
│ best:      <best>s               │
│ worst:     <worst>s              │
│ p95 mean:  <p95.mean>s           │
│ p99 mean:  <p99.mean>s           │
│ total:     <total_duration>s     │
│ fn total:  <functions_duration>s │
╰──────────────────────────────────╯
```

The `doc:` line is omitted when `doc` is empty. The `call:` line shows the function name and its arguments. Times are in seconds. Labels are padded to the same width for alignment. `total:` is the wall-clock time of the whole benchmark loop; `fn total:` is the sum of per-call timings (`math.fsum(durations)`). The border width adapts to the terminal width (minimum 20 columns).

If `--max-mean` is supplied and the actual mean exceeds the threshold, the output is printed in full and then a failure line is added before the process exits with code `1`:

```
FAIL: mean <actual>s exceeds --max-mean <threshold>s
```

```python
# benchmark.py
from microbenchmark import Scenario

def build_list():
    return list(range(1000))

scenario = Scenario(build_list, doc='Build a list of 1000 integers.', number=500)

if __name__ == '__main__':
    scenario.cli()
```

```
$ python benchmark.py
╭─────────────────────────────────────────────────╮
│ benchmark: build_list                           │
│ call:      build_list()                         │
│ doc:       Build a list of 1000 integers.       │
│ runs:      500                                  │
│ mean:      0.000012s                            │
│ median:    0.000011s                            │
│ best:      0.000010s                            │
│ worst:     0.000018s                            │
│ p95 mean:  0.000011s                            │
│ p99 mean:  0.000012s                            │
│ total:     0.006100s                            │
│ fn total:  0.006000s                            │
╰─────────────────────────────────────────────────╯
```

Use `--histogram` to append an ASCII distribution chart below the metrics:

```
$ python benchmark.py --histogram
╭─────────────────────────────────────────────────╮
│ benchmark: build_list                           │
│ call:      build_list()                         │
│ doc:       Build a list of 1000 integers.       │
│ runs:      500                                  │
│ mean:      0.000012s                            │
│ median:    0.000011s                            │
│ best:      0.000010s                            │
│ worst:     0.000018s                            │
│ p95 mean:  0.000011s                            │
│ p99 mean:  0.000012s                            │
│ total:     0.006100s                            │
│ fn total:  0.006000s                            │
│                                                 │
│ █████████████████████████████████████████████   │
│ █████████████████████████████████████████████   │
│ ████████████████████████████████████████████    │
│ ████████████████████████████   ████████████     │
│ ████████████████████ ██████    █████████        │
│ ██████████████ ████   ████      ██████          │
│ ████████ ████   ██     ██        ████           │
│ ████      ██     █               ██             │
╰─────────────────────────────────────────────────╯
```

Use `--number` to override the run count for this invocation. Use `--max-mean` to set a CI threshold:

```
$ python benchmark.py --max-mean 0.000001
╭─────────────────────────────────────────────────╮
│ benchmark: build_list                           │
│ call:      build_list()                         │
│ doc:       Build a list of 1000 integers.       │
│ runs:      500                                  │
│ mean:      0.000012s                            │
│ median:    0.000011s                            │
│ best:      0.000010s                            │
│ worst:     0.000018s                            │
│ p95 mean:  0.000011s                            │
│ p99 mean:  0.000012s                            │
│ total:     0.006100s                            │
│ fn total:  0.006000s                            │
╰─────────────────────────────────────────────────╯
FAIL: mean 0.000012s exceeds --max-mean 0.000001s
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

### `cli(argv=None)`

Runs all scenarios and prints their results to stdout. Each scenario block is displayed in a nested Unicode border. All inner blocks are wrapped together in a single outer border.

Supported arguments:

- `--number N` — passed to every scenario.
- `--max-mean THRESHOLD` — exits with code `1` if any scenario's mean exceeds the threshold.
- `--histogram` — append an ASCII histogram of per-call timings inside each inner border. The histogram is 8 rows tall and fills the available inner width.
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
╭────────────────────────────────────────────────────╮
│ ╭──────────────────────────────────────────────╮  │
│ │ benchmark: range_100                         │  │
│ │ call:      range_100()                       │  │
│ │ runs:      1000                              │  │
│ │ mean:      0.000003s                         │  │
│ │ median:    0.000003s                         │  │
│ │ best:      0.000002s                         │  │
│ │ worst:     0.000005s                         │  │
│ │ p95 mean:  0.000003s                         │  │
│ │ p99 mean:  0.000003s                         │  │
│ │ total:     0.003200s                         │  │
│ │ fn total:  0.003000s                         │  │
│ ╰──────────────────────────────────────────────╯  │
│ ╭──────────────────────────────────────────────╮  │
│ │ benchmark: range_1000                        │  │
│ │ call:      range_1000()                      │  │
│ │ runs:      1000                              │  │
│ │ mean:      0.000012s                         │  │
│ │ median:    0.000011s                         │  │
│ │ best:      0.000010s                         │  │
│ │ worst:     0.000018s                         │  │
│ │ p95 mean:  0.000011s                         │  │
│ │ p99 mean:  0.000012s                         │  │
│ │ total:     0.012500s                         │  │
│ │ fn total:  0.012000s                         │  │
│ ╰──────────────────────────────────────────────╯  │
╰────────────────────────────────────────────────────╯
```

---

## BenchmarkResult

`BenchmarkResult` is a dataclass that holds the outcome of a single benchmark run.

### Fields

- `scenario: Scenario | None` — the `Scenario` that produced this result, or `None` if the result was restored from JSON.
- `durations: tuple[float, ...]` — per-call timings in seconds, one entry per call, in the order they were measured.
- `total_duration: float` — wall-clock time of the entire benchmark loop in seconds, measured from just before the first call to just after the last call. Warmup time is not included. Must be provided at construction time.
- `mean: float` — arithmetic mean of `durations`, computed with `math.fsum` to minimize floating-point error. Computed automatically from `durations`.
- `functions_duration: float` — sum of all per-call timings (`math.fsum(durations)`). Computed automatically from `durations`.
- `median: float` — median of `durations`. Computed lazily on first access and cached for the lifetime of the result object.
- `best: float` — the shortest individual timing. Computed automatically.
- `worst: float` — the longest individual timing. Computed automatically.
- `is_primary: bool` — `True` for results returned directly by `run()`, `False` for results derived via `percentile()`. Preserved during JSON round-trips.

The `mean`, `best`, `worst`, and `functions_duration` fields are read-only computed values (not accepted as constructor arguments). The `total_duration` field is an input: pass it to the constructor. The `median`, `p95`, and `p99` properties are cached lazily.

```python
from microbenchmark import Scenario

result = Scenario(lambda: None, name='noop', number=100).run()
print(len(result.durations))
#> 100
print(result.is_primary)
#> True
print(isinstance(result.median, float))
#> True
print(isinstance(result.total_duration, float))
#> True
print(isinstance(result.functions_duration, float))
#> True
```

### `percentile(p)`

Returns a new `BenchmarkResult` containing only the `ceil(len(durations) * p / 100)` fastest timings, sorted by duration ascending. The returned result has `is_primary=False`. `p` must be in the range `(0, 100]`; passing `0` or a value above `100` raises `ValueError`.

Percentiles help you focus on the typical case by trimming outliers. If your benchmark includes occasional GC pauses or scheduling jitter, the p95 or p99 view shows what most calls actually experience. `is_primary=False` marks results that are derived from raw data rather than measured directly; this distinction is preserved during JSON round-trips.

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

`to_json()` serializes the result to a JSON string. It stores `durations`, `is_primary`, `total_duration`, and the scenario's `name`, `doc`, and `number`. The `functions_duration` field is derived and not stored.

`from_json()` is a class method that restores a `BenchmarkResult` from a JSON string produced by `to_json()`. Because the original callable cannot be serialized, the restored result has `scenario=None`. The `mean`, `best`, `worst`, `median`, and `functions_duration` fields are recomputed from `durations` on restoration.

**Backward compatibility:** JSON produced by older versions of `microbenchmark` that do not include `total_duration` can still be loaded. When `total_duration` is absent, `from_json()` falls back to `math.fsum(durations)` (equivalent to `functions_duration`), meaning `total_duration` will equal `functions_duration` (overhead is treated as zero).

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
print(restored.median == result.median)
#> True
```

---

## CLI

The `microbenchmark` package installs a command-line tool of the same name. It lets you run any `Scenario` or `ScenarioGroup` object directly from the terminal without writing a wrapper script.

### Usage

```
microbenchmark TARGET [OPTIONS]
```

`TARGET` is the fully-qualified import path to a `Scenario` or `ScenarioGroup` object in your module, in the form `module.path:attribute`:

```
microbenchmark my_pkg.bench:suite
microbenchmark my_pkg.bench:single_scenario --number 500
microbenchmark my_pkg.bench:suite --max-mean 0.001
```

The module must be importable — either installed in the current environment or located in the current working directory. If the module is a local file (e.g. `bench.py`), run the command from the directory that contains it:

```
microbenchmark bench:suite
```

### Options

All options accepted by `Scenario.cli()` and `ScenarioGroup.cli()` are forwarded automatically:

- `--number N` — override the iteration count for this run.
- `--max-mean THRESHOLD` — exit with code `1` if any scenario's mean time (seconds) exceeds `THRESHOLD`.
- `--help` — print usage and exit.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | All benchmarks passed. |
| 1 | A benchmark exceeded `--max-mean`. |
| 3 | Invalid target specification or import error. |

### Example

Given a file `bench.py` in the current directory:

```python
from microbenchmark import Scenario, arguments

scenario = Scenario(sorted, arguments([3, 1, 2]), name='sort', number=1000)
```

Run it directly:

```
$ microbenchmark bench:scenario --number 500
```

---

## Comparison with alternatives

| Feature | `microbenchmark` | `timeit` (stdlib) | `pytest-benchmark` |
|---|---|---|---|
| Per-call timings | yes | via `repeat(number=1)` | yes |
| Percentile views | yes | no | yes |
| Median | yes | no | yes |
| JSON serialization | yes | no | yes |
| Inject custom timer | yes | yes | no |
| Warmup support | yes | no | yes (calibration) |
| CI integration (`--max-mean`) | yes | no | via configuration |
| Keyword arguments | yes | yes | yes |
| `+` operator for grouping | yes | no | no |
| External dependencies | one (`printo`) | none | several |
| Embeddable in your own code | yes | yes | pytest plugin required |

`timeit` from the standard library is great for interactive exploration, but it gives only a single aggregate number per call — you can get a list by using `repeat(number=1)`, though the interface is not designed around it. `pytest-benchmark` is powerful and well-integrated into the `pytest` ecosystem, but it is tightly coupled to the test runner and brings its own dependencies. `microbenchmark` sits between the two: richer than `timeit`, lighter and more portable than `pytest-benchmark`, and not tied to any test framework.
