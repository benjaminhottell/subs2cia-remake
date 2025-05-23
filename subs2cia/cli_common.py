import typing as ty

from subs2cia import (
    subtitles,
    ffmpeg_helpers,
)

from subs2cia.ffprobe_wrapper import FfprobeWrapper


class SubtitlesSelectionError(RuntimeError):
    pass


def optionally_extract_subtitles(
    ffprobe: FfprobeWrapper,
    ffmpeg_cmd: str,
    subs_path: str,
    subs_index: int|None,
    extraction_path: str,
) -> str:
    '''
    This function may (or may not) extract or convert subtitles from an incompatible file to a compatible file. If a conversion occurs, then the path specified in extraction_path will be written to. It will then return the path to the subtitles. (I.e., it will return subs_path or extraction_path depending on whether an extraction was necessary)

    If subs_path refers to a 'standalone' subtitles file that this codebase natively supports, then nothing occurs and subs_path is returned.

    If subs_path refers to a container file (e.g. mp4, mkv, etc.), then it will attempt to select a subtitles stream from it. If subs_index is specified (non-None) then then that specific stream will be selected. The stream will be demuxed into extraction_path. The returned path will be extraction_path.

    If subs_path refers to a 'standalone' subtitles file that this codebase does not natively support, then it will be treated as though it were a container file anyway. This way, ffmpeg will convert the subtitles as best as it can for us.
    '''

    subs_is_standalone = subtitles.is_supported_file(subs_path)

    if subs_is_standalone:
        return subs_path

    # Because FfprobeWrapper caches the results, we do not need to worry if the target path was already probed.
    subs_probe = ffprobe.probe(
        target_path=subs_path,
    )

    subs_stream = subs_probe.get_first_stream_matching(
        index=subs_index,
        codec_type='subtitle',
    )

    if subs_stream is None:
        raise SubtitlesSelectionError(
            'Cannot find a valid subtitles stream or supported subtitles file.'
        )

    ffmpeg_helpers.demux_stream(
        ffmpeg_cmd=ffmpeg_cmd,
        input_path=subs_path,
        stream_index=subs_stream.get_index(),
        output_path=extraction_path,
        overwrite=True,
    )

    return extraction_path


def modify_subtitles(
    subs: subtitles.Subtitles,
    keep_blank: bool = False,
    remove_containing: ty.Iterable[str]|None = None,
    keep_containing: ty.Iterable[str]|None = None,
) -> None:
    '''
    Perform common operations on a given Subtitles object. The object is modified in-place.

    If `keep_blank` is False, subtitles that are empty or solely whitespace will be removed.
    '''

    if not keep_blank:
        subs.filter_events(lambda e: len(e.plain_text.strip()) != 0)

    if remove_containing is not None:
        for x in remove_containing:
            subs.filter_events(lambda e: x not in e.plain_text)

    if keep_containing is not None:
        for x in keep_containing:
            subs.filter_events(lambda e: x in e.plain_text)

