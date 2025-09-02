# views.py

import os
import subprocess
import uuid
import tempfile

from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import librosa
import soundfile as sf

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
        return JsonResponse({"error": "Only POST allowed."}, status=405)

    # 1) 업로드 파일 저장
    f = request.FILES.get('file') or request.FILES.get('video_file')
    if not f:
        return JsonResponse({"error": "No file provided"}, status=400)

    # 임시 디렉터리 준비
    work_dir = tempfile.mkdtemp(prefix="denoise_")
    in_mp4 = os.path.join(work_dir, f"{uuid.uuid4()}.mp4")
    with open(in_mp4, 'wb') as wf:
        for chunk in f.chunks():
            wf.write(chunk)

    try:
        # 2) MP4 → WAV (mono, 48kHz)
        extracted_wav = os.path.join(work_dir, "extracted.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", in_mp4,
            "-vn", "-ac", "1", "-ar", "48000",
            extracted_wav
        ], check=True)

        # 3) RNNoise 노이즈 제거
        denoised_wav = os.path.join(work_dir, "denoised.wav")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", extracted_wav,
            "-af", "arnndn",
            denoised_wav
        ], check=True)

        # 4) librosa HPSS → 타격음 분리
        y, sr = librosa.load(denoised_wav, sr=None, mono=True)
        _, y_p = librosa.effects.hpss(y)
        hits_wav = os.path.join(work_dir, "hits_only.wav")
        sf.write(hits_wav, y_p, sr)

        # 5) 영상 + 분리된 타격음 오디오 재합성
        out_mp4 = os.path.join(work_dir, "output_hits_only.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", in_mp4,
            "-i", hits_wav,
            "-c:v", "copy",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            out_mp4
        ], check=True)

        # 6) 결과 반환
        return FileResponse(
            open(out_mp4, 'rb'),
            as_attachment=True,
            filename="hits_only.mp4",
            content_type="video/mp4"
        )

    except subprocess.CalledProcessError as e:
        return JsonResponse({"error": f"ffmpeg error: {e}"}, status=500)

    finally:
        # temp cleanup
        for fn in os.listdir(work_dir):
            try:
                os.remove(os.path.join(work_dir, fn))
            except:
                pass
        os.rmdir(work_dir)
