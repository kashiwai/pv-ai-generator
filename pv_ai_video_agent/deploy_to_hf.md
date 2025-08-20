# 🚀 Hugging Face Spacesへのデプロイ方法

## 前提条件
- Hugging Faceアカウント
- 各種APIキー（Hailuo、OpenAI等）

## デプロイ手順

### 1. Hugging Faceでスペースを作成

1. [Hugging Face](https://huggingface.co) にログイン
2. 「New Space」をクリック
3. 以下を設定:
   - Space name: `pv-ai-generator`（任意）
   - Select the Space SDK: **Gradio**
   - Space hardware: **CPU basic**（無料）または **GPU**（有料・高速）
   - Visibility: Public または Private

### 2. ファイルをアップロード

#### 方法A: Git経由（推奨）
```bash
# リポジトリをクローン
git clone https://huggingface.co/spaces/YOUR_USERNAME/pv-ai-generator
cd pv-ai-generator

# ファイルをコピー
cp -r /path/to/pv_ai_video_agent/* .

# HF用ファイルを使用
mv app_hf.py app.py
mv requirements_hf.txt requirements.txt
mv README_HF.md README.md

# Git設定
git add .
git commit -m "Initial commit"
git push
```

#### 方法B: Web UIから直接アップロード
1. Spaceのページで「Files」タブを開く
2. 「Add file」→「Upload files」
3. 全ファイルをドラッグ&ドロップ

### 3. Secretsの設定

Spaceの「Settings」→「Repository secrets」で以下を追加:

```
HAILUO_API_KEY=your_hailuo_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here（オプション）
FISH_AUDIO_API_KEY=your_fish_audio_key_here（オプション）
```

### 4. 起動確認

1. Spaceが自動的にビルド開始
2. 「Building」→「Running」になるまで待機（5-10分）
3. アプリが表示されたら完了！

## 📁 必要なファイル構造

```
your-space/
├── app.py (app_hf.pyをリネーム)
├── requirements.txt (requirements_hf.txtをリネーム)
├── README.md (README_HF.mdをリネーム)
├── config.json
├── agent_core/
│   ├── character/
│   ├── plot/
│   ├── tts/
│   ├── video/
│   ├── composer/
│   └── utils/
└── assets/
    ├── input/
    ├── output/
    ├── temp/
    └── characters/
```

## ⚙️ トラブルシューティング

### ビルドエラーの場合
- `requirements.txt`のバージョンを確認
- Logsタブでエラー詳細を確認

### メモリ不足の場合
- Space hardwareをアップグレード
- または処理を軽量化（解像度を下げる等）

### APIエラーの場合
- Secretsが正しく設定されているか確認
- APIキーの有効性を確認

## 🎯 推奨設定

### 無料プラン
- CPU basic
- 最大3分の動画
- 低解像度（720p）

### 有料プラン
- GPU T4 small
- 最大7分の動画
- フルHD（1080p）

## 📝 注意事項

- 無料プランは処理が遅い場合があります
- APIの利用制限に注意してください
- 定期的にtempフォルダをクリーンアップ

## 🔗 参考リンク

- [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Gradio Documentation](https://www.gradio.app/docs/)