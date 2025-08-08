# Hugging Face Spaces デプロイ完全手順

## 1. Hugging Face Spacesにプッシュ

### 方法A: Git経由でプッシュ（推奨）

```bash
# 1. 現在のディレクトリで作業
cd /Users/kotarokashiwai/PVmovieegent/pv_ai_video_agent/pv-ai-generator

# 2. Hugging Faceリポジトリを追加
git remote add huggingface https://huggingface.co/spaces/mmz2501/pv-ai-generator

# 3. Hugging Faceにログイン（初回のみ）
# ブラウザで https://huggingface.co/settings/tokens にアクセス
# "New token"をクリックして、Write権限のトークンを作成
# 以下のコマンドでユーザー名とトークンを入力
git config --global credential.helper store

# 4. プッシュ
git push huggingface main

# もしmainブランチがない場合
git push huggingface master:main
```

### 方法B: Webインターフェース経由

1. https://huggingface.co/spaces/mmz2501/pv-ai-generator にアクセス
2. "Files and versions"タブをクリック
3. "Add file" → "Upload files"を選択
4. 以下のファイルをアップロード:
   - app.py
   - requirements.txt
   - config.json
   - packages.txt
   - DEPLOYMENT.md
   - agent_core/ フォルダ全体
   - assets/ フォルダ構造（空フォルダ）

## 2. APIキーをSecretsに設定

### 設定手順

1. **Spaceの設定ページにアクセス**
   ```
   https://huggingface.co/spaces/mmz2501/pv-ai-generator/settings
   ```

2. **"Repository secrets"セクションを開く**

3. **以下のAPIキーを追加**（必要なものだけでOK）

#### 必須APIキー（最低限1つ）
```
OPENAI_API_KEY = sk-xxx...          # GPT-4用
または
ANTHROPIC_API_KEY = sk-ant-xxx...   # Claude用
または
GOOGLE_API_KEY = AIzaSy...          # Gemini用
```

#### 推奨APIキー（高品質生成）
```
MIDJOURNEY_API_KEY = xxx...         # 画像生成（最優先）
PIAPI_KEY = xxx...                 # Hailuo 02映像生成（PiAPI経由・推奨）
  または
HAILUO_API_KEY = xxx...            # 同上（互換性のため）
VEO3_API_KEY = xxx...              # 映像生成（推奨）
```

#### PiAPIの取得方法
1. https://piapi.ai にアクセス
2. アカウント作成
3. Dashboard → API Keysでキーを取得
4. `PIAPI_KEY`または`HAILUO_API_KEY`として設定

#### オプションAPIキー
```
DEEPSEEK_API_KEY = xxx...          # 代替LLM
FISH_AUDIO_API_KEY = xxx...        # 高品質TTS
SORA_API_KEY = xxx...              # OpenAI映像生成
SEEDANCE_API_KEY = xxx...          # 代替映像生成
DOMOAI_API_KEY = xxx...            # 代替映像生成
```

### APIキーの追加方法

1. "New secret"ボタンをクリック
2. Name欄に`OPENAI_API_KEY`などのキー名を入力
3. Value欄にAPIキーの値を入力
4. "Save"をクリック
5. 各APIキーについて繰り返す

## 3. 自動的にビルド・起動

### ビルドプロセス

Spacesは自動的に以下を実行:

1. **依存関係のインストール**
   - requirements.txtから自動インストール
   - packages.txt（システムパッケージ）から自動インストール

2. **アプリケーションの起動**
   - app.pyを自動実行
   - Gradio UIが自動的に公開

### 確認方法

1. **ビルドログの確認**
   ```
   https://huggingface.co/spaces/mmz2501/pv-ai-generator
   ```
   → "Logs"タブでビルド状況を確認

2. **ステータス確認**
   - 🟢 Running: 正常稼働中
   - 🟡 Building: ビルド中（5-10分かかる場合あり）
   - 🔴 Error: エラー発生（ログを確認）

3. **動作テスト**
   - タイトル入力: "テストPV"
   - 音楽ファイル: 短い音楽ファイルをアップロード
   - "PV生成開始"をクリック
   - プログレスバーが進行することを確認

## トラブルシューティング

### よくあるエラーと対処法

#### 1. "Build failed"エラー
```bash
# requirements.txtを確認
gradio==4.36.0  # バージョンを固定
moviepy==1.0.3   # Python 3.10互換
```

#### 2. "No module named 'xxx'"エラー
```bash
# requirements.txtに追加
pip install xxx
```

#### 3. APIキーエラー
```
Error: OPENAI_API_KEY not found
```
→ Settings → Repository secretsで設定

#### 4. メモリエラー
```
# Settings → Hardwareで変更
CPU basic → CPU upgrade
または
CPU basic → GPU small
```

## 完全デプロイチェックリスト

- [ ] Gitリポジトリの準備完了
- [ ] すべてのファイルをプッシュ
- [ ] 最低1つのAPIキーを設定
- [ ] ビルドが成功（緑色のRunning表示）
- [ ] UIが正常に表示
- [ ] テスト生成が動作

## コマンドまとめ

```bash
# 一括実行用
cd /Users/kotarokashiwai/PVmovieegent/pv_ai_video_agent/pv-ai-generator
git remote add huggingface https://huggingface.co/spaces/mmz2501/pv-ai-generator
git push huggingface main
```

## サポート

問題が発生した場合:
1. Logsタブでエラー詳細を確認
2. requirements.txtのバージョンを確認
3. APIキーが正しく設定されているか確認

---

**重要**: シンプル化は禁止。すべての機能を完全実装で動作させること。