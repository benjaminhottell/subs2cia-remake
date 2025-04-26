import typing as ty

import sys

from subs2cia.usage_error import UsageError

from subs2cia import (
    cli_srs,
    cli_condense,
)


# 80-character ruler
################################################################################

_USAGE = '''\
usage: subs2cia COMMAND [OPTIONS...]
       subs2cia COMMAND --help

This package provides a handful of tools for working with video/audio files
with accompanying subtitles.

Supported commands:

  condense  Generate a condensed (dialogue-only) file

  srs       Generate an Anki-compatible notes import (like subs2srs)
'''


def _show_usage():
    raise UsageError(_USAGE)


def main(argv: ty.Sequence[str]|None = None) -> int:

    if argv is None:
        argv = sys.argv[1:]

    _subcommand_mains = {
        'srs':      cli_srs.main,
        'condense': cli_condense.main,
    }

    if len(argv) == 0 or argv[0] in ('-h', '--help', 'help'):
        _show_usage()
        return 1

    subcommand_name = argv[0]
    argv = argv[1:]

    if subcommand_name not in _subcommand_mains:
        raise UsageError(
            f'No such subcommand: {subcommand_name}\n'
            'Use --help to see the usage.'
        )

    subcommand_main = _subcommand_mains[subcommand_name]

    code = subcommand_main(argv=argv)

    if not isinstance(code, int):
        raise TypeError('Got an invalid return code from module ' + subcommand_name)

    return code


if __name__ == '__main__':
    try:
        code = main()
    except UsageError as e:
        print(str(e), file=sys.stderr)
        code = 1
    sys.exit(code)

