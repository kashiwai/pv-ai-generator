# Streamlit Cloudデプロイ手順

## 1. GitHubにリポジトリ作成

```bash
# GitHubで新しいリポジトリを作成
# リポジトリ名: pv-ai-generator

# ローカルからpush
git add .
git commit -m "Initial commit: PV AI Generator for Streamlit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pv-ai-generator.git
git push -u origin main
```

## 2. Streamlit Cloudでデプロイ

1. [share.streamlit.io](https://share.streamlit.io)にアクセス
2. GitHubアカウントでログイン
3. "New app"をクリック
4. 以下を設定:
   - Repository: `YOUR_USERNAME/pv-ai-generator`
   - Branch: `main`
   - Main file path: `app.py`
5. "Deploy\!"をクリック

## 3. APIキー設定（重要）

デプロイ後、アプリの設定画面で:

1. "Settings"タブを開く
2. "Secrets"セクションを選択
3. 以下を追加:

```toml
PIAPI_KEY = "your_actual_piapi_key"
MIDJOURNEY_API_KEY = "your_actual_midjourney_key"
HAILUO_API_KEY = "your_actual_hailuo_key"
FISH_AUDIO_KEY = "your_actual_fish_audio_key"
OPENAI_API_KEY = "your_actual_openai_key"
GOOGLE_API_KEY = "your_actual_google_key"
```

4. "Save"をクリック

## 4. 動作確認

- URLは: `https://YOUR_APP_NAME.streamlit.app`
- 音楽ファイルアップロードが動作するか確認
- API接続が正常か確認

## トラブルシューティング

### エラー: "ModuleNotFoundError"
→ requirements.txtを確認

### エラー: "API key not found"
→ Secretsが正しく設定されているか確認

### ファイルアップロードが失敗
→ .streamlit/config.tomlのmaxUploadSizeを確認
EOF < /dev/null