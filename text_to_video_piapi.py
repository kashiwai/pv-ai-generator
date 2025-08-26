#!/usr/bin/env python3
"""
Text-to-Video PIAPI統合モジュール
PIAPIを通じてHailuo AI等でText-to-Video生成を実装
"""

import streamlit as st
import requests
import json
import time
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path

class TextToVideoPIAPI:
    """PIAPIを使用したText-to-Video生成"""
    
    def __init__(self):
        # APIキーを取得
        self.api_key = st.session_state.get('api_keys', {}).get('piapi', '')
        self.x_key = st.session_state.get('api_keys', {}).get('piapi_xkey', '')
        self.base_url = "https://api.piapi.ai"
        
        if not self.api_key or not self.x_key:
            st.warning("⚠️ PIAPIキーが設定されていません")
        
        self.headers = {
            "x-api-key": self.x_key,
            "Content-Type": "application/json"
        }
    
    def generate_video_from_text(self, 
                                text_prompt: str,
                                duration: int = 8,
                                motion_intensity: int = 5) -> Dict[str, Any]:
        """
        テキストから直接動画を生成
        
        Args:
            text_prompt: 動画生成用のテキストプロンプト
            duration: 動画の長さ（秒）
            motion_intensity: 動きの強度（1-10）
        
        Returns:
            生成結果
        """
        
        if not self.x_key:
            return {
                "status": "error",
                "message": "PIAPIキーが設定されていません"
            }
        
        # Hailuo AI Text-to-Video エンドポイント
        endpoint = f"{self.base_url}/api/v1/task"
        
        payload = {
            "model": "hailuo",  # Hailuo AIモデルを使用
            "task_type": "text-to-video",
            "input": {
                "prompt": text_prompt,
                "duration": duration,
                "motion_intensity": motion_intensity,
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "camera_movement": "smooth"
            }
        }
        
        try:
            # リクエスト送信
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # task_id取得
                task_id = None
                if isinstance(result, dict) and 'data' in result:
                    task_id = result['data'].get('task_id')
                
                if task_id:
                    return {
                        "status": "success",
                        "task_id": task_id,
                        "message": "動画生成を開始しました"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "task_idが取得できませんでした"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"APIエラー: {response.status_code}",
                    "details": response.text[:500]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"エラー: {str(e)}"
            }
    
    def check_video_status(self, task_id: str) -> Dict[str, Any]:
        """
        動画生成のステータスを確認
        
        Args:
            task_id: タスクID
        
        Returns:
            ステータス情報
        """
        endpoint = f"{self.base_url}/api/v1/task/{task_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result:
                    data = result['data']
                    status = data.get('status', 'unknown')
                    output = data.get('output', {})
                    
                    # ステータスの正規化
                    if status.lower() == 'completed':
                        video_url = output.get('video_url', '')
                        return {
                            "status": "completed",
                            "video_url": video_url,
                            "message": "動画生成完了"
                        }
                    elif status.lower() in ['processing', 'pending', 'staged']:
                        progress = output.get('progress', 0)
                        return {
                            "status": "processing",
                            "progress": progress,
                            "message": f"処理中... {progress}%"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"エラー: {status}"
                        }
                
            return {
                "status": "error",
                "message": f"ステータス確認エラー: {response.status_code}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"エラー: {str(e)}"
            }
    
    def wait_for_video_completion(self, task_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        動画生成の完了を待つ
        
        Args:
            task_id: タスクID
            timeout: タイムアウト（秒）
        
        Returns:
            完成した動画情報
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        while time.time() - start_time < timeout:
            # ステータスチェック
            result = self.check_video_status(task_id)
            
            if result['status'] == 'completed':
                progress_bar.progress(1.0)
                status_text.success("✅ 動画生成完了!")
                return result
            elif result['status'] == 'error':
                progress_bar.empty()
                status_text.error(f"❌ {result['message']}")
                return result
            else:
                # 進捗更新
                progress = result.get('progress', 0) / 100
                progress_bar.progress(progress)
                status_text.info(f"⏳ {result['message']}")
            
            time.sleep(3)  # 3秒ごとにチェック
        
        progress_bar.empty()
        status_text.warning("⚠️ タイムアウト: 生成に時間がかかっています")
        return {
            "status": "timeout",
            "message": f"タスク {task_id} がタイムアウトしました"
        }

def generate_videos_from_script(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    台本から動画を生成（Text-to-Video）
    
    Args:
        script: 生成された台本
        character_photos: キャラクター写真（オプション）
    
    Returns:
        生成された動画リスト
    """
    
    # Text-to-Video生成器を初期化
    generator = TextToVideoPIAPI()
    
    # デモモード確認
    if not generator.x_key or generator.x_key == 'demo':
        st.warning("⚠️ デモモード: 実際の動画は生成されません")
        # デモ用のダミーデータを返す
        return [
            {
                "scene_id": f"scene_{i+1}",
                "video_url": f"https://example.com/demo_video_{i+1}.mp4",
                "status": "completed",
                "duration": 8
            }
            for i in range(len(script.get('scenes', [])))
        ]
    
    generated_videos = []
    scenes = script.get('scenes', [])
    
    st.info(f"🎬 {len(scenes)}個のシーンから動画を生成します")
    
    for i, scene in enumerate(scenes):
        st.subheader(f"シーン {i+1}/{len(scenes)}")
        
        # 動画生成プロンプトを作成
        video_prompt = scene.get('visual_prompt', '')
        if not video_prompt:
            st.warning(f"シーン{i+1}のプロンプトがありません")
            continue
        
        # プロンプトからMidjourneyパラメータを除去
        video_prompt = video_prompt.replace('--ar 16:9', '').replace('--v 6', '').strip()
        
        # 動画生成開始
        with st.spinner(f"シーン{i+1}を生成中..."):
            result = generator.generate_video_from_text(
                text_prompt=video_prompt,
                duration=scene.get('duration', 8),
                motion_intensity=5
            )
            
            if result['status'] == 'success':
                # 完了を待つ
                task_id = result['task_id']
                st.info(f"タスクID: {task_id}")
                
                final_result = generator.wait_for_video_completion(task_id)
                
                if final_result['status'] == 'completed':
                    generated_videos.append({
                        "scene_id": scene.get('id', f'scene_{i+1}'),
                        "video_url": final_result['video_url'],
                        "status": "completed",
                        "duration": scene.get('duration', 8),
                        "prompt": video_prompt
                    })
                    st.success(f"✅ シーン{i+1}生成完了")
                else:
                    st.error(f"❌ シーン{i+1}生成失敗: {final_result['message']}")
            else:
                st.error(f"❌ エラー: {result['message']}")
    
    return generated_videos

# Streamlitアプリから呼び出すための関数
def run_text_to_video_workflow(script: Dict) -> Dict[str, Any]:
    """
    Text-to-Videoワークフローを実行
    
    Args:
        script: 生成された台本
    
    Returns:
        ワークフロー結果
    """
    
    st.header("🎬 Text-to-Video生成")
    
    # 動画生成
    videos = generate_videos_from_script(script)
    
    if videos:
        st.success(f"✅ {len(videos)}個の動画を生成しました")
        
        # 結果を表示
        st.subheader("生成された動画")
        for video in videos:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.video(video['video_url'])
            with col2:
                st.write(f"**シーンID:** {video['scene_id']}")
                st.write(f"**時間:** {video['duration']}秒")
                st.write(f"**ステータス:** {video['status']}")
        
        return {
            "status": "success",
            "videos": videos,
            "count": len(videos)
        }
    else:
        st.error("❌ 動画生成に失敗しました")
        return {
            "status": "error",
            "message": "動画生成に失敗しました"
        }