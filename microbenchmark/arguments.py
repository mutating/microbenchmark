from __future__ import annotations

from printo import describe_data_object


class arguments:  # noqa: N801
    """Captures positional and keyword arguments for a benchmarked function.

    Create an instance by calling it like a function:

        args = arguments(3, 1, 2)
        args_with_kw = arguments(3, 1, 2, key=str)
    """

    __slots__ = ('args', 'kwargs')

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.args: tuple[object, ...] = args
        self.kwargs: dict[str, object] = dict(kwargs)

    def __repr__(self) -> str:
        return describe_data_object('arguments', self.args, self.kwargs)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, arguments):
            return NotImplemented
        return self.args == other.args and self.kwargs == other.kwargs

    def __hash__(self) -> int:
        return hash((self.args, tuple(sorted(self.kwargs.items()))))
