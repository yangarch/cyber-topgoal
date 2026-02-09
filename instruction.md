# Cyber TopGoal

# Project Goal
Python FastAPI를 사용하여 개인 소장용 음악 스트리밍 웹 서비스를 구축한다.
Docker Compose로 배포하며, 로컬 폴더(Artist/Album/Track 구조)를 마운트하여 스트리밍한다.
친구들과의 추억을 공유하는 용도이므로 **방명록(Guestbook)** 기능과 모바일 친화적인 Dark Mode UI를 제공한다.

# Tech Stack
- Backend: Python 3.11+, FastAPI, Uvicorn
- Database: SQLite (Built-in, for Guestbook persistence)
- Audio Processing: `mutagen` (for Metadata & ID3 tags)
- Frontend: HTML5, Vanilla JS (No build steps), Simple CSS (Dark mode)
- Deployment: Docker, Docker Compose

# Core Features & Logic

1. **File System Scanning & Metadata**
   - 서버 시작 시 `MUSIC_DIR` (환경변수, 기본값 `/music`) 하위의 모든 오디오 파일(.mp3, .wav 등)을 재귀적으로 스캔.
   - **Metadata Logic:**
     1. ID3 태그 (Title, Artist, Album) 우선.
     2. 태그 부재 시 파일명을 Title, 폴더명을 Album/Artist로 사용.
   - **Album Art:**
     1. 파일 내장 이미지 -> 폴더 내 `cover.jpg`, `folder.jpg` 순으로 탐색.
     2. 없으면 기본 Placeholder 사용.
   - 데이터는 서버 시작 시 메모리에 캐싱하여 빠른 응답 보장.

2. **Audio Streaming (Performance Critical)**
   - 대용량 파일(WAV) 및 탐색(Seeking) 지원을 위해 **HTTP Range Request**를 반드시 구현한다.
   - `StreamingResponse`와 generator를 사용하여 청크 단위 전송.

3. **Guestbook (방명록)**
   - **DB:** `sqlite3`를 사용하여 `comments.db` 파일에 저장 (Volume 마운트 필요).
   - **Schema:** `id`, `nickname`, `content`, `created_at`.
   - **UI:** 플레이어 하단에 심플한 댓글 목록과 입력 폼(닉네임/내용) 배치. 별도 로그인 없이 작성 가능.

4. **Playback Logic (Shuffle & Queue)**
   - **Frontend Queue:** '체크'된 곡들만으로 재생 큐 구성. (LocalStorage에 체크 상태 저장 권장)
   - **Smart Shuffle:** 피셔-예이츠 알고리즘 등으로, 큐의 모든 곡을 1회 순회하기 전까지 중복 재생 금지.
   - **UI Controls:** 재생/일시정지, 이전/다음, 볼륨, 프로그레스 바.

# API Structure
- `GET /api/library`: 전체 곡 리스트 (JSON)
- `GET /api/stream/{file_id}`: 스트리밍 (Range Header 지원)
- `GET /api/cover/{file_id}`: 커버 이미지
- `GET /api/comments`: 방명록 목록 조회
- `POST /api/comments`: 방명록 작성
- `GET /`: 메인 페이지 (SPA 형태)

# Docker Configuration
- `Dockerfile`: python:slim 기반.
- `docker-compose.yml`:
  - Port: 8000
  - Volumes:
    - `./music_files:/music` (음원 폴더)
    - `./data:/data` (방명록 DB 파일 저장용)