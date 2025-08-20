---
title: PV AI Video Generator
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app_hf.py
pinned: false
license: mit
---

# 🎬 PV自動生成AIエージェント

音楽に合わせて自動的にプロモーションビデオを生成するAIエージェントです。

## ✨ 特徴

- 🎵 **最大7分**までの動画生成対応
- 🤖 **複数AI連携**: GPT-4、Claude、Gemini、Deepseekによる構成・台本生成
- 🎥 **Hailuo 02 AI**による高品質映像生成（メイン）
- 🗣️ **音声合成**: Google TTS / Fish Audio
- 🎨 **キャラクター一貫性**維持機能

## 🚀 使い方

1. **基本情報を入力**
   - タイトル、キーワード、雰囲気を設定

2. **コンテンツを追加**
   - 歌詞またはメッセージを入力
   - 音楽ファイル（MP3/WAV）をアップロード

3. **キャラクター設定**（オプション）
   - 画像をアップロード、またはAIで自動生成

4. **PV生成開始**
   - 「🚀 PV生成開始」ボタンをクリック
   - 処理完了まで待機（3-10分程度）

## ⚙️ 設定

### Secretsに追加が必要なAPIキー

- `HAILUO_API_KEY` - Hailuo 02 AI（映像生成）
- `OPENAI_API_KEY` - OpenAI GPT-4（構成・台本）
- `GOOGLE_API_KEY` - Google Gemini & TTS
- `ANTHROPIC_API_KEY` - Claude（オプション）
- `FISH_AUDIO_API_KEY` - Fish Audio（オプション）

## 📋 処理フロー

1. 🖼️ キャラクター画像の準備
2. 📝 構成案の生成（複数AI案）
3. ✍️ 台本の作成
4. 🗣️ ナレーション音声の合成
5. 🎬 シーンごとの映像生成（8秒×最大60カット）
6. 🎵 音声・映像・BGMの合成
7. ✅ 完成動画の出力

## 🎯 推奨設定

- **映像生成**: Hailuo 02 AI（高品質・安定）
- **音声合成**: Google TTS（多言語対応）
- **解像度**: 1920×1080（フルHD）
- **FPS**: 30

## 📝 注意事項

- 処理時間は動画の長さによって変動します
- APIキーは必ず設定してください
- 無料枠では生成回数に制限がある場合があります

## 🔗 リンク

- [GitHub](https://github.com/yourusername/pv-ai-video-agent)
- [Documentation](https://github.com/yourusername/pv-ai-video-agent/wiki)

## 📄 ライセンス

MIT License