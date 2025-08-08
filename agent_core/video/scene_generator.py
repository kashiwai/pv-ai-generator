import asyncio
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import time

from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
MOVIEPY_AVAILABLE = True

class SceneGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.video_provider = config.get("video_provider", "hailuo")
        self.hailuo_api_key = config.get("hailuo_api_key")
        self.sora_api_key = config.get("sora_api_key")
        self.veo3_api_key = config.get("veo3_api_key")
        self.seedance_api_key = config.get("seedance_api_key")
        self.domoai_api_key = config.get("domoai_api_key")
        self.scene_duration = config.get("scene_duration", 8)
    
    async def generate_scene_prompts(self, script: Dict, character_refs: List[Dict], 
                                    duration: float) -> List[Dict]:
        """
        台本から各シーンの映像生成プロンプトを作成
        """
        scenes = script.get("scenes", [])
        scene_prompts = []
        
        for scene in scenes:
            prompt = self.create_scene_prompt(
                scene,
                character_refs,
                script.get("visual_style", "")
            )
            
            scene_prompts.append({
                "scene_number": scene["scene_number"],
                "timestamp": scene["timestamp"],
                "duration": scene.get("duration", self.scene_duration),
                "prompt": prompt,
                "camera_movement": scene.get("camera_movement", "固定"),
                "transition": scene.get("transition", "カット"),
                "mood": scene.get("mood", "normal")
            })
        
        return scene_prompts
    
    def create_scene_prompt(self, scene: Dict, character_refs: List[Dict], 
                           visual_style: str) -> str:
        """
        単一シーンのプロンプトを作成
        """
        base_prompt = scene.get("visual_description", "")
        
        if character_refs:
            char_tokens = [ref.get("consistency_prompt", "") for ref in character_refs[:2]]
            char_prompt = " ".join(char_tokens)
            base_prompt = f"{char_prompt} {base_prompt}"
        
        key_elements = scene.get("key_elements", [])
        if key_elements:
            elements_prompt = ", ".join(key_elements)
            base_prompt = f"{base_prompt}, featuring {elements_prompt}"
        
        mood = scene.get("mood", "normal")
        mood_prompt = self.get_mood_prompt(mood)
        
        camera = scene.get("camera_movement", "固定")
        camera_prompt = self.get_camera_prompt(camera)
        
        full_prompt = f"""
        {base_prompt}
        Style: {visual_style}
        Mood: {mood_prompt}
        Camera: {camera_prompt}
        High quality, cinematic, 8 seconds duration
        """.strip()
        
        return full_prompt
    
    def get_mood_prompt(self, mood: str) -> str:
        """
        雰囲気に応じたプロンプト追加
        """
        mood_map = {
            "期待感": "anticipatory, hopeful atmosphere",
            "展開": "developing narrative, progressive",
            "高揚": "climactic, intense, emotional peak",
            "余韻": "reflective, peaceful conclusion",
            "normal": "balanced, natural atmosphere"
        }
        return mood_map.get(mood, "balanced atmosphere")
    
    def get_camera_prompt(self, camera_movement: str) -> str:
        """
        カメラワークのプロンプト
        """
        camera_map = {
            "スローズームイン": "slow zoom in",
            "スローズームアウト": "slow zoom out",
            "パン": "panning shot",
            "ティルト": "tilting camera",
            "トラッキング": "tracking shot",
            "固定": "static shot",
            "手持ちカメラ": "handheld camera",
            "ダイナミックズーム": "dynamic zoom",
            "回転": "rotating camera",
            "クレーン": "crane shot"
        }
        return camera_map.get(camera_movement, "static shot")
    
    async def generate_videos(self, scene_prompts: List[Dict], 
                            output_dir: Path) -> List[Dict]:
        """
        プロンプトから実際に映像を生成
        """
        video_clips = []
        
        for prompt_info in scene_prompts:
            try:
                if self.video_provider == "hailuo" and self.hailuo_api_key:
                    video_path = await self.generate_with_hailuo(prompt_info, output_dir)
                elif self.video_provider == "sora" and self.sora_api_key:
                    video_path = await self.generate_with_sora(prompt_info, output_dir)
                elif self.video_provider == "veo3" and self.veo3_api_key:
                    video_path = await self.generate_with_veo3(prompt_info, output_dir)
                elif self.video_provider == "seedance" and self.seedance_api_key:
                    video_path = await self.generate_with_seedance(prompt_info, output_dir)
                elif self.video_provider == "domoai" and self.domoai_api_key:
                    video_path = await self.generate_with_domoai(prompt_info, output_dir)
                else:
                    video_path = await self.generate_placeholder_video(prompt_info, output_dir)
                
                video_clips.append({
                    "scene_number": prompt_info["scene_number"],
                    "file_path": str(video_path),
                    "duration": prompt_info["duration"],
                    "transition": prompt_info["transition"]
                })
                
            except Exception as e:
                print(f"Video generation error for scene {prompt_info['scene_number']}: {e}")
                placeholder = await self.generate_placeholder_video(prompt_info, output_dir)
                video_clips.append({
                    "scene_number": prompt_info["scene_number"],
                    "file_path": str(placeholder),
                    "duration": prompt_info["duration"],
                    "transition": prompt_info["transition"]
                })
        
        return video_clips
    
    async def generate_with_hailuo(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        Hailuo 02 AI APIで映像生成（メイン推奨）
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.hailuo_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt_info["prompt"],
                "duration": prompt_info["duration"],
                "model": "hailuo-02",
                "resolution": "1920x1080",
                "fps": 30,
                "quality": "high",
                "camera_motion": prompt_info.get("camera_movement", "static")
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.hailuo.ai/v2/video/generate",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                if task_id:
                    video_url = await self.wait_for_hailuo_completion(task_id)
                    if video_url:
                        return await self.download_video(video_url, prompt_info["scene_number"], output_dir)
            
            return await self.generate_placeholder_video(prompt_info, output_dir)
            
        except Exception as e:
            print(f"Hailuo generation error: {e}")
            return await self.generate_placeholder_video(prompt_info, output_dir)
    
    async def wait_for_hailuo_completion(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        """
        Hailuo生成タスクの完了を待つ
        """
        headers = {
            "Authorization": f"Bearer {self.hailuo_api_key}"
        }
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    f"https://api.hailuo.ai/v2/video/status/{task_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        return result.get("video_url")
                    elif status == "failed":
                        print(f"Hailuo task failed: {result.get('error')}")
                        return None
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Hailuo status check error: {e}")
                return None
        
        return None
    
    async def generate_with_sora(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        SORA APIで映像生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.sora_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt_info["prompt"],
                "duration": prompt_info["duration"],
                "resolution": "1920x1080",
                "fps": 30
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.openai.com/v1/sora/generate",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("video_url")
                
                if video_url:
                    return await self.download_video(video_url, prompt_info["scene_number"], output_dir)
            
            return await self.generate_placeholder_video(prompt_info, output_dir)
            
        except Exception as e:
            print(f"SORA generation error: {e}")
            return await self.generate_placeholder_video(prompt_info, output_dir)
    
    async def generate_with_veo3(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        VEO3 APIで映像生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.veo3_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt_info["prompt"],
                "duration_seconds": prompt_info["duration"],
                "width": 1920,
                "height": 1080
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.veo3.ai/v1/generate",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("output_url")
                
                if video_url:
                    return await self.download_video(video_url, prompt_info["scene_number"], output_dir)
            
            return await self.generate_placeholder_video(prompt_info, output_dir)
            
        except Exception as e:
            print(f"VEO3 generation error: {e}")
            return await self.generate_placeholder_video(prompt_info, output_dir)
    
    async def generate_with_seedance(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        Seedance APIで映像生成
        """
        try:
            headers = {
                "X-API-Key": self.seedance_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "text_prompt": prompt_info["prompt"],
                "video_length": prompt_info["duration"],
                "video_width": 1920,
                "video_height": 1080,
                "fps": 30
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.seedance.ai/v1/video/generate",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("video_url")
                
                if video_url:
                    return await self.download_video(video_url, prompt_info["scene_number"], output_dir)
            
            return await self.generate_placeholder_video(prompt_info, output_dir)
            
        except Exception as e:
            print(f"Seedance generation error: {e}")
            return await self.generate_placeholder_video(prompt_info, output_dir)
    
    async def generate_with_domoai(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        DomoAI APIで映像生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.domoai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt_info["prompt"],
                "duration": prompt_info["duration"],
                "style": "cinematic",
                "quality": "high"
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.domoai.com/v1/video/create",
                headers=headers,
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                video_url = result.get("video_url")
                
                if video_url:
                    return await self.download_video(video_url, prompt_info["scene_number"], output_dir)
            
            return await self.generate_placeholder_video(prompt_info, output_dir)
            
        except Exception as e:
            print(f"DomoAI generation error: {e}")
            return await self.generate_placeholder_video(prompt_info, output_dir)
    
    async def download_video(self, video_url: str, scene_number: int, output_dir: Path) -> Path:
        """
        URLから映像をダウンロード
        """
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                output_path = output_dir / f"scene_{scene_number:03d}.mp4"
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return output_path
        except Exception as e:
            print(f"Video download error: {e}")
        
        return None
    
    async def generate_placeholder_video(self, prompt_info: Dict, output_dir: Path) -> Path:
        """
        プレースホルダー映像を生成
        """
        output_path = output_dir / f"scene_{prompt_info['scene_number']:03d}.mp4"
        
        if not MOVIEPY_AVAILABLE:
            # FFmpegで直接黒画面動画を作成
            import subprocess
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:s=1920x1080:d={prompt_info["duration"]}',
                '-y',
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True)
            return output_path
        
        output_path = output_dir / f"scene_{prompt_info['scene_number']:03d}.mp4"
        
        background = ColorClip(
            size=(1920, 1080),
            color=(30, 30, 30),
            duration=prompt_info["duration"]
        )
        
        text = TextClip(
            f"Scene {prompt_info['scene_number']}\n{prompt_info['mood']}",
            fontsize=48,
            color='white',
            font='Arial',
            method='caption',
            size=(1920*0.8, None)
        ).set_position('center').set_duration(prompt_info["duration"])
        
        video = CompositeVideoClip([background, text])
        
        video.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast'
        )
        
        background.close()
        text.close()
        video.close()
        
        return output_path