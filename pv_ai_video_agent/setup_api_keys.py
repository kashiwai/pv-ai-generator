#!/usr/bin/env python3
"""
APIキー設定ヘルパースクリプト
ローカル開発環境用のAPIキー設定を支援
"""

import os
import sys
from pathlib import Path
import getpass

def setup_streamlit_secrets():
    """Streamlit secrets.tomlファイルを設定"""
    secrets_dir = Path.home() / ".streamlit"
    secrets_file = secrets_dir / "secrets.toml"
    
    print("🔐 Streamlit Secrets設定")
    print("-" * 50)
    
    # ディレクトリ作成
    secrets_dir.mkdir(exist_ok=True)
    
    # 既存のsecretsをチェック
    existing_keys = {}
    if secrets_file.exists():
        print(f"既存のsecretsファイルが見つかりました: {secrets_file}")
        response = input("上書きしますか？ (y/n): ")
        if response.lower() != 'y':
            print("設定をキャンセルしました")
            return
        
        # 既存の内容を読み込み（バックアップ用）
        import toml
        try:
            with open(secrets_file, 'r') as f:
                existing_keys = toml.load(f)
        except:
            pass
    
    print("\nPIAPIキーを入力してください")
    print("（https://piapi.ai のダッシュボードから取得）\n")
    
    # PIAPIメインキー
    piapi_key = getpass.getpass("PIAPI_KEY (メインキー): ")
    if not piapi_key:
        piapi_key = existing_keys.get('PIAPI_KEY', '')
    
    # PIAPI XKEY
    piapi_xkey = getpass.getpass("PIAPI_XKEY (Xキー): ")
    if not piapi_xkey:
        piapi_xkey = existing_keys.get('PIAPI_XKEY', '')
    
    # その他のAPIキー（オプション）
    print("\nその他のAPIキー（オプション、Enterでスキップ）")
    
    openai_key = getpass.getpass("OPENAI_API_KEY: ")
    if not openai_key:
        openai_key = existing_keys.get('OPENAI_API_KEY', '')
    
    google_key = getpass.getpass("GOOGLE_API_KEY: ")
    if not google_key:
        google_key = existing_keys.get('GOOGLE_API_KEY', '')
    
    anthropic_key = getpass.getpass("ANTHROPIC_API_KEY: ")
    if not anthropic_key:
        anthropic_key = existing_keys.get('ANTHROPIC_API_KEY', '')
    
    # secrets.toml作成
    secrets_content = f'''# Streamlit Secrets Configuration
# このファイルは.gitignoreに含まれるべきです

# PIAPI設定（必須）
PIAPI_KEY = "{piapi_key}"
PIAPI_XKEY = "{piapi_xkey}"

# その他のAPI設定（オプション）
OPENAI_API_KEY = "{openai_key}"
GOOGLE_API_KEY = "{google_key}"
ANTHROPIC_API_KEY = "{anthropic_key}"

# Midjourney/Hailuo設定（PIAPIを使用）
MIDJOURNEY_API_KEY = "{piapi_xkey}"
HAILUO_API_KEY = "{piapi_key}"
'''
    
    # ファイル保存
    with open(secrets_file, 'w') as f:
        f.write(secrets_content)
    
    # パーミッション設定（読み取り専用）
    os.chmod(secrets_file, 0o600)
    
    print(f"\n✅ Secretsファイルを作成しました: {secrets_file}")
    print("   （このファイルは自動的に.gitignoreされます）")
    
    # テスト実行を提案
    print("\n次のコマンドでテストできます:")
    print("  python3 test_piapi_midjourney.py")

def setup_env_file():
    """.envファイルを設定"""
    env_file = Path(".env")
    
    print("\n📄 .envファイル設定")
    print("-" * 50)
    
    if env_file.exists():
        print(f"既存の.envファイルが見つかりました: {env_file}")
        response = input("上書きしますか？ (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\n環境変数用の.envファイルを作成します")
    
    # キー入力
    piapi_key = getpass.getpass("PIAPI_KEY: ")
    piapi_xkey = getpass.getpass("PIAPI_XKEY: ")
    
    env_content = f'''# Local Development Environment Variables
PIAPI_KEY={piapi_key}
PIAPI_XKEY={piapi_xkey}
'''
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ .envファイルを作成しました: {env_file}")
    
    # .gitignoreに追加
    gitignore = Path(".gitignore")
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            content = f.read()
        if '.env' not in content:
            with open(gitignore, 'a') as f:
                f.write("\n# Environment variables\n.env\n")
            print("✅ .envを.gitignoreに追加しました")

def verify_setup():
    """設定を確認"""
    print("\n🔍 設定確認")
    print("-" * 50)
    
    # Streamlit secrets確認
    secrets_file = Path.home() / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        print(f"✅ Streamlit secrets: {secrets_file}")
        try:
            import toml
            with open(secrets_file, 'r') as f:
                secrets = toml.load(f)
            
            if secrets.get('PIAPI_KEY') and secrets.get('PIAPI_XKEY'):
                print("  ✅ PIAPIキーが設定されています")
            else:
                print("  ⚠️ PIAPIキーが不完全です")
        except Exception as e:
            print(f"  ❌ エラー: {e}")
    else:
        print("❌ Streamlit secretsが見つかりません")
    
    # .env確認
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .envファイル: {env_file}")
    
    # テストコマンド
    print("\n📝 次のステップ:")
    print("1. テストを実行:")
    print("   python3 test_piapi_midjourney.py")
    print("\n2. Streamlitアプリを起動:")
    print("   streamlit run pv-ai-generator/streamlit_app.py")

def main():
    print("=" * 60)
    print("🎬 PV AI Generator - APIキー設定ツール")
    print("=" * 60)
    
    print("\nどの方法で設定しますか？")
    print("1. Streamlit Secrets（推奨）")
    print("2. .envファイル")
    print("3. 両方")
    print("4. 設定確認のみ")
    
    choice = input("\n選択 (1-4): ")
    
    if choice == '1':
        setup_streamlit_secrets()
    elif choice == '2':
        setup_env_file()
    elif choice == '3':
        setup_streamlit_secrets()
        setup_env_file()
    elif choice == '4':
        pass
    else:
        print("無効な選択です")
        return
    
    # 設定確認
    verify_setup()
    
    print("\n" + "=" * 60)
    print("設定完了")
    print("=" * 60)

if __name__ == "__main__":
    main()