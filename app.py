#!/usr/bin/env python3
"""
PV自動生成AIエージェント - 段階的復元版 Step 1
基本的なUIコンポーネントのテスト
"""

import gradio as gr
import os
import json
from pathlib import Path

print("===== Application Startup - Step 1: Basic UI =====")

# 環境設定
def setup_environment():
    config = {
        "piapi_key": os.getenv("PIAPI_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
    }
    return config

config = setup_environment()

def create_interface():
    """基本的なUIコンポーネントを持つインターフェースを作成"""
    
    with gr.Blocks(title="PV自動生成AIエージェント") as demo:
        gr.Markdown("""
        # 🎬 PV自動生成AIエージェント
        
        音楽に合わせて、AIが自動的にプロモーションビデオを生成します。
        
        **🎨 Midjourney v6.1 (PiAPI)** × **🎥 Hailuo 02 AI (PiAPI)**
        """)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📝 基本情報")
                title = gr.Textbox(
                    label="タイトル *",
                    placeholder="PVのタイトルを入力"
                )
                keywords = gr.Textbox(
                    label="キーワード",
                    placeholder="青春, 友情, 冒険"
                )
                description = gr.Textbox(
                    label="説明",
                    lines=3,
                    placeholder="PVの概要を説明してください"
                )
                mood = gr.Dropdown(
                    label="雰囲気",
                    choices=["明るい", "感動的", "ノスタルジック", "エネルギッシュ"],
                    value="明るい"
                )
                
                gr.Markdown("## 🎵 コンテンツ")
                lyrics = gr.Textbox(
                    label="歌詞/メッセージ",
                    lines=5,
                    placeholder="歌詞またはナレーションを入力"
                )
                audio_file = gr.Audio(
                    label="音楽ファイル *",
                    type="filepath"
                )
                # gr.Filesは問題を起こすため、単一ファイルに変更
                character_images = gr.File(
                    label="キャラクター画像（1枚）",
                    file_types=["image"],
                    type="filepath"
                )
                
                generate_btn = gr.Button("🚀 PV生成開始", variant="primary", size="lg")
                
            with gr.Column():
                gr.Markdown("## 📺 生成結果")
                output_video = gr.Video(label="完成PV")
                status_message = gr.Textbox(
                    label="ステータス",
                    interactive=False,
                    value="待機中..."
                )
                
                gr.Markdown("""
                ## 📋 処理フロー
                1. キャラクター画像準備
                2. 構成案生成
                3. 台本作成
                4. ナレーション音声合成
                5. 映像生成
                6. 動画合成
                7. 完成！
                
                **APIキー設定**: Settings → Repository secrets → PIAPI_KEY
                """)
        
        # シンプルな処理関数（同期版）
        def generate_pv(title, keywords, description, mood, lyrics, audio_file, character_images):
            """PV生成のメイン処理（段階的復元版）"""
            try:
                # 入力検証
                if not title:
                    return None, "❌ タイトルを入力してください"
                if not audio_file:
                    return None, "❌ 音楽ファイルをアップロードしてください"
                
                # APIキーの確認
                has_piapi = bool(config.get("piapi_key"))
                has_openai = bool(config.get("openai_api_key"))
                has_google = bool(config.get("google_api_key"))
                
                status_lines = [
                    "✅ 入力を受け付けました！",
                    "",
                    f"タイトル: {title}",
                    f"キーワード: {keywords or 'なし'}",
                    f"雰囲気: {mood}",
                    f"音楽ファイル: アップロード済み",
                    f"キャラクター画像: {'アップロード済み' if character_images else 'なし'}",
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
                else:
                    status_lines.append("🚀 次のステップ: 完全な機能を段階的に追加中...")
                
                return None, "\n".join(status_lines)
                
            except Exception as e:
                return None, f"❌ エラーが発生しました: {str(e)}"
        
        # イベントハンドラー（Gradio 4.x用にconcurrency_limit設定）
        generate_btn.click(
            fn=generate_pv,
            inputs=[title, keywords, description, mood, lyrics, audio_file, character_images],
            outputs=[output_video, status_message],
            concurrency_limit=2  # 同時実行数を制限
        )
        
        # サンプル
        gr.Examples(
            examples=[
                ["青春の輝き", "学校, 友情, 夢", "高校生たちの青春物語", "明るい", "明日へ向かって", None, None],
                ["星空の約束", "ファンタジー, 冒険", "魔法の世界での冒険", "感動的", "星に願いを", None, None],
            ],
            inputs=[title, keywords, description, mood, lyrics, audio_file, character_images]
        )
    
    return demo

if __name__ == "__main__":
    print("Creating interface...")
    
    # ディレクトリ作成
    for d in ["assets/input", "assets/output", "assets/temp", "assets/characters"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    demo = create_interface()
    
    # HF Spaces環境検出
    is_spaces = os.getenv("SPACE_ID") is not None
    
    print(f"Environment: {'HF Spaces' if is_spaces else 'Local'}")
    print("Launching application...")
    
    # Gradio 4.xではqueueのみ呼び出し（concurrency_limitは各イベントで設定）
    demo.queue()
    
    if is_spaces:
        # HF Spaces用の設定 - API情報生成を無効化
        demo.launch(
            show_api=False,  # API情報生成を無効化（エラー回避）
            max_threads=10
        )
    else:
        demo.launch(show_api=False)