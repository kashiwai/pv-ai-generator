#!/bin/bash
# 完全自動承認フックスクリプト

echo "🤖 完全自動承認システム起動"

# 1. ファイル変更監視
watch_files() {
    fswatch -o . | while read num; do
        echo "[$(date)] ファイル変更検出"
        python3 auto_version_manager.py
    done
}

# 2. 定期実行（10分ごと）
periodic_check() {
    while true; do
        sleep 600  # 10分
        echo "[$(date)] 定期チェック実行"
        python3 mcp_auto_record.py
        
        # 変更があれば自動バージョンアップ
        if git status --porcelain | grep -q "M\|A\|D"; then
            echo "変更検出 - 自動バージョンアップ実行"
            python3 auto_version_manager.py
        fi
    done
}

# 3. コミット前の自動チェック
pre_commit_hook() {
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "🔍 コミット前チェック"

# テスト実行
python3 test_piapi_midjourney.py

# バージョン自動更新
python3 auto_version_manager.py

exit 0
EOF
    chmod +x .git/hooks/pre-commit
}

# フック設定
setup_hooks() {
    echo "フック設定中..."
    pre_commit_hook
    echo "✅ Git pre-commitフック設定完了"
}

# メイン処理
main() {
    setup_hooks
    
    echo "自動承認システムを開始します"
    echo "1. ファイル監視開始"
    echo "2. 定期チェック開始"
    
    # バックグラウンドで実行
    periodic_check &
    PERIODIC_PID=$!
    
    # fswatch がインストールされているか確認
    if command -v fswatch &> /dev/null; then
        watch_files &
        WATCH_PID=$!
    else
        echo "⚠️ fswatchがインストールされていません"
        echo "  brew install fswatch でインストールしてください"
    fi
    
    echo "✅ 完全自動承認システム稼働中"
    echo "  定期チェック PID: $PERIODIC_PID"
    [ ! -z "$WATCH_PID" ] && echo "  ファイル監視 PID: $WATCH_PID"
    
    # プロセス管理
    trap "kill $PERIODIC_PID $WATCH_PID 2>/dev/null" EXIT
    
    # 待機
    wait
}

# 実行
main