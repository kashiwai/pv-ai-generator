#!/usr/bin/env python3
"""
Google Vertex AI Imagen Video APIテスト
"""

import os
import json
import requests
import time
from pathlib import Path

def test_google_imagen_video():
    """Google Vertex AI Imagen Videoテスト"""
    
    print("=" * 60)
    print("🎬 Google Vertex AI Imagen Video テスト")
    print("=" * 60)
    
    # プロジェクト設定
    project_id = "medent-9167b"
    location = "us-central1"
    
    # Service Account認証
    json_path = Path('/tmp/google-service-account.json')
    if not json_path.exists():
        print("❌ Service Account JSONファイルが見つかりません")
        return False
    
    # アクセストークンを取得
    print("\n🔑 アクセストークンを取得...")
    
    try:
        # google-authを使用してトークンを取得
        import google.auth
        import google.auth.transport.requests
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(json_path)
        
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # トークンをリフレッシュ
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        
        access_token = credentials.token
        print("✅ アクセストークン取得成功")
        
    except Exception as e:
        print(f"❌ トークン取得エラー: {e}")
        
        # 代替方法：APIキーを使用
        print("\n📝 APIキーモードで試行...")
        api_key = "AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8"
        
        # Generative AI経由でVideo生成を試みる
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Generate a video: A beautiful sunrise over mountains with moving clouds"
                }]
            }],
            "generationConfig": {
                "temperature": 0.8
            }
        }
        
        print(f"URL: {url}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Gemini APIで動作確認成功（テキスト生成）")
            print("\n⚠️ 注意: Veo3は限定アクセスのため、現在は利用できません")
            print("代替案：")
            print("1. RunComfy Seedance API")
            print("2. PIAPI Hailuo API")
            print("3. Stability AI API")
            return False
        else:
            print(f"❌ エラー: {response.status_code}")
            print(response.text[:200])
            return False
        
        return False
    
    # Vertex AI Video APIを試す
    print("\n🎥 Vertex AI Video APIを試行...")
    
    # Imagen Video API エンドポイント
    endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/imagegeneration:predict"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # リクエストペイロード（静止画生成）
    payload = {
        "instances": [{
            "prompt": "A beautiful sunrise over mountains"
        }],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
            "addWatermark": False
        }
    }
    
    print(f"Endpoint: {endpoint}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Imagen API接続成功（静止画生成）")
            print("\n⚠️ 注：動画生成（Veo）は現在限定アクセスです")
            return True
        elif response.status_code == 404:
            print("❌ APIエンドポイントが見つかりません")
            print("Veo3は限定アクセスのため、一般利用はできません")
            return False
        else:
            print(f"❌ エラー: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
        return False

if __name__ == "__main__":
    success = test_google_imagen_video()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 部分的成功：Imagen API（静止画）は動作")
        print("⚠️ Veo3（動画）は限定アクセスです")
    else:
        print("ℹ️ Veo3は現在限定アクセスです")
        print("\n利用可能な代替手段：")
        print("1. RunComfy Seedance（高品質）")
        print("2. Stability AI（安定性高い）")
        print("3. PIAPI Hailuo（コスト効率的）")
    print("=" * 60)