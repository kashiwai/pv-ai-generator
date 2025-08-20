import asyncio
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import shutil
import numpy as np

from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, TextClip, ImageClip, ColorClip, concatenate_videoclips
from moviepy.video.fx import resize, fadein, fadeout
MOVIEPY_AVAILABLE = True

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: PyDub not available. Audio processing will be limited.")

class VideoComposer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ffmpeg_path = config.get("ffmpeg_path", "ffmpeg")
        self.default_fps = 30
        self.default_resolution = (1920, 1080)
        
    async def compose_final_video(self, video_clips: List[Dict], 
                                 narration_files: List[Dict],
                                 bgm_file: str, output_dir: Path) -> Path:
        """
        最終的なPV動画を合成
        """
        try:
            temp_video = output_dir / "temp_video.mp4"
            temp_audio = output_dir / "temp_audio.mp3"
            final_output = output_dir / "final_pv.mp4"
            
            await self.merge_video_clips(video_clips, temp_video)
            
            await self.create_audio_track(narration_files, bgm_file, temp_audio)
            
            await self.combine_video_audio(temp_video, temp_audio, final_output)
            
            subtitle_file = output_dir / "subtitles.json"
            if subtitle_file.exists():
                final_with_subtitles = output_dir / "final_pv_with_subtitles.mp4"
                await self.add_subtitles(final_output, subtitle_file, final_with_subtitles)
                return final_with_subtitles
            
            return final_output
            
        except Exception as e:
            print(f"Video Composition Error: {e}")
            raise
    
    async def merge_video_clips(self, video_clips: List[Dict], output_file: Path):
        """
        複数の動画クリップを結合
        """
        if not MOVIEPY_AVAILABLE:
            print("MoviePy not available. Using FFmpeg directly.")
            await self.merge_with_ffmpeg(video_clips, output_file)
            return
            
        if not video_clips:
            await self.create_placeholder_video(output_file)
            return
        
        clips = []
        
        for clip_info in video_clips:
            clip_path = clip_info.get("file_path")
            if clip_path and Path(clip_path).exists():
                try:
                    clip = VideoFileClip(str(clip_path))
                    
                    clip = clip.resize(self.default_resolution)
                    
                    if clip_info.get("transition") == "fade":
                        clip = clip.fadein(0.5).fadeout(0.5)
                    
                    clips.append(clip)
                except Exception as e:
                    print(f"Error loading clip {clip_path}: {e}")
                    placeholder = await self.create_placeholder_clip(
                        clip_info.get("duration", 8)
                    )
                    clips.append(placeholder)
        
        if not clips:
            await self.create_placeholder_video(output_file)
            return
        
        final_video = concatenate_videoclips(clips, method="compose")
        
        final_video.write_videofile(
            str(output_file),
            fps=self.default_fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )
        
        for clip in clips:
            clip.close()
        final_video.close()
    
    async def create_audio_track(self, narration_files: List[Dict], 
                                bgm_file: str, output_file: Path):
        """
        ナレーションとBGMを合成した音声トラックを作成
        """
        if not PYDUB_AVAILABLE:
            print("PyDub not available. Using basic audio.")
            if bgm_file and Path(bgm_file).exists():
                shutil.copy(bgm_file, output_file)
            return
            
        bgm_audio = None
        if bgm_file and Path(bgm_file).exists():
            bgm_audio = AudioSegment.from_file(bgm_file)
            bgm_audio = bgm_audio - 10
        
        combined_audio = AudioSegment.silent(duration=0)
        current_position = 0
        
        for narration_info in sorted(narration_files, key=lambda x: x["scene_number"]):
            narration_file = narration_info.get("audio_file")
            timestamp = narration_info.get("timestamp", "00:00-00:08")
            
            start_time = self.parse_timestamp(timestamp.split('-')[0]) * 1000
            
            if narration_file and Path(narration_file).exists():
                narration = AudioSegment.from_file(narration_file)
                
                silence_duration = start_time - current_position
                if silence_duration > 0:
                    combined_audio += AudioSegment.silent(duration=silence_duration)
                    current_position = start_time
                
                combined_audio = combined_audio.overlay(
                    narration,
                    position=current_position
                )
                current_position += len(narration)
        
        if bgm_audio:
            if len(combined_audio) > len(bgm_audio):
                loops_needed = (len(combined_audio) // len(bgm_audio)) + 1
                bgm_audio = bgm_audio * loops_needed
            
            bgm_audio = bgm_audio[:len(combined_audio)]
            
            final_audio = bgm_audio.overlay(combined_audio)
        else:
            final_audio = combined_audio
        
        final_audio.export(output_file, format="mp3", bitrate="320k")
    
    async def combine_video_audio(self, video_file: Path, audio_file: Path, 
                                 output_file: Path):
        """
        動画と音声を結合
        """
        cmd = [
            self.ffmpeg_path,
            '-i', str(video_file),
            '-i', str(audio_file),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-y',
            str(output_file)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()}")
    
    async def add_subtitles(self, video_file: Path, subtitle_file: Path, 
                          output_file: Path):
        """
        字幕を動画に追加
        """
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitle_data = json.load(f)
        
        video = VideoFileClip(str(video_file))
        
        subtitle_clips = []
        for subtitle in subtitle_data.get("subtitles", []):
            text = subtitle["text"]
            start = subtitle["start"]
            end = subtitle["end"]
            
            txt_clip = TextClip(
                text,
                fontsize=48,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial',
                method='caption',
                size=(video.w * 0.8, None),
                align='center'
            )
            
            txt_clip = txt_clip.set_position(('center', 'bottom'))
            txt_clip = txt_clip.set_start(start).set_duration(end - start)
            
            subtitle_clips.append(txt_clip)
        
        final_video = CompositeVideoClip([video] + subtitle_clips)
        
        final_video.write_videofile(
            str(output_file),
            fps=self.default_fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )
        
        video.close()
        final_video.close()
    
    async def merge_with_ffmpeg(self, video_clips: List[Dict], output_file: Path):
        """
        FFmpegを直接使用して動画を結合
        """
        if not video_clips:
            return
        
        # 一時ファイルリストを作成
        list_file = output_file.parent / "concat_list.txt"
        with open(list_file, 'w') as f:
            for clip in video_clips:
                if clip.get("file_path") and Path(clip["file_path"]).exists():
                    f.write(f"file '{clip['file_path']}'\n")
        
        # FFmpegで結合
        cmd = [
            self.ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            '-y',
            str(output_file)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        list_file.unlink()
    
    async def create_placeholder_video(self, output_file: Path, duration: float = 10):
        """
        プレースホルダー動画を作成
        """
        if not MOVIEPY_AVAILABLE:
            # FFmpegで黒画面動画を作成
            cmd = [
                self.ffmpeg_path,
                '-f', 'lavfi',
                '-i', f'color=c=black:s={self.default_resolution[0]}x{self.default_resolution[1]}:d={duration}',
                '-y',
                str(output_file)
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return
            
        from moviepy.editor import ColorClip
        
        clip = ColorClip(
            size=self.default_resolution,
            color=(30, 30, 30),
            duration=duration
        )
        
        text = TextClip(
            "Processing Video...",
            fontsize=72,
            color='white',
            font='Arial'
        ).set_position('center').set_duration(duration)
        
        final = CompositeVideoClip([clip, text])
        
        final.write_videofile(
            str(output_file),
            fps=self.default_fps,
            codec='libx264',
            threads=4,
            preset='ultrafast'
        )
        
        clip.close()
        text.close()
        final.close()
    
    async def create_placeholder_clip(self, duration: float):
        """
        プレースホルダークリップを作成
        """
        if not MOVIEPY_AVAILABLE:
            return None
            
        from moviepy.editor import ColorClip
        
        return ColorClip(
            size=self.default_resolution,
            color=(50, 50, 50),
            duration=duration
        )
    
    def parse_timestamp(self, timestamp: str) -> float:
        """
        タイムスタンプを秒に変換
        """
        try:
            parts = timestamp.strip().split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0
        except:
            return 0
    
    async def apply_video_effects(self, video_file: Path, effects: List[str], 
                                 output_file: Path):
        """
        動画エフェクトを適用
        """
        video = VideoFileClip(str(video_file))
        
        for effect in effects:
            if effect == "slow_motion":
                video = video.fx(lambda clip: clip.speedx(0.5))
            elif effect == "speed_up":
                video = video.fx(lambda clip: clip.speedx(2.0))
            elif effect == "black_white":
                video = video.fx(lambda clip: clip.fx(
                    lambda frame: np.dot(frame[...,:3], [0.2989, 0.5870, 0.1140])
                ))
            elif effect == "vintage":
                pass
        
        video.write_videofile(
            str(output_file),
            fps=self.default_fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )
        
        video.close()
    
    async def create_transition(self, clip1_path: Path, clip2_path: Path, 
                              transition_type: str, output_file: Path):
        """
        2つのクリップ間にトランジションを作成
        """
        clip1 = VideoFileClip(str(clip1_path))
        clip2 = VideoFileClip(str(clip2_path))
        
        if transition_type == "crossfade":
            clip1 = clip1.fadeout(1.0)
            clip2 = clip2.fadein(1.0)
            
            from moviepy.editor import concatenate_videoclips
            final = concatenate_videoclips([clip1, clip2], method="compose")
            
        elif transition_type == "wipe":
            final = concatenate_videoclips([clip1, clip2])
            
        else:
            from moviepy.editor import concatenate_videoclips
            final = concatenate_videoclips([clip1, clip2])
        
        final.write_videofile(
            str(output_file),
            fps=self.default_fps,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )
        
        clip1.close()
        clip2.close()
        final.close()