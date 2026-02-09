import hashlib

def generate_file_id(path: str) -> str:
    """Generates a unique ID based on the file path using SHA256."""
    # Handle paths with surrogate characters (common in Docker/Linux with non-UTF8 filenames)
    return hashlib.sha256(path.encode('utf-8', errors='replace')).hexdigest()
