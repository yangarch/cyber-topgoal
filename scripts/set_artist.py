#!/usr/bin/env python3
"""Edit the artist tag of audio files, then rescan the library to apply.

The library shows "Unknown Artist" when a file has no artist tag. Use this
to list such files and write the correct artist directly into the file.

Usage:
  # List every file whose artist is missing/Unknown under the music dir
  python scripts/set_artist.py --list

  # Set the artist tag on one file
  python scripts/set_artist.py "music_files/some/track.mp3" "정확한 아티스트명"

The music dir defaults to $MUSIC_DIR, then ./music_files. Supports
mp3 / m4a / flac / ogg (anything mutagen can write in easy mode).

After editing, hit the 🔄 Rescan button in the app (or restart the
container) so the new tags are picked up.
"""
import os
import sys
from mutagen import File

MUSIC_DIR = os.environ.get("MUSIC_DIR", "./music_files")
EXTS = ('.mp3', '.m4a', '.flac', '.ogg', '.wav')


def _artist_of(path):
    try:
        audio = File(path, easy=True)
    except Exception:
        return None
    if not audio:
        return None
    return (audio.get('artist', [None]) or [None])[0]


def list_missing():
    missing = []
    for root, _, files in os.walk(MUSIC_DIR):
        for name in files:
            if not name.lower().endswith(EXTS):
                continue
            path = os.path.join(root, name)
            artist = _artist_of(path)
            if not artist or artist.strip().lower() == "unknown artist":
                missing.append(path)
    if not missing:
        print("아티스트 태그가 비어있는 파일이 없습니다.")
        return
    print(f"아티스트 태그가 없는 파일 {len(missing)}개:")
    for p in missing:
        print(f"  {p}")


def set_artist(path, artist):
    if not os.path.isfile(path):
        sys.exit(f"파일을 찾을 수 없습니다: {path}")
    audio = File(path, easy=True)
    if audio is None:
        sys.exit(f"지원하지 않는/읽을 수 없는 파일입니다: {path}")
    if audio.tags is None:
        audio.add_tags()
    audio['artist'] = artist
    audio.save()
    print(f"OK: {path}\n  artist -> {artist}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return
    if args[0] == "--list":
        list_missing()
        return
    if len(args) != 2:
        sys.exit("사용법: python scripts/set_artist.py \"<파일경로>\" \"<아티스트명>\"")
    set_artist(args[0], args[1])


if __name__ == "__main__":
    main()
