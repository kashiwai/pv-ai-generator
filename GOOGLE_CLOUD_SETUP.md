# Google Cloud Service Account設定ガイド

## 🔧 Streamlit CloudでのService Account設定

### 1. JSONキーの内容を確認
ダウンロードしたJSONファイルを開いて、以下のような構造を確認：

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\nxxxxx\n-----END PRIVATE KEY-----\n",
  "client_email": "pv-ai-generator@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/xxxxx"
}
```

### 2. Streamlit Cloudに追加

#### 方法A: Streamlit Cloud管理画面から
1. [Streamlit Cloud](https://share.streamlit.io/)にログイン
2. あなたのアプリ → **Settings** → **Secrets**
3. 以下の形式でJSONの内容を追加：

```toml
[GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\nxxxxx\n-----END PRIVATE KEY-----\n"
client_email = "pv-ai-generator@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/xxxxx"

# プロジェクトIDも別途設定（オプション）
GOOGLE_CLOUD_PROJECT = "your-project-id"
```

#### 方法B: ローカルでテスト（.streamlit/secrets.toml）
```bash
# ローカルテスト用
mkdir -p ~/.streamlit
nano ~/.streamlit/secrets.toml
# 上記と同じ内容を貼り付け
```

### 3. 必要なAPIを有効化

Google Cloud Consoleで以下のAPIを有効化：

1. **Vertex AI API**
   ```
   https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
   ```

2. **Generative Language API** (Gemini用)
   ```
   https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   ```

### 4. 確認事項

- [ ] Service Accountが作成されている
- [ ] Vertex AI Userロールが付与されている
- [ ] JSONキーがダウンロードされている
- [ ] Streamlit Secretsに追加されている
- [ ] 必要なAPIが有効化されている

## ⚠️ 重要な注意事項

1. **private_keyの改行に注意**
   - `\n`はそのまま記述（改行しない）
   - 実際の改行は`\n`として保存

2. **JSONキーのセキュリティ**
   - GitHubにコミットしない
   - 安全な場所に保管
   - 不要になったら削除

3. **プロジェクトID確認方法**
   ```bash
   gcloud config get-value project
   ```
   または、Google Cloud Console右上のプロジェクト選択メニューで確認

## 🚀 デプロイ後の確認

Streamlit Cloudにデプロイ後、アプリ内で以下が表示されれば成功：

```
✅ Google Cloud Service Account設定完了 (Project: your-project-id)
```

エラーが出る場合は、以下を確認：
- Service Accountの権限
- APIの有効化状態
- Secretsの記述形式（特にprivate_keyの改行）