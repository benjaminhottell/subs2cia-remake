import typing as ty

import os

from subs2cia.subtitles_types import Subtitles, SubtitlesEvent
from subs2cia.time_ranges import TimeRanges
from subs2cia import subtitles_ass
from subs2cia import path_helpers


class UnsupportedSubtitlesFormatError(ValueError):
    pass


def _guess_format_from_extension(
    file_path: str|os.PathLike,
) -> str:
    ext = path_helpers.get_ext(file_path)

    if len(ext) == 0:
        return ''

    return ext[1:].lower()


def get_supported_formats() -> ty.Collection[str]:
    return {
        'ass',
    }


def is_supported_file(file_path: str|os.PathLike):
    format = _guess_format_from_extension(file_path)
    return format in get_supported_formats()


def parse(
    file: ty.IO[str],
    format: str,
) -> Subtitles:

    if format == 'ass':
        return subtitles_ass.parse(file)

    else:
        raise UnsupportedSubtitlesFormatError(
            f'Unsupported or invalid subtitles format: {format}'
        )


def parse_at_path(
    file_path: str|os.PathLike,
    encoding: str = 'utf-8',
) -> Subtitles:

    format = _guess_format_from_extension(file_path)

    with open(
        file_path,
        'r',
        encoding=encoding,
    ) as in_file:

        return parse(
            in_file,
            format=format,
        )


def retime(
    in_file: ty.IO[str],
    out_file: ty.IO[str],
    time_ranges: TimeRanges,
    format: str,
) -> None:

    if format == 'ass':
        return subtitles_ass.retime(in_file, out_file, time_ranges)

    else:
        raise UnsupportedSubtitlesFormatError(
            f'Unsupported or invalid subtitles format: {format}'
        )


__all__ = [
    'Subtitles',
    'SubtitlesEvent',
    'get_supported_formats',
    'is_supported_file',
    'parse',
    'parse_at_path',
    'retime',
]

