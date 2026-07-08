import os
import glob
import base64
from mutagen import File
from mutagen.id3 import ID3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from typing import Dict, Optional, Tuple
from .models import Track
from .utils import generate_file_id

MUSIC_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']


def extract_cover(path: str) -> Optional[Tuple[bytes, str]]:
    """Extract embedded album art from an audio file.

    Returns (image_bytes, mime_type) or None if no embedded art exists.
    Supports mp3 (APIC), m4a/mp4 (covr), flac (pictures), ogg (metadata_block_picture).
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.mp3':
            tags = ID3(path)
            for key in tags.keys():
                if key.startswith('APIC'):
                    apic = tags[key]
                    return apic.data, (apic.mime or 'image/jpeg')

        elif ext in ('.m4a', '.mp4', '.aac'):
            mp4 = MP4(path)
            covers = mp4.tags.get('covr') if mp4.tags else None
            if covers:
                cover = covers[0]
                mime = 'image/png' if cover.imageformat == MP4Cover.FORMAT_PNG else 'image/jpeg'
                return bytes(cover), mime

        elif ext == '.flac':
            flac = FLAC(path)
            if flac.pictures:
                pic = flac.pictures[0]
                return pic.data, (pic.mime or 'image/jpeg')

        elif ext == '.ogg':
            audio = File(path)
            b64 = audio.get('metadata_block_picture') if audio else None
            if b64:
                pic = Picture(base64.b64decode(b64[0]))
                return pic.data, (pic.mime or 'image/jpeg')
    except Exception:
        pass
    return None

class MusicScanner:
    def __init__(self, music_dir: str):
        self.music_dir = music_dir
        self.library: Dict[str, Track] = {}

    def scan(self):
        print(f"Scanning music directory: {self.music_dir}")
        self.library.clear()
        
        # Walk through directory
        for root, _, files in os.walk(self.music_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in MUSIC_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    try:
                        self._process_file(full_path)
                    except Exception as e:
                        print(f"Error processing {full_path}: {e}")
        
        print(f"Scanned {len(self.library)} tracks.")

    def _sanitize(self, s: str) -> str:
        """Sanitizes a string to be safe for JSON encoding (removes surrogates)."""
        if s is None:
            return ""
        return s.encode('utf-8', 'replace').decode('utf-8')

    def _fix_mojibake(self, s: Optional[str]) -> Optional[str]:
        """Repair Korean tags stored as CP949 but mis-decoded as latin-1.

        e.g. '¸ß½ÃÄÚÇà' -> '멕시코행'. Conservative: only converts when the
        latin-1 high bytes re-decode into actual Hangul, so legitimate Latin
        titles (Café, Motörhead, ...) are left untouched.
        """
        if not s:
            return s
        # Already has Hangul/CJK -> nothing to repair.
        if any('가' <= ch <= '힣' or '一' <= ch <= '鿿' for ch in s):
            return s
        # No latin-1 high bytes -> not this kind of corruption.
        if not any('' <= ch <= 'ÿ' for ch in s):
            return s
        try:
            repaired = s.encode('latin-1').decode('cp949')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
        # Accept only if the result actually contains Hangul.
        if any('가' <= ch <= '힣' for ch in repaired):
            return repaired
        return s

    def _process_file(self, path: str):
        audio = File(path, easy=True)
        id3_tags = None
        
        if path.lower().endswith('.mp3'):
             try:
                 id3_tags = ID3(path)
             except:
                 pass

        title = None
        artist = None
        album = None
        duration = 0.0

        filename = os.path.basename(path)
        folder = os.path.basename(os.path.dirname(path))
        
        # Metadata extraction
        if audio:
            title = self._fix_mojibake(audio.get('title', [None])[0])
            artist = self._fix_mojibake(audio.get('artist', [None])[0])
            album = self._fix_mojibake(audio.get('album', [None])[0])
            duration = audio.info.length if hasattr(audio, 'info') else 0.0
        
        # Fallbacks
        if not title:
            title = os.path.splitext(filename)[0]
        if not artist:
            artist = "Unknown Artist"
        if not album:
            album = folder

        file_id = generate_file_id(path)
        
        # Check for cover art
        has_cover = False
        if id3_tags:
            for key in id3_tags.keys():
                if key.startswith("APIC"):
                     has_cover = True
                     break
        
        # If no embedded cover, check folder for images
        if not has_cover:
             folder_path = os.path.dirname(path)
             for img in ['cover.jpg', 'folder.jpg', 'cover.png', 'folder.png']:
                 if os.path.exists(os.path.join(folder_path, img)):
                     has_cover = True # Use a flag that we will handle in the API logic
                     break

        # Sanitize strings to avoid UnicodeEncodeError in JSON response
        # BUT keep path raw for file access. We will exclude it from API response.
        track = Track(
            id=file_id,
            title=self._sanitize(title),
            artist=self._sanitize(artist),
            album=self._sanitize(album),
            duration=duration,
            path=path,
            has_cover=has_cover
        )
        self.library[file_id] = track

    def get_track(self, file_id: str) -> Optional[Track]:
        return self.library.get(file_id)

    def get_all_tracks(self):
        return list(self.library.values())
