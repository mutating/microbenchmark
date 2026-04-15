from __future__ import annotations

import importlib
import sys
from pathlib import Path

from microbenchmark.scenario import Scenario
from microbenchmark.scenario_group import ScenarioGroup


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    if not args or ':' not in args[0]:
        sys.stderr.write(
            'microbenchmark: expected TARGET in the form module.path:attr\n'
            'Usage: microbenchmark module.path:attr [OPTIONS]\n',
        )
        sys.exit(3)

    spec, *rest = args
    colon_pos = spec.index(':')
    module_path = spec[:colon_pos]
    attr_name = spec[colon_pos + 1:]

    if not module_path or not attr_name:
        sys.stderr.write(
            f'microbenchmark: invalid target {spec!r} — '
            'expected non-empty module and attribute\n',
        )
        sys.exit(3)

    # Ensure CWD is importable so local (non-installed) modules can be found.
    cwd = str(Path.cwd())
    if cwd not in sys.path and '' not in sys.path:
        sys.path.insert(0, cwd)  # pragma: no cover

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        sys.stderr.write(f'microbenchmark: cannot import module {module_path!r}: {exc}\n')
        sys.exit(3)

    sentinel = object()
    target: object = getattr(module, attr_name, sentinel)
    if target is sentinel:
        sys.stderr.write(
            f'microbenchmark: module {module_path!r} has no attribute {attr_name!r}\n',
        )
        sys.exit(3)

    if not isinstance(target, (Scenario, ScenarioGroup)):
        sys.stderr.write(
            f'microbenchmark: {module_path}:{attr_name} is a '
            f'{type(target).__name__!r}, expected Scenario or ScenarioGroup\n',
        )
        sys.exit(3)

    target.cli(argv=rest)


if __name__ == '__main__':
    main()
