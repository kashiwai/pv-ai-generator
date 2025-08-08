#!/usr/bin/env python3
"""
PV自動生成AIエージェント - 完全機能版
"""

import gradio as gr
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

# コアモジュールをインポート
try:
    from core import ScriptGenerator, PVGenerator
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("Warning: Core modules not available")

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("===== PV AI Generator Starting =====")

# 環境設定
config = {
    # PiAPI統合キー
    "piapi_key": os.getenv("PIAPI_KEY", ""),
    
    # 個別APIキー（PiAPIキーがない場合の代替）
    "midjourney_api_key": os.getenv("MIDJOURNEY_API_KEY", ""),
    "hailuo_api_key": os.getenv("HAILUO_API_KEY", ""),
    
    # LLM APIキー
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    
    # 音声合成
    "fish_audio_key": os.getenv("FISH_AUDIO_KEY", ""),
    
    # その他の動画生成API
    "veo3_api_key": os.getenv("VEO3_API_KEY", ""),
    "sora_api_key": os.getenv("SORA_API_KEY", ""),
}

def process_music_file(file_obj):
    """音楽ファイルを処理"""
    if not file_obj:
        return None
    
    try:
        # Gradioのファイルオブジェクトからパスを取得
        if hasattr(file_obj, 'name'):
            return file_obj.name
        return file_obj
    except:
        return None

def get_audio_duration(file_path: str) -> int:
    """音楽ファイルの長さを取得"""
    try:
        # 簡易的な長さ取得（デフォルト3分）
        return 180
    except:
        return 180

def generate_pv_with_music(title, keywords, music_file, lyrics, style):
    """
    音楽付きPV生成のメイン処理
    """
    try:
        # 入力検証
        if not title:
            return "❌ タイトルを入力してください", None
        
        # 音楽ファイル処理
        music_path = process_music_file(music_file)
        if music_path:
            audio_duration = get_audio_duration(music_path)
        else:
            audio_duration = 180  # デフォルト3分
        
        # APIキーの確認
        has_piapi = bool(config.get("piapi_key"))
        has_midjourney = bool(config.get("midjourney_api_key"))
        has_hailuo = bool(config.get("hailuo_api_key"))
        has_fish = bool(config.get("fish_audio_key"))
        has_openai = bool(config.get("openai_api_key"))
        has_google = bool(config.get("google_api_key"))
        
        # 画像・動画生成が可能かチェック
        can_generate_images = has_piapi or has_midjourney
        can_generate_videos = has_piapi or has_hailuo
        
        status_lines = [
            "🎬 **PV生成処理**",
            "",
            f"📝 タイトル: {title}",
            f"🏷️ キーワード: {keywords or 'なし'}",
            f"🎨 スタイル: {style}",
            f"🎵 音楽: {'アップロード済み' if music_path else 'なし'}",
            f"📜 歌詞: {'あり' if lyrics else 'なし'}",
            f"⏱️ 長さ: {audio_duration}秒",
            "",
        ]
        
        # コアモジュールが利用可能な場合は実際に処理
        if CORE_AVAILABLE and (can_generate_images or can_generate_videos):
            status_lines.append("**処理開始:**")
            status_lines.append("")
            
            # 1. 台本生成
            status_lines.append("📝 台本生成中...")
            script_gen = ScriptGenerator(config)
            script_data = script_gen.generate_script(
                title, keywords, lyrics, style, audio_duration
            )
            status_lines.append(f"✅ 台本生成完了（{script_data['num_scenes']}シーン）")
            
            # 台本の一部を表示
            for scene in script_data['scenes'][:2]:  # 最初の2シーン
                status_lines.append("")
                status_lines.append(f"【シーン{scene['number']}】")
                status_lines.append(f"説明: {scene['description'][:50]}...")
                if scene.get('narration'):
                    status_lines.append(f"ナレーション: 「{scene['narration']}」")
            
            # 2. PV生成
            status_lines.append("")
            status_lines.append("🎬 PV生成処理中...")
            pv_gen = PVGenerator(config)
            result = pv_gen.generate_pv(
                title, keywords, music_path, lyrics, style, script_data
            )
            
            # 結果を表示
            if result.get('steps'):
                status_lines.extend(result['steps'])
            
            if result.get('status') == 'completed':
                status_lines.append("")
                status_lines.append("✅ **PV生成完了！**")
                if result.get('output_path'):
                    status_lines.append(f"💾 出力: {result['output_path']}")
                    # ビデオを返す
                    return "\n".join(status_lines), result['output_path']
            
            # クリーンアップ
            pv_gen.cleanup()
            
        else:
            # APIキー状態を表示
            status_lines.extend([
                "**APIキー状態:**",
                f"- PiAPI (統合): {'✅ 設定済み' if has_piapi else '❌ 未設定'}",
                f"- Midjourney (個別): {'✅ 設定済み' if has_midjourney else '❌ 未設定'}",
                f"- Hailuo (個別): {'✅ 設定済み' if has_hailuo else '❌ 未設定'}",
                f"- Fish Audio TTS: {'✅ 設定済み' if has_fish else '❌ 未設定'}",
                f"- OpenAI: {'✅ 設定済み' if has_openai else '❌ 未設定'}",
                f"- Google: {'✅ 設定済み' if has_google else '❌ 未設定'}",
                "",
                f"📸 画像生成: {'✅ 利用可能' if can_generate_images else '❌ 利用不可'}",
                f"🎥 動画生成: {'✅ 利用可能' if can_generate_videos else '❌ 利用不可'}",
                "",
            ])
        
            if not can_generate_images and not can_generate_videos:
                status_lines.append("⚠️ 画像・動画生成のAPIキーが設定されていません。")
                status_lines.append("")
                status_lines.append("以下のいずれかを設定してください:")
                status_lines.append("【統合API（推奨）】")
                status_lines.append("- PIAPI_KEY: PiAPI統合キー（Midjourney + Hailuo）")
                status_lines.append("")
                status_lines.append("【個別API】")
                status_lines.append("- MIDJOURNEY_API_KEY: Midjourney直接アクセス")
                status_lines.append("- HAILUO_API_KEY: Hailuo直接アクセス")
                status_lines.append("")
                status_lines.append("Settings → Repository secrets で設定")
            elif not CORE_AVAILABLE:
                status_lines.append("⚠️ コアモジュールが読み込まれていません。")
                status_lines.append("システムを再起動してください。")
        
        return "\n".join(status_lines), None
        
    except Exception as e:
        logger.error(f"PV generation error: {e}")
        return f"❌ エラーが発生しました: {str(e)}", None

# Gradio Interface
with gr.Blocks(title="PV自動生成AIエージェント", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 PV自動生成AIエージェント
    
    音楽に合わせて、AIが自動的にプロモーションビデオを生成します。
    
    **使用AI:**
    - 🎨 画像生成: Midjourney v6.1 (PiAPI)
    - 🎥 動画生成: Hailuo 02 AI (PiAPI)  
    - 🗣️ 音声合成: Fish Audio TTS
    - 📝 台本生成: OpenAI GPT-4 / Google Gemini
    """)
    
    with gr.Row():
        with gr.Column():
            title_input = gr.Textbox(
                label="タイトル *",
                placeholder="PVのタイトルを入力"
            )
            keywords_input = gr.Textbox(
                label="キーワード",
                placeholder="青春, 友情, 冒険"
            )
            lyrics_input = gr.Textbox(
                label="歌詞/ナレーション",
                lines=5,
                placeholder="歌詞またはナレーションテキスト（オプション）"
            )
            style_input = gr.Dropdown(
                label="ビジュアルスタイル",
                choices=["cinematic", "anime", "realistic", "fantasy", "retro", "cyberpunk"],
                value="cinematic"
            )
            
            gr.Markdown("🎵 **音楽ファイル** (MP3/WAV/M4A)")
            with gr.Row():
                music_input = gr.Audio(
                    label="音楽アップロード",
                    type="filepath",
                    elem_id="music_upload"
                )
            
            generate_btn = gr.Button("🚀 PV生成開始", variant="primary", size="lg")
        
        with gr.Column():
            output = gr.Textbox(
                label="処理結果",
                lines=15,
                max_lines=25
            )
            video_output = gr.Video(
                label="生成されたPV",
                visible=False
            )
    
    def update_video_visibility(text, video):
        """ビデオ出力の表示を更新"""
        if video:
            return gr.update(visible=True)
        return gr.update(visible=False)
    
    generate_btn.click(
        fn=generate_pv_with_music,
        inputs=[title_input, keywords_input, music_input, lyrics_input, style_input],
        outputs=[output, video_output]
    ).then(
        fn=update_video_visibility,
        inputs=[output, video_output],
        outputs=video_output
    )
    
    gr.Markdown("""
    ---
    ### 📌 使い方
    1. PVのタイトルを入力
    2. キーワードを追加（オプション）
    3. 歌詞やナレーションを入力（オプション）
    4. ビジュアルスタイルを選択
    5. 「PV生成開始」ボタンをクリック
    
    ### ⚙️ APIキー設定
    Settings → Repository secrets から以下のキーを設定:
    - `PIAPI_KEY`: PiAPI統合キー（Midjourney + Hailuo）
    - `FISH_AUDIO_KEY`: Fish Audio TTSキー
    - `OPENAI_API_KEY`: OpenAI APIキー（オプション）
    - `GOOGLE_API_KEY`: Google APIキー（オプション）
    """)

if __name__ == "__main__":
    print("Creating directories...")
    
    # ディレクトリ作成
    for d in ["assets/input", "assets/output", "assets/temp", "assets/characters"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    # HF Spaces環境検出
    is_spaces = os.getenv("SPACE_ID") is not None
    
    print(f"Environment: {'HF Spaces' if is_spaces else 'Local'}")
    print("Launching application...")
    
    # 起動
    if is_spaces:
        demo.queue()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_api=False
        )
    else:
        demo.launch(show_api=False)