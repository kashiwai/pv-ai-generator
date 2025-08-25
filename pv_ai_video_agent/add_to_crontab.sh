#!/bin/bash

# 現在のcrontabを一時ファイルに保存
crontab -l > /tmp/current_cron 2>/dev/null || true

# PV AI Generator MCP設定を追加（重複チェック付き）
echo "" >> /tmp/current_cron
echo "# PV AI Generator MCP Auto Recording (every 10 minutes)" >> /tmp/current_cron

# 10分ごとの自動記録
if ! grep -q "mcp_auto_record.py" /tmp/current_cron; then
    echo "*/10 * * * * cd /Users/kotarokashiwai/PVmovieegent/pv_ai_video_agent && /usr/bin/python3 mcp_auto_record.py >> mcp_logs/cron.log 2>&1" >> /tmp/current_cron
fi

echo "# PV AI Generator API Status Check (every 30 minutes)" >> /tmp/current_cron

# 30分ごとのAPI状態チェック
if ! grep -q "mcp_check_apis.py" /tmp/current_cron; then
    echo "*/30 * * * * cd /Users/kotarokashiwai/PVmovieegent/pv_ai_video_agent && /usr/bin/python3 mcp_check_apis.py >> mcp_logs/api_check.log 2>&1" >> /tmp/current_cron
fi

echo "# PV AI Generator MCP Server Start on Reboot" >> /tmp/current_cron

# システム起動時のMCPサーバー起動
if ! grep -q "mcp_server.py" /tmp/current_cron; then
    echo "@reboot cd /Users/kotarokashiwai/PVmovieegent/pv_ai_video_agent && /usr/bin/python3 mcp_server.py >> mcp_logs/server.log 2>&1 &" >> /tmp/current_cron
fi

# crontabを更新
crontab /tmp/current_cron

# 一時ファイルを削除
rm /tmp/current_cron

echo "✅ Crontab設定を追加しました"
echo ""
echo "追加された設定:"
echo "  • 10分ごと: 自動記録 (mcp_auto_record.py)"
echo "  • 30分ごと: API状態チェック (mcp_check_apis.py)"
echo "  • 起動時: MCPサーバー起動 (mcp_server.py)"
echo ""
echo "現在のcrontab:"
crontab -l | grep -E "(mcp_|PV AI Generator)" || echo "設定が見つかりません"