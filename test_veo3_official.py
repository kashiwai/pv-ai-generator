#!/usr/bin/env python3
"""
Google Veo 3.0 公式API実装テスト
"""

import os
import json
import requests
import time
from pathlib import Path
import base64

def test_veo3_official():
    """Google Veo 3.0 公式APIテスト"""
    
    print("=" * 60)
    print("🎬 Google Veo 3.0 公式APIテスト")
    print("=" * 60)
    
    # プロジェクト設定
    project_id = "medent-9167b"
    location = "us-central1"
    model_id = "veo-3.0-generate-preview"  # または veo-3.0-fast-generate-preview
    
    # Service Account認証
    json_path = Path('/tmp/google-service-account.json')
    if not json_path.exists():
        print("❌ Service Account JSONファイルが見つかりません")
        return False
    
    # アクセストークンを取得
    print("\n🔑 アクセストークンを取得...")
    
    try:
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
        return False
    
    # Veo 3.0 APIエンドポイント
    endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predictLongRunning"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # テストプロンプト
    test_prompt = "大空に新しい太陽が昇る、美しい朝焼けの風景"
    
    # リクエストペイロード
    payload = {
        "instances": [
            {
                "prompt": test_prompt
            }
        ],
        "parameters": {
            "aspectRatio": "16:9",
            "durationSeconds": 5,
            "enhancePrompt": True,
            "generateAudio": True,
            "sampleCount": 1,
            "personGeneration": "allow"
        }
    }
    
    print(f"\n📝 プロンプト: {test_prompt}")
    print(f"\n🎥 Veo 3.0で動画生成を開始...")
    print(f"Model: {model_id}")
    print(f"Endpoint: {endpoint}")
    print(f"\nPayload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        print(f"\n📡 レスポンス:")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Veo 3.0 APIリクエスト成功!")
            
            # 長時間実行ジョブの情報を取得
            operation_name = result.get('name')
            print(f"Operation ID: {operation_name}")
            
            # ジョブのステータスをポーリング
            print("\n⏳ 動画生成中...")
            
            status_endpoint = f"https://{location}-aiplatform.googleapis.com/v1/{operation_name}"
            
            for i in range(60):  # 最大10分待機
                time.sleep(10)
                
                status_response = requests.get(
                    status_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    done = status_data.get('done', False)
                    
                    print(f"  [{i+1}/60] Status: {'完了' if done else '処理中'}")
                    
                    if done:
                        if 'error' in status_data:
                            print(f"\n❌ エラー: {status_data['error']}")
                            return False
                        
                        response_data = status_data.get('response', {})
                        predictions = response_data.get('predictions', [])
                        
                        if predictions:
                            video_data = predictions[0]
                            print(f"\n🎉 動画生成完了!")
                            
                            # GCSのURIまたはBase64データを確認
                            if 'gcsUri' in video_data:
                                print(f"動画URL: {video_data['gcsUri']}")
                            elif 'bytesBase64Encoded' in video_data:
                                print(f"動画データ: Base64エンコード済み（{len(video_data['bytesBase64Encoded'])} bytes）")
                            
                            return True
                        else:
                            print("\n⚠️ 予測結果が空です")
                            return False
            
            print("\n⏱️ タイムアウト（10分）")
            return False
            
        elif response.status_code == 404:
            print("❌ エンドポイントが見つかりません")
            print("Veo 3.0は限定プレビュー版です。アクセス権限を確認してください。")
            
            # フォールバック：Veo 2.0を試す
            print("\n🔄 Veo 2.0にフォールバック...")
            model_id_v2 = "veo-generate"  # Veo 2.0
            endpoint_v2 = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id_v2}:predictLongRunning"
            
            response_v2 = requests.post(endpoint_v2, json=payload, headers=headers, timeout=30)
            
            if response_v2.status_code == 200:
                print("✅ Veo 2.0 APIは利用可能です")
                return True
            else:
                print(f"❌ Veo 2.0もエラー: {response_v2.status_code}")
                return False
                
        elif response.status_code == 403:
            print("❌ アクセス拒否")
            print("Veo APIへのアクセス権限がありません。")
            print("以下を確認してください：")
            print("1. Vertex AI APIが有効化されているか")
            print("2. Service AccountにVertex AI Userロールが付与されているか")
            print("3. Veo 3.0プレビューへのアクセス権限があるか")
            return False
            
        else:
            print(f"❌ HTTPエラー: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_veo3_fast():
    """Veo 3.0 Fast版のテスト"""
    
    print("\n" + "=" * 60)
    print("🚀 Google Veo 3.0 Fast版テスト")
    print("=" * 60)
    
    # プロジェクト設定
    project_id = "medent-9167b"
    location = "us-central1"
    model_id = "veo-3.0-fast-generate-preview"
    
    # Service Account認証
    json_path = Path('/tmp/google-service-account.json')
    if not json_path.exists():
        print("❌ Service Account JSONファイルが見つかりません")
        return False
    
    try:
        import google.auth
        import google.auth.transport.requests
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(json_path)
        
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        
        access_token = credentials.token
        print("✅ アクセストークン取得成功")
        
    except Exception as e:
        print(f"❌ トークン取得エラー: {e}")
        return False
    
    # エンドポイント
    endpoint = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predictLongRunning"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "instances": [
            {
                "prompt": "A cinematic sunrise over mountains"
            }
        ],
        "parameters": {
            "aspectRatio": "16:9",
            "durationSeconds": 3,
            "sampleCount": 1
        }
    }
    
    print(f"\n🎥 Veo 3.0 Fastで動画生成...")
    print(f"Model: {model_id}")
    
    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Veo 3.0 Fast APIリクエスト成功!")
        return True
    else:
        print(f"❌ エラー: {response.text[:200]}")
        return False

if __name__ == "__main__":
    # Veo 3.0 標準版をテスト
    success = test_veo3_official()
    
    # Fast版もテスト
    if not success:
        success_fast = test_veo3_fast()
    else:
        success_fast = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Veo 3.0が利用可能です！")
    elif success_fast:
        print("✅ Veo 3.0 Fast版が利用可能です！")
    else:
        print("⚠️ Veo 3.0は限定プレビューです")
        print("\n現在利用可能な方法：")
        print("1. Veoプレビューへのアクセス申請")
        print("2. Imagen 3で静止画生成→AnimateDiffで動画化")
        print("3. RunComfy Seedance API（外部サービス）")
        print("4. Stability AI（外部サービス）")
    print("=" * 60)