import zlib
import struct
import os

def create_placeholder():
    # Ensure static directory exists
    os.makedirs('static', exist_ok=True)
    
    target = 'static/placeholder.png'
    print(f"Creating {target}...")
    
    # 1x1 Red Pixel PNG
    w, h = 100, 100
    
    # PNG Signature
    png_sig = b'\x89PNG\r\n\x1a\n'
    
    # IHDR Chunk
    ihdr_data = struct.pack('>2I5B', w, h, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + ihdr_crc.to_bytes(4, 'big')
    
    # IDAT Chunk (Image Data)
    # Simple red pixel repeated? No, just black/transparent for now or simple noise
    # Let's make it a simple gray block
    raw_data = b'\x00' + (b'\xcc\xcc\xcc\xff' * w * h) # Gray
    compressed_data = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed_data)
    idat = struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data + idat_crc.to_bytes(4, 'big')
    
    # IEND Chunk
    iend_crc = zlib.crc32(b'IEND')
    iend = struct.pack('>I', 0) + b'IEND' + iend_crc.to_bytes(4, 'big')
    
    with open(target, 'wb') as f:
        f.write(png_sig + ihdr + idat + iend)
        
    print(f"Successfully created {target}")
    print(f"File size: {os.path.getsize(target)} bytes")

if __name__ == '__main__':
    create_placeholder()
