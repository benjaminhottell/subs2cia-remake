import unittest

from subs2cia.time_ranges import TimeRanges
from subs2cia.retiming_helpers import adjust_timing


class TestAdjustTimingFromStart(unittest.TestCase):

    # Cases where the subtitle to re-time starts at time=0 ('the start')
    # I feel this is a little easier to reason about than the other cases

    def test_empty_range(self):
        tr = TimeRanges.create_empty(1000)
        new_range = adjust_timing(0, 100, tr)
        self.assertIsNone(new_range)

    def test_no_change_perfect_fit(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 100)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 100))

    def test_no_change_perfect_fit_from_consolidation(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(50, 100)
        tr.add(0, 50)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 100))

    def test_change_hole_at_start(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(20, 100)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 80))

    def test_change_hole_at_end(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 80)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 80))

    def test_change_hole_at_start_and_end(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(20, 80)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 60))

    def test_hole_in_middle(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 20)
        tr.add(80, 100)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 40))

    def test_two_holes_in_middle(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 20)
        tr.add(40, 50)
        tr.add(80, 100)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 50))

    def test_many_holes(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(10, 20)
        tr.add(40, 50)
        tr.add(80, 90)
        new_range = adjust_timing(0, 100, tr)
        self.assertEqual(new_range, (0, 30))


class TestAdjustTimingAdvanced(unittest.TestCase):

    def test_no_change_perfect_fit_with_nearby_tricksters(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 498)
        tr.add(500, 600)
        tr.add(602, 999)
        new_range = adjust_timing(500, 600, tr)
        self.assertEqual(new_range, (498, 598))

    def test_empty_range(self):
        tr = TimeRanges.create_empty(1000)
        new_range = adjust_timing(50, 100, tr)
        self.assertIsNone(new_range)

    def test_no_change_expansive_fit(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(0, 2000)
        new_range = adjust_timing(50, 100, tr)
        self.assertEqual(new_range, (50, 100))

    def test_many_holes_away_from_start(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(10, 20)
        tr.add(40, 50)
        tr.add(80, 90)
        new_range = adjust_timing(50, 150, tr)
        self.assertEqual(new_range, (20, 30))

    def test_many_holes_away_from_start2(self):
        tr = TimeRanges.create_empty(1000)
        tr.add(15, 25)
        tr.add(45, 55)
        tr.add(85, 95)
        new_range = adjust_timing(50, 150, tr)
        self.assertEqual(new_range, (15, 30))


