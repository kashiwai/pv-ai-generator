---
title: PV AI Video Generator
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
python_version: 3.10
app_file: app.py
pinned: false
license: mit
---

# 🎬 PV自動生成AIエージェント

音楽に合わせて自動的にプロモーションビデオを生成するAIエージェントです。
Hugging Face Spacesで完全動作対応。

## ✨ 主な機能

- 🎵 **最大7分**までの動画生成対応
- 🎨 **Midjourney v6.1** (PiAPI経由) - 高品質画像生成
- 🎥 **Hailuo 02 AI** (PiAPI経由) - 高品質映像生成（推奨）
- 🤖 **複数AI連携**: GPT-4、Claude、Gemini、Deepseekによる構成・台本生成
- 🗣️ **音声合成**: Google TTS / Fish Audio
- 🎨 **キャラクター一貫性**維持機能
- 📱 **Hugging Face Spaces**完全対応

## 🚀 使い方

### ローカル実行
```bash
cd pv_ai_video_agent
source venv/bin/activate
python app.py
```

### Hugging Face Spacesへのデプロイ

1. **Spaceを作成**
   - [Hugging Face](https://huggingface.co)にログイン
   - 「New Space」→ Gradio SDK選択

2. **ファイルをアップロード**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/pv-ai-generator
   cd pv-ai-generator
   cp -r /path/to/pv_ai_video_agent/* .
   git add .
   git commit -m "Initial deployment"
   git push
   ```

3. **Secretsを設定**（Settings → Repository secrets）
   ```
   PIAPI_KEY=your_key（必須：Midjourney + Hailuo統合）
   OPENAI_API_KEY=your_key（オプション）
   GOOGLE_API_KEY=your_key（オプション）
   ANTHROPIC_API_KEY=your_key（オプション）
   FISH_AUDIO_API_KEY=your_key（オプション）
   ```

## 📋 処理フロー

1. 🖼️ キャラクター画像の準備（アップロード or AI生成）
2. 📝 構成案の生成（複数AI案から選択）
3. ✍️ 台本の作成
4. 🗣️ ナレーション音声の合成
5. 🎬 シーンごとの映像生成（8秒×最大60カット）
6. 🎵 音声・映像・BGMの合成
7. ✅ 完成動画の出力

## 📁 プロジェクト構造

```
pv_ai_video_agent/
├── app.py                       # メインアプリケーション（HF Spaces対応）
├── agent_core/
│   ├── character/               # キャラクター管理
│   ├── plot/                    # 構成・台本生成
│   ├── tts/                     # 音声合成
│   ├── video/                   # 映像生成
│   ├── composer/                # 動画合成
│   └── utils/                   # ユーティリティ
├── assets/
│   ├── input/                   # 入力ファイル
│   ├── output/                  # 出力動画
│   ├── temp/                    # 一時ファイル
│   └── characters/              # キャラクター画像
├── config.json                  # 設定ファイル
├── requirements.txt             # 依存関係
└── README.md                    # このファイル
```

## ⚙️ 設定

### 映像生成プロバイダー
- **Hailuo 02 AI**（推奨）: 高品質・安定
- SORA: OpenAI
- VEO3: Google
- Seedance
- DomoAI

### カスタマイズ（config.json）
```json
{
  "video_provider": "hailuo",     // デフォルト: Hailuo 02 AI
  "tts_provider": "google",        // 音声合成
  "scene_duration": 8,             // シーン長さ（秒）
  "max_video_duration": 420        // 最大7分
}
```

## 🎯 推奨スペック

### Hugging Face Spaces
- **無料プラン**: CPU basic（処理遅め）
- **推奨**: GPU T4 small以上（高速処理）

### ローカル環境
- Python 3.11以上
- RAM: 8GB以上
- FFmpeg インストール済み

## 📝 必要なAPIキー

| サービス | 用途 | 必須 |
|---------|------|------|
| PiAPI | Midjourney + Hailuo統合 | ✅ |
| OpenAI | 構成・台本 | ⭕ |
| Google | 音声合成 | ⭕ |
| Anthropic | 構成補助 | ⭕ |
| Fish Audio | 高品質音声 | ⭕ |

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

## 📄 ライセンス

MIT License

## 🔗 リンク

- [Hugging Face Space](https://huggingface.co/spaces/YOUR_USERNAME/pv-ai-generator)
- [GitHub Repository](https://github.com/YOUR_USERNAME/pv-ai-video-agent)
- [Documentation](https://github.com/YOUR_USERNAME/pv-ai-video-agent/wiki)