import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from gtts import gTTS
import requests
import tempfile
import wave
import numpy as np
from pydub import AudioSegment
from pydub.silence import split_on_silence

class TTSGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tts_provider = config.get("tts_provider", "google")
        self.fish_audio_api_key = config.get("fish_audio_api_key")
        self.fish_audio_url = "https://api.fish.audio/v1/tts"
        
    async def generate_narration(self, script: Dict, output_dir: Path) -> List[Dict]:
        """
        台本からナレーション音声を生成
        """
        scenes = script.get("scenes", [])
        narration_files = []
        
        for scene in scenes:
            if scene.get("narration"):
                audio_file = await self.generate_scene_narration(
                    scene["scene_number"],
                    scene["narration"],
                    scene.get("mood", "normal"),
                    output_dir
                )
                
                if audio_file:
                    narration_files.append({
                        "scene_number": scene["scene_number"],
                        "timestamp": scene["timestamp"],
                        "duration": scene["duration"],
                        "audio_file": audio_file,
                        "text": scene["narration"]
                    })
        
        subtitle_file = output_dir / "subtitles.json"
        self.generate_subtitle_file(narration_files, subtitle_file)
        
        return narration_files
    
    async def generate_scene_narration(self, scene_number: int, text: str, 
                                      mood: str, output_dir: Path) -> Optional[Path]:
        """
        シーンごとのナレーション生成
        """
        output_file = output_dir / f"narration_scene_{scene_number:03d}.mp3"
        
        try:
            if self.tts_provider == "fish_audio" and self.fish_audio_api_key:
                return await self.generate_with_fish_audio(text, mood, output_file)
            else:
                return await self.generate_with_google_tts(text, mood, output_file)
                
        except Exception as e:
            print(f"TTS Generation Error for scene {scene_number}: {e}")
            return await self.generate_with_google_tts(text, mood, output_file)
    
    async def generate_with_google_tts(self, text: str, mood: str, 
                                      output_file: Path) -> Optional[Path]:
        """
        Google TTSを使用した音声生成
        """
        try:
            lang = 'ja'
            
            speed_map = {
                "期待感": 1.0,
                "展開": 1.1,
                "高揚": 1.2,
                "余韻": 0.9,
                "normal": 1.0
            }
            speed = speed_map.get(mood, 1.0)
            
            tts = gTTS(text=text, lang=lang, slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                audio = AudioSegment.from_mp3(tmp_file.name)
                
                audio = audio.speedup(playback_speed=speed)
                
                audio = self.apply_mood_effects(audio, mood)
                
                audio.export(output_file, format="mp3", bitrate="192k")
                
                os.unlink(tmp_file.name)
            
            return output_file
            
        except Exception as e:
            print(f"Google TTS Error: {e}")
            return None
    
    async def generate_with_fish_audio(self, text: str, mood: str, 
                                      output_file: Path) -> Optional[Path]:
        """
        Fish Audioを使用した音声生成
        """
        try:
            voice_map = {
                "期待感": "cheerful",
                "展開": "narrative",
                "高揚": "emotional",
                "余韻": "gentle",
                "normal": "default"
            }
            
            headers = {
                "Authorization": f"Bearer {self.fish_audio_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "text": text,
                "voice": voice_map.get(mood, "default"),
                "language": "ja",
                "speed": 1.0,
                "pitch": 1.0,
                "format": "mp3"
            }
            
            response = await asyncio.to_thread(
                requests.post,
                self.fish_audio_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                audio = AudioSegment.from_mp3(output_file)
                audio = self.apply_mood_effects(audio, mood)
                audio.export(output_file, format="mp3", bitrate="192k")
                
                return output_file
            else:
                print(f"Fish Audio API Error: {response.status_code}")
                return await self.generate_with_google_tts(text, mood, output_file)
                
        except Exception as e:
            print(f"Fish Audio Error: {e}")
            return await self.generate_with_google_tts(text, mood, output_file)
    
    def apply_mood_effects(self, audio: AudioSegment, mood: str) -> AudioSegment:
        """
        雰囲気に応じた音声エフェクトを適用
        """
        if mood == "期待感":
            audio = audio.fade_in(500)
            audio = audio + 2
        elif mood == "高揚":
            audio = audio + 3
            audio = audio.compress_dynamic_range()
        elif mood == "余韻":
            audio = audio - 2
            audio = audio.fade_out(1000)
        elif mood == "ミステリアス":
            audio = audio.low_pass_filter(3000)
            audio = audio - 1
        
        return audio
    
    def generate_subtitle_file(self, narration_files: List[Dict], output_file: Path):
        """
        字幕ファイルの生成（JSON形式）
        """
        subtitles = []
        
        for narration in narration_files:
            subtitles.append({
                "scene": narration["scene_number"],
                "start": self.parse_timestamp(narration["timestamp"].split('-')[0]),
                "end": self.parse_timestamp(narration["timestamp"].split('-')[1]),
                "text": narration["text"]
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "subtitles": subtitles,
                "format": "json",
                "language": "ja"
            }, f, ensure_ascii=False, indent=2)
    
    def parse_timestamp(self, timestamp: str) -> float:
        """
        タイムスタンプを秒に変換
        """
        try:
            parts = timestamp.strip().split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            return 0
        except:
            return 0
    
    async def generate_voice_samples(self, character_descriptions: List[str]) -> Dict[str, str]:
        """
        キャラクターごとの音声サンプル生成
        """
        voice_samples = {}
        
        for i, description in enumerate(character_descriptions):
            sample_text = f"こんにちは、私は{description}です。"
            sample_file = Path(f"assets/temp/voice_sample_{i}.mp3")
            
            await self.generate_with_google_tts(
                sample_text, 
                "normal", 
                sample_file
            )
            
            voice_samples[f"character_{i}"] = str(sample_file)
        
        return voice_samples
    
    def merge_narration_files(self, narration_files: List[Path], 
                            output_file: Path) -> Path:
        """
        複数のナレーションファイルを結合
        """
        combined = AudioSegment.empty()
        
        for file_path in narration_files:
            if file_path.exists():
                audio = AudioSegment.from_mp3(file_path)
                combined += audio
                combined += AudioSegment.silent(duration=500)
        
        combined.export(output_file, format="mp3", bitrate="192k")
        return output_file
    
    async def adjust_narration_timing(self, narration_file: Path, 
                                     target_duration: float) -> Path:
        """
        ナレーションのタイミング調整
        """
        audio = AudioSegment.from_mp3(narration_file)
        current_duration = len(audio) / 1000.0
        
        if current_duration > target_duration:
            speed_ratio = current_duration / target_duration
            audio = audio.speedup(playback_speed=speed_ratio)
        elif current_duration < target_duration * 0.8:
            silence_duration = int((target_duration - current_duration) * 1000)
            audio = audio + AudioSegment.silent(duration=silence_duration)
        
        output_file = narration_file.parent / f"{narration_file.stem}_adjusted.mp3"
        audio.export(output_file, format="mp3", bitrate="192k")
        
        return output_file