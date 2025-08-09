"""
PIAPI統合モジュール
Hailuo, Midjourney等のAIサービスをPIAPI経由で利用
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO

class PIAPIClient:
    """PIAPI統合クライアント"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.piapi.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_image_midjourney(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Midjourney経由で画像生成
        
        Args:
            prompt: 画像生成プロンプト
            kwargs: 追加パラメータ（aspect_ratio, style, version等）
        
        Returns:
            生成結果
        """
        endpoint = f"{self.base_url}/midjourney/imagine"
        
        payload = {
            "prompt": prompt,
            "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
            "version": kwargs.get("version", "6"),
            "style": kwargs.get("style", "raw"),
            "quality": kwargs.get("quality", 2),
            "stylize": kwargs.get("stylize", 100),
            "chaos": kwargs.get("chaos", 0)
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            # ジョブIDを返して、後でステータスを確認
            return {
                "status": "success",
                "job_id": result.get("job_id"),
                "message": "画像生成を開始しました"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_video_hailuo(self, image_url: str, prompt: str, duration: int = 5) -> Dict[str, Any]:
        """
        Hailuo AI経由で動画生成
        
        Args:
            image_url: 元画像のURL
            prompt: 動画生成プロンプト
            duration: 動画の長さ（秒）
        
        Returns:
            生成結果
        """
        endpoint = f"{self.base_url}/hailuo/generate"
        
        payload = {
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
            "motion_intensity": 5,  # 1-10のスケール
            "camera_movement": "auto"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "job_id": result.get("job_id"),
                "message": "動画生成を開始しました"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def check_job_status(self, job_id: str, service: str = "midjourney") -> Dict[str, Any]:
        """
        ジョブのステータスを確認
        
        Args:
            job_id: ジョブID
            service: サービス名（midjourney, hailuo等）
        
        Returns:
            ステータス情報
        """
        endpoint = f"{self.base_url}/{service}/status/{job_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": result.get("status", "processing"),
                "progress": result.get("progress", 0),
                "result_url": result.get("result_url"),
                "message": result.get("message", "処理中...")
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_character_consistent_images(self, character_photos: List, scenes: List[Dict]) -> List[Dict]:
        """
        キャラクター一貫性のある画像を生成
        
        Args:
            character_photos: キャラクター写真リスト
            scenes: シーン情報リスト
        
        Returns:
            生成された画像情報リスト
        """
        generated_images = []
        
        # キャラクター写真をbase64エンコード
        character_refs = []
        for photo in character_photos[:3]:  # 最大3枚まで参照
            photo_bytes = photo.read()
            photo.seek(0)
            base64_image = base64.b64encode(photo_bytes).decode('utf-8')
            character_refs.append(f"data:image/jpeg;base64,{base64_image}")
        
        for scene in scenes:
            # キャラクター参照を含むプロンプト生成
            enhanced_prompt = f"{scene['visual_prompt']} --cref {' '.join(character_refs[:1])} --cw 100"
            
            result = self.generate_image_midjourney(enhanced_prompt)
            generated_images.append({
                "scene_id": scene['id'],
                "job_id": result.get("job_id"),
                "status": "generating",
                "prompt": enhanced_prompt
            })
        
        return generated_images
    
    def create_pv_from_images(self, images: List[Dict], music_info: Dict) -> Dict[str, Any]:
        """
        画像から完全なPVを作成
        
        Args:
            images: 生成された画像リスト
            music_info: 音楽情報
        
        Returns:
            PV生成結果
        """
        video_segments = []
        
        # 各画像から動画セグメントを生成
        for image in images:
            if image.get("result_url"):
                video_result = self.generate_video_hailuo(
                    image_url=image["result_url"],
                    prompt=f"Smooth camera movement, {image.get('prompt', '')}",
                    duration=image.get("duration", 5)
                )
                video_segments.append(video_result)
        
        # 動画セグメントを結合（PIAPIの動画結合エンドポイントを使用）
        endpoint = f"{self.base_url}/video/merge"
        
        payload = {
            "segments": [seg["job_id"] for seg in video_segments if seg.get("job_id")],
            "music_url": music_info.get("url"),
            "duration": music_info.get("duration"),
            "transitions": "smooth",
            "output_format": "mp4",
            "resolution": "1920x1080"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "job_id": result.get("job_id"),
                "message": "PV生成を開始しました"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


def generate_images_with_piapi(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    PIAPIを使用して台本から画像を生成
    
    Args:
        script: 確定した台本
        character_photos: キャラクター写真（オプション）
    
    Returns:
        生成された画像情報リスト
    """
    # APIキーを取得
    piapi_key = st.session_state.api_keys.get('piapi', '')
    if not piapi_key:
        st.error("PIAPIキーが設定されていません")
        return []
    
    client = PIAPIClient(piapi_key)
    generated_images = []
    
    # プログレスバー表示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    scenes = script.get('scenes', [])
    total_scenes = len(scenes)
    
    if character_photos:
        # キャラクター一貫性のある画像生成
        status_text.text("キャラクター参照画像を処理中...")
        generated_images = client.generate_character_consistent_images(character_photos, scenes)
    else:
        # 通常の画像生成
        for i, scene in enumerate(scenes):
            status_text.text(f"シーン {scene['id']} を生成中... ({i+1}/{total_scenes})")
            progress_bar.progress((i + 1) / total_scenes)
            
            result = client.generate_image_midjourney(scene['visual_prompt'])
            
            generated_images.append({
                "scene_id": scene['id'],
                "job_id": result.get("job_id"),
                "status": "generating",
                "prompt": scene['visual_prompt'],
                "time": scene['time'],
                "duration": scene.get('duration', 5)
            })
            
            time.sleep(0.5)  # API制限対策
    
    # ジョブの完了を待つ
    status_text.text("画像生成の完了を待っています...")
    completed_images = wait_for_image_completion(client, generated_images)
    
    progress_bar.progress(1.0)
    status_text.success(f"✅ {len(completed_images)}枚の画像生成が完了しました")
    
    return completed_images


def wait_for_image_completion(client: PIAPIClient, images: List[Dict], timeout: int = 300) -> List[Dict]:
    """
    画像生成の完了を待つ
    
    Args:
        client: PIAPIクライアント
        images: 生成中の画像リスト
        timeout: タイムアウト（秒）
    
    Returns:
        完成した画像リスト
    """
    start_time = time.time()
    completed_images = []
    
    while time.time() - start_time < timeout:
        all_completed = True
        
        for image in images:
            if image.get("status") != "completed":
                # ステータスチェック
                status = client.check_job_status(image["job_id"], "midjourney")
                
                if status["status"] == "completed":
                    image["status"] = "completed"
                    image["result_url"] = status.get("result_url")
                    completed_images.append(image)
                elif status["status"] == "error":
                    image["status"] = "error"
                    image["error_message"] = status.get("message")
                else:
                    all_completed = False
        
        if all_completed:
            break
        
        time.sleep(5)  # 5秒ごとにチェック
    
    return completed_images


def create_pv_with_piapi(images: List[Dict], music_info: Dict, settings: Dict) -> Dict[str, Any]:
    """
    PIAPIを使用してPVを作成
    
    Args:
        images: 生成された画像リスト
        music_info: 音楽情報
        settings: 生成設定
    
    Returns:
        PV生成結果
    """
    piapi_key = st.session_state.api_keys.get('piapi', '')
    if not piapi_key:
        st.error("PIAPIキーが設定されていません")
        return {"status": "error", "message": "APIキー未設定"}
    
    client = PIAPIClient(piapi_key)
    
    # PV作成開始
    with st.spinner("PVを生成中..."):
        result = client.create_pv_from_images(images, music_info)
    
    if result["status"] == "success":
        # 完了を待つ
        job_id = result["job_id"]
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        while True:
            status = client.check_job_status(job_id, "video")
            
            if status["status"] == "completed":
                progress_bar.progress(1.0)
                status_placeholder.success("✅ PV生成完了！")
                return {
                    "status": "success",
                    "video_url": status.get("result_url"),
                    "job_id": job_id
                }
            elif status["status"] == "error":
                status_placeholder.error(f"❌ エラー: {status.get('message')}")
                return {
                    "status": "error",
                    "message": status.get("message")
                }
            else:
                progress = status.get("progress", 0) / 100
                progress_bar.progress(progress)
                status_placeholder.info(f"処理中... {status.get('message', '')}")
            
            time.sleep(5)
    
    return result