#!/usr/bin/env python3
"""
動画生成プロセスのデバッグスクリプト
Streamlit Cloudで動画生成が止まっている問題を診断
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

def check_piapi_task(task_id: str):
    """PIAPIタスクのステータスを確認"""
    
    # APIキー取得
    x_key = os.getenv('PIAPI_XKEY', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
    
    headers = {
        "x-api-key": x_key,
        "Content-Type": "application/json"
    }
    
    url = f"https://api.piapi.ai/api/v1/task/{task_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # データ構造の確認
            if 'data' in data:
                task_data = data['data']
                status = task_data.get('status', 'unknown')
                progress = task_data.get('output', {}).get('progress', 0)
                
                print(f"タスク {task_id}:")
                print(f"  ステータス: {status}")
                print(f"  進捗: {progress}%")
                
                if status == 'completed':
                    image_url = task_data.get('output', {}).get('image_url')
                    if image_url:
                        print(f"  画像URL: {image_url[:100]}...")
                
                return status
            else:
                print(f"タスク {task_id}: データ構造エラー")
                return 'error'
                
        elif response.status_code == 404:
            print(f"タスク {task_id}: 見つかりません（404）")
            return 'not_found'
        else:
            print(f"タスク {task_id}: HTTPエラー {response.status_code}")
            return 'error'
            
    except Exception as e:
        print(f"タスク {task_id}: 例外 {e}")
        return 'error'

def analyze_video_generation_issues():
    """動画生成の問題を分析"""
    
    print("=" * 60)
    print("🎬 動画生成デバッグ")
    print("=" * 60)
    
    print("\n1️⃣ 一般的な問題と解決策:")
    print("-" * 40)
    
    issues = [
        {
            "問題": "画像生成で止まる",
            "原因": [
                "Midjourney処理待ち（relaxモードは遅い）",
                "タスクIDの取得失敗",
                "APIレート制限"
            ],
            "解決策": [
                "fastモードを使用",
                "タイムアウトを延長（300秒→600秒）",
                "バッチサイズを減らす"
            ]
        },
        {
            "問題": "動画生成で止まる",
            "原因": [
                "Hailuo AI処理待ち",
                "大きな画像サイズ",
                "ネットワークタイムアウト"
            ],
            "解決策": [
                "画像サイズを最適化",
                "タイムアウトを延長",
                "リトライロジックを追加"
            ]
        },
        {
            "問題": "進捗が表示されない",
            "原因": [
                "ステータスチェック間隔が長い",
                "UIの更新が止まる",
                "WebSocketの切断"
            ],
            "解決策": [
                "チェック間隔を短縮（5秒→2秒）",
                "プログレスバーの更新頻度を上げる",
                "定期的なping送信"
            ]
        }
    ]
    
    for issue in issues:
        print(f"\n🔴 {issue['問題']}")
        print("  原因:")
        for cause in issue['原因']:
            print(f"    • {cause}")
        print("  解決策:")
        for solution in issue['解決策']:
            print(f"    ✅ {solution}")
    
    print("\n" + "=" * 60)
    print("2️⃣ 推奨される改善策")
    print("=" * 60)
    
    print("""
1. タイムアウト設定の最適化:
   - 画像生成: 600秒（10分）
   - 動画生成: 900秒（15分）
   - ステータスチェック: 2秒間隔

2. エラーハンドリングの強化:
   - リトライ機能（最大3回）
   - 部分的な成功の処理
   - エラー時の代替処理

3. パフォーマンス最適化:
   - バッチ処理サイズ: 2→1
   - 並行処理の制限
   - キャッシュの活用

4. デバッグ情報の追加:
   - 各ステップの実行時間記録
   - APIレスポンスの詳細ログ
   - エラースタックトレース
    """)
    
    # サンプルタスクのチェック
    print("\n3️⃣ 最近のタスクステータス確認")
    print("-" * 40)
    
    # 先ほど生成されたタスクIDをチェック
    recent_tasks = [
        "ccff9d3d-c197-4bcb-85ed-f6acf93ac327",  # テストで生成されたタスク
        "a476a8ee-71e7-422b-bf65-d8a4d9b8735c",  # 別のテストタスク
    ]
    
    for task_id in recent_tasks:
        check_piapi_task(task_id)
        time.sleep(1)

def create_optimized_config():
    """最適化された設定ファイルを作成"""
    
    config = {
        "timeouts": {
            "image_generation": 600,  # 10分
            "video_generation": 900,  # 15分
            "status_check_interval": 2,  # 2秒
            "network_timeout": 30  # 30秒
        },
        "batch_settings": {
            "image_batch_size": 1,  # 1つずつ処理
            "max_parallel_videos": 2,  # 最大2つの動画を並行処理
        },
        "retry_settings": {
            "max_retries": 3,
            "retry_delay": 5  # 5秒待機
        },
        "midjourney_settings": {
            "process_mode": "fast",  # fastモード推奨
            "check_interval": 2,
            "max_wait_time": 600
        },
        "hailuo_settings": {
            "quality": "high",
            "motion_intensity": 5,
            "check_interval": 5,
            "max_wait_time": 900
        }
    }
    
    print("\n4️⃣ 最適化設定")
    print("-" * 40)
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    # 設定ファイルを保存
    with open("video_generation_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ 設定ファイル作成: video_generation_config.json")

def main():
    """メイン処理"""
    
    # 問題分析
    analyze_video_generation_issues()
    
    # 最適化設定作成
    create_optimized_config()
    
    print("\n" + "=" * 60)
    print("デバッグ完了")
    print("=" * 60)
    
    print("\n次のステップ:")
    print("1. video_generation_config.jsonの設定を適用")
    print("2. piapi_integration.pyのタイムアウトを延長")
    print("3. ステータスチェック間隔を短縮")
    print("4. エラーハンドリングを強化")

if __name__ == "__main__":
    main()