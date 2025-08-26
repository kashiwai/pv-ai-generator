#!/usr/bin/env python3
"""
Google Cloud SDK設定ヘルパー
Streamlit Cloud用のGoogle Cloud認証設定
"""

import os
import json
import base64
import streamlit as st
from pathlib import Path

def setup_google_cloud_auth():
    """
    Google Cloud認証を設定（Streamlit Cloud対応）
    """
    
    # 方法1: Streamlit SecretsからService Account JSONを取得
    if hasattr(st, 'secrets') and 'GOOGLE_SERVICE_ACCOUNT' in st.secrets:
        try:
            # SecretsからService Account情報を取得
            service_account_info = dict(st.secrets['GOOGLE_SERVICE_ACCOUNT'])
            
            # 一時ファイルとして保存
            temp_path = Path('/tmp/google-service-account.json')
            with open(temp_path, 'w') as f:
                json.dump(service_account_info, f)
            
            # 環境変数に設定
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(temp_path)
            
            # プロジェクトIDを設定
            if 'project_id' in service_account_info:
                os.environ['GOOGLE_CLOUD_PROJECT'] = service_account_info['project_id']
                
            return True, service_account_info.get('project_id', 'unknown')
            
        except Exception as e:
            st.warning(f"⚠️ Service Account設定エラー: {str(e)}")
    
    # 方法2: APIキーベースの簡易認証（制限あり）
    if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
        os.environ['GOOGLE_API_KEY'] = st.secrets['GOOGLE_API_KEY']
        return False, None
    
    # 方法3: セッション状態からAPIキーを取得
    if 'api_keys' in st.session_state and st.session_state.api_keys.get('google'):
        os.environ['GOOGLE_API_KEY'] = st.session_state.api_keys['google']
        return False, None
    
    return False, None

def create_service_account_template():
    """
    Service Accountテンプレートを生成（ユーザー設定用）
    """
    template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nyour-private-key\\n-----END PRIVATE KEY-----\\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
    }
    
    return template

def setup_vertex_ai_with_api_key():
    """
    APIキーのみでVertex AIを設定（制限付き）
    """
    import google.auth
    from google.auth.credentials import AnonymousCredentials
    
    # APIキー認証（制限あり）
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    
    if api_key:
        # 匿名認証を使用（APIキーはリクエスト時に付加）
        credentials = AnonymousCredentials()
        
        # プロジェクトIDは自動検出または手動設定
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
        
        return credentials, project_id
    
    return None, None

# Streamlit Cloudでの設定方法
SETUP_INSTRUCTIONS = """
## 🔧 Google Cloud設定方法

### 方法1: Service Account（推奨）
1. Google Cloud Consoleでサービスアカウントを作成
2. 「Vertex AI User」ロールを付与
3. JSONキーをダウンロード
4. Streamlit Secretsに追加:
   ```toml
   [GOOGLE_SERVICE_ACCOUNT]
   type = "service_account"
   project_id = "your-project-id"
   private_key_id = "xxx"
   private_key = "-----BEGIN PRIVATE KEY-----\\nxxx\\n-----END PRIVATE KEY-----\\n"
   client_email = "xxx@xxx.iam.gserviceaccount.com"
   client_id = "xxx"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "xxx"
   ```

### 方法2: APIキー（簡易・制限あり）
1. Google Cloud ConsoleでAPIキーを作成
2. Generative Language APIを有効化
3. Streamlit Secretsに追加:
   ```toml
   GOOGLE_API_KEY = "AIzaSyXXXXXXXXXXXXX"
   ```
"""

def initialize_google_cloud():
    """
    Google Cloud SDKを初期化（メイン関数）
    """
    
    # 認証設定
    has_service_account, project_id = setup_google_cloud_auth()
    
    if has_service_account:
        st.success(f"✅ Google Cloud Service Account設定完了 (Project: {project_id})")
        
        try:
            # Vertex AIを初期化
            import vertexai
            vertexai.init(project=project_id, location="us-central1")
            return True
        except Exception as e:
            st.warning(f"⚠️ Vertex AI初期化エラー: {str(e)}")
            return False
            
    elif os.environ.get('GOOGLE_API_KEY'):
        st.info("ℹ️ Google APIキーで動作中（一部機能制限あり）")
        return True
    else:
        st.warning("⚠️ Google Cloud認証が設定されていません")
        with st.expander("設定方法を見る"):
            st.markdown(SETUP_INSTRUCTIONS)
        return False

# エクスポート
if __name__ == "__main__":
    # スタンドアロンテスト
    print("Google Cloud SDK設定テスト")
    print("="*50)
    
    # 環境変数チェック
    print(f"GOOGLE_API_KEY: {'設定済み' if os.environ.get('GOOGLE_API_KEY') else '未設定'}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {'設定済み' if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else '未設定'}")
    print(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', '未設定')}")
    
    # テンプレート生成
    template = create_service_account_template()
    print("\nService Accountテンプレート:")
    print(json.dumps(template, indent=2))