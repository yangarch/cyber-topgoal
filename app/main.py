import os
import mimetypes
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from .scanner import MusicScanner
from .database import init_db, create_comment, get_comments
from .models import Track, PublicTrack, Comment, CommentCreate

MUSIC_DIR = os.environ.get("MUSIC_DIR", "/music")
scanner = MusicScanner(MUSIC_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Cyber TopGoal...")
    init_db()
    scanner.scan()
    yield
    # Shutdown
    print("Shutting down Cyber TopGoal...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/library", response_model=list[PublicTrack])
async def get_library():
    # Convert internal Track to PublicTrack
    tracks = scanner.get_all_tracks()
    return [
        PublicTrack(
            id=t.id,
            title=t.title,
            artist=t.artist,
            album=t.album,
            duration=t.duration,
            has_cover=t.has_cover
        ) for t in tracks
    ]

@app.post("/api/library/scan")
async def scan_library():
    scanner.scan()
    return {"message": "Scan completed", "tracks": len(scanner.library)}

@app.get("/api/comments", response_model=list[Comment])
async def read_comments():
    return get_comments()

@app.post("/api/comments", response_model=Comment)
async def post_comment(comment: CommentCreate):
    return create_comment(comment)

@app.get("/api/stream/{file_id}")
async def stream_audio(file_id: str, range: Optional[str] = Header(None)):
    track = scanner.get_track(file_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    file_path = track.path
    file_size = os.path.getsize(file_path)
    
    start = 0
    end = file_size - 1
    
    if range:
        try:
            start_str, end_str = range.replace("bytes=", "").split("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else end
        except ValueError:
             pass # Invalid range header, ignore

    # Calculate content length
    content_length = (end - start) + 1
    
    def iterfile():
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_read = 0
            while bytes_read < content_length:
                 chunk_size = min(1024 * 64, content_length - bytes_read) # 64KB chunks
                 data = f.read(chunk_size)
                 if not data:
                     break
                 yield data
                 bytes_read += len(data)

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": mimetypes.guess_type(file_path)[0] or "application/octet-stream",
    }
    
    return StreamingResponse(iterfile(), status_code=206, headers=headers)

@app.get("/api/cover/{file_id}")
async def get_cover(file_id: str):
    track = scanner.get_track(file_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Try to extract embedded art
    # Simplified: For now, if scanner says has_cover, we try to find a file.
    # A real robust implementation would extract ID3 APIC frames. 
    # Here checking for folder images is easier for MVP.
    
    folder_path = os.path.dirname(track.path)
    for img in ['cover.jpg', 'folder.jpg', 'cover.png', 'folder.png']:
         img_path = os.path.join(folder_path, img)
         if os.path.exists(img_path):
             return FileResponse(img_path)
    
    # Placeholder
    return FileResponse("static/placeholder.png")

