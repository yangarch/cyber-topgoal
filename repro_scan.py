import os
from app.scanner import MusicScanner

# Setup test environment
TEST_DIR = "test_music"
os.makedirs(f"{TEST_DIR}/Artist/Album", exist_ok=True)
with open(f"{TEST_DIR}/Artist/Album/test.mp3", "w") as f:
    f.write("dummy content")

print(f"Created test structure in {TEST_DIR}")

# Run scanner
scanner = MusicScanner(TEST_DIR)
scanner.scan()

# Check results
tracks = scanner.get_all_tracks()
print(f"Found {len(tracks)} tracks")
for t in tracks:
    print(f" - {t.title} ({t.path})")

# Cleanup
import shutil
shutil.rmtree(TEST_DIR)
