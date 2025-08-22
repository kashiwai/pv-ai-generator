"""
動画編集モジュール
生成された動画の編集、合成、エフェクト追加
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import json

class VideoEditor:
    """動画編集クラス"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.temp_dir = Path(tempfile.gettempdir()) / "pv_editor"
        self.temp_dir.mkdir(exist_ok=True)
    
    def merge_scenes(self, 
                    scene_videos: List[str],
                    audio_file: str,
                    output_path: str,
                    transitions: str = "crossfade",
                    progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        複数のシーン動画を結合して音楽と同期
        
        Args:
            scene_videos: シーン動画のパスリスト
            audio_file: 音楽ファイルのパス
            output_path: 出力ファイルパス
            transitions: トランジション効果
            progress_callback: 進捗コールバック
        
        Returns:
            編集結果
        """
        try:
            if progress_callback:
                progress_callback(0.1, "🎬 動画編集を開始...")
            
            # FFmpegを使用して動画を結合
            concat_file = self.temp_dir / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for video in scene_videos:
                    f.write(f"file '{video}'\n")
            
            if progress_callback:
                progress_callback(0.3, "📹 シーンを結合中...")
            
            # 動画を結合
            merged_video = self.temp_dir / "merged_video.mp4"
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                str(merged_video),
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"動画結合エラー: {result.stderr}"
                }
            
            if progress_callback:
                progress_callback(0.6, "🎵 音楽を追加中...")
            
            # 音楽を追加
            cmd = [
                'ffmpeg',
                '-i', str(merged_video),
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                output_path,
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(1.0, "✅ 編集完了！")
                
                return {
                    "status": "success",
                    "output_path": output_path,
                    "duration": self._get_video_duration(output_path)
                }
            else:
                return {
                    "status": "error",
                    "message": f"音楽追加エラー: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"編集エラー: {str(e)}"
            }
    
    def add_transitions(self,
                       video_path: str,
                       transition_type: str = "fade",
                       duration: float = 1.0) -> str:
        """
        トランジション効果を追加
        
        Args:
            video_path: 動画パス
            transition_type: トランジションタイプ
            duration: トランジション時間
        
        Returns:
            出力パス
        """
        output_path = self.temp_dir / f"transition_{Path(video_path).name}"
        
        # FFmpegフィルターでトランジション追加
        if transition_type == "fade":
            filter_str = f"fade=t=in:st=0:d={duration},fade=t=out:st=-{duration}:d={duration}"
        elif transition_type == "crossfade":
            filter_str = f"xfade=transition=fade:duration={duration}:offset=0"
        else:
            filter_str = ""
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def add_text_overlay(self,
                        video_path: str,
                        text: str,
                        position: str = "bottom",
                        font_size: int = 48,
                        color: str = "white") -> str:
        """
        テキストオーバーレイを追加
        
        Args:
            video_path: 動画パス
            text: 表示テキスト
            position: 表示位置
            font_size: フォントサイズ
            color: テキスト色
        
        Returns:
            出力パス
        """
        output_path = self.temp_dir / f"text_{Path(video_path).name}"
        
        # 位置を設定
        if position == "top":
            pos_str = "x=(w-text_w)/2:y=50"
        elif position == "center":
            pos_str = "x=(w-text_w)/2:y=(h-text_h)/2"
        else:  # bottom
            pos_str = "x=(w-text_w)/2:y=h-text_h-50"
        
        # FFmpegでテキストオーバーレイ
        filter_str = f"drawtext=text='{text}':fontsize={font_size}:fontcolor={color}:{pos_str}"
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def add_filter(self,
                  video_path: str,
                  filter_type: str = "vintage") -> str:
        """
        フィルターエフェクトを追加
        
        Args:
            video_path: 動画パス
            filter_type: フィルタータイプ
        
        Returns:
            出力パス
        """
        output_path = self.temp_dir / f"filter_{Path(video_path).name}"
        
        # フィルター定義
        filters = {
            "vintage": "curves=vintage",
            "grayscale": "colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3",
            "blur": "boxblur=5:1",
            "sharpen": "unsharp=5:5:1.0:5:5:0.0",
            "brightness": "eq=brightness=0.1",
            "contrast": "eq=contrast=1.2",
            "sepia": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        }
        
        filter_str = filters.get(filter_type, "")
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def adjust_speed(self,
                    video_path: str,
                    speed: float = 1.0) -> str:
        """
        動画の速度を調整
        
        Args:
            video_path: 動画パス
            speed: 速度倍率
        
        Returns:
            出力パス
        """
        output_path = self.temp_dir / f"speed_{Path(video_path).name}"
        
        # FFmpegで速度調整
        video_filter = f"setpts={1/speed}*PTS"
        audio_filter = f"atempo={speed}"
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', video_filter,
            '-filter:a', audio_filter,
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def extract_clip(self,
                    video_path: str,
                    start_time: float,
                    end_time: float) -> str:
        """
        動画の一部を切り出し
        
        Args:
            video_path: 動画パス
            start_time: 開始時間（秒）
            end_time: 終了時間（秒）
        
        Returns:
            出力パス
        """
        output_path = self.temp_dir / f"clip_{Path(video_path).name}"
        duration = end_time - start_time
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def create_thumbnail(self,
                        video_path: str,
                        time_position: float = 0) -> str:
        """
        サムネイル画像を生成
        
        Args:
            video_path: 動画パス
            time_position: サムネイル位置（秒）
        
        Returns:
            画像パス
        """
        output_path = self.temp_dir / f"thumb_{Path(video_path).stem}.jpg"
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(time_position),
            '-vframes', '1',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, capture_output=True)
        return str(output_path)
    
    def _get_video_duration(self, video_path: str) -> float:
        """動画の長さを取得"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get('format', {}).get('duration', 0))
        
        return 0
    
    def apply_batch_edits(self,
                         video_path: str,
                         edits: List[Dict[str, Any]],
                         progress_callback: Optional[callable] = None) -> str:
        """
        複数の編集を一括適用
        
        Args:
            video_path: 動画パス
            edits: 編集リスト
            progress_callback: 進捗コールバック
        
        Returns:
            最終出力パス
        """
        current_path = video_path
        total_edits = len(edits)
        
        for i, edit in enumerate(edits):
            if progress_callback:
                progress = (i + 1) / total_edits
                progress_callback(progress, f"編集 {i+1}/{total_edits}: {edit.get('type', 'unknown')}")
            
            edit_type = edit.get('type')
            
            if edit_type == 'transition':
                current_path = self.add_transitions(
                    current_path,
                    edit.get('transition_type', 'fade'),
                    edit.get('duration', 1.0)
                )
            elif edit_type == 'text':
                current_path = self.add_text_overlay(
                    current_path,
                    edit.get('text', ''),
                    edit.get('position', 'bottom'),
                    edit.get('font_size', 48),
                    edit.get('color', 'white')
                )
            elif edit_type == 'filter':
                current_path = self.add_filter(
                    current_path,
                    edit.get('filter_type', 'vintage')
                )
            elif edit_type == 'speed':
                current_path = self.adjust_speed(
                    current_path,
                    edit.get('speed', 1.0)
                )
        
        if progress_callback:
            progress_callback(1.0, "✅ 全編集完了")
        
        return current_path