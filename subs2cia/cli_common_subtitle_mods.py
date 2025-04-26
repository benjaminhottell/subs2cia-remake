import typing as ty

import argparse

from subs2cia import (
    subtitles,
)


# This module contains common utilities for CLIs that need to modify subtitles based on user arguments.


def add_subtitle_modification_args(
    parser: argparse.ArgumentParser
) -> None:
    '''
    Adds the following arguments to your argument parser:

    - `subs_keep_blank`
    - `subs_remove_containing`
    - `subs_keep_containing`

    They are intended for use with the function `modify_subtitles_with_user_args`.
    '''

    parser.add_argument(
        '--keep-blank-subs', '--keep-blank-subtitles',
        dest='subs_keep_blank',
        help=(
            'Do not automatically remove subtitles with blank text. '
            '(Blank refers to text that is either empty or consists entirely of whitespace characters)'
        ),
        action='store_true',
        default=False,
    )

    parser.add_argument(
        '--remove-subs-containing', '--remove-subtitles-containing',
        dest='subs_remove_containing',
        help=(
            'Remove subtitles containing the given string. '
            'The comparison is case sensitive. '
            'You may specify this command multiple times.'
        ),
        action='append',
    )

    parser.add_argument(
        '--keep-subs-containing', '--keep-subtitles-containing',
        dest='subs_keep_containing',
        help=(
            'Keep only subtitles containing the given string. '
            'The comparison is case sensitive. '
            'You may specify this command multiple times.'
        ),
        action='append',
    )


def modify_subtitles(
    subs: subtitles.Subtitles,
    keep_blank: bool = False,
    remove_containing: ty.Iterable[str]|None = None,
    keep_containing: ty.Iterable[str]|None = None,
) -> None:
    '''
    Perform common operations on a given Subtitles object. The object is modified in-place.

    If `keep_blank` is False, subtitles that are empty or solely whitespace will be removed.
    '''

    if not keep_blank:
        subs.filter_events(lambda e: len(e.plain_text.strip()) != 0)

    if remove_containing is not None:
        for x in remove_containing:
            subs.filter_events(lambda e: x not in e.plain_text)

    if keep_containing is not None:
        for x in keep_containing:
            subs.filter_events(lambda e: x in e.plain_text)


def modify_subtitles_with_user_args(
    subs: subtitles.Subtitles,
    args: argparse.Namespace,
) -> None:
    return modify_subtitles(
        subs,
        keep_blank=args.subs_keep_blank,
        remove_containing=args.subs_remove_containing,
        keep_containing=args.subs_keep_containing,
    )

