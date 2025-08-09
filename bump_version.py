#!/usr/bin/env python3
"""
バージョン番号を自動インクリメントするスクリプト
使い方: python bump_version.py [major|minor|patch]
デフォルトはpatch（最後の数字）をインクリメント
"""

import json
import sys
from datetime import datetime

def bump_version(bump_type='patch'):
    """
    バージョン番号をインクリメント
    
    Args:
        bump_type: 'major', 'minor', 'patch'のいずれか
    """
    # version.jsonを読み込み
    try:
        with open('version.json', 'r') as f:
            version_info = json.load(f)
    except FileNotFoundError:
        # ファイルがない場合は初期値を設定
        version_info = {
            "major": 2,
            "minor": 0,
            "patch": 0
        }
    
    # バージョン番号をインクリメント
    if bump_type == 'major':
        version_info['major'] += 1
        version_info['minor'] = 0
        version_info['patch'] = 0
    elif bump_type == 'minor':
        version_info['minor'] += 1
        version_info['patch'] = 0
    else:  # patch
        version_info['patch'] += 1
    
    # バージョン文字列を生成
    version_info['version'] = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    version_info['build_date'] = datetime.now().strftime('%Y-%m-%d')
    version_info['description'] = "PV自動生成AIエージェント"
    
    # version.jsonに保存
    with open('version.json', 'w') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print(f"✅ バージョンを {version_info['version']} に更新しました")
    return version_info['version']

if __name__ == '__main__':
    # コマンドライン引数を確認
    bump_type = 'patch'  # デフォルト
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['major', 'minor', 'patch']:
            bump_type = arg
    
    new_version = bump_version(bump_type)