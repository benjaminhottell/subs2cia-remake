import typing as ty

import argparse
import sys
import os
import shutil
import mimetypes
import tempfile

from subs2cia import (
    cli_common,
    path_helpers,
    ffmpeg_helpers,
    subtitles,
)

from subs2cia.ffprobe_wrapper import (
    FfprobeResult,
    FfprobeStream,
    FfprobeWrapper,
)

from subs2cia.time_ranges import TimeRanges


def main(argv: ty.Sequence[str]|None = None) -> int:

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='subs2cia',
        description='Generate condensed audio files from an audio/video file and subtitles.',
    )

    parser.add_argument(
        '-i', '--input-path',
        help=(
            'The audio/video file with embedded subtitles to condense. '
            'You may also use the arguments '
            '--input-video-path, --input-audio-path, and --input-subs-path '
            'in the case where the contents are spread across multiple files.'
        ),
        default=None,
    )

    parser.add_argument(
        '-iv', '--input-video-path',
        help=(
            'The path to the file containing the video to use. '
            'If not specified, defaults to the path specified via --input-path.'
        ),
        default=None,
    )

    parser.add_argument(
        '-ia', '--input-audio-path',
        help=(
            'The path to the file containing the audio to use. '
            'If not specified, defaults to the path specified via --input-path.'
        ),
        default=None,
    )

    parser.add_argument(
        '-is', '--input-subs-path', '--input-subtitles-path',
        help=(
            'The path to the file containing the subtitles to use. '
            'If not specified, defaults to the path specified via --input-path.'
        ),
        default=None,
    )

    parser.add_argument(
        '-ise', '--input-subs-encoding', '--input-subtitles-encoding',
        help=(
            'The encoding of the subtitles file. '
            'Default: %(default)s'
        ),
        default='utf-8',
    )

    parser.add_argument(
        '-ivs', '--input-video-stream',
        help=(
            'The specific stream index for the video contained in '
            '--input-video-path or --input-path.'
        ),
        type=int,
        default=None,
    )

    parser.add_argument(
        '-ias', '--input-audio-stream',
        help=(
            'The specific stream index for the audio contained in '
            '--input-audio-path or --input-path.'
        ),
        type=int,
        default=None,
    )

    parser.add_argument(
        '-iss', '--input-subs-stream',
        help=(
            'The specific stream index for the subtitles contained in '
            '--input-subs-path or --input-path.'
        ),
        type=int,
        default=None,
    )

    parser.add_argument(
        '-o', '--output-path',
        help=(
            'The path to write the output to. '
            'If not specified, defaults to the path specified in --input-path but '
            'with its extension replaced to `.condensed.mp3`. '
            'If --input-path is not specified in favor of the more specific options, '
            'then you must explicitly set --output-path.'
        ),
        default=None,
    )

    parser.add_argument(
        '-os', '--output-subs-path',
        help=(
            'The path to write the re-timed subtitles to. '
            'If not specified, defaults the path specified by --output-path with the suffix replaced by .ass. '
            'The suffix of this path controls the format of the output. '
            'Ignored if --embed-subtitles is set.'
        ),
        default=None,
    )

    parser.add_argument(
        '-w', '--overwrite',
        help='Overwrite the output file (specified in --output-path), if it exists.',
        action='store_true',
        default=False,
    )

    parser.add_argument(
        '-p', '--padding',
        help=(
            'Add some number of seconds to the start and end of each subtitle. '
            'This value may be a floating point value (e.g. 1.5). '
            'It may be rounded if it is strangely precise (e.g. 1.000000001 -> 1.0). '
            'Mutually exclusive with --padding-start and --padding-end.'
        ),
        type=float,
        default=None,
    )

    parser.add_argument(
        '-ps', '--padding-start',
        help=(
            'Add some number of seconds to the start of each subtitle. '
            'Follows the same semantics as --padding, though it is mutually exclusive with --padding. '
            'See also --padding-end'
        ),
        type=float,
        default=None,
    )

    parser.add_argument(
        '-pe', '--padding-end',
        help=(
            'Add some number of seconds to the end of each subtitle. '
            'Follows the same semantics as --padding, though it is mutually exclusive with --padding. '
            'See also --padding-start'
        ),
        type=float,
        default=None,
    )

    cli_common.add_subtitle_modification_args(parser)

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

    args = parser.parse_args(argv)

    input_path: str|None = args.input_path

    input_audio_path: str|None = args.input_audio_path
    input_audio_index: int|None = args.input_audio_stream

    input_video_path: str|None = args.input_video_path
    input_video_index: int|None = args.input_video_stream

    input_subs_path: str|None = args.input_subs_path
    input_subs_index: int|None = args.input_subs_stream
    input_subs_encoding: str = args.input_subs_encoding

    output_path: str|None = args.output_path
    output_subs_path: str|None = args.output_subs_path

    allow_overwrite: bool = args.overwrite

    ffmpeg_cmd: str = args.ffmpeg_cmd


    # Resolve path to output
    if output_path is None:
        if input_path is not None:
            output_path = path_helpers.swap_ext(input_path, '.condensed.mp3')
        else:
            print('Missing --output-path (-o) or --input-path (-i)', file=sys.stderr)
            print('Use --help for more information', file=sys.stderr)
            return 1


    # Resolve path to subtitles output
    if output_subs_path is None:
        output_subs_path = path_helpers.swap_ext(output_path, '.ass')


    # The extension of the output controls the format of the output
    # i.e., setting it to /path/to/something.mp3 will make it an mp3 file

    # Passing a path to guess_type is 'soft deprecated' in newer versions of Python
    # (In practice this means it will work but new code is encouraged to use a different function)
    output_format_mime, _ = mimetypes.guess_type(output_path)

    # In the case where the output is an audio file (e.g. mp3),
    # then we should not waste time sorting out the video file.

    ignore_video = (
        isinstance(output_format_mime, str) 
        and output_format_mime.startswith('audio/')
    )


    # Resolve paths to input video/audio/subs input
    if input_video_path is None:
        input_video_path = input_path
    if input_audio_path is None:
        input_audio_path = input_path
    if input_subs_path is None:
        input_subs_path = input_path

    # If the output is audio, intercept and discard the video
    if ignore_video:
        input_video_path = None

    # Avoid accidental mis-use, favor the more specific paths defined immediately above
    del input_path

    # Sanity checks on inputs

    if input_video_path is None and input_audio_path is None:
        print('No video or audio input specified.', file=sys.stderr)
        return 1

    if input_subs_path is None:
        print('No subtitles input specified.', file=sys.stderr)
        return 1


    if not allow_overwrite:

        paths_already_existing = set()

        if os.path.exists(output_path):
            paths_already_existing.add(output_path)

        if os.path.exists(output_subs_path):
            paths_already_existing.add(output_subs_path)

        if len(paths_already_existing) > 0:

            for clashing_path in paths_already_existing:
                print('Output path already exists:', clashing_path, file=sys.stderr)

            print('Pass --overwrite (or -w) to overwrite this output file.', file=sys.stderr)
            print('Or, use --output-path (or -o) to specify a different path.', file=sys.stderr)
            return 1


    # Resolve padding options

    padding = args.padding
    padding_start = args.padding_start
    padding_end = args.padding_end

    if padding is not None:

        if padding_start is not None or padding_end is not None:
            print('Cannot simultaneously use --padding and --padding-start/--padding-end', file=sys.stderr)
            return 1

        padding_start = padding
        padding_end = padding

    else:
        if padding_start is None:
            padding_start = 0.0
        if padding_end is None:
            padding_end = 0.0



    # Resolve wrappers to external binaries

    ffprobe = FfprobeWrapper(
        ffprobe_cmd=args.ffprobe_cmd,
    )


    # Create a list of things that need to be closed when done

    close_later = list()


    # Begin try-finally block for close_later
    try:

        # Resolve scratch directory

        scratch_path = args.scratch_path

        if scratch_path is None:
            tempdir = tempfile.TemporaryDirectory()
            scratch_path = tempdir.name
            close_later.append(tempdir)


        # Now we must probe the audio and/or video file inputs
        # The probe will reveal useful information about the audio/video
        # (Note that probing invokes a subprocess and is therefore expensive,
        # so try to re-use probes whenever possible)

        audio_probe: FfprobeResult|None = None
        video_probe: FfprobeResult|None = None

        if input_audio_path is not None:
            audio_probe = ffprobe.probe(
                target_path=input_audio_path,
            )

        if input_video_path is not None:
            video_probe = ffprobe.probe(
                target_path=input_video_path,
            )


        # Each input file consists of one or more streams
        # (Unless the subtitles file is a standalone subtitles file)
        # We need to select one stream to use

        audio_stream: FfprobeStream|None = None
        video_stream: FfprobeStream|None = None

        if audio_probe is not None:
            audio_stream = audio_probe.get_first_stream_matching(
                index=input_audio_index,
                codec_type='audio',
            )

        if video_probe is not None:
            video_stream = video_probe.get_first_stream_matching(
                index=input_video_index,
                codec_type='video',
            )

        # Avoid confusion, use get_index() on the stream itself :)
        del input_audio_index
        del input_video_index


        # Error condition check
        if audio_stream is None and video_stream is None:
            print('No audio or video stream found.', file=sys.stderr)
            return 1


        extraction_suffix = '.ass'

        extraction_path = os.path.join(
            scratch_path,
            'subtitles-extracted' + extraction_suffix,
        )

        extracted_subs_path = cli_common.optionally_extract_subtitles(
            ffprobe=ffprobe,
            ffmpeg_cmd=ffmpeg_cmd,
            subs_path=input_subs_path,
            subs_index=input_subs_index,
            extraction_path=extraction_path,
        )

        # prefer extracted_subs_path now
        del input_subs_path

        subs = subtitles.parse_at_path(
            extracted_subs_path,
            encoding=input_subs_encoding,
        )


        # Apply subtitle modifications
        cli_common.modify_subtitles_with_user_args(subs, args)


        # From the subtitles we can extract the times in which subtitles would be on-screen

        subs_time_ranges = TimeRanges.from_unsorted(
            [
                (x.start, x.end)
                for x in subs.events
            ],
            units_per_second=subs.event_units_per_second,
        )


        # Apply padding options to the subtitle timings
        # 1/100 of a second accuracy is 'good enough'

        subs_time_ranges.add_padding(
            pad_start=round(padding_start * 100),
            pad_end=round(padding_end * 100),
            pad_ups=100,
        )


        # Rewrite the subs with the new time ranges

        retime_suffix = '.ass'

        retime_path = os.path.join(
            scratch_path,
            'subtitles-retimed' + retime_suffix,
        )

        with open(extracted_subs_path, 'r') as retime_in_file:

            with open(retime_path, 'w') as retime_out_file:

                subtitles.retime(
                    in_file=retime_in_file,
                    out_file=retime_out_file,
                    time_ranges=subs_time_ranges,
                    format='ass',
                )


        # Find the corresponding time ranges in the audio/video

        audio_time_ranges = (
            subs_time_ranges.with_units_per_second(
                audio_stream.get_units_per_second()
            )
            if audio_stream is not None
            else None
        )

        video_time_ranges = (
            subs_time_ranges.with_units_per_second(
                video_stream.get_units_per_second()
            )
            if video_stream is not None
            else None
        )


        # Gather up the input files that we will need to pass to ffmpeg

        # ffmpeg thinks in terms of an array of input files and indexes into that array
        # Here we build that array and decide which indexes correspond to which input files

        # In the case where just --input-path is specified, all indexes are 0 and the array has just one element

        input_files: list[str] = list()

        # subs_file_index: int|None = None
        video_file_index: int|None = None
        audio_file_index: int|None = None

        if input_audio_path is not None:
            try:
                audio_file_index = input_files.index(input_audio_path)
            except ValueError:
                audio_file_index = len(input_files)
                input_files.append(input_audio_path)

        if input_video_path is not None:
            try:
                video_file_index = input_files.index(input_video_path)
            except ValueError:
                video_file_index = len(input_files)
                input_files.append(input_video_path)


        # Given these time ranges, we can create a ffmpeg filter to trim the audio and/or video down

        complex_filter_path = os.path.join(scratch_path, 'trim-complex-filter.txt')

        with open(complex_filter_path, 'w', encoding='utf-8') as filter_file:

            output_audio_stream = (
                ffmpeg_helpers.write_complex_filter_for_audio_trim(
                    file=filter_file,
                    audio_time_ranges=audio_time_ranges,
                    audio_file_index=audio_file_index,
                    audio_stream_index=audio_stream.get_index(),
                )
                if (
                    audio_time_ranges is not None 
                    and audio_file_index is not None
                    and audio_stream is not None
                )
                else None
            )

            output_video_stream = (
                ffmpeg_helpers.write_complex_filter_for_video_trim(
                    file=filter_file,
                    video_time_ranges=video_time_ranges,
                    video_file_index=video_file_index,
                    video_stream_index=video_stream.get_index(),
                )
                if (
                    video_time_ranges is not None
                    and video_file_index is not None
                    and video_stream is not None
                )
                else None
            )

        ffmpeg_helpers.apply_complex_filter(
            ffmpeg_cmd=ffmpeg_cmd,
            input_file_paths=input_files,
            output_path=output_path,
            output_audio_stream=output_audio_stream,
            output_video_stream=output_video_stream,
            complex_filter_path=filter_file.name,
            overwrite=allow_overwrite,
        )

        if path_helpers.get_ext(retime_path) == path_helpers.get_ext(output_subs_path):
            shutil.move(
                retime_path,
                output_subs_path,
            )

        else:
            ffmpeg_helpers.demux_stream(
                ffmpeg_cmd=ffmpeg_cmd,
                input_path=retime_path,
                output_path=output_subs_path,
                stream_index=0,
            )

        return 0


    finally:

        failed_to_close = False

        while len(close_later) > 0:
            x = close_later.pop()
            try:
                x.__exit__(None, None, None)
            except Exception as e:
                print(str(e), file=sys.stderr)
                failed_to_close = True

        if failed_to_close:
            print('At least one error occurred while cleaning up.', file=sys.stderr)
            return 1

