#!/bin/bash

# 最小構成セットアップ（エラーが出ても動作する最小限のパッケージのみ）
echo "🎬 PV AIエージェント - 最小構成セットアップ"
echo "============================================"

# Python3チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3が必要です: brew install python@3.11"
    exit 1
fi

# 仮想環境作成
echo "📦 仮想環境を作成..."
python3 -m venv venv
source venv/bin/activate

# 最小限の必須パッケージのみインストール
echo "📦 必須パッケージをインストール..."
pip install --upgrade pip

# 絶対に必要なもののみ
pip install gradio
pip install Pillow
pip install numpy
pip install requests
pip install pyyaml

# 音声処理（エラーが出ても続行）
echo "🎵 音声パッケージを試行..."
pip install gtts || echo "⚠️ gTTSのインストールに失敗（続行）"
pip install pydub || echo "⚠️ pydubのインストールに失敗（続行）"

# 動画処理（エラーが出ても続行）
echo "🎥 動画パッケージを試行..."
pip install moviepy || echo "⚠️ moviepyのインストールに失敗（続行）"

# AI API（オプション）
echo "🤖 AI APIパッケージを試行..."
pip install openai || echo "⚠️ OpenAIのインストールに失敗（続行）"

echo ""
echo "✅ 最小構成のセットアップ完了"
echo ""
echo "起動方法:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "注意: 一部機能が制限される可能性があります"