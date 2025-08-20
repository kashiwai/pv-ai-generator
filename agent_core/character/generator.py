import asyncio
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
import base64
from PIL import Image
import io
import time

class CharacterGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dalle_api_key = config.get("openai_api_key")
        self.midjourney_api_key = config.get("midjourney_api_key")
        self.provider = config.get("image_provider", "dalle")
        
        if self.dalle_api_key:
            openai.api_key = self.dalle_api_key
    
    async def generate_characters(self, keywords: str, mood: str, 
                                 description: str, reference_images: Optional[List[Path]] = None) -> List[Dict[str, Any]]:
        """
        キャラクター画像をAIで生成（一貫性機能付き）
        """
        character_refs = []
        character_ref_url = None
        
        # 参照画像がある場合はアップロード
        if reference_images and len(reference_images) > 0:
            character_ref_url = await self.upload_image_for_reference(reference_images[0])
        
        prompts = self.create_character_prompts(keywords, mood, description)
        
        for i, prompt in enumerate(prompts):
            try:
                if self.provider == "midjourney" and self.midjourney_api_key:
                    # キャラクター参照を含めて生成
                    image_path = await self.generate_with_midjourney(prompt, character_ref_url)
                else:
                    image_path = await self.generate_with_dalle(prompt)
                
                if image_path:
                    character_refs.append({
                        "id": f"gen_char_{i}",
                        "original_path": str(image_path),
                        "description": prompt,
                        "consistency_prompt": self.create_consistency_prompt(f"gen_char_{i}"),
                        "has_consistency": character_ref_url is not None
                    })
                    
            except Exception as e:
                print(f"Character generation error: {e}")
                character_refs.append(self.create_fallback_character(i))
        
        return character_refs
    
    def create_character_prompts(self, keywords: str, mood: str, 
                                description: str) -> List[str]:
        """
        キャラクター生成用のプロンプトを作成
        """
        base_style = self.get_style_for_mood(mood)
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        prompts = []
        
        main_prompt = f"""
        {base_style} style character design,
        {', '.join(keyword_list[:3])},
        {description[:100]},
        high quality, detailed, professional character art,
        consistent character design sheet
        """
        prompts.append(main_prompt.strip())
        
        if len(keyword_list) > 3:
            secondary_prompt = f"""
            {base_style} style supporting character,
            {', '.join(keyword_list[3:])},
            complementary to main character,
            high quality, detailed
            """
            prompts.append(secondary_prompt.strip())
        
        return prompts
    
    def get_style_for_mood(self, mood: str) -> str:
        """
        雰囲気に応じたアートスタイルを取得
        """
        style_map = {
            "明るい": "vibrant anime",
            "感動的": "emotional cinematic",
            "ノスタルジック": "nostalgic watercolor",
            "エネルギッシュ": "dynamic action",
            "ミステリアス": "mysterious dark fantasy",
            "ダーク": "dark gothic",
            "ファンタジー": "fantasy illustration",
            "クール": "cool modern"
        }
        return style_map.get(mood, "anime")
    
    async def generate_with_dalle(self, prompt: str) -> Optional[Path]:
        """
        DALL-E 3で画像を生成
        """
        try:
            response = await asyncio.to_thread(
                openai.Image.create,
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                n=1
            )
            
            image_url = response['data'][0]['url']
            
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                
                output_dir = Path("assets/characters")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                import hashlib
                image_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                output_path = output_dir / f"dalle_char_{image_hash}.png"
                
                with open(output_path, 'wb') as f:
                    f.write(image_response.content)
                
                return output_path
                
        except Exception as e:
            print(f"DALL-E generation error: {e}")
            return None
    
    async def generate_with_midjourney(self, prompt: str, character_ref: Optional[str] = None) -> Optional[Path]:
        """
        PIAPI経由でMidjourneyを使用して画像を生成
        """
        try:
            # PIAPIのエンドポイントとヘッダー設定
            headers = {
                "x-api-key": self.midjourney_api_key,
                "Content-Type": "application/json"
            }
            
            # キャラクター参照を含むプロンプトの構築
            full_prompt = prompt
            if character_ref:
                # キャラクター一貫性のためのパラメータ追加
                if "--cref" not in prompt:
                    full_prompt = f"{prompt} --cref {character_ref} --cw 100"
            
            # アスペクト比とバージョンを追加
            if "--ar" not in full_prompt:
                full_prompt += " --ar 1:1"
            if "--v" not in full_prompt:
                full_prompt += " --v 6.1"
            
            payload = {
                "model": "midjourney",
                "task_type": "imagine",
                "input": {
                    "prompt": full_prompt,
                    "process_mode": "relax",
                    "skip_prompt_check": False
                }
            }
            
            # PIAPIエンドポイントを使用
            response = await asyncio.to_thread(
                requests.post,
                "https://api.piapi.ai/api/v1/task",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = None
                
                # task_idの取得
                if isinstance(result, dict):
                    if 'data' in result and isinstance(result['data'], dict):
                        task_id = result['data'].get('task_id')
                    elif 'task_id' in result:
                        task_id = result['task_id']
                
                if task_id:
                    # タスク完了を待つ
                    image_url = await self.wait_for_midjourney_completion(task_id, headers)
                    
                    if image_url:
                        # 画像をダウンロードして保存
                        image_response = requests.get(image_url)
                        if image_response.status_code == 200:
                            output_dir = Path("assets/characters")
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            import hashlib
                            image_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                            output_path = output_dir / f"mj_char_{image_hash}.png"
                            
                            with open(output_path, 'wb') as f:
                                f.write(image_response.content)
                            
                            return output_path
            
            print(f"Midjourney API response: {response.status_code}")
            return await self.generate_with_dalle(prompt)
            
        except Exception as e:
            print(f"Midjourney generation error: {e}")
            return await self.generate_with_dalle(prompt)
    
    def create_consistency_prompt(self, character_id: str) -> str:
        """
        一貫性保持用のプロンプトテンプレート
        """
        return f"{{character_reference:{character_id}}} maintaining consistent appearance and style"
    
    def create_fallback_character(self, index: int) -> Dict[str, Any]:
        """
        フォールバック用のキャラクター情報
        """
        fallback_path = Path("assets/characters/fallback.png")
        
        if not fallback_path.exists():
            self.create_placeholder_image(fallback_path)
        
        return {
            "id": f"fallback_char_{index}",
            "original_path": str(fallback_path),
            "description": "Default character placeholder",
            "consistency_prompt": "generic character"
        }
    
    def create_placeholder_image(self, output_path: Path):
        """
        プレースホルダー画像を作成
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.new('RGB', (512, 512), color=(128, 128, 128))
        
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        text = "Character\nPlaceholder"
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            font = ImageFont.load_default()
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        position = ((512 - text_width) / 2, (512 - text_height) / 2)
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        img.save(output_path)
    
    async def wait_for_midjourney_completion(self, task_id: str, headers: dict, timeout: int = 300) -> Optional[str]:
        """
        Midjourneyタスクの完了を待つ
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # ステータスチェック
                response = requests.get(
                    f"https://api.piapi.ai/api/v1/task/{task_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "processing").lower()
                    
                    if status == "completed":
                        output = result.get("output", {})
                        return output.get("image_url")
                    elif status == "failed" or status == "error":
                        print(f"Midjourney task failed: {result.get('message')}")
                        return None
                
                await asyncio.sleep(5)  # 5秒待機
                
            except Exception as e:
                print(f"Status check error: {e}")
                return None
        
        print("Midjourney task timeout")
        return None
    
    async def generate_character_with_consistency(self, base_prompt: str, reference_image_path: Optional[Path] = None) -> Optional[Path]:
        """
        キャラクター一貫性を保持して画像を生成
        """
        character_ref = None
        
        if reference_image_path and reference_image_path.exists():
            # 参照画像をアップロードしてURLを取得
            character_ref = await self.upload_image_for_reference(reference_image_path)
        
        # Midjourneyで生成
        if self.provider == "midjourney" and self.midjourney_api_key:
            return await self.generate_with_midjourney(base_prompt, character_ref)
        else:
            return await self.generate_with_dalle(base_prompt)
    
    async def upload_image_for_reference(self, image_path: Path) -> Optional[str]:
        """
        参照画像をアップロードしてURLを取得
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Base64エンコード
            import base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "x-api-key": self.midjourney_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "image": f"data:image/png;base64,{base64_image}",
                "purpose": "character_reference"
            }
            
            response = requests.post(
                "https://api.piapi.ai/upload/image",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("url")
            
        except Exception as e:
            print(f"Image upload error: {e}")
        
        return None
    
    async def enhance_character(self, image_path: Path, enhancement_type: str) -> Path:
        """
        キャラクター画像をエンハンス
        """
        img = Image.open(image_path)
        
        if enhancement_type == "upscale":
            new_size = (img.width * 2, img.height * 2)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        elif enhancement_type == "stylize":
            from PIL import ImageFilter
            img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            
        elif enhancement_type == "clean":
            from PIL import ImageFilter
            img = img.filter(ImageFilter.SMOOTH_MORE)
        
        output_path = image_path.parent / f"{image_path.stem}_enhanced{image_path.suffix}"
        img.save(output_path)
        
        return output_path