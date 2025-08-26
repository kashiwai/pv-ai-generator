#!/usr/bin/env python3
"""
RunComfy Seedance クイックテスト
"""

import requests
import json

# 設定
deployment_id = "fdac4bbd-491d-47d7-ae45-ce70b67a067f"
api_token = "79521d2f-f728-47fe-923a-fde31f65df1f"  # API TOKEN

url = f"https://api.runcomfy.net/prod/v1/deployments/{deployment_id}/inference"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

payload = {
    "overrides": {
        "prompt": "A beautiful sunrise",
        "duration": 3
    }
}

print(f"URL: {url}")
print(f"Token: {api_token[:10]}...")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(url, headers=headers, json=payload, timeout=30)

print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text[:500]}")