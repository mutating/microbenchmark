from __future__ import annotations

import shutil
from collections.abc import Sequence

_BLOCKS = ' ▁▂▃▄▅▆▇█'


def _format_duration(t: float) -> str:
    """Format *t* seconds into a compact human-readable string."""
    if t >= 1.0:
        return f'{t:.3f}s'
    if t >= 1e-3:
        return f'{t * 1e3:.2f}ms'
    if t >= 1e-6:
        return f'{t * 1e6:.2f}\u03bcs'
    return f'{t * 1e9:.2f}ns'


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


def histogram_bounds(durations: Sequence[float]) -> tuple[float, float]:
    """Return ``(lo, hi)`` bounds for a histogram: minimum and p99 value.

    The p99 clip prevents extreme outliers from compressing the bulk of the
    distribution into the leftmost column.

    Args:
        durations: Sequence of per-call timings in seconds.

    Raises:
        ValueError: If *durations* is empty.
    """
    if not durations:
        raise ValueError('durations must not be empty')
    sorted_durs = sorted(durations)
    lo = sorted_durs[0]
    p99_idx = min(len(sorted_durs) - 1, int(len(sorted_durs) * 0.99))
    return lo, sorted_durs[p99_idx]


def draw_histogram_axis(lo: float, hi: float, width: int) -> str:
    """Return a single-line x-axis label for a histogram with bounds *lo*/*hi*.

    The minimum value is left-aligned; the p99 clip value is right-aligned.
    Both are formatted with auto-selected time units (ns / μs / ms / s).

    Args:
        lo: Minimum value displayed on the x-axis.
        hi: Maximum value (p99 clip point) displayed on the x-axis.
        width: Total width of the label in characters.
    """
    if width < 1:
        return ''
    left = _format_duration(lo)
    right = _format_duration(hi) + ' (p99)'
    if len(left) + 1 + len(right) > width:
        return left[:width]
    spaces = width - len(left) - len(right)
    return left + ' ' * spaces + right


def draw_histogram(durations: Sequence[float], width: int, height: int) -> list[str]:
    """Render an ASCII bar chart of *durations* as a ``height`` x ``width`` grid.

    The output is ``width`` characters wide and ``height`` rows tall.  Each
    cell uses one of the Unicode block characters ``' ▁▂▃▄▅▆▇█'`` so bar
    heights are resolved at 1/8-row precision, giving smooth transitions
    between adjacent buckets.  Returns an empty list when any dimension is
    zero/negative or when *durations* is empty.

    Internally the data is bucketed into at most 20 bins regardless of
    *width*.  Each bin is then rendered as ``width // n_buckets`` characters
    wide.  This prevents timer-quantisation artefacts from producing a single
    spike with stray isolated pixels.

    The x-axis upper bound is clipped to the p99 value via
    :func:`histogram_bounds`.  Values above the clip point are omitted.

    When all values are identical (``hi == lo``), the middle bin is drawn
    full-height and all others are left empty.

    Args:
        durations: Sequence of per-call timings in seconds.
        width: Total number of output characters per row.
        height: Number of rows in the chart.
    """
    if width < 1 or height < 1 or len(durations) == 0:
        return []

    lo, hi = histogram_bounds(durations)

    # Cap the number of data buckets at 20 so that adjacent quantised timer
    # values are merged into the same wider bar.
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
    bar_heights_float = [
        c / max_count * height if c > 0 else 0.0
        for c in counts
    ]

    rows: list[str] = []
    for row in range(height - 1, -1, -1):
        line_chars: list[str] = []
        for col in range(width):
            bh = bar_heights_float[col * n_buckets // width]
            if bh >= row + 1:
                line_chars.append('█')
            elif bh > row:
                frac = bh - row
                line_chars.append(_BLOCKS[max(1, min(8, round(frac * 8)))])
            else:
                line_chars.append(' ')
        rows.append(''.join(line_chars))
    return rows
