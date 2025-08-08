import asyncio
import json
from typing import List, Dict, Any
import openai
import anthropic
import google.generativeai as genai
from datetime import timedelta

class ScriptPlanner:
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
            
        if self.config.get("deepseek_api_key"):
            self.ai_clients["deepseek"] = self.config["deepseek_api_key"]
    
    async def generate_plot_options(self, title: str, keywords: str, 
                                   description: str, mood: str, 
                                   lyrics: str, duration: float) -> List[Dict]:
        duration_str = str(timedelta(seconds=int(duration)))
        
        prompt_template = f"""
        PVの構成案を作成してください。

        【基本情報】
        - タイトル: {title}
        - キーワード: {keywords}
        - 説明: {description}
        - 雰囲気: {mood}
        - 動画長さ: {duration_str}
        
        【歌詞/メッセージ】
        {lyrics[:1000] if lyrics else "なし"}
        
        【要求事項】
        1. 導入部（15-30秒）
        2. 展開部（メインストーリー）
        3. クライマックス
        4. エンディング（15-30秒）
        
        以下のJSON形式で構成案を出力してください：
        {{
            "title": "構成案のタイトル",
            "concept": "コンセプトの説明",
            "introduction": {{
                "duration": "秒数",
                "description": "導入部の内容",
                "key_scenes": ["シーン1", "シーン2"]
            }},
            "development": {{
                "duration": "秒数",
                "description": "展開部の内容",
                "key_scenes": ["シーン1", "シーン2", "シーン3"]
            }},
            "climax": {{
                "duration": "秒数",
                "description": "クライマックスの内容",
                "key_scenes": ["シーン1", "シーン2"]
            }},
            "ending": {{
                "duration": "秒数",
                "description": "エンディングの内容",
                "key_scenes": ["シーン1", "シーン2"]
            }},
            "visual_style": "映像スタイルの説明",
            "color_palette": ["色1", "色2", "色3"],
            "emotions_flow": ["感情1", "感情2", "感情3"]
        }}
        """
        
        plot_options = []
        
        if "gpt" in self.ai_clients:
            gpt_plot = await self.generate_with_gpt(prompt_template)
            if gpt_plot:
                plot_options.append({"source": "GPT-4", "plot": gpt_plot})
        
        if "claude" in self.ai_clients:
            claude_plot = await self.generate_with_claude(prompt_template)
            if claude_plot:
                plot_options.append({"source": "Claude", "plot": claude_plot})
        
        if "gemini" in self.ai_clients:
            gemini_plot = await self.generate_with_gemini(prompt_template)
            if gemini_plot:
                plot_options.append({"source": "Gemini", "plot": gemini_plot})
        
        if not plot_options:
            plot_options.append(self.generate_default_plot(title, keywords, mood, duration))
        
        return plot_options
    
    async def generate_with_gpt(self, prompt: str) -> Dict:
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはPV構成の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"GPT Error: {e}")
            return None
    
    async def generate_with_claude(self, prompt: str) -> Dict:
        try:
            client = self.ai_clients["claude"]
            response = await asyncio.to_thread(
                client.messages.create,
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.8,
                system="あなたはPV構成の専門家です。",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"Claude Error: {e}")
            return None
    
    async def generate_with_gemini(self, prompt: str) -> Dict:
        try:
            model = self.ai_clients["gemini"]
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            
            content = response.text
            return self.parse_json_response(content)
            
        except Exception as e:
            print(f"Gemini Error: {e}")
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
    
    def generate_default_plot(self, title: str, keywords: str, 
                             mood: str, duration: float) -> Dict:
        total_seconds = int(duration)
        intro_duration = min(30, total_seconds // 10)
        ending_duration = min(30, total_seconds // 10)
        climax_duration = total_seconds // 4
        development_duration = total_seconds - intro_duration - ending_duration - climax_duration
        
        return {
            "source": "Default",
            "plot": {
                "title": f"{title} - ストーリー構成",
                "concept": f"{mood}な雰囲気で{keywords}を表現するPV",
                "introduction": {
                    "duration": intro_duration,
                    "description": "世界観の導入とキャラクター紹介",
                    "key_scenes": ["オープニング", "キャラクター登場"]
                },
                "development": {
                    "duration": development_duration,
                    "description": "メインストーリーの展開",
                    "key_scenes": ["日常シーン", "出会い", "成長"]
                },
                "climax": {
                    "duration": climax_duration,
                    "description": "感動的なクライマックス",
                    "key_scenes": ["決意", "挑戦"]
                },
                "ending": {
                    "duration": ending_duration,
                    "description": "希望に満ちたエンディング",
                    "key_scenes": ["解決", "未来への展望"]
                },
                "visual_style": f"{mood}で印象的な映像表現",
                "color_palette": self.get_color_palette(mood),
                "emotions_flow": ["期待", "展開", "高揚", "感動", "余韻"]
            }
        }
    
    def get_color_palette(self, mood: str) -> List[str]:
        palettes = {
            "明るい": ["#FFD700", "#87CEEB", "#98FB98"],
            "感動的": ["#FF69B4", "#DDA0DD", "#F0E68C"],
            "ノスタルジック": ["#DEB887", "#BC8F8F", "#F4A460"],
            "エネルギッシュ": ["#FF4500", "#FFD700", "#00CED1"],
            "ミステリアス": ["#483D8B", "#8B008B", "#4B0082"],
            "ダーク": ["#2F4F4F", "#696969", "#708090"],
            "ファンタジー": ["#9370DB", "#00BFFF", "#FFB6C1"],
            "クール": ["#4169E1", "#00FFFF", "#C0C0C0"]
        }
        return palettes.get(mood, ["#808080", "#A9A9A9", "#D3D3D3"])
    
    def select_best_plot(self, plot_options: List[Dict]) -> Dict:
        if not plot_options:
            return None
            
        for option in plot_options:
            if option["source"] in ["GPT-4", "Claude"]:
                return option["plot"]
        
        return plot_options[0]["plot"]
    
    def calculate_scene_count(self, duration: float) -> int:
        scene_duration = 8
        return min(60, int(duration / scene_duration))