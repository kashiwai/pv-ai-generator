#!/usr/bin/env python3
"""
PIAPI Hailuo API 正しいエンドポイントでテスト
"""

import requests
import json
import time

def test_piapi_hailuo():
    """PIAPI Hailuoで動画生成"""
    
    print("=" * 60)
    print("🎬 PIAPI Hailuo 動画生成テスト（修正版）")
    print("=" * 60)
    
    # APIキー
    piapi_key = "328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b"
    piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
    
    # テストプロンプト
    test_prompt = "A beautiful sunrise over mountains with clouds moving slowly"
    
    print(f"\n📝 プロンプト: {test_prompt}")
    
    # 正しいエンドポイント（ユーザー提供のドキュメントより）
    endpoints = [
        "https://api.piapi.ai/api/hailuo/v2/video",  # V2エンドポイント
        "https://api.piapi.ai/hailuo/generate",       # 生成エンドポイント
        "https://api.piapi.ai/v1/hailuo",            # V1エンドポイント
    ]
    
    for endpoint in endpoints:
        print(f"\n🔍 エンドポイントをテスト: {endpoint}")
        
        headers = {
            "X-API-Key": piapi_xkey,
            "Api-Key": piapi_key,
            "Content-Type": "application/json"
        }
        
        # ユーザー提供のパラメータ形式
        payload = {
            "prompt": test_prompt,
            "task_type": "video_generation",
            "model": "s2v-01",
            "duration": 5,
            "aspect_ratio": "16:9"
        }
        
        try:
            response = requests.post(
                endpoint, 
                json=payload, 
                headers=headers, 
                timeout=15
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功: {json.dumps(result, indent=2)[:500]}")
                
                if 'task_id' in result or 'id' in result:
                    task_id = result.get('task_id') or result.get('id')
                    print(f"\n📌 Task ID: {task_id}")
                    
                    # ステータス確認
                    check_status(task_id, piapi_key, piapi_xkey)
                    return True
                    
            elif response.status_code == 404:
                print(f"❌ 404: エンドポイントが存在しません")
            else:
                print(f"❌ エラー: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 例外: {e}")
    
    return False

def check_status(task_id, piapi_key, piapi_xkey):
    """タスクのステータスを確認"""
    
    print(f"\n⏳ タスク {task_id} のステータスを確認中...")
    
    status_endpoints = [
        f"https://api.piapi.ai/api/hailuo/v2/status/{task_id}",
        f"https://api.piapi.ai/v1/task/{task_id}",
        f"https://api.piapi.ai/hailuo/status/{task_id}"
    ]
    
    headers = {
        "X-API-Key": piapi_xkey,
        "Api-Key": piapi_key
    }
    
    for endpoint in status_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ ステータス取得成功: {endpoint}")
                print(f"Status: {result.get('status', 'unknown')}")
                
                if result.get('status') == 'completed':
                    print(f"🎉 動画URL: {result.get('video_url', 'N/A')}")
                    
                return True
                
        except Exception as e:
            print(f"⚠️ ステータス確認エラー: {e}")
    
    return False

def test_runcomfy_seedance():
    """RunComfy Seedance APIテスト"""
    
    print("\n" + "=" * 60)
    print("🎬 RunComfy Seedance APIテスト")
    print("=" * 60)
    
    # RunComfy設定
    userid = "4368e0d2-edde-48c2-be18-e3caac513c1a"
    api_endpoints = [
        "https://api.runcomfy.com/v1/video/generate",
        "https://www.runcomfy.com/api/v1/generate",
        "https://api.runcomfy.net/prod/v1/generate"
    ]
    
    test_prompt = "A cinematic sunrise over mountains"
    
    for endpoint in api_endpoints:
        print(f"\n🔍 エンドポイント: {endpoint}")
        
        headers = {
            "Authorization": f"Bearer {userid}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": test_prompt,
            "model": "seedance",
            "duration": 5,
            "aspect_ratio": "16:9"
        }
        
        try:
            response = requests.post(
                endpoint, 
                json=payload, 
                headers=headers, 
                timeout=15
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ RunComfy API接続成功")
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:500]}")
                return True
            elif response.status_code == 521:
                print(f"❌ 521: サーバーダウン")
            else:
                print(f"❌ エラー: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 例外: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Text-to-Video API動作確認")
    print("=" * 80)
    
    # PIAPI Hailuoテスト
    hailuo_success = test_piapi_hailuo()
    
    # RunComfy Seedanceテスト
    runcomfy_success = test_runcomfy_seedance()
    
    print("\n" + "=" * 80)
    print("📊 テスト結果:")
    print(f"  PIAPI Hailuo: {'✅ 成功' if hailuo_success else '❌ 失敗'}")
    print(f"  RunComfy Seedance: {'✅ 成功' if runcomfy_success else '❌ 失敗'}")
    
    if hailuo_success or runcomfy_success:
        print("\n✅ 少なくとも1つのAPIが利用可能です！")
    else:
        print("\n❌ 両方のAPIが利用できません")
        print("\n代替案:")
        print("1. APIキーを確認")
        print("2. エンドポイントURLを更新")
        print("3. Stability AI APIを検討")
    print("=" * 80)