#!/usr/bin/env python3
"""
RunComfy Seedance API実装（正式エンドポイント）
"""

import requests
import json
import time
from typing import Dict, Any

def test_runcomfy_seedance():
    """RunComfy Seedance動画生成テスト"""
    
    print("=" * 60)
    print("🎬 RunComfy Seedance動画生成テスト")
    print("=" * 60)
    
    # RunComfy設定
    deployment_id = "fdac4bbd-491d-47d7-ae45-ce70b67a067f"
    # APIトークン（UserIDではなくトークンの可能性）
    api_tokens = [
        "4368e0d2-edde-48c2-be18-e3caac513c1a",  # UserID
        "79521d2f-f728-47fe-923a-fde31f65df1f",   # Token1  
        "2bc59974-218f-45d7-b50e-3fb11e970f33"    # Token2
    ]
    
    # 正しいエンドポイント
    url = f"https://api.runcomfy.net/prod/v1/deployments/{deployment_id}/inference"
    
    # テストプロンプト
    test_prompt = "A beautiful sunrise over mountains with clouds moving slowly, cinematic quality"
    
    print(f"\n📝 プロンプト: {test_prompt}")
    print(f"🔗 URL: {url}")
    
    # 各トークンで試す
    for token in api_tokens:
        print(f"\n🔑 トークンをテスト: {token[:10]}...")
        
        # ヘッダー設定
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
        # リクエストペイロード
        payload = {
            "overrides": {
                "prompt": test_prompt,
                "duration": 5,
                "aspect_ratio": "16:9",
                "fps": 30,
                "quality": "high"
            }
        }
        
        print(f"\n🚀 動画生成リクエスト送信中...")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"\n📡 レスポンス:")
            print(f"Status Code: {response.status_code}")
        
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功!")
                print(f"Response: {json.dumps(result, indent=2)[:500]}")
                
                # request_idを取得
                if 'request_id' in result:
                    request_id = result['request_id']
                    print(f"\n📌 Request ID: {request_id}")
                    
                    # 結果URLを構築
                    result_url = f"https://api.runcomfy.net/prod/v1/deployments/{deployment_id}/requests/{request_id}/result"
                    return check_result_url(result_url, token)
                    
                # ジョブIDまたはステータスURL取得
                elif 'job_id' in result:
                    job_id = result['job_id']
                    print(f"\n📌 Job ID: {job_id}")
                    return check_job_status(job_id, token)
                elif 'status_url' in result:
                    print(f"\n📌 Status URL: {result['status_url']}")
                    return check_status_url(result['status_url'], token)
                else:
                    print("\n⚠️ 即座に結果が返されました")
                    if 'output' in result:
                        print(f"出力: {result['output']}")
                    return True
                    
            elif response.status_code == 401:
                print("❌ 認証エラー: このトークンは無効です")
            elif response.status_code == 403:
                print("❌ アクセス拒否: このトークンには権限がありません")
            elif response.status_code == 404:
                print("❌ デプロイメントが見つかりません")
            else:
                print(f"❌ エラー: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ 例外エラー: {e}")
    
    return False

def check_result_url(result_url: str, api_key: str) -> bool:
    """結果URLを確認"""
    
    print(f"\n⏳ 結果を確認中: {result_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for i in range(30):  # 最大5分待機
        time.sleep(10)
        
        try:
            response = requests.get(result_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                print(f"  [{i+1}/30] Status: {status}")
                
                if status == 'completed':
                    print(f"\n🎉 動画生成完了!")
                    if 'output' in result:
                        print(f"Output: {json.dumps(result['output'], indent=2)[:500]}")
                    return True
                elif status in ['failed', 'error']:
                    print(f"\n❌ 生成失敗: {result.get('error', 'unknown')}")
                    return False
                    
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("\n⏱️ タイムアウト（5分）")
    return False

def check_job_status(job_id: str, api_key: str) -> bool:
    """ジョブステータスを確認"""
    
    print(f"\n⏳ ジョブ {job_id} のステータス確認中...")
    
    url = f"https://api.runcomfy.net/prod/v1/jobs/{job_id}"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    for i in range(30):  # 最大5分待機
        time.sleep(10)
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                print(f"  [{i+1}/30] Status: {status}")
                
                if status == 'completed':
                    output = result.get('output', {})
                    video_url = output.get('video_url') or output.get('url')
                    
                    if video_url:
                        print(f"\n🎉 動画生成完了!")
                        print(f"動画URL: {video_url}")
                        return True
                    else:
                        print("\n⚠️ 動画URLが見つかりません")
                        print(f"Output: {output}")
                        return False
                        
                elif status in ['failed', 'error']:
                    print(f"\n❌ 生成失敗: {result.get('error', 'unknown')}")
                    return False
                    
        except Exception as e:
            print(f"  エラー: {e}")
    
    print("\n⏱️ タイムアウト（5分）")
    return False

def check_status_url(status_url: str, api_key: str) -> bool:
    """ステータスURLを確認"""
    
    print(f"\n⏳ ステータス確認中: {status_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    for i in range(30):
        time.sleep(10)
        
        try:
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                print(f"  [{i+1}/30] Status: {status}")
                
                if status == 'completed':
                    print(f"\n🎉 動画生成完了!")
                    if 'output' in result:
                        print(f"Output: {result['output']}")
                    return True
                elif status in ['failed', 'error']:
                    print(f"\n❌ 失敗: {result.get('error')}")
                    return False
                    
        except Exception as e:
            print(f"  エラー: {e}")
    
    return False

def test_simple_request():
    """シンプルなリクエストテスト"""
    
    print("\n" + "=" * 60)
    print("🔍 シンプルリクエストテスト")
    print("=" * 60)
    
    deployment_id = "fdac4bbd-491d-47d7-ae45-ce70b67a067f"
    userid = "4368e0d2-edde-48c2-be18-e3caac513c1a"
    url = f"https://api.runcomfy.net/prod/v1/deployments/{deployment_id}/inference"
    
    # 最小限のペイロード
    payload = {"overrides": {}}
    
    headers = {
        "Authorization": f"Bearer {userid}",
        "Content-Type": "application/json"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 接続成功!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
            return True
        else:
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RunComfy Seedance動画生成テスト")
    print("=" * 80)
    
    # メインテスト
    success = test_runcomfy_seedance()
    
    if not success:
        # シンプルテスト
        simple_success = test_simple_request()
        
        if simple_success:
            print("\n✅ API接続は成功しています")
            print("パラメータを調整してください")
    
    print("\n" + "=" * 80)
    if success:
        print("✅ RunComfy Seedance動画生成成功!")
    else:
        print("⚠️ 動画生成に失敗しました")
        print("\n確認事項:")
        print("1. APIキー（User ID）が正しいか")
        print("2. デプロイメントIDが正しいか")
        print("3. パラメータ形式が正しいか")
    print("=" * 80)