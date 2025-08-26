#!/usr/bin/env python3
"""
実際のText-to-Video生成テスト（PIAPI Hailuo使用）
"""

import requests
import json
import time
import sys

def test_hailuo_video_generation():
    """PIAPI Hailuoで動画生成をテスト"""
    
    print("=" * 60)
    print("🎬 PIAPI Hailuo 動画生成テスト")
    print("=" * 60)
    
    # APIキー
    piapi_key = "328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b"
    piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
    
    # テストプロンプト
    test_prompt = "大空に新しい太陽が発見した"
    
    print(f"\n📝 プロンプト: {test_prompt}")
    
    # Step 1: 動画生成ジョブを開始
    url = "https://api.piapi.ai/mj/v2/hailuo"
    
    headers = {
        "X-API-Key": piapi_xkey,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "prompt": test_prompt,
        "task_type": "video_generation",
        "model": "s2v-01",
        "options": {
            "duration": 5,
            "aspect_ratio": "16:9",
            "resolution": "1920x1080"
        },
        "webhook_url": "",
        "webhook_secret": ""
    }
    
    print("\n🚀 動画生成ジョブを開始...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n📡 レスポンス:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == 200:
                task_id = result.get('data', {}).get('task_id')
                print(f"\n✅ ジョブ開始成功!")
                print(f"Task ID: {task_id}")
                
                # Step 2: ステータスをポーリング
                if task_id:
                    print("\n⏳ 生成状況を確認中...")
                    
                    status_url = f"https://api.piapi.ai/mj/v2/task/{task_id}"
                    
                    for i in range(30):  # 最大5分待機
                        time.sleep(10)  # 10秒待機
                        
                        status_response = requests.get(
                            status_url,
                            headers={"X-API-Key": piapi_xkey},
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data.get('data', {}).get('status')
                            
                            print(f"  [{i+1}/30] Status: {status}")
                            
                            if status == 'completed':
                                video_url = status_data.get('data', {}).get('video_url')
                                print(f"\n🎉 動画生成完了!")
                                print(f"動画URL: {video_url}")
                                return True
                            elif status == 'failed':
                                print(f"\n❌ 生成失敗: {status_data.get('data', {}).get('error')}")
                                return False
                    
                    print("\n⏱️ タイムアウト（5分）")
                    return False
            else:
                print(f"\n❌ エラー: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTPエラー: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 例外エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_hailuo_video_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ テスト成功！動画生成が機能しています。")
    else:
        print("❌ テスト失敗。APIキーまたはパラメータを確認してください。")
    print("=" * 60)