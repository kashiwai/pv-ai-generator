"""
台本生成モジュール
"""
import os
import json
from typing import Dict, List, Optional

class ScriptGenerator:
    """台本生成クラス"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def generate_script(self, title: str, keywords: str, lyrics: str, style: str, duration: int = 180) -> Dict:
        """構成案と台本を生成"""
        
        # シーン数を計算（30秒ごとに1シーン）
        num_scenes = min(max(duration // 30, 4), 12)  # 最小4シーン、最大12シーン
        
        # フォールバック台本を生成
        script = self._generate_fallback_script(title, keywords, style, num_scenes)
        
        # シーンごとに分割
        scenes = self._parse_script_to_scenes(script, num_scenes)
        
        return {
            "full_script": script,
            "scenes": scenes,
            "duration": duration,
            "num_scenes": num_scenes
        }
    
    def _generate_fallback_script(self, title: str, keywords: str, style: str, num_scenes: int) -> str:
        """フォールバック台本生成"""
        scenes_text = []
        
        scene_templates = [
            {
                "name": "オープニング",
                "description": f"タイトル「{title}」のフェードイン、{keywords}をイメージした美しい風景",
                "camera": "ゆっくりとしたズームイン",
                "tone": "期待感と神秘性",
                "narration": "新しい物語が始まる"
            },
            {
                "name": "導入",
                "description": f"メインキャラクターの登場、{style}スタイルの演出",
                "camera": "キャラクターにフォーカス",
                "tone": "親しみやすさと共感",
                "narration": "出会いが運命を変える"
            },
            {
                "name": "展開",
                "description": "アクションシーケンス、ドラマチックな展開",
                "camera": "ダイナミックな動き",
                "tone": "緊張感と興奮",
                "narration": "挑戦が始まった"
            },
            {
                "name": "クライマックス",
                "description": "最高潮の瞬間、感動的なシーン",
                "camera": "感情を強調するクローズアップ",
                "tone": "感動と達成感",
                "narration": "夢は叶う"
            },
            {
                "name": "エンディング",
                "description": "静かな終わり、余韻を残すシーン",
                "camera": "ゆっくりとしたフェードアウト",
                "tone": "満足感と希望",
                "narration": "物語は続く"
            }
        ]
        
        for i in range(min(num_scenes, len(scene_templates))):
            template = scene_templates[i]
            scenes_text.append(f"""
シーン{i+1}: {template['name']}
- {template['description']}
- カメラ：{template['camera']}
- トーン：{template['tone']}
- ナレーション：「{template['narration']}」
""")
        
        return "\n".join(scenes_text)
    
    def _parse_script_to_scenes(self, script: str, num_scenes: int) -> List[Dict]:
        """台本をシーンごとに分割"""
        scenes = []
        
        # シンプルな分割ロジック
        lines = script.split('\n')
        current_scene = {
            "description": "",
            "camera_work": "",
            "tone": "",
            "narration": ""
        }
        scene_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'シーン' in line:
                if current_scene["description"]:
                    scenes.append({
                        "id": f"scene_{scene_count}",
                        "number": scene_count + 1,
                        **current_scene,
                        "duration": 30
                    })
                    current_scene = {
                        "description": "",
                        "camera_work": "",
                        "tone": "",
                        "narration": ""
                    }
                    scene_count += 1
            elif 'カメラ' in line:
                current_scene["camera_work"] = line.split('：')[-1].strip()
            elif 'トーン' in line:
                current_scene["tone"] = line.split('：')[-1].strip()
            elif 'ナレーション' in line:
                current_scene["narration"] = line.split('：')[-1].strip().strip('「」')
            elif line.startswith('-'):
                desc = line[1:].strip()
                if desc and not any(k in desc for k in ['カメラ', 'トーン', 'ナレーション']):
                    current_scene["description"] += desc + " "
        
        # 最後のシーン追加
        if current_scene["description"]:
            scenes.append({
                "id": f"scene_{scene_count}",
                "number": scene_count + 1,
                **current_scene,
                "duration": 30
            })
        
        return scenes[:num_scenes]