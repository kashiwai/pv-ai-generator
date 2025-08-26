#!/usr/bin/env python3
"""
統合Text-to-Videoモジュール
優先順位: 1. Google Veo3, 2. RunComfy Seedance, 3. PIAPI Hailuo
"""

import streamlit as st
import requests
import json
import time
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import aiohttp

class UnifiedTextToVideo:
    """統合Text-to-Video生成クラス"""
    
    def __init__(self):
        # APIキーを取得（新しいキー）
        self.google_api_key = st.session_state.get('api_keys', {}).get('google', 'AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8')
        
        # RunComfy API設定
        self.runcomfy_userid = "4368e0d2-edde-48c2-be18-e3caac513c1a"
        self.runcomfy_token = "79521d2f-f728-47fe-923a-fde31f65df1f"
        self.runcomfy_token2 = "2bc59974-218f-45d7-b50e-3fb11e970f33"
        self.runcomfy_base_url = "https://api.runcomfy.net/prod/v1"
        
        # PIAPI設定（Hailuo AI用）
        self.piapi_key = st.session_state.get('api_keys', {}).get('piapi', '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b')
        self.piapi_xkey = st.session_state.get('api_keys', {}).get('piapi_xkey', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
        self.piapi_base_url = "https://api.piapi.ai"
    
    def generate_with_google_veo(self, text_prompt: str, duration: int = 8) -> Dict[str, Any]:
        """
        Google Veo3で動画生成（最優先）
        Vertex AI経由で正式なVeo APIを使用
        """
        
        if not self.google_api_key:
            return {
                "status": "unavailable",
                "message": "Google APIキーが設定されていません"
            }
        
        st.info("🎬 Google Vertex AI Veoで動画生成を開始...")
        
        # Vertex AI Veoを使用
        try:
            from text_to_video_vertex_veo import generate_video_with_vertex_veo
            
            result = generate_video_with_vertex_veo(text_prompt, duration)
            
            if result.get('status') == 'completed':
                return result
            elif result.get('status') == 'unavailable':
                # Veoが利用できない場合はフォールバック
                st.warning("⚠️ Vertex AI Veoが利用できません。代替手段を使用します。")
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.google_api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Veo3スタイルのプロンプト生成
            enhanced_prompt = f"""
            Generate a high-quality video with the following specifications:
            - Duration: {duration} seconds
            - Style: Cinematic, professional
            - Content: {text_prompt}
            - Resolution: 1920x1080
            - Frame rate: 30fps
            """
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": enhanced_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "topK": 40,
                    "topP": 0.95
                }
            }
            
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Veo3が利用可能になるまでの仮処理
                return {
                    "status": "pending_veo3",
                    "message": "Veo3は現在限定アクセスです。代替手段を使用します。",
                    "fallback": True
                }
            else:
                return {
                    "status": "unavailable",
                    "message": f"Google API応答: {response.status_code}",
                    "fallback": True
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Veo3接続エラー: {str(e)}",
                "fallback": True
            }
    
    def generate_with_piapi_seedance(self, text_prompt: str, duration: int = 8) -> Dict[str, Any]:
        """
        PIAPI経由でSeedanceを使用（第2優先）
        """
        
        st.info("🎬 PIAPI Seedanceで動画生成中...")
        
        # PIAPI Seedanceエンドポイント（標準のPIAPIエンドポイントを使用）
        endpoint = f"{self.piapi_base_url}/api/v1/task"
        
        headers = {
            "x-api-key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        # PIAPI Seedanceペイロード
        payload = {
            "model": "seedance",
            "task_type": "text-to-video",
            "input": {
                "prompt": text_prompt,
                "duration": duration,
                "resolution": "1920x1080",
                "fps": 30,
                "aspect_ratio": "16:9",
                "motion_intensity": 5,
                "style": "cinematic"
            }
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                task_id = result.get('task_id', result.get('data', {}).get('task_id'))
                if task_id:
                    return {
                        "status": "success",
                        "task_id": task_id,
                        "provider": "piapi_seedance",
                        "message": "PIAPI Seedanceで生成開始"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "RunComfy: run_idが取得できませんでした"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"RunComfy APIエラー: {response.status_code}",
                    "details": response.text[:500]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"RunComfyエラー: {str(e)}"
            }
    
    def check_piapi_seedance_status(self, task_id: str) -> Dict[str, Any]:
        """
        PIAPI Seedanceタスクのステータス確認
        """
        endpoint = f"{self.piapi_base_url}/api/v1/task/{task_id}"
        
        headers = {
            "x-api-key": self.piapi_xkey
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                if status == 'completed':
                    outputs = result.get('outputs', {})
                    video_url = outputs.get('video_url', outputs.get('output_url', ''))
                    
                    return {
                        "status": "completed",
                        "video_url": video_url,
                        "message": "RunComfy Seedance生成完了"
                    }
                elif status in ['running', 'queued', 'processing']:
                    progress = result.get('progress', 0)
                    return {
                        "status": "processing",
                        "progress": progress,
                        "message": f"処理中... {progress}%"
                    }
                elif status == 'failed':
                    return {
                        "status": "error",
                        "message": result.get('error', 'RunComfy処理失敗')
                    }
                else:
                    return {
                        "status": status,
                        "message": f"ステータス: {status}"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"ステータス確認エラー: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"エラー: {str(e)}"
            }
    
    def generate_with_piapi_hailuo(self, text_prompt: str, duration: int = 8) -> Dict[str, Any]:
        """
        PIAPI経由でHailuo AIを使用（第3優先・フォールバック）
        """
        
        if not self.piapi_xkey:
            return {
                "status": "error",
                "message": "PIAPI XKEYが設定されていません"
            }
        
        st.info("🎬 PIAPI Hailuo AIで動画生成中...")
        
        endpoint = f"{self.piapi_base_url}/api/v1/task"
        
        headers = {
            "x-api-key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "hailuo",
            "task_type": "video_generation",
            "input": {
                "prompt": text_prompt,
                "model": "s2v-01",
                "expand_prompt": True,
                "duration": duration,
                "resolution": 768
            },
            "config": {
                "service_mode": "public"
            }
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result and 'task_id' in result['data']:
                    return {
                        "status": "success",
                        "task_id": result['data']['task_id'],
                        "provider": "piapi_hailuo",
                        "message": "PIAPI Hailuo AIで生成開始"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "task_idが取得できませんでした"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"PIAPI APIエラー: {response.status_code}",
                    "details": response.text[:500]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"PIAPIエラー: {str(e)}"
            }
    
    def check_piapi_status(self, task_id: str) -> Dict[str, Any]:
        """
        PIAPIタスクのステータス確認
        """
        endpoint = f"{self.piapi_base_url}/api/v1/task/{task_id}"
        
        headers = {
            "x-api-key": self.piapi_xkey
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'data' in result:
                    data = result['data']
                    status = data.get('status', 'unknown').lower()
                    output = data.get('output', {})
                    
                    if status == 'completed':
                        video_url = output.get('video_url', '')
                        return {
                            "status": "completed",
                            "video_url": video_url,
                            "message": "PIAPI Hailuo生成完了"
                        }
                    elif status in ['processing', 'pending', 'staged']:
                        progress = output.get('progress', 0)
                        return {
                            "status": "processing",
                            "progress": progress,
                            "message": f"処理中... {progress}%"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"ステータス: {status}"
                        }
                
                return {
                    "status": "error",
                    "message": "データが見つかりません"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"エラー: {str(e)}"
            }
    
    def wait_for_completion(self, provider: str, task_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        動画生成の完了を待つ
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        check_interval = 3
        
        while time.time() - start_time < timeout:
            # プロバイダーに応じてステータス確認
            if provider == "piapi_seedance":
                result = self.check_piapi_seedance_status(task_id)
            elif provider == "piapi_hailuo":
                result = self.check_piapi_status(task_id)
            else:
                result = {"status": "error", "message": "不明なプロバイダー"}
            
            if result['status'] == 'completed':
                progress_bar.progress(1.0)
                status_text.success(f"✅ 動画生成完了!")
                return result
            elif result['status'] == 'error':
                progress_bar.empty()
                status_text.error(f"❌ {result['message']}")
                return result
            else:
                progress = result.get('progress', 0) / 100
                if progress == 0:
                    elapsed = time.time() - start_time
                    progress = min(elapsed / timeout * 0.9, 0.9)
                
                progress_bar.progress(progress)
                status_text.info(f"⏳ {result.get('message', '処理中...')}")
            
            time.sleep(check_interval)
        
        progress_bar.empty()
        status_text.warning(f"⚠️ タイムアウト")
        return {
            "status": "timeout",
            "message": f"タスク {task_id} がタイムアウトしました"
        }
    
    def generate_video_auto(self, text_prompt: str, duration: int = 8) -> Dict[str, Any]:
        """
        優先順位に従って自動的にAPIを選択して動画生成
        優先順位: 1. Veo3, 2. RunComfy Seedance, 3. PIAPI Hailuo
        """
        
        # 1. Google Veo3を試す（最優先）
        st.info("🎯 優先順位1: Google Veo3を確認中...")
        result = self.generate_with_google_veo(text_prompt, duration)
        
        if result.get('status') != 'unavailable' and not result.get('fallback'):
            # Veo3が利用可能な場合
            if 'task_id' in result or 'operation_id' in result:
                return self.wait_for_completion('veo3', result.get('task_id', result.get('operation_id')))
            return result
        
        # 2. PIAPI Seedanceを試す（第2優先）
        st.info("🎯 優先順位2: PIAPI Seedanceで生成...")
        result = self.generate_with_piapi_seedance(text_prompt, duration)
        
        if result.get('status') == 'success':
            return self.wait_for_completion('piapi_seedance', result['task_id'])
        
        # 3. PIAPI Hailuoを試す（フォールバック）
        st.info("🎯 優先順位3: PIAPI Hailuo AIで生成...")
        result = self.generate_with_piapi_hailuo(text_prompt, duration)
        
        if result.get('status') == 'success':
            return self.wait_for_completion('piapi_hailuo', result['task_id'])
        
        return {
            "status": "error",
            "message": "すべてのText-to-Video APIが利用できません"
        }

def generate_videos_from_script(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    台本から動画を生成（統合版）
    """
    
    generator = UnifiedTextToVideo()
    generated_videos = []
    scenes = script.get('scenes', [])
    
    st.info(f"🎬 {len(scenes)}個のシーンから動画を生成します")
    st.success("優先順位: 1️⃣ Google Veo3 → 2️⃣ RunComfy Seedance → 3️⃣ PIAPI Hailuo")
    
    for i, scene in enumerate(scenes):
        st.subheader(f"シーン {i+1}/{len(scenes)}")
        
        # プロンプトを準備
        video_prompt = scene.get('visual_prompt', scene.get('content', ''))
        if not video_prompt:
            st.warning(f"シーン{i+1}のプロンプトがありません")
            continue
        
        # Midjourneyパラメータを除去
        video_prompt = video_prompt.replace('--ar 16:9', '').replace('--v 6', '').replace('--cref', '').strip()
        
        with st.expander(f"プロンプト: {video_prompt[:50]}...", expanded=False):
            st.text(video_prompt)
        
        # 動画生成
        with st.spinner(f"シーン{i+1}を生成中..."):
            result = generator.generate_video_auto(
                text_prompt=video_prompt,
                duration=scene.get('duration', 8)
            )
            
            if result.get('status') == 'completed':
                video_info = {
                    "scene_id": scene.get('id', f'scene_{i+1}'),
                    "video_url": result.get('video_url', ''),
                    "status": "completed",
                    "duration": scene.get('duration', 8),
                    "prompt": video_prompt,
                    "provider": result.get('provider', 'unknown')
                }
                generated_videos.append(video_info)
                
                st.success(f"✅ シーン{i+1}生成完了 (プロバイダー: {result.get('provider', 'unknown')})")
                
                if video_info['video_url']:
                    st.video(video_info['video_url'])
            else:
                st.error(f"❌ シーン{i+1}生成失敗: {result.get('message', 'Unknown error')}")
                generated_videos.append({
                    "scene_id": scene.get('id', f'scene_{i+1}'),
                    "status": "failed",
                    "error": result.get('message', 'Unknown error'),
                    "prompt": video_prompt
                })
    
    return generated_videos

# エクスポート
__all__ = ['UnifiedTextToVideo', 'generate_videos_from_script']