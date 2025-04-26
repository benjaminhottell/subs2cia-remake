# subs2cia-remake

Provides a handful of tools for generating studying material from video/audio files and accompanying subtitles.

This is a partial rewrite of the original [subs2cia by Daniel Xing](https://github.com/dxing97/subs2cia). This rewrite comes with many breaking changes.


## Dependencies

- [Python 3](https://www.python.org/downloads/)
- [ffmpeg](https://ffmpeg.org/) (and ffprobe, which should come with ffmpeg)

This package was developed and tested using Python version 3.12 and ffmpeg version 7.2, though it may work with earlier versions.

This package does not depend on any other Python packages (aside from the standard library).


## condense

Given a video/audio file, generates a condensed audio file given its subtitles. This is useful for removing sections without any dialogue, which may come in handy for studying.

Below are some usage examples. Use the `--help` argument to see the full usage and additional options.

Generate a condensed audio file from a video file with embedded subtitles:

```bash
python3 -m subs2cia condense -p 0.5 -o /path/to/output.mp3 -i /path/to/input.mp4
```

(Note that the extension of the output path controls the format of the output. If you set the extension of the output path to `.mp4`, then a video would be generated instead. The `-p 0.5` argument adds 0.5 seconds of padding before and after every subtitle.)

Generate a condensed audio file from a video file with external subtitles:

```bash
python3 -m subs2cia condense -p 0.5 -o /path/to/output.mp3 -i /path/to/input.mp4 -is /path/to/subtitles.vtt
```


## srs (WIP)

Generate an Anki-compatible notes import based on the subtitles.

```bash
python3 -m subs2cia srs -i /path/to/input.mp4
```

Use `-is` to specify an alternate set of subtitles to use.

```bash
python3 -m subs2cia sr -i /path/to/input.mp4 -is /path/to/subtitles.vtt
```

By default, the media files (screenshots, etc.) will appear in the same directory as the output file. You may use `-m` to specify a path to your Anki instance's media directory instead.

```bash
python3 -m subs2cia srs -i /path/to/input.mp4 -m "~/.local/share/Anki2/User 1/collection.media"
```

