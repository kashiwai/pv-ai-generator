#!/bin/bash

# MCPサーバー自動起動設定スクリプト

echo "MCPサーバー自動起動設定を開始..."

# 現在のディレクトリを取得
CURRENT_DIR="$(pwd)"
PYTHON_PATH="$(which python3)"

# 1. crontab設定を追加（10分ごとの記録）
echo "crontab設定を追加中..."

# 一時ファイルに現在のcrontabを保存
crontab -l > /tmp/mycron 2>/dev/null || true

# MCPの設定を追加（重複を避ける）
grep -q "mcp_auto_record.py" /tmp/mycron || {
    echo "# MCP Server Auto Recording (every 10 minutes)" >> /tmp/mycron
    echo "*/10 * * * * cd $CURRENT_DIR && $PYTHON_PATH mcp_auto_record.py >> mcp_logs/cron.log 2>&1" >> /tmp/mycron
}

grep -q "mcp_check_apis.py" /tmp/mycron || {
    echo "# MCP API Status Check (every 30 minutes)" >> /tmp/mycron
    echo "*/30 * * * * cd $CURRENT_DIR && $PYTHON_PATH mcp_check_apis.py >> mcp_logs/cron.log 2>&1" >> /tmp/mycron
}

# 起動時にMCPサーバーを開始
grep -q "mcp_server.py" /tmp/mycron || {
    echo "# MCP Server Start on Reboot" >> /tmp/mycron
    echo "@reboot cd $CURRENT_DIR && $PYTHON_PATH mcp_server.py >> mcp_logs/server.log 2>&1 &" >> /tmp/mycron
}

# crontabを更新
crontab /tmp/mycron
rm /tmp/mycron

echo "✅ crontab設定完了"

# 2. launchd設定（macOS用）
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS検出: launchdサービスを設定中..."
    
    # plistファイルを作成
    PLIST_FILE="$HOME/Library/LaunchAgents/com.pv-ai-generator.mcp-server.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pv-ai-generator.mcp-server</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$CURRENT_DIR/mcp_server.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$CURRENT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>$CURRENT_DIR/mcp_logs/server.log</string>
    
    <key>StandardErrorPath</key>
    <string>$CURRENT_DIR/mcp_logs/server_error.log</string>
    
    <key>StartInterval</key>
    <integer>600</integer>
</dict>
</plist>
EOF
    
    # サービスをロード
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"
    
    echo "✅ launchdサービス設定完了"
fi

# 3. 起動スクリプトを作成
cat > "$CURRENT_DIR/start_mcp.sh" << 'EOF'
#!/bin/bash

# MCPサーバー起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 既存のプロセスを確認
if pgrep -f "mcp_server.py" > /dev/null; then
    echo "MCPサーバーは既に起動しています"
    exit 0
fi

# ログディレクトリを作成
mkdir -p mcp_logs

# MCPサーバーを起動
echo "MCPサーバーを起動中..."
nohup python3 mcp_server.py >> mcp_logs/server.log 2>&1 &
echo $! > mcp_logs/server.pid

echo "MCPサーバーが起動しました (PID: $(cat mcp_logs/server.pid))"

# 10秒待機して起動を確認
sleep 10

if pgrep -f "mcp_server.py" > /dev/null; then
    echo "✅ MCPサーバーは正常に動作しています"
else
    echo "❌ MCPサーバーの起動に失敗しました"
    exit 1
fi
EOF

chmod +x "$CURRENT_DIR/start_mcp.sh"

# 4. 停止スクリプトを作成
cat > "$CURRENT_DIR/stop_mcp.sh" << 'EOF'
#!/bin/bash

# MCPサーバー停止スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f mcp_logs/server.pid ]; then
    PID=$(cat mcp_logs/server.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "MCPサーバーを停止中 (PID: $PID)..."
        kill $PID
        rm mcp_logs/server.pid
        echo "✅ MCPサーバーが停止しました"
    else
        echo "MCPサーバーは既に停止しています"
        rm mcp_logs/server.pid
    fi
else
    # pidファイルがない場合はプロセス名で検索
    if pgrep -f "mcp_server.py" > /dev/null; then
        echo "MCPサーバープロセスを停止中..."
        pkill -f "mcp_server.py"
        echo "✅ MCPサーバーが停止しました"
    else
        echo "MCPサーバーは起動していません"
    fi
fi
EOF

chmod +x "$CURRENT_DIR/stop_mcp.sh"

echo ""
echo "====================================="
echo "MCPサーバー自動起動設定が完了しました"
echo "====================================="
echo ""
echo "使用方法:"
echo "  起動: ./start_mcp.sh"
echo "  停止: ./stop_mcp.sh"
echo ""
echo "自動実行:"
echo "  - 10分ごとの記録: 有効"
echo "  - 30分ごとのAPI確認: 有効"
echo "  - システム起動時の自動開始: 有効"
echo ""
echo "ログファイル:"
echo "  - mcp_logs/server.log"
echo "  - mcp_logs/cron.log"
echo ""