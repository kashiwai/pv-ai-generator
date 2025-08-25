#!/usr/bin/env python3
"""
PIAPI設定確認スクリプト
現在の設定状況を確認し、問題を診断
"""

import os
import sys
import json
from pathlib import Path

def check_streamlit_cloud():
    """Streamlit Cloud設定を確認"""
    print("\n☁️ Streamlit Cloud設定確認")
    print("-" * 50)
    
    # デプロイ済みURL
    app_url = "https://pv-ai-generator-8tfxczsibmrquxq9ybjxgi.streamlit.app/"
    print(f"デプロイURL: {app_url}")
    print("\n重要: Streamlit CloudのSecretsは以下から設定:")
    print("1. アプリのメニュー → Settings → Secrets")
    print("2. 以下のキーを設定:")
    print("   - PIAPI_KEY (メインキー)")
    print("   - PIAPI_XKEY (Xキー)")

def check_local_setup():
    """ローカル設定を確認"""
    print("\n💻 ローカル環境設定確認")
    print("-" * 50)
    
    # Streamlit secrets
    secrets_file = Path.home() / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        print(f"✅ Streamlit secrets存在: {secrets_file}")
        try:
            import toml
            with open(secrets_file, 'r') as f:
                secrets = toml.load(f)
            
            keys = ['PIAPI_KEY', 'PIAPI_XKEY', 'OPENAI_API_KEY']
            for key in keys:
                if key in secrets and secrets[key]:
                    val = secrets[key]
                    masked = val[:8] + "..." if len(val) > 8 else "***"
                    print(f"  ✅ {key}: {masked}")
                else:
                    print(f"  ❌ {key}: 未設定")
        except Exception as e:
            print(f"  エラー: {e}")
    else:
        print(f"❌ Streamlit secrets未作成")
        print(f"  作成場所: {secrets_file}")
    
    # 環境変数
    print("\n環境変数:")
    env_keys = ['PIAPI_KEY', 'PIAPI_XKEY']
    for key in env_keys:
        val = os.getenv(key)
        if val:
            masked = val[:8] + "..." if len(val) > 8 else "***"
            print(f"  ✅ {key}: {masked}")
        else:
            print(f"  ❌ {key}: 未設定")

def check_piapi_integration():
    """PIAPI統合の確認"""
    print("\n🔌 PIAPI統合確認")
    print("-" * 50)
    
    # piapi_integration.pyの確認
    piapi_file = Path("pv-ai-generator/piapi_integration.py")
    if piapi_file.exists():
        print(f"✅ PIAPI統合モジュール存在")
        
        with open(piapi_file, 'r') as f:
            content = f.read()
        
        # 重要な関数の存在確認
        functions = [
            "generate_image_midjourney",
            "check_job_status",
            "generate_character_consistent_images"
        ]
        
        for func in functions:
            if f"def {func}" in content:
                print(f"  ✅ {func}関数: 実装済み")
            else:
                print(f"  ❌ {func}関数: 未実装")
    else:
        print(f"❌ PIAPI統合モジュールが見つかりません")

def suggest_fixes():
    """修正提案"""
    print("\n💡 推奨される修正手順")
    print("=" * 50)
    
    print("\n1. ローカルテスト用の設定:")
    print("   mkdir -p ~/.streamlit")
    print("   cat > ~/.streamlit/secrets.toml << 'EOF'")
    print("   PIAPI_KEY = \"your-main-key\"")
    print("   PIAPI_XKEY = \"your-x-key\"")
    print("   EOF")
    
    print("\n2. Streamlit Cloudの設定:")
    print("   a. https://share.streamlit.io にログイン")
    print("   b. アプリを選択 → Settings → Secrets")
    print("   c. 上記と同じキーを設定")
    
    print("\n3. PIAPIアカウントの確認:")
    print("   a. https://piapi.ai にログイン")
    print("   b. ダッシュボードでキーを確認")
    print("   c. クレジット残高を確認")
    
    print("\n4. テスト実行:")
    print("   python3 test_piapi_midjourney.py")

def check_recent_errors():
    """最近のエラーログを確認"""
    print("\n📝 最近のエラー傾向")
    print("-" * 50)
    
    common_errors = {
        "401": "認証エラー - APIキーが無効",
        "403": "権限エラー - アクセス権限なし",
        "429": "レート制限 - API呼び出し頻度超過",
        "insufficient quota": "クレジット不足",
        "daily limit": "デイリー制限到達"
    }
    
    print("よくあるエラーと対処法:")
    for error, solution in common_errors.items():
        print(f"  • {error}: {solution}")

def main():
    print("=" * 60)
    print("🎬 PIAPI/Midjourney 設定診断")
    print("=" * 60)
    
    # 各種チェック
    check_streamlit_cloud()
    check_local_setup()
    check_piapi_integration()
    check_recent_errors()
    
    # 修正提案
    suggest_fixes()
    
    print("\n" + "=" * 60)
    print("診断完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. 上記の設定を確認")
    print("2. python3 test_piapi_midjourney.py でテスト")
    print("3. streamlit run pv-ai-generator/streamlit_app.py でローカル起動")

if __name__ == "__main__":
    main()