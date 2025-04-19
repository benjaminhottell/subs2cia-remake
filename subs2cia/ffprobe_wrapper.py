import typing as ty

import subprocess
import json


class FfprobeStream:

    def __init__(
        self,
        data: dict[str, ty.Any],
    ):
        self._data = data

    def unwrap(self) -> dict[str, ty.Any]:
        return self._data

    def get_codec_type(self) -> str:
        ret = self._data.get('codec_type')
        if not isinstance(ret, str):
            raise TypeError('codec_type field missing or invalid')
        return ret

    def get_index(self) -> int:
        ret = self._data.get('index')
        if not isinstance(ret, int):
            raise TypeError('index field missing or invalid')
        return ret

    def get_time_base(self) -> str:
        ret = self._data.get('time_base')
        if not isinstance(ret, str):
            raise TypeError('time_base field missing or invalid')
        return ret

    def get_units_per_second(self) -> int:
        raw = self.get_time_base()

        parts = raw.split('/')

        if len(parts) != 2:
            raise TypeError('time_base malformed')

        top = int(parts[0])
        bottom = int(parts[1])

        # We want the reciprocal
        return bottom // top


class FfprobeResult:

    def __init__(
        self,
        data: dict[str, ty.Any],
    ):
        self._data = data

    def unwrap(self) -> dict[str, ty.Any]:
        return self._data

    def get_streams(self) -> list[FfprobeStream]:

        streams = self._data.get('streams')

        if not isinstance(streams, (list, tuple)):
            raise TypeError('streams field missing or invalid')

        return [
            FfprobeStream(x)
            for x in streams
            if isinstance(x, dict)
        ]

    def get_first_stream_matching(
        self,
        index: int|None = None,
        codec_type: str|None = None,
    ) -> FfprobeStream|None:

        streams = self.get_streams()

        if index is not None:
            return streams[index]

        for stream in streams:

            if codec_type is not None and stream.get_codec_type() != codec_type:
                continue

            return stream

        return None


class FfprobeWrapper:

    def __init__(
        self,
        ffprobe_cmd: str,
        process_encoding: str = 'utf-8',
    ):
        self._ffprobe_cmd = ffprobe_cmd
        self._process_encoding = process_encoding

    def probe(
        self,
        target_path: str,
        show_streams: bool = False,
        show_format: bool = False,
        encoding: str = 'utf-8',
    ) -> FfprobeResult:

        args = [
            self._ffprobe_cmd,
            '-v', 'quiet',
            '-print_format', 'json',
        ]

        if show_format:
            args.append('-show_format')

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

        return FfprobeResult(ret)

