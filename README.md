# VoiceNoise - 비디오 노이즈 제거 & 타격음 분리

> 비디오에서 깨끗한 타격음만 추출하는 AI 기반 오디오 처리 서비스

## 빠른 시작 (5분 설치)

**아무것도 설치되지 않은 macOS에서 완벽하게 작동하도록 설정합니다.**

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/voicenoise.git
cd voicenoise

# 2. 실행 권한 부여
chmod +x setup_complete.sh build_ffmpeg_rnnoise.sh

# 3. 자동 설치 실행 (30-40분 소요)
./setup_complete.sh

# 4. 서버 실행
source venv/bin/activate
python manage.py runserver

# 5. 브라우저에서 접속
# http://localhost:8000
```

**완료!** 이제 RNNoise Stage 2까지 완벽하게 작동합니다.

---

## 📋 시스템 요구사항

### 최소 요구사항
- **OS**: macOS 10.15 이상 (Intel/M1/M2 지원)
- **메모리**: 8GB RAM
- **저장공간**: 5GB 여유 공간
- **Python**: 3.8 이상

### 자동으로 설치되는 항목
- Homebrew (패키지 관리자)
- Python 3.11
- FFmpeg (RNNoise 포함 커스텀 빌드)
- Django 및 필수 Python 패키지
- RNNoise 최신 모델

---

## 🔧 수동 설치 (단계별)

### Step 1: 기본 도구 설치

```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 필수 패키지 설치
brew install python@3.11 git wget autoconf automake libtool pkg-config
```

### Step 2: FFmpeg + RNNoise 빌드 (필수!)

**⚠️ 중요: 일반 FFmpeg는 RNNoise를 지원하지 않습니다. 반드시 빌드해야 합니다.**

```bash
# 빌드 스크립트 실행 (30-40분 소요)
chmod +x build_ffmpeg_rnnoise.sh
./build_ffmpeg_rnnoise.sh
```

빌드 과정:
1. xiph/rnnoise 최신 소스 다운로드
2. RNNoise 라이브러리 컴파일
3. FFmpeg 소스 다운로드
4. FFmpeg를 RNNoise와 함께 컴파일
5. 시스템에 설치 및 모델 추출

### Step 3: Python 환경 설정

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: 프로젝트 설정

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에서 SECRET_KEY 변경 (자동 생성됨)

# 데이터베이스 초기화
python manage.py migrate

# 로그 디렉토리 생성
mkdir -p logs
```

### Step 5: 설치 확인

```bash
# RNNoise 지원 확인 (필수!)
ffmpeg -h filter=arnndn

# 출력에 다음이 표시되어야 함:
# Filter arnndn
#   Apply Recurrent Neural Network for audio denoising.
```

---

## 🎯 사용 방법

### 웹 인터페이스 사용

1. 서버 실행:
```bash
source venv/bin/activate
python manage.py runserver
```

2. 브라우저에서 `http://localhost:8000` 접속

3. 비디오 파일 업로드 (최대 500MB)
   - 지원 형식: MP4, AVI, MOV, MKV
   - 드래그 & 드롭 또는 클릭하여 선택

4. 처리 완료 후 자동 다운로드

### API 사용

```bash
# cURL 예제
curl -X POST http://localhost:8000/separate_clicks/ \
     -F "file=@video.mp4" \
     -o output.mp4
```

```python
# Python 예제
import requests

with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/separate_clicks/',
        files={'file': f}
    )
    
if response.status_code == 200:
    with open('output.mp4', 'wb') as out:
        out.write(response.content)
```

---

## 🔬 처리 과정 (파이프라인)

```
비디오 업로드
    ↓
오디오 추출 (48kHz, Mono)
    ↓
Stage 1: 전통적 노이즈 제거
  • Highpass Filter (100Hz↑)
  • Lowpass Filter (8000Hz↓)
  • ANLMDN (적응형 노이즈 제거)
    ↓
Stage 2: RNNoise 딥러닝 노이즈 제거
  • xiph/rnnoise 최신 모델
  • 실시간 음성/노이즈 분리
    ↓
Stage 3: HPSS 타격음 분리
  • Harmonic 성분 제거
  • Percussive 성분만 추출
    ↓
비디오 재합성
    ↓
결과 다운로드
```

---

## ⚠️ 문제 해결

### 1. "arnndn filter not found" 오류

**원인**: FFmpeg가 RNNoise 없이 설치됨

**해결**:
```bash
# FFmpeg 재빌드
./build_ffmpeg_rnnoise.sh

# 확인
ffmpeg -h filter=arnndn
```

### 2. "command not found: brew" 오류

**해결**:
```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# M1/M2 Mac인 경우 PATH 추가
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### 3. Python 패키지 설치 실패

**해결**:
```bash
# pip 업그레이드
pip install --upgrade pip setuptools wheel

# 개별 설치
pip install numpy==1.24.3
pip install scipy==1.10.1
pip install librosa --no-cache-dir
```

### 4. 서버 실행 오류

**해결**:
```bash
# 가상환경 재활성화
deactivate
source venv/bin/activate

# 마이그레이션 재실행
python manage.py migrate

# 포트 변경 (8000이 사용 중인 경우)
python manage.py runserver 8080
```

---

## 📁 프로젝트 구조

```
voicenoise/
├── setup_complete.sh        # 🚀 완전 자동 설치 스크립트
├── build_ffmpeg_rnnoise.sh  # 🔧 FFmpeg+RNNoise 빌드
├── manage.py                # Django 관리
├── requirements.txt         # Python 패키지 목록
├── .env.example            # 환경 변수 템플릿
│
├── voiceNoise/             # Django 설정
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── noiseapp/               # 메인 애플리케이션
│   ├── views.py           # 핵심 처리 로직 (파이프라인)
│   └── templates/         # 웹 UI
│
├── rnnoise-models/         # RNNoise 모델
│   └── xiph_latest.bin    # xiph 최신 모델
│
├── logs/                   # 로그 파일
└── venv/                   # Python 가상환경
```

---

## 🔒 보안 설정 (프로덕션)

```python
# .env 파일 수정
DEBUG=False
SECRET_KEY=your-secure-random-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CSRF 보호 활성화
# views.py에서 @csrf_exempt 제거
```

---

## 📊 성능 정보

- **처리 시간**: 1분 비디오 기준 약 20-30초
- **메모리 사용**: 파일 크기의 3-4배
- **CPU 사용**: 멀티코어 활용 (병렬 처리)
- **품질**: Stage 1+2 적용시 노이즈 90% 이상 제거

---

## 🆘 지원

### 로그 확인
```bash
tail -f logs/django.log
```

### 시스템 상태
```bash
# FFmpeg 버전
ffmpeg -version

# Python 패키지
pip list

# 디스크 공간
df -h
```
