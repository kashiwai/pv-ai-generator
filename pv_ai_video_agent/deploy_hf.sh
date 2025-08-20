#!/bin/bash

# Hugging Face Spacesデプロイスクリプト

echo "🚀 Hugging Face Spacesへのデプロイ開始"
echo "===================================="

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 引数チェック
if [ "$#" -ne 1 ]; then
    echo -e "${RED}使用方法: ./deploy_hf.sh <HF_TOKEN>${NC}"
    echo "例: ./deploy_hf.sh hf_xxxxxxxxxxxxx"
    exit 1
fi

HF_TOKEN=$1

# クローン先ディレクトリ
DEPLOY_DIR="pv-ai-generator-deploy"

# 既存ディレクトリを削除
if [ -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}既存のデプロイディレクトリを削除...${NC}"
    rm -rf $DEPLOY_DIR
fi

# リポジトリをクローン
echo -e "${YELLOW}1. リポジトリをクローン...${NC}"
git clone https://mmz2501:${HF_TOKEN}@huggingface.co/spaces/mmz2501/pv-ai-generator $DEPLOY_DIR

if [ $? -ne 0 ]; then
    echo -e "${RED}クローンに失敗しました。トークンを確認してください。${NC}"
    exit 1
fi

cd $DEPLOY_DIR

# ファイルをコピー
echo -e "${YELLOW}2. ファイルをコピー...${NC}"

# メインファイル
cp ../app.py .
cp ../requirements.txt .
cp ../packages.txt .
cp ../config.json .
cp ../README.md .

# agent_coreディレクトリ
cp -r ../agent_core .

# assetsディレクトリ構造を作成
mkdir -p assets/{input,output,temp,characters}

# .gitkeepファイルを追加
touch assets/input/.gitkeep
touch assets/output/.gitkeep
touch assets/temp/.gitkeep
touch assets/characters/.gitkeep

# .gitignoreを作成
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env
*.log
.DS_Store
assets/temp/*
assets/output/*
!assets/temp/.gitkeep
!assets/output/.gitkeep
EOF

# Git設定
echo -e "${YELLOW}3. Gitにコミット...${NC}"
git config user.email "mmz2501@huggingface.co"
git config user.name "mmz2501"

git add .
git commit -m "Deploy full PV AI Generator with Hailuo 02 AI support"

# プッシュ
echo -e "${YELLOW}4. Hugging Face Spacesにプッシュ...${NC}"
git push origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ デプロイ成功！${NC}"
    echo ""
    echo "次のステップ:"
    echo "1. https://huggingface.co/spaces/mmz2501/pv-ai-generator/settings"
    echo "   でAPIキーを設定（Repository secrets）"
    echo ""
    echo "必須APIキー:"
    echo "  - HAILUO_API_KEY"
    echo "  - OPENAI_API_KEY"
    echo "  - GOOGLE_API_KEY"
    echo ""
    echo "2. Spaceが自動的にビルド・起動します"
    echo ""
    echo "URL: https://huggingface.co/spaces/mmz2501/pv-ai-generator"
else
    echo -e "${RED}プッシュに失敗しました${NC}"
    exit 1
fi

cd ..
echo -e "${GREEN}完了！${NC}"