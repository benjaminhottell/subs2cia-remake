import typing as ty

from subs2cia.time_ranges import TimeRanges
from subs2cia.retiming_helpers import adjust_timing
from .subtitles_types import Subtitles, SubtitlesEvent


def parse_time(field: str) -> int:
    parts = field.split(':')

    if len(parts) != 3:
        raise ValueError(f'Invalid time field, expected 3 parts separated by a colon (:) but got {field}')

    hours = int(parts[0])
    mins = int(parts[1])
    seconds_and_hundredths = parts[2]

    parts = seconds_and_hundredths.split('.')

    if len(parts) != 2:
        raise ValueError(f'Invalid seconds.hundredths, expected 2 parts separated by a period (.) but got {seconds_and_hundredths}')

    seconds = int(parts[0])
    hundredths = int(parts[1])

    if hours < 0 or mins < 0 or seconds < 0 or hundredths < 0:
        raise ValueError('Invalid time field, negative value')

    return hundredths + (seconds * 100) + (mins * 100 * 60) + (hours * 100 * 60 * 60)


def unparse_time(hundredths: int) -> str:

    if hundredths < 0:
        raise ValueError(f'Negative time cannot exist, got {hundredths}')

    unparse_hours = hundredths // (100 * 60 * 60)
    unparse_mins = (hundredths // (100 * 60)) % 60
    unparse_seconds = (hundredths // 100) % 60
    unparse_hundredths = hundredths % 100

    out_hours = str(unparse_hours)
    out_mins = str(unparse_mins).rjust(2, '0')
    out_seconds = str(unparse_seconds).rjust(2, '0')
    out_hundredths = str(unparse_hundredths).rjust(2, '0')

    return f'{out_hours}:{out_mins}:{out_seconds}.{out_hundredths}'


def escape_to_plain_text(text: str) -> str:

    parts = list()

    i = 0

    while i < len(text):

        c = text[i]

        if c == '\\' and i+1 < len(text):

            next = text[i+1]

            if next == 'n' or next == 'N':
                parts.append('\n')
                i += 2
                continue

        parts.append(c)
        i += 1
        continue

    return ''.join(parts)


def parse(
    file: ty.IO[str],
) -> Subtitles:

    events: list[SubtitlesEvent] = list()

    # State machine
    _STATE_SKIP_UNTIL_EVENTS = 1
    _STATE_GET_FORMAT = 2
    _STATE_GET_EVENTS = 3

    state = _STATE_SKIP_UNTIL_EVENTS

    start_idx: int|None = None
    end_idx: int|None = None
    text_idx: int|None = None

    format: ty.Sequence[str]|None = None

    for ln in file:
        ln = ln.rstrip()


        if state == _STATE_SKIP_UNTIL_EVENTS:
            if ln == '[Events]':
                state = _STATE_GET_FORMAT
            continue


        elif state == _STATE_GET_FORMAT:

            if not ln.startswith('Format:'):
                raise ValueError(f'Expected a Format line, got: {ln}')

            format = [x.strip() for x in ln[7:].split(',')]

            try:
                end_idx = format.index('End')
            except ValueError as e:
                raise ValueError('Malformed Format line, does not contain "End"') from e

            try:
                start_idx = format.index('Start')
            except ValueError as e:
                raise ValueError('Malformed Format line, does not contain "Start"') from e

            try:
                text_idx = format.index('Text')
            except ValueError as e:
                raise ValueError('Malformed Format line, does not contain "Text"') from e

            if text_idx != len(format) - 1:
                raise ValueError('Malformed Format line, "Text" must be the last field')

            state = _STATE_GET_EVENTS
            continue


        elif state == _STATE_GET_EVENTS:

            assert format is not None
            assert start_idx is not None
            assert end_idx is not None
            assert text_idx is not None

            if ln == '':
                state = _STATE_SKIP_UNTIL_EVENTS
                continue

            if not ln.startswith('Dialogue:'):
                continue

            ln = ln[9:]
            ln = ln.lstrip()

            event = ln.split(',', len(format) - 1)

            if len(event) != len(format):
                raise ValueError(f'Malformed event, invalid number of fields, got {len(event)} but expected {len(format)}')

            raw_text = event[text_idx]

            parsed_event = SubtitlesEvent(
                start=parse_time(event[start_idx]),
                end=parse_time(event[end_idx]),
                raw_text=raw_text,
                plain_text=escape_to_plain_text(raw_text),
            )

            events.append(parsed_event)

        else:
            raise RuntimeError('Unreachable')

    return Subtitles(
        events=events,
        event_units_per_second=100,
    )


def retime(
    in_file: ty.IO[str],
    out_file: ty.IO[str],
    time_ranges: TimeRanges,
) -> None:

    time_ranges.with_units_per_second(100)

    # State machine
    _STATE_SKIP_UNTIL_EVENTS = 1
    _STATE_GET_FORMAT = 2
    _STATE_GET_EVENTS = 3

    state = _STATE_SKIP_UNTIL_EVENTS

    start_idx: int|None = None
    end_idx: int|None = None

    format: ty.Sequence[str]|None = None

    for ln in in_file:
        ln = ln.rstrip()


        if state == _STATE_SKIP_UNTIL_EVENTS:

            if ln == '[Events]':
                state = _STATE_GET_FORMAT

            out_file.write(ln)
            out_file.write('\n')

            continue


        elif state == _STATE_GET_FORMAT:

            if not ln.startswith('Format:'):
                raise ValueError(f'Expected a Format line, got: {ln}')

            format = [x.strip() for x in ln[7:].split(',')]

            try:
                end_idx = format.index('End')
            except ValueError as e:
                raise ValueError('Malformed Format line, does not contain "End"') from e

            try:
                start_idx = format.index('Start')
            except ValueError as e:
                raise ValueError('Malformed Format line, does not contain "Start"') from e

            state = _STATE_GET_EVENTS

            out_file.write(ln)
            out_file.write('\n')

            continue


        elif state == _STATE_GET_EVENTS:

            assert format is not None
            assert start_idx is not None
            assert end_idx is not None

            if ln == '':
                state = _STATE_SKIP_UNTIL_EVENTS
                out_file.write(ln)
                out_file.write('\n')
                continue

            if not ln.startswith('Dialogue:'):
                out_file.write(ln)
                out_file.write('\n')
                continue

            ln = ln[9:]
            ln = ln.lstrip()

            event = ln.split(',', len(format) - 1)

            if len(event) != len(format):
                raise ValueError(f'Malformed event, invalid number of fields, got {len(event)} but expected {len(format)}')

            start = parse_time(event[start_idx])
            end = parse_time(event[end_idx])

            new_range = adjust_timing(
                sub_start=start,
                sub_end=end,
                time_ranges=time_ranges,
            )

            if new_range is None:
                continue

            new_start, new_end = new_range

            #if new_start > new_end:
                #continue

            event[start_idx] = unparse_time(new_start)
            event[end_idx] = unparse_time(new_end)

            out_file.write('Dialogue: ')
            out_file.write(','.join(event))
            out_file.write('\n')

        else:
            raise RuntimeError('Unreachable')

