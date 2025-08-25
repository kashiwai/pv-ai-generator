#!/usr/bin/env python3
"""
API接続状態チェックスクリプト
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

async def check_piapi():
    """PIAPI接続チェック"""
    api_key = os.environ.get("PIAPI_KEY")
    x_key = os.environ.get("PIAPI_XKEY")
    
    if not api_key or not x_key:
        return {"status": "not_configured", "message": "Keys not set"}
    
    try:
        # PIAPIヘルスチェックエンドポイント（仮）
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": x_key,
                "Content-Type": "application/json"
            }
            # 実際のエンドポイントに置き換える必要があります
            url = "https://api.piapi.ai/api/v1/health"
            
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    return {"status": "connected", "message": "OK"}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_openai():
    """OpenAI API接続チェック"""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        return {"status": "not_configured", "message": "Key not set"}
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            url = "https://api.openai.com/v1/models"
            
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    return {"status": "connected", "message": "OK"}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_google():
    """Google API接続チェック"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        return {"status": "not_configured", "message": "Key not set"}
    
    # Google APIの実際のチェック実装
    return {"status": "not_tested", "message": "Check not implemented"}

async def check_anthropic():
    """Anthropic API接続チェック"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        return {"status": "not_configured", "message": "Key not set"}
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            url = "https://api.anthropic.com/v1/messages"
            
            # 最小限のテストリクエスト
            data = {
                "model": "claude-3-haiku-20240307",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            async with session.post(url, headers=headers, json=data, timeout=5) as response:
                if response.status in [200, 401, 403]:  # 認証エラーも「接続可能」とみなす
                    return {"status": "connected", "message": f"HTTP {response.status}"}
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def main():
    """メイン処理"""
    print("API接続状態チェック開始...")
    
    # 全APIを並行チェック
    results = await asyncio.gather(
        check_piapi(),
        check_openai(),
        check_google(),
        check_anthropic()
    )
    
    # 結果をまとめる
    api_status = {
        "timestamp": datetime.now().isoformat(),
        "piapi": results[0],
        "openai": results[1],
        "google": results[2],
        "anthropic": results[3]
    }
    
    # ログディレクトリ作成
    log_dir = Path("mcp_logs")
    log_dir.mkdir(exist_ok=True)
    
    # 結果を保存
    status_file = log_dir / "api_status.json"
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(api_status, f, indent=2, ensure_ascii=False)
    
    # 結果を表示
    print("\n===== API接続状態 =====")
    print(f"チェック時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 30)
    
    for api_name, status in [("PIAPI", results[0]), ("OpenAI", results[1]), 
                              ("Google", results[2]), ("Anthropic", results[3])]:
        status_icon = "✅" if status["status"] == "connected" else "❌" if status["status"] == "error" else "⚠️"
        print(f"{status_icon} {api_name}: {status['status']} - {status['message']}")
    
    print("-" * 30)
    
    # 重要な警告
    if results[0]["status"] != "connected":
        print("\n⚠️  警告: PIAPIが接続できません！Midjourney/Hailuo機能が使用できません。")
    
    connected_count = sum(1 for r in results if r["status"] == "connected")
    print(f"\n接続済みAPI: {connected_count}/4")

if __name__ == "__main__":
    asyncio.run(main())