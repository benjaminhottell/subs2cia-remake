import unittest

from subs2cia.time_ranges import TimeRanges


class TestAddingRanges(unittest.TestCase):

    def test_add1(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(100, 500)
        self.assertEqual(tr[0], (100, 500))

    def test_add2(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(100, 500)
        tr.add(600, 1000)
        self.assertEqual(tr[0], (100, 500))
        self.assertEqual(tr[1], (600, 1000))

    def test_add2_merged(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(100, 500)
        tr.add(500, 1000)
        self.assertEqual(tr[0], (100, 1000))

    def test_add3_merged(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(10, 20)
        tr.add(15, 95)
        tr.add(90, 100)
        self.assertEqual(tr[0], (10, 100))
        self.assertEqual(len(tr), 1)

    def test_add5_merged(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(1, 2)
        tr.add(4, 5)
        tr.add(96, 97)
        tr.add(99, 100)
        tr.add(1, 100)
        self.assertEqual(tr[0], (1, 100))
        self.assertEqual(len(tr), 1)

    def test_add3_unsorted(self) -> None:
        tr = TimeRanges.create_empty(1000)
        tr.add(100, 200)
        tr.add(10, 20)
        tr.add(1, 2)
        l = list(tr)
        self.assertEqual(l, [(1,2), (10, 20), (100, 200)])

