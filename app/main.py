import os
import mimetypes
from fastapi import FastAPI, Request, Header, HTTPException, Depends, Form
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from .scanner import MusicScanner, extract_cover
from .database import init_db, create_comment, get_comments, increment_play_count, increment_finish_count, get_all_track_stats
from .models import Track, PublicTrack, Comment, CommentCreate
from . import auth

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

# 인증 없이 접근 가능한 경로 (로그인 화면, 정적 리소스, 헬스체크 등)
PUBLIC_PATHS = ("/login", "/logout", "/static", "/health", "/favicon.ico")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # ACCESS_PASSWORD 가 설정돼 있을 때만 인증을 적용한다.
    if not auth.AUTH_ENABLED:
        return await call_next(request)

    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/static"):
        return await call_next(request)

    if auth.verify_token(request.cookies.get(auth.COOKIE_NAME)):
        return await call_next(request)

    # 인증되지 않은 요청: API/스트리밍은 401, 페이지 요청은 로그인으로 리다이렉트
    if path.startswith("/api"):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": False})


@app.post("/login")
async def login_submit(request: Request, password: str = Form("")):
    if auth.check_password(password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key=auth.COOKIE_NAME,
            value=auth.make_token(),
            max_age=auth.COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=auth.COOKIE_SECURE,
        )
        return response
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": True}, status_code=401
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(auth.COOKIE_NAME)
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/library", response_model=list[PublicTrack])
async def get_library():
    # Convert internal Track to PublicTrack
    tracks = scanner.get_all_tracks()
    stats = get_all_track_stats()
    
    return [
        PublicTrack(
            id=t.id,
            title=t.title,
            artist=t.artist,
            album=t.album,
            duration=t.duration,
            has_cover=t.has_cover,
            play_count=stats.get(t.id, {}).get('play', 0),
            finish_count=stats.get(t.id, {}).get('finish', 0)
        ) for t in tracks
    ]

@app.post("/api/library/scan")
async def scan_library():
    scanner.scan()
    return {"message": "Scan completed", "tracks": len(scanner.library)}

@app.post("/api/track/{file_id}/play")
async def track_play(file_id: str):
    increment_play_count(file_id)
    return {"status": "ok"}

@app.post("/api/track/{file_id}/finish")
async def track_finish(file_id: str):
    increment_finish_count(file_id)
    return {"status": "ok"}

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

    cache_headers = {"Cache-Control": "public, max-age=86400"}

    # 1) Embedded album art (mp3 / m4a / flac / ogg)
    cover = extract_cover(track.path)
    if cover:
        data, mime = cover
        return Response(content=data, media_type=mime, headers=cache_headers)

    # 2) Fallback: an image file sitting in the album folder
    folder_path = os.path.dirname(track.path)
    for img in ['cover.jpg', 'folder.jpg', 'cover.png', 'folder.png']:
         img_path = os.path.join(folder_path, img)
         if os.path.exists(img_path):
             return FileResponse(img_path, headers=cache_headers)

    # 3) Default cover
    return FileResponse("static/default.jpeg", headers=cache_headers)

