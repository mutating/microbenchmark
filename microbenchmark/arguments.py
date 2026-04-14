from __future__ import annotations

from printo import describe_data_object
from sigmatch import PossibleCallMatcher
from sigmatch.errors import SignatureNotFoundError, UnsupportedSignatureError


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

    def match(self, function: object) -> bool:
        """Check whether *function* can be called with these arguments.

        Returns ``True`` if the call is compatible with the function's
        signature, ``False`` if not.

        **Limitation:** if Python cannot introspect the signature of
        *function* (e.g. built-in / C-extension functions such as ``len``),
        the check is silently skipped and ``True`` is returned.  The function
        will be validated at runtime when the benchmark actually runs.
        """
        from sigmatch import SignatureMismatchError  # noqa: PLC0415
        shape = ('.',) * len(self.args) + tuple(self.kwargs)
        matcher: PossibleCallMatcher = PossibleCallMatcher(*shape)
        try:
            matcher.match(function, raise_exception=True)  # type: ignore[arg-type]
            return True
        except SignatureMismatchError:
            return False
        except (SignatureNotFoundError, UnsupportedSignatureError):
            return True
