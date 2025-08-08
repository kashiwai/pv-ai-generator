import gradio as gr
import json
import os
from pathlib import Path
import asyncio
from datetime import datetime

# 環境設定
def setup_environment():
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # 環境変数から設定を上書き
    env_keys = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY", 
                "HAILUO_API_KEY", "VEO3_API_KEY", "MIDJOURNEY_API_KEY", "FISH_AUDIO_API_KEY"]
    
    for key in env_keys:
        if value := os.getenv(key):
            config[key.lower()] = value
    
    return config

config = setup_environment()

# インポート
from agent_core.character.image_picker import ImagePicker
from agent_core.character.generator import CharacterGenerator
from agent_core.plot.script_planner import ScriptPlanner
from agent_core.plot.script_writer import ScriptWriter
from agent_core.tts.tts_generator import TTSGenerator
from agent_core.video.scene_generator import SceneGenerator
from agent_core.composer.merge_video import VideoComposer
from agent_core.utils.helpers import load_config, get_audio_duration

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
        
    async def generate_pv(self, title, keywords, description, mood, lyrics, audio_file, character_images):
        try:
            if not title or not audio_file:
                return None, "タイトルと音楽ファイルは必須です"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f"assets/temp/{timestamp}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            audio_duration = get_audio_duration(audio_file)
            if audio_duration > 420:
                return None, "音楽ファイルは最大7分までです"
            
            # キャラクター処理
            if character_images:
                character_refs = self.image_picker.process_images(character_images)
            else:
                character_refs = await self.character_generator.generate_characters(
                    keywords or "", mood or "明るい", description or ""
                )
            
            # 構成・台本生成
            plot_options = await self.script_planner.generate_plot_options(
                title, keywords or "", description or "", mood or "明るい", 
                lyrics or "", audio_duration
            )
            selected_plot = self.script_planner.select_best_plot(plot_options)
            script = await self.script_writer.write_script(selected_plot, lyrics, audio_duration)
            
            # 音声生成
            narration_files = await self.tts_generator.generate_narration(script, output_dir)
            
            # 映像生成
            scene_prompts = await self.scene_generator.generate_scene_prompts(
                script, character_refs, audio_duration
            )
            video_clips = await self.scene_generator.generate_videos(scene_prompts, output_dir)
            
            # 合成
            final_video = await self.video_composer.compose_final_video(
                video_clips, narration_files, audio_file, output_dir
            )
            
            output_path = Path(f"assets/output/PV_{title}_{timestamp}.mp4")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.move(final_video, output_path)
            
            return str(output_path), f"PV生成完了: {output_path.name}"
            
        except Exception as e:
            return None, f"エラー: {str(e)}"

# インターフェース
def create_interface():
    agent = PVGeneratorAgent()
    
    with gr.Blocks() as demo:
        gr.Markdown("# 🎬 PV自動生成AIエージェント")
        gr.Markdown("**Midjourney × Hailuo/VEO3** で高品質PVを自動生成")
        
        with gr.Row():
            with gr.Column():
                title = gr.Textbox(label="タイトル（必須）", placeholder="PVのタイトル")
                keywords = gr.Textbox(label="キーワード", placeholder="青春, 友情, 冒険")
                description = gr.Textbox(label="説明", lines=2)
                mood = gr.Dropdown(
                    label="雰囲気",
                    choices=["明るい", "感動的", "ノスタルジック", "エネルギッシュ", 
                            "ミステリアス", "ダーク", "ファンタジー", "クール"],
                    value="明るい"
                )
                lyrics = gr.Textbox(label="歌詞/メッセージ", lines=5)
                audio_file = gr.Audio(label="音楽ファイル（必須）", type="filepath")
                character_images = gr.File(label="キャラクター画像", file_count="multiple", type="filepath")
                generate_btn = gr.Button("PV生成開始", variant="primary")
                
            with gr.Column():
                output_video = gr.Video(label="完成PV")
                status = gr.Textbox(label="ステータス")
        
        def run_async(*args):
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except:
                pass
            return asyncio.run(agent.generate_pv(*args))
        
        generate_btn.click(
            fn=run_async,
            inputs=[title, keywords, description, mood, lyrics, audio_file, character_images],
            outputs=[output_video, status]
        )
    
    return demo

if __name__ == "__main__":
    # ディレクトリ作成
    for d in ["assets/input", "assets/output", "assets/temp", "assets/characters"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    demo = create_interface()
    demo.launch()