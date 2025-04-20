import typing as ty


class SubtitlesEvent:

    def __init__(
        self,
        start: int,
        end: int,
        raw_text: str,
        plain_text: str,
    ):
        self.start = start
        self.end = end
        self.raw_text = raw_text
        self.plain_text = plain_text

    def clone(self) -> 'SubtitlesEvent':
        return SubtitlesEvent(
            start=self.start,
            end=self.end,
            raw_text=self.raw_text,
            plain_text=self.plain_text,
        )

    def __repr__(self) -> str:
        return (
            'SubtitlesEvent('
            f'start={self.start!r}, '
            f'end={self.end!r}, '
            f'raw_text={self.raw_text!r}, '
            f'plain_text={self.plain_text!r}'
            ')'
        )


class Subtitles:

    def __init__(
        self,
        events: ty.Sequence[SubtitlesEvent],
        event_units_per_second: int,
    ):
        self.events = events
        self.event_units_per_second = event_units_per_second

    def filter_events(
        self,
        test: ty.Callable[[SubtitlesEvent], bool],
    ) -> ty.Self:
        '''Remove events that do not match the given predicate function.'''
        self.events = [x for x in self.events if test(x)]
        return self

    def __repr__(self) -> str:
        return (
            'Subtitles('
            f'events={self.events!r}, '
            f'event_units_per_second={self.event_units_per_second!r}, '
            ')'
        )

