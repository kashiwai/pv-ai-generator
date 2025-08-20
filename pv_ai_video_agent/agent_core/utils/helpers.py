import json
import os
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import librosa
import soundfile as sf
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
import yaml

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    設定ファイルを読み込む
    """
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_path.endswith('.json'):
                return json.load(f)
            elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
                return yaml.safe_load(f)
    
    return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """
    デフォルト設定を返す
    """
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "fish_audio_api_key": os.getenv("FISH_AUDIO_API_KEY", ""),
        "midjourney_api_key": os.getenv("MIDJOURNEY_API_KEY", ""),
        "sora_api_key": os.getenv("SORA_API_KEY", ""),
        "veo3_api_key": os.getenv("VEO3_API_KEY", ""),
        "seedance_api_key": os.getenv("SEEDANCE_API_KEY", ""),
        "domoai_api_key": os.getenv("DOMOAI_API_KEY", ""),
        "tts_provider": "google",
        "image_provider": "dalle",
        "video_provider": "placeholder",
        "ffmpeg_path": "ffmpeg",
        "max_video_duration": 420,
        "scene_duration": 8,
        "output_resolution": [1920, 1080],
        "output_fps": 30,
        "audio_bitrate": "192k",
        "video_bitrate": "5000k"
    }

def save_config(config: Dict[str, Any], config_path: str = "config.json"):
    """
    設定ファイルを保存
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        if config_path.endswith('.json'):
            json.dump(config, f, ensure_ascii=False, indent=2)
        elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

def get_audio_duration(audio_file: Union[str, Path]) -> float:
    """
    音声ファイルの長さを取得（秒）
    """
    try:
        audio, sr = librosa.load(audio_file, sr=None)
        duration = len(audio) / sr
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def save_temp_file(content: bytes, extension: str = ".tmp") -> Path:
    """
    一時ファイルを保存
    """
    temp_dir = Path("assets/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, 
        suffix=extension, 
        dir=temp_dir
    )
    temp_file.write(content)
    temp_file.close()
    
    return Path(temp_file.name)

def calculate_file_hash(file_path: Union[str, Path]) -> str:
    """
    ファイルのハッシュ値を計算
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def resize_image(image_path: Union[str, Path], target_size: tuple) -> Path:
    """
    画像をリサイズ
    """
    img = Image.open(image_path)
    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
    
    output_path = Path(image_path).parent / f"{Path(image_path).stem}_resized{Path(image_path).suffix}"
    img_resized.save(output_path)
    
    return output_path

def convert_audio_format(audio_file: Union[str, Path], output_format: str = "mp3") -> Path:
    """
    音声ファイルのフォーマットを変換
    """
    audio, sr = librosa.load(audio_file, sr=None)
    
    output_path = Path(audio_file).parent / f"{Path(audio_file).stem}.{output_format}"
    
    if output_format == "wav":
        sf.write(output_path, audio, sr)
    else:
        from pydub import AudioSegment
        audio_segment = AudioSegment(
            audio.tobytes(),
            frame_rate=sr,
            sample_width=audio.dtype.itemsize,
            channels=1
        )
        audio_segment.export(output_path, format=output_format)
    
    return output_path

def split_text_into_chunks(text: str, max_length: int = 500) -> List[str]:
    """
    テキストを指定長さのチャンクに分割
    """
    sentences = text.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def format_timestamp(seconds: float) -> str:
    """
    秒数をタイムスタンプ形式に変換
    """
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def parse_timestamp_to_seconds(timestamp: str) -> float:
    """
    タイムスタンプを秒数に変換
    """
    parts = timestamp.split(':')
    
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        return float(timestamp)

def validate_file_type(file_path: Union[str, Path], allowed_types: List[str]) -> bool:
    """
    ファイルタイプを検証
    """
    file_extension = Path(file_path).suffix.lower().replace('.', '')
    return file_extension in allowed_types

def create_directory_structure(base_path: Union[str, Path]):
    """
    必要なディレクトリ構造を作成
    """
    base = Path(base_path)
    
    directories = [
        base / "assets" / "input",
        base / "assets" / "output",
        base / "assets" / "temp",
        base / "assets" / "characters",
        base / "agent_core" / "character",
        base / "agent_core" / "plot",
        base / "agent_core" / "tts",
        base / "agent_core" / "video",
        base / "agent_core" / "composer",
        base / "agent_core" / "utils"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def clean_temp_files(temp_dir: Union[str, Path] = "assets/temp", max_age_hours: int = 24):
    """
    古い一時ファイルを削除
    """
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        return
    
    current_time = datetime.now()
    max_age = timedelta(hours=max_age_hours)
    
    for file in temp_path.glob("*"):
        if file.is_file():
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            if current_time - file_time > max_age:
                try:
                    file.unlink()
                    print(f"Deleted old temp file: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")

def estimate_processing_time(duration: float, scene_count: int) -> str:
    """
    処理時間の推定
    """
    base_time = 60
    per_scene_time = 30
    per_minute_audio = 20
    
    estimated_seconds = base_time + (scene_count * per_scene_time) + (duration / 60 * per_minute_audio)
    
    return format_timestamp(estimated_seconds)

def generate_unique_id() -> str:
    """
    ユニークIDを生成
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = hashlib.md5(os.urandom(16)).hexdigest()[:8]
    return f"{timestamp}_{random_part}"

def merge_json_files(file_paths: List[Union[str, Path]]) -> Dict:
    """
    複数のJSONファイルをマージ
    """
    merged = {}
    
    for file_path in file_paths:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged.update(data)
    
    return merged

def validate_api_keys(config: Dict[str, Any]) -> Dict[str, bool]:
    """
    APIキーの存在を検証
    """
    validation = {}
    
    api_keys = [
        "openai_api_key",
        "anthropic_api_key",
        "google_api_key",
        "deepseek_api_key",
        "fish_audio_api_key",
        "midjourney_api_key",
        "sora_api_key",
        "veo3_api_key",
        "seedance_api_key",
        "domoai_api_key"
    ]
    
    for key in api_keys:
        validation[key] = bool(config.get(key))
    
    return validation