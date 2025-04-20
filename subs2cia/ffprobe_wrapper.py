import typing as ty

import logging
import subprocess
import json

logger = logging.getLogger(__name__)


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

        if index is None:
            streams = self.get_streams()
        else:
            streams = [self.get_streams()[index]]

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
        self._cached_results: dict[str, FfprobeResult] = dict()

    def probe(
        self,
        target_path: str,
        allow_cache: bool = True,
        encoding: str = 'utf-8',
    ) -> FfprobeResult:

        if allow_cache and target_path in self._cached_results:
            return self._cached_results[target_path]

        args = [
            self._ffprobe_cmd,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
        ]

        args.append('--')
        args.append(target_path)

        logger.debug(f'Invoking ffprobe: {args}')

        p = subprocess.run(
            args,
            encoding=encoding,
            stdout=subprocess.PIPE,
            check=True,
        )

        raw_result = json.loads(p.stdout)

        if not isinstance(raw_result, dict):
            raise TypeError('ffprobe returned an unexpected JSON value, expected a dict (object)')

        result = FfprobeResult(raw_result)

        self._cached_results[target_path] = result

        return result

