#!/usr/bin/env python3
"""
PIAPI Kling単体テスト
"""

import requests
import json

# APIキー
piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
base_url = "https://api.piapi.ai"

print("⚡ PIAPI Kling動画生成テスト")
print("=" * 50)

# Step 1: 動画生成リクエスト
url = f"{base_url}/api/v1/task"

headers = {
    "X-API-Key": piapi_xkey,
    "Content-Type": "application/json"
}

payload = {
    "model": "kling",
    "task_type": "video_generation",
    "input": {
        "prompt": "White egrets fly over vast paddy fields",
        "negative_prompt": "",
        "cfg_scale": 0.5,
        "duration": 5,
        "aspect_ratio": "16:9",
        "camera_control": {
            "type": "simple",
            "config": {
                "horizontal": 0,
                "vertical": 0,
                "pan": -10,
                "tilt": 0,
                "roll": 0,
                "zoom": 0
            }
        },
        "mode": "std"
    },
    "config": {
        "service_mode": "public",
        "webhook_config": {
            "endpoint": "",
            "secret": ""
        }
    }
}

print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(url, json=payload, headers=headers, timeout=30)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    
    if 'task_id' in result or (result.get('data') and 'task_id' in result['data']):
        task_id = result.get('task_id') or result['data']['task_id']
        print(f"\n✅ Kling タスク開始成功!")
        print(f"Task ID: {task_id}")
        
        # ステータス確認（1回だけ）
        print(f"\n⏳ ステータス確認...")
        
        status_url = f"{base_url}/api/v1/task/{task_id}"
        status_response = requests.get(status_url, headers={"X-API-Key": piapi_xkey}, timeout=10)
        
        print(f"Status Response: {status_response.text}")
        
    else:
        print(f"❌ Task ID取得失敗: {result}")
else:
    print(f"❌ リクエスト失敗")