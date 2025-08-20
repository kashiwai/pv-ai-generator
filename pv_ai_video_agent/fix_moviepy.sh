#!/bin/bash

echo "🔧 MoviePyインストール修正スクリプト"
echo "======================================"

# Python 3.13は新しすぎる可能性があるため、別の方法を試す

# 仮想環境を再作成（Python 3.11推奨）
echo "1. 仮想環境をリセット..."
rm -rf venv

# Python 3.11が利用可能か確認
if command -v python3.11 &> /dev/null; then
    echo "✓ Python 3.11が見つかりました"
    python3.11 -m venv venv
elif command -v python3.12 &> /dev/null; then
    echo "✓ Python 3.12が見つかりました"
    python3.12 -m venv venv
else
    echo "⚠️ Python 3.11/3.12が見つかりません。現在のPython3を使用"
    python3 -m venv venv
fi

source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip setuptools wheel

# 基本パッケージをインストール
echo "2. 基本パッケージをインストール..."
pip install gradio
pip install numpy
pip install Pillow
pip install requests
pip install pyyaml

# MoviePyの依存関係を先にインストール
echo "3. MoviePy依存関係をインストール..."
pip install imageio==2.31.1
pip install imageio-ffmpeg==0.4.9
pip install decorator

# MoviePyを特定バージョンでインストール
echo "4. MoviePyをインストール..."
pip install moviepy==1.0.3

# その他の必要パッケージ
echo "5. その他のパッケージをインストール..."
pip install pydub
pip install gtts
pip install openai
pip install anthropic
pip install google-generativeai
pip install aiohttp
pip install python-dotenv

echo ""
echo "✅ 修正完了！"
echo ""
echo "実行方法:"
echo "  source venv/bin/activate"
echo "  python app.py"