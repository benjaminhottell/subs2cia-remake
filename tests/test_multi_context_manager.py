import typing as ty
import unittest

from subs2cia.multi_context_manager import MultiContextManager


class PhonyManager():

    def __init__(
        self,
        enter_action: ty.Callable,
        exit_action: ty.Callable,
    ):
        self._enter_action = enter_action
        self._exit_action = exit_action

    def __enter__(self):
        self._enter_action()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        del exc_type, exc_value, tb
        self._exit_action()


class TestMultiContextManager(unittest.TestCase):
    
    def test_call_order(self):

        things = list()

        with MultiContextManager() as deferred:

            deferred.accept(PhonyManager(
                enter_action=lambda: things.append('enter-a'),
                exit_action=lambda: things.append('exit-a'),
            ))

            deferred.accept(PhonyManager(
                enter_action=lambda: things.append('enter-b'),
                exit_action=lambda: things.append('exit-b'),
            ))

            deferred.accept(PhonyManager(
                enter_action=lambda: things.append('enter-c'),
                exit_action=lambda: things.append('exit-c'),
            ))


        self.assertEqual(
            things,
            [
                'enter-a',
                'enter-b',
                'enter-c',
                'exit-c',
                'exit-b',
                'exit-a',
            ]
        )
