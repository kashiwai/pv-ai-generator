#!/usr/bin/env python3
"""
統合Text-to-Video実装（修正版）
PIAPI Hailuo/Kling動画生成に特化
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List, Optional

class UnifiedTextToVideoFixed:
    """修正版Text-to-Video生成クラス"""
    
    def __init__(self):
        # PIAPIキー（デフォルト値設定）
        self.piapi_key = st.session_state.get('api_keys', {}).get('piapi', '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b')
        self.piapi_xkey = st.session_state.get('api_keys', {}).get('piapi_xkey', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
        
        # Google APIキー（オプション）
        self.google_api_key = st.session_state.get('api_keys', {}).get('google', 'AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8')
    
    def generate_video_auto(self, text_prompt: str, duration: int = 5) -> Dict[str, Any]:
        """
        自動で最適なAPIを選択して動画生成
        優先順位: 1. Hailuo, 2. Kling
        """
        
        st.info(f"🎬 動画生成開始: {text_prompt[:50]}...")
        
        # 方法1: PIAPI Hailuo（最優先）
        result = self.generate_with_hailuo(text_prompt, duration)
        if result.get('status') == 'success':
            return result
        
        # 方法2: PIAPI Kling（次善）
        result = self.generate_with_kling(text_prompt, duration)
        if result.get('status') == 'success':
            return result
        
        # 全て失敗
        return {
            'status': 'error',
            'message': '動画生成APIが利用できません',
            'provider': 'none'
        }
    
    def generate_with_hailuo(self, text_prompt: str, duration: int = 5) -> Dict[str, Any]:
        """PIAPI Hailuoで動画生成"""
        
        if not self.piapi_xkey:
            return {'status': 'error', 'message': 'PIAPI XKEYが設定されていません'}
        
        url = "https://api.piapi.ai/api/v1/task"
        
        headers = {
            "X-API-Key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "hailuo",
            "task_type": "video_generation",
            "input": {
                "prompt": text_prompt,
                "model": "t2v-01",
                "expand_prompt": True
            },
            "config": {
                "service_mode": "public",
                "webhook_config": {
                    "endpoint": "",
                    "secret": ""
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    data = result.get('data', {})
                    task_id = data.get('task_id')
                    
                    if task_id:
                        st.success(f"✅ Hailuo動画生成開始: Task {task_id[:8]}...")
                        
                        # ポーリングして結果を取得
                        video_url = self.poll_task_status(task_id, "Hailuo")
                        
                        if video_url:
                            return {
                                'status': 'success',
                                'video_url': video_url,
                                'task_id': task_id,
                                'provider': 'hailuo',
                                'message': 'Hailuo動画生成成功'
                            }
            
            return {'status': 'error', 'message': f'Hailuo失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Hailuo例外: {str(e)}'}
    
    def generate_with_kling(self, text_prompt: str, duration: int = 5) -> Dict[str, Any]:
        """PIAPI Klingで動画生成"""
        
        if not self.piapi_xkey:
            return {'status': 'error', 'message': 'PIAPI XKEYが設定されていません'}
        
        url = "https://api.piapi.ai/api/v1/task"
        
        headers = {
            "X-API-Key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "kling",
            "task_type": "video_generation",
            "input": {
                "prompt": text_prompt,
                "negative_prompt": "",
                "cfg_scale": 0.5,
                "duration": duration,
                "aspect_ratio": "16:9",
                "camera_control": {
                    "type": "simple",
                    "config": {
                        "horizontal": 0,
                        "vertical": 0,
                        "pan": -10,
                        "tilt": 0,
                        "roll": 0,
                        "zoom": 0
                    }
                },
                "mode": "std"
            },
            "config": {
                "service_mode": "public",
                "webhook_config": {
                    "endpoint": "",
                    "secret": ""
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    data = result.get('data', {})
                    task_id = data.get('task_id')
                    
                    if task_id:
                        st.success(f"✅ Kling動画生成開始: Task {task_id[:8]}...")
                        
                        # ポーリングして結果を取得
                        video_url = self.poll_task_status(task_id, "Kling")
                        
                        if video_url:
                            return {
                                'status': 'success',
                                'video_url': video_url,
                                'task_id': task_id,
                                'provider': 'kling',
                                'message': 'Kling動画生成成功'
                            }
            
            return {'status': 'error', 'message': f'Kling失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Kling例外: {str(e)}'}
    
    def poll_task_status(self, task_id: str, provider: str) -> Optional[str]:
        """タスクのステータスをポーリング"""
        
        url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        headers = {"X-API-Key": self.piapi_xkey}
        
        max_attempts = 30  # 最大5分待機
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(max_attempts):
            progress = (i + 1) / max_attempts
            progress_bar.progress(progress)
            status_text.text(f"⏳ {provider}処理中... [{i+1}/{max_attempts}]")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {})
                    status = data.get('status', 'unknown')
                    
                    if status == 'completed':
                        output = data.get('output', {})
                        
                        # Hailuoの場合
                        if provider == "Hailuo":
                            video_url = output.get('video_url') or output.get('download_url')
                            if video_url:
                                progress_bar.progress(1.0)
                                status_text.success(f"✅ {provider}動画生成完了!")
                                return video_url
                        
                        # Klingの場合
                        elif provider == "Kling":
                            works = output.get('works', [])
                            if works and len(works) > 0:
                                for work in works:
                                    if work.get('resource'):
                                        progress_bar.progress(1.0)
                                        status_text.success(f"✅ {provider}動画生成完了!")
                                        return work['resource']
                    
                    elif status in ['failed', 'error']:
                        status_text.error(f"❌ {provider}生成失敗")
                        return None
                
            except Exception as e:
                pass
            
            time.sleep(10)  # 10秒待機
        
        status_text.warning(f"⏱️ {provider}タイムアウト")
        return None

# Streamlitから使用する関数
def generate_videos_from_script(script: Dict[str, Any], character_photos: List[str] = None) -> List[Dict[str, Any]]:
    """台本から動画を生成（Streamlit対応）"""
    
    generator = UnifiedTextToVideoFixed()
    results = []
    
    scenes = script.get('scenes', [])
    
    for i, scene in enumerate(scenes):
        scene_num = i + 1
        prompt = scene.get('visual_prompt', '') or scene.get('content', '')
        
        st.markdown(f"### 🎬 シーン{scene_num}の動画生成")
        
        result = generator.generate_video_auto(prompt, duration=5)
        
        result['scene_number'] = scene_num
        result['timestamp'] = f"{i*5}-{(i+1)*5}s"
        
        results.append(result)
        
        if result.get('status') == 'success':
            st.video(result.get('video_url'))
    
    return results

# エクスポート
if __name__ == "__main__":
    # テスト実行
    st.title("Text-to-Video テスト")
    
    prompt = st.text_input("プロンプト", "A beautiful sunrise over mountains")
    
    if st.button("生成開始"):
        generator = UnifiedTextToVideoFixed()
        result = generator.generate_video_auto(prompt, duration=5)
        
        if result['status'] == 'success':
            st.success(f"✅ 動画生成成功！")
            st.video(result['video_url'])
        else:
            st.error(f"❌ 失敗: {result['message']}")