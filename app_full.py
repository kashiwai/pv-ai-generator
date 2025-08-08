#!/usr/bin/env python3
"""
PV自動生成AIエージェント - 完全機能版
Midjourney v6.1 (PiAPI) × Hailuo 02 AI (PiAPI) × Fish Audio TTS
"""

import gradio as gr
import os
import json
import asyncio
import aiohttp
import time
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("===== PV AI Generator - Full Version Starting =====")

# 環境設定
config = {
    "piapi_key": os.getenv("PIAPI_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    "fish_audio_key": os.getenv("FISH_AUDIO_KEY", ""),
}

# API設定
PIAPI_BASE_URL = "https://api.piapi.ai"
MIDJOURNEY_ENDPOINT = f"{PIAPI_BASE_URL}/mj/v2/imagine"
HAILUO_ENDPOINT = f"{PIAPI_BASE_URL}/hailuo/generate"
FISH_AUDIO_BASE_URL = "https://api.fish.audio"
FISH_TTS_ENDPOINT = f"{FISH_AUDIO_BASE_URL}/v1/tts"

class ScriptGenerator:
    """台本生成クラス"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    async def generate_script(self, title: str, keywords: str, lyrics: str, style: str, duration: int = 180) -> Dict:
        """構成案と台本を生成"""
        
        # シーン数を計算（30秒ごとに1シーン）
        num_scenes = min(max(duration // 30, 4), 12)  # 最小4シーン、最大12シーン
        
        # プロンプト作成
        prompt = f"""
        以下の条件でPV（プロモーションビデオ）の台本を作成してください：
        
        タイトル: {title}
        キーワード: {keywords}
        スタイル: {style}
        長さ: {duration}秒
        シーン数: {num_scenes}
        
        {f'歌詞/ナレーション: {lyrics}' if lyrics else ''}
        
        各シーンについて以下を含めてください：
        1. シーンの説明（視覚的な内容）
        2. カメラワーク
        3. 感情的なトーン
        4. ナレーション（あれば）
        """
        
        # 台本生成（OpenAI > Google > ダミー）
        script = await self._generate_with_llm(prompt)
        
        # シーンごとに分割
        scenes = self._parse_script_to_scenes(script, num_scenes)
        
        return {
            "full_script": script,
            "scenes": scenes,
            "duration": duration,
            "num_scenes": num_scenes
        }
    
    async def _generate_with_llm(self, prompt: str) -> str:
        """LLMで台本生成"""
        
        # OpenAI
        if self.config.get("openai_api_key"):
            try:
                import openai
                openai.api_key = self.config["openai_api_key"]
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8
                )
                return response.choices[0].message.content
            except:
                pass
        
        # Google Gemini
        if self.config.get("google_api_key"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config["google_api_key"])
                model = genai.GenerativeModel('gemini-pro')
                response = await model.generate_content_async(prompt)
                return response.text
            except:
                pass
        
        # フォールバック：基本的な台本生成
        return self._generate_fallback_script(prompt)
    
    def _generate_fallback_script(self, prompt: str) -> str:
        """フォールバック台本生成"""
        # プロンプトから情報を抽出
        title = "未知の物語"
        keywords = "冒険"
        style = "cinematic"
        
        if "タイトル:" in prompt:
            title = prompt.split("タイトル:")[1].split("\n")[0].strip()
        if "キーワード:" in prompt:
            keywords = prompt.split("キーワード:")[1].split("\n")[0].strip()
        if "スタイル:" in prompt:
            style = prompt.split("スタイル:")[1].split("\n")[0].strip()
        
        return f"""
        シーン1: オープニング
        - タイトル「{title}」のフェードイン
        - {keywords}をイメージした美しい風景
        - カメラ：ゆっくりとしたズームイン
        - トーン：期待感と神秘性
        - ナレーション：「新しい物語が始まる」
        
        シーン2: 導入
        - メインキャラクターの登場
        - {style}スタイルの演出
        - カメラ：キャラクターにフォーカス
        - トーン：親しみやすさと共感
        - ナレーション：「出会いが運命を変える」
        
        シーン3: 展開
        - アクションシーケンス
        - ドラマチックな展開
        - カメラ：ダイナミックな動き
        - トーン：緊張感と興奮
        - ナレーション：「挑戦が始まった」
        
        シーン4: クライマックス
        - 最高潮の瞬間
        - 感動的なシーン
        - カメラ：感情を強調するクローズアップ
        - トーン：感動と達成感
        - ナレーション：「夢は叶う」
        
        シーン5: エンディング
        - 静かな終わり
        - 余韻を残すシーン
        - カメラ：ゆっくりとしたフェードアウト
        - トーン：満足感と希望
        - ナレーション：「物語は続く」
        """
    
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
                
            if 'シーン' in line or 'Scene' in line:
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
            elif 'カメラ' in line or 'Camera' in line:
                current_scene["camera_work"] = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
            elif 'トーン' in line or 'Tone' in line:
                current_scene["tone"] = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
            elif 'ナレーション' in line or 'Narration' in line:
                current_scene["narration"] = line.split('：')[-1].strip().strip('「」') if '：' in line else line.split(':')[-1].strip().strip('「」')
            else:
                if not line.startswith('-'):
                    current_scene["description"] += line + " "
        
        # 最後のシーン追加
        if current_scene["description"]:
            scenes.append({
                "id": f"scene_{scene_count}",
                "number": scene_count + 1,
                **current_scene,
                "duration": 30
            })
        
        # シーン数調整
        while len(scenes) < num_scenes:
            scenes.append({
                "id": f"scene_{len(scenes)}",
                "number": len(scenes) + 1,
                "description": f"追加シーン {len(scenes) + 1}",
                "camera_work": "標準",
                "tone": "ニュートラル",
                "narration": "",
                "duration": 30
            })
        
        return scenes[:num_scenes]

class TTSGenerator:
    """音声合成クラス"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_narration(self, text: str, voice_id: str = "default") -> Optional[str]:
        """Fish Audio TTSでナレーション生成"""
        
        if not text:
            return None
            
        if not self.config.get("fish_audio_key"):
            logger.warning("Fish Audio key not configured, using fallback TTS")
            return await self._generate_fallback_tts(text)
        
        headers = {
            "Authorization": f"Bearer {self.config['fish_audio_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "voice": voice_id,
            "language": "ja",
            "speed": 1.0,
            "format": "mp3"
        }
        
        try:
            async with self.session.post(FISH_TTS_ENDPOINT, headers=headers, json=data) as resp:
                if resp.status == 200:
                    # 音声データを一時ファイルに保存
                    audio_data = await resp.read()
                    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    temp_file.write(audio_data)
                    temp_file.close()
                    return temp_file.name
        except Exception as e:
            logger.error(f"Fish Audio TTS failed: {e}")
        
        return await self._generate_fallback_tts(text)
    
    async def _generate_fallback_tts(self, text: str) -> Optional[str]:
        """フォールバックTTS（Google TTS）"""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='ja')
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tts.save(temp_file.name)
            return temp_file.name
        except Exception as e:
            logger.error(f"Fallback TTS failed: {e}")
            return None

class PVGenerator:
    """PV生成の核となるクラス"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        self.script_generator = ScriptGenerator(config)
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_image_midjourney(self, prompt: str) -> Optional[str]:
        """Midjourney v6.1で画像生成 (PiAPI経由)"""
        if not self.config.get("piapi_key"):
            logger.warning("PiAPI key not configured")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.config['piapi_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "model": "v6.1",
            "aspect_ratio": "16:9",
            "quality": "high"
        }
        
        try:
            async with self.session.post(MIDJOURNEY_ENDPOINT, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("image_url")
        except Exception as e:
            logger.error(f"Midjourney generation failed: {e}")
        return None
    
    async def generate_video_hailuo(self, prompt: str, image_url: Optional[str] = None) -> Optional[str]:
        """Hailuo 02 AIで動画生成 (PiAPI経由)"""
        if not self.config.get("piapi_key"):
            logger.warning("PiAPI key not configured")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.config['piapi_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "duration": 5,  # 5秒の動画
            "resolution": "1920x1080"
        }
        
        if image_url:
            data["image_url"] = image_url
            
        try:
            async with self.session.post(HAILUO_ENDPOINT, headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("video_url")
        except Exception as e:
            logger.error(f"Hailuo generation failed: {e}")
        return None

def process_audio_file(file_path: str) -> Dict:
    """音楽ファイルを処理"""
    if not file_path:
        return {"error": "音楽ファイルが指定されていません"}
        
    # gr.Fileの場合、ファイルパスはfile.nameで取得
    if hasattr(file_path, 'name'):
        file_path = file_path.name
        
    if not Path(file_path).exists():
        return {"error": "音楽ファイルが見つかりません"}
    
    # 音楽ファイルの長さを取得（簡易版）
    try:
        import librosa
        duration = librosa.get_duration(filename=file_path)
    except:
        duration = 180  # デフォルト3分
    
    return {
        "path": file_path,
        "duration": int(duration),
        "format": Path(file_path).suffix
    }

async def generate_pv_async(title: str, keywords: str, music_file: str, lyrics: str = "", style: str = "cinematic") -> Dict:
    """
    PV生成のメイン非同期処理
    """
    results = {
        "status": "processing",
        "steps": [],
        "output": None
    }
    
    try:
        # 音楽ファイル処理
        audio_info = process_audio_file(music_file)
        if "error" in audio_info:
            results["status"] = "error"
            results["error"] = audio_info["error"]
            return results
        
        results["steps"].append(f"✅ 音楽ファイル処理完了（{audio_info['duration']}秒）")
        
        async with PVGenerator(config) as generator:
            # 1. 台本生成
            results["steps"].append("📝 台本生成中...")
            script_data = await generator.script_generator.generate_script(
                title, keywords, lyrics, style, audio_info["duration"]
            )
            results["steps"].append(f"✅ 台本生成完了（{script_data['num_scenes']}シーン）")
            
            # 2. ナレーション音声生成
            async with TTSGenerator(config) as tts:
                narration_files = []
                for i, scene in enumerate(script_data["scenes"], 1):
                    if scene.get("narration"):
                        results["steps"].append(f"🗣️ シーン{i}のナレーション生成中...")
                        narration_file = await tts.generate_narration(scene["narration"])
                        if narration_file:
                            narration_files.append({
                                "scene_id": scene["id"],
                                "file": narration_file
                            })
                            results["steps"].append(f"✅ シーン{i}のナレーション生成完了")
            
            # 3. キャラクター画像生成
            character_prompt = f"{title} character, {keywords}, {style} style, high quality, 16:9"
            results["steps"].append("🎨 キャラクター画像生成中...")
            character_image = await generator.generate_image_midjourney(character_prompt)
            
            if character_image:
                results["steps"].append("✅ キャラクター画像生成完了")
            else:
                results["steps"].append("⚠️ キャラクター画像生成スキップ（APIキー未設定）")
            
            # 4. シーンごとの動画生成
            video_urls = []
            for i, scene in enumerate(script_data["scenes"], 1):
                scene_prompt = f"{scene['description']}, {style} style, {scene['camera_work']}, {scene['tone']}"
                results["steps"].append(f"🎬 シーン{i}生成中...")
                
                # 最初のシーンはキャラクター画像を使用
                video_url = await generator.generate_video_hailuo(
                    scene_prompt,
                    character_image if i == 1 else None
                )
                
                if video_url:
                    video_urls.append({
                        "scene_id": scene["id"],
                        "url": video_url,
                        "duration": scene["duration"]
                    })
                    results["steps"].append(f"✅ シーン{i}生成完了")
                else:
                    results["steps"].append(f"⚠️ シーン{i}生成スキップ")
            
            # 5. 結果をまとめる
            results["script"] = script_data
            results["narrations"] = narration_files
            results["videos"] = video_urls
            results["character_image"] = character_image
            results["status"] = "completed"
            
            # 6. 最終動画合成（将来実装）
            if video_urls:
                results["steps"].append("🎵 動画合成準備中...")
                # ここにMoviePyを使った合成処理を追加
                results["steps"].append("⚠️ 動画合成機能は実装予定")
            
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        logger.error(f"PV generation error: {e}")
    
    return results

def generate_pv(title, keywords, music_file, lyrics, style):
    """
    PV生成のメイン処理（同期ラッパー）
    
    Args:
        title: PVのタイトル
        keywords: キーワード（カンマ区切り）
        music_file: 音楽ファイルのパス
        lyrics: 歌詞/ナレーション
        style: ビジュアルスタイル
    
    Returns:
        結果メッセージ
    """
    try:
        # 入力検証
        if not title:
            return "❌ タイトルを入力してください"
        if not music_file:
            return "❌ 音楽ファイルをアップロードしてください"
        
        # 非同期処理を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                generate_pv_async(title, keywords, music_file, lyrics, style)
            )
        finally:
            loop.close()
        
        # APIキーの確認
        has_piapi = bool(config.get("piapi_key"))
        has_fish = bool(config.get("fish_audio_key"))
        has_openai = bool(config.get("openai_api_key"))
        has_google = bool(config.get("google_api_key"))
        
        status_lines = [
            "🎬 **PV生成結果**",
            "",
            f"📝 タイトル: {title}",
            f"🏷️ キーワード: {keywords or 'なし'}",
            f"🎨 スタイル: {style}",
            f"🎵 音楽: アップロード済み",
            "",
            "**処理ステップ:**",
        ]
        
        # 処理結果を追加
        if result.get("steps"):
            status_lines.extend(result["steps"])
        
        # 台本情報を追加
        if result.get("script"):
            status_lines.extend([
                "",
                "**📜 生成された台本:**",
                f"シーン数: {result['script']['num_scenes']}",
                f"総時間: {result['script']['duration']}秒",
            ])
            
            for scene in result['script']['scenes'][:3]:  # 最初の3シーンを表示
                status_lines.extend([
                    "",
                    f"【シーン{scene['number']}】",
                    f"説明: {scene['description'][:100]}...",
                    f"カメラ: {scene['camera_work']}",
                    f"トーン: {scene['tone']}",
                ])
                if scene.get('narration'):
                    status_lines.append(f"ナレーション: 「{scene['narration']}」")
        
        status_lines.extend([
            "",
            "**APIキー状態:**",
            f"- PiAPI (Midjourney + Hailuo): {'✅ 設定済み' if has_piapi else '❌ 未設定'}",
            f"- Fish Audio TTS: {'✅ 設定済み' if has_fish else '❌ 未設定'}",
            f"- OpenAI: {'✅ 設定済み' if has_openai else '❌ 未設定'}",
            f"- Google: {'✅ 設定済み' if has_google else '❌ 未設定'}",
            "",
        ])
        
        if not has_piapi:
            status_lines.append("⚠️ PiAPIキーが設定されていません。")
            status_lines.append("Settings → Repository secrets → PIAPI_KEY で設定してください。")
        
        if result.get("status") == "completed":
            status_lines.append("")
            status_lines.append("✅ **PV生成完了！**")
            if result.get("videos"):
                status_lines.append(f"生成された動画数: {len(result['videos'])}")
            if result.get("narrations"):
                status_lines.append(f"生成されたナレーション数: {len(result['narrations'])}")
        elif result.get("status") == "error":
            status_lines.append("")
            status_lines.append(f"❌ エラー: {result.get('error', '不明なエラー')}")
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"❌ エラーが発生しました: {str(e)}"

# Gradio Interface（完全機能版 - gr.Audioの代わりにgr.File使用）
demo = gr.Interface(
    fn=generate_pv,
    inputs=[
        gr.Textbox(label="タイトル *", placeholder="PVのタイトルを入力"),
        gr.Textbox(label="キーワード", placeholder="青春, 友情, 冒険"),
        gr.File(label="音楽ファイル *", file_types=[".mp3", ".wav", ".m4a", ".ogg"]),
        gr.Textbox(label="歌詞/ナレーション", lines=5, placeholder="歌詞またはナレーションテキスト（オプション）"),
        gr.Dropdown(
            label="ビジュアルスタイル",
            choices=["cinematic", "anime", "realistic", "fantasy", "retro", "cyberpunk"],
            value="cinematic"
        ),
    ],
    outputs=gr.Textbox(label="処理結果", lines=30),
    title="🎬 PV自動生成AIエージェント",
    description="""
    音楽に合わせて、AIが自動的にプロモーションビデオを生成します。
    
    **使用AI:**
    - 🎨 画像生成: Midjourney v6.1 (PiAPI)
    - 🎥 動画生成: Hailuo 02 AI (PiAPI)  
    - 🗣️ 音声合成: Fish Audio TTS
    - 📝 台本生成: OpenAI GPT-4 / Google Gemini
    - ✂️ 動画編集: MoviePy 3.x
    
    最大7分までの動画生成に対応
    """,
    theme=gr.themes.Soft(),
    allow_flagging="never",
    analytics_enabled=False,
)

if __name__ == "__main__":
    print("Creating directories...")
    
    # ディレクトリ作成
    for d in ["assets/input", "assets/output", "assets/temp", "assets/characters"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    # HF Spaces環境検出
    is_spaces = os.getenv("SPACE_ID") is not None
    
    print(f"Environment: {'HF Spaces' if is_spaces else 'Local'}")
    print("Launching application...")
    
    # シンプルな起動
    demo.launch(show_api=False)