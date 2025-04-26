import typing as ty

import argparse

from subs2cia.time_ranges import TimeRanges
from subs2cia.usage_error import UsageError


def add_padding_args(
    parser: argparse.ArgumentParser,
) -> None:
    '''
    Adds the following arguments to your argument parser:

    - `padding`
    - `padding_start`
    - `padding_end`

    They are intended for use with the function `apply_padding_from_user_args`.
    '''

    parser.add_argument(
        '-p', '--padding',
        help=(
            'Add some number of seconds to the start and end of each subtitle. '
            'This value may be a floating point value (e.g. 1.5). '
            'It may be rounded if it is strangely precise (e.g. 1.000000001 -> 1.0). '
            'Mutually exclusive with --padding-start and --padding-end.'
        ),
        type=float,
        default=None,
    )

    parser.add_argument(
        '-ps', '--padding-start',
        help=(
            'Add some number of seconds to the start of each subtitle. '
            'Follows the same semantics as --padding, though it is mutually exclusive with --padding. '
            'See also --padding-end'
        ),
        type=float,
        default=None,
    )

    parser.add_argument(
        '-pe', '--padding-end',
        help=(
            'Add some number of seconds to the end of each subtitle. '
            'Follows the same semantics as --padding, though it is mutually exclusive with --padding. '
            'See also --padding-start'
        ),
        type=float,
        default=None,
    )


def apply_padding_from_user_args(
    time_ranges: TimeRanges,
    args: argparse.Namespace,
) -> None:

    padding = args.padding
    padding_start = args.padding_start
    padding_end = args.padding_end

    if padding is not None:

        if padding_start is not None:
            raise UsageError(
                'Cannot simultaneously use --padding (-p) and '
                '--padding-start (-ps). Please remove one or '
                'the other.'
            )

        if padding_end is not None:
            raise UsageError(
                'Cannot simultaneously use --padding (-p) and '
                '--padding-end (-pe). Please remove one or '
                'the other.'
            )

        padding_start = padding
        padding_end = padding

    else:
        if padding_start is None:
            padding_start = 0.0
        if padding_end is None:
            padding_end = 0.0

    # 1/100 of a second accuracy is 'good enough'

    time_ranges.add_padding(
        pad_start=round(padding_start * 100),
        pad_end=round(padding_end * 100),
        pad_ups=100,
    )

