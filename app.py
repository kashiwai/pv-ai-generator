#!/usr/bin/env python3
"""
PV自動生成AIエージェント - 安定版
"""

import gradio as gr
import os
from pathlib import Path

print("===== PV AI Generator Starting =====")

# 環境設定
config = {
    "piapi_key": os.getenv("PIAPI_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    "fish_audio_key": os.getenv("FISH_AUDIO_KEY", ""),
}

def generate_pv(title, keywords, lyrics, style):
    """
    PV生成のメイン処理
    """
    try:
        # 入力検証
        if not title:
            return "❌ タイトルを入力してください"
        
        # APIキーの確認
        has_piapi = bool(config.get("piapi_key"))
        has_fish = bool(config.get("fish_audio_key"))
        has_openai = bool(config.get("openai_api_key"))
        has_google = bool(config.get("google_api_key"))
        
        status_lines = [
            "🎬 **PV生成システム**",
            "",
            f"📝 タイトル: {title}",
            f"🏷️ キーワード: {keywords or 'なし'}",
            f"🎨 スタイル: {style}",
            f"📜 歌詞: {'あり' if lyrics else 'なし'}",
            "",
            "**処理フロー:**",
            "1. 📝 台本生成",
            "2. 🎨 キャラクター画像生成 (Midjourney v6.1)",
            "3. 🗣️ ナレーション音声合成 (Fish Audio)",
            "4. 🎬 シーン動画生成 (Hailuo 02 AI)",
            "5. 🎵 動画合成 (MoviePy)",
            "",
            "**APIキー状態:**",
            f"- PiAPI (Midjourney + Hailuo): {'✅ 設定済み' if has_piapi else '❌ 未設定'}",
            f"- Fish Audio TTS: {'✅ 設定済み' if has_fish else '❌ 未設定'}",
            f"- OpenAI: {'✅ 設定済み' if has_openai else '❌ 未設定'}",
            f"- Google: {'✅ 設定済み' if has_google else '❌ 未設定'}",
            "",
        ]
        
        if not has_piapi:
            status_lines.append("⚠️ PiAPIキーが設定されていません。")
            status_lines.append("Settings → Repository secrets → PIAPI_KEY で設定してください。")
            status_lines.append("")
            status_lines.append("PiAPIで利用可能:")
            status_lines.append("- Midjourney v6.1 (画像生成)")
            status_lines.append("- Hailuo 02 AI (動画生成)")
        else:
            status_lines.append("✅ PV生成準備完了！")
            status_lines.append("")
            status_lines.append("⚠️ 注意: 音楽ファイルのアップロード機能は")
            status_lines.append("技術的な制限により一時的に無効化されています。")
            status_lines.append("完全版は近日実装予定です。")
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"❌ エラーが発生しました: {str(e)}"

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
            generate_btn = gr.Button("🚀 PV生成開始", variant="primary")
        
        with gr.Column():
            output = gr.Textbox(
                label="処理結果",
                lines=20,
                max_lines=30
            )
    
    generate_btn.click(
        fn=generate_pv,
        inputs=[title_input, keywords_input, lyrics_input, style_input],
        outputs=output
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