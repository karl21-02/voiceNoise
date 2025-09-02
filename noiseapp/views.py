# views.py

import os
import subprocess
import uuid
import tempfile
import logging
import shutil

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render

import librosa
import soundfile as sf

# BASE_DIR 설정
BASE_DIR = settings.BASE_DIR

logger = logging.getLogger(__name__)

def index(request):
    """홈페이지 - 파일 업로드 UI"""
    return render(request, 'noiseapp/index.html')

@csrf_exempt
def separate_clicks(request):
    """
    POST: 파일 업로드(key='file' 또는 'video_file')
    1) MP4→WAV 추출
    2) RNNoise로 노이즈 제거
    3) librosa HPSS로 타격음만 분리
    4) 원본 비디오 + 타격음 오디오 재합성
    → 최종 MP4 리턴
    """
    if request.method != 'POST':
        logger.warning(f"Invalid request method: {request.method}")
        return JsonResponse({"error": "POST 메소드만 허용됩니다."}, status=405)

    # 1) 업로드 파일 검증
    f = request.FILES.get('file') or request.FILES.get('video_file')
    if not f:
        logger.error("No file provided in request")
        return JsonResponse({"error": "파일이 제공되지 않았습니다. 비디오 파일을 업로드해주세요."}, status=400)
    
    # 파일 크기 제한 (500MB)
    max_size = 500 * 1024 * 1024
    if f.size > max_size:
        logger.error(f"File too large: {f.size} bytes")
        return JsonResponse({"error": f"파일이 너무 큽니다. 최대 크기는 {max_size // (1024*1024)}MB입니다."}, status=400)
    
    # 파일 확장자 검증
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    file_ext = os.path.splitext(f.name)[1].lower()
    if file_ext not in allowed_extensions:
        logger.error(f"Invalid file extension: {file_ext}")
        return JsonResponse({"error": f"유효하지 않은 파일 형식입니다. 허용되는 형식: {', '.join(allowed_extensions)}"}, status=400)

    # 임시 디렉터리 준비
    work_dir = None
    try:
        work_dir = tempfile.mkdtemp(prefix="denoise_")
        in_mp4 = os.path.join(work_dir, f"input_{uuid.uuid4()}{file_ext}")
        
        # 파일 저장
        with open(in_mp4, 'wb') as wf:
            for chunk in f.chunks():
                wf.write(chunk)
        
        logger.info(f"Processing file: {f.name} ({f.size} bytes)")

        # 2) MP4 → WAV (mono, 48kHz)
        extracted_wav = os.path.join(work_dir, "extracted.wav")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", in_mp4,
            "-vn", "-ac", "1", "-ar", "48000",
            extracted_wav
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg extraction failed: {result.stderr}")
            return JsonResponse({
                "error": "비디오에서 오디오 추출에 실패했습니다.", 
                "details": "비디오 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다."
            }, status=400)

        # 3) 노이즈 제거 - 다단계 파이프라인
        # Stage 1: 전통적 필터로 기본 노이즈 제거
        stage1_wav = os.path.join(work_dir, "denoised_stage1.wav")
        logger.info("Stage 1: Applying traditional noise reduction filters")
        
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", extracted_wav,
            "-af", "highpass=f=100,lowpass=f=8000,anlmdn=s=7:p=0.002:r=0.002:m=15",
            stage1_wav
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"Stage 1 noise reduction failed: {result.stderr}")
            return JsonResponse({
                "error": "노이즈 제거 적용에 실패했습니다.", 
                "details": "전통적 필터 적용 중 오류가 발생했습니다."
            }, status=500)
        
        # Stage 2: RNNoise로 추가 노이즈 제거 (가능한 경우)
        denoised_wav = os.path.join(work_dir, "denoised_final.wav")
        
        # RNNoise 지원 확인 (실제 필터 목록에서 확인)
        check_rnnoise = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True
        )
        
        # RNNoise 사용 시도
        rnnoise_applied = False
        if "arnndn" in check_rnnoise.stdout:
            rnnoise_model = os.path.join(BASE_DIR, 'rnnoise-models', 'xiph_latest.bin')
            
            if os.path.exists(rnnoise_model):
                logger.info(f"Stage 2: Applying RNNoise with xiph model: {rnnoise_model}")
                result = subprocess.run([
                    "ffmpeg", "-y",
                    "-i", stage1_wav,
                    "-af", f"arnndn=m={rnnoise_model}",
                    denoised_wav
                ], capture_output=True, text=True, timeout=120)
            else:
                logger.info("Stage 2: Applying built-in RNNoise")
                result = subprocess.run([
                    "ffmpeg", "-y",
                    "-i", stage1_wav,
                    "-af", "arnndn",
                    denoised_wav
                ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                rnnoise_applied = True
                logger.info("Stage 2: RNNoise successfully applied")
            else:
                logger.warning(f"Stage 2: RNNoise failed, using Stage 1 output only: {result.stderr}")
        else:
            logger.info("Stage 2: RNNoise not available, using Stage 1 output only")
        
        # RNNoise가 실패하거나 사용 불가능한 경우 Stage 1 결과 사용
        if not rnnoise_applied:
            import shutil
            shutil.copy(stage1_wav, denoised_wav)
            logger.info("Using Stage 1 output as final denoised audio")
        
        # 최종 파일 확인
        if not os.path.exists(denoised_wav):
            logger.error("Final denoised file not created")
            return JsonResponse({
                "error": "노이즈 제거 처리 실패", 
                "details": "최종 오디오 파일 생성에 실패했습니다."
            }, status=500)

        # 4) librosa HPSS → 타격음 분리
        try:
            y, sr = librosa.load(denoised_wav, sr=None, mono=True)
            if y is None or len(y) == 0:
                raise ValueError("Audio data is empty")
            
            _, y_p = librosa.effects.hpss(y, margin=2.0)
            hits_wav = os.path.join(work_dir, "hits_only.wav")
            sf.write(hits_wav, y_p, sr)
            logger.info("HPSS separation completed successfully")
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            return JsonResponse({
                "error": "타격음 분리에 실패했습니다.", 
                "details": str(e)
            }, status=500)

        # 5) 영상 + 분리된 타격음 오디오 재합성
        out_mp4 = os.path.join(work_dir, f"output_hits_only_{uuid.uuid4()}.mp4")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", in_mp4,
            "-i", hits_wav,
            "-c:v", "copy",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            out_mp4
        ], capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg muxing failed: {result.stderr}")
            return JsonResponse({
                "error": "출력 비디오 생성에 실패했습니다.", 
                "details": "비디오와 처리된 오디오를 결합할 수 없습니다."
            }, status=500)

        # 6) 결과 파일 검증
        if not os.path.exists(out_mp4) or os.path.getsize(out_mp4) == 0:
            logger.error("Output file is empty or doesn't exist")
            return JsonResponse({"error": "출력 파일 생성에 실패했습니다."}, status=500)

        # 7) 결과 반환
        logger.info(f"Successfully processed file: {f.name}")
        response = FileResponse(
            open(out_mp4, 'rb'),
            as_attachment=True,
            filename=f"hits_only_{os.path.splitext(f.name)[0]}.mp4",
            content_type="video/mp4"
        )
        
        # 응답 후 정리를 위해 임시 경로 저장
        response['X-Temp-Dir'] = work_dir
        return response

    except subprocess.TimeoutExpired:
        logger.error("Processing timeout exceeded")
        return JsonResponse({
            "error": "처리 시간 초과.", 
            "details": "파일이 너무 크거나 복잡하여 제한 시간 내에 처리할 수 없습니다."
        }, status=408)
    
    except OSError as e:
        logger.error(f"System error: {str(e)}")
        return JsonResponse({
            "error": "시스템 오류가 발생했습니다.", 
            "details": "FFmpeg가 설치되지 않았거나 접근할 수 없습니다."
        }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({
            "error": "예기치 않은 오류가 발생했습니다.", 
            "details": str(e)
        }, status=500)

    finally:
        # 임시 디렉터리 정리
        if work_dir and os.path.exists(work_dir):
            try:
                shutil.rmtree(work_dir)
                logger.debug(f"Cleaned up temp directory: {work_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {work_dir}: {e}")
