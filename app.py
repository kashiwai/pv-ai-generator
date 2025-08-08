#!/usr/bin/env python3
"""
PV自動生成AIエージェント - 安定版（ファイルアップローダー使用）
"""

import gradio as gr
import os
import shutil
import tempfile
from pathlib import Path

print("===== PV AI Generator (Stable) Starting =====")

# 環境設定
config = {
    "piapi_key": os.getenv("PIAPI_KEY", ""),
    "midjourney_api_key": os.getenv("MIDJOURNEY_API_KEY", ""),
    "hailuo_api_key": os.getenv("HAILUO_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    "fish_audio_key": os.getenv("FISH_AUDIO_KEY", ""),
}

# アップロードディレクトリ
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def handle_music_upload(file):
    """音楽ファイルをアップロード処理"""
    if file is None:
        return "音楽ファイルを選択してください", None
    
    try:
        # ファイルを保存
        file_path = Path(file.name)
        dest_path = UPLOAD_DIR / file_path.name
        shutil.copy(file.name, dest_path)
        
        return f"✅ ファイルアップロード完了: {file_path.name}", str(dest_path)
    except Exception as e:
        return f"❌ アップロードエラー: {str(e)}", None

def generate_pv_main(title, keywords, lyrics, style, music_path):
    """PV生成メイン処理"""
    
    if not title:
        return "❌ タイトルを入力してください"
    
    if not music_path:
        return "❌ 音楽ファイルをアップロードしてください"
    
    # APIキー確認
    has_piapi = bool(config.get("piapi_key"))
    has_midjourney = bool(config.get("midjourney_api_key"))
    has_hailuo = bool(config.get("hailuo_api_key"))
    
    can_generate = has_piapi or (has_midjourney and has_hailuo)
    
    output_text = f"""
🎬 **PV生成処理**

📝 タイトル: {title}
🏷️ キーワード: {keywords or 'なし'}
🎨 スタイル: {style}
🎵 音楽ファイル: アップロード済み
📜 歌詞: {'あり' if lyrics else 'なし'}

**APIキー状態:**
- PiAPI: {'✅' if has_piapi else '❌'}
- Midjourney: {'✅' if has_midjourney else '❌'}
- Hailuo: {'✅' if has_hailuo else '❌'}

**処理フロー:**
1. 📝 台本生成
2. 🎨 画像生成 (Midjourney)
3. 🎬 動画生成 (Hailuo)
4. 🎵 音楽同期
5. ✂️ 最終合成

"""
    
    if can_generate:
        output_text += "✅ PV生成準備完了！\n"
        output_text += "（実際の生成処理は実装中）"
    else:
        output_text += "⚠️ APIキーを設定してください\n"
        output_text += "Settings → Repository secrets"
    
    return output_text

# Gradioインターフェース
with gr.Blocks(title="PV自動生成", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 PV自動生成AIエージェント
    
    **Midjourney × Hailuo × Fish Audio**で高品質PVを自動生成
    """)
    
    with gr.Row():
        with gr.Column():
            # 基本情報
            title_input = gr.Textbox(label="タイトル *", placeholder="PVのタイトル")
            keywords_input = gr.Textbox(label="キーワード", placeholder="青春, 友情, 冒険")
            style_input = gr.Dropdown(
                label="スタイル",
                choices=["cinematic", "anime", "realistic", "fantasy"],
                value="cinematic"
            )
            
            # 音楽アップロード（シンプル版）
            gr.Markdown("### 🎵 音楽ファイル")
            music_file = gr.File(
                label="音楽をアップロード",
                file_types=[".mp3", ".wav", ".m4a"],
                type="file"
            )
            upload_status = gr.Textbox(label="アップロード状態", interactive=False)
            music_path_state = gr.State()
            
            # アップロード処理
            music_file.change(
                fn=handle_music_upload,
                inputs=music_file,
                outputs=[upload_status, music_path_state]
            )
            
            # 歌詞
            lyrics_input = gr.Textbox(
                label="歌詞/ナレーション",
                lines=3,
                placeholder="歌詞またはナレーション（オプション）"
            )
            
            generate_btn = gr.Button("🚀 PV生成開始", variant="primary")
        
        with gr.Column():
            output = gr.Textbox(label="処理結果", lines=20)
    
    # 生成処理
    generate_btn.click(
        fn=generate_pv_main,
        inputs=[title_input, keywords_input, lyrics_input, style_input, music_path_state],
        outputs=output
    )

if __name__ == "__main__":
    # HF Spaces環境検出
    is_spaces = os.getenv("SPACE_ID") is not None
    
    print(f"Environment: {'HF Spaces' if is_spaces else 'Local'}")
    
    if is_spaces:
        demo.queue()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            show_api=False
        )
    else:
        demo.launch(show_api=False)