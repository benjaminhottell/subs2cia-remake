import unittest


def main() -> int:

    loader = unittest.TestLoader()

    runner = unittest.TextTestRunner()

    tests = loader.discover('tests')

    result = runner.run(tests)

    if not result.wasSuccessful():
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

