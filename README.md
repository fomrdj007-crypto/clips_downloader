# YouTube Segment Downloader

Python script that downloads YouTube videos at the best quality up to **1080p**. You can clip a time range, or batch-download a list of clips from a `links.txt` file.

## Features

- Best available quality, capped at 1080p (4K / 1440p is ignored)
- Download a single video or only a start–end segment
- Batch mode: read titles, URLs, and timestamps from `links.txt`
- Filenames taken from your titles in `links.txt`
- Works on **Windows** and **macOS**

## Requirements

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/) (needed to merge video + audio and cut clips)

## Install

### 1. Python package

```bash
pip install yt-dlp
```

If `pip` is not found on Mac:

```bash
python3 -m pip install yt-dlp
```

### 2. FFmpeg

**Windows (easiest):**

```powershell
winget install ffmpeg
```

Close and reopen PowerShell, then check:

```powershell
ffmpeg -version
```

**macOS (Homebrew):**

```bash
brew install ffmpeg
```

Then check:

```bash
ffmpeg -version
```

If you do not have Homebrew yet:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Files

Put these in the same folder:

```text
youtube_segment_downloader.py
links.txt
```

## links.txt format

Separate each video with a blank line.

```text
1. Jimmy fallon interview:
https://www.youtube.com/watch?v=kOYS9lX2pgg

1. Ryan reynolds and hugh jackman about short torso(long)
https://www.youtube.com/watch?v=Jvgm3IT5DsI
0:31 1:20

1. I miss being horrible: The ellen show(moderate)
https://youtu.be/G2r_I1G_mfA?t=243
3:54 4:08
```

| Line | Meaning |
| --- | --- |
| 1 | Title used as the output filename |
| 2 | YouTube URL |
| 3 | Start and end time (optional) |

- If line 3 is missing, the full video is downloaded.
- If line 3 is present, only that segment is saved.
- Leading numbers like `1.` are stripped from the filename.
- Long titles are trimmed automatically.

Time formats accepted: `90`, `1:30`, `00:01:30`.

## Usage

On Windows use `py` or `python`. On Mac use `python3`.

### Batch download from links.txt

```bash
python3 youtube_segment_downloader.py
```

Windows:

```powershell
py youtube_segment_downloader.py
```

Files are saved next to the script, named from the titles in `links.txt`.

### One full video

```bash
python3 youtube_segment_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### One clip

```bash
python3 youtube_segment_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" -s 1:20 -e 1:50
```

Start and end must both be given, or neither.

### Custom output folder

```bash
python3 youtube_segment_downloader.py -o ~/Movies
```

Windows:

```powershell
py youtube_segment_downloader.py -o "C:\Users\YourName\Videos"
```

### Custom links file

```bash
python3 youtube_segment_downloader.py -f ~/Desktop/links.txt
```

### Combine options

```bash
python3 youtube_segment_downloader.py -f ./links.txt -o ~/Movies
```

### Help

```bash
python3 youtube_segment_downloader.py -h
```

## Command summary

| Goal | Command |
| --- | --- |
| All clips from `links.txt` | `python3 youtube_segment_downloader.py` |
| One full video | `python3 youtube_segment_downloader.py "URL"` |
| One clip | `python3 youtube_segment_downloader.py "URL" -s 1:20 -e 1:50` |
| Custom save folder | add `-o "/path/to/folder"` |
| Custom links file | add `-f "/path/to/links.txt"` |

## Notes

- Quality is limited to 1080p on purpose.
- YouTube URLs in `youtu.be` and `youtube.com` form both work.
- FFmpeg must be available in your terminal PATH. After installing it, open a **new** terminal window before running the script.
- If a clip still looks like the full video, make sure you are using the latest `youtube_segment_downloader.py` and that the third line in that `links.txt` section has two timestamps.

## License

Use this script for content you have the right to download. You are responsible for following YouTube’s terms and copyright law.
