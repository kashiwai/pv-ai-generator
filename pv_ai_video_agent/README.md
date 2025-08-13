---
title: PV AI Video Generator
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: streamlit
sdk_version: 1.39.0
app_file: streamlit_app.py
pinned: false
license: mit
---

# 🎬 PV自動生成AIエージェント

音楽に合わせて自動的にプロモーションビデオを生成するAIエージェントです。
Streamlit Cloudで稼働中。

🔗 **デプロイ済みアプリ**: https://pv-ai-generator-8tfxczsibmrquxq9ybjxgi.streamlit.app/

## ✨ 主な機能

- 🎵 **最大7分**までの動画生成対応
- 🤖 **複数AI連携**: GPT-4、Claude、Gemini、Deepseekによる構成・台本生成
- 🎥 **Hailuo 02 AI**による高品質映像生成（メイン推奨）
- 🗣️ **音声合成**: Google TTS / Fish Audio
- 🎨 **キャラクター一貫性**維持機能
- 📱 **Hugging Face Spaces**完全対応

## 🚀 使い方

### ローカル実行
```bash
cd pv_ai_video_agent
source venv/bin/activate
streamlit run streamlit_app.py
```

### Hugging Face Spacesへのデプロイ

1. **Spaceを作成**
   - [Hugging Face](https://huggingface.co)にログイン
   - 「New Space」→ Streamlit SDK選択

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
   PIAPI_KEY=your_main_key
   PIAPI_XKEY=your_x_key
   OPENAI_API_KEY=your_key
   GOOGLE_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key（オプション）
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
├── streamlit_app.py             # メインアプリケーション（Streamlit版）
├── app.py                       # Gradio版（レガシー）
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
- **Hailuo AI**（推奨）: PIAPI経由で高品質・安定
- **Midjourney**: PIAPI経由で画像生成
- SORA: OpenAI
- VEO3: Google
- Seedance
- DomoAI

### カスタマイズ（config.json）
```json
{
  "video_provider": "hailuo",     // デフォルト: Hailuo AI（PIAPI経由）
  "image_provider": "midjourney",  // 画像生成（PIAPI経由）
  "tts_provider": "google",        // 音声合成
  "scene_duration": 8,             // シーン長さ（秒）
  "max_video_duration": 420        // 最大7分
}
```

## 🎯 推奨スペック

### Hugging Face Spaces / Streamlit Cloud
- **無料プラン**: CPU basic（処理遅め）
- **推奨**: GPU T4 small以上（高速処理）
- **Streamlit Cloud**: 自動スケーリング対応

### ローカル環境
- Python 3.11以上
- RAM: 8GB以上
- FFmpeg インストール済み

## 📝 必要なAPIキー

| サービス | 用途 | 必須 |
|---------|------|------|
| PIAPI Key | 認証用メインキー | ✅ |
| PIAPI XKey | Midjourney/Hailuo用 | ✅ |
| OpenAI | 構成・台本 | ✅ |
| Google | 音声合成 | ✅ |
| Anthropic | 構成補助 | ⭕ |

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

## 📄 ライセンス

MIT License

## 🔗 リンク

- [Streamlit Cloud App](https://pv-ai-generator-8tfxczsibmrquxq9ybjxgi.streamlit.app/)
- [GitHub Repository](https://github.com/YOUR_USERNAME/pv-ai-video-agent)
- [Documentation](https://github.com/YOUR_USERNAME/pv-ai-video-agent/wiki)