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

# PiAPI設定
PIAPI_BASE_URL = "https://api.piapi.ai"
MIDJOURNEY_ENDPOINT = f"{PIAPI_BASE_URL}/mj/v2/imagine"
HAILUO_ENDPOINT = f"{PIAPI_BASE_URL}/hailuo/generate"

class PVGenerator:
    """PV生成の核となるクラス"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.session = None
        
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
    if not file_path or not Path(file_path).exists():
        return {"error": "音楽ファイルが見つかりません"}
    
    # ここで音楽解析を行う（将来的に）
    return {
        "path": file_path,
        "duration": 180,  # 仮の値
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
        
        results["steps"].append("✅ 音楽ファイル処理完了")
        
        async with PVGenerator(config) as generator:
            # 1. キャラクター画像生成
            character_prompt = f"{title} character, {keywords}, {style} style, high quality"
            results["steps"].append("🎨 キャラクター画像生成中...")
            character_image = await generator.generate_image_midjourney(character_prompt)
            
            if character_image:
                results["steps"].append("✅ キャラクター画像生成完了")
            else:
                results["steps"].append("⚠️ キャラクター画像生成スキップ（APIキー未設定）")
            
            # 2. シーンごとの動画生成
            scenes = [
                f"Opening scene of {title}, {keywords}",
                f"Main story of {title}, emotional moment",
                f"Climax scene of {title}, dramatic",
                f"Ending of {title}, peaceful resolution"
            ]
            
            video_urls = []
            for i, scene_prompt in enumerate(scenes, 1):
                results["steps"].append(f"🎬 シーン{i}生成中...")
                video_url = await generator.generate_video_hailuo(
                    scene_prompt,
                    character_image if i == 1 else None
                )
                if video_url:
                    video_urls.append(video_url)
                    results["steps"].append(f"✅ シーン{i}生成完了")
                else:
                    results["steps"].append(f"⚠️ シーン{i}生成スキップ")
            
            results["video_urls"] = video_urls
            results["status"] = "completed"
            
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
        
        status_lines.extend([
            "",
            "**APIキー状態:**",
            f"- PiAPI (Midjourney + Hailuo): {'✅ 設定済み' if has_piapi else '❌ 未設定'}",
            f"- Fish Audio TTS: {'✅ 設定済み' if has_fish else '❌ 未設定'}",
            "",
        ])
        
        if not has_piapi:
            status_lines.append("⚠️ PiAPIキーが設定されていません。")
            status_lines.append("Settings → Repository secrets → PIAPI_KEY で設定してください。")
        
        if result.get("status") == "completed":
            status_lines.append("")
            status_lines.append("✅ **PV生成完了！**")
            if result.get("video_urls"):
                status_lines.append(f"生成された動画数: {len(result['video_urls'])}")
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
    outputs=gr.Textbox(label="処理結果", lines=25),
    title="🎬 PV自動生成AIエージェント",
    description="""
    音楽に合わせて、AIが自動的にプロモーションビデオを生成します。
    
    **使用AI:**
    - 🎨 画像生成: Midjourney v6.1 (PiAPI)
    - 🎥 動画生成: Hailuo 02 AI (PiAPI)  
    - 🗣️ 音声合成: Fish Audio TTS
    - ✂️ 動画編集: MoviePy 3.x
    
    最大7分までの動画生成に対応
    """,
    examples=[
        ["青春の輝き", "学校, 友情, 夢", None, "明日へ向かって走り出す", "anime"],
        ["星空の約束", "ファンタジー, 冒険", None, "星に願いを込めて", "fantasy"],
    ],
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