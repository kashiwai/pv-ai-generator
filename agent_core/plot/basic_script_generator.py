"""
基本台本生成モジュール（リアルタイム進捗表示対応）
OpenAI、Claude、Gemini APIを使用して実際の台本を生成
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime

class BasicScriptGenerator:
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
    
    async def generate_script(self, 
                            title: str,
                            keywords: str,
                            description: str,
                            mood: str,
                            lyrics: str,
                            duration: float,
                            pattern_type: str = "story",
                            character_reference: Dict = None,
                            progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        実際のAI APIを使用して台本を生成
        
        Args:
            title: PVのタイトル
            keywords: キーワード（カンマ区切り）
            description: PVの説明
            mood: 雰囲気
            lyrics: 歌詞
            duration: 動画の長さ（秒）
            pattern_type: 台本のパターン（story/visual/music）
            character_reference: キャラクター参照情報
            progress_callback: 進捗を通知するコールバック関数
        
        Returns:
            生成された台本データ
        """
        # シーン数を計算（8秒ごと）
        scene_duration = 8
        num_scenes = int(duration / scene_duration)
        
        # 進捗通知
        if progress_callback:
            progress_callback(0.05, f"📝 {pattern_type}パターンで台本を生成開始...")
        
        # プロンプトを作成
        prompt = self._create_script_prompt(
            title=title,
            keywords=keywords,
            description=description,
            mood=mood,
            lyrics=lyrics,
            num_scenes=num_scenes,
            pattern_type=pattern_type,
            character_reference=character_reference
        )
        
        # 進捗通知
        if progress_callback:
            progress_callback(0.1, "🤖 AI APIを呼び出し中...")
        
        # AI APIを呼び出し（優先順位: Claude > GPT-4 > Gemini）
        script_content = None
        
        if self.anthropic_key:
            if progress_callback:
                progress_callback(0.15, "🤖 Claude 3で生成中...")
            script_content = await self._generate_with_claude(prompt)
        elif self.openai_key:
            if progress_callback:
                progress_callback(0.15, "🤖 GPT-4で生成中...")
            script_content = await self._generate_with_gpt4(prompt)
        elif self.google_key:
            if progress_callback:
                progress_callback(0.15, "🤖 Geminiで生成中...")
            script_content = await self._generate_with_gemini(prompt)
        else:
            if progress_callback:
                progress_callback(0.15, "⚠️ APIキーなし、フォールバック生成...")
            script_content = self._generate_fallback_script(
                title, keywords, mood, num_scenes, pattern_type, character_reference
            )
        
        # スクリプトをパース
        if progress_callback:
            progress_callback(0.7, "📋 台本を構造化中...")
        
        scenes = self._parse_script_to_scenes(
            script_content, 
            num_scenes, 
            scene_duration,
            pattern_type,
            character_reference
        )
        
        # 各シーンのビジュアルプロンプトを生成
        if progress_callback:
            progress_callback(0.8, "🎨 ビジュアルプロンプトを生成中...")
        
        for i, scene in enumerate(scenes):
            scene['video_prompt'] = self._create_video_prompt(scene, character_reference)
            scene['visual_description'] = self._create_visual_prompt(scene, character_reference)
            
            # シーンごとの進捗更新
            if progress_callback:
                progress = 0.8 + (0.2 * (i + 1) / len(scenes))
                progress_callback(progress, f"🎬 シーン {i+1}/{len(scenes)} を最適化中...")
        
        # 完了
        if progress_callback:
            progress_callback(1.0, "✅ 台本生成完了！")
        
        return {
            "type": pattern_type,
            "title": title,
            "total_duration": duration,
            "num_scenes": num_scenes,
            "scenes": scenes,
            "generated_at": datetime.now().isoformat(),
            "ai_model": self._get_used_model()
        }
    
    def _create_script_prompt(self, title: str, keywords: str, description: str,
                            mood: str, lyrics: str, num_scenes: int,
                            pattern_type: str, character_reference: Dict) -> str:
        """台本生成用のプロンプトを作成"""
        
        # キャラクター情報を追加
        character_desc = ""
        if character_reference:
            character_desc = f"""
【重要】メインキャラクター設定：
- 名前: {character_reference.get('name', '主人公')}
- 性別: {character_reference.get('gender', '未指定')}
- 年齢: {character_reference.get('age', '20代')}
- 外見: {character_reference.get('appearance', 'ビジネスカジュアル')}
- 特徴: {character_reference.get('features', '明るく前向きな性格')}

このキャラクターを全てのシーンに登場させ、一貫性を保ってください。
"""
        
        # パターンごとの指示
        pattern_instructions = {
            "story": "ストーリー性を重視し、起承転結のある展開にしてください。",
            "visual": "ビジュアル的なインパクトを重視し、印象的な映像表現を中心にしてください。",
            "music": "音楽との同期を重視し、リズムや歌詞に合わせた演出を考えてください。"
        }
        
        return f"""
PVの台本を作成してください。

【基本情報】
- タイトル: {title}
- キーワード: {keywords}
- 説明: {description}
- 雰囲気: {mood}
- 総シーン数: {num_scenes}
- パターン: {pattern_type}
{character_desc}

【歌詞・メッセージ】
{lyrics[:500] if lyrics else "（歌詞なし）"}

【作成指示】
{pattern_instructions.get(pattern_type, "")}

各シーンごとに以下の形式で作成してください（各シーン500-1000文字）：

シーン1: [タイムスタンプ]
内容: [そのシーンのストーリー内容を500-1000文字で詳細に記述]
キャラクター: [登場キャラクターの動作や表情]
カメラワーク: [カメラの動きや構図]
雰囲気: [そのシーンの雰囲気や感情]

重要：
1. 各シーンは500-1000文字で具体的に記述
2. メインキャラクターは必ず同一人物として描写
3. Text-to-Video AIが理解しやすい視覚的な描写
4. 前後のシーンとの自然な繋がり
"""
    
    async def _generate_with_claude(self, prompt: str) -> str:
        """Claude 3で台本を生成"""
        try:
            message = self.claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.8,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude generation error: {e}")
            return None
    
    async def _generate_with_gpt4(self, prompt: str) -> str:
        """GPT-4で台本を生成"""
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "あなたは優秀な映像ディレクターです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.8
            )
            return response.choices[0].message['content']
        except Exception as e:
            print(f"GPT-4 generation error: {e}")
            return None
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Geminiで台本を生成"""
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
    
    def _generate_fallback_script(self, title: str, keywords: str, mood: str,
                                 num_scenes: int, pattern_type: str,
                                 character_reference: Dict) -> str:
        """フォールバック用の台本生成"""
        char_name = character_reference.get('name', '主人公') if character_reference else '主人公'
        
        scenes_text = []
        for i in range(num_scenes):
            timestamp = f"{i*8}-{(i+1)*8}"
            
            if i == 0:
                content = f"オープニング。{title}の世界が始まる。{char_name}が登場し、{keywords}の雰囲気を醸し出す。"
            elif i == num_scenes - 1:
                content = f"エンディング。{char_name}の物語が一旦の終わりを迎える。{mood}な雰囲気で締めくくる。"
            else:
                content = f"シーン{i+1}。{char_name}の物語が展開。{pattern_type}パターンに従って演出。"
            
            scenes_text.append(f"""
シーン{i+1}: {timestamp}秒
内容: {content}
キャラクター: {char_name}が中心となって動く
カメラワーク: {pattern_type}に適したカメラワーク
雰囲気: {mood}
""")
        
        return "\n".join(scenes_text)
    
    def _parse_script_to_scenes(self, script_content: str, num_scenes: int,
                               scene_duration: int, pattern_type: str,
                               character_reference: Dict) -> List[Dict]:
        """生成されたスクリプトをシーンごとにパース"""
        scenes = []
        
        # スクリプトを行ごとに分割
        lines = script_content.split('\n')
        current_scene = {}
        scene_number = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # シーンの開始を検出
            if 'シーン' in line and ':' in line:
                # 前のシーンを保存
                if current_scene and 'content' in current_scene:
                    scenes.append(current_scene)
                
                scene_number += 1
                # タイムスタンプを抽出
                timestamp_part = line.split(':')[-1].strip()
                if '-' in timestamp_part:
                    start, end = timestamp_part.replace('秒', '').split('-')
                    timestamp = f"{start.strip()}-{end.strip()}"
                else:
                    timestamp = f"{(scene_number-1)*scene_duration}-{scene_number*scene_duration}"
                
                current_scene = {
                    'scene_number': scene_number,
                    'timestamp': timestamp,
                    'content': '',
                    'character_action': '',
                    'camera_work': '',
                    'mood': ''
                }
            
            # 各要素を抽出
            elif '内容:' in line:
                current_scene['content'] = line.split('内容:')[-1].strip()
            elif 'キャラクター:' in line:
                current_scene['character_action'] = line.split('キャラクター:')[-1].strip()
            elif 'カメラワーク:' in line or 'カメラ:' in line:
                current_scene['camera_work'] = line.split(':')[-1].strip()
            elif '雰囲気:' in line:
                current_scene['mood'] = line.split('雰囲気:')[-1].strip()
            elif current_scene and 'content' in current_scene and line:
                # 内容の続きを追加
                current_scene['content'] += ' ' + line
        
        # 最後のシーンを追加
        if current_scene and 'content' in current_scene:
            scenes.append(current_scene)
        
        # シーンが不足している場合は補完
        while len(scenes) < num_scenes:
            scene_number = len(scenes) + 1
            scenes.append({
                'scene_number': scene_number,
                'timestamp': f"{(scene_number-1)*scene_duration}-{scene_number*scene_duration}",
                'content': f"シーン{scene_number}の内容（{pattern_type}パターン）",
                'character_action': 'キャラクターのアクション',
                'camera_work': 'スタンダードショット',
                'mood': 'ノーマル'
            })
        
        return scenes[:num_scenes]
    
    def _create_video_prompt(self, scene: Dict, character_reference: Dict) -> str:
        """Text-to-Video用のプロンプトを生成"""
        char_desc = ""
        if character_reference:
            char_desc = f"Main character: {character_reference.get('description', '')}. "
        
        return f"""
{char_desc}{scene.get('content', '')[:200]}
Camera: {scene.get('camera_work', 'standard shot')}
Mood: {scene.get('mood', 'normal')}
High quality, cinematic, 8 seconds
"""
    
    def _create_visual_prompt(self, scene: Dict, character_reference: Dict) -> str:
        """Midjourney用のビジュアルプロンプトを生成"""
        char_desc = ""
        if character_reference:
            char_desc = f"{character_reference.get('description', '')}, "
        
        return f"""
{char_desc}{scene.get('content', '')[:100]}, 
{scene.get('mood', 'normal')} mood, 
cinematic lighting, high quality, 
--ar 16:9 --v 6
"""
    
    def _get_used_model(self) -> str:
        """使用したAIモデルを返す"""
        if self.anthropic_key:
            return "Claude 3 Opus"
        elif self.openai_key:
            return "GPT-4 Turbo"
        elif self.google_key:
            return "Gemini Pro"
        else:
            return "Fallback"