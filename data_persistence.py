"""
データ永続化モジュール
Streamlit Cloudでのデータ保存・復元機能
"""

import json
import os
import pickle
import base64
from datetime import datetime
from typing import Any, Dict, Optional
import streamlit as st
from pathlib import Path
import gzip

class DataPersistenceManager:
    """データ永続化マネージャー"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def save_to_secrets(self, key: str, data: Any) -> bool:
        """
        データをStreamlit Secretsに保存（小サイズデータ用）
        """
        try:
            # データをJSON形式で圧縮
            json_str = json.dumps(data, ensure_ascii=False)
            compressed = gzip.compress(json_str.encode())
            encoded = base64.b64encode(compressed).decode()
            
            # Secretsに保存（手動で設定が必要）
            st.info(f"""
            📌 **データをSecretsに保存するには：**
            1. Streamlit Cloud管理画面を開く
            2. Settings → Secretsに移動
            3. 以下を追加：
            ```toml
            {key} = "{encoded[:100]}..."  # 実際は全文を貼り付け
            ```
            """)
            return True
        except Exception as e:
            st.error(f"保存エラー: {str(e)}")
            return False
    
    def load_from_secrets(self, key: str) -> Optional[Any]:
        """
        Streamlit Secretsからデータを読み込み
        """
        try:
            if key in st.secrets:
                encoded = st.secrets[key]
                compressed = base64.b64decode(encoded)
                json_str = gzip.decompress(compressed).decode()
                return json.loads(json_str)
        except Exception as e:
            st.error(f"読み込みエラー: {str(e)}")
        return None
    
    def export_project_data(self, project_data: Dict) -> str:
        """
        プロジェクトデータをエクスポート（ダウンロード可能な形式）
        """
        try:
            # タイムスタンプ付きファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pv_project_{timestamp}.json"
            
            # データを整形
            export_data = {
                "version": "5.4.0",
                "timestamp": timestamp,
                "project": project_data
            }
            
            # JSON文字列化
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            # Base64エンコード（ダウンロード用）
            b64 = base64.b64encode(json_str.encode()).decode()
            
            # ダウンロードリンク作成
            href = f'<a href="data:application/json;base64,{b64}" download="{filename}">📥 プロジェクトファイルをダウンロード</a>'
            
            return href
            
        except Exception as e:
            st.error(f"エクスポートエラー: {str(e)}")
            return ""
    
    def import_project_data(self, uploaded_file) -> Optional[Dict]:
        """
        アップロードされたプロジェクトファイルをインポート
        """
        try:
            # ファイル読み込み
            content = uploaded_file.read()
            
            # JSONパース
            data = json.loads(content)
            
            # バージョンチェック
            if "version" in data:
                st.info(f"📂 プロジェクトバージョン: {data['version']}")
            
            # プロジェクトデータ返却
            return data.get("project", data)
            
        except Exception as e:
            st.error(f"インポートエラー: {str(e)}")
            return None
    
    def create_session_backup(self) -> bool:
        """
        現在のセッションデータをバックアップ
        """
        try:
            # セッションステート全体を取得
            session_data = dict(st.session_state)
            
            # シリアライズ可能なデータのみ抽出
            backup_data = {}
            for key, value in session_data.items():
                try:
                    json.dumps(value)  # テスト
                    backup_data[key] = value
                except:
                    continue  # シリアライズ不可はスキップ
            
            # タイムスタンプ付きで保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"session_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            # 古いバックアップを削除（最新10件のみ保持）
            backups = sorted(self.backup_dir.glob("session_*.json"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            return True
            
        except Exception as e:
            st.error(f"バックアップエラー: {str(e)}")
            return False
    
    def restore_session_backup(self, backup_file: Path) -> bool:
        """
        バックアップからセッション復元
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # セッションステートに復元
            for key, value in backup_data.items():
                st.session_state[key] = value
            
            return True
            
        except Exception as e:
            st.error(f"復元エラー: {str(e)}")
            return False
    
    def get_available_backups(self) -> list:
        """
        利用可能なバックアップリストを取得
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob("session_*.json"), reverse=True):
            timestamp = backup_file.stem.replace("session_", "")
            backups.append({
                "file": backup_file,
                "timestamp": timestamp,
                "size": backup_file.stat().st_size
            })
        return backups

def create_persistence_ui():
    """
    データ永続化UIを作成
    """
    manager = DataPersistenceManager()
    
    # エクスポート機能
    if st.button("📥 プロジェクトをエクスポート", use_container_width=True):
        project_data = {
            "generated_scripts": st.session_state.get("generated_scripts", {}),
            "generated_images": st.session_state.get("generated_images", {}),
            "generated_videos": st.session_state.get("generated_videos", {}),
            "project_settings": st.session_state.get("project_settings", {}),
        }
        
        download_link = manager.export_project_data(project_data)
        st.markdown(download_link, unsafe_allow_html=True)
        st.success("エクスポート準備完了!")
    
    # インポート機能
    uploaded_file = st.file_uploader(
        "📤 プロジェクトをインポート",
        type=['json'],
        help="以前エクスポートしたプロジェクトファイルを選択"
    )
    
    if uploaded_file:
        project_data = manager.import_project_data(uploaded_file)
        if project_data:
            # データを復元
            if "generated_scripts" in project_data:
                st.session_state.generated_scripts = project_data["generated_scripts"]
            if "generated_images" in project_data:
                st.session_state.generated_images = project_data["generated_images"]
            if "generated_videos" in project_data:
                st.session_state.generated_videos = project_data["generated_videos"]
            if "project_settings" in project_data:
                st.session_state.project_settings = project_data["project_settings"]
            
            st.success("✅ プロジェクトをインポートしました!")
            st.rerun()
    
    # 自動バックアップ
    if st.checkbox("🔄 自動バックアップ", value=True):
        if st.button("💾 今すぐバックアップ", use_container_width=True):
            if manager.create_session_backup():
                st.success("バックアップ完了!")
        
        # バックアップリスト表示
        backups = manager.get_available_backups()
        if backups:
            st.markdown("**📁 利用可能なバックアップ:**")
            for backup in backups[:5]:  # 最新5件表示
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(backup["timestamp"])
                with col2:
                    if st.button("復元", key=f"restore_{backup['timestamp']}"):
                        if manager.restore_session_backup(backup["file"]):
                            st.success("復元完了!")
                            st.rerun()

def save_to_github(data: Dict, filename: str) -> bool:
    """
    GitHubリポジトリにデータを保存（別実装が必要）
    """
    # GitHub APIを使用した保存処理
    # 実装にはGitHub Personal Access Tokenが必要
    pass

if __name__ == "__main__":
    # テスト用
    st.title("データ永続化テスト")
    create_persistence_ui()