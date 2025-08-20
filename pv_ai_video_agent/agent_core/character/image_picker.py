import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import hashlib
import json

class ImagePicker:
    def __init__(self):
        self.character_dir = Path("assets/characters")
        self.character_dir.mkdir(parents=True, exist_ok=True)
        self.character_registry = self.character_dir / "registry.json"
        self.load_registry()
        
    def load_registry(self):
        """キャラクター登録情報を読み込む"""
        if self.character_registry.exists():
            with open(self.character_registry, 'r', encoding='utf-8') as f:
                self.registry = json.load(f)
        else:
            self.registry = {}
    
    def save_registry(self):
        """キャラクター登録情報を保存"""
        with open(self.character_registry, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    def process_images(self, image_files: List[str]) -> List[Dict[str, Any]]:
        """
        アップロードされた画像を処理し、キャラクター参照情報を返す
        """
        character_refs = []
        
        for image_file in image_files:
            if not Path(image_file).exists():
                continue
            
            character_info = self.register_character(image_file)
            character_refs.append(character_info)
        
        return character_refs
    
    def register_character(self, image_path: str) -> Dict[str, Any]:
        """
        キャラクター画像を登録
        """
        image_path = Path(image_path)
        
        image_hash = self.calculate_image_hash(image_path)
        
        if image_hash in self.registry:
            return self.registry[image_hash]
        
        img = Image.open(image_path)
        
        character_id = f"char_{image_hash[:8]}"
        
        saved_path = self.character_dir / f"{character_id}{image_path.suffix}"
        shutil.copy2(image_path, saved_path)
        
        thumbnail = self.create_thumbnail(img, character_id)
        
        character_info = {
            "id": character_id,
            "original_path": str(saved_path),
            "thumbnail_path": str(thumbnail),
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "hash": image_hash,
            "description": self.generate_character_description(img),
            "consistency_prompt": self.create_consistency_prompt(character_id)
        }
        
        self.registry[image_hash] = character_info
        self.save_registry()
        
        return character_info
    
    def calculate_image_hash(self, image_path: Path) -> str:
        """画像のハッシュ値を計算"""
        with open(image_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def create_thumbnail(self, img: Image.Image, character_id: str) -> Path:
        """サムネイル画像を作成"""
        thumbnail_size = (256, 256)
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        
        thumbnail_path = self.character_dir / f"{character_id}_thumb.jpg"
        thumbnail.save(thumbnail_path, "JPEG", quality=85)
        
        return thumbnail_path
    
    def generate_character_description(self, img: Image.Image) -> str:
        """
        画像から基本的なキャラクター説明を生成
        """
        aspect_ratio = img.width / img.height
        
        if aspect_ratio > 1.2:
            orientation = "横長"
        elif aspect_ratio < 0.8:
            orientation = "縦長"
        else:
            orientation = "正方形に近い"
        
        return f"{orientation}の画像、サイズ: {img.width}x{img.height}"
    
    def create_consistency_prompt(self, character_id: str) -> str:
        """
        キャラクター一貫性のためのプロンプトテンプレートを作成
        """
        return f"{{character_ref:{character_id}}} を使用して、同一キャラクターを維持"
    
    def get_character_by_id(self, character_id: str) -> Optional[Dict[str, Any]]:
        """IDでキャラクター情報を取得"""
        for char_info in self.registry.values():
            if char_info["id"] == character_id:
                return char_info
        return None
    
    def list_all_characters(self) -> List[Dict[str, Any]]:
        """登録されているすべてのキャラクターをリスト"""
        return list(self.registry.values())
    
    def delete_character(self, character_id: str) -> bool:
        """キャラクターを削除"""
        for hash_key, char_info in list(self.registry.items()):
            if char_info["id"] == character_id:
                
                for path_key in ["original_path", "thumbnail_path"]:
                    if path_key in char_info:
                        file_path = Path(char_info[path_key])
                        if file_path.exists():
                            file_path.unlink()
                
                del self.registry[hash_key]
                self.save_registry()
                return True
        
        return False
    
    def export_character_prompt(self, character_id: str) -> Dict[str, Any]:
        """
        映像生成用のキャラクタープロンプトをエクスポート
        """
        char_info = self.get_character_by_id(character_id)
        
        if not char_info:
            return None
        
        return {
            "reference_image": char_info["original_path"],
            "consistency_token": f"{{char:{character_id}}}",
            "description": char_info["description"],
            "dimensions": {
                "width": char_info["width"],
                "height": char_info["height"]
            }
        }
    
    def prepare_for_midjourney(self, character_id: str) -> Optional[str]:
        """
        Midjourney用にキャラクター参照を準備
        """
        char_info = self.get_character_by_id(character_id)
        if not char_info:
            return None
        
        # キャラクター参照用のパスを返す
        return char_info["original_path"]