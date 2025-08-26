#!/usr/bin/env python3
"""
PIAPI公式ドキュメントに基づくHailuo AI実装
"""

import requests
import json
import time

def test_piapi_hailuo_official():
    """PIAPI Hailuo公式実装"""
    
    print("=" * 60)
    print("🎬 PIAPI Hailuo AI 公式実装テスト")
    print("=" * 60)
    
    # APIキー
    piapi_key = "328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b"
    piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
    
    # ユーザー提供のドキュメントに基づく正しい形式
    base_url = "https://api.piapi.ai"
    
    # テストプロンプト
    test_prompt = "A beautiful sunrise over mountains, cinematic quality"
    
    print(f"\n📝 プロンプト: {test_prompt}")
    
    # 1. Midjourney経由でHailuoを試す（PIAPIの主要機能）
    print("\n🔍 方法1: Midjourney/Hailuo統合エンドポイント")
    
    url = f"{base_url}/mj/v2/imagine"
    
    headers = {
        "X-API-Key": piapi_xkey,
        "Content-Type": "application/json"
    }
    
    # Hailuoビデオ生成用のパラメータ
    payload = {
        "prompt": test_prompt,
        "process_mode": "hailuo",  # Hailuoモード
        "aspect_ratio": "16:9",
        "duration": 5,
        "webhook_endpoint": "",
        "webhook_secret": ""
    }
    
    print(f"URL: {url}")
    print(f"Headers: X-API-Key: {piapi_xkey[:10]}...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
            
            if 'task_id' in result:
                return check_task_status(result['task_id'], piapi_xkey)
        else:
            print(f"❌ エラー: {response.text[:300]}")
    except Exception as e:
        print(f"❌ 例外: {e}")
    
    # 2. 直接Hailuoエンドポイントを試す
    print("\n🔍 方法2: 直接Hailuo API")
    
    # 複数のエンドポイント形式を試す
    endpoints = [
        f"{base_url}/hailuo/v1/generate",
        f"{base_url}/v1/hailuo/generate",
        f"{base_url}/api/v1/hailuo"
    ]
    
    for endpoint in endpoints:
        print(f"\nテスト: {endpoint}")
        
        headers = {
            "X-API-Key": piapi_xkey,
            "Api-Key": piapi_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": test_prompt,
            "duration_seconds": 5,
            "aspect_ratio": "16:9"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 成功!")
                result = response.json()
                print(f"Result: {json.dumps(result, indent=2)[:300]}")
                return True
            elif response.status_code != 404:
                print(f"Response: {response.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
    
    return False

def check_task_status(task_id, api_key):
    """タスクステータスを確認"""
    
    print(f"\n⏳ タスク {task_id} のステータス確認中...")
    
    url = f"https://api.piapi.ai/mj/v2/task/{task_id}/fetch"
    
    headers = {
        "X-API-Key": api_key
    }
    
    for i in range(5):
        time.sleep(3)
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                print(f"  [{i+1}/5] Status: {status}")
                
                if status == 'SUCCESS':
                    print(f"✅ 完了!")
                    if 'uri' in result:
                        print(f"動画URL: {result['uri']}")
                    return True
                elif status == 'FAILED':
                    print(f"❌ 失敗: {result.get('error', 'unknown error')}")
                    return False
        except Exception as e:
            print(f"  Error: {e}")
    
    return False

def test_midjourney_imagine():
    """Midjourney Imagine API（画像生成）テスト"""
    
    print("\n" + "=" * 60)
    print("🎨 Midjourney Imagine API テスト（画像生成）")
    print("=" * 60)
    
    piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
    
    url = "https://api.piapi.ai/mj/v2/imagine"
    
    headers = {
        "X-API-Key": piapi_xkey,
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "a beautiful landscape --ar 16:9 --v 6",
        "process_mode": "fast",
        "webhook_endpoint": "",
        "webhook_secret": ""
    }
    
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Midjourney API接続成功!")
            print(f"Task ID: {result.get('task_id', 'N/A')}")
            return True
        else:
            print(f"❌ エラー: {response.text[:300]}")
            return False
    except Exception as e:
        print(f"❌ 例外: {e}")
        return False

if __name__ == "__main__":
    print("🚀 PIAPI公式実装テスト")
    print("=" * 80)
    
    # Hailuo動画生成テスト
    hailuo_success = test_piapi_hailuo_official()
    
    # Midjourney画像生成テスト
    midjourney_success = test_midjourney_imagine()
    
    print("\n" + "=" * 80)
    print("📊 テスト結果:")
    print(f"  Hailuo動画生成: {'✅ 成功' if hailuo_success else '❌ 失敗'}")
    print(f"  Midjourney画像生成: {'✅ 成功' if midjourney_success else '❌ 失敗'}")
    
    if hailuo_success:
        print("\n✅ Hailuo動画生成が利用可能です！")
    elif midjourney_success:
        print("\n⚠️ Midjourney画像生成は動作しています")
        print("動画生成には別の方法が必要です")
    
    print("\n📝 推奨事項:")
    print("1. PIAPI Midjourneyで画像生成")
    print("2. 生成した画像をImage-to-Videoで動画化")
    print("3. または別のText-to-Video APIを使用")
    print("=" * 80)