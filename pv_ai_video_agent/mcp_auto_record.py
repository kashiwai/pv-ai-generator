#!/usr/bin/env python3
"""
10分ごとの自動記録スクリプト
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import subprocess

def get_git_status():
    """Gitステータスを取得"""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout else []
    except:
        return []

def get_current_branch():
    """現在のGitブランチを取得"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def get_project_stats():
    """プロジェクト統計を取得"""
    stats = {
        "python_files": 0,
        "total_lines": 0,
        "modified_files": []
    }
    
    # Pythonファイル数をカウント
    for root, dirs, files in os.walk("."):
        # 仮想環境を除外
        if "venv" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                stats["python_files"] += 1
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        stats["total_lines"] += len(f.readlines())
                except:
                    pass
    
    # 変更されたファイル
    git_status = get_git_status()
    stats["modified_files"] = [f.split()[-1] for f in git_status if f]
    
    return stats

def check_api_status():
    """API設定状態をチェック"""
    apis = {
        "PIAPI_KEY": bool(os.environ.get("PIAPI_KEY")),
        "PIAPI_XKEY": bool(os.environ.get("PIAPI_XKEY")),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "GOOGLE_API_KEY": bool(os.environ.get("GOOGLE_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY"))
    }
    return apis

def record_status():
    """ステータスを記録"""
    timestamp = datetime.now()
    
    # 記録データを作成
    record = {
        "timestamp": timestamp.isoformat(),
        "git": {
            "branch": get_current_branch(),
            "status": get_git_status()
        },
        "project": get_project_stats(),
        "apis": check_api_status(),
        "environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "cwd": os.getcwd()
        }
    }
    
    # ログディレクトリを作成
    log_dir = Path("mcp_logs")
    log_dir.mkdir(exist_ok=True)
    
    # 日付ごとのログファイル
    log_file = log_dir / f"auto_record_{timestamp.strftime('%Y%m%d')}.json"
    
    # 既存のログを読み込み
    records = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except:
            records = []
    
    # 新しい記録を追加
    records.append(record)
    
    # ファイルに保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    # サマリーファイルも更新
    summary_file = log_dir / "summary.json"
    summary = {
        "last_update": timestamp.isoformat(),
        "total_records": len(records),
        "current_status": {
            "branch": record["git"]["branch"],
            "modified_files": len(record["git"]["status"]),
            "python_files": record["project"]["python_files"],
            "total_lines": record["project"]["total_lines"],
            "apis_configured": sum(1 for v in record["apis"].values() if v)
        }
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] 自動記録完了")
    print(f"  - ブランチ: {record['git']['branch']}")
    print(f"  - 変更ファイル: {len(record['git']['status'])}個")
    print(f"  - Pythonファイル: {record['project']['python_files']}個")
    print(f"  - 総行数: {record['project']['total_lines']:,}行")
    print(f"  - API設定: {sum(1 for v in record['apis'].values() if v)}/5")
    
    return record

def main():
    """メイン処理"""
    try:
        record = record_status()
        
        # 重要な変更があれば通知
        if len(record["git"]["status"]) > 10:
            print("\n⚠️  多数のファイルが変更されています！コミットを検討してください。")
        
        if not record["apis"]["PIAPI_KEY"] or not record["apis"]["PIAPI_XKEY"]:
            print("\n⚠️  PIAPIキーが設定されていません！")
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()