import typing as ty

import os
import sys
import argparse
import tempfile
import subprocess
import html
import csv

from subs2cia import (
    ffprobe_wrapper,
    path_helpers,
    subtitles,
    cli_common_overwrite,
    cli_common_input_streams,
    cli_common_subtitle_extraction,
)

from subs2cia.multi_context_manager import MultiContextManager

from subs2cia.usage_error import UsageError


def swap_disallowed_chars(
    name: str,
    disallowed_chars: str,
    swapped: str = '_',
):
    builder = list()

    for c in name:
        if c in disallowed_chars:
            builder.append(swapped)
        else:
            builder.append(c)

    return ''.join(builder)


def convert_ups(
    old_stamp: int,
    old_ups: int,
    new_ups: int,
) -> int:
    if old_ups == new_ups:
        return old_stamp
    return round(old_stamp / old_ups * new_ups)


# 80-character ruler
################################################################################

_HELP_COLUMNS = '''\
List of available column names:

text
    Text of the relevant subtitle

screenclip
    Screenshot of the clipped portion. (For use with Anki, empty if no video)

screenclip_path
    Path to the screenshot of the clipped portion.
'''


# Not yet implemented:

#audioclip
#Audio of the clipped portion. (For use with Anki, empty if no audio)

#videoclip
#Video of the clipped portion. (For use with Anki, empty if no video)


def _select_columns(
    raw: str,
    allowed: set[str],
) -> ty.Sequence[str]:

    parts = raw.split(',')
    parts = [x.strip().lower() for x in parts]

    for part in parts:
        if part not in allowed:
            raise UsageError(
                f'Got unrecognized or invalid column: {part!r}\n'
                'Use --help-columns to see a list of valid columns.'
            )

    return parts


_DELIMITERS = {
    'tab': '\t',
    'pipe': '|',
    'semicolon': ';',
    'colon': ':',
    'comma': ',',
    'space': ' ',
}


def _csv_delimiter(raw: str) -> str:
    if raw in _DELIMITERS:
        return _DELIMITERS[raw]

    if len(raw) == 1:
        return raw

    raise ValueError('Invalid delimiter')


def _guess_delimiter_from_extension(file_path: str) -> str|None:

    file_ext = path_helpers.get_ext(file_path)
    file_ext = file_ext.lower()

    if file_ext == '.csv':
        return ','
    elif file_ext == '.tsv':
        return '\t'
    else:
        return None


def _stamp_to_ffmpeg_duration(
    stamp: int,
    ups: int,
) -> str:

    if ups < 1:
        raise ValueError(f'Units per second too small to make sense: {ups!r}')

    if stamp < 0:
        return '-' + _stamp_to_ffmpeg_duration(-stamp, ups)

    if ups == 1:
        return str(stamp)

    if ups <= 1000:
        return str(convert_ups(stamp, ups, 1000)) + 'ms'

    return str(convert_ups(stamp, ups, 1000000)) + 'us'


class SrsExportJob:

    def __init__(
        self,
        ffmpeg_cmd: str,
        output_path: str,
        ffmpeg_args: ty.Sequence[str],
    ):
        self.ffmpeg_cmd = ffmpeg_cmd
        self.output_path = output_path
        self.ffmpeg_args = tuple(ffmpeg_args)

    def __call__(self) -> None:

        if os.path.exists(self.output_path):
            return

        args = [
            self.ffmpeg_cmd,
            '-loglevel', 'warning',
            '-y',
            *self.ffmpeg_args
        ]

        subprocess.run(
            args,
            check=True,
        )

    @staticmethod
    def create_screenshot_job(
        ffmpeg_cmd: str,
        input_path: str,
        timestamp: int,
        timestamp_ups: int,
        output_path: str,
    ) -> 'SrsExportJob':

        seek = _stamp_to_ffmpeg_duration(timestamp, timestamp_ups)

        args = [
            '-ss', seek,
            '-i', input_path,

            # Magical commands to take a screenshot
            '-frames:v', '1',
            '-update', '1',

            output_path,
        ]

        return SrsExportJob(
            ffmpeg_cmd=ffmpeg_cmd,
            output_path=output_path,
            ffmpeg_args=args,
        )


def main(
    argv: ty.Sequence[str]|None = None,
) -> int:

    parser = argparse.ArgumentParser(
        prog='srs',
        description='Generate an Anki-compatible import',
    )

    parser.add_argument(
        '--columns', '-c',
        help=(
            'Comma-separated list of columns that should appear in the export. '
            'Use --help-columns to see a full list of valid options. '
            'Default: %(default)s'
        ),
        default='text,screenclip,audioclip,videoclip',
    )

    parser.add_argument(
        '--help-columns',
        help='Display a list of valid values to use with --columns',
        action='store_true',
        default=False,
    )

    # See: https://github.com/ankitects/anki/blob/main/rslib/src/media/files.rs
    parser.add_argument(
        '--disallowed-chars',
        help=(
            'Specify characters that cannot show up in media file names. '
            'Default: %(default)s'
        ),
        default='[]<>:"/?*^\\|',
    )

    parser.add_argument(
        '-o', '--output-path',
        help=(
            'Path to write the import CSV/TSV file to. '
            'If not specified, defaults to the input with the suffix '
            'replaced with `.srs_export.tsv`. '
            'See also --output-delimiter'
        ),
        default=None,
    )

    parser.add_argument(
        '--output-delimiter',
        help=(
            'Delimiter of the output file. '
            'Must be a single character string or one of: '
            + ', '.join(_DELIMITERS.keys()) + '. '
            'If not specified, infer the delimiter from the suffix of the path '
            'specified in --output-path. '
            'If specified, the suffix of the path in --output-path is ignored.'
        ),
        type=_csv_delimiter,
        default=None,
    )

    parser.add_argument(
        '-m', '--media',
        help=(
            'Path to write the media files to. '
            'If not specified, it will be the same directory as the path specified in --output-path.'
        ),
        default=None,
    )

    parser.add_argument(
        '-w', '--overwrite',
        help='Allow overwriting output paths',
        action='store_true',
        default=False,
    )

    parser.add_argument(
        '--scratch-path',
        help=(
            'Path to a directory to use as a scratch directory for temporary files. '
            'If specified, temporary files will be created and preserved in this directory. '
            'If the directory is not empty, some files may be overwritten. '
            '(It is up to you to ensure no data will be accidentally lost) '
            'If not specified, a temporary directory will be created and deleted after running.'
        ),
        default=None,
    )

    parser.add_argument(
        '--ffmpeg-cmd', '--ffmpeg-command',
        help='Specify the command for ffmpeg.',
        default='ffmpeg',
    )

    parser.add_argument(
        '--ffprobe-cmd', '--ffprobe-command',
        help='Specify the command for ffprobe.',
        default='ffprobe',
    )

    cli_common_input_streams.add_input_streams_args(parser)

    args = parser.parse_args(argv)


    if args.help_columns:
        print(_HELP_COLUMNS, file=sys.stderr)
        return 1



    disallowed_chars: str = args.disallowed_chars


    allow_overwite: bool = args.overwrite


    output_columns = _select_columns(
        raw=args.columns,
        allowed={
            'text',
            'screenclip',
            'audioclip',
            'videoclip',
            'timestamp',
        }
    )


    # Resolve input paths

    inputs = cli_common_input_streams.resolve_input_streams_from_user_args(args)

    if inputs.subs_path is None:
        print('No subtitles input specified.', file=sys.stderr)
        return 1


    # Resolve output_delimiter and output_path together

    output_path: str|None = args.output_path
    output_delimiter: str|None = args.output_delimiter

    if output_path is None and inputs.default_input_path is not None:
        output_path = path_helpers.swap_ext(inputs.default_input_path, '.srs_export.tsv')

    if output_path is None:
        raise UsageError(
            'Failed to select an output path. '
            'Please set --output-path.'
        )

    if not allow_overwite:
        cli_common_overwrite.check_overwritten_outputs((output_path,))

    if output_delimiter is None and output_path is not None:
        output_delimiter = _guess_delimiter_from_extension(output_path)

    if output_delimiter is None:
        raise UsageError(
            'Failed to select a delimiter for the output path. '
            'Please set --output to a file ending in .tsv or .csv, '
            'or set --output-delimiter.'
        )


    # Resolve path to media

    media_dir: str|None = args.media

    if media_dir is None:
        media_dir = os.path.dirname(output_path)


    # Resolve external binaries

    ffmpeg_cmd: str = args.ffmpeg_cmd
    ffprobe_cmd: str = args.ffprobe_cmd
    ffprobe = ffprobe_wrapper.FfprobeWrapper(ffprobe_cmd)


    # Probe input video/audio

    input_video_probe = (
        ffprobe.probe(inputs.video_path)
        if inputs.video_path is not None
        else None
    )

    input_video_stream = (
        input_video_probe.get_first_stream_matching(
            index=inputs.video_stream_index,
            codec_type='video',
        )
        if input_video_probe is not None
        else None
    )

    input_audio_probe = (
        ffprobe.probe(inputs.audio_path)
        if inputs.audio_path is not None
        else None
    )

    input_audio_stream = (
        input_video_probe.get_first_stream_matching(
            index=inputs.video_stream_index,
            codec_type='audio',
        )
        if input_video_probe is not None
        else None
    )


    with MultiContextManager() as deferred:


        # Resolve path to scratch directory

        scratch_path: str|None = args.scratch_path

        if scratch_path is None:

            scratch_path = deferred.accept(
                tempfile.TemporaryDirectory()
            )


        # Extract subtitles to scratch directory (if necessary)

        extraction_suffix = '.ass'

        extraction_path = os.path.join(
            scratch_path,
            'subtitles-extracted' + extraction_suffix,
        )

        inputs.subs_path = cli_common_subtitle_extraction.optionally_extract_subtitles(
            ffprobe=ffprobe,
            ffmpeg_cmd=args.ffmpeg_cmd,
            subs_path=inputs.subs_path,
            subs_index=inputs.subs_stream_index,
            extraction_path=extraction_path,
        )


        # Parse extracted subtitles

        subs = subtitles.parse_at_path(
            inputs.subs_path,
            encoding=inputs.subs_encoding,
        )


        # TODO: subtitle modifications


        # TODO: control file naming via args

        general_prefix: str|None = None

        if general_prefix is None and inputs.default_input_path is not None:
            general_prefix = path_helpers.swap_ext(
                os.path.basename(inputs.default_input_path),
                '',
            )

        if general_prefix is None:
            raise UsageError(
                'Could not resolve a prefix for the output file names.'
            )

        general_prefix = swap_disallowed_chars(general_prefix, disallowed_chars)


        screenshot_suffix = '.jpg'
        video_suffix = '.mp4'
        audio_suffix = '.mp3'


        # Each subtitle event corresponds to one SRS note
        # It may also create zero or more jobs to run later

        jobs: list[SrsExportJob] = list()

        with open(
            output_path,
            'w',
            newline='',
            encoding='utf-8',
        ) as output_file:

            csvw = csv.writer(
                output_file,
                delimiter=output_delimiter,
            )

            screenclip_path: str|None = None

            for sub_event in subs.events:

                time_range = ''.join((
                    str(sub_event.start),
                    '-',
                    str(sub_event.end),
                ))

                if (
                    'screenclip' in output_columns
                    and input_video_probe is not None
                    and input_video_stream is not None
                    and inputs.video_path is not None
                ):

                    screenclip_path = os.path.join(
                        media_dir,
                        ''.join((
                            general_prefix,
                            '_',
                            time_range,
                            screenshot_suffix,
                        ))
                    )

                    jobs.append(SrsExportJob.create_screenshot_job(
                        ffmpeg_cmd=ffmpeg_cmd,
                        input_path=inputs.video_path,
                        output_path=screenclip_path,
                        timestamp=sub_event.start,
                        timestamp_ups=subs.event_units_per_second,
                    ))

                screenclip = (
                    f'<img src="{html.escape(os.path.basename(screenclip_path))}" />'
                    if screenclip_path is not None
                    else ''
                )

                row_values = {
                    'text': sub_event.plain_text,
                    'screenclip_path': screenclip_path,
                    'screenclip': screenclip,
                }

                row = [
                    row_values.get(key, '')
                    for key in output_columns
                ]

                csvw.writerow(row)


        # Execute jobs
        # TODO: consider multiprocessing

        job_progress = 0

        for job in jobs:
            print(f'Job {job_progress+1} / {len(jobs)} ...', file=sys.stderr)
            job()
            job_progress += 1


    return 0

