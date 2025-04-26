import typing as ty
from types import TracebackType

import tempfile

T = ty.TypeVar('T')

EnteredType = ty.TypeVar(
    'EnteredType',
    covariant=True,
)


class LikeContextManager(ty.Protocol, ty.Generic[EnteredType]):
    '''Protocol for something that looks and acts like a context manager'''

    def __enter__(self) -> EnteredType:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException]|None,
        exc_val: BaseException|None,
        exc_tb: TracebackType|None,
    ) -> ty.Any:
        ...


class MultiContextManager:
    '''
    A context manager that supports managing zero or more 'child' context managers. Child context managers are closed when this 'parent' context manager is closed.

    To register a 'child' context manager, use the `accept` method.

    Example usage:

    ```py
    with MultiContextManager() as deferred:
        open_file = deferred.accept(open('/path/to/file', 'r'))
    ````
    '''

    def __init__(self):
        self._close_later: list[LikeContextManager[ty.Any]] = list()

    @ty.overload
    def accept(self, child: LikeContextManager[T]) -> T:
        ...

    @ty.overload
    def accept(self, child: tempfile.TemporaryDirectory[str]) -> str:
        ...

    def accept(self, child: ty.Any) -> ty.Any:
        '''
        Register a 'child' context manager. It will be closed when this 'parent' context manager is closed.
        '''
        ret = child.__enter__()
        self._close_later.append(child)
        return ret

    def __enter__(self) -> ty.Self:
        return self

    def __exit__(self, exc_type, exc_value, tb) -> None:

        del exc_type, exc_value, tb

        errors: list[Exception] = list()

        while len(self._close_later) > 0:

            x = self._close_later.pop()

            try:
                x.__exit__(None, None, None)
            except Exception as e:
                errors.append(e)

        if len(errors) > 0:

            msg_builder = list()

            msg_builder.append('At least one error occurred during cleanup:')

            for error in errors:
                msg_builder.append(str(error))

            raise ExceptionGroup(
                'MultiContextManager cleanup',
                errors,
            )

