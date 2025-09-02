#!/bin/bash

# FFmpeg를 RNNoise와 함께 컴파일하는 스크립트
# macOS와 Linux에서 동작

echo "FFmpeg with RNNoise 빌드 스크립트"
echo "=================================="

# 작업 디렉토리 설정
WORK_DIR="$PWD/ffmpeg-build"
PREFIX="$WORK_DIR/install"

mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 1. RNNoise 빌드
echo "1. RNNoise 빌드 중..."
if [ ! -d "rnnoise" ]; then
    git clone https://github.com/xiph/rnnoise.git
fi

cd rnnoise
./autogen.sh
./configure --prefix="$PREFIX"
make
make install
cd ..

# 2. FFmpeg 소스 다운로드
echo "2. FFmpeg 소스 다운로드 중..."
if [ ! -d "ffmpeg" ]; then
    git clone https://github.com/FFmpeg/FFmpeg.git ffmpeg
fi

cd ffmpeg

# 3. FFmpeg 컴파일 (RNNoise 포함)
echo "3. FFmpeg 컴파일 중..."
PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" \
./configure \
    --prefix="$PREFIX" \
    --enable-gpl \
    --enable-version3 \
    --enable-nonfree \
    --enable-librnnoise \
    --extra-cflags="-I$PREFIX/include" \
    --extra-ldflags="-L$PREFIX/lib" \
    --extra-libs="-lrnnoise"

make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu)
make install

echo ""
echo "=================================="
echo "빌드 완료!"
echo ""
echo "FFmpeg 실행:"
echo "  $PREFIX/bin/ffmpeg"
echo ""
echo "시스템 전체에서 사용하려면:"
echo "  export PATH=\"$PREFIX/bin:\$PATH\""
echo ""
echo "또는 시스템에 설치:"
echo "  sudo cp $PREFIX/bin/ffmpeg /usr/local/bin/"
echo "  sudo cp $PREFIX/bin/ffprobe /usr/local/bin/"
echo ""
echo "RNNoise 필터 테스트:"
echo "  $PREFIX/bin/ffmpeg -h filter=arnndn"