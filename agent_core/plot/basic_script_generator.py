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
            # シーン番号を追加
            scene['scene_number'] = i + 1
            
            # ビデオプロンプトとMidjourneyプロンプトを生成
            scene['video_prompt'] = self._create_video_prompt(scene, character_reference)
            scene['visual_description'] = self._create_visual_prompt(scene, character_reference)
            
            # Midjourneyプロンプトを明示的に追加
            scene['midjourney_prompt'] = scene['visual_description']
            
            # ビジュアルプロンプトの短縮版も追加（UI表示用）
            scene['visual_prompt'] = scene['visual_description'][:200] + "..."
            
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
        
        # 空のシーンを補完（より詳細な内容で）
        char_name = character_reference.get('name', '主人公') if character_reference else '主人公'
        
        # シーン内容のテンプレート
        scene_contents = {
            'story': [
                f"オープニング。{char_name}が初めて登場。物語の世界観が明らかになる。カメラは広角で舞台全体を映し出し、{char_name}の存在感を際立たせる。",
                f"{char_name}の日常。普段の生活や環境が描かれる。親しみやすい表情や仕草で、観客との距離を縮める。",
                f"変化の兆し。{char_name}の周りで何かが起き始める。表情に微かな変化が現れ、物語が動き出す予感。",
                f"展開。{char_name}が新しい状況に直面。感情の揺れ動きが表情や動作に現れる。",
                f"深まる物語。{char_name}の内面が掘り下げられる。クローズアップで細かな表情の変化を捉える。",
                f"転換点。{char_name}にとって重要な瞬間。決意や覚悟が表情に表れる。",
                f"加速。物語のペースが上がり、{char_name}の動きも活発に。ダイナミックなカメラワーク。",
                f"葛藤。{char_name}が困難に直面。複雑な感情が交錯する表情を丁寧に描写。",
                f"決断。{char_name}が重要な選択をする。強い意志が瞳に宿る。",
                f"行動。{char_name}が決断に基づいて動く。力強い動作と確信に満ちた表情。",
                f"クライマックスへ。最高潮に向けて緊張が高まる。{char_name}の感情も最高潮に。",
                f"頂点。物語の最も重要な瞬間。{char_name}の全てが表現される。",
                f"解決。問題が解決に向かう。{char_name}の表情に安堵や達成感。",
                f"余韻。物語の締めくくり。{char_name}の新たな表情、成長した姿。",
                f"エンディング。{char_name}の物語が美しく終わる。観客の心に残る最後の表情。"
            ],
            'visual': [
                f"ビジュアルインパクト。{char_name}の美しさを最大限に引き出す構図と照明。",
                f"色彩の魔法。{char_name}を彩る豊かな色調。衣装や背景との調和。",
                f"光と影の演出。{char_name}の立体感を強調する照明効果。",
                f"動きの美学。{char_name}の優雅な動作をスローモーションで捉える。",
                f"表情のアート。{char_name}の微細な表情変化を芸術的に表現。",
                f"構図の妙。{char_name}を中心とした印象的なフレーミング。",
                f"テクスチャーの表現。{char_name}の衣装や髪の質感を詳細に描写。",
                f"空間の演出。{char_name}と背景の関係性を美しく表現。",
                f"時間の流れ。{char_name}の動きで時間の経過を表現。",
                f"幻想的な世界。{char_name}を夢のような雰囲気で包む。",
                f"コントラストの美。{char_name}を際立たせる明暗の対比。",
                f"シンメトリー。{char_name}を中心とした対称的な構図。",
                f"リズミカルな編集。{char_name}の動きが音楽と完全に同期。",
                f"感情の可視化。{char_name}の内面を視覚的に表現。",
                f"フィナーレ。{char_name}の美しさが最高潮に達する瞬間。"
            ],
            'music': [
                f"イントロ。音楽の始まりと共に{char_name}が登場。リズムに合わせた登場シーン。",
                f"ビート開始。{char_name}の動きが音楽のビートと同期。",
                f"メロディー展開。{char_name}の感情が音楽の流れと共鳴。",
                f"リズムの変化。{char_name}の動きも音楽に合わせて変化。",
                f"静かなパート。{char_name}の繊細な表情を音楽が引き立てる。",
                f"盛り上がり前。{char_name}の期待感が高まる表情。",
                f"サビ突入。{char_name}の感情が爆発。音楽と完全に一体化。",
                f"サビ継続。{char_name}の魅力が最大限に発揮される。",
                f"ブリッジ。{char_name}の新たな一面が音楽と共に現れる。",
                f"転調。音楽の変化と共に{char_name}の表情も変わる。",
                f"ラストサビへ。{char_name}の感情が再び高まる。",
                f"最高潮。音楽のクライマックスで{char_name}も最高の表情。",
                f"音楽の収束。{char_name}の動きもゆっくりと落ち着く。",
                f"アウトロ。{char_name}の余韻を残す表情。",
                f"フェードアウト。音楽と共に{char_name}の姿も美しく消えていく。"
            ]
        }
        
        # パターンに応じたコンテンツを選択
        pattern_contents = scene_contents.get(pattern_type, scene_contents['story'])
        
        for i, scene in enumerate(scenes):
            if not scene['content']:
                # 配列の範囲内で内容を取得
                if i < len(pattern_contents):
                    scene['content'] = pattern_contents[i]
                else:
                    # 配列を超えた場合は循環使用
                    scene['content'] = pattern_contents[i % len(pattern_contents)]
            
            if not scene['character_action']:
                if i == 0:
                    scene['character_action'] = f"{char_name}が優雅に登場"
                elif i == len(scenes) - 1:
                    scene['character_action'] = f"{char_name}が感動的なフィナーレ"
                else:
                    scene['character_action'] = f"{char_name}が魅力的に動く"
            
            if not scene['camera_work']:
                camera_options = ["ワイドショット", "ミディアムショット", "クローズアップ", 
                                "パン", "ドリー", "トラッキング", "クレーン"]
                scene['camera_work'] = camera_options[i % len(camera_options)]
            
            if not scene['mood']:
                mood_options = ["明るい", "優しい", "ドラマチック", "幻想的", 
                              "情熱的", "穏やか", "神秘的"]
                scene['mood'] = mood_options[i % len(mood_options)]
        
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
        """Midjourney用の詳細なビジュアルプロンプトを生成"""
        
        # キャラクター描写
        char_desc = ""
        if character_reference:
            char_desc = f"""beautiful Japanese woman, 25 years old, {character_reference.get('appearance', 'elegant')}, 
            {character_reference.get('features', 'professional look')}, """
        
        # シーンの詳細な視覚的描写を生成
        scene_number = scene.get('scene_number', 1)
        scene_content = scene.get('content', '')
        
        # シーンタイプに応じた視覚要素
        visual_elements = {
            1: "establishing shot, wide angle, golden hour lighting",
            2: "medium shot, soft natural lighting, bokeh background",
            3: "dynamic angle, dramatic lighting, motion blur",
            4: "close-up shot, emotional expression, rim lighting",
            5: "aerial view, sunset colors, cinematic composition",
            6: "tracking shot, vibrant colors, depth of field",
            7: "low angle, powerful stance, volumetric lighting",
            8: "intimate framing, warm tones, soft focus",
            9: "action sequence, high contrast, sharp details",
            10: "sweeping panorama, epic scale, god rays",
            11: "artistic composition, color grading, lens flare",
            12: "emotional climax, dramatic shadows, backlight",
            13: "resolution scene, balanced lighting, serene atmosphere",
            14: "closing shot, sunset silhouette, nostalgic mood",
            15: "final frame, perfect lighting, memorable composition"
        }
        
        # 基本的な視覚要素を取得
        base_visual = visual_elements.get(scene_number, "cinematic shot, professional lighting")
        
        # ムードに応じた追加要素
        mood = scene.get('mood', 'normal')
        mood_elements = {
            '明るい': "bright colors, cheerful atmosphere, soft shadows",
            '優しい': "pastel colors, soft lighting, dreamy quality",
            'ドラマチック': "high contrast, dramatic shadows, intense colors",
            '幻想的': "ethereal lighting, fantasy elements, magical atmosphere",
            '情熱的': "warm colors, dynamic composition, intense mood",
            '穏やか': "calm atmosphere, balanced colors, peaceful scene",
            '神秘的': "mysterious lighting, fog effects, enigmatic mood"
        }
        
        mood_visual = mood_elements.get(mood, "balanced lighting, natural colors")
        
        # カメラワークの詳細
        camera = scene.get('camera_work', 'standard')
        camera_details = {
            'ワイドショット': "wide angle lens, full body shot, environmental context",
            'ミディアムショット': "medium focal length, waist-up framing, clear details",
            'クローズアップ': "close-up lens, facial details, emotional focus",
            'パン': "panning motion, horizontal movement, dynamic flow",
            'ドリー': "dolly shot, smooth forward movement, depth",
            'トラッキング': "tracking shot, following subject, motion",
            'クレーン': "crane shot, vertical movement, revealing composition"
        }
        
        camera_visual = camera_details.get(camera, "standard framing, clear composition")
        
        # 完全なプロンプトを構築
        midjourney_prompt = f"""{char_desc}{scene_content[:150]}, 
{base_visual}, {mood_visual}, {camera_visual},
photorealistic, ultra detailed, professional photography, 
award winning composition, masterpiece quality,
8k resolution, sharp focus, perfect lighting,
--ar 16:9 --v 6 --style raw --quality 2"""
        
        return midjourney_prompt.strip()
    
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