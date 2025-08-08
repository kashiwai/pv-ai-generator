import asyncio
import json
from typing import Dict, List, Any, Optional
import openai
import anthropic
import google.generativeai as genai
from datetime import timedelta

class ScriptWriter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialize_ai_clients()
        
    def initialize_ai_clients(self):
        self.ai_clients = {}
        
        if self.config.get("openai_api_key"):
            openai.api_key = self.config["openai_api_key"]
            self.ai_clients["gpt"] = "gpt-4"
            
        if self.config.get("anthropic_api_key"):
            self.ai_clients["claude"] = anthropic.Anthropic(
                api_key=self.config["anthropic_api_key"]
            )
            
        if self.config.get("google_api_key"):
            genai.configure(api_key=self.config["google_api_key"])
            self.ai_clients["gemini"] = genai.GenerativeModel('gemini-pro')
    
    async def write_script(self, plot: Dict, lyrics: Optional[str], 
                          duration: float) -> Dict:
        
        duration_str = str(timedelta(seconds=int(duration)))
        scene_count = self.calculate_scene_count(duration)
        
        prompt = f"""
        以下の構成案を元に、PV用の詳細な台本を作成してください。

        【構成案】
        - タイトル: {plot.get('title', 'PV')}
        - コンセプト: {plot.get('concept', '')}
        - 導入部: {json.dumps(plot.get('introduction', {}), ensure_ascii=False)}
        - 展開部: {json.dumps(plot.get('development', {}), ensure_ascii=False)}
        - クライマックス: {json.dumps(plot.get('climax', {}), ensure_ascii=False)}
        - エンディング: {json.dumps(plot.get('ending', {}), ensure_ascii=False)}
        - ビジュアルスタイル: {plot.get('visual_style', '')}
        - カラーパレット: {', '.join(plot.get('color_palette', []))}
        
        【歌詞/メッセージ】
        {lyrics[:2000] if lyrics else "インストゥルメンタル"}
        
        【技術仕様】
        - 動画長さ: {duration_str}
        - シーン数: 約{scene_count}シーン（8秒/シーン）
        
        【出力形式】
        以下のJSON形式で台本を出力してください：
        {{
            "title": "台本タイトル",
            "total_duration": {duration},
            "scenes": [
                {{
                    "scene_number": 1,
                    "timestamp": "00:00-00:08",
                    "duration": 8,
                    "type": "introduction/development/climax/ending",
                    "narration": "ナレーション文（あれば）",
                    "visual_description": "映像の詳細な説明",
                    "camera_movement": "カメラワーク（パン、ズーム、固定など）",
                    "mood": "シーンの雰囲気",
                    "key_elements": ["要素1", "要素2"],
                    "transition": "次シーンへの遷移方法"
                }}
            ],
            "narration_style": "ナレーションのスタイル説明",
            "visual_consistency": "映像全体の一貫性に関する注意点"
        }}
        
        注意点：
        - 各シーンは約8秒を基準とする
        - ナレーションは自然で感情的に
        - 映像説明は具体的かつ詳細に
        - 音楽との同期を意識
        """
        
        script = None
        
        if "gpt" in self.ai_clients:
            script = await self.generate_script_with_gpt(prompt)
        elif "claude" in self.ai_clients:
            script = await self.generate_script_with_claude(prompt)
        elif "gemini" in self.ai_clients:
            script = await self.generate_script_with_gemini(prompt)
        
        if not script:
            script = self.generate_default_script(plot, lyrics, duration, scene_count)
        
        return self.validate_and_fix_script(script, duration)
    
    async def generate_script_with_gpt(self, prompt: str) -> Dict:
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはPV台本のプロフェッショナルライターです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"GPT Script Error: {e}")
            return None
    
    async def generate_script_with_claude(self, prompt: str) -> Dict:
        try:
            client = self.ai_clients["claude"]
            response = await asyncio.to_thread(
                client.messages.create,
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                system="あなたはPV台本のプロフェッショナルライターです。",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"Claude Script Error: {e}")
            return None
    
    async def generate_script_with_gemini(self, prompt: str) -> Dict:
        try:
            model = self.ai_clients["gemini"]
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            content = response.text
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"Gemini Script Error: {e}")
            return None
    
    def parse_json_response(self, content: str) -> Dict:
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        return None
    
    def calculate_scene_count(self, duration: float) -> int:
        scene_duration = 8
        return min(60, max(1, int(duration / scene_duration)))
    
    def generate_default_script(self, plot: Dict, lyrics: Optional[str], 
                               duration: float, scene_count: int) -> Dict:
        scenes = []
        scene_duration = duration / scene_count
        
        for i in range(scene_count):
            start_time = i * scene_duration
            end_time = min((i + 1) * scene_duration, duration)
            
            if i < scene_count * 0.15:
                scene_type = "introduction"
                mood = "期待感"
            elif i < scene_count * 0.7:
                scene_type = "development"
                mood = "展開"
            elif i < scene_count * 0.85:
                scene_type = "climax"
                mood = "高揚"
            else:
                scene_type = "ending"
                mood = "余韻"
            
            scenes.append({
                "scene_number": i + 1,
                "timestamp": f"{int(start_time//60):02d}:{int(start_time%60):02d}-{int(end_time//60):02d}:{int(end_time%60):02d}",
                "duration": scene_duration,
                "type": scene_type,
                "narration": self.generate_narration_for_scene(i, scene_count, lyrics),
                "visual_description": self.generate_visual_description(scene_type, plot),
                "camera_movement": self.select_camera_movement(scene_type),
                "mood": mood,
                "key_elements": self.get_key_elements(scene_type, plot),
                "transition": self.select_transition(i, scene_count)
            })
        
        return {
            "title": plot.get('title', 'PV台本'),
            "total_duration": duration,
            "scenes": scenes,
            "narration_style": "感情豊かで自然な語り口",
            "visual_consistency": "キャラクターと世界観の一貫性を保持"
        }
    
    def generate_narration_for_scene(self, scene_index: int, 
                                    total_scenes: int, lyrics: Optional[str]) -> str:
        if not lyrics:
            return ""
        
        lyrics_lines = lyrics.split('\n')
        if not lyrics_lines:
            return ""
        
        lines_per_scene = max(1, len(lyrics_lines) // total_scenes)
        start_line = scene_index * lines_per_scene
        end_line = min(start_line + lines_per_scene, len(lyrics_lines))
        
        if start_line < len(lyrics_lines):
            return ' '.join(lyrics_lines[start_line:end_line])
        return ""
    
    def generate_visual_description(self, scene_type: str, plot: Dict) -> str:
        descriptions = {
            "introduction": "キャラクターが登場し、世界観を紹介する印象的なオープニングシーン",
            "development": "ストーリーが展開し、キャラクターの感情や関係性が描かれるシーン",
            "climax": "感動的で印象的な、物語の頂点となるシーン",
            "ending": "余韻を残す美しいエンディングシーン"
        }
        
        base_description = descriptions.get(scene_type, "印象的なシーン")
        visual_style = plot.get('visual_style', '')
        
        return f"{base_description}。{visual_style}"
    
    def select_camera_movement(self, scene_type: str) -> str:
        movements = {
            "introduction": ["スローズームイン", "パン", "固定ショット"],
            "development": ["トラッキング", "パン", "ティルト", "手持ちカメラ"],
            "climax": ["ダイナミックズーム", "回転", "クレーン"],
            "ending": ["スローズームアウト", "固定ロングショット", "フェード"]
        }
        
        import random
        return random.choice(movements.get(scene_type, ["固定ショット"]))
    
    def get_key_elements(self, scene_type: str, plot: Dict) -> List[str]:
        base_elements = []
        
        if scene_type == "introduction" and "introduction" in plot:
            base_elements = plot["introduction"].get("key_scenes", [])[:2]
        elif scene_type == "development" and "development" in plot:
            base_elements = plot["development"].get("key_scenes", [])[:2]
        elif scene_type == "climax" and "climax" in plot:
            base_elements = plot["climax"].get("key_scenes", [])[:2]
        elif scene_type == "ending" and "ending" in plot:
            base_elements = plot["ending"].get("key_scenes", [])[:2]
        
        if not base_elements:
            base_elements = ["キャラクター", "背景"]
        
        return base_elements
    
    def select_transition(self, scene_index: int, total_scenes: int) -> str:
        if scene_index == total_scenes - 1:
            return "フェードアウト"
        
        transitions = ["カット", "ディゾルブ", "ワイプ", "フェード"]
        
        import random
        return random.choice(transitions)
    
    def validate_and_fix_script(self, script: Dict, duration: float) -> Dict:
        if not script:
            return self.generate_default_script({}, None, duration, 10)
        
        if "scenes" not in script or not script["scenes"]:
            script["scenes"] = []
            scene_count = self.calculate_scene_count(duration)
            for i in range(scene_count):
                script["scenes"].append({
                    "scene_number": i + 1,
                    "timestamp": f"{i*8:02d}:{(i+1)*8:02d}",
                    "duration": 8,
                    "type": "development",
                    "narration": "",
                    "visual_description": "シーン",
                    "camera_movement": "固定",
                    "mood": "通常",
                    "key_elements": [],
                    "transition": "カット"
                })
        
        script["total_duration"] = duration
        
        return script