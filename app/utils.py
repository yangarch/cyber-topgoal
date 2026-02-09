import hashlib

def generate_file_id(path: str) -> str:
    """Generates a unique ID based on the file path using SHA256."""
    return hashlib.sha256(path.encode('utf-8')).hexdigest()
