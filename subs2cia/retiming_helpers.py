import typing as ty

from subs2cia.time_ranges import TimeRanges


def adjust_timing(
    sub_start: int,
    sub_end: int,
    time_ranges: TimeRanges,
) -> ty.Tuple[int, int]|None:

    '''
    Return the start and end times of a subtitle that it should have if only the given time ranges are kept in the video.
    '''

    # There is no time on screen,
    # therefore no subtitles appear,
    # therefore this subtitle should not appear.
    if len(time_ranges) == 0:
        return None

    # Find the first relevant time range
    # (It is relevant if it may intersect with the subtitle's duration)

    # This gets us close to the first/last relevant range
    guess_idx = time_ranges.get_index(sub_start)

    if guess_idx >= len(time_ranges):
        guess_idx -= 1

    first_idx = guess_idx
    last_idx = guess_idx

    for i in range(guess_idx, -1, -1):
        this_range = time_ranges[i]

        if this_range[1] < sub_start:
            first_idx = i + 1
            break

        first_idx = i

    # Find the last relevant range

    last_idx = first_idx

    for i in range(guess_idx, len(time_ranges)):

        this_range = time_ranges[i]

        if this_range[0] > sub_end:
            last_idx = i - 1
            break

        last_idx = i

    if first_idx >= len(time_ranges):
        return None

    first_range = time_ranges[first_idx]
    last_range = time_ranges[last_idx]

    # If the first relevant time range starts after the subtitle starts,
    # clip the subtitle's duration
    if first_range[0] >= sub_start:
        sub_start = time_ranges[first_idx][0]

    # If the last relevant time range ends before the subtitle ends,
    # clip the subtitle's duration
    if last_range[1] <= sub_end:
        sub_end = last_range[1]

    cumulative_skip_before = time_ranges.get_cumulative_skip(first_idx)
    cumulative_skip_during = time_ranges.get_cumulative_skip(last_idx)

    #print(
    #    'sub_start', sub_start,
    #    'sub_end', sub_end,
    #    'first_idx', first_idx,
    #    'last_idx', last_idx,
    #    'first_range', first_range,
    #    'last_range', last_range,
    #    'cumulative_skip_before', cumulative_skip_before,
    #    'cumulative_skip_during', cumulative_skip_during,
    #)

    sub_start -= cumulative_skip_before
    sub_end -= cumulative_skip_during

    if sub_end <= sub_start:
        return None

    return (sub_start, sub_end)

