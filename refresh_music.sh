#!/bin/bash

# ==========================================
# 설정 변수
# ==========================================
MUSIC_DIR="/home/data/cyber-topgoal/music_files/"
PROJECT_DIR="/home/data/cyber-topgoal/"  # docker-compose.yml이 있는 폴더

echo "=========================================="
echo "🎵 음악 파일 인코딩 자동 정리 시작"
echo "   대상 경로: $MUSIC_DIR"
echo "=========================================="

# 1. 파일명 인코딩 변환 (CP949 -> UTF-8)
echo ""
echo "[1/3] 파일명 인코딩 변환 중 (convmv)..."
# 에러가 나더라도(이미 UTF-8인 파일 등) 스크립트가 멈추지 않게 함
convmv -f cp949 -t utf-8 --notest -r "$MUSIC_DIR"

# 2. ID3 태그 인코딩 변환 & v1 태그 삭제
echo ""
echo "[2/3] ID3 태그 인코딩 변환 중 (mid3iconv)..."
find "$MUSIC_DIR" -name "*.mp3" -print0 | xargs -0 mid3iconv -e cp949 --remove-v1

# 3. 도커 컨테이너 재시작 (라이브러리 갱신용)
# FastAPI 서버가 시작될 때만 파일을 스캔한다면 재시작이 필수입니다.
echo ""
echo "[3/3] 서비스 재시작 중 (라이브러리 갱신)..."
cd "$PROJECT_DIR"
docker compose restart

echo ""
echo "=========================================="
echo "✅ 모든 작업 완료! 이제 음악을 즐기세요."
echo "=========================================="