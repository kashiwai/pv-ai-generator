"""
詳細スクリプト生成モジュール
各シーンごとに2000-3000文字の詳細な描写を生成
Text-to-Video AIに最適化されたプロンプトを作成
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
import openai
import anthropic
import google.generativeai as genai
from pathlib import Path

class DetailedScriptWriter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.openai_key = config.get("openai_api_key")
        self.anthropic_key = config.get("anthropic_api_key")
        self.google_key = config.get("google_api_key")
        self.character_reference = None  # キャラクター参照情報
        
        # API初期化
        if self.openai_key:
            openai.api_key = self.openai_key
        if self.anthropic_key:
            self.claude_client = anthropic.Anthropic(api_key=self.anthropic_key)
        if self.google_key:
            genai.configure(api_key=self.google_key)
    
    async def generate_detailed_script(self, 
                                      basic_script: Dict,
                                      duration: float,
                                      scene_duration: int = 8,
                                      character_reference: Dict = None,
                                      progress_callback = None) -> Dict[str, Any]:
        """
        基本台本から詳細スクリプトを生成（500-1000文字/シーン）
        
        Args:
            basic_script: 基本的な台本情報
            duration: 動画の総時間（秒）
            scene_duration: 1シーンあたりの秒数
            character_reference: キャラクター参照情報
            progress_callback: 進捗を通知するコールバック関数
        
        Returns:
            詳細スクリプト情報（500-1000文字/シーン）
        """
        # キャラクター参照を保存
        if character_reference:
            self.character_reference = character_reference
        # シーン数を計算
        num_scenes = int(duration / scene_duration)
        
        # タイムラインに基づいてシーンを分割
        timeline_scenes = self.split_scenes_by_time(basic_script, num_scenes, scene_duration)
        
        # 各シーンの詳細スクリプトを生成
        detailed_scenes = []
        for i, scene in enumerate(timeline_scenes):
            # 進捗を通知
            if progress_callback:
                progress = (i + 1) / len(timeline_scenes)
                progress_callback(progress, f"シーン {i+1}/{len(timeline_scenes)} を生成中...")
            
            detailed_scene = await self.generate_scene_detail(
                scene, i + 1, num_scenes
            )
            detailed_scenes.append(detailed_scene)
        
        return {
            "version": "2.4.0",
            "type": "text_to_video_script",
            "total_duration": duration,
            "scene_duration": scene_duration,
            "num_scenes": num_scenes,
            "scenes": detailed_scenes,
            "metadata": {
                "characters": basic_script.get("characters", []),
                "style": basic_script.get("style", "cinematic"),
                "mood": basic_script.get("mood", "normal")
            }
        }
    
    def split_scenes_by_time(self, script: Dict, num_scenes: int, 
                            scene_duration: int) -> List[Dict]:
        """
        時間軸に基づいてシーンを分割
        """
        scenes = []
        existing_scenes = script.get("scenes", [])
        
        for i in range(num_scenes):
            start_time = i * scene_duration
            end_time = (i + 1) * scene_duration
            
            # 既存のシーンから該当時間のものを探す
            matched_scene = None
            for scene in existing_scenes:
                scene_start = scene.get("timestamp", 0)
                if start_time <= scene_start < end_time:
                    matched_scene = scene
                    break
            
            if matched_scene:
                scenes.append({
                    "scene_number": i + 1,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": scene_duration,
                    "content": matched_scene.get("content", ""),
                    "visual_description": matched_scene.get("visual_description", ""),
                    "mood": matched_scene.get("mood", "normal")
                })
            else:
                # 新しいシーンを作成
                scenes.append({
                    "scene_number": i + 1,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": scene_duration,
                    "content": "",
                    "visual_description": "",
                    "mood": "normal"
                })
        
        return scenes
    
    async def generate_scene_detail(self, scene: Dict, scene_num: int, 
                                   total_scenes: int) -> Dict[str, Any]:
        """
        単一シーンの詳細スクリプトを生成（500-1000文字）
        """
        prompt = self.create_detail_prompt(scene, scene_num, total_scenes)
        
        # 優先順位: Claude > GPT-4 > Gemini
        detailed_script = None
        
        if self.anthropic_key:
            detailed_script = await self.generate_with_claude(prompt)
        elif self.openai_key:
            detailed_script = await self.generate_with_gpt4(prompt)
        elif self.google_key:
            detailed_script = await self.generate_with_gemini(prompt)
        else:
            detailed_script = self.generate_fallback_script(scene)
        
        # Text-to-Video用のプロンプトを生成
        video_prompt = self.create_video_prompt(detailed_script)
        
        return {
            "scene_number": scene_num,
            "timestamp": f"{scene['start_time']}-{scene['end_time']}s",
            "duration": scene['duration'],
            "detailed_script": detailed_script,
            "video_prompt": video_prompt,
            "technical_parameters": {
                "camera_movement": self.determine_camera_movement(scene_num, total_scenes),
                "lighting": self.determine_lighting(scene),
                "effects": self.determine_effects(scene),
                "transitions": self.determine_transitions(scene_num, total_scenes)
            }
        }
    
    def create_detail_prompt(self, scene: Dict, scene_num: int, 
                            total_scenes: int) -> str:
        """
        詳細スクリプト生成用のプロンプトを作成
        """
        position = "opening" if scene_num <= 2 else "ending" if scene_num >= total_scenes - 1 else "middle"
        
        # キャラクター情報を作成
        character_description = ""
        if self.character_reference:
            character_description = f"""
        
        【重要】メインキャラクター情報：
        {self.character_reference.get('description', '')}
        - 性別: {self.character_reference.get('gender', '未指定')}
        - 年齢: {self.character_reference.get('age', '未指定')}
        - 外見特徴: {self.character_reference.get('appearance', '未指定')}
        - 服装: {self.character_reference.get('clothing', '未指定')}
        
        ※このキャラクターを必ず全シーンに登場させ、一貫性を保ってください。
        ※同一人物として明確に描写し、外見の詳細を毎回含めてください。
        """
        
        return f"""
        以下のシーンについて、500-1000文字の詳細なスクリプトを日本語で作成してください。
        
        シーン番号: {scene_num}/{total_scenes}
        時間: {scene['start_time']}-{scene['end_time']}秒
        位置: {position}
        基本内容: {scene.get('content', '')}
        視覚的説明: {scene.get('visual_description', '')}
        雰囲気: {scene.get('mood', 'normal')}
        {character_description}
        
        以下の要素を簡潔に含めてください：
        
        1. **環境と雰囲気** (150-200文字)
           - 場所、時間帯、天候
           - 全体的な色調と光の状態
        
        2. **登場人物と動作** (150-200文字)
           - メインキャラクターの外見を必ず詳細に描写
           - 同一人物であることを明確にする
           - 具体的な動作とポーズ
        
        3. **カメラワークと構図** (100-150文字)
           - カメラの動き（パン、ズーム、固定など）
           - アングルと構図
        
        4. **視覚効果と演出** (100-150文字)
           - 使用する効果（フィルター、トランジション）
           - 演出のポイント
        
        重要：
        1. Text-to-Video AIのために、具体的で視覚的な描写を心がける
        2. 文字数は必ず500-1000文字以内に収める
        3. メインキャラクターは必ず同一人物として描写し、全シーンで一貫性を保つ
        """
    
    async def generate_with_claude(self, prompt: str) -> str:
        """
        Claude 3で詳細スクリプトを生成
        """
        try:
            message = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1500,
                temperature=0.8,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude generation error: {e}")
            return None
    
    async def generate_with_gpt4(self, prompt: str) -> str:
        """
        GPT-4で詳細スクリプトを生成
        """
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "あなたは映像制作の専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8
            )
            return response.choices[0].message['content']
        except Exception as e:
            print(f"GPT-4 generation error: {e}")
            return None
    
    async def generate_with_gemini(self, prompt: str) -> str:
        """
        Geminiで詳細スクリプトを生成
        """
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return None
    
    def generate_fallback_script(self, scene: Dict) -> str:
        """
        フォールバック用の詳細スクリプト（500-1000文字）
        """
        # キャラクター情報を取得
        character_desc = ""
        if self.character_reference:
            character_desc = self.character_reference.get('description', '20代後半の若者')
        else:
            character_desc = "20代後半の若者"
            
        return f"""
        【シーン {scene['scene_number']}】
        時間: {scene['start_time']}-{scene['end_time']}秒
        
        ＜環境と雰囲気＞
        現代的な都市空間。朝の柔らかな光がビルのガラス面に反射し、都市全体を金色に染める。
        澄んだ空に薄い雲が流れ、カフェからコーヒーの香りが漂う。街の音が都市のリズムを刻む。
        
        ＜登場人物と動作＞
        メインキャラクター（{character_desc}）がビジネススーツ姿で登場。
        同一人物としての特徴を保ち、表情には希望と不安が混在。
        自信に満ちた歩き方で前進し、時折立ち止まって深呼吸。建物の入口で一瞬躊躇い、決意を胸に扉を開ける。
        
        ＜カメラワークと構図＞
        後ろ姿から始まり、ゆっくり回り込んで正面ショットへ。主人公の動きを追うトラッキングショット。
        扉が閉まる瞬間にフェードアウト。
        
        ＜視覚効果と演出＞
        暖色系のカラーグレーディングで朝の光を強調。レンズフレアを適度に使用。
        クロスフェードで次のシーンへスムーズに移行。希望に満ちたBGMと環境音をミックス。
        
        このシーンは物語の始まりを象徴し、メインキャラクターの新たな挑戦を表現。
        観客に共感と期待感を抱かせる演出を目指す。同一人物が全シーンを通して登場。
        """
    
    def create_video_prompt(self, detailed_script: str) -> str:
        """
        Text-to-Video AI用のプロンプトを生成
        """
        # 詳細スクリプトから重要な要素を抽出
        # キャラクター描写を強調
        
        # 最初の500文字を要約として使用
        summary = detailed_script[:500] if len(detailed_script) > 500 else detailed_script
        
        # キャラクター参照を追加
        if self.character_reference:
            character_note = f"\n\n[IMPORTANT: Main character must be the same person throughout all scenes: {self.character_reference.get('description', '')}]"
            summary += character_note
        
        return f"""
        High quality cinematic video generation:
        
        {summary}
        
        Technical requirements:
        - Resolution: 1920x1080
        - Frame rate: 30fps
        - Duration: 8 seconds
        - Style: Cinematic, professional
        - Lighting: Natural, realistic
        - Camera: Smooth movement
        - Color: Warm tones
        
        Ensure temporal consistency and smooth transitions.
        """
    
    def determine_camera_movement(self, scene_num: int, total_scenes: int) -> str:
        """
        シーン番号に基づいてカメラムーブメントを決定
        """
        if scene_num == 1:
            return "establishing_shot_slow_zoom_in"
        elif scene_num == total_scenes:
            return "slow_zoom_out_fade"
        elif scene_num % 3 == 0:
            return "dynamic_tracking"
        elif scene_num % 2 == 0:
            return "smooth_pan"
        else:
            return "static_with_subtle_movement"
    
    def determine_lighting(self, scene: Dict) -> str:
        """
        シーンの雰囲気に基づいて照明を決定
        """
        mood = scene.get("mood", "normal")
        lighting_map = {
            "期待感": "golden_hour_warm",
            "展開": "natural_daylight",
            "高揚": "dramatic_contrast",
            "余韻": "soft_twilight",
            "normal": "balanced_natural"
        }
        return lighting_map.get(mood, "balanced_natural")
    
    def determine_effects(self, scene: Dict) -> List[str]:
        """
        シーンに適用する効果を決定
        """
        effects = []
        mood = scene.get("mood", "normal")
        
        if mood == "期待感":
            effects.extend(["lens_flare", "warm_glow"])
        elif mood == "高揚":
            effects.extend(["motion_blur", "dynamic_particles"])
        elif mood == "余韻":
            effects.extend(["soft_focus", "vignette"])
        
        return effects
    
    def determine_transitions(self, scene_num: int, total_scenes: int) -> str:
        """
        シーン間のトランジションを決定
        """
        if scene_num == total_scenes:
            return "fade_to_black"
        elif scene_num % 5 == 0:
            return "creative_wipe"
        elif scene_num % 3 == 0:
            return "cross_dissolve"
        else:
            return "cut"
    
    async def export_for_text_to_video(self, detailed_script: Dict,
                                      output_path: Path) -> Path:
        """
        Text-to-Video AI用にスクリプトをエクスポート
        """
        export_data = {
            "version": detailed_script["version"],
            "metadata": detailed_script["metadata"],
            "scenes": []
        }
        
        for scene in detailed_script["scenes"]:
            export_data["scenes"].append({
                "scene_number": scene["scene_number"],
                "timestamp": scene["timestamp"],
                "video_prompt": scene["video_prompt"],
                "technical_parameters": scene["technical_parameters"]
            })
        
        output_file = output_path / "text_to_video_script.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_file