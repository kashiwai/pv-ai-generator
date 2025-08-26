#!/usr/bin/env python3
"""
Service Account JSON設定スクリプト
"""

import json
import sys
from pathlib import Path

def setup_service_account(json_path):
    """
    Service Account JSONをsecrets.tomlに設定
    """
    
    # JSONファイルを読み込み
    with open(json_path, 'r') as f:
        service_account = json.load(f)
    
    # secrets.tomlのパス
    secrets_path = Path.home() / '.streamlit' / 'secrets.toml'
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 既存のsecrets.tomlを読み込み
    existing_content = ""
    if secrets_path.exists():
        with open(secrets_path, 'r') as f:
            existing_content = f.read()
    
    # GOOGLE_SERVICE_ACCOUNTセクションを作成
    service_account_section = "\n\n# Google Cloud Service Account\n[GOOGLE_SERVICE_ACCOUNT]\n"
    
    for key, value in service_account.items():
        if isinstance(value, str):
            # private_keyの改行を適切に処理
            if key == "private_key":
                # 改行をエスケープ
                value = value.replace('\n', '\\n')
            # 値を適切にクォート
            service_account_section += f'{key} = "{value}"\n'
        else:
            service_account_section += f'{key} = {json.dumps(value)}\n'
    
    # プロジェクトIDも追加
    if 'project_id' in service_account:
        service_account_section += f'\n# Project ID\nGOOGLE_CLOUD_PROJECT = "{service_account["project_id"]}"\n'
    
    # secrets.tomlに追加
    with open(secrets_path, 'w') as f:
        # 既存のGOOGLE_SERVICE_ACCOUNTセクションを削除
        import re
        existing_content = re.sub(
            r'\[GOOGLE_SERVICE_ACCOUNT\].*?(?=\n\[|\Z)',
            '',
            existing_content,
            flags=re.DOTALL
        )
        
        f.write(existing_content.strip())
        f.write(service_account_section)
    
    print(f"✅ Service Accountを設定しました: {secrets_path}")
    print(f"📋 Project ID: {service_account.get('project_id', 'N/A')}")
    print(f"📧 Service Account: {service_account.get('client_email', 'N/A')}")
    
    return service_account

def test_connection(service_account):
    """
    接続テスト
    """
    print("\n🔄 接続テスト中...")
    
    import os
    os.environ['GOOGLE_CLOUD_PROJECT'] = service_account.get('project_id', '')
    
    # テスト用の認証情報を作成
    temp_path = Path('/tmp/google-service-account.json')
    with open(temp_path, 'w') as f:
        json.dump(service_account, f)
    
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(temp_path)
    
    try:
        # Google Cloud認証テスト
        import google.auth
        credentials, project = google.auth.default()
        print(f"✅ 認証成功: Project = {project}")
        
        # Vertex AI接続テスト
        try:
            import vertexai
            vertexai.init(project=project, location="us-central1")
            print("✅ Vertex AI接続成功")
        except Exception as e:
            print(f"⚠️ Vertex AI接続エラー: {str(e)}")
            
    except Exception as e:
        print(f"❌ 認証エラー: {str(e)}")
        print("\n💡 以下を確認してください:")
        print("1. Service Accountに適切なロールが付与されているか")
        print("2. Vertex AI APIが有効化されているか")
        print("3. プロジェクトIDが正しいか")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python setup_service_account.py <JSONファイルのパス>")
        print("例: python setup_service_account.py ~/Downloads/pv-ai-generator-xxxxx.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not Path(json_path).exists():
        print(f"❌ ファイルが見つかりません: {json_path}")
        sys.exit(1)
    
    # Service Account設定
    service_account = setup_service_account(json_path)
    
    # 接続テスト
    test_connection(service_account)