import unittest

from subs2cia.cli_common import modify_subtitles
from subs2cia.subtitles_types import Subtitles, SubtitlesEvent


def get_test_subtitles():
    return Subtitles(
        events=[
            SubtitlesEvent(
                start=0,
                end=1000,
                raw_text='Hello, world',
                plain_text='Hello, world',
            ),
            SubtitlesEvent(
                start=1000,
                end=2000,
                raw_text='Goodbye, world',
                plain_text='Goodbye, world',
            ),
        ],
        event_units_per_second=1000,
    )


class TestModifySubtitles(unittest.TestCase):

    def test_keep_blank(self):
        subs = Subtitles(
            events=[
                SubtitlesEvent(
                    start=0,
                    end=1000,
                    raw_text='',
                    plain_text='',
                ),
            ],
            event_units_per_second=1000,
        )
        modify_subtitles(subs, keep_blank=True)
        self.assertEqual(len(subs.events), 1)

    def test_remove_blank(self):
        subs = Subtitles(
            events=[
                SubtitlesEvent(
                    start=0,
                    end=1000,
                    raw_text='',
                    plain_text='',
                ),
            ],
            event_units_per_second=1000,
        )
        modify_subtitles(subs, keep_blank=False)
        self.assertEqual(len(subs.events), 0)

    def test_keep_containing_string(self):
        subs = Subtitles(
            events=[
                SubtitlesEvent(
                    start=0,
                    end=1000,
                    raw_text='Hello, world',
                    plain_text='Hello, world',
                ),
                SubtitlesEvent(
                    start=1000,
                    end=2000,
                    raw_text='Goodbye, world',
                    plain_text='Goodbye, world',
                ),
            ],
            event_units_per_second=1000,
        )
        modify_subtitles(subs, keep_containing=['Hello'])
        self.assertEqual(len(subs.events), 1)
        self.assertEqual(subs.events[0].plain_text, 'Hello, world')

    def test_remove_containing_string(self):
        subs = Subtitles(
            events=[
                SubtitlesEvent(
                    start=0,
                    end=1000,
                    raw_text='Hello, world',
                    plain_text='Hello, world',
                ),
                SubtitlesEvent(
                    start=1000,
                    end=2000,
                    raw_text='Goodbye, world',
                    plain_text='Goodbye, world',
                ),
            ],
            event_units_per_second=1000,
        )
        modify_subtitles(subs, remove_containing=['Hello'])
        self.assertEqual(len(subs.events), 1)
        self.assertEqual(subs.events[0].plain_text, 'Goodbye, world')

