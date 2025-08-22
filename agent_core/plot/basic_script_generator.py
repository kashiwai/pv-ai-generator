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
        
        # APIが利用できない場合やエラーの場合はフォールバック
        if not script_content:
            if progress_callback:
                progress_callback(0.15, "📝 デモモードで生成中...")
            
            # より詳細なフォールバックスクリプトを生成
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
        
        # 各シーンの時間を明確に指定
        scene_list = "\n".join([f"シーン{i+1}: {i*8}-{(i+1)*8}秒" for i in range(num_scenes)])
        
        return f"""
PVの台本を作成してください。必ず{num_scenes}個のシーンすべてを作成してください。

【基本情報】
- タイトル: {title}
- キーワード: {keywords}
- 説明: {description}
- 雰囲気: {mood}
- 総シーン数: {num_scenes}個（必須）
- 各シーン: 8秒
- パターン: {pattern_type}
{character_desc}

【歌詞・メッセージ】
{lyrics[:1000] if lyrics else "（歌詞なし）"}

【作成指示】
{pattern_instructions.get(pattern_type, "")}

【必ず以下の{num_scenes}個のシーンをすべて作成してください】
{scene_list}

各シーンは必ず以下の形式で記述してください：

シーン[番号]: [開始時間]-[終了時間]秒
内容: [そのシーンのストーリー内容を500-1000文字で詳細に記述。視覚的で具体的な描写を含める]
キャラクター: [登場キャラクターの具体的な動作、表情、衣装など]
カメラワーク: [カメラの動き、アングル、構図を具体的に]
雰囲気: [そのシーンの雰囲気、色調、感情]

【重要な注意事項】
1. 必ず{num_scenes}個のシーンをすべて生成すること（省略禁止）
2. 各シーンは500-1000文字で具体的かつ詳細に記述
3. メインキャラクターは全シーンで同一人物として一貫性を保つ
4. Text-to-Video AIのために視覚的で具体的な描写を使用
5. シーンは時系列順に、ストーリーとして繋がるように
6. 各シーンで異なる展開や演出を入れて単調にならないように

必ずシーン1からシーン{num_scenes}まですべて生成してください。
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
        """フォールバック用の台本生成（デモモード）"""
        import time
        char_name = character_reference.get('name', '主人公') if character_reference else '主人公'
        
        # パターンごとのテンプレート
        scene_templates = {
            'story': [
                {'phase': '導入', 'camera': 'エスタブリッシングショット', 'action': '物語の舞台設定'},
                {'phase': '展開', 'camera': 'クローズアップ', 'action': 'キャラクターの感情表現'},
                {'phase': '転換', 'camera': 'ダイナミックな動き', 'action': '重要な出来事の発生'},
                {'phase': 'クライマックス', 'camera': 'インパクトのある構図', 'action': '最高潮の瞬間'},
                {'phase': '結末', 'camera': 'ゆっくりとしたパン', 'action': '物語の締めくくり'}
            ],
            'visual': [
                {'phase': 'ビジュアルインパクト', 'camera': 'ワイドショット', 'action': '印象的な映像'},
                {'phase': '色彩の遊び', 'camera': 'アーティスティック', 'action': '視覚的な美しさ'},
                {'phase': '動きの美学', 'camera': 'スローモーション', 'action': '優雅な動き'},
                {'phase': '光と影', 'camera': 'コントラスト強調', 'action': 'ドラマチックな演出'},
                {'phase': '幻想的な世界', 'camera': 'ドリーミーな表現', 'action': '非現実的な美'}
            ],
            'music': [
                {'phase': 'イントロ同期', 'camera': 'リズミカルな編集', 'action': '音楽の始まりに合わせて'},
                {'phase': 'ビート同期', 'camera': 'カット編集', 'action': 'リズムに合わせた動き'},
                {'phase': 'メロディ表現', 'camera': 'フロー感のある動き', 'action': '音楽の流れを視覚化'},
                {'phase': 'サビ演出', 'camera': 'ダイナミックな展開', 'action': '盛り上がりの表現'},
                {'phase': 'アウトロ', 'camera': 'フェードアウト', 'action': '余韻を残す終わり方'}
            ]
        }
        
        templates = scene_templates.get(pattern_type, scene_templates['story'])
        scenes_text = []
        
        for i in range(num_scenes):
            timestamp = f"{i*8}-{(i+1)*8}"
            template = templates[i % len(templates)]
            
            # より詳細な内容を生成（500-800文字）
            content = f"""
{template['phase']}のシーン。{title}の世界観を表現する重要な場面。
{char_name}が中心となり、{keywords}の要素を織り交ぜながら物語が展開していく。
{mood}な雰囲気の中、観客の心を掴む印象的な瞬間を創出する。
カメラは{template['camera']}を用いて、{template['action']}を効果的に表現。
光の使い方、色調、構図など、すべての要素が調和して一つの芸術作品を作り上げる。
このシーンでは特に{char_name}の内面や感情の変化を丁寧に描写し、
観客が共感できるような普遍的なテーマを扱う。
背景には{keywords}に関連する要素を配置し、世界観の深みを演出。
音楽との調和も重要で、{pattern_type}パターンの特徴を最大限に活かす。
"""
            
            scenes_text.append(f"""
シーン{i+1}: {timestamp}秒
内容: {content.strip()}
キャラクター: {char_name}が{template['action']}を行う
カメラワーク: {template['camera']}
雰囲気: {mood} - {template['phase']}
""")
            
            # 少し遅延を入れてリアル感を出す
            time.sleep(0.1)
        
        return "\n".join(scenes_text)
    
    def _parse_script_to_scenes(self, script_content: str, num_scenes: int,
                               scene_duration: int, pattern_type: str,
                               character_reference: Dict) -> List[Dict]:
        """生成されたスクリプトをシーンごとにパース（改善版）"""
        scenes = []
        
        # まず全シーンのデフォルト構造を作成
        for i in range(num_scenes):
            scenes.append({
                'scene_number': i + 1,
                'timestamp': f"{i*scene_duration}-{(i+1)*scene_duration}",
                'content': '',
                'character_action': '',
                'camera_work': '',
                'mood': ''
            })
        
        # スクリプトを行ごとに分割
        lines = script_content.split('\n')
        current_scene_idx = -1
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # シーンの開始を検出（シーン1、シーン2など）
            import re
            scene_match = re.match(r'シーン(\d+)[:\s]', line)
            if scene_match:
                scene_num = int(scene_match.group(1))
                if 1 <= scene_num <= num_scenes:
                    current_scene_idx = scene_num - 1
                    current_field = None
                    # タイムスタンプも更新（もし含まれていれば）
                    if '-' in line and '秒' in line:
                        timestamp_match = re.search(r'(\d+)-(\d+)', line)
                        if timestamp_match:
                            scenes[current_scene_idx]['timestamp'] = f"{timestamp_match.group(1)}-{timestamp_match.group(2)}"
                continue
            
            # 現在処理中のシーンがある場合
            if current_scene_idx >= 0:
                # 各フィールドを検出
                if line.startswith('内容:'):
                    current_field = 'content'
                    content = line[3:].strip()
                    if content:
                        scenes[current_scene_idx]['content'] = content
                elif line.startswith('キャラクター:'):
                    current_field = 'character_action'
                    content = line[7:].strip()
                    if content:
                        scenes[current_scene_idx]['character_action'] = content
                elif line.startswith('カメラワーク:') or line.startswith('カメラ:'):
                    current_field = 'camera_work'
                    content = line.split(':', 1)[-1].strip()
                    if content:
                        scenes[current_scene_idx]['camera_work'] = content
                elif line.startswith('雰囲気:'):
                    current_field = 'mood'
                    content = line[4:].strip()
                    if content:
                        scenes[current_scene_idx]['mood'] = content
                # 継続行の処理
                elif current_field and not any(line.startswith(prefix) for prefix in ['内容:', 'キャラクター:', 'カメラ', '雰囲気:']):
                    if current_field == 'content':
                        scenes[current_scene_idx]['content'] += ' ' + line
                    elif current_field == 'character_action':
                        scenes[current_scene_idx]['character_action'] += ' ' + line
                    elif current_field == 'camera_work':
                        scenes[current_scene_idx]['camera_work'] += ' ' + line
                    elif current_field == 'mood':
                        scenes[current_scene_idx]['mood'] += ' ' + line
        
        # 空のシーンを補完
        char_name = character_reference.get('name', '主人公') if character_reference else '主人公'
        for i, scene in enumerate(scenes):
            if not scene['content']:
                # シーン位置に応じた内容を生成
                if i == 0:
                    scene['content'] = f"オープニング。{char_name}が登場し、物語が始まる。{pattern_type}パターンに従った印象的な導入。"
                elif i == len(scenes) - 1:
                    scene['content'] = f"エンディング。{char_name}の物語がクライマックスを迎え、感動的な締めくくり。"
                else:
                    scene['content'] = f"シーン{i+1}。{char_name}の物語が展開。{pattern_type}パターンに応じた演出。"
            
            if not scene['character_action']:
                scene['character_action'] = f"{char_name}が中心となって動く"
            if not scene['camera_work']:
                scene['camera_work'] = "スタンダードショット"
            if not scene['mood']:
                scene['mood'] = "ノーマル"
        
        return scenes
    
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