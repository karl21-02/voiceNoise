#!/usr/bin/env python
"""
RNNoise 모델 다운로드 스크립트
GitHub에서 RNNoise 모델을 다운로드합니다.
"""

import os
import urllib.request
import sys

def download_models():
    # 모델 저장 디렉토리 생성
    models_dir = "rnnoise-models"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"디렉토리 생성: {models_dir}")
    
    # 다운로드할 모델 목록 (GregorR의 rnnoise-models 저장소에서)
    models = {
        "cb.rnnn": "https://raw.githubusercontent.com/GregorR/rnnoise-models/master/cb.rnnn",
        "lq.rnnn": "https://raw.githubusercontent.com/GregorR/rnnoise-models/master/lq.rnnn",
        "mp.rnnn": "https://raw.githubusercontent.com/GregorR/rnnoise-models/master/mp.rnnn",
        "sh.rnnn": "https://raw.githubusercontent.com/GregorR/rnnoise-models/master/sh.rnnn",
    }
    
    print("RNNoise 모델 다운로드 시작...")
    print("=" * 50)
    
    for model_name, url in models.items():
        model_path = os.path.join(models_dir, model_name)
        
        if os.path.exists(model_path):
            print(f"✓ {model_name} - 이미 존재함")
            continue
        
        try:
            print(f"다운로드 중: {model_name}...", end=" ")
            urllib.request.urlretrieve(url, model_path)
            print("완료!")
        except Exception as e:
            print(f"실패: {e}")
            continue
    
    print("=" * 50)
    print("모델 다운로드 완료!")
    print("\n사용 가능한 모델:")
    print("- cb.rnnn: 일반적인 용도 (기본)")
    print("- lq.rnnn: 낮은 품질 오디오용")
    print("- mp.rnnn: 음악/팟캐스트용")
    print("- sh.rnnn: 음성 중심")
    
    # 기본 모델 설정 안내
    print("\n기본 모델은 'cb.rnnn'으로 설정되어 있습니다.")
    print("다른 모델을 사용하려면 views.py의 rnnoise_model 경로를 수정하세요.")

if __name__ == "__main__":
    try:
        download_models()
    except KeyboardInterrupt:
        print("\n다운로드가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)