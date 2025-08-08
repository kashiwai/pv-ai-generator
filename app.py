#!/usr/bin/env python3
"""
PV自動生成AIエージェント - Interface版（安定動作優先）
"""

import gradio as gr
import os
import json
from pathlib import Path

print("===== Application Startup - Interface Version =====")

# 環境設定
config = {
    "piapi_key": os.getenv("PIAPI_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
}

def generate_pv(title, keywords, audio_file):
    """
    PV生成のメイン処理（シンプル版）
    
    Args:
        title: PVのタイトル
        keywords: キーワード（カンマ区切り）
        audio_file: 音楽ファイルのパス
    
    Returns:
        結果メッセージ
    """
    try:
        # 入力検証
        if not title:
            return "❌ タイトルを入力してください"
        if not audio_file:
            return "❌ 音楽ファイルをアップロードしてください"
        
        # APIキーの確認
        has_piapi = bool(config.get("piapi_key"))
        has_openai = bool(config.get("openai_api_key"))
        has_google = bool(config.get("google_api_key"))
        
        status_lines = [
            "✅ 入力を受け付けました！",
            "",
            f"タイトル: {title}",
            f"キーワード: {keywords or 'なし'}",
            f"音楽ファイル: アップロード済み",
            "",
            "**APIキー状態:**",
            f"- PiAPI (Midjourney + Hailuo): {'✅ 設定済み' if has_piapi else '❌ 未設定'}",
            f"- OpenAI: {'✅ 設定済み' if has_openai else '❌ 未設定'}",
            f"- Google: {'✅ 設定済み' if has_google else '❌ 未設定'}",
            "",
        ]
        
        if not has_piapi:
            status_lines.append("⚠️ PiAPIキーが設定されていません。")
            status_lines.append("Settings → Repository secrets → PIAPI_KEY で設定してください。")
            status_lines.append("")
            status_lines.append("PiAPIで利用可能：")
            status_lines.append("- Midjourney v6.1 (画像生成)")
            status_lines.append("- Hailuo 02 AI (動画生成)")
        else:
            status_lines.append("🚀 PV生成機能を段階的に追加中...")
            status_lines.append("")
            status_lines.append("処理フロー：")
            status_lines.append("1. 🖼️ キャラクター画像の準備")
            status_lines.append("2. 📝 構成案の生成")
            status_lines.append("3. ✍️ 台本の作成")
            status_lines.append("4. 🗣️ ナレーション音声の合成")
            status_lines.append("5. 🎬 シーンごとの映像生成")
            status_lines.append("6. 🎵 動画合成")
            status_lines.append("7. ✅ 完成！")
        
        return "\n".join(status_lines)
        
    except Exception as e:
        return f"❌ エラーが発生しました: {str(e)}"

# Gradio Interface（最も安定）
demo = gr.Interface(
    fn=generate_pv,
    inputs=[
        gr.Textbox(label="タイトル *", placeholder="PVのタイトルを入力"),
        gr.Textbox(label="キーワード", placeholder="青春, 友情, 冒険"),
        gr.Audio(label="音楽ファイル *", type="filepath"),
    ],
    outputs=gr.Textbox(label="処理結果", lines=20),
    title="🎬 PV自動生成AIエージェント",
    description="""
    音楽に合わせて、AIが自動的にプロモーションビデオを生成します。
    
    **🎨 Midjourney v6.1 (PiAPI)** × **🎥 Hailuo 02 AI (PiAPI)**
    
    最大7分までの動画生成に対応予定
    """,
    examples=[
        ["青春の輝き", "学校, 友情, 夢", None],
        ["星空の約束", "ファンタジー, 冒険", None],
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