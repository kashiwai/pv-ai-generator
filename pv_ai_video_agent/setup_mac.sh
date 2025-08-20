#!/bin/bash

# PV AI Video Agent - macOS Setup Script
echo "🎬 PV自動生成AIエージェント セットアップ開始"
echo "================================================"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python バージョンチェック
echo -e "\n${YELLOW}1. Python環境チェック${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION が見つかりました${NC}"
else
    echo -e "${RED}✗ Python3が見つかりません。Homebrewでインストールしてください:${NC}"
    echo "  brew install python@3.11"
    exit 1
fi

# 仮想環境の作成
echo -e "\n${YELLOW}2. 仮想環境の作成${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ 仮想環境を作成しました${NC}"
else
    echo -e "${GREEN}✓ 仮想環境は既に存在します${NC}"
fi

# 仮想環境のアクティベート
echo -e "\n${YELLOW}3. 仮想環境をアクティベート${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ 仮想環境をアクティベートしました${NC}"

# pip のアップグレード
echo -e "\n${YELLOW}4. pipをアップグレード${NC}"
pip install --upgrade pip setuptools wheel

# 依存関係のインストール（エラーを無視して継続）
echo -e "\n${YELLOW}5. 必要なパッケージをインストール${NC}"

# Core dependencies
echo "📦 コア依存関係をインストール中..."
pip install gradio --no-cache-dir
pip install asyncio-mqtt --no-cache-dir

# AI/ML APIs
echo "🤖 AI/ML APIライブラリをインストール中..."
pip install openai --no-cache-dir
pip install anthropic --no-cache-dir
pip install google-generativeai --no-cache-dir

# Audio processing
echo "🎵 音声処理ライブラリをインストール中..."
pip install librosa --no-cache-dir
pip install soundfile --no-cache-dir
pip install pydub --no-cache-dir
pip install gtts --no-cache-dir

# Video processing
echo "🎥 動画処理ライブラリをインストール中..."
pip install moviepy --no-cache-dir
pip install opencv-python --no-cache-dir
pip install ffmpeg-python --no-cache-dir

# Image processing
echo "🖼️ 画像処理ライブラリをインストール中..."
pip install Pillow --no-cache-dir
pip install numpy --no-cache-dir

# Utilities
echo "🔧 ユーティリティをインストール中..."
pip install requests --no-cache-dir
pip install aiohttp --no-cache-dir
pip install python-dotenv --no-cache-dir
pip install pyyaml --no-cache-dir

# FFmpegのインストールチェック
echo -e "\n${YELLOW}6. FFmpegチェック${NC}"
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1)
    echo -e "${GREEN}✓ $FFMPEG_VERSION${NC}"
else
    echo -e "${YELLOW}FFmpegが見つかりません。インストールしますか? (y/n)${NC}"
    read -r response
    if [[ "$response" == "y" ]]; then
        if command -v brew &> /dev/null; then
            brew install ffmpeg
            echo -e "${GREEN}✓ FFmpegをインストールしました${NC}"
        else
            echo -e "${RED}Homebrewが見つかりません。手動でFFmpegをインストールしてください${NC}"
        fi
    fi
fi

# 必要なディレクトリの作成
echo -e "\n${YELLOW}7. 必要なディレクトリを作成${NC}"
mkdir -p assets/{input,output,temp,characters}
echo -e "${GREEN}✓ ディレクトリ構造を作成しました${NC}"

# 環境変数ファイルの作成
echo -e "\n${YELLOW}8. 環境設定ファイルの準備${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# AI API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
FISH_AUDIO_API_KEY=
MIDJOURNEY_API_KEY=
HAILUO_API_KEY=
SORA_API_KEY=
VEO3_API_KEY=
SEEDANCE_API_KEY=
DOMOAI_API_KEY=
EOF
    echo -e "${GREEN}✓ .envファイルを作成しました${NC}"
    echo -e "${YELLOW}  APIキーを.envファイルに設定してください${NC}"
else
    echo -e "${GREEN}✓ .envファイルは既に存在します${NC}"
fi

# 起動スクリプトの作成
echo -e "\n${YELLOW}9. 起動スクリプトを作成${NC}"
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python app.py
EOF
chmod +x run.sh
echo -e "${GREEN}✓ run.shを作成しました${NC}"

# セットアップ完了
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}✅ セットアップが完了しました！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "次のステップ:"
echo "1. APIキーを .env ファイルに設定"
echo "2. 以下のコマンドでアプリを起動:"
echo -e "   ${YELLOW}./run.sh${NC}"
echo ""
echo "または手動で:"
echo -e "   ${YELLOW}source venv/bin/activate${NC}"
echo -e "   ${YELLOW}python app.py${NC}"
echo ""
echo "アプリは http://localhost:7860 でアクセスできます"