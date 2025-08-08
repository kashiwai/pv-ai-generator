import gradio as gr
import json
import os
import tempfile
import shutil
from pathlib import Path
import asyncio
from datetime import datetime
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Hugging Face Spaces環境変数から設定を読み込み
def setup_environment():
    """環境変数から設定を読み込み、config.jsonを更新"""
    config_path = Path("config.json")
    
    # デフォルト設定を読み込み
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # 環境変数から設定を上書き
    env_mappings = {
        "PIAPI_KEY": "piapi_key",  # PiAPI統一キー
        "PIAPI_KEY": "hailuo_api_key",  # Hailuo用にも設定
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
        "GOOGLE_API_KEY": "google_api_key",
        "DEEPSEEK_API_KEY": "deepseek_api_key",
        "FISH_AUDIO_API_KEY": "fish_audio_api_key",
        "SORA_API_KEY": "sora_api_key",
        "VEO3_API_KEY": "veo3_api_key",
        "SEEDANCE_API_KEY": "seedance_api_key",
        "DOMOAI_API_KEY": "domoai_api_key"
    }
    
    for env_key, config_key in env_mappings.items():
        if env_value := os.getenv(env_key):
            config[config_key] = env_value
    
    # Hugging Face Spaces用のデフォルト設定
    config["video_provider"] = os.getenv("VIDEO_PROVIDER", "hailuo")
    config["tts_provider"] = os.getenv("TTS_PROVIDER", "google")
    config["image_provider"] = os.getenv("IMAGE_PROVIDER", "midjourney")  # Midjourney優先
    config["ffmpeg_path"] = "ffmpeg"  # Spacesには事前インストール済み
    
    # 更新された設定を保存
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

# 環境設定を実行
config = setup_environment()

# 必要なモジュールをインポート
from agent_core.character.image_picker import ImagePicker
from agent_core.character.generator import CharacterGenerator
from agent_core.plot.script_planner import ScriptPlanner
from agent_core.plot.script_writer import ScriptWriter
from agent_core.tts.tts_generator import TTSGenerator
from agent_core.video.scene_generator import SceneGenerator
from agent_core.composer.merge_video import VideoComposer
from agent_core.utils.helpers import load_config, save_temp_file, get_audio_duration

class PVGeneratorAgent:
    def __init__(self):
        self.config = load_config()
        self.image_picker = ImagePicker()
        self.character_generator = CharacterGenerator(self.config)
        self.script_planner = ScriptPlanner(self.config)
        self.script_writer = ScriptWriter(self.config)
        self.tts_generator = TTSGenerator(self.config)
        self.scene_generator = SceneGenerator(self.config)
        self.video_composer = VideoComposer(self.config)
        
    async def generate_pv(self, title, keywords, description, mood, lyrics, 
                          audio_file, character_images):
        try:
            # 入力検証
            if not title:
                return None, "❌ タイトルを入力してください"
            if not audio_file:
                return None, "❌ 音楽ファイルをアップロードしてください"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"assets/temp/{timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 音声ファイルの長さを取得
            audio_duration = get_audio_duration(audio_file)
            if audio_duration > 420:
                return None, "❌ 音楽ファイルは最大7分までです"
            elif audio_duration == 0:
                return None, "❌ 音楽ファイルの読み込みに失敗しました"
            
            print(f"[1/7] キャラクター画像処理中...")
            if character_images:
                character_refs = self.image_picker.process_images(character_images)
            else:
                character_refs = await self.character_generator.generate_characters(
                    keywords, mood, description
                )
            
            print(f"[2/7] 構成案生成中...")
            plot_options = await self.script_planner.generate_plot_options(
                title, keywords, description, mood, lyrics, audio_duration
            )
            
            selected_plot = self.script_planner.select_best_plot(plot_options)
            
            print(f"[3/7] 台本作成中...")
            script = await self.script_writer.write_script(
                selected_plot, lyrics, audio_duration
            )
            
            print(f"[4/7] ナレーション音声生成中...")
            narration_files = await self.tts_generator.generate_narration(
                script, output_dir
            )
            
            print(f"[5/7] シーンプロンプト生成中...")
            scene_prompts = await self.scene_generator.generate_scene_prompts(
                script, character_refs, audio_duration
            )
            
            print(f"[6/7] 映像生成中...")
            video_clips = await self.scene_generator.generate_videos(
                scene_prompts, output_dir
            )
            
            print(f"[7/7] 動画合成中...")
            final_video = await self.video_composer.compose_final_video(
                video_clips, narration_files, audio_file, output_dir
            )
            
            # 出力ファイルを移動
            output_path = Path(f"assets/output/PV_{title}_{timestamp}.mp4")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(final_video, output_path)
            
            return str(output_path), f"✅ PV動画を生成しました: {output_path.name}"
            
        except Exception as e:
            return None, f"❌ エラーが発生しました: {str(e)}"

def create_interface():
    agent = PVGeneratorAgent()
    
    with gr.Blocks(title="PV自動生成AIエージェント", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎬 PV自動生成AIエージェント
        
        音楽に合わせて、AI が自動的にプロモーションビデオを生成します。
        最大7分までの動画生成に対応しています。
        
        **🎨 Midjourney v6.1 (PiAPI)** × **🎥 Hailuo 02 AI (PiAPI)** × **Google VEO3** 
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📝 基本情報")
                title = gr.Textbox(
                    label="タイトル *", 
                    placeholder="PVのタイトルを入力（必須項目）"
                )
                keywords = gr.Textbox(
                    label="キーワード", 
                    placeholder="青春, 友情, 冒険 (カンマ区切り)"
                )
                description = gr.Textbox(
                    label="紹介文", 
                    lines=3, 
                    placeholder="PVの概要を説明してください"
                )
                mood = gr.Dropdown(
                    label="雰囲気",
                    choices=["明るい", "感動的", "ノスタルジック", "エネルギッシュ", 
                            "ミステリアス", "ダーク", "ファンタジー", "クール"],
                    value="明るい"
                )
                
                gr.Markdown("## 🎵 コンテンツ")
                lyrics = gr.Textbox(
                    label="歌詞 / メッセージ", 
                    lines=10, 
                    placeholder="歌詞またはナレーション用のメッセージを入力"
                )
                audio_file = gr.Audio(
                    label="音楽ファイル (MP3/WAV/M4A) *", 
                    type="filepath"
                )
                
                gr.Markdown("## 🎨 キャラクター (オプション)")
                character_images = gr.File(
                    label="キャラクター画像",
                    file_count="multiple",
                    file_types=["image"],
                    type="filepath"
                )
                
                generate_btn = gr.Button("🚀 PV生成開始", variant="primary", size="lg")
                
            with gr.Column(scale=1):
                gr.Markdown("## 📺 生成結果")
                output_video = gr.Video(label="完成PV")
                status_message = gr.Textbox(label="ステータス", interactive=False)
                
                gr.Markdown("""
                ## 📋 処理フロー
                1. 🖼️ キャラクター画像の準備
                2. 📝 構成案の生成（複数案）
                3. ✍️ 台本の作成
                4. 🗣️ ナレーション音声の合成
                5. 🎬 シーンごとの映像生成
                6. 🎵 音声・映像・BGMの合成
                7. ✅ 完成動画の出力
                
                **処理時間の目安**: 3分の動画で約5-10分
                """)
                
                with gr.Accordion("⚙️ 詳細設定", open=False):
                    gr.Markdown(f"""
                    ### 現在の設定
                    - **PiAPI統合**: Midjourney + Hailuo 02 を一つのキーで管理
                    - **画像生成**: Midjourney v6.1 (PiAPI経由・最優先)
                    - **映像生成**: Hailuo 02 (PiAPI経由・推奨)
                    - **音声合成**: {config.get('tts_provider', 'google').upper()}
                    
                    ### PiAPIで利用可能なAI
                    - **PiAPI統一キー**:
                      - Midjourney v6.1 (画像生成)
                      - Hailuo 02 (映像生成)
                    - **その他のAI**:
                      - 構成・台本: GPT-4 / Claude / Gemini / Deepseek
                      - 画像: DALL-E 3 (フォールバック)
                      - 音声: Google TTS / Fish Audio
                      - 映像: VEO3 / SORA / Seedance / DomoAI
                    """)
        
        # イベントハンドラー（シンプル版）
        def run_generation(title, keywords, description, mood, lyrics, audio_file, character_images):
            """
            PV生成を実行（同期ラッパー）
            """
            return asyncio.run(
                agent.generate_pv(title, keywords, description, mood, lyrics, 
                                audio_file, character_images)
            )
        
        generate_btn.click(
            fn=run_generation,
            inputs=[title, keywords, description, mood, lyrics, audio_file, character_images],
            outputs=[output_video, status_message]
        )
        
        # サンプル
        gr.Examples(
            examples=[
                ["青春の輝き", "学校, 友情, 夢", "高校生たちの青春物語", "明るい", 
                 "明日へ向かって走り出そう\n新しい世界が待っている", None, None],
                ["星空の約束", "ファンタジー, 冒険, 魔法", "魔法の世界での冒険", "ファンタジー", 
                 "星空に誓った約束を\n忘れることはないよ", None, None],
            ],
            inputs=[title, keywords, description, mood, lyrics, audio_file, character_images]
        )
        
        # フッター
        gr.Markdown("""
        ---
        <center>
        
        Made with ❤️ by PV AI Generator Team
        
        ⚠️ **注意**: APIキーが設定されていない場合、一部機能が制限されます
        
        PiAPI: https://piapi.ai | Docs: PIAPI_SETUP.md
        
        </center>
        """)
    
    return demo

# Hugging Face Spaces対応
if __name__ == "__main__":
    # 必要なディレクトリを作成
    for dir_path in ["assets/input", "assets/output", "assets/temp", "assets/characters"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    demo = create_interface()
    
    # Hugging Face Spaces環境を検出
    import sys
    is_hf_spaces = sys.executable.startswith('/home/user/app') or \
                   os.getenv('SPACE_ID') is not None or \
                   os.getenv('SYSTEM') == 'spaces'
    
    # シンプルな起動設定
    demo.queue()
    
    if is_hf_spaces:
        # HF Spaces用 - share=Trueでlocalhost問題を回避
        demo.launch(share=True)
    else:
        # ローカル環境
        demo.launch(share=False)