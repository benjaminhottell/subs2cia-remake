import typing as ty

import os

from subs2cia.usage_error import UsageError


class OutputsExistError(UsageError):

    def __init__(
        self,
        msg: str,
        existing_paths: ty.Collection[str],
    ):
        super().__init__(msg)
        self.existing_paths = existing_paths


def check_overwritten_outputs(
    output_paths: ty.Iterable[str],
) -> None:
    '''
    Checks if given output paths exist.

    If none of the given paths exist, does nothing.

    If one or more of the given paths already exist, raises an OutputsExistError
    '''

    existing_paths: set[str] = set()

    for file_path in output_paths:
        if file_path not in existing_paths and os.path.exists(file_path):
            existing_paths.add(file_path)

    if len(existing_paths) == 0:
        return

    msg_parts: list[str] = list()

    if len(existing_paths) == 1:
        msg_parts.append('Output path already exists: ')
        msg_parts.append(next(iter(existing_paths)))
        msg_parts.append('\n')

    else:
        msg_parts.append('Multiple output paths already exist:\n')
        for existing_path in existing_paths:
            msg_parts.append(existing_path)
            msg_parts.append('\n')

    msg_parts.append('Pass --overwrite (or -w) to ignore existing outputs.')

    raise OutputsExistError(
        ''.join(msg_parts),
        existing_paths=existing_paths,
    )

