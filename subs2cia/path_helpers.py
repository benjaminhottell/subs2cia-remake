import typing

import os


def swap_ext(
    file_path: str|os.PathLike,
    new_ext: str,
) -> str:
    basename, _ = os.path.splitext(file_path)
    return basename + new_ext


def get_ext(
    file_path: str|os.PathLike,
) -> str:
    _, ext = os.path.splitext(file_path)
    return ext


def avoid_leading_dash(file_path: str) -> str:
    if file_path.startswith('-'):
        return os.path.abspath(file_path)
    return file_path

