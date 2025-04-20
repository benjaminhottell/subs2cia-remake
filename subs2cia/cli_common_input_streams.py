import typing as ty

import argparse
import dataclasses


# This module contains common utilities for CLIs that need to accept 3 optional input streams (video, audio, subtitles).


def add_input_streams_args(
    parser: argparse.ArgumentParser,
) -> None:
    '''
    Adds the following arguments to your argument parser:

    - `input_path`
    - `input_video_path`
    - `input_audio_path`
    - `input_subs_path`
    - `input_subs_encoding`
    - `input_video_stream`
    - `input_audio_stream`
    - `input_subs_stream`

    They are intended for use with the function `resolve_input_streams_from_user_args`.
    '''

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


@dataclasses.dataclass
class InputStreams:

    default_input_path: str|None

    video_path: str|None
    audio_path: str|None
    subs_path: str|None

    subs_encoding: str

    video_stream_index: int|None
    audio_stream_index: int|None
    subs_stream_index: int|None

    def discard_video(self) -> ty.Self:
        self.video_path = None
        self.video_stream = None
        return self


def resolve_input_streams_from_user_args(
    args: argparse.Namespace,
) -> InputStreams:

    input_path: str|None = args.input_path

    video_path: str|None = args.input_video_path
    audio_path: str|None = args.input_audio_path
    subs_path: str|None = args.input_subs_path

    video_stream_index: int|None = args.input_video_stream
    audio_stream_index: int|None = args.input_audio_stream
    subs_stream_index: int|None = args.input_subs_stream

    subs_encoding: str = args.input_subs_encoding

    # Resolve paths to input video/audio/subs input
    if video_path is None:
        video_path = input_path

    if audio_path is None:
        audio_path = input_path

    if subs_path is None:
        subs_path = input_path


    return InputStreams(

        default_input_path=input_path,

        video_path=video_path,
        audio_path=audio_path,
        subs_path=subs_path,

        subs_encoding=subs_encoding,

        video_stream_index=video_stream_index,
        audio_stream_index=audio_stream_index,
        subs_stream_index=subs_stream_index,

    )

