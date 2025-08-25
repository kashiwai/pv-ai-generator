#!/usr/bin/env python3
"""
シンプルなMidjourney画像生成テスト
Streamlit依存なしで実行
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

def test_midjourney_generation():
    """PIAPI経由でMidjourney画像を生成"""
    
    print("🎨 Midjourney画像生成テスト")
    print("=" * 60)
    
    # APIキー取得
    api_key = os.getenv('PIAPI_KEY')
    x_key = os.getenv('PIAPI_XKEY')
    
    if not api_key or not x_key:
        print("❌ PIAPIキーが環境変数に設定されていません")
        return
    
    print(f"✅ APIキー検出")
    print(f"  PIAPI_KEY: {api_key[:16]}...")
    print(f"  PIAPI_XKEY: {x_key[:16]}...")
    
    # テストプロンプト
    test_prompts = [
        "beautiful japanese garden, cherry blossoms, peaceful atmosphere, professional photography --ar 16:9 --v 6",
        "modern business presentation, professional meeting room, clean design --ar 16:9 --v 6",
        "abstract technology background, blue and purple gradient, futuristic --ar 16:9 --v 6"
    ]
    
    base_url = "https://api.piapi.ai"
    headers = {
        "x-api-key": x_key,
        "Content-Type": "application/json"
    }
    
    for i, prompt in enumerate(test_prompts[:1], 1):  # 最初の1つだけテスト
        print(f"\n📝 テスト {i}")
        print("-" * 40)
        print(f"プロンプト: {prompt[:60]}...")
        
        # タスク作成
        payload = {
            "model": "midjourney",
            "task_type": "imagine",
            "input": {
                "prompt": prompt,
                "process_mode": "relax",
                "skip_prompt_check": False
            }
        }
        
        try:
            # リクエスト送信
            response = requests.post(
                f"{base_url}/api/v1/task",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # task_id取得
                task_id = None
                if isinstance(result, dict) and 'data' in result:
                    task_id = result['data'].get('task_id')
                
                if task_id:
                    print(f"✅ タスク作成成功: {task_id}")
                    
                    # ステータス確認（最大30秒待機）
                    print("\n⏳ 生成状態を確認中...")
                    for check in range(6):  # 5秒ごと6回 = 30秒
                        time.sleep(5)
                        
                        # ステータスチェック
                        status_response = requests.get(
                            f"{base_url}/api/v1/task/{task_id}",
                            headers=headers,
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            # ステータス取得
                            if 'data' in status_data:
                                task_status = status_data['data'].get('status', 'unknown')
                                progress = status_data['data'].get('output', {}).get('progress', 0)
                                
                                print(f"  {check+1}. ステータス: {task_status} (進捗: {progress}%)")
                                
                                # 完了チェック
                                if task_status.lower() in ['completed', 'success']:
                                    image_url = status_data['data'].get('output', {}).get('image_url')
                                    if image_url:
                                        print(f"\n✅ 画像生成完了!")
                                        print(f"  URL: {image_url}")
                                        return True
                                elif task_status.lower() in ['failed', 'error']:
                                    error_msg = status_data['data'].get('output', {}).get('error', 'Unknown error')
                                    print(f"\n❌ 生成失敗: {error_msg}")
                                    return False
                        else:
                            print(f"  ステータスチェック失敗: {status_response.status_code}")
                    
                    print("\n⚠️ タイムアウト: 生成に時間がかかっています")
                    print(f"  タスクID {task_id} で後ほど確認してください")
                else:
                    print("❌ task_idが取得できませんでした")
                    print(f"レスポンス: {json.dumps(result, indent=2)[:500]}")
            else:
                print(f"❌ エラー: ステータスコード {response.status_code}")
                print(f"詳細: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ 例外発生: {e}")
    
    return False

def check_hooks_setup():
    """Hooks設定を確認"""
    print("\n🪝 Hooks自動実行設定確認")
    print("=" * 60)
    
    # Claude Code Hooksファイル確認
    hooks_file = Path(".claude-code-hooks")
    if hooks_file.exists():
        print(f"✅ Hooksファイル存在: {hooks_file}")
        
        with open(hooks_file, 'r') as f:
            content = json.load(f)
        
        if 'hooks' in content:
            print("\n設定されているフック:")
            for hook_name, hook_config in content['hooks'].items():
                print(f"  • {hook_name}: {hook_config.get('description', 'No description')}")
                if 'command' in hook_config:
                    print(f"    コマンド: {hook_config['command'][:50]}...")
        
        if 'autoExecute' in content:
            auto_tasks = content.get('autoExecute', {}).get('tasks', [])
            if auto_tasks:
                print(f"\n自動実行タスク: {len(auto_tasks)}個")
                for task in auto_tasks:
                    print(f"  • {task.get('name')}: {task.get('trigger')}")
    else:
        print(f"❌ Hooksファイルが見つかりません: {hooks_file}")
    
    # crontab確認
    print("\n📅 Crontab設定:")
    import subprocess
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            mcp_lines = [line for line in lines if 'mcp' in line.lower()]
            if mcp_lines:
                print("✅ MCP関連のcrontabエントリ:")
                for line in mcp_lines:
                    if not line.startswith('#'):
                        print(f"  {line}")
            else:
                print("⚠️ MCP関連のcrontabエントリが見つかりません")
        else:
            print("❌ crontabが設定されていません")
    except Exception as e:
        print(f"❌ crontab確認エラー: {e}")
    
    # MCPログ確認
    print("\n📊 MCPログ状況:")
    log_dir = Path("mcp_logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.json")) + list(log_dir.glob("*.log"))
        if log_files:
            print(f"✅ ログファイル数: {len(log_files)}")
            for log_file in sorted(log_files)[-3:]:  # 最新3つ
                size = log_file.stat().st_size
                print(f"  • {log_file.name} ({size} bytes)")
        else:
            print("⚠️ ログファイルが見つかりません")
    else:
        print("❌ MCPログディレクトリが存在しません")

def main():
    print("=" * 60)
    print("🎬 Midjourney & Hooks テスト")
    print("=" * 60)
    
    # Midjourney生成テスト
    success = test_midjourney_generation()
    
    # Hooks設定確認
    check_hooks_setup()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Midjourney画像生成: 成功")
    else:
        print("⚠️ Midjourney画像生成: 未完了またはエラー")
    print("=" * 60)

if __name__ == "__main__":
    main()