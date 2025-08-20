"""
高度な台本分析・生成モジュール
歌詞、情景、感情から深い台本を生成
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import openai
import anthropic
import google.generativeai as genai
from pathlib import Path

class AdvancedScriptAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_key = config.get("openai_api_key")
        self.anthropic_key = config.get("anthropic_api_key")
        self.google_key = config.get("google_api_key")
        
        # API初期化
        if self.openai_key:
            openai.api_key = self.openai_key
        if self.anthropic_key:
            self.claude_client = anthropic.Anthropic(api_key=self.anthropic_key)
        if self.google_key:
            genai.configure(api_key=self.google_key)
    
    async def analyze_and_enhance_script(self,
                                        lyrics: str,
                                        keywords: str,
                                        description: str,
                                        mood: str,
                                        music_duration: float) -> Dict[str, Any]:
        """
        歌詞と情景から深い台本を生成
        
        Args:
            lyrics: 歌詞またはメッセージ
            keywords: キーワード（カンマ区切り）
            description: 作品の説明
            mood: 雰囲気
            music_duration: 音楽の長さ（秒）
        
        Returns:
            分析結果と強化された台本
        """
        
        # 1. 歌詞の詳細分析
        lyrics_analysis = await self.analyze_lyrics_deep(lyrics)
        
        # 2. 感情曲線の生成
        emotion_curve = await self.generate_emotion_curve(lyrics, music_duration)
        
        # 3. シンボリズムとメタファーの抽出
        symbolism = await self.extract_symbolism(lyrics, keywords, description)
        
        # 4. ストーリーアークの構築
        story_arc = await self.build_story_arc(
            lyrics_analysis, 
            emotion_curve,
            symbolism,
            music_duration
        )
        
        # 5. 詳細なシーン生成
        detailed_scenes = await self.generate_detailed_scenes(
            story_arc,
            lyrics_analysis,
            emotion_curve,
            symbolism,
            music_duration
        )
        
        return {
            "version": "2.4.0",
            "analysis": {
                "lyrics_analysis": lyrics_analysis,
                "emotion_curve": emotion_curve,
                "symbolism": symbolism,
                "story_arc": story_arc
            },
            "detailed_script": detailed_scenes,
            "metadata": {
                "keywords": keywords,
                "mood": mood,
                "duration": music_duration
            }
        }
    
    async def analyze_lyrics_deep(self, lyrics: str) -> Dict[str, Any]:
        """
        歌詞の深層分析
        """
        prompt = f"""
        以下の歌詞/テキストを詳細に分析してください：
        
        {lyrics}
        
        以下の観点から分析を行ってください：
        
        1. **主題とテーマ**
           - 中心的なメッセージ
           - 副次的なテーマ
           - 隠されたメッセージ
        
        2. **感情の層**
           - 表層的な感情
           - 深層的な感情
           - 感情の変化と転換点
        
        3. **イメージと象徴**
           - 視覚的イメージ
           - 聴覚的イメージ
           - 触覚的イメージ
           - 象徴的な要素
        
        4. **物語構造**
           - 起承転結
           - クライマックス
           - 解決または余韻
        
        5. **キャラクター/話者**
           - 話者の立場
           - 感情状態
           - 変化と成長
        
        6. **時間と空間**
           - 時間的設定
           - 空間的設定
           - 時空の変化
        
        JSON形式で出力してください。
        """
        
        if self.anthropic_key:
            analysis = await self.analyze_with_claude(prompt)
        elif self.openai_key:
            analysis = await self.analyze_with_gpt4(prompt)
        else:
            analysis = self.create_basic_analysis(lyrics)
        
        return json.loads(analysis) if isinstance(analysis, str) else analysis
    
    async def generate_emotion_curve(self, lyrics: str, duration: float) -> List[Dict]:
        """
        感情曲線の生成（時間軸に沿った感情の変化）
        """
        # 歌詞を時間で分割
        lines = lyrics.split('\n')
        time_per_line = duration / max(len(lines), 1)
        
        emotion_points = []
        current_time = 0
        
        for i, line in enumerate(lines):
            if line.strip():
                emotion = await self.analyze_line_emotion(line, i, len(lines))
                emotion_points.append({
                    "time": current_time,
                    "text": line,
                    "primary_emotion": emotion["primary"],
                    "intensity": emotion["intensity"],
                    "secondary_emotions": emotion["secondary"],
                    "visual_mood": emotion["visual_mood"]
                })
            current_time += time_per_line
        
        # 感情の補間とスムージング
        smoothed_curve = self.smooth_emotion_curve(emotion_points)
        
        return smoothed_curve
    
    async def analyze_line_emotion(self, line: str, position: int, total: int) -> Dict:
        """
        単一行の感情分析
        """
        position_context = "beginning" if position < total * 0.3 else \
                          "climax" if position > total * 0.7 else "middle"
        
        prompt = f"""
        以下のテキスト行の感情を分析してください：
        "{line}"
        
        位置: {position_context}
        
        以下を判定してください：
        1. 主要な感情（喜び、悲しみ、怒り、恐れ、驚き、期待、信頼、嫌悪から選択）
        2. 感情の強度（0-100）
        3. 副次的な感情（複数可）
        4. 視覚的な雰囲気（明るい、暗い、神秘的、激しい、穏やか、など）
        
        JSON形式で返してください。
        """
        
        # 簡略化のため、ルールベースで判定
        emotions = {
            "primary": self.detect_primary_emotion(line),
            "intensity": self.calculate_intensity(line, position_context),
            "secondary": self.detect_secondary_emotions(line),
            "visual_mood": self.determine_visual_mood(line)
        }
        
        return emotions
    
    def detect_primary_emotion(self, text: str) -> str:
        """
        主要な感情を検出
        """
        emotion_keywords = {
            "喜び": ["嬉しい", "楽しい", "幸せ", "笑", "明るい", "光"],
            "悲しみ": ["悲しい", "涙", "寂しい", "切ない", "別れ"],
            "怒り": ["怒", "憤", "許せない", "腹立"],
            "恐れ": ["怖", "恐", "不安", "心配"],
            "驚き": ["驚", "びっくり", "突然", "まさか"],
            "期待": ["待つ", "楽しみ", "希望", "願", "夢"],
            "信頼": ["信じ", "頼", "安心", "守"],
            "嫌悪": ["嫌", "憎", "汚", "醜"]
        }
        
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return emotion
        
        return "期待"  # デフォルト
    
    def calculate_intensity(self, text: str, position: str) -> int:
        """
        感情の強度を計算
        """
        base_intensity = 50
        
        # 感嘆符や強調表現で強度増加
        if "！" in text or "!!" in text:
            base_intensity += 20
        if "とても" in text or "すごく" in text or "本当に" in text:
            base_intensity += 15
        
        # 位置による調整
        if position == "climax":
            base_intensity += 20
        elif position == "beginning":
            base_intensity -= 10
        
        return min(100, max(0, base_intensity))
    
    def detect_secondary_emotions(self, text: str) -> List[str]:
        """
        副次的な感情を検出
        """
        emotions = []
        
        emotion_patterns = {
            "nostalgic": ["昔", "思い出", "あの頃", "懐かし"],
            "lonely": ["一人", "孤独", "寂し"],
            "hopeful": ["きっと", "いつか", "願"],
            "passionate": ["熱", "燃え", "情熱"],
            "peaceful": ["静か", "穏やか", "安らぎ"]
        }
        
        for emotion, patterns in emotion_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    emotions.append(emotion)
                    break
        
        return emotions[:3]  # 最大3つまで
    
    def determine_visual_mood(self, text: str) -> str:
        """
        視覚的な雰囲気を決定
        """
        mood_keywords = {
            "bright": ["光", "明", "輝", "太陽", "晴"],
            "dark": ["闇", "暗", "影", "夜", "黒"],
            "mystical": ["神秘", "不思議", "魔法", "幻"],
            "intense": ["激", "強", "爆", "炎"],
            "calm": ["静", "穏", "優", "柔"],
            "colorful": ["色", "虹", "カラフル", "鮮"],
            "monochrome": ["白黒", "モノクロ", "灰"]
        }
        
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return mood
        
        return "balanced"
    
    def smooth_emotion_curve(self, points: List[Dict]) -> List[Dict]:
        """
        感情曲線をスムージング
        """
        if len(points) <= 2:
            return points
        
        smoothed = []
        for i in range(len(points)):
            point = points[i].copy()
            
            # 前後のポイントを考慮して強度を調整
            if 0 < i < len(points) - 1:
                prev_intensity = points[i-1]["intensity"]
                next_intensity = points[i+1]["intensity"]
                point["intensity"] = int((prev_intensity + point["intensity"] * 2 + next_intensity) / 4)
            
            smoothed.append(point)
        
        return smoothed
    
    async def extract_symbolism(self, lyrics: str, keywords: str, 
                               description: str) -> Dict[str, Any]:
        """
        シンボリズムとメタファーの抽出
        """
        prompt = f"""
        以下の要素から象徴的な意味とメタファーを抽出してください：
        
        歌詞/テキスト:
        {lyrics}
        
        キーワード: {keywords}
        説明: {description}
        
        以下を分析してください：
        
        1. **中心的シンボル**
           - 主要な象徴
           - その意味
           - 視覚的表現方法
        
        2. **メタファー**
           - 使用されている比喩
           - 隠喩の意味
           - 映像化の方法
        
        3. **色彩象徴**
           - 主要な色
           - 色の意味
           - 感情との関連
        
        4. **自然要素**
           - 自然のシンボル
           - 季節、天候
           - 時間帯
        
        5. **文化的参照**
           - 文化的シンボル
           - 伝統的要素
           - 現代的要素
        
        JSON形式で出力してください。
        """
        
        # 基本的なシンボル抽出
        symbolism = {
            "central_symbols": self.extract_central_symbols(lyrics, keywords),
            "metaphors": self.extract_metaphors(lyrics),
            "color_symbolism": self.extract_color_symbolism(lyrics, description),
            "nature_elements": self.extract_nature_elements(lyrics),
            "cultural_references": self.extract_cultural_references(lyrics, keywords)
        }
        
        return symbolism
    
    def extract_central_symbols(self, lyrics: str, keywords: str) -> List[Dict]:
        """
        中心的なシンボルを抽出
        """
        symbols = []
        
        # キーワードから主要シンボルを特定
        keyword_list = [k.strip() for k in keywords.split(',')]
        
        symbol_mapping = {
            "愛": {"symbol": "heart", "meaning": "love and connection", "visual": "glowing red heart"},
            "夢": {"symbol": "stars", "meaning": "hopes and aspirations", "visual": "shooting stars"},
            "自由": {"symbol": "wings", "meaning": "freedom and liberation", "visual": "spreading wings"},
            "時間": {"symbol": "clock", "meaning": "passage of time", "visual": "flowing sand"},
            "旅": {"symbol": "path", "meaning": "life journey", "visual": "winding road"},
            "光": {"symbol": "sun", "meaning": "hope and enlightenment", "visual": "rising sun"},
            "成長": {"symbol": "tree", "meaning": "growth and development", "visual": "growing tree"}
        }
        
        for keyword in keyword_list:
            for key, value in symbol_mapping.items():
                if key in keyword or key in lyrics:
                    symbols.append(value)
        
        return symbols[:3]  # 最大3つ
    
    def extract_metaphors(self, lyrics: str) -> List[Dict]:
        """
        メタファーを抽出
        """
        metaphors = []
        
        # パターンマッチングでメタファーを検出
        patterns = [
            (r"(.+)のよう[に|な](.+)", "simile"),
            (r"(.+)は(.+)", "metaphor"),
            (r"まるで(.+)", "comparison")
        ]
        
        for pattern, type_ in patterns:
            matches = re.findall(pattern, lyrics)
            for match in matches[:2]:  # 各タイプ最大2つ
                metaphors.append({
                    "type": type_,
                    "expression": match if isinstance(match, str) else " ".join(match),
                    "visual_interpretation": self.interpret_metaphor_visually(match)
                })
        
        return metaphors
    
    def interpret_metaphor_visually(self, metaphor) -> str:
        """
        メタファーを視覚的に解釈
        """
        if isinstance(metaphor, tuple):
            metaphor = " ".join(metaphor)
        
        # 簡単な視覚化ルール
        if "風" in metaphor:
            return "flowing particles and movement"
        elif "光" in metaphor:
            return "glowing aura and brightness"
        elif "花" in metaphor:
            return "blooming flowers transition"
        elif "海" in metaphor:
            return "ocean waves and depth"
        else:
            return "abstract visual representation"
    
    def extract_color_symbolism(self, lyrics: str, description: str) -> Dict:
        """
        色彩象徴を抽出
        """
        colors = {
            "primary_colors": [],
            "emotional_colors": [],
            "symbolic_meanings": {}
        }
        
        color_emotions = {
            "赤": {"emotion": "passion", "meaning": "love, energy, danger"},
            "青": {"emotion": "calm", "meaning": "peace, sadness, depth"},
            "緑": {"emotion": "growth", "meaning": "nature, life, harmony"},
            "黄": {"emotion": "joy", "meaning": "happiness, energy, caution"},
            "紫": {"emotion": "mystery", "meaning": "royalty, spirituality, creativity"},
            "白": {"emotion": "purity", "meaning": "innocence, new beginning, emptiness"},
            "黒": {"emotion": "depth", "meaning": "mystery, elegance, ending"},
            "金": {"emotion": "luxury", "meaning": "success, wealth, divine"},
            "銀": {"emotion": "modern", "meaning": "technology, future, moon"}
        }
        
        text = lyrics + " " + description
        for color, attributes in color_emotions.items():
            if color in text:
                colors["primary_colors"].append(color)
                colors["emotional_colors"].append(attributes["emotion"])
                colors["symbolic_meanings"][color] = attributes["meaning"]
        
        # デフォルト色を追加
        if not colors["primary_colors"]:
            colors["primary_colors"] = ["青", "白"]
            colors["emotional_colors"] = ["calm", "purity"]
        
        return colors
    
    def extract_nature_elements(self, lyrics: str) -> Dict:
        """
        自然要素を抽出
        """
        elements = {
            "season": self.detect_season(lyrics),
            "weather": self.detect_weather(lyrics),
            "time_of_day": self.detect_time_of_day(lyrics),
            "landscape": self.detect_landscape(lyrics)
        }
        
        return elements
    
    def detect_season(self, text: str) -> str:
        """
        季節を検出
        """
        seasons = {
            "spring": ["春", "桜", "新緑", "花見"],
            "summer": ["夏", "海", "花火", "祭り", "暑"],
            "autumn": ["秋", "紅葉", "落ち葉", "収穫"],
            "winter": ["冬", "雪", "寒", "クリスマス"]
        }
        
        for season, keywords in seasons.items():
            for keyword in keywords:
                if keyword in text:
                    return season
        
        return "timeless"
    
    def detect_weather(self, text: str) -> str:
        """
        天候を検出
        """
        weather_patterns = {
            "sunny": ["晴", "太陽", "日差し"],
            "rainy": ["雨", "傘", "濡れ"],
            "cloudy": ["曇", "雲", "霧"],
            "snowy": ["雪", "吹雪", "白"],
            "stormy": ["嵐", "雷", "風"]
        }
        
        for weather, patterns in weather_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return weather
        
        return "clear"
    
    def detect_time_of_day(self, text: str) -> str:
        """
        時間帯を検出
        """
        times = {
            "dawn": ["夜明け", "朝焼け", "早朝"],
            "morning": ["朝", "午前", "モーニング"],
            "noon": ["昼", "正午", "日中"],
            "evening": ["夕", "黄昏", "夕焼け"],
            "night": ["夜", "深夜", "星", "月"]
        }
        
        for time, keywords in times.items():
            for keyword in keywords:
                if keyword in text:
                    return time
        
        return "day"
    
    def detect_landscape(self, text: str) -> List[str]:
        """
        風景要素を検出
        """
        landscapes = []
        
        landscape_keywords = {
            "urban": ["街", "ビル", "都市", "道路"],
            "nature": ["森", "山", "川", "自然"],
            "ocean": ["海", "波", "浜", "港"],
            "sky": ["空", "雲", "星", "宇宙"],
            "indoor": ["部屋", "家", "建物", "室内"]
        }
        
        for landscape, keywords in landscape_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    landscapes.append(landscape)
                    break
        
        return landscapes[:2] if landscapes else ["abstract"]
    
    def extract_cultural_references(self, lyrics: str, keywords: str) -> List[str]:
        """
        文化的参照を抽出
        """
        references = []
        
        # 日本文化要素
        japanese_culture = ["桜", "祭り", "神社", "着物", "侍", "忍者", "茶道", "武士道"]
        for element in japanese_culture:
            if element in lyrics or element in keywords:
                references.append(f"japanese_{element}")
        
        # 現代文化要素
        modern_culture = ["スマホ", "SNS", "AI", "ロボット", "宇宙", "未来"]
        for element in modern_culture:
            if element in lyrics or element in keywords:
                references.append(f"modern_{element}")
        
        return references[:3] if references else ["universal"]
    
    async def build_story_arc(self, lyrics_analysis: Dict, emotion_curve: List[Dict],
                            symbolism: Dict, duration: float) -> Dict:
        """
        ストーリーアークの構築
        """
        # 三幕構成で構築
        act1_duration = duration * 0.25  # 導入
        act2_duration = duration * 0.5   # 展開
        act3_duration = duration * 0.25  # 結末
        
        story_arc = {
            "structure": "three_act",
            "acts": [
                {
                    "act": 1,
                    "name": "Setup",
                    "duration": act1_duration,
                    "description": "導入部 - 世界観と主人公の紹介",
                    "key_elements": self.extract_act1_elements(lyrics_analysis, symbolism),
                    "emotional_tone": self.get_emotional_tone(emotion_curve, 0, act1_duration)
                },
                {
                    "act": 2,
                    "name": "Confrontation",
                    "duration": act2_duration,
                    "description": "展開部 - 葛藤と成長",
                    "key_elements": self.extract_act2_elements(lyrics_analysis, symbolism),
                    "emotional_tone": self.get_emotional_tone(emotion_curve, act1_duration, act1_duration + act2_duration)
                },
                {
                    "act": 3,
                    "name": "Resolution",
                    "duration": act3_duration,
                    "description": "結末部 - 解決と新たな始まり",
                    "key_elements": self.extract_act3_elements(lyrics_analysis, symbolism),
                    "emotional_tone": self.get_emotional_tone(emotion_curve, act1_duration + act2_duration, duration)
                }
            ],
            "turning_points": [
                {
                    "time": act1_duration,
                    "description": "第一転換点 - 日常から非日常へ",
                    "visual_cue": "dramatic camera movement"
                },
                {
                    "time": act1_duration + act2_duration / 2,
                    "description": "中間点 - 最大の試練",
                    "visual_cue": "intense close-up"
                },
                {
                    "time": act1_duration + act2_duration,
                    "description": "第二転換点 - クライマックスへ",
                    "visual_cue": "epic wide shot"
                }
            ]
        }
        
        return story_arc
    
    def extract_act1_elements(self, analysis: Dict, symbolism: Dict) -> List[str]:
        """
        第一幕の要素を抽出
        """
        elements = ["world_building", "character_introduction"]
        
        if symbolism.get("central_symbols"):
            elements.append("symbol_introduction")
        if analysis.get("setting"):
            elements.append("setting_establishment")
        
        return elements
    
    def extract_act2_elements(self, analysis: Dict, symbolism: Dict) -> List[str]:
        """
        第二幕の要素を抽出
        """
        return ["conflict_development", "character_growth", "obstacle_confrontation", "relationship_dynamics"]
    
    def extract_act3_elements(self, analysis: Dict, symbolism: Dict) -> List[str]:
        """
        第三幕の要素を抽出
        """
        return ["climax", "resolution", "transformation", "new_beginning"]
    
    def get_emotional_tone(self, emotion_curve: List[Dict], start_time: float, 
                          end_time: float) -> str:
        """
        指定時間範囲の感情トーンを取得
        """
        relevant_emotions = [
            e for e in emotion_curve 
            if start_time <= e.get("time", 0) < end_time
        ]
        
        if not relevant_emotions:
            return "neutral"
        
        # 最も頻繁な感情を特定
        primary_emotions = [e.get("primary_emotion", "neutral") for e in relevant_emotions]
        most_common = max(set(primary_emotions), key=primary_emotions.count)
        
        return most_common
    
    async def generate_detailed_scenes(self, story_arc: Dict, lyrics_analysis: Dict,
                                      emotion_curve: List[Dict], symbolism: Dict,
                                      duration: float) -> List[Dict]:
        """
        詳細なシーン生成（2000-3000文字/シーン）
        """
        scenes = []
        scene_duration = 8  # 各シーン8秒
        num_scenes = int(duration / scene_duration)
        
        for i in range(num_scenes):
            scene_time = i * scene_duration
            act_number = self.determine_act(scene_time, story_arc)
            
            scene = await self.create_detailed_scene(
                scene_number=i + 1,
                scene_time=scene_time,
                scene_duration=scene_duration,
                act_number=act_number,
                story_arc=story_arc,
                lyrics_analysis=lyrics_analysis,
                emotion_curve=emotion_curve,
                symbolism=symbolism,
                total_scenes=num_scenes
            )
            
            scenes.append(scene)
        
        return scenes
    
    def determine_act(self, time: float, story_arc: Dict) -> int:
        """
        時間からアクト番号を決定
        """
        cumulative_time = 0
        for act in story_arc["acts"]:
            cumulative_time += act["duration"]
            if time < cumulative_time:
                return act["act"]
        return 3
    
    async def create_detailed_scene(self, scene_number: int, scene_time: float,
                                   scene_duration: int, act_number: int,
                                   story_arc: Dict, lyrics_analysis: Dict,
                                   emotion_curve: List[Dict], symbolism: Dict,
                                   total_scenes: int) -> Dict:
        """
        単一の詳細シーンを作成（2000-3000文字）
        """
        # 該当する感情ポイントを取得
        relevant_emotions = [
            e for e in emotion_curve
            if scene_time <= e.get("time", 0) < scene_time + scene_duration
        ]
        
        # シーンの役割を決定
        scene_role = self.determine_scene_role(scene_number, total_scenes, act_number)
        
        # 詳細な描写を生成
        detailed_description = await self.generate_scene_description(
            scene_number=scene_number,
            scene_role=scene_role,
            act_number=act_number,
            emotions=relevant_emotions,
            symbolism=symbolism,
            story_arc=story_arc
        )
        
        return {
            "scene_number": scene_number,
            "timestamp": f"{scene_time}-{scene_time + scene_duration}s",
            "act": act_number,
            "role": scene_role,
            "detailed_description": detailed_description,
            "emotion_points": relevant_emotions,
            "visual_elements": self.extract_visual_elements(detailed_description, symbolism),
            "camera_instructions": self.generate_camera_instructions(scene_role, act_number),
            "color_palette": self.determine_color_palette(relevant_emotions, symbolism),
            "lighting": self.determine_lighting_setup(scene_role, relevant_emotions),
            "effects": self.determine_special_effects(scene_role, act_number)
        }
    
    def determine_scene_role(self, scene_number: int, total_scenes: int, 
                            act_number: int) -> str:
        """
        シーンの役割を決定
        """
        position_ratio = scene_number / total_scenes
        
        if scene_number == 1:
            return "opening"
        elif scene_number == total_scenes:
            return "ending"
        elif position_ratio < 0.1:
            return "establishment"
        elif 0.45 < position_ratio < 0.55:
            return "midpoint"
        elif 0.7 < position_ratio < 0.8:
            return "climax_buildup"
        elif 0.8 < position_ratio < 0.9:
            return "climax"
        elif act_number == 1:
            return "setup"
        elif act_number == 2:
            return "development"
        else:
            return "resolution"
    
    async def generate_scene_description(self, **kwargs) -> str:
        """
        シーンの詳細な描写を生成（2000-3000文字）
        """
        template = """
        【シーン {scene_number}】
        
        ＜時間と空間の設定＞
        {time_space_description}
        
        ＜環境の詳細描写＞
        {environment_description}
        
        ＜登場要素と配置＞
        {elements_description}
        
        ＜動きとアクション＞
        {action_description}
        
        ＜感情表現と内面描写＞
        {emotion_description}
        
        ＜象徴的要素＞
        {symbolic_description}
        
        ＜音響設計＞
        {sound_description}
        
        ＜カメラワークと構図＞
        {camera_description}
        
        ＜照明と色彩＞
        {lighting_description}
        
        ＜特殊効果とポストプロダクション＞
        {effects_description}
        """
        
        # 各セクションの内容を生成
        descriptions = {
            "scene_number": kwargs["scene_number"],
            "time_space_description": self.generate_time_space_description(kwargs),
            "environment_description": self.generate_environment_description(kwargs),
            "elements_description": self.generate_elements_description(kwargs),
            "action_description": self.generate_action_description(kwargs),
            "emotion_description": self.generate_emotion_description(kwargs),
            "symbolic_description": self.generate_symbolic_description(kwargs),
            "sound_description": self.generate_sound_description(kwargs),
            "camera_description": self.generate_camera_description(kwargs),
            "lighting_description": self.generate_lighting_description(kwargs),
            "effects_description": self.generate_effects_description(kwargs)
        }
        
        return template.format(**descriptions)
    
    def generate_time_space_description(self, context: Dict) -> str:
        """
        時間と空間の設定の詳細描写（約200-300文字）
        """
        role = context.get("scene_role", "normal")
        
        descriptions = {
            "opening": "物語の始まりは、時間が止まったかのような静寂の中から始まります。朝靄が立ち込める都市の風景、まだ眠りから覚めきらない街並みが、これから始まる物語の舞台となります。空間は無限に広がり、可能性に満ちています。",
            "climax": "クライマックスの瞬間、時間は引き延ばされ、一秒が永遠のように感じられます。空間は収縮と拡張を繰り返し、感情の高まりと共に現実と非現実の境界が曖昧になっていきます。",
            "ending": "物語の終わりに向かって、時間はゆっくりと正常に戻っていきます。空間は新たな意味を持ち、始まりとは異なる、しかしより深い理解をもたらす風景へと変化しています。"
        }
        
        return descriptions.get(role, "時間は流れ続け、空間は変化し続けています。この瞬間もまた、大きな物語の一部として、独自の意味と美しさを持っています。")
    
    def generate_environment_description(self, context: Dict) -> str:
        """
        環境の詳細描写（約300-400文字）
        """
        return """
        環境は生きているかのように呼吸し、シーンの感情と共鳴しています。
        建物の窓は朝日を反射し、まるで無数の目が世界を見つめているかのようです。
        街路樹の葉がそよ風に揺れ、自然のリズムを刻んでいます。
        遠くから聞こえる都市の音—車のエンジン音、人々の話し声、鳥のさえずり—が
        複雑な音のタペストリーを織りなしています。
        空気には朝の新鮮さと、これから始まる一日への期待が漂っています。
        光と影のコントラストが、空間に深みと立体感を与え、
        観る者の視線を自然に導いていきます。
        """
    
    def generate_elements_description(self, context: Dict) -> str:
        """
        登場要素と配置の描写（約300-400文字）
        """
        return """
        画面の中央には主要な視覚要素が配置され、観客の注意を引きつけます。
        前景には動きのある要素—風に舞う紙片、歩く人々のシルエット—が
        深度と動きを演出しています。
        中景では物語の核心となる要素が展開し、
        背景は全体の雰囲気を支える壮大なキャンバスとなっています。
        各要素は黄金比に基づいて配置され、視覚的な調和を生み出しています。
        小道具や装飾的要素も意味を持ち、物語の層を深めています。
        全ての要素が有機的に結びつき、一つの完成された世界を構築しています。
        """
    
    def generate_action_description(self, context: Dict) -> str:
        """
        動きとアクションの描写（約300-400文字）
        """
        return """
        動きは流れるように始まり、徐々に加速していきます。
        カメラは被写体を追いかけ、時に先回りし、観客を物語の中へと引き込みます。
        人物の動作は自然でありながら、象徴的な意味を持ち、
        一つ一つのジェスチャーが感情を雄弁に語ります。
        環境要素も静止することなく、常に微細な動きを続け、
        シーン全体に生命力を与えています。
        動きのテンポは音楽と完璧に同期し、
        視覚と聴覚の調和が生まれています。
        アクションの頂点では、全ての要素が一つの瞬間に収束し、
        強烈な印象を残します。
        """
    
    def generate_emotion_description(self, context: Dict) -> str:
        """
        感情表現と内面描写（約300-400文字）
        """
        emotions = context.get("emotions", [])
        primary_emotion = emotions[0]["primary_emotion"] if emotions else "希望"
        
        return f"""
        このシーンに流れる感情は「{primary_emotion}」を中心に、
        複雑な感情の層を形成しています。
        表面的には穏やかに見える表情の奥に、
        激しい内面の葛藤が渦巻いています。
        瞳の輝きは希望を映し出し、
        微かな口元の動きは決意を物語っています。
        身体言語—肩の角度、手の位置、歩き方—全てが
        言葉にならない感情を表現しています。
        周囲の環境もまた、この感情と共鳴し、
        色彩や光の変化を通じて内面世界を外在化しています。
        観客は、これらの視覚的手がかりを通じて、
        登場人物の心の奥深くに触れることができます。
        """
    
    def generate_symbolic_description(self, context: Dict) -> str:
        """
        象徴的要素の描写（約200-300文字）
        """
        symbolism = context.get("symbolism", {})
        symbols = symbolism.get("central_symbols", [])
        
        symbol_text = symbols[0]["symbol"] if symbols else "光"
        
        return f"""
        このシーンの中心には「{symbol_text}」という象徴が配置されています。
        それは単なる視覚的要素を超えて、
        物語全体のテーマを体現する存在となっています。
        この象徴は様々な形で画面に現れ—
        時に直接的に、時に暗示的に—
        観客の無意識に働きかけます。
        色彩、形状、配置、すべてが計算され、
        深い意味の層を構築しています。
        伝統的な象徴性と現代的な解釈が融合し、
        普遍的でありながら新鮮な視覚体験を生み出しています。
        """
    
    def generate_sound_description(self, context: Dict) -> str:
        """
        音響設計の描写（約200-300文字）
        """
        return """
        音響設計は映像と完璧に調和し、感情の深度を増幅させます。
        環境音は現実感を与えながら、音楽的要素と融合し、
        独特の音響空間を創造しています。
        ダイアログやナレーションがある場合は、
        明瞭さを保ちながら感情的なニュアンスを伝えます。
        効果音は控えめながら効果的に使用され、
        アクションを強調し、転換点を際立たせます。
        音の遠近感、左右のバランス、周波数の分布、
        全てが立体的な音響体験を生み出し、
        観客を物語の世界に没入させます。
        """
    
    def generate_camera_description(self, context: Dict) -> str:
        """
        カメラワークと構図の描写（約200-300文字）
        """
        role = context.get("scene_role", "normal")
        
        camera_styles = {
            "opening": "確立ショットから始まり、ゆっくりとズームインしていく",
            "climax": "ダイナミックな動きと極端なアングルを組み合わせる",
            "ending": "ゆっくりとプルバックし、全体像を見せる"
        }
        
        style = camera_styles.get(role, "安定した動きで被写体を追う")
        
        return f"""
        カメラワークは「{style}」アプローチを採用しています。
        構図は三分割法を基本としながら、
        必要に応じて対称性や黄金比を活用しています。
        被写界深度は感情の焦点に応じて調整され、
        重要な要素を視覚的に強調します。
        カメラの動きは音楽のリズムと同期し、
        流れるような視覚体験を創造します。
        アングルの変化は物語の展開を予感させ、
        観客の期待と驚きのバランスを保ちます。
        """
    
    def generate_lighting_description(self, context: Dict) -> str:
        """
        照明と色彩の描写（約200-300文字）
        """
        return """
        照明デザインは自然光と人工光を巧みに組み合わせ、
        シーンの感情的トーンを確立しています。
        キーライトは主要な要素を照らし出し、
        フィルライトは影を和らげ、細部を見せます。
        バックライトは被写体を背景から分離させ、
        立体感と奥行きを演出します。
        色温度は場面の雰囲気に応じて調整され、
        暖色系と寒色系のバランスが
        視覚的な温度感を生み出しています。
        光と影のコントラストは、
        ドラマチックな瞬間を強調し、
        感情の起伏を視覚化します。
        """
    
    def generate_effects_description(self, context: Dict) -> str:
        """
        特殊効果とポストプロダクションの描写（約200-300文字）
        """
        return """
        ポストプロダクションでは、撮影された素材を芸術作品へと昇華させます。
        カラーグレーディングは全体の統一感を保ちながら、
        各シーンの独自性を引き出します。
        必要に応じてCGエレメントを追加し、
        現実を超えた表現を可能にします。
        パーティクルエフェクトや光のエフェクトは
        控えめながら効果的に使用され、
        魔法のような瞬間を演出します。
        トランジションは次のシーンへの期待を高め、
        物語の流れを途切れさせません。
        最終的な仕上げは、技術と芸術の完璧な融合を目指します。
        """
    
    def extract_visual_elements(self, description: str, symbolism: Dict) -> List[str]:
        """
        視覚要素を抽出
        """
        elements = []
        
        # シンボルから要素を追加
        if symbolism.get("central_symbols"):
            for symbol in symbolism["central_symbols"][:2]:
                elements.append(symbol.get("visual", "abstract_symbol"))
        
        # 色彩から要素を追加
        if symbolism.get("color_symbolism"):
            colors = symbolism["color_symbolism"].get("primary_colors", [])
            for color in colors[:2]:
                elements.append(f"{color}_element")
        
        # 自然要素を追加
        if symbolism.get("nature_elements"):
            landscape = symbolism["nature_elements"].get("landscape", [])
            elements.extend(landscape[:2])
        
        return elements if elements else ["abstract_visual"]
    
    def generate_camera_instructions(self, role: str, act: int) -> Dict:
        """
        カメラ指示を生成
        """
        instructions = {
            "opening": {
                "type": "establishing_shot",
                "movement": "slow_push_in",
                "angle": "wide",
                "focus": "soft_to_sharp"
            },
            "climax": {
                "type": "dynamic_sequence",
                "movement": "rapid_cuts_and_movements",
                "angle": "varied_extreme",
                "focus": "selective_dramatic"
            },
            "ending": {
                "type": "resolution_shot",
                "movement": "slow_pull_out",
                "angle": "wide_establishing",
                "focus": "deep_focus"
            }
        }
        
        default = {
            "type": "standard_coverage",
            "movement": "smooth_tracking",
            "angle": "eye_level",
            "focus": "standard"
        }
        
        return instructions.get(role, default)
    
    def determine_color_palette(self, emotions: List[Dict], symbolism: Dict) -> Dict:
        """
        カラーパレットを決定
        """
        palette = {
            "primary": [],
            "secondary": [],
            "accent": []
        }
        
        # 感情から色を決定
        for emotion in emotions[:2]:
            emotion_type = emotion.get("primary_emotion", "")
            if emotion_type == "喜び":
                palette["primary"].append("#FFD700")  # Gold
            elif emotion_type == "悲しみ":
                palette["primary"].append("#4169E1")  # Royal Blue
            elif emotion_type == "期待":
                palette["primary"].append("#FF69B4")  # Hot Pink
        
        # シンボリズムから色を追加
        if symbolism.get("color_symbolism"):
            colors = symbolism["color_symbolism"].get("primary_colors", [])
            color_map = {
                "赤": "#DC143C",
                "青": "#0000CD",
                "緑": "#228B22",
                "黄": "#FFD700",
                "紫": "#8B008B",
                "白": "#FFFFFF",
                "黒": "#000000"
            }
            
            for color in colors[:2]:
                if color in color_map:
                    palette["secondary"].append(color_map[color])
        
        # デフォルト色を確保
        if not palette["primary"]:
            palette["primary"] = ["#4A90E2", "#F5F5F5"]
        if not palette["secondary"]:
            palette["secondary"] = ["#7FBF7F", "#FFB347"]
        
        palette["accent"] = ["#FF6B6B", "#4ECDC4"]
        
        return palette
    
    def determine_lighting_setup(self, role: str, emotions: List[Dict]) -> Dict:
        """
        照明セットアップを決定
        """
        base_setup = {
            "key_light": {
                "intensity": 100,
                "color_temp": 5600,
                "angle": 45
            },
            "fill_light": {
                "intensity": 50,
                "color_temp": 5600,
                "angle": -30
            },
            "back_light": {
                "intensity": 75,
                "color_temp": 5600,
                "angle": 180
            }
        }
        
        # 役割に応じて調整
        if role == "climax":
            base_setup["key_light"]["intensity"] = 150
            base_setup["back_light"]["intensity"] = 100
        elif role == "ending":
            base_setup["key_light"]["color_temp"] = 3200  # Warmer
            base_setup["fill_light"]["intensity"] = 70
        
        # 感情に応じて色温度を調整
        if emotions:
            primary_emotion = emotions[0].get("primary_emotion", "")
            if primary_emotion in ["悲しみ", "恐れ"]:
                base_setup["key_light"]["color_temp"] = 6500  # Cooler
            elif primary_emotion in ["喜び", "期待"]:
                base_setup["key_light"]["color_temp"] = 4500  # Warmer
        
        return base_setup
    
    def determine_special_effects(self, role: str, act: int) -> List[str]:
        """
        特殊効果を決定
        """
        effects = []
        
        # 役割に応じた効果
        role_effects = {
            "opening": ["fade_in", "lens_flare", "depth_of_field"],
            "climax": ["motion_blur", "particle_effects", "time_remapping", "color_burst"],
            "ending": ["fade_out", "vignette", "soft_glow"],
            "establishment": ["atmospheric_haze", "subtle_particles"],
            "development": ["speed_ramping", "dynamic_transitions"]
        }
        
        effects.extend(role_effects.get(role, ["standard_color_correction"]))
        
        # アクトに応じた追加効果
        if act == 1:
            effects.append("establishing_atmosphere")
        elif act == 2:
            effects.append("tension_building_effects")
        elif act == 3:
            effects.append("resolution_effects")
        
        return effects[:5]  # 最大5つの効果
    
    async def analyze_with_claude(self, prompt: str) -> str:
        """
        Claudeで分析
        """
        try:
            message = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude analysis error: {e}")
            return None
    
    async def analyze_with_gpt4(self, prompt: str) -> str:
        """
        GPT-4で分析
        """
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "あなたは詩的な分析の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.7
            )
            return response.choices[0].message['content']
        except Exception as e:
            print(f"GPT-4 analysis error: {e}")
            return None
    
    def create_basic_analysis(self, lyrics: str) -> Dict:
        """
        基本的な分析（フォールバック）
        """
        return {
            "themes": ["universal_human_experience"],
            "emotions": ["mixed_feelings"],
            "imagery": ["abstract_visuals"],
            "structure": ["free_form"],
            "character": ["universal_protagonist"],
            "setting": ["timeless_space"]
        }