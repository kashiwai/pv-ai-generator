#!/usr/bin/env python3
"""
MCPフック用ヘルパー関数
"""

import json
import os
from datetime import datetime
from pathlib import Path

def log_task(task_name: str):
    """タスク実行をログに記録"""
    log_dir = Path("mcp_logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "tasks.json"
    
    # 既存のログを読み込み
    tasks = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except:
            tasks = []
    
    # 新しいタスクを追加
    task_entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task_name,
        "pid": os.getpid()
    }
    tasks.append(task_entry)
    
    # 保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    print(f"Task logged: {task_name}")

def log_event(event_type: str, data: dict = None):
    """イベントをログに記録"""
    log_dir = Path("mcp_logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "events.json"
    
    # 既存のログを読み込み
    events = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except:
            events = []
    
    # 新しいイベントを追加
    event_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data or {}
    }
    events.append(event_entry)
    
    # 保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    print(f"Event logged: {event_type}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        log_task(sys.argv[1])
    else:
        log_event("test", {"message": "Test event"})