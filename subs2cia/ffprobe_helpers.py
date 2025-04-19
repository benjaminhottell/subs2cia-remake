import typing as ty

import subprocess
import json


def run_ffprobe(
    ffprobe_cmd: str,
    target_path: str,
    show_streams: bool = False,
    show_format: bool = False,
    encoding: str = 'utf-8',
) -> dict[str, ty.Any]:

    args = [
        ffprobe_cmd,
        '-v', 'quiet',
        '-print_format', 'json',
    ]

    if show_format:
        args.append('-show-format')

    if show_streams:
        args.append('-show_streams')

    args.append('--')
    args.append(target_path)

    p = subprocess.run(
        args,
        encoding=encoding,
        stdout=subprocess.PIPE,
        check=True,
    )

    ret = json.loads(p.stdout)

    if not isinstance(ret, dict):
        raise TypeError('ffprobe returned an unexpected JSON value, expected a dict (object)')

    return ret


def get_first_stream(
    probe_result: dict[str, ty.Any],
    codec_type: str|None = None,
) -> dict[str, ty.Any]|None:
 
    if 'streams' not in probe_result:
        raise ValueError('No streams in probe result')

    for stream in probe_result['streams']:

        if codec_type is not None and stream.get('codec_type') == codec_type:
            return stream

    return None


def get_stream_index(
    stream: dict[str, ty.Any]
) -> int:

    ret = stream.get('index')

    if not isinstance(ret, int):
        raise TypeError('index field missing or invalid')

    return ret


def get_stream_units_per_second(
    stream: dict[str, ty.Any]
) -> int:

    raw = stream.get('time_base')

    if not isinstance(raw, str):
        raise TypeError('time_base field missing or invalid')

    parts = raw.split('/')

    if len(parts) != 2:
        raise TypeError('time_base malformed')

    top = int(parts[0])
    bottom = int(parts[1])

    # We want the reciprocal
    return bottom // top


def select_stream(
    probe_result: dict[str, ty.Any],
    index: int,
):

    if 'streams' not in probe_result:
        raise ValueError('No streams in probe result')

    return probe_result['streams'][index]

