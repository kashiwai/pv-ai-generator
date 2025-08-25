#!/usr/bin/env python3
"""
PIAPI Midjourney統合テストスクリプト
PIAPIキーとMidjourney設定の診断
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent / "pv-ai-generator"))

def check_env_keys():
    """環境変数のAPIキーをチェック"""
    print("\n🔑 環境変数チェック")
    print("-" * 50)
    
    keys = {
        'PIAPI_KEY': os.getenv('PIAPI_KEY'),
        'PIAPI_XKEY': os.getenv('PIAPI_XKEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'MIDJOURNEY_API_KEY': os.getenv('MIDJOURNEY_API_KEY')
    }
    
    for key_name, key_value in keys.items():
        if key_value:
            masked = key_value[:8] + "..." + key_value[-4:] if len(key_value) > 12 else "***"
            print(f"✅ {key_name}: {masked} ({len(key_value)}文字)")
        else:
            print(f"❌ {key_name}: 未設定")
    
    return keys

def check_streamlit_secrets():
    """Streamlit Secretsファイルをチェック"""
    print("\n📄 Streamlit Secrets チェック")
    print("-" * 50)
    
    secrets_path = Path.home() / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        print(f"✅ Secretsファイル存在: {secrets_path}")
        try:
            import toml
            with open(secrets_path, 'r') as f:
                secrets = toml.load(f)
                
            keys_found = []
            for key in ['PIAPI_KEY', 'PIAPI_XKEY', 'MIDJOURNEY_API_KEY']:
                if key in secrets:
                    keys_found.append(key)
            
            if keys_found:
                print(f"  見つかったキー: {', '.join(keys_found)}")
            else:
                print("  ⚠️ PIAPIキーが見つかりません")
        except Exception as e:
            print(f"  エラー: {e}")
    else:
        print(f"❌ Secretsファイルが存在しません: {secrets_path}")

def test_piapi_connection(api_key, x_key):
    """PIAPI接続テスト"""
    print("\n🌐 PIAPI接続テスト")
    print("-" * 50)
    
    if not api_key or not x_key:
        print("❌ PIAPIキーが設定されていません")
        return False
    
    # ヘルスチェック用のエンドポイント
    base_url = "https://api.piapi.ai"
    headers = {
        "x-api-key": x_key,
        "Content-Type": "application/json"
    }
    
    # 簡単なテストプロンプト
    test_payload = {
        "model": "midjourney",
        "task_type": "imagine",
        "input": {
            "prompt": "test image --ar 16:9 --v 6",
            "process_mode": "relax",
            "skip_prompt_check": False
        }
    }
    
    try:
        print(f"エンドポイント: {base_url}/api/v1/task")
        print(f"X-API-Key: {x_key[:8]}...{x_key[-4:]}")
        
        response = requests.post(
            f"{base_url}/api/v1/task",
            json=test_payload,
            headers=headers,
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 接続成功!")
            print(f"レスポンス: {json.dumps(result, indent=2)[:500]}...")
            
            # task_idの確認
            task_id = None
            if isinstance(result, dict):
                if 'data' in result and isinstance(result['data'], dict):
                    task_id = result['data'].get('task_id')
                elif 'task_id' in result:
                    task_id = result['task_id']
            
            if task_id:
                print(f"✅ Task ID取得成功: {task_id}")
                return True
            else:
                print("⚠️ Task IDが取得できませんでした")
                return False
                
        elif response.status_code == 401:
            print("❌ 認証エラー: APIキーが無効です")
        elif response.status_code == 403:
            print("❌ アクセス拒否: 権限がありません")
        elif response.status_code == 429:
            print("⚠️ レート制限: しばらく待ってから再試行してください")
        else:
            print(f"❌ エラー: {response.text}")
        
        return False
        
    except requests.exceptions.Timeout:
        print("❌ タイムアウト: APIサーバーが応答しません")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: ネットワークを確認してください")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_midjourney_with_piapi():
    """PIAPIを使用したMidjourney画像生成テスト"""
    print("\n🎨 Midjourney画像生成テスト")
    print("-" * 50)
    
    try:
        from piapi_integration import PIAPIClient
        print("✅ PIAPIモジュールのインポート成功")
    except ImportError as e:
        print(f"❌ PIAPIモジュールのインポート失敗: {e}")
        return
    
    # キーを取得
    api_key = os.getenv('PIAPI_KEY')
    x_key = os.getenv('PIAPI_XKEY')
    
    if not api_key or not x_key:
        print("❌ PIAPIキーが設定されていません")
        print("\n💡 解決方法:")
        print("1. 環境変数を設定:")
        print("   export PIAPI_KEY='your-main-key'")
        print("   export PIAPI_XKEY='your-x-key'")
        print("\n2. またはStreamlit Secretsに設定:")
        print("   ~/.streamlit/secrets.toml に追加")
        return
    
    # PIAPIクライアントを初期化
    client = PIAPIClient(api_key, x_key)
    print(f"✅ PIAPIClient初期化完了")
    
    # テスト画像生成
    test_prompt = "beautiful landscape, mountains, sunset, high quality, professional photography --ar 16:9 --v 6"
    print(f"\nテストプロンプト: {test_prompt[:50]}...")
    
    result = client.generate_image_midjourney(test_prompt, aspect_ratio="16:9")
    
    if result.get("status") == "success":
        task_id = result.get("task_id")
        print(f"✅ タスク作成成功: {task_id}")
        
        # ステータスチェック
        print("\n⏳ 生成状態を確認中...")
        for i in range(5):  # 最大5回チェック
            time.sleep(3)
            status = client.check_job_status(task_id)
            print(f"  {i+1}. ステータス: {status.get('status')} - {status.get('message')}")
            
            if status.get('status') == 'completed':
                print(f"✅ 画像生成完了!")
                print(f"  URL: {status.get('result_url')}")
                break
            elif status.get('status') == 'error':
                print(f"❌ エラー: {status.get('message')}")
                break
    else:
        print(f"❌ タスク作成失敗: {result.get('message')}")
        if result.get('details'):
            print(f"詳細: {result.get('details')}")

def diagnose_issues():
    """問題診断と推奨事項"""
    print("\n🔍 診断結果と推奨事項")
    print("=" * 50)
    
    issues = []
    
    # キーチェック
    keys = check_env_keys()
    
    if not keys['PIAPI_KEY']:
        issues.append("PIAPIメインキー(PIAPI_KEY)が未設定")
    
    if not keys['PIAPI_XKEY']:
        issues.append("PIAPI XKey(PIAPI_XKEY)が未設定")
    
    if issues:
        print("\n⚠️ 発見された問題:")
        for issue in issues:
            print(f"  • {issue}")
        
        print("\n💡 解決方法:")
        print("\n1. 環境変数を設定する場合:")
        print("   ```bash")
        print("   export PIAPI_KEY='your-main-key-here'")
        print("   export PIAPI_XKEY='your-x-key-here'")
        print("   ```")
        
        print("\n2. Streamlit Secretsを使用する場合:")
        print("   ~/.streamlit/secrets.toml に以下を追加:")
        print("   ```toml")
        print("   PIAPI_KEY = \"your-main-key-here\"")
        print("   PIAPI_XKEY = \"your-x-key-here\"")
        print("   ```")
        
        print("\n3. PIAPIアカウントの確認:")
        print("   • https://piapi.ai にログイン")
        print("   • ダッシュボードからAPIキーを確認")
        print("   • メインキーとXKeyの両方が必要")
        
    else:
        print("✅ すべての必須キーが設定されています")
        
        # 接続テスト
        if test_piapi_connection(keys['PIAPI_KEY'], keys['PIAPI_XKEY']):
            print("\n✅ PIAPI接続は正常です")
        else:
            print("\n⚠️ PIAPI接続に問題があります")
            print("  • APIキーが正しいか確認してください")
            print("  • クレジット残高を確認してください")
            print("  • レート制限に達していないか確認してください")

def main():
    print("=" * 60)
    print("🎬 PIAPI/Midjourney 統合診断ツール")
    print("=" * 60)
    
    # 環境チェック
    check_env_keys()
    check_streamlit_secrets()
    
    # 接続テスト
    api_key = os.getenv('PIAPI_KEY')
    x_key = os.getenv('PIAPI_XKEY')
    
    if api_key and x_key:
        test_piapi_connection(api_key, x_key)
        test_midjourney_with_piapi()
    
    # 診断
    diagnose_issues()
    
    print("\n" + "=" * 60)
    print("診断完了")
    print("=" * 60)

if __name__ == "__main__":
    main()