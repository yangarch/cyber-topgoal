#!/usr/bin/env python3
"""Edit the artist tag of audio files, then rescan the library to apply.

The library shows "Unknown Artist" when a file has no artist tag. Some files
also carry a literal placeholder like "알 수 없는 음악가" written by ripping
software. Use this to find such files and write the correct artist.

Usage:
  # List files whose artist is missing OR a known placeholder
  python scripts/set_artist.py --list [DIR]

  # Dump EVERY file with its current artist tag (diagnostic)
  python scripts/set_artist.py --all [DIR]

  # Set the artist tag on one file
  python scripts/set_artist.py "<file path>" "<정확한 아티스트명>"

DIR (for --list/--all) defaults to $MUSIC_DIR, then ./music_files.
On the server run it inside the container so DIR points at the real library:
  docker compose exec web python scripts/set_artist.py --list
Supports mp3 / m4a / flac / ogg via mutagen.

After editing, hit the 🔄 Rescan button (or restart the container).
"""
import os
import sys
from mutagen import File

DEFAULT_DIR = os.environ.get("MUSIC_DIR", "./music_files")
EXTS = ('.mp3', '.m4a', '.flac', '.ogg', '.wav')

# Placeholder artist values treated as "missing" (spaces stripped, lowercased).
# Add more variants here if you spot others.
PLACEHOLDERS = {
    "unknownartist",
    "unknown",
    "알수없는음악가",
    "알수없는아티스트",
    "알수없음",
}


def _artist_of(path):
    try:
        audio = File(path, easy=True)
    except Exception:
        return None
    if not audio:
        return None
    return (audio.get('artist', [None]) or [None])[0]


def _is_placeholder(artist):
    if not artist or not artist.strip():
        return True
    return "".join(artist.split()).lower() in PLACEHOLDERS


def _iter_audio(scan_dir):
    for root, _, files in os.walk(scan_dir):
        for name in files:
            if name.lower().endswith(EXTS):
                yield os.path.join(root, name)


def _resolve_dir(args):
    scan_dir = args[0] if args else DEFAULT_DIR
    abs_dir = os.path.abspath(scan_dir)
    print(f"스캔 폴더: {abs_dir}")
    if not os.path.isdir(abs_dir):
        sys.exit(f"  -> 폴더가 존재하지 않습니다. 경로를 확인하세요.")
    return scan_dir


def list_missing(args):
    scan_dir = _resolve_dir(args)
    total = 0
    hits = []
    for path in _iter_audio(scan_dir):
        total += 1
        artist = _artist_of(path)
        if _is_placeholder(artist):
            hits.append((path, artist))
    print(f"오디오 파일 {total}개 검사함.")
    if not hits:
        print("아티스트가 비었거나 placeholder인 파일이 없습니다.")
        return
    print(f"수정이 필요한 파일 {len(hits)}개:")
    for path, artist in hits:
        print(f"  [{artist!r}]  {path}")


def list_all(args):
    scan_dir = _resolve_dir(args)
    total = 0
    for path in _iter_audio(scan_dir):
        total += 1
        print(f"  {_artist_of(path)!r:30}  {path}")
    print(f"총 {total}개 파일.")


def set_artist(path, artist):
    if not os.path.isfile(path):
        sys.exit(f"파일을 찾을 수 없습니다: {path}")
    audio = File(path, easy=True)
    if audio is None:
        sys.exit(f"지원하지 않는/읽을 수 없는 파일입니다: {path}")
    if audio.tags is None:
        audio.add_tags()
    old = (audio.get('artist', [None]) or [None])[0]
    audio['artist'] = artist
    audio.save()
    print(f"OK: {path}\n  artist: {old!r} -> {artist!r}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--list":
        list_missing(args[1:])
        return
    if args[0] == "--all":
        list_all(args[1:])
        return
    if len(args) != 2:
        sys.exit("사용법: python scripts/set_artist.py \"<파일경로>\" \"<아티스트명>\"")
    set_artist(args[0], args[1])


if __name__ == "__main__":
    main()
