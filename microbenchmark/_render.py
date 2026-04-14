from __future__ import annotations

import shutil
from collections.abc import Sequence


def terminal_width() -> int:
    """Return the current terminal width, clamped to a minimum of 20."""
    cols = shutil.get_terminal_size((80, 24)).columns
    return max(cols, 20)


def draw_box(lines: list[str], width: int) -> list[str]:
    """Draw a Unicode border box around *lines*.

    Each output line is exactly *width* characters wide.  Content lines are
    padded with spaces or truncated to ``width - 4`` characters (2 chars for
    the border + space on each side).

    Box drawing uses ASCII + box-drawing characters (``╭╮╰╯│─``).  Width is
    measured by ``len()``, which counts every character as 1 column.  Emoji or
    CJK characters may cause visual misalignment.

    Args:
        lines: Content lines to render inside the box.
        width: Total width of each output line, including borders.
    """
    inner_width = width - 4  # 2 for │ and 1 space on each side
    top = '╭' + '─' * (width - 2) + '╮'
    bottom = '╰' + '─' * (width - 2) + '╯'
    result = [top]
    for line in lines:
        if len(line) > inner_width:
            content = line[:inner_width]
        else:
            content = line.ljust(inner_width)
        result.append('│ ' + content + ' │')
    result.append(bottom)
    return result


def draw_nested(
    inner_blocks: list[list[str]],
    extras: list[str],
    width: int,
) -> list[str]:
    """Draw an outer border box wrapping pre-rendered *inner_blocks*.

    Each inner block is already a list of strings (e.g. from :func:`draw_box`).
    They are placed inside the outer border with 1-space padding on each side.
    *extras* are additional plain-text lines rendered after the inner blocks,
    also padded.

    Args:
        inner_blocks: List of already-rendered blocks (each a list of strings).
        extras: Extra plain-text lines appended after the inner blocks.
        width: Total width of the outer box.
    """
    inner_width = width - 4  # space for │ + space on each side

    def pad_inner_line(line: str) -> str:
        if len(line) > inner_width:
            content = line[:inner_width]
        else:
            content = line.ljust(inner_width)
        return '│ ' + content + ' │'

    top = '╭' + '─' * (width - 2) + '╮'
    bottom = '╰' + '─' * (width - 2) + '╯'
    result = [top]
    for block in inner_blocks:
        for line in block:
            result.append(pad_inner_line(line))
    for line in extras:
        result.append(pad_inner_line(line))
    result.append(bottom)
    return result


def draw_histogram(durations: Sequence[float], width: int, height: int) -> list[str]:
    """Render an ASCII bar chart of *durations* as a ``height`` x ``width`` grid.

    The output is ``width`` characters wide and ``height`` rows tall.  Filled
    cells use ``'█'``; empty cells use ``' '``.  Returns an empty list when any
    dimension is zero/negative or when *durations* is empty.

    Internally the data is bucketed into at most 20 bins regardless of
    *width*.  Each bin is then rendered as ``width // n_buckets`` characters
    wide.  This prevents timer-quantisation artefacts (where most measurements
    snap to a handful of discrete nanosecond values) from producing a single
    column spike with stray isolated pixels elsewhere.

    The x-axis upper bound is clipped to the p99 value to prevent extreme
    outliers from compressing the bulk of the distribution.  Values above the
    p99 clip point are omitted from buckets.

    When all values are identical (``hi == lo``), the middle bin is drawn
    full-height and all others are left empty.

    Args:
        durations: Sequence of per-call timings in seconds.
        width: Total number of output characters per row.
        height: Number of rows in the chart.
    """
    if width < 1 or height < 1 or len(durations) == 0:
        return []

    sorted_durs = sorted(durations)
    lo = sorted_durs[0]
    p99_idx = min(len(sorted_durs) - 1, int(len(sorted_durs) * 0.99))
    hi = sorted_durs[p99_idx]

    # Cap the number of data buckets at 20 so that each bucket spans a
    # visible fraction of the output width and adjacent quantised values are
    # merged into the same bar.
    n_buckets = min(width, 20)
    counts = [0] * n_buckets

    if hi == lo:
        counts[n_buckets // 2] = 1
    else:
        span = hi - lo
        for d in durations:
            if d > hi:
                continue
            idx = min(n_buckets - 1, int((d - lo) / span * n_buckets))
            counts[idx] += 1

    max_count = max(counts)
    bar_heights = [
        round(c / max_count * height) if c > 0 else 0
        for c in counts
    ]

    rows: list[str] = []
    for row in range(height - 1, -1, -1):
        line = ''.join(
            '█' if bar_heights[col * n_buckets // width] > row else ' '
            for col in range(width)
        )
        rows.append(line)
    return rows
