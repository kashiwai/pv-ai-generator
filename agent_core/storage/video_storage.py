"""
動画ストレージ管理モジュール
生成された動画の保存と管理
"""

import os
import shutil
import httpx
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class VideoStorage:
    """動画ストレージ管理クラス"""
    
    def __init__(self, storage_dir: str = "generated_videos"):
        """
        Args:
            storage_dir: 動画保存ディレクトリ
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # プロジェクトごとのサブディレクトリ
        self.projects_dir = self.storage_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        
        # 一時ファイル用
        self.temp_dir = self.storage_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def create_project_folder(self, project_id: str) -> Path:
        """
        プロジェクト用のフォルダを作成
        
        Args:
            project_id: プロジェクトID
        
        Returns:
            プロジェクトフォルダのパス
        """
        project_path = self.projects_dir / project_id
        project_path.mkdir(exist_ok=True)
        
        # サブフォルダを作成
        (project_path / "scenes").mkdir(exist_ok=True)
        (project_path / "edited").mkdir(exist_ok=True)
        (project_path / "exports").mkdir(exist_ok=True)
        
        return project_path
    
    async def download_video(self, video_url: str, save_path: Path,
                           progress_callback: Optional[callable] = None) -> bool:
        """
        動画URLからファイルをダウンロード
        
        Args:
            video_url: 動画のURL
            save_path: 保存先パス
            progress_callback: 進捗コールバック
        
        Returns:
            成功の可否
        """
        try:
            async with httpx.AsyncClient() as client:
                if progress_callback:
                    progress_callback(0, "ダウンロード開始...")
                
                response = await client.get(video_url, follow_redirects=True)
                
                if response.status_code == 200:
                    # ファイルを保存
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                    if progress_callback:
                        progress_callback(1.0, "ダウンロード完了")
                    
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def save_scene_video(self, project_id: str, scene_number: int,
                        video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        シーン動画を保存
        
        Args:
            project_id: プロジェクトID
            scene_number: シーン番号
            video_data: 動画データ（URL含む）
        
        Returns:
            保存情報
        """
        project_path = self.create_project_folder(project_id)
        scene_path = project_path / "scenes" / f"scene_{scene_number:03d}.mp4"
        
        # メタデータを保存
        metadata = {
            "scene_number": scene_number,
            "timestamp": video_data.get("timestamp", ""),
            "video_url": video_data.get("video_url", ""),
            "download_url": video_data.get("download_url", ""),
            "local_path": str(scene_path),
            "saved_at": datetime.now().isoformat(),
            "status": video_data.get("status", "pending")
        }
        
        # メタデータファイルを保存
        metadata_path = project_path / "scenes" / f"scene_{scene_number:03d}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return metadata
    
    def save_edited_video(self, project_id: str, video_path: str,
                         edit_name: str = "edited") -> str:
        """
        編集済み動画を保存
        
        Args:
            project_id: プロジェクトID
            video_path: 編集済み動画のパス
            edit_name: 編集バージョン名
        
        Returns:
            保存先パス
        """
        project_path = self.projects_dir / project_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = project_path / "edited" / f"{edit_name}_{timestamp}.mp4"
        
        # ファイルをコピー
        shutil.copy2(video_path, save_path)
        
        return str(save_path)
    
    def save_final_export(self, project_id: str, video_path: str,
                         export_name: str = "final") -> str:
        """
        最終エクスポート動画を保存
        
        Args:
            project_id: プロジェクトID
            video_path: エクスポート動画のパス
            export_name: エクスポート名
        
        Returns:
            保存先パス
        """
        project_path = self.projects_dir / project_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = project_path / "exports" / f"{export_name}_{timestamp}.mp4"
        
        # ファイルをコピー
        shutil.copy2(video_path, save_path)
        
        # エクスポート情報を保存
        export_info = {
            "export_name": export_name,
            "timestamp": timestamp,
            "file_path": str(save_path),
            "file_size": os.path.getsize(save_path),
            "exported_at": datetime.now().isoformat()
        }
        
        info_path = project_path / "exports" / f"{export_name}_{timestamp}.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(export_info, f, ensure_ascii=False, indent=2)
        
        return str(save_path)
    
    def get_project_videos(self, project_id: str) -> Dict[str, List[Dict]]:
        """
        プロジェクトの全動画情報を取得
        
        Args:
            project_id: プロジェクトID
        
        Returns:
            動画情報の辞書
        """
        project_path = self.projects_dir / project_id
        
        if not project_path.exists():
            return {"scenes": [], "edited": [], "exports": []}
        
        result = {
            "scenes": [],
            "edited": [],
            "exports": []
        }
        
        # シーン動画
        scenes_dir = project_path / "scenes"
        if scenes_dir.exists():
            for json_file in sorted(scenes_dir.glob("*.json")):
                with open(json_file, 'r', encoding='utf-8') as f:
                    result["scenes"].append(json.load(f))
        
        # 編集済み動画
        edited_dir = project_path / "edited"
        if edited_dir.exists():
            for video_file in sorted(edited_dir.glob("*.mp4")):
                result["edited"].append({
                    "file_name": video_file.name,
                    "file_path": str(video_file),
                    "file_size": os.path.getsize(video_file),
                    "modified_at": datetime.fromtimestamp(
                        os.path.getmtime(video_file)
                    ).isoformat()
                })
        
        # エクスポート動画
        exports_dir = project_path / "exports"
        if exports_dir.exists():
            for json_file in sorted(exports_dir.glob("*.json")):
                with open(json_file, 'r', encoding='utf-8') as f:
                    result["exports"].append(json.load(f))
        
        return result
    
    def cleanup_temp_files(self):
        """一時ファイルをクリーンアップ"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        ストレージ情報を取得
        
        Returns:
            ストレージ使用状況
        """
        total_size = 0
        file_count = 0
        project_count = 0
        
        if self.storage_dir.exists():
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mov', '.avi')):
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            project_count = len(list(self.projects_dir.iterdir()))
        
        return {
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "project_count": project_count,
            "storage_path": str(self.storage_dir)
        }
    
    async def save_all_scene_videos(self, project_id: str, video_results: List[Dict],
                                   progress_callback: Optional[callable] = None) -> List[str]:
        """
        全シーンの動画を保存
        
        Args:
            project_id: プロジェクトID
            video_results: 動画生成結果のリスト
            progress_callback: 進捗コールバック
        
        Returns:
            保存されたファイルパスのリスト
        """
        saved_paths = []
        total = len(video_results)
        
        for i, result in enumerate(video_results):
            if progress_callback:
                progress = (i + 1) / total
                progress_callback(progress, f"動画 {i+1}/{total} を保存中...")
            
            # 動画情報を保存
            metadata = self.save_scene_video(
                project_id,
                result.get("scene_number", i+1),
                result
            )
            
            # URLから実際にダウンロード（必要な場合）
            if result.get("download_url") and not result.get("download_url", "").startswith("demo://"):
                await self.download_video(
                    result["download_url"],
                    Path(metadata["local_path"])
                )
            
            saved_paths.append(metadata["local_path"])
        
        if progress_callback:
            progress_callback(1.0, "✅ 全動画の保存完了")
        
        return saved_paths