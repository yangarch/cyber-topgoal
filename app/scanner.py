import os
import glob
from mutagen import File
from mutagen.id3 import ID3
from typing import Dict, Optional
from .models import Track
from .utils import generate_file_id

MUSIC_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']

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
            title = audio.get('title', [None])[0]
            artist = audio.get('artist', [None])[0]
            album = audio.get('album', [None])[0]
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

        track = Track(
            id=file_id,
            title=title,
            artist=artist,
            album=album,
            duration=duration,
            path=path,
            has_cover=has_cover
        )
        self.library[file_id] = track

    def get_track(self, file_id: str) -> Optional[Track]:
        return self.library.get(file_id)

    def get_all_tracks(self):
        return list(self.library.values())
