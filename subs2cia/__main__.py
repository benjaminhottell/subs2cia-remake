import sys

from subs2cia.usage_error import UsageError
from subs2cia.cli import main


if __name__ == '__main__':
    try:
        code = main()
    except UsageError as e:
        print(str(e), file=sys.stderr)
        code = 1

    sys.exit(code)

