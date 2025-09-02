#!/bin/bash

# FFmpeg + RNNoise 빌드 스크립트
# macOS 전용 (Intel/M1/M2 자동 감지)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}FFmpeg + RNNoise 빌드 시작${NC}"
echo -e "${BLUE}예상 소요 시간: 30-40분${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# CPU 아키텍처 확인
if [[ $(uname -m) == 'arm64' ]]; then
    ARCH="arm64"
    echo -e "${GREEN}✓ Apple Silicon (M1/M2) 감지됨${NC}"
else
    ARCH="x86_64"
    echo -e "${GREEN}✓ Intel Mac 감지됨${NC}"
fi

# 작업 디렉토리 생성
BUILD_DIR="$HOME/ffmpeg-rnnoise-build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# 1. RNNoise 빌드
echo -e "${YELLOW}[1/4] RNNoise 소스 다운로드 및 빌드...${NC}"
if [ ! -d "rnnoise" ]; then
    git clone https://github.com/xiph/rnnoise.git
fi

cd rnnoise

# 최신 버전으로 업데이트
git pull

# autogen.sh 실행 (모델 자동 다운로드)
echo "RNNoise 모델 다운로드 중..."
if ! command -v wget &> /dev/null; then
    brew install wget
fi
./autogen.sh

# configure 및 빌드
./configure --prefix="$BUILD_DIR/rnnoise-install"
make clean 2>/dev/null || true
make -j$(sysctl -n hw.ncpu)
make install

# 바이너리 모델 추출
echo -e "${YELLOW}[2/4] RNNoise 모델 추출...${NC}"
if [ -f "examples/.libs/dump_weights_blob" ]; then
    ./examples/.libs/dump_weights_blob
    if [ -f "weights_blob.bin" ]; then
        echo -e "${GREEN}✓ weights_blob.bin 생성됨${NC}"
    fi
fi

cd "$BUILD_DIR"

# 2. FFmpeg 소스 다운로드
echo -e "${YELLOW}[3/4] FFmpeg 소스 다운로드...${NC}"
if [ ! -d "ffmpeg" ]; then
    git clone --depth 1 https://github.com/FFmpeg/FFmpeg.git ffmpeg
else
    cd ffmpeg
    git pull
    cd ..
fi

cd ffmpeg

# 3. FFmpeg 컴파일
echo -e "${YELLOW}[4/4] FFmpeg 컴파일 (RNNoise 포함)...${NC}"
echo "CPU 코어 수: $(sysctl -n hw.ncpu)"

# 기존 빌드 정리
make clean 2>/dev/null || true

# configure 실행
PKG_CONFIG_PATH="$BUILD_DIR/rnnoise-install/lib/pkgconfig:$PKG_CONFIG_PATH" \
./configure \
    --prefix="$BUILD_DIR/ffmpeg-install" \
    --enable-gpl \
    --enable-nonfree \
    --enable-librnnoise \
    --extra-cflags="-I$BUILD_DIR/rnnoise-install/include" \
    --extra-ldflags="-L$BUILD_DIR/rnnoise-install/lib" \
    --extra-libs="-lrnnoise" \
    --arch="$ARCH" \
    --disable-debug \
    --enable-optimizations

# 컴파일
echo "컴파일 시작 (시간이 걸립니다)..."
make -j$(sysctl -n hw.ncpu)
make install

cd "$BUILD_DIR"

# 4. 시스템에 설치
echo ""
echo -e "${YELLOW}FFmpeg 시스템 설치...${NC}"

# 기존 FFmpeg 백업
if [ -f "/usr/local/bin/ffmpeg" ]; then
    sudo mv /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg.backup.$(date +%Y%m%d) 2>/dev/null || true
fi
if [ -f "/usr/local/bin/ffprobe" ]; then
    sudo mv /usr/local/bin/ffprobe /usr/local/bin/ffprobe.backup.$(date +%Y%m%d) 2>/dev/null || true
fi

# 새 FFmpeg 설치
sudo cp "$BUILD_DIR/ffmpeg-install/bin/ffmpeg" /usr/local/bin/
sudo cp "$BUILD_DIR/ffmpeg-install/bin/ffprobe" /usr/local/bin/

# Homebrew 경로에도 복사 (있는 경우)
if [ -d "/opt/homebrew/bin" ]; then
    sudo cp "$BUILD_DIR/ffmpeg-install/bin/ffmpeg" /opt/homebrew/bin/ffmpeg 2>/dev/null || true
    sudo cp "$BUILD_DIR/ffmpeg-install/bin/ffprobe" /opt/homebrew/bin/ffprobe 2>/dev/null || true
fi

# 5. RNNoise 모델 복사
echo -e "${YELLOW}RNNoise 모델 복사...${NC}"
ORIGINAL_DIR="$(dirname "$0")"
cd "$ORIGINAL_DIR"

mkdir -p rnnoise-models
if [ -f "$BUILD_DIR/rnnoise/weights_blob.bin" ]; then
    cp "$BUILD_DIR/rnnoise/weights_blob.bin" rnnoise-models/xiph_latest.bin
    echo -e "${GREEN}✓ xiph_latest.bin 모델 복사됨${NC}"
fi

# 6. 설치 확인
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}설치 확인${NC}"
echo -e "${BLUE}======================================${NC}"

# FFmpeg 버전 확인
echo -e "${YELLOW}FFmpeg 버전:${NC}"
ffmpeg -version | head -n 1

# RNNoise 지원 확인
echo ""
echo -e "${YELLOW}RNNoise 필터 확인:${NC}"
if ffmpeg -h filter=arnndn 2>&1 | grep -q "arnndn"; then
    echo -e "${GREEN}✓ RNNoise (arnndn) 필터 사용 가능${NC}"
    ffmpeg -h filter=arnndn | grep -A 5 "arnndn AVOptions"
else
    echo -e "${RED}✗ RNNoise 필터를 찾을 수 없습니다${NC}"
    echo "문제 해결:"
    echo "1. 스크립트를 다시 실행해보세요"
    echo "2. sudo 권한이 필요할 수 있습니다"
    exit 1
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}FFmpeg + RNNoise 빌드 완료!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "빌드 파일 위치: $BUILD_DIR"
echo "모델 파일 위치: $(pwd)/rnnoise-models/xiph_latest.bin"
echo ""