# API 문서

## 개요

VoiceNoise API는 비디오 파일의 오디오를 처리하여 노이즈를 제거하고 타격음만을 분리하는 RESTful API입니다.

## Base URL

```
http://localhost:8000
```

## 인증

현재 인증이 필요하지 않습니다. (프로덕션에서는 인증 구현 필요)

## 엔드포인트

### 1. 타격음 분리

비디오 파일에서 타격음만을 분리하여 새로운 비디오 파일을 생성합니다.

#### Endpoint

```
POST /separate_clicks/
```

#### Request

##### Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| Content-Type | multipart/form-data | Yes | 파일 업로드를 위한 content type |

##### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes* | 업로드할 비디오 파일 |
| video_file | File | Yes* | 업로드할 비디오 파일 (file 대신 사용 가능) |

*Note: `file` 또는 `video_file` 중 하나는 필수

##### File Requirements

- **최대 크기**: 500MB
- **지원 형식**: MP4, AVI, MOV, MKV
- **권장 형식**: MP4 (H.264 코덱)

#### Response

##### Success Response (200 OK)

```
Content-Type: video/mp4
Content-Disposition: attachment; filename="hits_only_[original_filename].mp4"
```

파일이 직접 다운로드됩니다.

##### Error Responses

###### 400 Bad Request

파일이 제공되지 않았을 때:
```json
{
    "error": "파일이 제공되지 않았습니다. 비디오 파일을 업로드해주세요."
}
```

파일이 너무 클 때:
```json
{
    "error": "파일이 너무 큽니다. 최대 크기는 500MB입니다."
}
```

지원하지 않는 파일 형식:
```json
{
    "error": "유효하지 않은 파일 형식입니다. 허용되는 형식: .mp4, .avi, .mov, .mkv"
}
```

오디오 추출 실패:
```json
{
    "error": "비디오에서 오디오 추출에 실패했습니다.",
    "details": "비디오 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다."
}
```

###### 405 Method Not Allowed

```json
{
    "error": "POST 메소드만 허용됩니다."
}
```

###### 408 Request Timeout

```json
{
    "error": "처리 시간 초과.",
    "details": "파일이 너무 크거나 복잡하여 제한 시간 내에 처리할 수 없습니다."
}
```

###### 500 Internal Server Error

노이즈 제거 실패:
```json
{
    "error": "노이즈 제거 적용에 실패했습니다.",
    "details": "RNNoise 필터가 실패했습니다. ffmpeg가 RNNoise 지원과 함께 컴파일되었는지 확인해주세요."
}
```

타격음 분리 실패:
```json
{
    "error": "타격음 분리에 실패했습니다.",
    "details": "[구체적인 에러 메시지]"
}
```

비디오 생성 실패:
```json
{
    "error": "출력 비디오 생성에 실패했습니다.",
    "details": "비디오와 처리된 오디오를 결합할 수 없습니다."
}
```

시스템 오류:
```json
{
    "error": "시스템 오류가 발생했습니다.",
    "details": "FFmpeg가 설치되지 않았거나 접근할 수 없습니다."
}
```

#### 사용 예제

##### cURL

```bash
# 기본 요청
curl -X POST http://localhost:8000/separate_clicks/ \
     -F "file=@/path/to/video.mp4" \
     -o output.mp4

# 진행 상황 표시
curl -X POST http://localhost:8000/separate_clicks/ \
     -F "file=@/path/to/video.mp4" \
     --progress-bar \
     -o output.mp4
```

##### Python (requests)

```python
import requests

def process_video(input_path, output_path):
    """
    비디오 파일을 처리하여 타격음만 분리
    """
    url = "http://localhost:8000/separate_clicks/"
    
    with open(input_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as out:
            out.write(response.content)
        print(f"처리 완료: {output_path}")
        return True
    else:
        print(f"오류 발생: {response.json()}")
        return False

# 사용 예
process_video('input.mp4', 'output.mp4')
```

##### JavaScript (Fetch API)

```javascript
async function processVideo(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('http://localhost:8000/separate_clicks/', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // 다운로드 링크 생성
            const a = document.createElement('a');
            a.href = url;
            a.download = 'output.mp4';
            a.click();
            
            URL.revokeObjectURL(url);
            return true;
        } else {
            const error = await response.json();
            console.error('오류:', error);
            return false;
        }
    } catch (error) {
        console.error('네트워크 오류:', error);
        return false;
    }
}

// HTML input element에서 사용
document.getElementById('fileInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        processVideo(file);
    }
});
```

##### HTML Form

```html
<!DOCTYPE html>
<html>
<head>
    <title>비디오 처리</title>
</head>
<body>
    <h1>타격음 분리 서비스</h1>
    <form action="http://localhost:8000/separate_clicks/" 
          method="POST" 
          enctype="multipart/form-data">
        <label for="file">비디오 파일 선택:</label>
        <input type="file" 
               name="file" 
               id="file" 
               accept=".mp4,.avi,.mov,.mkv" 
               required>
        <button type="submit">처리 시작</button>
    </form>
</body>
</html>
```

## 처리 과정 상세

1. **파일 검증**: 파일 크기, 형식 확인
2. **오디오 추출**: 48kHz, 모노 오디오로 변환
3. **노이즈 제거**: RNNoise 모델 적용
4. **타격음 분리**: HPSS 알고리즘으로 percussive 성분 추출
5. **비디오 재생성**: 원본 비디오 + 처리된 오디오

## 성능 고려사항

- **처리 시간**: 파일 크기에 따라 30초~3분
- **메모리 사용**: 파일 크기의 약 3-4배
- **CPU 사용률**: 처리 중 높은 CPU 사용
- **동시 처리**: 현재 동시 처리 제한 없음 (프로덕션에서는 큐 시스템 권장)

## 제한사항

- 최대 파일 크기: 500MB
- 처리 타임아웃: 오디오 추출 120초, 비디오 합성 180초
- 지원 코덱: FFmpeg가 지원하는 모든 코덱
- 출력 형식: MP4 (H.264 비디오 코덱 유지)

## 문제 해결

### 일반적인 문제

1. **"FFmpeg가 설치되지 않았거나 접근할 수 없습니다"**
   - FFmpeg 설치 확인: `ffmpeg -version`
   - PATH 환경변수 확인

2. **"RNNoise 필터가 실패했습니다"**
   - FFmpeg RNNoise 지원 확인: `ffmpeg -h filter=arnndn`
   - RNNoise 모델 파일 존재 확인

3. **"처리 시간 초과"**
   - 더 작은 파일로 테스트
   - 서버 타임아웃 설정 증가 고려

### 로그 확인

```bash
# Django 로그
tail -f logs/django.log

# 특정 에러 검색
grep "ERROR" logs/django.log
```

## 버전 정보

- API Version: 1.0.0
- Last Updated: 2024

## 지원

문제가 발생하면 로그를 확인하고 GitHub Issues에 보고해주세요.