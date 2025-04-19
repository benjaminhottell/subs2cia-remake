import typing as ty

import math


def _ranges_overlap(
    range1: ty.Tuple[int, int],
    range2: ty.Tuple[int, int],
) -> bool:
    return (
        (range1[0] >= range2[0] and range1[0] <= range2[1]) or
        (range2[0] >= range1[0] and range2[0] <= range1[1])
    )


def _merge_ranges(
    range1: ty.Tuple[int, int],
    range2: ty.Tuple[int, int],
) -> ty.Tuple[int, int]:
    return (
        max(0, min(range1[0], range2[0])),
        max(range1[1], range2[1])
    )


def _consolidate_overlapping_ranges(
    time_ranges: list[ty.Tuple[int, int]]
) -> list[ty.Tuple[int, int]]:

    '''
    time_ranges must be sorted on x[0] before calling this!
    '''

    if len(time_ranges) <= 1:
        return time_ranges

    it = iter(time_ranges)

    ret = [next(it)]

    for r2 in it:
        r1 = ret[-1]

        if _ranges_overlap(r1, r2):
            ret[-1] = _merge_ranges(r1, r2)
        else:
            ret.append(r2)

    return ret


class TimeRanges:

    def __init__(
        self,
        ranges: list[ty.Tuple[int, int]],
        units_per_second: int,
    ):
        '''
        The input ranges must be sorted and consolidated.
        If in doubt, call a static constructor (from_unsorted).
        '''
        self._ranges = ranges
        self._units_per_second = units_per_second
        self._cached_cumulative_skip: ty.Sequence[int]|None = None

    @staticmethod
    def from_unsorted(
        ranges: ty.Iterable[ty.Tuple[int, int]],
        units_per_second: int,
    ) -> 'TimeRanges':

        ranges = list(ranges)

        ranges.sort(key=lambda x: x[0])

        ranges = _consolidate_overlapping_ranges(ranges)

        return TimeRanges(
            ranges,
            units_per_second=units_per_second,
        )

    @staticmethod
    def create_empty(units_per_second: int) -> 'TimeRanges':
        return TimeRanges(list(), units_per_second)

    def clone(self) -> 'TimeRanges':
        return TimeRanges(
            ranges=list(self._ranges),
            units_per_second=self._units_per_second,
        )

    def get_units_per_second(self) -> int:
        return self._units_per_second

    def set_units_per_second(
        self,
        ups: int,
    ) -> ty.Self:

        if self._units_per_second == ups:
            return self

        factor: float = ups / self._units_per_second

        if math.isnan(factor) or math.isinf(factor):
            raise ValueError('Got a bad factor')

        self._ranges = [
            (
                math.floor(x[0] * factor),
                math.ceil(x[1] * factor)
            )
            for x in self._ranges
        ]

        self._cached_cumulative_skip = None

        return self

    def with_units_per_second(
        self,
        ups: int,
    ) -> 'TimeRanges':
        return self.clone().set_units_per_second(ups)

    def add_padding(
        self,
        pad_start: int,
        pad_end: int,
        pad_ups: int,
    ) -> ty.Self:

        if pad_start == 0 and pad_end == 0:
            return self

        if pad_ups > self._units_per_second:
            self.set_units_per_second(pad_ups)

        elif pad_ups < self._units_per_second:
            factor: float = self._units_per_second / pad_ups
            pad_start = math.floor(factor * pad_start)
            pad_end = math.ceil(factor * pad_end)
            #pad_ups = self._units_per_second

        self._ranges = [
            (
                max(0, r[0] - pad_start),
                r[1] + pad_end,
            )
            for r in self._ranges
        ]

        self._ranges = _consolidate_overlapping_ranges(self._ranges)

        self._cached_cumulative_skip = None

        return self

    def get_index(self, start: int) -> int:
        '''
        Binary search on self._ranges (based on the range start stamps)
        '''

        if len(self._ranges) == 0:
            return 0

        # The given range starts before the earliest range
        if self._ranges[0][0] > start:
            return 0

        # The given range starts after the latest range
        if self._ranges[-1][0] < start:
            return len(self._ranges)

        high = len(self._ranges)
        low = 0

        while low < high:

            middle = (low + high) // 2
            middle_value = self._ranges[middle]

            if middle_value[0] == start:
                return middle

            elif middle_value[0] < start:
                low = middle + 1

            else:
                high = middle

        # If we did contain this range, it would show up at this index
        return low

    def _consolidate_overlapping_ranges_around(self, index: int) -> None:

        if len(self._ranges) <= 1:
            return

        while (
            index > 0 and
            _ranges_overlap(self._ranges[index-1], self._ranges[index])
        ):
            self._ranges[index-1] = _merge_ranges(self._ranges[index-1], self._ranges[index])
            del self._ranges[index]
            index -= 1

        while (
            (index + 1) < len(self._ranges) and
            _ranges_overlap(self._ranges[index], self._ranges[index+1])
        ):
            self._ranges[index] = _merge_ranges(self._ranges[index], self._ranges[index+1])
            del self._ranges[index+1]

        self._cached_cumulative_skip = None

    def add(
        self,
        start: int,
        end: int,
    ) -> None:
        idx = self.get_index(start)
        self._ranges.insert(idx, (start, end))
        self._consolidate_overlapping_ranges_around(idx)

    def _rebuild_cumulative_skip(self) -> None:

        if len(self._ranges) == 0:
            self._cached_cumulative_skip = list()
            return

        cache: list[int] = list()

        cache.append(self._ranges[0][0])

        for idx in range(1, len(self._ranges)):
            this_skip = self._ranges[idx][0] - self._ranges[idx-1][1]
            cache.append(cache[idx-1] + this_skip)

        self._cached_cumulative_skip = cache

    def get_cumulative_skip(self, idx: int) -> int:
        if self._cached_cumulative_skip is None:
            self._rebuild_cumulative_skip()
        assert self._cached_cumulative_skip is not None
        return self._cached_cumulative_skip[idx]

    def __getitem__(self, x: int) -> ty.Tuple[int, int]:
        return self._ranges.__getitem__(x)

    def __len__(self) -> int:
        return len(self._ranges)

    def __iter__(self) -> ty.Iterator[ty.Tuple[int, int]]:
        return iter(self._ranges)

    def __next__(self) -> ty.Any:
        raise TypeError('Call __iter__ first')

