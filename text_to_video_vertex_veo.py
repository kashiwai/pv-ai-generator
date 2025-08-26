#!/usr/bin/env python3
"""
Google Vertex AI Veo Text-to-Video実装
正式なGoogle Veo APIを使用
"""

import streamlit as st
import time
import json
import base64
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests

# Google Cloud SDKは条件付きインポート
try:
    from google.cloud import aiplatform
    from google.oauth2 import service_account
    import vertexai
    from vertexai.preview.vision_models import VideoGenerationModel
    import google.auth
    import google.auth.transport.requests
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    st.warning("⚠️ Google Cloud SDKがインストールされていません。APIキーモードで動作します。")

class VertexAIVeo:
    """Google Vertex AI Veo Text-to-Video生成クラス"""
    
    def __init__(self):
        # Google Cloud設定ヘルパーを使用
        from google_cloud_setup import initialize_google_cloud
        
        # Google Cloud設定
        self.location = "us-central1"  # リージョン設定
        self.google_api_key = st.session_state.get('api_keys', {}).get('google', 'AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8')
        
        # Google Cloud SDK初期化
        self.initialized = initialize_google_cloud()
        
        # プロジェクトID取得
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    
    def generate_video_with_veo(self, 
                               text_prompt: str,
                               duration: int = 8,
                               aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """
        Google Veoで動画生成（正式版）
        
        Args:
            text_prompt: 動画生成用のプロンプト
            duration: 動画の長さ（秒）
            aspect_ratio: アスペクト比
        
        Returns:
            生成結果
        """
        
        if not self.initialized:
            # Vertex AIが初期化されていない場合は、REST APIを直接使用
            return self.generate_video_with_rest_api(text_prompt, duration, aspect_ratio)
        
        try:
            st.info("🎬 Google Veoで動画生成を開始...")
            
            # VideoGenerationModelを使用
            model = VideoGenerationModel.from_pretrained("veo")
            
            # 動画生成パラメータ
            generation_config = {
                "prompt": text_prompt,
                "duration": f"{duration}s",
                "aspect_ratio": aspect_ratio,
                "resolution": "1920x1080",
                "fps": 30,
                "style": "cinematic"
            }
            
            # 動画生成開始
            response = model.generate_video(
                prompt=text_prompt,
                **generation_config
            )
            
            # ジョブIDを取得
            if hasattr(response, 'name'):
                return {
                    "status": "success",
                    "job_id": response.name,
                    "provider": "vertex_ai_veo",
                    "message": "Google Veoで生成開始"
                }
            else:
                return {
                    "status": "error",
                    "message": "ジョブIDを取得できませんでした"
                }
                
        except Exception as e:
            st.warning(f"⚠️ Vertex AI SDK エラー: {str(e)}")
            # REST APIにフォールバック
            return self.generate_video_with_rest_api(text_prompt, duration, aspect_ratio)
    
    def generate_video_with_rest_api(self, 
                                    text_prompt: str,
                                    duration: int = 8,
                                    aspect_ratio: str = "16:9") -> Dict[str, Any]:
        """
        REST API経由でVeo動画生成
        """
        
        st.info("🎬 Google Veo REST APIで動画生成...")
        
        # アクセストークンを取得
        access_token = self._get_access_token()
        
        if not access_token:
            return {
                "status": "error",
                "message": "アクセストークンを取得できませんでした"
            }
        
        # Veo API エンドポイント
        endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo:predict"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # リクエストボディ
        payload = {
            "instances": [{
                "prompt": text_prompt
            }],
            "parameters": {
                "duration": duration,
                "aspectRatio": aspect_ratio.replace(":", "_"),  # "16:9" -> "16_9"
                "resolution": "1920x1080",
                "frameRate": 30,
                "videoCodec": "h264",
                "audioCodec": "aac",
                "style": "cinematic",
                "cameraMovement": "smooth",
                "lightingStyle": "natural"
            }
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                
                # レスポンスから動画URLまたはジョブIDを取得
                if 'predictions' in result:
                    prediction = result['predictions'][0]
                    
                    if 'videoUrl' in prediction:
                        return {
                            "status": "completed",
                            "video_url": prediction['videoUrl'],
                            "provider": "vertex_ai_veo",
                            "message": "Google Veo生成完了"
                        }
                    elif 'operationId' in prediction:
                        return {
                            "status": "success",
                            "job_id": prediction['operationId'],
                            "provider": "vertex_ai_veo",
                            "message": "Google Veo生成開始"
                        }
                
                # 非同期処理の場合
                if 'name' in result:
                    return {
                        "status": "success",
                        "job_id": result['name'],
                        "provider": "vertex_ai_veo",
                        "message": "Google Veo生成開始"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "予期しないレスポンス形式",
                        "details": str(result)[:500]
                    }
                    
            elif response.status_code == 404:
                return {
                    "status": "unavailable",
                    "message": "Veo APIが利用できません。プロジェクトでVeoが有効か確認してください。",
                    "fallback": True
                }
            else:
                return {
                    "status": "error",
                    "message": f"API エラー: {response.status_code}",
                    "details": response.text[:500]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"リクエストエラー: {str(e)}"
            }
    
    def _get_access_token(self) -> Optional[str]:
        """
        Google Cloud アクセストークンを取得
        """
        try:
            # デフォルト認証情報を使用
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # プロジェクトIDを更新
            if project:
                self.project_id = project
            
            # トークンをリフレッシュ
            auth_request = google.auth.transport.requests.Request()
            credentials.refresh(auth_request)
            
            return credentials.token
            
        except Exception as e:
            # APIキーを使用した認証にフォールバック
            st.warning(f"⚠️ デフォルト認証失敗: {str(e)}")
            
            # APIキー認証（制限あり）
            return None
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Veoジョブのステータス確認
        """
        
        access_token = self._get_access_token()
        
        if not access_token:
            return {
                "status": "error",
                "message": "アクセストークンを取得できませんでした"
            }
        
        # オペレーションステータスエンドポイント
        endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/{job_id}"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('done'):
                    # 完了
                    if 'response' in result:
                        response_data = result['response']
                        
                        if 'videoUrl' in response_data:
                            return {
                                "status": "completed",
                                "video_url": response_data['videoUrl'],
                                "message": "Google Veo生成完了"
                            }
                    
                    if 'error' in result:
                        return {
                            "status": "error",
                            "message": result['error'].get('message', 'エラーが発生しました')
                        }
                else:
                    # 処理中
                    metadata = result.get('metadata', {})
                    progress = metadata.get('progress', 0)
                    
                    return {
                        "status": "processing",
                        "progress": progress,
                        "message": f"処理中... {progress}%"
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
    
    def wait_for_completion(self, job_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        動画生成の完了を待つ
        """
        start_time = time.time()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        check_interval = 5  # 5秒ごとにチェック
        
        while time.time() - start_time < timeout:
            result = self.check_job_status(job_id)
            
            if result['status'] == 'completed':
                progress_bar.progress(1.0)
                status_text.success("✅ Google Veo動画生成完了!")
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
                status_text.info(f"⏳ {result.get('message', 'Google Veo処理中...')}")
            
            time.sleep(check_interval)
        
        progress_bar.empty()
        status_text.warning("⚠️ タイムアウト")
        return {
            "status": "timeout",
            "message": f"ジョブ {job_id} がタイムアウトしました"
        }

def generate_video_with_vertex_veo(text_prompt: str, duration: int = 8) -> Dict[str, Any]:
    """
    Vertex AI Veoで動画生成（メイン関数）
    """
    
    veo = VertexAIVeo()
    
    # 動画生成開始
    result = veo.generate_video_with_veo(text_prompt, duration)
    
    if result.get('status') == 'success' and 'job_id' in result:
        # ジョブの完了を待つ
        return veo.wait_for_completion(result['job_id'])
    
    return result

# エクスポート
__all__ = ['VertexAIVeo', 'generate_video_with_vertex_veo']