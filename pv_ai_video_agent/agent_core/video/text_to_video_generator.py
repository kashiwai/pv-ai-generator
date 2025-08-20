"""
Text-to-Video生成モジュール
Veo3、Seedance等のText-to-Video AIとの統合
キャラクター一貫性機能付き
"""

import asyncio
import json
import requests
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import time
from PIL import Image
import io

class TextToVideoGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.veo3_api_key = config.get("veo3_api_key")
        self.seedance_api_key = config.get("seedance_api_key")
        self.piapi_key = config.get("piapi_key") or config.get("hailuo_api_key")
        
        # デフォルトプロバイダー
        self.default_provider = config.get("text_to_video_provider", "veo3")
        
        # キャラクター一貫性設定
        self.character_consistency_enabled = True
        self.character_references = {}
    
    async def generate_video_from_script(self, 
                                        detailed_script: Dict,
                                        character_reference: Optional[Dict] = None,
                                        output_dir: Path = None) -> List[Dict]:
        """
        詳細スクリプトから動画を生成
        
        Args:
            detailed_script: 詳細な台本（2000-3000文字/シーン）
            character_reference: キャラクター参照情報
            output_dir: 出力ディレクトリ
        
        Returns:
            生成された動画情報のリスト
        """
        if output_dir is None:
            output_dir = Path("assets/output/videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # キャラクター参照を準備
        if character_reference:
            await self.prepare_character_reference(character_reference)
        
        generated_videos = []
        scenes = detailed_script.get("scenes", [])
        
        for scene in scenes:
            video_info = await self.generate_scene_video(
                scene=scene,
                scene_number=scene.get("scene_number", 1),
                total_scenes=len(scenes),
                output_dir=output_dir
            )
            
            if video_info:
                generated_videos.append(video_info)
        
        return generated_videos
    
    async def prepare_character_reference(self, character_ref: Dict) -> None:
        """
        キャラクター参照を準備（一貫性のため）
        
        Args:
            character_ref: キャラクター参照情報
        """
        # Veo3用のキャラクター参照準備
        if self.veo3_api_key:
            veo3_ref = await self.prepare_veo3_character_reference(character_ref)
            self.character_references["veo3"] = veo3_ref
        
        # Seedance用のキャラクター参照準備
        if self.seedance_api_key:
            seedance_ref = await self.prepare_seedance_character_reference(character_ref)
            self.character_references["seedance"] = seedance_ref
    
    async def prepare_veo3_character_reference(self, character_ref: Dict) -> Dict:
        """
        Veo3用のキャラクター参照を準備
        
        Veo3のキャラクター一貫性機能:
        1. Reference Image Upload - 参照画像のアップロード
        2. Character ID Generation - キャラクターIDの生成
        3. Consistency Token - 一貫性トークンの使用
        """
        reference_data = {
            "method": "character_embedding",
            "character_id": None,
            "embedding_vector": None,
            "reference_images": [],
            "description": character_ref.get("description", ""),
            "consistency_settings": {
                "strength": 0.9,  # 0.0-1.0 (1.0 = 最大一貫性)
                "detail_preservation": "high",
                "facial_lock": True,
                "body_lock": True,
                "clothing_lock": False  # 服装は変更可能
            }
        }
        
        # 参照画像がある場合
        if character_ref.get("image_path"):
            image_path = Path(character_ref["image_path"])
            if image_path.exists():
                # Veo3 APIに画像をアップロード
                character_id = await self.upload_to_veo3(image_path)
                reference_data["character_id"] = character_id
                reference_data["reference_images"].append(str(image_path))
                
                # エンベディングベクトルを生成
                embedding = await self.generate_veo3_embedding(character_id)
                reference_data["embedding_vector"] = embedding
        
        # プロンプトテンプレートを作成
        reference_data["prompt_template"] = self.create_veo3_consistency_prompt(
            character_ref.get("description", ""),
            reference_data["character_id"]
        )
        
        return reference_data
    
    async def upload_to_veo3(self, image_path: Path) -> str:
        """
        Veo3に画像をアップロードしてキャラクターIDを取得
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Base64エンコード
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.veo3_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "image": f"data:image/png;base64,{base64_image}",
                "type": "character_reference",
                "settings": {
                    "extract_features": True,
                    "generate_embedding": True,
                    "preserve_identity": True
                }
            }
            
            # Veo3 Character Upload API
            response = requests.post(
                "https://api.veo3.ai/v1/character/upload",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("character_id")
            else:
                print(f"Veo3 upload error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Veo3 upload exception: {e}")
            return None
    
    async def generate_veo3_embedding(self, character_id: str) -> List[float]:
        """
        Veo3でキャラクターエンベディングを生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.veo3_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "character_id": character_id,
                "embedding_type": "facial_identity",
                "dimension": 512
            }
            
            response = requests.post(
                "https://api.veo3.ai/v1/character/embedding",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])
            
        except Exception as e:
            print(f"Veo3 embedding error: {e}")
        
        return []
    
    def create_veo3_consistency_prompt(self, description: str, character_id: str) -> str:
        """
        Veo3用の一貫性プロンプトテンプレート作成
        """
        if character_id:
            return f"""
            [CHARACTER_REF:{character_id}]
            [CONSISTENCY:MAX]
            [IDENTITY_LOCK:TRUE]
            
            {description}
            
            Technical requirements:
            - Maintain exact facial features from reference
            - Keep consistent body proportions
            - Allow natural movement and expressions
            - Preserve identity across all frames
            """
        else:
            return f"""
            {description}
            
            Character consistency notes:
            - Use same character throughout
            - Maintain consistent appearance
            - Keep facial features stable
            """
    
    async def prepare_seedance_character_reference(self, character_ref: Dict) -> Dict:
        """
        Seedance用のキャラクター参照を準備
        
        Seedanceのキャラクター一貫性機能:
        1. Face Swap Technology - 顔交換技術
        2. Motion Capture Reference - モーションキャプチャ参照
        3. Style Transfer - スタイル転送
        """
        reference_data = {
            "method": "face_swap_plus_style",
            "face_id": None,
            "style_reference": None,
            "motion_reference": None,
            "consistency_settings": {
                "face_swap_strength": 0.95,  # 顔の一致度
                "style_consistency": 0.8,     # スタイルの一貫性
                "motion_smoothness": 0.9,     # 動きの滑らかさ
                "temporal_coherence": True,   # 時間的一貫性
                "identity_preservation": {
                    "facial_features": True,
                    "body_shape": True,
                    "skin_tone": True,
                    "hair_style": True,
                    "clothing_style": False
                }
            }
        }
        
        # 参照画像がある場合
        if character_ref.get("image_path"):
            image_path = Path(character_ref["image_path"])
            if image_path.exists():
                # Seedance APIに画像をアップロード
                face_id = await self.upload_to_seedance(image_path)
                reference_data["face_id"] = face_id
                
                # スタイル参照を生成
                style_ref = await self.generate_seedance_style_reference(face_id)
                reference_data["style_reference"] = style_ref
        
        # Seedance特有のプロンプト構造
        reference_data["prompt_structure"] = self.create_seedance_consistency_prompt(
            character_ref.get("description", ""),
            reference_data["face_id"]
        )
        
        return reference_data
    
    async def upload_to_seedance(self, image_path: Path) -> str:
        """
        Seedanceに画像をアップロードして顔IDを取得
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Seedanceは直接ファイルアップロードをサポート
            files = {
                'image': ('character.png', image_data, 'image/png')
            }
            
            headers = {
                "Authorization": f"Bearer {self.seedance_api_key}"
            }
            
            data = {
                "type": "face_reference",
                "extract_features": "true",
                "generate_face_id": "true"
            }
            
            # Seedance Face Upload API
            response = requests.post(
                "https://api.seedance.ai/v1/face/upload",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("face_id")
            else:
                print(f"Seedance upload error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Seedance upload exception: {e}")
            return None
    
    async def generate_seedance_style_reference(self, face_id: str) -> Dict:
        """
        Seedanceでスタイル参照を生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.seedance_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "face_id": face_id,
                "generate_style": True,
                "style_parameters": {
                    "preserve_identity": True,
                    "enhance_features": False,
                    "artistic_style": "realistic"
                }
            }
            
            response = requests.post(
                "https://api.seedance.ai/v1/style/generate",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            print(f"Seedance style generation error: {e}")
        
        return {}
    
    def create_seedance_consistency_prompt(self, description: str, face_id: str) -> str:
        """
        Seedance用の一貫性プロンプト構造作成
        """
        if face_id:
            return {
                "main_prompt": description,
                "face_reference": face_id,
                "consistency_instructions": [
                    "FACE_SWAP_MODE:ENABLED",
                    "IDENTITY_PRESERVATION:MAX",
                    "TEMPORAL_COHERENCE:HIGH",
                    "MOTION_SMOOTHING:ENABLED"
                ],
                "technical_params": {
                    "face_swap_strength": 0.95,
                    "identity_threshold": 0.9,
                    "temporal_window": 5,
                    "motion_interpolation": "cubic"
                }
            }
        else:
            return {
                "main_prompt": description,
                "consistency_instructions": [
                    "USE_SAME_CHARACTER:TRUE",
                    "MAINTAIN_APPEARANCE:HIGH"
                ]
            }
    
    async def generate_scene_video(self, scene: Dict, scene_number: int,
                                  total_scenes: int, output_dir: Path) -> Optional[Dict]:
        """
        単一シーンの動画を生成
        """
        # プロバイダーを選択
        provider = self.select_provider_for_scene(scene, scene_number)
        
        # プロンプトを準備
        video_prompt = self.prepare_video_prompt(scene, provider)
        
        # 動画生成
        if provider == "veo3" and self.veo3_api_key:
            result = await self.generate_with_veo3(video_prompt, scene, output_dir)
        elif provider == "seedance" and self.seedance_api_key:
            result = await self.generate_with_seedance(video_prompt, scene, output_dir)
        elif self.piapi_key:
            result = await self.generate_with_hailuo(video_prompt, scene, output_dir)
        else:
            result = self.generate_placeholder_video(scene, output_dir)
        
        return result
    
    def select_provider_for_scene(self, scene: Dict, scene_number: int) -> str:
        """
        シーンに最適なプロバイダーを選択
        """
        # シーンの特性に基づいて選択
        scene_role = scene.get("role", "normal")
        
        # 重要なシーンにはVeo3を優先
        if scene_role in ["climax", "opening", "ending"] and self.veo3_api_key:
            return "veo3"
        
        # アクションシーンにはSeedanceを優先
        if scene_role in ["action", "dynamic"] and self.seedance_api_key:
            return "seedance"
        
        # デフォルトプロバイダー
        if self.default_provider == "veo3" and self.veo3_api_key:
            return "veo3"
        elif self.default_provider == "seedance" and self.seedance_api_key:
            return "seedance"
        elif self.piapi_key:
            return "hailuo"
        
        return "placeholder"
    
    def prepare_video_prompt(self, scene: Dict, provider: str) -> str:
        """
        プロバイダーに応じたプロンプトを準備
        """
        base_description = scene.get("detailed_description", "")
        video_prompt = scene.get("video_prompt", "")
        
        # キャラクター参照を含める
        if provider in self.character_references:
            char_ref = self.character_references[provider]
            
            if provider == "veo3":
                # Veo3形式
                if char_ref.get("character_id"):
                    video_prompt = f"[CHARACTER_REF:{char_ref['character_id']}]\n{video_prompt}"
            
            elif provider == "seedance":
                # Seedance形式
                if char_ref.get("face_id"):
                    video_prompt = {
                        "prompt": video_prompt,
                        "face_id": char_ref["face_id"],
                        "style_reference": char_ref.get("style_reference", {})
                    }
        
        return video_prompt
    
    async def generate_with_veo3(self, prompt: str, scene: Dict, 
                                output_dir: Path) -> Optional[Dict]:
        """
        Veo3で動画生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.veo3_api_key}",
                "Content-Type": "application/json"
            }
            
            # キャラクター参照を含むペイロード
            payload = {
                "prompt": prompt,
                "duration": scene.get("duration", 8),
                "resolution": "1920x1080",
                "fps": 30,
                "style": "cinematic",
                "quality": "high"
            }
            
            # キャラクター一貫性設定を追加
            if "veo3" in self.character_references:
                char_ref = self.character_references["veo3"]
                if char_ref.get("character_id"):
                    payload["character_reference"] = {
                        "character_id": char_ref["character_id"],
                        "embedding_vector": char_ref.get("embedding_vector", []),
                        "consistency_strength": 0.9
                    }
            
            # 技術パラメータを追加
            tech_params = scene.get("technical_parameters", {})
            payload["camera"] = tech_params.get("camera_instructions", {})
            payload["lighting"] = tech_params.get("lighting", {})
            payload["effects"] = tech_params.get("effects", [])
            
            # Veo3 Video Generation API
            response = requests.post(
                "https://api.veo3.ai/v1/video/generate",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                # 生成完了を待つ
                video_url = await self.wait_for_veo3_completion(task_id)
                
                if video_url:
                    # 動画をダウンロード
                    video_path = await self.download_video(
                        video_url, 
                        output_dir / f"scene_{scene['scene_number']}_veo3.mp4"
                    )
                    
                    return {
                        "scene_number": scene["scene_number"],
                        "provider": "veo3",
                        "video_path": str(video_path),
                        "duration": scene.get("duration", 8),
                        "timestamp": scene.get("timestamp", ""),
                        "character_consistent": True
                    }
            
        except Exception as e:
            print(f"Veo3 generation error: {e}")
        
        return None
    
    async def wait_for_veo3_completion(self, task_id: str, timeout: int = 300) -> Optional[str]:
        """
        Veo3タスクの完了を待つ
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                headers = {
                    "Authorization": f"Bearer {self.veo3_api_key}"
                }
                
                response = requests.get(
                    f"https://api.veo3.ai/v1/video/status/{task_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        return result.get("video_url")
                    elif status == "failed":
                        print(f"Veo3 task failed: {result.get('error')}")
                        return None
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Veo3 status check error: {e}")
        
        return None
    
    async def generate_with_seedance(self, prompt: Any, scene: Dict,
                                    output_dir: Path) -> Optional[Dict]:
        """
        Seedanceで動画生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.seedance_api_key}",
                "Content-Type": "application/json"
            }
            
            # プロンプトの処理
            if isinstance(prompt, dict):
                # Seedance形式のプロンプト
                payload = {
                    "prompt": prompt.get("prompt", ""),
                    "face_id": prompt.get("face_id"),
                    "style_reference": prompt.get("style_reference", {}),
                    "duration": scene.get("duration", 8),
                    "resolution": "1920x1080",
                    "fps": 30
                }
            else:
                payload = {
                    "prompt": prompt,
                    "duration": scene.get("duration", 8),
                    "resolution": "1920x1080",
                    "fps": 30
                }
            
            # キャラクター一貫性設定
            if "seedance" in self.character_references:
                char_ref = self.character_references["seedance"]
                if char_ref.get("face_id"):
                    payload["face_swap"] = {
                        "enabled": True,
                        "face_id": char_ref["face_id"],
                        "strength": 0.95,
                        "preserve_expressions": True
                    }
                    payload["consistency"] = char_ref.get("consistency_settings", {})
            
            # 技術パラメータ
            payload["motion"] = {
                "smoothness": 0.9,
                "natural_movement": True,
                "physics_based": True
            }
            
            # Seedance Video Generation API
            response = requests.post(
                "https://api.seedance.ai/v1/video/generate",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get("job_id")
                
                # 生成完了を待つ
                video_url = await self.wait_for_seedance_completion(job_id)
                
                if video_url:
                    # 動画をダウンロード
                    video_path = await self.download_video(
                        video_url,
                        output_dir / f"scene_{scene['scene_number']}_seedance.mp4"
                    )
                    
                    return {
                        "scene_number": scene["scene_number"],
                        "provider": "seedance",
                        "video_path": str(video_path),
                        "duration": scene.get("duration", 8),
                        "timestamp": scene.get("timestamp", ""),
                        "character_consistent": True
                    }
            
        except Exception as e:
            print(f"Seedance generation error: {e}")
        
        return None
    
    async def wait_for_seedance_completion(self, job_id: str, timeout: int = 300) -> Optional[str]:
        """
        Seedanceタスクの完了を待つ
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                headers = {
                    "Authorization": f"Bearer {self.seedance_api_key}"
                }
                
                response = requests.get(
                    f"https://api.seedance.ai/v1/video/status/{job_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        return result.get("video_url")
                    elif status == "failed":
                        print(f"Seedance task failed: {result.get('message')}")
                        return None
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Seedance status check error: {e}")
        
        return None
    
    async def generate_with_hailuo(self, prompt: str, scene: Dict,
                                  output_dir: Path) -> Optional[Dict]:
        """
        Hailuo AI（PIAPI経由）で動画生成（フォールバック）
        """
        try:
            headers = {
                "x-api-key": self.piapi_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "hailuo-02",
                "task_type": "text_to_video",
                "input": {
                    "prompt": prompt,
                    "duration": scene.get("duration", 8),
                    "quality": "high",
                    "enable_motion_control": True
                }
            }
            
            response = requests.post(
                "https://api.piapi.ai/api/v1/task",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("data", {}).get("task_id")
                
                # 完了を待つ
                video_url = await self.wait_for_hailuo_completion(task_id)
                
                if video_url:
                    video_path = await self.download_video(
                        video_url,
                        output_dir / f"scene_{scene['scene_number']}_hailuo.mp4"
                    )
                    
                    return {
                        "scene_number": scene["scene_number"],
                        "provider": "hailuo",
                        "video_path": str(video_path),
                        "duration": scene.get("duration", 8),
                        "timestamp": scene.get("timestamp", ""),
                        "character_consistent": False  # Hailuoは参照画像なし
                    }
            
        except Exception as e:
            print(f"Hailuo generation error: {e}")
        
        return None
    
    async def wait_for_hailuo_completion(self, task_id: str, timeout: int = 300) -> Optional[str]:
        """
        Hailuoタスクの完了を待つ
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                headers = {
                    "x-api-key": self.piapi_key
                }
                
                response = requests.get(
                    f"https://api.piapi.ai/api/v1/task/{task_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "").lower()
                    
                    if status == "completed":
                        output = result.get("output", {})
                        return output.get("video_url")
                    elif status in ["failed", "error"]:
                        return None
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Hailuo status check error: {e}")
        
        return None
    
    def generate_placeholder_video(self, scene: Dict, output_dir: Path) -> Dict:
        """
        プレースホルダー動画を生成
        """
        video_path = output_dir / f"scene_{scene['scene_number']}_placeholder.mp4"
        
        # 実際の実装では、MoviePyで簡単な動画を生成
        # ここでは仮のパスを返す
        
        return {
            "scene_number": scene["scene_number"],
            "provider": "placeholder",
            "video_path": str(video_path),
            "duration": scene.get("duration", 8),
            "timestamp": scene.get("timestamp", ""),
            "character_consistent": False
        }
    
    async def download_video(self, video_url: str, output_path: Path) -> Path:
        """
        動画をダウンロード
        """
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return output_path
            
        except Exception as e:
            print(f"Video download error: {e}")
            return output_path  # エラーでもパスを返す
    
    def get_character_consistency_tips(self, provider: str) -> Dict[str, Any]:
        """
        プロバイダー別のキャラクター一貫性のヒントを取得
        """
        tips = {
            "veo3": {
                "method": "Character Embedding",
                "requirements": [
                    "高解像度の正面顔写真（1024x1024以上）",
                    "良好な照明条件",
                    "中立的な表情",
                    "複数角度の写真があればより良い"
                ],
                "best_practices": [
                    "CHARACTER_REF タグを全プロンプトに含める",
                    "一貫性強度を0.8-0.95に設定",
                    "顔のロックを有効化",
                    "時間的一貫性を最大に設定"
                ],
                "limitations": [
                    "極端な角度変化では精度が低下",
                    "照明条件の大きな変化に弱い",
                    "衣装の変更は可能だが顔は固定"
                ]
            },
            "seedance": {
                "method": "Face Swap + Style Transfer",
                "requirements": [
                    "クリアな顔写真（512x512以上）",
                    "正面または3/4角度",
                    "髪型が明確に見える",
                    "全身写真があるとなお良い"
                ],
                "best_practices": [
                    "Face IDを全シーンで使用",
                    "スワップ強度を0.9以上に設定",
                    "表情の保持を有効化",
                    "モーションスムージングを使用"
                ],
                "limitations": [
                    "極端な表情変化で不自然になる可能性",
                    "髪型の大きな変更は困難",
                    "メガネなどのアクセサリーに注意"
                ]
            },
            "general": {
                "tips": [
                    "同じ服装の指定をプロンプトに含める",
                    "特徴的な要素（髪色、目の色等）を明記",
                    "「same person」「consistent character」を追加",
                    "シーン間で大きな時間経過を避ける"
                ]
            }
        }
        
        return tips.get(provider, tips["general"])