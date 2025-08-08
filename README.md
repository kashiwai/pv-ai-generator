# PV自動生成AIエージェント

Midjourney × Hailuo × Fish Audioを使用した高品質PV自動生成システム

## 🚀 デモ

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/kashiwai/pv-ai-generator/main/app.py)

## ✨ 特徴

- **Midjourney v6.1** - 高品質な画像生成
- **Hailuo AI** - スムーズな動画生成  
- **Fish Audio** - 自然なTTS
- **音楽アップロード対応** - MP3, WAV, M4A等
- **最大7分のPV生成** - プロ品質の長編動画

## 📦 インストール

```bash
git clone https://github.com/yourusername/pv-ai-generator
cd pv-ai-generator
pip install -r requirements.txt
```

## 🔑 API設定

### 環境変数（推奨）

`.env`ファイルを作成:

```env
PIAPI_KEY=your_piapi_key
MIDJOURNEY_API_KEY=your_midjourney_key
HAILUO_API_KEY=your_hailuo_key
FISH_AUDIO_KEY=your_fish_audio_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

### Streamlit Secrets（Streamlit Cloud用）

`.streamlit/secrets.toml`:

```toml
PIAPI_KEY = "your_piapi_key"
MIDJOURNEY_API_KEY = "your_midjourney_key"
HAILUO_API_KEY = "your_hailuo_key"
FISH_AUDIO_KEY = "your_fish_audio_key"
```

## 🎮 使い方

### ローカル実行

```bash
streamlit run app.py
```

### Streamlit Cloudデプロイ

1. GitHubにリポジトリをpush
2. [Streamlit Cloud](https://share.streamlit.io)にログイン
3. 新しいアプリをデプロイ
4. SecretsタブでAPIキーを設定

## 📁 プロジェクト構成

```
pv-ai-generator/
├── app.py                 # メインアプリケーション
├── requirements.txt       # 依存関係
├── core/
│   ├── __init__.py
│   ├── script_generator.py   # 台本生成
│   ├── image_generator.py    # Midjourney統合
│   ├── video_generator.py    # Hailuo統合
│   ├── audio_processor.py    # 音声処理
│   └── pv_generator.py       # PV生成統合
└── utils/
    ├── __init__.py
    └── api_client.py         # API通信
```

## 🎯 使用例

1. **タイトルとキーワード入力**
   - タイトル: "青春の夢"
   - キーワード: 青春, 友情, 冒険

2. **音楽アップロード**
   - MP3/WAVファイルをアップロード

3. **スタイル選択**
   - anime, cinematic, realistic等

4. **生成開始**
   - 3-5分で完成

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します！

## 📧 サポート

問題がある場合はIssueを作成してください。
EOF < /dev/null