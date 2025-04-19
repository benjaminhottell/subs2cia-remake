import typing as ty

import os
import subprocess

from subs2cia import path_helpers
from subs2cia.time_ranges import TimeRanges


# ffmpeg usage
# ffmpeg global_options... input_options... -i input_path output_options... output_path


def _safe_path(file_path: str) -> str:
    if not os.path.isabs(file_path) and file_path.startswith('-'):
        return './' + file_path
    return file_path


def demux_stream(
    ffmpeg_cmd: str,
    input_path: str,
    stream_index: int,
    output_path: str,
    encoding: str = 'utf-8',
    overwrite: bool = False,
) -> None:
    '''
    Demux (extract) a single stream from a file.
    The output format is inferred from the extension of the output path.
    '''

    input_path = _safe_path(input_path)
    output_path = _safe_path(output_path)

    args = [
        ffmpeg_cmd,
        ('-y' if overwrite else '-n'),
        '-i', input_path,
        '-map', '0:'+str(stream_index),
        output_path,
    ]

    subprocess.run(
        args,
        encoding=encoding,
        check=True,
    )


def write_complex_filter_for_audio_trim(
    file: ty.IO[str],
    audio_time_ranges: TimeRanges,
    audio_file_index: int,
    audio_stream_index: int,
    temp_audio_stream_prefix = 'a',
    temp_concat_audio_stream_prefix = 'ca',
) -> str:

    if len(audio_time_ranges) == 0:
        raise ValueError('No time ranges for audio trim')

    total_audio_streams = 0
    total_concat_audio_streams = 0
    audio_streams = list()

    # The filters for trimming audio and video seem suspiciously similar but are subtly different
    # As a result I did not try to 'de-duplicate these parts'

    for time_range in audio_time_ranges:

        this_out = f'{temp_audio_stream_prefix}{total_audio_streams}'
        total_audio_streams += 1

        # Stream that goes into the filter
        file.write('[')
        file.write(str(audio_file_index))
        file.write(':')
        file.write(str(audio_stream_index))
        file.write(']')

        # atrim filter
        # Note the use of 'atrim' and 'asetpts' instead of 'trim' and 'setpts'
        file.write('atrim=')
        file.write('start_pts=')
        file.write(str(time_range[0]))
        file.write(':')
        file.write('end_pts=')
        file.write(str(time_range[1]))
        file.write(',asetpts=PTS-STARTPTS')

        # Stream that it goes 'out' to
        file.write('[')
        file.write(this_out)
        file.write(']')

        # End of line
        file.write(';')

        audio_streams.append(this_out)

        # Concatenate audio streams if necessary
        if len(audio_streams) >= 2:

            this_concat_out = f'{temp_concat_audio_stream_prefix}{total_concat_audio_streams}'
            total_concat_audio_streams += 1

            stream2 = audio_streams.pop()
            stream1 = audio_streams.pop()

            # Input streams
            file.write('[')
            file.write(stream1)
            file.write(']')
            file.write('[')
            file.write(stream2)
            file.write(']')

            # Note this is different from how videos are concat'd
            file.write('concat=v=0:a=1')

            # Output stream
            file.write('[')
            file.write(this_concat_out)
            file.write(']')
            file.write(';')

            audio_streams.append(this_concat_out)

    return audio_streams[-1]


def write_complex_filter_for_video_trim(
    file: ty.IO[str],
    video_time_ranges: TimeRanges,
    video_file_index: int,
    video_stream_index: int,
    temp_video_stream_prefix = 'v',
    temp_concat_video_stream_prefix = 'cv',
) -> str:

    if len(video_time_ranges) == 0:
        raise ValueError('No time ranges for video trim')

    total_video_streams = 0
    total_concat_video_streams = 0
    video_streams = list()

    for time_range in video_time_ranges:

        this_out = f'{temp_video_stream_prefix}{total_video_streams}'
        total_video_streams += 1

        # Stream that goes into the filter
        file.write('[')
        file.write(str(video_file_index))
        file.write(':')
        file.write(str(video_stream_index))
        file.write(']')

        # Trim filter
        file.write('trim=')
        file.write('start_pts=')
        file.write(str(time_range[0]))
        file.write(':')
        file.write('end_pts=')
        file.write(str(time_range[1]))
        file.write(',setpts=PTS-STARTPTS')

        # Stream that it goes 'out' to
        file.write('[')
        file.write(this_out)
        file.write(']')

        # End of line
        file.write(';')

        video_streams.append(this_out)

        # Concatenate video streams if necessary
        if len(video_streams) >= 2:

            this_concat_out = f'{temp_concat_video_stream_prefix}{total_concat_video_streams}'
            total_concat_video_streams += 1

            stream2 = video_streams.pop()
            stream1 = video_streams.pop()

            # Input streams
            file.write('[')
            file.write(stream1)
            file.write(']')
            file.write('[')
            file.write(stream2)
            file.write(']')

            file.write('concat')

            # Output stream
            file.write('[')
            file.write(this_concat_out)
            file.write(']')
            file.write(';')

            video_streams.append(this_concat_out)

    return video_streams[-1]


def apply_complex_filter(

    ffmpeg_cmd: str,

    input_file_paths: ty.Sequence[str],

    output_path: str,

    output_audio_stream: str|None = None,
    output_video_stream: str|None = None,
    output_subs_stream: str|None = None,

    complex_filter: str|None = None,
    complex_filter_path: str|None = None,

    encoding: str = 'utf-8',

    overwrite: bool = False,

) -> None:

    if len(input_file_paths) == 0:
        raise ValueError('No input files')

    if output_audio_stream is None and output_video_stream is None:
        raise ValueError('Outputting no video and no audio')

    if complex_filter is None and complex_filter_path is None:
        raise ValueError('No complex filter')

    if complex_filter is not None and complex_filter_path is not None:
        raise ValueError('Too many complex filters')

    input_file_paths = [
        path_helpers.avoid_leading_dash(x)
        for x in input_file_paths
    ]

    args = [
        ffmpeg_cmd,
        ('-y' if overwrite else '-n'),
    ]

    if complex_filter is not None:
        args.append('-filter_complex')
        args.append(complex_filter)

    if complex_filter_path is not None:
        args.append('-/filter_complex')
        args.append(complex_filter_path)

    for input_file in input_file_paths:
        args.append('-i')
        args.append(input_file)

    if output_audio_stream is not None:
        args.append('-map')
        args.append('[' + output_audio_stream + ']')

    if output_video_stream is not None:
        args.append('-map')
        args.append('[' + output_video_stream + ']')

    if output_subs_stream is not None:
        args.append('-scodec')
        args.append('copy')
        args.append('-map')
        args.append(output_subs_stream)

    args.append(output_path)

    subprocess.run(
        args,
        encoding=encoding,
        check=True,
    )

