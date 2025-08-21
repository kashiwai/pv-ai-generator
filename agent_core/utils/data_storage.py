"""
データ保存・読み込みユーティリティ
プロジェクトデータの永続化を管理
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pickle

class DataStorage:
    """プロジェクトデータの保存・読み込みを管理"""
    
    def __init__(self, storage_dir: str = "saved_projects"):
        """
        Args:
            storage_dir: 保存先ディレクトリ
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_project(self, project_data: Dict[str, Any], project_id: Optional[str] = None) -> str:
        """
        プロジェクトデータを保存
        
        Args:
            project_data: 保存するプロジェクトデータ
            project_id: プロジェクトID（省略時は自動生成）
        
        Returns:
            保存したプロジェクトのID
        """
        # プロジェクトIDを生成または使用
        if not project_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = project_data.get('basic_info', {}).get('title', 'untitled')
            project_id = f"{title}_{timestamp}".replace(' ', '_').replace('/', '_')
        
        # プロジェクトディレクトリを作成
        project_dir = self.storage_dir / project_id
        project_dir.mkdir(exist_ok=True)
        
        # メタデータを追加
        project_data['metadata'] = {
            'project_id': project_id,
            'saved_at': datetime.now().isoformat(),
            'version': project_data.get('version', '2.4.2')
        }
        
        # JSONファイルとして保存
        json_file = project_dir / "project_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # ファイルアップロードオブジェクトを除外してJSONシリアライズ
            serializable_data = self._prepare_for_json(project_data)
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        # バイナリデータ（画像、音楽）を別途保存
        self._save_binary_files(project_data, project_dir)
        
        return project_id
    
    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        プロジェクトデータを読み込み
        
        Args:
            project_id: プロジェクトID
        
        Returns:
            プロジェクトデータ（存在しない場合はNone）
        """
        project_dir = self.storage_dir / project_id
        json_file = project_dir / "project_data.json"
        
        if not json_file.exists():
            return None
        
        # JSONファイルを読み込み
        with open(json_file, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # バイナリファイルの参照を復元
        project_data = self._restore_binary_references(project_data, project_dir)
        
        return project_data
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        保存されているプロジェクトの一覧を取得
        
        Returns:
            プロジェクト情報のリスト
        """
        projects = []
        
        for project_dir in self.storage_dir.iterdir():
            if project_dir.is_dir():
                json_file = project_dir / "project_data.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            projects.append({
                                'project_id': project_dir.name,
                                'title': data.get('basic_info', {}).get('title', 'Unknown'),
                                'saved_at': data.get('metadata', {}).get('saved_at', 'Unknown'),
                                'version': data.get('metadata', {}).get('version', 'Unknown')
                            })
                    except Exception as e:
                        print(f"Error loading project {project_dir.name}: {e}")
        
        # 新しい順にソート
        projects.sort(key=lambda x: x['saved_at'], reverse=True)
        
        return projects
    
    def delete_project(self, project_id: str) -> bool:
        """
        プロジェクトを削除
        
        Args:
            project_id: プロジェクトID
        
        Returns:
            削除成功の可否
        """
        project_dir = self.storage_dir / project_id
        
        if project_dir.exists():
            import shutil
            shutil.rmtree(project_dir)
            return True
        
        return False
    
    def export_project(self, project_id: str, export_path: str) -> bool:
        """
        プロジェクトをエクスポート（ZIPファイルとして）
        
        Args:
            project_id: プロジェクトID
            export_path: エクスポート先パス
        
        Returns:
            エクスポート成功の可否
        """
        project_dir = self.storage_dir / project_id
        
        if not project_dir.exists():
            return False
        
        import zipfile
        import shutil
        
        # 一時的にZIPファイルを作成
        temp_zip = f"{export_path}.tmp"
        shutil.make_archive(temp_zip.replace('.tmp', ''), 'zip', project_dir)
        
        # 最終的なパスに移動
        shutil.move(f"{temp_zip.replace('.tmp', '')}.zip", export_path)
        
        return True
    
    def import_project(self, import_path: str) -> Optional[str]:
        """
        プロジェクトをインポート（ZIPファイルから）
        
        Args:
            import_path: インポート元パス
        
        Returns:
            インポートしたプロジェクトのID（失敗時はNone）
        """
        import zipfile
        import tempfile
        
        if not os.path.exists(import_path):
            return None
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # ZIPファイルを解凍
                with zipfile.ZipFile(import_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # project_data.jsonを探す
                json_file = None
                for root, dirs, files in os.walk(temp_dir):
                    if 'project_data.json' in files:
                        json_file = Path(root) / 'project_data.json'
                        break
                
                if not json_file:
                    return None
                
                # プロジェクトデータを読み込み
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 新しいプロジェクトIDを生成
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                project_id = f"imported_{timestamp}"
                
                # プロジェクトディレクトリにコピー
                import shutil
                dest_dir = self.storage_dir / project_id
                shutil.copytree(json_file.parent, dest_dir)
                
                return project_id
                
        except Exception as e:
            print(f"Error importing project: {e}")
            return None
    
    def _prepare_for_json(self, data: Any) -> Any:
        """JSONシリアライズ可能な形式に変換"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # ファイルアップロードオブジェクトをスキップ
                if key in ['audio_file', 'character_images']:
                    result[key] = None  # 後で別途保存
                else:
                    result[key] = self._prepare_for_json(value)
            return result
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif hasattr(data, '__dict__'):
            # オブジェクトを辞書に変換
            return self._prepare_for_json(data.__dict__)
        else:
            return data
    
    def _save_binary_files(self, project_data: Dict, project_dir: Path):
        """バイナリファイル（画像、音楽）を保存"""
        # 基本情報からファイルを取得
        basic_info = project_data.get('basic_info', {})
        
        # 音楽ファイルを保存
        if basic_info.get('audio_file'):
            audio_file = basic_info['audio_file']
            if hasattr(audio_file, 'read'):
                audio_path = project_dir / f"audio{Path(audio_file.name).suffix}"
                with open(audio_path, 'wb') as f:
                    audio_file.seek(0)
                    f.write(audio_file.read())
        
        # キャラクター画像を保存
        if basic_info.get('character_images'):
            images_dir = project_dir / "character_images"
            images_dir.mkdir(exist_ok=True)
            
            for i, img_file in enumerate(basic_info['character_images']):
                if hasattr(img_file, 'read'):
                    img_path = images_dir / f"character_{i}{Path(img_file.name).suffix}"
                    with open(img_path, 'wb') as f:
                        img_file.seek(0)
                        f.write(img_file.read())
    
    def _restore_binary_references(self, project_data: Dict, project_dir: Path) -> Dict:
        """バイナリファイルの参照を復元"""
        # 音楽ファイルの参照を復元
        audio_files = list(project_dir.glob("audio.*"))
        if audio_files:
            project_data.setdefault('basic_info', {})['audio_file_path'] = str(audio_files[0])
        
        # キャラクター画像の参照を復元
        images_dir = project_dir / "character_images"
        if images_dir.exists():
            image_paths = [str(p) for p in images_dir.glob("character_*")]
            if image_paths:
                project_data.setdefault('basic_info', {})['character_image_paths'] = image_paths
        
        return project_data
    
    def autosave(self, session_data: Dict[str, Any], autosave_id: str = "autosave"):
        """
        自動保存（セッションデータを保存）
        
        Args:
            session_data: セッションデータ
            autosave_id: 自動保存ID
        """
        autosave_dir = self.storage_dir / "_autosaves"
        autosave_dir.mkdir(exist_ok=True)
        
        autosave_file = autosave_dir / f"{autosave_id}.json"
        
        # セッションデータを保存
        with open(autosave_file, 'w', encoding='utf-8') as f:
            serializable_data = self._prepare_for_json(session_data)
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
    
    def load_autosave(self, autosave_id: str = "autosave") -> Optional[Dict[str, Any]]:
        """
        自動保存データを読み込み
        
        Args:
            autosave_id: 自動保存ID
        
        Returns:
            セッションデータ（存在しない場合はNone）
        """
        autosave_file = self.storage_dir / "_autosaves" / f"{autosave_id}.json"
        
        if not autosave_file.exists():
            return None
        
        with open(autosave_file, 'r', encoding='utf-8') as f:
            return json.load(f)