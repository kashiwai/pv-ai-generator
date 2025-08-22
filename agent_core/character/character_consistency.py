"""
キャラクター一貫性システム
1枚の写真から全編通して同じキャラクターを維持
"""

import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image
import io
import hashlib

class CharacterConsistencySystem:
    """キャラクター一貫性を保つためのシステム"""
    
    def __init__(self):
        self.character_profiles = {}
        self.face_embeddings = {}
        self.character_prompts = {}
    
    def register_character(self, 
                          image_path: str,
                          character_name: str = "主人公",
                          age: Optional[int] = None,
                          description: Optional[str] = None) -> Dict[str, Any]:
        """
        キャラクターを登録
        
        Args:
            image_path: キャラクター画像のパス
            character_name: キャラクター名
            age: 年齢（オプション）
            description: 説明（オプション）
        
        Returns:
            キャラクタープロファイル
        """
        # 画像からIDを生成
        character_id = self._generate_character_id(image_path)
        
        # 画像を解析
        character_features = self._analyze_character_image(image_path)
        
        # プロファイルを作成
        profile = {
            "id": character_id,
            "name": character_name,
            "age": age or "推定20代",
            "description": description or self._generate_description(character_features),
            "image_path": image_path,
            "features": character_features,
            "reference_url": None  # Midjourney/SD用のリファレンスURL
        }
        
        # 保存
        self.character_profiles[character_id] = profile
        
        # プロンプトテンプレートを生成
        self.character_prompts[character_id] = self._create_character_prompts(profile)
        
        return profile
    
    def _generate_character_id(self, image_path: str) -> str:
        """画像からユニークIDを生成"""
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()[:8]
        return f"char_{image_hash}"
    
    def _analyze_character_image(self, image_path: str) -> Dict[str, Any]:
        """
        画像からキャラクターの特徴を抽出
        
        Returns:
            特徴辞書
        """
        # 画像を読み込み
        img = Image.open(image_path)
        
        # 基本的な画像情報
        features = {
            "image_size": img.size,
            "image_format": img.format,
        }
        
        # AIによる特徴抽出（ここでは仮の実装）
        # 実際にはCLIP、Face Recognition等を使用
        features.update({
            "hair_color": "黒髪",  # 仮の値
            "hair_style": "ロングヘア",
            "eye_color": "茶色",
            "face_shape": "卵型",
            "clothing_style": "カジュアル",
            "accessories": [],
            "expression": "笑顔",
            "pose": "正面向き"
        })
        
        return features
    
    def _generate_description(self, features: Dict[str, Any]) -> str:
        """特徴から説明文を生成"""
        desc_parts = []
        
        if features.get("hair_color") and features.get("hair_style"):
            desc_parts.append(f"{features['hair_color']}の{features['hair_style']}")
        
        if features.get("eye_color"):
            desc_parts.append(f"{features['eye_color']}の瞳")
        
        if features.get("clothing_style"):
            desc_parts.append(f"{features['clothing_style']}な服装")
        
        if features.get("expression"):
            desc_parts.append(f"{features['expression']}")
        
        return "、".join(desc_parts) + "の女性"
    
    def _create_character_prompts(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """
        各AIサービス用のプロンプトテンプレートを作成
        
        Returns:
            プロンプト辞書
        """
        base_description = profile['description']
        features = profile['features']
        
        prompts = {
            "midjourney": f"beautiful young woman, {features.get('hair_color', 'black')} {features.get('hair_style', 'hair')}, {features.get('eye_color', 'brown')} eyes, {features.get('expression', 'smiling')}, consistent character, same person throughout --cref [CHARACTER_REF] --cw 100",
            
            "stable_diffusion": f"(masterpiece, best quality), 1girl, {features.get('hair_color', 'black')} hair, {features.get('hair_style', 'long hair')}, {features.get('eye_color', 'brown')} eyes, {features.get('expression', 'smile')}, consistent facial features, same character",
            
            "dalle": f"A {profile.get('age', 'young')} woman with {features.get('hair_color', 'black')} {features.get('hair_style', 'hair')}, {features.get('eye_color', 'brown')} eyes, {features.get('expression', 'smiling expression')}, photorealistic, consistent appearance",
            
            "video": f"A {profile.get('age', 'young')} woman, {base_description}, natural movement, consistent appearance throughout the video"
        }
        
        return prompts
    
    def get_scene_prompt(self, 
                        character_id: str,
                        scene_description: str,
                        service: str = "midjourney") -> str:
        """
        シーン用のプロンプトを生成
        
        Args:
            character_id: キャラクターID
            scene_description: シーンの説明
            service: 使用するサービス
        
        Returns:
            完成したプロンプト
        """
        if character_id not in self.character_profiles:
            raise ValueError(f"Character {character_id} not found")
        
        profile = self.character_profiles[character_id]
        base_prompt = self.character_prompts[character_id].get(service, "")
        
        # シーン説明を組み込む
        if service == "midjourney":
            # Midjourneyの場合、キャラクターリファレンスを使用
            prompt = f"{scene_description}, {base_prompt}"
            if profile.get('reference_url'):
                prompt = prompt.replace('[CHARACTER_REF]', profile['reference_url'])
        else:
            # その他のサービス
            prompt = f"{base_prompt}, {scene_description}"
        
        return prompt
    
    def apply_to_all_scenes(self,
                           character_id: str,
                           scenes: List[Dict[str, Any]],
                           service: str = "midjourney") -> List[Dict[str, Any]]:
        """
        全シーンにキャラクターを適用
        
        Args:
            character_id: キャラクターID
            scenes: シーンリスト
            service: 使用するサービス
        
        Returns:
            更新されたシーンリスト
        """
        updated_scenes = []
        
        for scene in scenes:
            # 各シーンにキャラクターを適用
            updated_scene = scene.copy()
            
            # 元のプロンプトを取得
            original_prompt = scene.get('prompt', scene.get('content', ''))
            
            # キャラクター用のプロンプトを生成
            character_prompt = self.get_scene_prompt(
                character_id,
                original_prompt,
                service
            )
            
            # シーンを更新
            updated_scene['character_prompt'] = character_prompt
            updated_scene['character_id'] = character_id
            updated_scene['character_name'] = self.character_profiles[character_id]['name']
            
            updated_scenes.append(updated_scene)
        
        return updated_scenes
    
    def create_character_sheet(self, character_id: str) -> Dict[str, Any]:
        """
        キャラクターシートを作成（全角度・表情集）
        
        Args:
            character_id: キャラクターID
        
        Returns:
            キャラクターシート情報
        """
        profile = self.character_profiles[character_id]
        
        # 様々な角度と表情のプロンプト
        variations = {
            "front_smile": f"{profile['description']}, front view, smiling, happy expression",
            "front_neutral": f"{profile['description']}, front view, neutral expression",
            "side_profile": f"{profile['description']}, side profile view, elegant pose",
            "three_quarter": f"{profile['description']}, three quarter view, natural pose",
            "back_view": f"{profile['description']}, back view, looking over shoulder",
            "closeup_face": f"{profile['description']}, close up face, detailed features",
            "full_body": f"{profile['description']}, full body shot, standing pose",
            "action_pose": f"{profile['description']}, dynamic action pose, energetic"
        }
        
        return {
            "character_id": character_id,
            "character_name": profile['name'],
            "variations": variations,
            "reference_image": profile['image_path']
        }
    
    def enhance_with_face_swap(self,
                              character_id: str,
                              target_video: str,
                              output_path: str) -> bool:
        """
        Face Swap技術でキャラクターを適用
        
        Args:
            character_id: キャラクターID
            target_video: ターゲット動画
            output_path: 出力パス
        
        Returns:
            成功の可否
        """
        # Face Swap APIとの連携（実装は仮）
        # 実際にはRoop、FaceSwap、DeepFaceLab等を使用
        
        profile = self.character_profiles[character_id]
        source_image = profile['image_path']
        
        # ここでFace Swap処理を実行
        # ...
        
        return True
    
    def save_profile(self, character_id: str, save_path: str):
        """プロファイルを保存"""
        if character_id not in self.character_profiles:
            raise ValueError(f"Character {character_id} not found")
        
        profile = self.character_profiles[character_id]
        
        # 画像をBase64エンコード
        with open(profile['image_path'], 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        save_data = {
            "profile": profile,
            "prompts": self.character_prompts[character_id],
            "image_data": image_data
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    def load_profile(self, load_path: str) -> str:
        """プロファイルを読み込み"""
        with open(load_path, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        profile = save_data['profile']
        character_id = profile['id']
        
        # 画像を復元
        image_data = base64.b64decode(save_data['image_data'])
        temp_path = Path(f"temp_{character_id}.jpg")
        with open(temp_path, 'wb') as f:
            f.write(image_data)
        
        profile['image_path'] = str(temp_path)
        
        # プロファイルを登録
        self.character_profiles[character_id] = profile
        self.character_prompts[character_id] = save_data['prompts']
        
        return character_id