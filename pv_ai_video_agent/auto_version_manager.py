#!/usr/bin/env python3
"""
完全自動バージョン管理・承認システム
ファイル変更を検出して自動的にバージョンアップ、コミット、プッシュを実行
"""

import os
import json
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class AutoVersionManager:
    """完全自動バージョン管理システム"""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.version_file = self.root_dir / "pv-ai-generator" / "version.txt"
        self.version_json = self.root_dir / "pv-ai-generator" / "version.json"
        self.changelog = self.root_dir / "CHANGELOG.md"
        self.file_hashes = {}
        self.hash_file = self.root_dir / ".file_hashes.json"
        
    def load_file_hashes(self):
        """ファイルハッシュを読み込み"""
        if self.hash_file.exists():
            with open(self.hash_file, 'r') as f:
                self.file_hashes = json.load(f)
        return self.file_hashes
    
    def save_file_hashes(self):
        """ファイルハッシュを保存"""
        with open(self.hash_file, 'w') as f:
            json.dump(self.file_hashes, f, indent=2)
    
    def get_file_hash(self, filepath: Path) -> str:
        """ファイルのハッシュを取得"""
        if not filepath.exists():
            return ""
        
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def detect_changes(self) -> Tuple[List[str], List[str], List[str]]:
        """変更されたファイルを検出"""
        self.load_file_hashes()
        
        added = []
        modified = []
        deleted = []
        
        # Pythonファイルをスキャン
        for py_file in self.root_dir.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
                
            rel_path = str(py_file.relative_to(self.root_dir))
            current_hash = self.get_file_hash(py_file)
            
            if rel_path not in self.file_hashes:
                added.append(rel_path)
            elif self.file_hashes[rel_path] != current_hash:
                modified.append(rel_path)
            
            self.file_hashes[rel_path] = current_hash
        
        # 削除されたファイルを検出
        for rel_path in list(self.file_hashes.keys()):
            if not (self.root_dir / rel_path).exists():
                deleted.append(rel_path)
                del self.file_hashes[rel_path]
        
        self.save_file_hashes()
        return added, modified, deleted
    
    def determine_version_bump(self, added: List[str], modified: List[str], deleted: List[str]) -> str:
        """バージョンアップの種類を判定"""
        total_changes = len(added) + len(modified) + len(deleted)
        
        # 大規模変更：メジャーバージョン
        if total_changes > 20:
            return "major"
        
        # 新機能追加：マイナーバージョン
        if added or total_changes > 5:
            return "minor"
        
        # バグ修正・小規模変更：パッチバージョン
        if modified or deleted:
            return "patch"
        
        return None
    
    def get_current_version(self) -> Tuple[int, int, int]:
        """現在のバージョンを取得"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                version = f.read().strip()
                parts = version.split('.')
                return int(parts[0]), int(parts[1]), int(parts[2])
        return 2, 6, 2  # デフォルト
    
    def bump_version(self, bump_type: str) -> str:
        """バージョンをアップ"""
        major, minor, patch = self.get_current_version()
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def update_version_files(self, new_version: str, changes: Dict):
        """バージョンファイルを更新"""
        # version.txt更新
        with open(self.version_file, 'w') as f:
            f.write(new_version)
        
        # version.json更新
        version_data = {
            "version": new_version,
            "major": int(new_version.split('.')[0]),
            "minor": int(new_version.split('.')[1]),
            "patch": int(new_version.split('.')[2]),
            "build_date": datetime.now().strftime("%Y-%m-%d"),
            "description": f"自動更新 v{new_version}"
        }
        
        with open(self.version_json, 'w') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
        
        # CHANGELOG更新
        self.update_changelog(new_version, changes)
    
    def update_changelog(self, version: str, changes: Dict):
        """CHANGELOGを更新"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        entry = f"\n## [{version}] - {date}\n\n"
        
        if changes['added']:
            entry += "### Added\n"
            for file in changes['added'][:5]:  # 最初の5件のみ
                entry += f"- {file}\n"
            if len(changes['added']) > 5:
                entry += f"- ...他{len(changes['added'])-5}件\n"
            entry += "\n"
        
        if changes['modified']:
            entry += "### Changed\n"
            for file in changes['modified'][:5]:
                entry += f"- {file}を更新\n"
            if len(changes['modified']) > 5:
                entry += f"- ...他{len(changes['modified'])-5}件\n"
            entry += "\n"
        
        if changes['deleted']:
            entry += "### Removed\n"
            for file in changes['deleted'][:5]:
                entry += f"- {file}を削除\n"
            if len(changes['deleted']) > 5:
                entry += f"- ...他{len(changes['deleted'])-5}件\n"
            entry += "\n"
        
        # CHANGELOGの先頭に追加
        if self.changelog.exists():
            with open(self.changelog, 'r') as f:
                content = f.read()
            
            # バージョン履歴の前に挿入
            if "##" in content:
                parts = content.split("##", 1)
                new_content = parts[0] + entry + "##" + parts[1]
            else:
                new_content = content + entry
            
            with open(self.changelog, 'w') as f:
                f.write(new_content)
    
    def auto_commit_and_push(self, version: str, changes: Dict):
        """自動コミットとプッシュ"""
        try:
            # 変更をステージング
            subprocess.run(["git", "add", "-A"], check=True)
            
            # コミットメッセージ作成
            commit_msg = f"🤖 Auto Update v{version}\n\n"
            
            if changes['added']:
                commit_msg += f"Added: {len(changes['added'])} files\n"
            if changes['modified']:
                commit_msg += f"Modified: {len(changes['modified'])} files\n"
            if changes['deleted']:
                commit_msg += f"Deleted: {len(changes['deleted'])} files\n"
            
            commit_msg += "\n🤖 Generated with Claude Code Auto-Manager\n"
            commit_msg += "Co-Authored-By: Claude <noreply@anthropic.com>"
            
            # コミット
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # プッシュ（リベース付き）
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            print(f"✅ v{version}を自動コミット・プッシュしました")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git操作エラー: {e}")
            return False
    
    def run(self):
        """自動バージョン管理を実行"""
        print("🤖 自動バージョン管理システム起動")
        print("=" * 60)
        
        # 変更検出
        added, modified, deleted = self.detect_changes()
        
        if not (added or modified or deleted):
            print("✅ 変更なし")
            return
        
        print(f"📊 変更検出:")
        print(f"  追加: {len(added)}件")
        print(f"  変更: {len(modified)}件")
        print(f"  削除: {len(deleted)}件")
        
        # バージョンアップ判定
        bump_type = self.determine_version_bump(added, modified, deleted)
        
        if not bump_type:
            print("✅ バージョンアップ不要")
            return
        
        # 新バージョン決定
        new_version = self.bump_version(bump_type)
        current_version = '.'.join(map(str, self.get_current_version()))
        
        print(f"\n📦 バージョンアップ:")
        print(f"  {current_version} → {new_version} ({bump_type})")
        
        # 自動承認
        print("\n✅ 自動承認: バージョンアップを実行します")
        
        # バージョンファイル更新
        changes = {
            'added': added,
            'modified': modified,
            'deleted': deleted
        }
        
        self.update_version_files(new_version, changes)
        
        # コミット・プッシュ
        if self.auto_commit_and_push(new_version, changes):
            print(f"\n🎉 v{new_version}のリリース完了！")
        else:
            print(f"\n⚠️ v{new_version}のリリースに失敗")

def main():
    """メイン処理"""
    manager = AutoVersionManager()
    manager.run()

if __name__ == "__main__":
    main()