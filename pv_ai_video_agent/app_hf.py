"""
Hugging Face Spaces用のエントリーポイント
"""
import os
import sys

# Spacesの環境変数から設定を読み込み
def setup_hf_environment():
    """Hugging Face Spaces環境の設定"""
    
    # Secretsから環境変数を設定
    env_mappings = {
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key", 
        "GOOGLE_API_KEY": "google_api_key",
        "HAILUO_API_KEY": "hailuo_api_key",
        "FISH_AUDIO_API_KEY": "fish_audio_api_key",
        "MIDJOURNEY_API_KEY": "midjourney_api_key",
    }
    
    # config.jsonを環境変数で上書き
    import json
    config_path = "config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        for env_key, config_key in env_mappings.items():
            if env_value := os.getenv(env_key):
                config[config_key] = env_value
        
        # Spaces用の設定
        config["video_provider"] = "hailuo"  # Hailuo 02 AIをデフォルトに
        config["tts_provider"] = "google"    # Google TTSをデフォルトに
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

# 環境設定
setup_hf_environment()

# メインアプリをインポート・実行
from app import create_interface

if __name__ == "__main__":
    demo = create_interface()
    
    # Hugging Face Spaces用の設定
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Spacesでは不要
        debug=False,
        show_error=True,
        quiet=False
    )