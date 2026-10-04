#!/usr/bin/env python3
"""
YouTube Segment Downloader

With no arguments:
    Reads links.txt in the same folder as this script and downloads each entry.

With arguments:
    Downloads a single URL, optionally clipped with --start / --end.

Quality: best available up to 1080p.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yt_dlp
from yt_dlp.utils import download_range_func

SCRIPT_DIR = Path(__file__).resolve().parent
LINKS_FILE = SCRIPT_DIR / "links.txt"
MAX_TITLE_LEN = 80

YOUTUBE_URL_RE = re.compile(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+", re.I)
TIMESTAMP_TOKEN_RE = re.compile(r"^\d+(?::\d{1,2}){0,2}(?:\.\d+)?$")


def timestamp_to_seconds(value: str) -> float:
    value = value.strip()
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value)

    parts = value.split(":")
    if len(parts) == 2 and all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)

    if len(parts) == 3 and all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    raise ValueError(
        f"Invalid timestamp '{value}'. Use seconds (90), MM:SS (1:30), or HH:MM:SS (0:01:30)."
    )


def sanitize_filename(title: str) -> str:
    title = title.strip()
    title = re.sub(r"^\d+\.\s*", "", title)
    title = re.sub(r'[<>:"/\\|?*]', "", title)
    title = re.sub(r"\s+", " ", title).strip(" .")
    if len(title) > MAX_TITLE_LEN:
        title = title[:MAX_TITLE_LEN].rstrip(" .")
    return title or "video"


def parse_timestamp_pair(line: str) -> tuple[str, str] | None:
    """Return start/end if the line looks like '0:31 1:20' or '0:37-1:14'."""
    tokens = line.replace(",", " ").replace("–", " ").replace("—", " ").split()
    expanded: list[str] = []
    for token in tokens:
        if "-" in token and ":" in token:
            expanded.extend(part for part in token.split("-") if part)
        else:
            expanded.append(token)
    times = [token for token in expanded if TIMESTAMP_TOKEN_RE.match(token)]
    if len(times) >= 2:
        return times[0], times[1]
    return None


def parse_links_file(path: Path) -> list[dict]:
    """Parse links.txt with or without blank lines between clips.

    A clip is a title line, then a YouTube URL, then an optional timestamp line.
    """
    if not path.exists():
        raise FileNotFoundError(f"Could not find {path}")

    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    entries: list[dict] = []
    pending_title: str | None = None

    i = 0
    while i < len(lines):
        line = lines[i]
        url_match = YOUTUBE_URL_RE.search(line)
        if url_match:
            url = url_match.group(0).rstrip(").,]")
            title = sanitize_filename(pending_title or f"video_{len(entries) + 1}")
            pending_title = None
            start = end = None
            if i + 1 < len(lines):
                pair = parse_timestamp_pair(lines[i + 1])
                if pair:
                    start, end = pair
                    i += 1
            entries.append({"title": title, "url": url, "start": start, "end": end})
        elif parse_timestamp_pair(line):
            pass
        else:
            pending_title = line
        i += 1

    if not entries:
        raise ValueError(f"No valid sections found in {path}")
    return entries


def download_video(
    url: str,
    output_dir: Path,
    title: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    if title:
        name = sanitize_filename(title)
    else:
        name = "%(title).80s"

    ydl_opts = {
        "format": (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo[height<=1080]+bestaudio/"
            "best[height<=1080]"
        ),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "outtmpl": str(output_dir / f"{name}.%(ext)s"),
        "quiet": False,
        "noprogress": False,
        "overwrites": True,
    }

    print(f"URL   : {url}")
    print(f"Title : {title or '(from YouTube)'}")

    if start and end:
        start_sec = timestamp_to_seconds(start)
        end_sec = timestamp_to_seconds(end)
        if end_sec <= start_sec:
            raise ValueError("End time must be greater than start time.")
        ydl_opts["download_ranges"] = download_range_func(None, [(start_sec, end_sec)])
        ydl_opts["force_keyframes_at_cuts"] = True
        print(f"Start : {start} ({start_sec}s)")
        print(f"End   : {end} ({end_sec}s)")
    else:
        print("Range : full video")

    print(f"Output: {output_dir}")
    print("Downloading...\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("Done.\n")


def download_from_links_file(links_path: Path, output_dir: Path) -> int:
    entries = parse_links_file(links_path)
    print(f"Found {len(entries)} section(s) in {links_path.name}\n")

    failed_titles: list[str] = []
    for i, entry in enumerate(entries, start=1):
        print("=" * 60)
        print(f"[{i}/{len(entries)}] {entry['title']}")
        print("=" * 60)
        try:
            download_video(
                url=entry["url"],
                output_dir=output_dir,
                title=entry["title"],
                start=entry["start"],
                end=entry["end"],
            )
        except Exception as exc:
            failed_titles.append(entry["title"])
            print(f"FAILED: {entry['title']}\n{exc}\n", file=sys.stderr)

    succeeded = len(entries) - len(failed_titles)
    print(f"Finished. {succeeded} succeeded, {len(failed_titles)} failed.")
    if failed_titles:
        print("\nFailed titles:")
        for title in failed_titles:
            print(f"  - {title}")
        failed_path = output_dir / "failed.txt"
        failed_path.write_text("\n".join(failed_titles) + "\n", encoding="utf-8")
        print(f"\nAlso saved to {failed_path}")
    return len(failed_titles)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download YouTube clips. "
            "Run with no arguments to process links.txt next to this script."
        )
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL (optional)")
    parser.add_argument("-s", "--start", help="Start time, e.g. 1:30")
    parser.add_argument("-e", "--end", help="End time, e.g. 2:45")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Folder to save files (default: same folder as the script / links.txt)",
    )
    parser.add_argument(
        "-f",
        "--file",
        default=None,
        help="Path to links.txt (default: links.txt next to this script)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_dir = Path(args.output) if args.output else SCRIPT_DIR

    try:
        if args.url:
            if bool(args.start) ^ bool(args.end):
                print("Provide both --start and --end, or neither.", file=sys.stderr)
                sys.exit(1)
            download_video(
                url=args.url,
                output_dir=output_dir,
                start=args.start,
                end=args.end,
            )
        else:
            links_path = Path(args.file) if args.file else LINKS_FILE
            failed = download_from_links_file(links_path, output_dir)
            sys.exit(1 if failed else 0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
