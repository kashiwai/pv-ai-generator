"""
高度なPV生成ワークフロー v2.4.0
Text-to-Video直接生成を含む新しいワークフロー
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

# コアモジュール
from ..character.generator import CharacterGenerator
from ..character.image_picker import ImagePicker
from ..plot.advanced_script_analyzer import AdvancedScriptAnalyzer
from ..plot.detailed_script_writer import DetailedScriptWriter
from ..video.text_to_video_generator import TextToVideoGenerator
from ..composer.merge_video import VideoComposer
from ..tts.tts_generator import TTSGenerator
from ..utils.helpers import load_config, get_audio_duration

class AdvancedPVGenerator:
    """
    v2.4.0 新ワークフロー実装
    基本入力 → 詳細台本(2000-3000文字/シーン) → Text-to-Video → 編集 → 出力
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = load_config()
        
        self.config = config
        self.version = "2.4.0"
        
        # モジュール初期化
        self.character_generator = CharacterGenerator(config)
        self.image_picker = ImagePicker()
        self.script_analyzer = AdvancedScriptAnalyzer(config)
        self.detailed_writer = DetailedScriptWriter(config)
        self.text_to_video = TextToVideoGenerator(config)
        self.video_composer = VideoComposer(config)
        self.tts_generator = TTSGenerator(config)
        
        # ワークフローモード
        self.workflow_mode = config.get("workflow_mode", "advanced")  # advanced or classic
    
    async def generate_pv(self,
                         title: str,
                         keywords: str,
                         description: str,
                         mood: str,
                         lyrics: str,
                         audio_file: str,
                         character_images: Optional[List[str]] = None,
                         use_text_to_video: bool = True,
                         progress_callback=None) -> Dict[str, Any]:
        """
        完全なPV生成プロセス
        
        Args:
            title: タイトル
            keywords: キーワード（カンマ区切り）
            description: 説明
            mood: 雰囲気
            lyrics: 歌詞/メッセージ
            audio_file: 音楽ファイルパス
            character_images: キャラクター画像パス
            use_text_to_video: Text-to-Video直接生成を使用するか
            progress_callback: 進捗コールバック関数
        
        Returns:
            生成結果
        """
        start_time = datetime.now()
        
        # 出力ディレクトリの準備
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"assets/output/{title}_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ワークフローログ
        workflow_log = {
            "version": self.version,
            "mode": "text_to_video" if use_text_to_video else "classic",
            "start_time": str(start_time),
            "steps": []
        }
        
        try:
            # Step 1: 音楽解析
            if progress_callback:
                progress_callback(0.05, "音楽ファイルを解析中...")
            
            music_duration = get_audio_duration(audio_file)
            workflow_log["music_duration"] = music_duration
            
            # Step 2: キャラクター準備
            if progress_callback:
                progress_callback(0.1, "キャラクター参照を準備中...")
            
            character_reference = await self.prepare_character_reference(
                character_images, keywords, mood, description
            )
            workflow_log["steps"].append({
                "step": "character_preparation",
                "status": "completed",
                "has_reference": character_reference is not None
            })
            
            # Step 3: 深層台本分析
            if progress_callback:
                progress_callback(0.2, "歌詞と情景を深層分析中...")
            
            script_analysis = await self.script_analyzer.analyze_and_enhance_script(
                lyrics=lyrics,
                keywords=keywords,
                description=description,
                mood=mood,
                music_duration=music_duration
            )
            workflow_log["steps"].append({
                "step": "script_analysis",
                "status": "completed",
                "analysis_depth": "deep"
            })
            
            # Step 4: 詳細スクリプト生成（2000-3000文字/シーン）
            if progress_callback:
                progress_callback(0.3, "詳細な台本を生成中（2000-3000文字/シーン）...")
            
            detailed_script = await self.detailed_writer.generate_detailed_script(
                basic_script=script_analysis["detailed_script"][0] if script_analysis.get("detailed_script") else {},
                duration=music_duration,
                scene_duration=8
            )
            
            # スクリプトをファイルに保存
            script_file = output_dir / "detailed_script.json"
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_script, f, ensure_ascii=False, indent=2)
            
            workflow_log["steps"].append({
                "step": "detailed_script_generation",
                "status": "completed",
                "num_scenes": len(detailed_script.get("scenes", [])),
                "script_file": str(script_file)
            })
            
            if use_text_to_video:
                # 新ワークフロー: Text-to-Video直接生成
                generated_videos = await self.generate_with_text_to_video(
                    detailed_script=detailed_script,
                    character_reference=character_reference,
                    output_dir=output_dir,
                    progress_callback=progress_callback
                )
            else:
                # クラシックワークフロー: 画像生成 → 動画生成
                generated_videos = await self.generate_with_classic_workflow(
                    detailed_script=detailed_script,
                    character_reference=character_reference,
                    output_dir=output_dir,
                    progress_callback=progress_callback
                )
            
            workflow_log["steps"].append({
                "step": "video_generation",
                "status": "completed",
                "method": "text_to_video" if use_text_to_video else "classic",
                "num_videos": len(generated_videos)
            })
            
            # Step 5: 音声合成（オプション）
            if progress_callback:
                progress_callback(0.7, "ナレーション音声を生成中...")
            
            narration_files = []
            if self.config.get("generate_narration", False):
                narration_files = await self.generate_narration(
                    detailed_script, output_dir
                )
                workflow_log["steps"].append({
                    "step": "narration_generation",
                    "status": "completed",
                    "num_files": len(narration_files)
                })
            
            # Step 6: 最終合成
            if progress_callback:
                progress_callback(0.8, "動画を合成中...")
            
            final_video = await self.compose_final_video(
                video_clips=generated_videos,
                narration_files=narration_files,
                audio_file=audio_file,
                output_dir=output_dir,
                title=title
            )
            
            workflow_log["steps"].append({
                "step": "final_composition",
                "status": "completed",
                "output_file": str(final_video)
            })
            
            # Step 7: 後処理
            if progress_callback:
                progress_callback(0.95, "最終処理中...")
            
            # ワークフローログを保存
            workflow_log["end_time"] = str(datetime.now())
            workflow_log["total_duration"] = str(datetime.now() - start_time)
            
            log_file = output_dir / "workflow_log.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_log, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback(1.0, "完了！")
            
            return {
                "status": "success",
                "video_path": str(final_video),
                "output_dir": str(output_dir),
                "workflow_log": workflow_log,
                "duration": music_duration,
                "title": title
            }
            
        except Exception as e:
            workflow_log["error"] = str(e)
            workflow_log["status"] = "failed"
            
            # エラーログを保存
            error_log_file = output_dir / "error_log.json"
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_log, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "error",
                "message": str(e),
                "output_dir": str(output_dir),
                "workflow_log": workflow_log
            }
    
    async def prepare_character_reference(self,
                                         character_images: Optional[List[str]],
                                         keywords: str,
                                         mood: str,
                                         description: str) -> Optional[Dict]:
        """
        キャラクター参照情報を準備
        """
        if character_images and len(character_images) > 0:
            # アップロードされた画像を使用
            character_refs = self.image_picker.process_images(character_images)
            if character_refs:
                main_character = character_refs[0]
                return {
                    "image_path": main_character["original_path"],
                    "description": main_character.get("description", ""),
                    "id": main_character["id"],
                    "has_reference": True
                }
        else:
            # AIで生成（オプション）
            if self.config.get("auto_generate_character", False):
                generated = await self.character_generator.generate_characters(
                    keywords=keywords,
                    mood=mood,
                    description=description,
                    reference_images=None
                )
                if generated:
                    return {
                        "image_path": generated[0]["original_path"],
                        "description": generated[0]["description"],
                        "id": generated[0]["id"],
                        "has_reference": True
                    }
        
        return None
    
    async def generate_with_text_to_video(self,
                                         detailed_script: Dict,
                                         character_reference: Optional[Dict],
                                         output_dir: Path,
                                         progress_callback=None) -> List[Dict]:
        """
        Text-to-Video直接生成
        """
        if progress_callback:
            progress_callback(0.4, "Text-to-Video生成を開始...")
        
        # Text-to-Video生成
        generated_videos = await self.text_to_video.generate_video_from_script(
            detailed_script=detailed_script,
            character_reference=character_reference,
            output_dir=output_dir / "videos"
        )
        
        if progress_callback:
            progress_callback(0.6, f"{len(generated_videos)}個の動画を生成完了")
        
        return generated_videos
    
    async def generate_with_classic_workflow(self,
                                            detailed_script: Dict,
                                            character_reference: Optional[Dict],
                                            output_dir: Path,
                                            progress_callback=None) -> List[Dict]:
        """
        クラシックワークフロー（画像→動画）
        """
        if progress_callback:
            progress_callback(0.4, "画像生成を開始...")
        
        # 画像生成（Midjourney等）
        generated_images = []
        scenes = detailed_script.get("scenes", [])
        
        for i, scene in enumerate(scenes):
            if progress_callback:
                progress_callback(0.4 + (0.2 * i / len(scenes)), 
                                f"シーン {i+1}/{len(scenes)} の画像を生成中...")
            
            # シーンプロンプトから画像生成
            image_path = await self.generate_scene_image(scene, character_reference, output_dir)
            generated_images.append({
                "scene_number": scene["scene_number"],
                "image_path": image_path,
                "prompt": scene.get("video_prompt", "")
            })
        
        if progress_callback:
            progress_callback(0.6, "画像から動画を生成中...")
        
        # 画像から動画生成
        generated_videos = []
        for img_info in generated_images:
            # Hailuo等で画像から動画生成
            video_info = await self.generate_video_from_image(img_info, output_dir)
            generated_videos.append(video_info)
        
        return generated_videos
    
    async def generate_scene_image(self, scene: Dict, 
                                  character_reference: Optional[Dict],
                                  output_dir: Path) -> str:
        """
        シーンの画像を生成
        """
        prompt = scene.get("video_prompt", "")
        
        # キャラクター参照を含める
        if character_reference:
            ref_path = Path(character_reference["image_path"])
            if ref_path.exists():
                # Midjourneyでキャラクター参照付き生成
                image_path = await self.character_generator.generate_with_midjourney(
                    prompt=prompt,
                    character_ref=character_reference.get("id")
                )
                if image_path:
                    return str(image_path)
        
        # フォールバック: DALL-E
        image_path = await self.character_generator.generate_with_dalle(prompt)
        return str(image_path) if image_path else ""
    
    async def generate_video_from_image(self, image_info: Dict, 
                                       output_dir: Path) -> Dict:
        """
        画像から動画を生成
        """
        # 簡略版実装
        return {
            "scene_number": image_info["scene_number"],
            "video_path": image_info["image_path"],  # 仮実装
            "duration": 8,
            "provider": "hailuo"
        }
    
    async def generate_narration(self, detailed_script: Dict,
                                output_dir: Path) -> List[str]:
        """
        ナレーション音声を生成
        """
        narration_dir = output_dir / "narration"
        narration_dir.mkdir(parents=True, exist_ok=True)
        
        narration_files = []
        scenes = detailed_script.get("scenes", [])
        
        for scene in scenes:
            # ナレーションテキストを抽出
            narration_text = self.extract_narration_text(scene)
            
            if narration_text:
                # TTS生成
                audio_file = await self.tts_generator.generate_speech(
                    text=narration_text,
                    output_path=narration_dir / f"scene_{scene['scene_number']}.mp3"
                )
                if audio_file:
                    narration_files.append(str(audio_file))
        
        return narration_files
    
    def extract_narration_text(self, scene: Dict) -> str:
        """
        シーンからナレーションテキストを抽出
        """
        # 詳細な描写から要約を生成
        detailed_desc = scene.get("detailed_description", "")
        
        # 簡略化: 最初の200文字を使用
        if len(detailed_desc) > 200:
            return detailed_desc[:200] + "..."
        return detailed_desc
    
    async def compose_final_video(self,
                                 video_clips: List[Dict],
                                 narration_files: List[str],
                                 audio_file: str,
                                 output_dir: Path,
                                 title: str) -> Path:
        """
        最終動画を合成
        """
        # VideoComposerを使用して合成
        final_output = output_dir / f"{title}_final.mp4"
        
        # 動画ファイルパスのリスト作成
        video_paths = [v["video_path"] for v in video_clips if v.get("video_path")]
        
        if not video_paths:
            # フォールバック: プレースホルダー動画
            video_paths = [str(output_dir / "placeholder.mp4")]
        
        # 合成実行
        result = await self.video_composer.compose_final_video(
            video_clips=video_paths,
            narration_files=narration_files,
            background_music=audio_file,
            output_path=final_output
        )
        
        return result if result else final_output
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        ワークフロー情報を取得
        """
        return {
            "version": self.version,
            "mode": self.workflow_mode,
            "capabilities": {
                "text_to_video": True,
                "character_consistency": True,
                "deep_script_analysis": True,
                "multi_provider": True
            },
            "providers": {
                "text_to_video": ["veo3", "seedance", "hailuo"],
                "image_generation": ["midjourney", "dalle"],
                "tts": ["google", "fish_audio"]
            },
            "workflow_steps": [
                "音楽解析",
                "キャラクター準備",
                "深層台本分析（歌詞・情景）",
                "詳細スクリプト生成（2000-3000文字/シーン）",
                "Text-to-Video直接生成",
                "音声合成（オプション）",
                "最終合成",
                "出力"
            ]
        }