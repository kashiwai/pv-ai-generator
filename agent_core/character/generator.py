import asyncio
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import openai
import base64
from PIL import Image
import io

class CharacterGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.dalle_api_key = config.get("openai_api_key")
        self.midjourney_api_key = config.get("midjourney_api_key")
        self.provider = config.get("image_provider", "dalle")
        
        if self.dalle_api_key:
            openai.api_key = self.dalle_api_key
    
    async def generate_characters(self, keywords: str, mood: str, 
                                 description: str) -> List[Dict[str, Any]]:
        """
        キャラクター画像をAIで生成
        """
        character_refs = []
        
        prompts = self.create_character_prompts(keywords, mood, description)
        
        for i, prompt in enumerate(prompts):
            try:
                # Midjourney を最優先で使用
                if self.midjourney_api_key:
                    print(f"Using Midjourney for character generation (Priority)")
                    image_path = await self.generate_with_midjourney(prompt)
                elif self.provider == "dalle" and self.dalle_api_key:
                    print(f"Using DALL-E 3 for character generation")
                    image_path = await self.generate_with_dalle(prompt)
                else:
                    print(f"No image generation API available, using fallback")
                    image_path = None
                
                if image_path:
                    character_refs.append({
                        "id": f"gen_char_{i}",
                        "original_path": str(image_path),
                        "description": prompt,
                        "consistency_prompt": self.create_consistency_prompt(f"gen_char_{i}")
                    })
                    
            except Exception as e:
                print(f"Character generation error: {e}")
                character_refs.append(self.create_fallback_character(i))
        
        return character_refs
    
    def create_character_prompts(self, keywords: str, mood: str, 
                                description: str) -> List[str]:
        """
        キャラクター生成用のプロンプトを作成（Midjourney最適化）
        """
        base_style = self.get_style_for_mood(mood)
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        prompts = []
        
        # Midjourney v6 に最適化されたプロンプト
        if self.midjourney_api_key:
            main_prompt = f"""
            {base_style} character portrait, {', '.join(keyword_list[:3])}, 
            {description[:100]}, ultra detailed, masterpiece, 
            professional character design, consistent features,
            studio lighting, 8k resolution --v 6 --style raw --ar 1:1
            """
        else:
            # DALL-E 3用のプロンプト
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
    
    async def generate_with_midjourney(self, prompt: str) -> Optional[Path]:
        """
        Midjourney APIで画像を生成
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.midjourney_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "version": "6",
                "aspect_ratio": "1:1",
                "quality": "high"
            }
            
            response = await asyncio.to_thread(
                requests.post,
                "https://api.midjourney.com/v1/imagine",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result.get("image_url")
                
                if image_url:
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