#!/bin/bash

# VoiceNoise 완전 자동 설치 스크립트
# macOS 전용 (Intel/M1/M2 지원)

set -e  # 에러 발생시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}VoiceNoise 완전 자동 설치 시작${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 1. Homebrew 설치 확인
echo -e "${YELLOW}[1/8] Homebrew 확인...${NC}"
if ! command -v brew &> /dev/null; then
    echo "Homebrew 설치 중..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # M1/M2 Mac의 경우 PATH 설정
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo -e "${GREEN}✓ Homebrew 이미 설치됨${NC}"
fi

# 2. 필수 도구 설치
echo -e "${YELLOW}[2/8] 필수 도구 설치...${NC}"
brew install python@3.11 git wget autoconf automake libtool pkg-config

# 3. Python 가상환경 생성
echo -e "${YELLOW}[3/8] Python 가상환경 생성...${NC}"
python3 -m venv venv
source venv/bin/activate

# 4. Python 패키지 설치
echo -e "${YELLOW}[4/8] Python 패키지 설치...${NC}"
pip install --upgrade pip
pip install Django==5.2.1
pip install librosa==0.10.1
pip install soundfile==0.12.1
pip install numpy scipy
pip install python-decouple==3.8

# 5. FFmpeg + RNNoise 빌드
echo -e "${YELLOW}[5/8] FFmpeg + RNNoise 빌드 (30-40분 소요)...${NC}"
./build_ffmpeg_rnnoise.sh

# 6. 환경 설정
echo -e "${YELLOW}[6/8] 환경 설정...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    # 랜덤 SECRET_KEY 생성
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" .env
    else
        sed -i "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" .env
    fi
    echo -e "${GREEN}✓ .env 파일 생성 및 SECRET_KEY 설정${NC}"
fi

# 7. 데이터베이스 초기화
echo -e "${YELLOW}[7/8] 데이터베이스 초기화...${NC}"
python manage.py migrate
mkdir -p logs

# 8. 설치 확인
echo -e "${YELLOW}[8/8] 설치 확인...${NC}"
echo ""

# FFmpeg RNNoise 확인
if ffmpeg -h filter=arnndn 2>&1 | grep -q "arnndn"; then
    echo -e "${GREEN}✓ FFmpeg RNNoise 설치 확인${NC}"
else
    echo -e "${RED}✗ FFmpeg RNNoise 설치 실패${NC}"
    echo "build_ffmpeg_rnnoise.sh를 다시 실행해주세요."
fi

# Python 패키지 확인
if python -c "import django, librosa, soundfile" 2>/dev/null; then
    echo -e "${GREEN}✓ Python 패키지 설치 확인${NC}"
else
    echo -e "${RED}✗ Python 패키지 설치 실패${NC}"
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}설치 완료!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "서버 실행:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "브라우저에서 접속:"
echo "  http://localhost:8000"
echo ""