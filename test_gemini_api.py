#!/usr/bin/env python3
"""
Gemini 2.5 Flash APIテストスクリプト
PIAPI経由でGemini画像生成をテスト
"""

import requests
import json
import time
import sys

# APIキー設定
PIAPI_KEY = "328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b"

def test_gemini_v1_task():
    """Gemini 2.5 Flash (v1 task API)をテスト"""
    
    print("\n=== Gemini 2.5 Flash テスト (v1 task API) ===\n")
    
    url = "https://api.piapi.ai/api/v1/task"
    
    headers = {
        "X-API-Key": PIAPI_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini",
        "task_type": "gemini-2.5-flash-image",
        "input": {
            "prompt": "create a 1/7 scale commercialized figure of the character in the illustration, in a realistic style and environment. Place the figure on a computer desk, using a circular transparent acrylic base without any text. On the computer screen, display the ZBrush modeling process of the figure. Next to the computer screen, place a BANDAI-style toy packaging box printed with the original artwork."
        }
    }
    
    print(f"📍 URL: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    print(f"🔑 API Key: {PIAPI_KEY[:10]}...{PIAPI_KEY[-10:]}")
    print("\n🚀 リクエスト送信中...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 成功レスポンス:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # タスクIDチェック
            if result.get('code') == 200:
                data = result.get('data', {})
                task_id = data.get('task_id')
                
                if task_id:
                    print(f"\n📌 Task ID取得: {task_id}")
                    print("⏳ ポーリング開始...")
                    
                    # タスクのポーリング
                    image_url = poll_gemini_task(task_id)
                    if image_url:
                        print(f"\n🖼️ 最終画像URL: {image_url}")
                        return True
                    else:
                        print("\n❌ ポーリングタイムアウト")
                        return False
                else:
                    print("\n❌ Task IDが返されませんでした")
                    return False
                    
        else:
            print(f"\n❌ エラー: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n💥 例外発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def poll_gemini_task(task_id, max_attempts=30):
    """Geminiタスクのポーリング"""
    
    url = f"https://api.piapi.ai/api/v1/task/{task_id}"
    headers = {"X-API-Key": PIAPI_KEY}
    
    for i in range(max_attempts):
        print(f"  [{i+1}/{max_attempts}] チェック中...", end="")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                # v1 task APIレスポンスフォーマット
                if result.get('code') == 200:
                    data = result.get('data', {})
                    status = data.get('status', 'pending')
                    
                    if status == 'completed':
                        print(" ✅ 完了!")
                        
                        output = data.get('output', {})
                        
                        # 画像URL取得（複数のフォーマットに対応）
                        if isinstance(output, str):
                            return output
                        elif isinstance(output, dict):
                            # image_urls フィールド（Gemini 2.5 Flash）
                            if output.get('image_urls'):
                                urls = output['image_urls']
                                if isinstance(urls, list) and len(urls) > 0:
                                    return urls[0]
                            # image_url フィールド
                            elif output.get('image_url'):
                                return output['image_url']
                            # images フィールド
                            elif output.get('images'):
                                images = output['images']
                                if isinstance(images, list) and len(images) > 0:
                                    if isinstance(images[0], str):
                                        return images[0]
                                    elif isinstance(images[0], dict) and images[0].get('url'):
                                        return images[0]['url']
                            # url フィールド
                            elif output.get('url'):
                                return output['url']
                        elif isinstance(output, list) and len(output) > 0:
                            if isinstance(output[0], str):
                                return output[0]
                            elif isinstance(output[0], dict) and output[0].get('url'):
                                return output[0]['url']
                        
                        print(f"\n  ⚠️ 画像URLが見つかりません。Output: {output}")
                        return None
                    
                    elif status in ['failed', 'error', 'cancelled']:
                        print(" ❌ 失敗")
                        print(f"  Error: {data.get('error', 'Unknown')}")
                        return None
                    else:
                        print(f" ⏳ Status: {status}")
                
        except Exception as e:
            print(f" 💥 {str(e)}")
            
        time.sleep(3)
    
    return None

def test_simple_prompt():
    """シンプルなプロンプトでテスト"""
    
    print("\n=== シンプルプロンプトテスト ===\n")
    
    url = "https://api.piapi.ai/api/v1/task"
    
    headers = {
        "X-API-Key": PIAPI_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini",
        "task_type": "gemini-2.5-flash-image",
        "input": {
            "prompt": "A beautiful Japanese woman in traditional kimono standing in front of cherry blossoms"
        }
    }
    
    print(f"📝 Simple Prompt: {payload['input']['prompt']}")
    print("\n🚀 リクエスト送信中...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                task_id = result.get('data', {}).get('task_id')
                if task_id:
                    print(f"✅ Task ID: {task_id}")
                    image_url = poll_gemini_task(task_id)
                    if image_url:
                        print(f"🖼️ Image URL: {image_url}")
                        return True
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=" * 70)
    print("Gemini 2.5 Flash API テスト (PIAPI経由)")
    print("=" * 70)
    
    # メインテスト（詳細なプロンプト）
    print("\n[Test 1] 詳細プロンプトテスト")
    success1 = test_gemini_v1_task()
    
    # シンプルなプロンプトでもテスト
    print("\n[Test 2] シンプルプロンプトテスト")
    success2 = test_simple_prompt()
    
    print("\n" + "=" * 70)
    print("テスト結果:")
    print(f"  Test 1 (詳細): {'✅ 成功' if success1 else '❌ 失敗'}")
    print(f"  Test 2 (シンプル): {'✅ 成功' if success2 else '❌ 失敗'}")
    print("=" * 70)