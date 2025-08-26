#!/usr/bin/env python3
"""
Streamlit対応動画生成モジュール
PIAPI (Hailuo/Kling) + RunComfy対応
"""

import streamlit as st
import requests
import json
import time
import asyncio
from typing import Dict, Any, Optional

class StreamlitVideoGenerator:
    """Streamlit環境での動画生成クラス"""
    
    def __init__(self):
        # APIキーをsession_stateから取得
        if 'api_keys' in st.session_state:
            self.piapi_key = st.session_state.api_keys.get('piapi', '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b')
            self.piapi_xkey = st.session_state.api_keys.get('piapi_xkey', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
        else:
            self.piapi_key = "328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b"
            self.piapi_xkey = "5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4"
        
        # RunComfy設定
        self.runcomfy_token = "79521d2f-f728-47fe-923a-fde31f65df1f"
        self.runcomfy_deployment = "fdac4bbd-491d-47d7-ae45-ce70b67a067f"
    
    def generate_video_streamlit(self, prompt: str, duration: int = 5, method: str = "auto") -> Dict[str, Any]:
        """
        Streamlit環境での動画生成
        
        Args:
            prompt: 動画生成プロンプト
            duration: 動画の長さ（秒）
            method: "auto", "hailuo", "kling", "runcomfy"
        
        Returns:
            生成結果
        """
        
        # Streamlitのプログレス表示
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        if method == "auto" or method == "hailuo":
            progress_placeholder.info("🌊 PIAPI Hailuoで動画生成中...")
            result = self.generate_with_hailuo(prompt, duration, status_placeholder)
            if result['status'] == 'success':
                progress_placeholder.success("✅ Hailuo動画生成完了！")
                return result
        
        if method == "auto" or method == "kling":
            progress_placeholder.info("⚡ PIAPI Klingで動画生成中...")
            result = self.generate_with_kling(prompt, duration, status_placeholder)
            if result['status'] == 'success':
                progress_placeholder.success("✅ Kling動画生成完了！")
                return result
        
        if method == "auto" or method == "runcomfy":
            progress_placeholder.info("🚀 RunComfy Seedanceで動画生成中...")
            result = self.generate_with_runcomfy(prompt, duration, status_placeholder)
            if result['status'] == 'success':
                progress_placeholder.success("✅ RunComfy動画生成完了！")
                return result
        
        progress_placeholder.error("❌ 動画生成に失敗しました")
        return {
            'status': 'error',
            'message': '全てのAPIで失敗しました'
        }
    
    def generate_with_hailuo(self, prompt: str, duration: int, status_placeholder) -> Dict[str, Any]:
        """PIAPI Hailuoで動画生成（Streamlit対応）"""
        
        url = "https://api.piapi.ai/api/v1/task"
        
        headers = {
            "X-API-Key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "hailuo",
            "task_type": "video_generation",
            "input": {
                "prompt": prompt,
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
            # リクエスト送信
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 200:
                    data = result.get('data', {})
                    task_id = data.get('task_id')
                    
                    if task_id:
                        # ステータスポーリング（Streamlit対応）
                        return self.poll_piapi_task(task_id, "Hailuo", status_placeholder)
                
            return {'status': 'error', 'message': f'Hailuo開始失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Hailuo例外: {e}'}
    
    def generate_with_kling(self, prompt: str, duration: int, status_placeholder) -> Dict[str, Any]:
        """PIAPI Klingで動画生成（Streamlit対応）"""
        
        url = "https://api.piapi.ai/api/v1/task"
        
        headers = {
            "X-API-Key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "kling",
            "task_type": "video_generation",
            "input": {
                "prompt": prompt,
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
                        return self.poll_piapi_task(task_id, "Kling", status_placeholder)
                
            return {'status': 'error', 'message': f'Kling開始失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Kling例外: {e}'}
    
    def generate_with_runcomfy(self, prompt: str, duration: int, status_placeholder) -> Dict[str, Any]:
        """RunComfy Seedanceで動画生成（ComfyUIワークフロー対応）"""
        
        url = f"https://api.runcomfy.net/prod/v1/deployments/{self.runcomfy_deployment}/inference"
        
        headers = {
            "Authorization": f"Bearer {self.runcomfy_token}",
            "Content-Type": "application/json"
        }
        
        # ComfyUIワークフロー形式のペイロード
        payload = {
            "overrides": {
                "text_input": prompt,  # ComfyUIの標準的なテキスト入力
                "positive_prompt": prompt,  # 別の一般的な名前
                "prompt_positive": prompt,  # さらに別の形式
                "duration": duration,
                "fps": 30,
                "width": 1920,
                "height": 1080
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                request_id = result.get('request_id')
                
                if request_id:
                    # RunComfyステータス確認
                    return self.poll_runcomfy_task(request_id, status_placeholder)
                
            return {'status': 'error', 'message': f'RunComfy開始失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'RunComfy例外: {e}'}
    
    def poll_piapi_task(self, task_id: str, api_name: str, status_placeholder) -> Dict[str, Any]:
        """PIAPIタスクのポーリング（Streamlit対応）"""
        
        url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        headers = {"X-API-Key": self.piapi_xkey}
        
        # 最大待機時間（5分）
        max_attempts = 30
        
        for i in range(max_attempts):
            # Streamlitステータス更新
            status_placeholder.info(f"⏳ {api_name}処理中... [{i+1}/{max_attempts}]")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {})
                    status = data.get('status', 'unknown')
                    
                    if status == 'completed':
                        output = data.get('output', {})
                        
                        # Hailuoの場合
                        if api_name == "Hailuo":
                            video_url = output.get('video_url') or output.get('download_url')
                            if video_url:
                                return {
                                    'status': 'success',
                                    'video_url': video_url,
                                    'task_id': task_id,
                                    'method': 'piapi_hailuo'
                                }
                        
                        # Klingの場合
                        elif api_name == "Kling":
                            works = output.get('works', [])
                            if works and len(works) > 0:
                                for work in works:
                                    if work.get('resource'):
                                        return {
                                            'status': 'success',
                                            'video_url': work['resource'],
                                            'task_id': task_id,
                                            'method': 'piapi_kling'
                                        }
                    
                    elif status in ['failed', 'error']:
                        return {'status': 'error', 'message': f'{api_name}生成失敗'}
                
            except Exception as e:
                pass
            
            # 待機
            time.sleep(10)
        
        return {'status': 'error', 'message': f'{api_name}タイムアウト'}
    
    def poll_runcomfy_task(self, request_id: str, status_placeholder) -> Dict[str, Any]:
        """RunComfyタスクのポーリング"""
        
        url = f"https://api.runcomfy.net/prod/v1/deployments/{self.runcomfy_deployment}/requests/{request_id}/result"
        headers = {"Authorization": f"Bearer {self.runcomfy_token}"}
        
        max_attempts = 30
        
        for i in range(max_attempts):
            status_placeholder.info(f"⏳ RunComfy処理中... [{i+1}/{max_attempts}]")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', 'unknown')
                    
                    if status == 'completed':
                        output = result.get('output', {})
                        video_url = output.get('video_url') or output.get('url')
                        
                        if video_url:
                            return {
                                'status': 'success',
                                'video_url': video_url,
                                'request_id': request_id,
                                'method': 'runcomfy_seedance'
                            }
                    
                    elif status in ['failed', 'error']:
                        return {'status': 'error', 'message': 'RunComfy生成失敗'}
                
            except Exception as e:
                pass
            
            time.sleep(10)
        
        return {'status': 'error', 'message': 'RunComfyタイムアウト'}

# Streamlitアプリ用関数
def create_video_generation_ui():
    """Streamlit UI作成"""
    
    st.subheader("🎬 Text-to-Video動画生成")
    
    # 生成器初期化
    if 'video_generator' not in st.session_state:
        st.session_state.video_generator = StreamlitVideoGenerator()
    
    # UI要素
    col1, col2 = st.columns([3, 1])
    
    with col1:
        prompt = st.text_area(
            "動画プロンプト",
            value="A beautiful sunrise over mountains with clouds moving slowly",
            height=100
        )
    
    with col2:
        duration = st.slider("動画の長さ（秒）", 3, 10, 5)
        
        method = st.selectbox(
            "生成方法",
            ["auto", "hailuo", "kling", "runcomfy"],
            format_func=lambda x: {
                "auto": "🤖 自動選択",
                "hailuo": "🌊 PIAPI Hailuo",
                "kling": "⚡ PIAPI Kling",
                "runcomfy": "🚀 RunComfy"
            }[x]
        )
    
    # 生成ボタン
    if st.button("🎬 動画生成開始", type="primary", use_container_width=True):
        with st.spinner("動画生成中..."):
            result = st.session_state.video_generator.generate_video_streamlit(
                prompt, duration, method
            )
            
            if result['status'] == 'success':
                st.success(f"✅ 動画生成成功！（{result.get('method', 'unknown')}）")
                
                if result.get('video_url'):
                    st.video(result['video_url'])
                    st.text(f"動画URL: {result['video_url']}")
                
                # 結果を保存
                if 'generation_history' not in st.session_state:
                    st.session_state.generation_history = []
                st.session_state.generation_history.append(result)
                
            else:
                st.error(f"❌ 生成失敗: {result.get('message', 'unknown error')}")

if __name__ == "__main__":
    # テスト用Streamlitアプリ
    st.title("🎬 Text-to-Video Generator")
    create_video_generation_ui()