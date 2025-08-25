#!/bin/bash

# PV AI Generator MCP起動スクリプト（APIキー設定付き）

echo "🚀 PV AI Generator MCP システム起動"
echo "=================================="

# Streamlit secretsからAPIキーを読み込む関数
load_api_keys() {
    SECRETS_FILE="$HOME/.streamlit/secrets.toml"
    
    if [ -f "$SECRETS_FILE" ]; then
        echo "✅ Secretsファイルを検出: $SECRETS_FILE"
        
        # 各APIキーを環境変数に設定
        export PIAPI_KEY=$(grep "^PIAPI_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export PIAPI_XKEY=$(grep "^PIAPI_XKEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export OPENAI_API_KEY=$(grep "^OPENAI_API_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export GOOGLE_API_KEY=$(grep "^GOOGLE_API_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export ANTHROPIC_API_KEY=$(grep "^ANTHROPIC_API_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export SEEDANCE_API_KEY=$(grep "^SEEDANCE_API_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        export DEEPSEEK_API_KEY=$(grep "^DEEPSEEK_API_KEY" "$SECRETS_FILE" | cut -d'"' -f2)
        
        echo "✅ APIキーを環境変数に設定しました"
        
        # 設定確認（最初の8文字のみ表示）
        [ ! -z "$PIAPI_KEY" ] && echo "  PIAPI_KEY: ${PIAPI_KEY:0:8}..."
        [ ! -z "$PIAPI_XKEY" ] && echo "  PIAPI_XKEY: ${PIAPI_XKEY:0:8}..."
        [ ! -z "$OPENAI_API_KEY" ] && echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:0:8}..."
    else
        echo "⚠️ Secretsファイルが見つかりません: $SECRETS_FILE"
        return 1
    fi
}

# ログディレクトリ作成
mkdir -p mcp_logs

# APIキーを読み込む
load_api_keys

echo ""
echo "📊 自動記録テスト実行..."
python3 mcp_auto_record.py

echo ""
echo "🔌 API接続テスト実行..."
python3 mcp_check_apis.py

echo ""
echo "🎯 MCPサーバー起動..."
# バックグラウンドで起動
nohup python3 mcp_server.py >> mcp_logs/server.log 2>&1 &
MCP_PID=$!
echo "✅ MCPサーバー起動 (PID: $MCP_PID)"

# PIDを保存
echo $MCP_PID > mcp_logs/server.pid

echo ""
echo "=================================="
echo "✅ PV AI Generator MCP起動完了"
echo "=================================="
echo ""
echo "ログ確認:"
echo "  tail -f mcp_logs/server.log"
echo ""
echo "停止方法:"
echo "  kill $(cat mcp_logs/server.pid)"
echo ""