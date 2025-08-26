#!/usr/bin/env python3
"""
Text-to-Video Google Veo3 & Seedance統合モジュール
Google Veo3とSeedance APIを使用してText-to-Video生成を実装
"""

import streamlit as st
import requests
import json
import time
import base64
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from pathlib import Path

class TextToVideoVeo3Seedance:
    """Google Veo3とSeedanceを使用したText-to-Video生成"""
    
    def __init__(self):
        # APIキーを取得
        self.google_api_key = st.session_state.get('api_keys', {}).get('google', '')
        self.seedance_api_key = st.session_state.get('api_keys', {}).get('seedance', '')
        
        # Google Veo3エンドポイント（正式版がリリースされたら更新）
        self.veo3_base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Seedanceエンドポイント
        self.seedance_base_url = "https://api.seedance.ai/v1"
        
        if not self.google_api_key and not self.seedance_api_key:
            st.warning("⚠️ Google Veo3またはSeedance APIキーが設定されていません")
    
    def generate_video_with_veo3(self, 
                                text_prompt: str,
                                duration: int = 8,
                                resolution: str = "1080p",
                                aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """
        Google Veo3を使用してテキストから動画を生成
        
        Args:
            text_prompt: 動画生成用のテキストプロンプト
            duration: 動画の長さ（秒）
            resolution: 解像度
            aspect_ratio: アスペクト比
        
        Returns:
            生成結果
        """
        
        if not self.google_api_key:
            return {
                "status": "error",
                "message": "Google APIキーが設定されていません"
            }
        
        # Google Veo3 APIエンドポイント
        # 注: Veo3の正式なAPIがリリースされたら更新が必要
        endpoint = f"{self.veo3_base_url}/models/veo3:generateVideo?key={self.google_api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": text_prompt,
            "videoConfig": {
                "duration": f"{duration}s",
                "resolution": resolution,
                "aspectRatio": aspect_ratio,
                "fps": 30,
                "quality": "high",
                "style": "cinematic"
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # Veo3のレスポンス処理
                if 'name' in result:
                    operation_name = result['name']
                    return {
                        "status": "success",
                        "operation_name": operation_name,
                        "message": "Veo3で動画生成を開始しました"
                    }
                else:
                    return {
                        "status": "success",
                        "video_url": result.get('videoUrl', ''),
                        "message": "動画生成完了"
                    }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "status": "error",
                    "message": f"Veo3 APIエラー: {response.status_code}",
                    "details": error_data.get('error', {}).get('message', response.text[:500])
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Veo3 APIタイムアウト"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Veo3エラー: {str(e)}"
            }
    
    def check_veo3_status(self, operation_name: str) -> Dict[str, Any]:
        """
        Veo3の動画生成ステータスを確認
        
        Args:
            operation_name: オペレーション名
        
        Returns:
            ステータス情報
        """
        endpoint = f"{self.veo3_base_url}/operations/{operation_name}?key={self.google_api_key}"
        
        try:
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('done'):
                    if 'response' in result:
                        video_data = result['response']
                        return {
                            "status": "completed",
                            "video_url": video_data.get('videoUrl', ''),
                            "message": "Veo3動画生成完了"
                        }
                    elif 'error' in result:
                        return {
                            "status": "error",
                            "message": f"Veo3エラー: {result['error'].get('message', 'Unknown error')}"
                        }
                else:
                    metadata = result.get('metadata', {})
                    progress = metadata.get('progress', 0)
                    return {
                        "status": "processing",
                        "progress": progress,
                        "message": f"Veo3処理中... {progress}%"
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
    
    def generate_video_with_seedance(self, 
                                    text_prompt: str,
                                    duration: int = 8,
                                    style: str = "realistic") -> Dict[str, Any]:
        """
        Seedanceを使用してテキストから動画を生成
        
        Args:
            text_prompt: 動画生成用のテキストプロンプト
            duration: 動画の長さ（秒）
            style: スタイル（realistic, anime, cartoon等）
        
        Returns:
            生成結果
        """
        
        if not self.seedance_api_key:
            return {
                "status": "error",
                "message": "Seedance APIキーが設定されていません"
            }
        
        # Seedance APIエンドポイント
        endpoint = f"{self.seedance_base_url}/generate/video"
        
        headers = {
            "Authorization": f"Bearer {self.seedance_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": text_prompt,
            "duration": duration,
            "style": style,
            "resolution": "1920x1080",
            "fps": 30,
            "aspectRatio": "16:9",
            "quality": "high",
            "motion_intensity": 5,
            "camera_movement": "dynamic"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                task_id = result.get('task_id', result.get('id'))
                if task_id:
                    return {
                        "status": "success",
                        "task_id": task_id,
                        "message": "Seedanceで動画生成を開始しました"
                    }
                else:
                    # 即座に生成される場合
                    return {
                        "status": "success",
                        "video_url": result.get('video_url', ''),
                        "message": "動画生成完了"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Seedance APIエラー: {response.status_code}",
                    "details": response.text[:500]
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Seedance APIタイムアウト"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Seedanceエラー: {str(e)}"
            }
    
    def check_seedance_status(self, task_id: str) -> Dict[str, Any]:
        """
        Seedanceの動画生成ステータスを確認
        
        Args:
            task_id: タスクID
        
        Returns:
            ステータス情報
        """
        endpoint = f"{self.seedance_base_url}/task/status/{task_id}"
        
        headers = {
            "Authorization": f"Bearer {self.seedance_api_key}"
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                status = result.get('status', 'unknown').lower()
                
                if status in ['completed', 'success', 'done']:
                    return {
                        "status": "completed",
                        "video_url": result.get('video_url', result.get('output_url', '')),
                        "download_url": result.get('download_url', ''),
                        "message": "Seedance動画生成完了"
                    }
                elif status in ['processing', 'pending', 'running']:
                    progress = result.get('progress', 0)
                    return {
                        "status": "processing",
                        "progress": progress,
                        "message": f"Seedance処理中... {progress}%"
                    }
                elif status in ['failed', 'error']:
                    return {
                        "status": "error",
                        "message": f"Seedanceエラー: {result.get('error_message', 'Generation failed')}"
                    }
                else:
                    return {
                        "status": "unknown",
                        "message": f"不明なステータス: {status}"
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
    
    def wait_for_completion(self, provider: str, task_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        動画生成の完了を待つ
        
        Args:
            provider: プロバイダー（veo3 or seedance）
            task_id: タスクIDまたはオペレーション名
            timeout: タイムアウト（秒）
        
        Returns:
            完成した動画情報
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        check_interval = 3  # 3秒ごとにチェック
        
        while time.time() - start_time < timeout:
            # ステータスチェック
            if provider == "veo3":
                result = self.check_veo3_status(task_id)
            else:
                result = self.check_seedance_status(task_id)
            
            if result['status'] == 'completed':
                progress_bar.progress(1.0)
                status_text.success(f"✅ {provider.upper()}動画生成完了!")
                return result
            elif result['status'] == 'error':
                progress_bar.empty()
                status_text.error(f"❌ {result['message']}")
                return result
            else:
                # 進捗更新
                progress = result.get('progress', 0) / 100
                if progress == 0:
                    # 進捗情報がない場合は経過時間から推定
                    elapsed = time.time() - start_time
                    progress = min(elapsed / timeout * 0.9, 0.9)  # 最大90%まで
                
                progress_bar.progress(progress)
                status_text.info(f"⏳ {result.get('message', f'{provider.upper()}処理中...')}")
            
            time.sleep(check_interval)
        
        progress_bar.empty()
        status_text.warning(f"⚠️ タイムアウト: {provider.upper()}生成に時間がかかっています")
        return {
            "status": "timeout",
            "message": f"タスク {task_id} がタイムアウトしました"
        }
    
    def generate_video_auto(self, text_prompt: str, duration: int = 8) -> Dict[str, Any]:
        """
        利用可能なAPIを自動選択して動画生成
        
        Args:
            text_prompt: 動画生成プロンプト
            duration: 動画の長さ
        
        Returns:
            生成結果
        """
        # Google Veo3を優先的に試す
        if self.google_api_key:
            st.info("🎬 Google Veo3で動画生成を試みます...")
            result = self.generate_video_with_veo3(text_prompt, duration)
            
            if result['status'] == 'success':
                if 'operation_name' in result:
                    # 非同期処理の場合
                    final_result = self.wait_for_completion('veo3', result['operation_name'])
                    if final_result['status'] == 'completed':
                        return final_result
                else:
                    # 即座に完了した場合
                    return result
            else:
                st.warning(f"⚠️ Veo3生成失敗: {result['message']}")
        
        # Seedanceを試す
        if self.seedance_api_key:
            st.info("🎬 Seedanceで動画生成を試みます...")
            result = self.generate_video_with_seedance(text_prompt, duration)
            
            if result['status'] == 'success':
                if 'task_id' in result:
                    # 非同期処理の場合
                    final_result = self.wait_for_completion('seedance', result['task_id'])
                    return final_result
                else:
                    # 即座に完了した場合
                    return result
            else:
                st.warning(f"⚠️ Seedance生成失敗: {result['message']}")
        
        # どちらのAPIキーも設定されていない場合
        if not self.google_api_key and not self.seedance_api_key:
            return {
                "status": "error",
                "message": "Google Veo3またはSeedance APIキーを設定してください"
            }
        
        return {
            "status": "error",
            "message": "動画生成に失敗しました"
        }

def generate_videos_from_script(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    台本から動画を生成（Google Veo3/Seedance Text-to-Video）
    
    Args:
        script: 生成された台本
        character_photos: キャラクター写真（オプション - 将来的な拡張用）
    
    Returns:
        生成された動画リスト
    """
    
    # Text-to-Video生成器を初期化
    generator = TextToVideoVeo3Seedance()
    
    # APIキー確認
    if not generator.google_api_key and not generator.seedance_api_key:
        st.error("❌ Google Veo3またはSeedance APIキーが設定されていません")
        st.info("サイドバーでAPIキーを設定してください:")
        st.code("Google API Key: AIzaSyCUDhyex-CRvb4ad9V90rW_Kvn9a_RmRvU")
        st.code("Seedance API Key: 6a28ac0141124793b1823df53cdd2207")
        
        # デモモードのダミーデータを返す
        return [
            {
                "scene_id": f"scene_{i+1}",
                "video_url": f"https://example.com/demo_video_{i+1}.mp4",
                "status": "demo",
                "duration": 8,
                "provider": "demo"
            }
            for i in range(len(script.get('scenes', [])))
        ]
    
    generated_videos = []
    scenes = script.get('scenes', [])
    
    st.info(f"🎬 {len(scenes)}個のシーンから動画を生成します")
    
    # 利用可能なプロバイダーを表示
    providers = []
    if generator.google_api_key:
        providers.append("Google Veo3")
    if generator.seedance_api_key:
        providers.append("Seedance")
    
    st.success(f"✅ 利用可能なAPI: {', '.join(providers)}")
    
    for i, scene in enumerate(scenes):
        st.subheader(f"シーン {i+1}/{len(scenes)}")
        
        # 動画生成プロンプトを作成
        video_prompt = scene.get('visual_prompt', scene.get('content', ''))
        if not video_prompt:
            st.warning(f"シーン{i+1}のプロンプトがありません")
            continue
        
        # Midjourneyパラメータを除去（Text-to-Videoには不要）
        video_prompt = video_prompt.replace('--ar 16:9', '').replace('--v 6', '').replace('--cref', '').strip()
        
        # プロンプトを表示
        with st.expander(f"プロンプト: {video_prompt[:50]}...", expanded=False):
            st.text(video_prompt)
        
        # 動画生成開始
        with st.spinner(f"シーン{i+1}を生成中..."):
            result = generator.generate_video_auto(
                text_prompt=video_prompt,
                duration=scene.get('duration', 8)
            )
            
            if result.get('status') in ['completed', 'success']:
                video_info = {
                    "scene_id": scene.get('id', f'scene_{i+1}'),
                    "video_url": result.get('video_url', ''),
                    "download_url": result.get('download_url', ''),
                    "status": "completed",
                    "duration": scene.get('duration', 8),
                    "prompt": video_prompt,
                    "provider": "veo3" if generator.google_api_key else "seedance"
                }
                generated_videos.append(video_info)
                
                st.success(f"✅ シーン{i+1}生成完了")
                
                # 動画プレビュー
                if video_info['video_url']:
                    st.video(video_info['video_url'])
            else:
                st.error(f"❌ シーン{i+1}生成失敗: {result.get('message', 'Unknown error')}")
                
                # エラー時でも記録
                generated_videos.append({
                    "scene_id": scene.get('id', f'scene_{i+1}'),
                    "status": "failed",
                    "error": result.get('message', 'Unknown error'),
                    "prompt": video_prompt
                })
    
    return generated_videos

# Streamlitアプリから呼び出すための関数
def run_text_to_video_workflow(script: Dict) -> Dict[str, Any]:
    """
    Google Veo3/Seedance Text-to-Videoワークフローを実行
    
    Args:
        script: 生成された台本
    
    Returns:
        ワークフロー結果
    """
    
    st.header("🎬 Text-to-Video生成 (Google Veo3 / Seedance)")
    
    # API設定確認
    api_keys = st.session_state.get('api_keys', {})
    
    if not api_keys.get('google') and not api_keys.get('seedance'):
        st.warning("⚠️ Text-to-Video APIキーが設定されていません")
        
        with st.expander("APIキー設定方法", expanded=True):
            st.markdown("""
            ### Google Veo3 APIキー設定
            1. サイドバーの「Google API Key」フィールドに以下を入力:
            ```
            AIzaSyCUDhyex-CRvb4ad9V90rW_Kvn9a_RmRvU
            ```
            
            ### Seedance APIキー設定
            1. サイドバーの「Seedance API Key」フィールドに以下を入力:
            ```
            6a28ac0141124793b1823df53cdd2207
            ```
            
            2. 「設定を保存」ボタンをクリック
            """)
    
    # 動画生成
    videos = generate_videos_from_script(script)
    
    if videos:
        success_count = len([v for v in videos if v.get('status') == 'completed'])
        
        if success_count > 0:
            st.success(f"✅ {success_count}個の動画を生成しました")
        else:
            st.warning(f"⚠️ 動画生成に問題がありました")
        
        # 結果を表示
        st.subheader("生成された動画")
        
        for video in videos:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if video.get('status') == 'completed' and video.get('video_url'):
                    st.video(video['video_url'])
                elif video.get('status') == 'failed':
                    st.error(f"❌ 生成失敗: {video.get('error', 'Unknown error')}")
                else:
                    st.info(f"📹 {video['scene_id']} - {video.get('status', 'Unknown')}")
            
            with col2:
                st.write(f"**シーンID:** {video['scene_id']}")
                st.write(f"**時間:** {video.get('duration', 8)}秒")
                st.write(f"**ステータス:** {video.get('status', 'unknown')}")
                st.write(f"**プロバイダー:** {video.get('provider', 'N/A')}")
                
                if video.get('download_url'):
                    st.markdown(f"[📥 ダウンロード]({video['download_url']})")
        
        return {
            "status": "success" if success_count > 0 else "partial",
            "videos": videos,
            "count": len(videos),
            "success_count": success_count
        }
    else:
        st.error("❌ 動画生成に失敗しました")
        return {
            "status": "error",
            "message": "動画生成に失敗しました"
        }

# エクスポート
__all__ = ['TextToVideoVeo3Seedance', 'generate_videos_from_script', 'run_text_to_video_workflow']