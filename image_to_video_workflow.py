#!/usr/bin/env python3
"""
画像→動画ワークフロー（v5.0.0）
1. Midjourney画像生成
2. Kling動画生成
日本人女性キャラクターの一貫性を保持
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

class ImageToVideoWorkflow:
    """画像→動画ワークフロー（Klingメイン）"""
    
    def __init__(self):
        # APIキー設定
        self.piapi_key = st.session_state.get('api_keys', {}).get('piapi', '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b')
        self.piapi_xkey = st.session_state.get('api_keys', {}).get('piapi_xkey', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
        
        # キャラクター設定（日本人女性）
        self.character_base = "beautiful Japanese woman, 25 years old, long black hair, elegant features"
        self.character_style = "photorealistic, high quality, professional photography"
    
    def generate_detailed_script(self, 
                               title: str, 
                               description: str,
                               duration: int = 180) -> Dict[str, Any]:
        """
        詳細な台本生成（キャラクター一貫性重視）
        
        Args:
            title: PVタイトル
            description: 概要説明
            duration: 動画の長さ（秒）
        
        Returns:
            詳細台本
        """
        
        # シーン数を計算（各シーン8秒）
        num_scenes = duration // 8
        
        script = {
            'title': title,
            'duration': duration,
            'character': self.character_base,
            'scenes': []
        }
        
        # 各シーンの詳細台本を生成
        for i in range(num_scenes):
            scene = {
                'scene_number': i + 1,
                'duration': 8,
                'time_range': f"{i*8}-{(i+1)*8}s",
                
                # ストーリー要素（詳細化）
                'narrative': self._generate_scene_narrative(i, num_scenes, title),
                
                # キャラクター描写（一貫性重視）
                'character_description': self._generate_character_description(i, num_scenes),
                
                # Midjourneyプロンプト（画像生成用）
                'midjourney_prompt': '',  # 後で生成
                
                # Kling動画プロンプト（動画化用）
                'kling_prompt': '',  # 後で生成
                
                # カメラワーク設定
                'camera_movement': self._get_camera_movement(i, num_scenes)
            }
            
            # プロンプト生成
            scene['midjourney_prompt'] = self._create_midjourney_prompt(scene)
            scene['kling_prompt'] = self._create_kling_prompt(scene)
            
            script['scenes'].append(scene)
        
        return script
    
    def _generate_scene_narrative(self, scene_index: int, total_scenes: int, title: str) -> str:
        """シーンのナラティブ生成"""
        
        # 起承転結構成
        if scene_index == 0:
            return f"オープニング: {title}の物語が始まる。主人公の日本人女性が登場。朝の光の中で新しい一日が始まる。"
        elif scene_index < total_scenes // 3:
            return f"導入部: 主人公が日常から旅立つ準備をする。期待と不安が入り混じる表情。"
        elif scene_index < total_scenes * 2 // 3:
            return f"展開部: 冒険の中で様々な体験をする主人公。成長と発見の瞬間。"
        elif scene_index < total_scenes - 1:
            return f"クライマックス: 最も重要な瞬間に直面する主人公。決意と勇気。"
        else:
            return f"エンディング: 物語の結末。新しい自分を見つけた主人公の満足げな表情。"
    
    def _generate_character_description(self, scene_index: int, total_scenes: int) -> str:
        """キャラクター描写（一貫性保持）"""
        
        # 基本設定（全シーン共通）
        base = "beautiful Japanese woman, 25 years old, long black hair, delicate features"
        
        # シーンごとの服装・表情
        if scene_index == 0:
            return f"{base}, wearing white summer dress, gentle smile, morning sunlight"
        elif scene_index < total_scenes // 2:
            return f"{base}, wearing white summer dress, thoughtful expression, natural lighting"
        else:
            return f"{base}, wearing white summer dress, confident smile, golden hour lighting"
    
    def _get_camera_movement(self, scene_index: int, total_scenes: int) -> Dict[str, Any]:
        """カメラワーク設定"""
        
        movements = [
            {"type": "zoom_in", "horizontal": 0, "vertical": 0, "zoom": 10},
            {"type": "pan_right", "horizontal": 10, "vertical": 0, "zoom": 0},
            {"type": "tilt_up", "horizontal": 0, "vertical": 10, "zoom": 0},
            {"type": "orbit", "horizontal": -10, "vertical": 5, "zoom": 5},
            {"type": "static", "horizontal": 0, "vertical": 0, "zoom": 0}
        ]
        
        return movements[scene_index % len(movements)]
    
    def _create_midjourney_prompt(self, scene: Dict[str, Any]) -> str:
        """Midjourney用プロンプト生成"""
        
        prompt = f"{scene['character_description']}, {scene['narrative']}, "
        prompt += f"{self.character_style}, cinematic composition, "
        prompt += f"8k resolution, professional photography --ar 16:9 --v 6 --style raw"
        
        return prompt
    
    def _create_kling_prompt(self, scene: Dict[str, Any]) -> str:
        """Kling動画用プロンプト生成"""
        
        camera = scene['camera_movement']
        
        prompt = f"{scene['character_description']} in motion, "
        prompt += f"{camera['type']} camera movement, "
        prompt += f"smooth cinematic sequence, natural movement"
        
        return prompt
    
    def generate_image_with_midjourney(self, prompt: str) -> Dict[str, Any]:
        """Midjourneyで画像生成"""
        
        # PIAPI v1 APIを使用
        url = "https://api.piapi.ai/api/v1/task"
        
        headers = {
            "X-API-Key": self.piapi_xkey,
            "Content-Type": "application/json"
        }
        
        # Midjourney用のペイロード
        payload = {
            "model": "midjourney",
            "task_type": "imagine",
            "input": {
                "prompt": prompt + " --ar 16:9 --v 6",  # アスペクト比とバージョンを追加
                "process_mode": "fast"
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
                        st.info(f"🎨 Midjourney Task ID: {task_id[:8]}...")
                        
                        # ポーリングして結果取得
                        image_url = self._poll_midjourney_task(task_id)
                        
                        if image_url:
                            return {
                                'status': 'success',
                                'image_url': image_url,
                                'task_id': task_id,
                                'message': 'Midjourney画像生成成功'
                            }
                        else:
                            return {
                                'status': 'error',
                                'message': 'Midjourney画像生成タイムアウト'
                            }
                    else:
                        return {
                            'status': 'error',
                            'message': 'Task ID が取得できませんでした'
                        }
                else:
                    return {
                        'status': 'error',
                        'message': f'API Error: {result.get("message", "Unknown error")}'
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP Error: {response.status_code}'
                }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Exception: {str(e)}'
            }
    
    def _poll_midjourney_task(self, task_id: str, max_attempts: int = 60) -> Optional[str]:
        """Midjourneyタスクのポーリング（最大3分待機）"""
        
        # PIAPI v1 APIのタスク状態確認
        url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        headers = {"X-API-Key": self.piapi_xkey}
        
        progress_text = st.empty()
        
        for i in range(max_attempts):
            progress_text.text(f"⏳ Midjourney処理中... [{i+1}/{max_attempts}]")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('code') == 200:
                        data = result.get('data', {})
                        status = data.get('status', 'pending')
                        
                        if status == 'completed':
                            output = data.get('output', {})
                            
                            # Midjourneyの出力フォーマットを確認
                            # 画像URLの取得（複数のフォーマットに対応）
                            image_url = None
                            
                            # パターン1: image_url直接
                            if output.get('image_url'):
                                image_url = output['image_url']
                            
                            # パターン2: images配列
                            elif output.get('images') and len(output['images']) > 0:
                                image_url = output['images'][0]
                            
                            # パターン3: imageUrls配列
                            elif output.get('imageUrls') and len(output['imageUrls']) > 0:
                                image_url = output['imageUrls'][0]
                            
                            # パターン4: url直接
                            elif output.get('url'):
                                image_url = output['url']
                            
                            # パターン5: result内
                            elif output.get('result'):
                                if isinstance(output['result'], str):
                                    image_url = output['result']
                                elif isinstance(output['result'], dict):
                                    image_url = output['result'].get('url') or output['result'].get('image_url')
                            
                            if image_url:
                                progress_text.success("✅ Midjourney画像生成完了!")
                                return image_url
                            else:
                                # デバッグ情報を表示
                                st.warning(f"画像URLが見つかりません。Output: {output}")
                                return None
                        
                        elif status in ['failed', 'error', 'cancelled']:
                            error_msg = data.get('error', {}).get('message', 'Unknown error')
                            progress_text.error(f"❌ 生成失敗: {error_msg}")
                            return None
                
            except Exception as e:
                if i == max_attempts - 1:
                    progress_text.error(f"❌ エラー: {str(e)}")
            
            time.sleep(3)  # 3秒待機
        
        progress_text.warning("⏱️ タイムアウト")
        return None
    
    def generate_video_with_kling(self, 
                                 image_url: str,
                                 prompt: str,
                                 duration: int = 5,
                                 camera_horizontal: int = 0,
                                 camera_vertical: int = 0,
                                 camera_zoom: int = 0) -> Dict[str, Any]:
        """Klingで画像から動画生成（Image-to-Video）"""
        
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
                "image_url": image_url,  # 画像URLを追加
                "negative_prompt": "",
                "cfg_scale": 0.5,
                "duration": duration,
                "aspect_ratio": "16:9",
                "camera_control": {
                    "type": "simple",
                    "config": {
                        "horizontal": camera_horizontal,
                        "vertical": camera_vertical,
                        "pan": 0,
                        "tilt": 0,
                        "roll": 0,
                        "zoom": camera_zoom
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
                        # ポーリングして結果取得
                        video_url = self._poll_kling_task(task_id)
                        
                        if video_url:
                            return {
                                'status': 'success',
                                'video_url': video_url,
                                'task_id': task_id
                            }
            
            return {'status': 'error', 'message': f'Kling失敗: {response.status_code}'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Kling例外: {str(e)}'}
    
    def _poll_kling_task(self, task_id: str, max_attempts: int = 120) -> Optional[str]:
        """Klingタスクのポーリング（最大20分待機）"""
        
        url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        headers = {"X-API-Key": self.piapi_xkey}
        
        # プログレス表示（Streamlit）
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for i in range(max_attempts):
            # プログレス更新
            if hasattr(st, 'progress'):
                progress = (i + 1) / max_attempts
                progress_bar.progress(progress)
                status_text.text(f"⏳ Kling動画生成中... [{i+1}/{max_attempts}] ({i*10}秒経過)")
            
            time.sleep(10)  # 10秒ごとにチェック
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    data = result.get('data', {})
                    status = data.get('status', 'unknown')
                    
                    if status == 'completed':
                        output = data.get('output', {})
                        works = output.get('works', [])
                        
                        if works and len(works) > 0:
                            for work in works:
                                if work.get('resource'):
                                    return work['resource']
                    
                    elif status in ['failed', 'error']:
                        return None
                        
            except Exception:
                pass
        
        return None
    
    def process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """シーンを処理（画像生成→動画生成）"""
        
        st.markdown(f"### 🎬 シーン{scene['scene_number']}の処理")
        
        # シーンの詳細を表示
        with st.expander(f"📝 シーン{scene['scene_number']}の詳細", expanded=True):
            st.write(f"**ナラティブ:** {scene['narrative']}")
            st.write(f"**キャラクター:** {scene['character_description']}")
            st.write(f"**時間:** {scene['time_range']}")
        
        # 画像生成セクション
        st.markdown("#### 🎨 画像生成")
        
        # プロンプトを編集可能にする
        edited_prompt = st.text_area(
            f"Midjourneyプロンプト（編集可能）",
            value=scene['midjourney_prompt'],
            key=f"prompt_scene_{scene['scene_number']}",
            height=100
        )
        
        # 画像生成ボタン
        col1, col2 = st.columns([1, 3])
        with col1:
            generate_image = st.button(
                "🎨 画像生成",
                key=f"gen_img_{scene['scene_number']}",
                type="primary"
            )
        with col2:
            regenerate_image = st.button(
                "🔄 画像再生成",
                key=f"regen_img_{scene['scene_number']}"
            )
        
        # 画像生成/再生成処理
        image_result = None
        if generate_image or regenerate_image:
            with st.spinner(f"🎨 画像生成中..."):
                image_result = self.generate_image_with_midjourney(edited_prompt)
                
                if image_result['status'] == 'success':
                    st.success("✅ 画像生成成功")
                    # セッションに保存
                    st.session_state[f"image_url_scene_{scene['scene_number']}"] = image_result['image_url']
                else:
                    st.error(f"❌ 画像生成失敗: {image_result.get('message')}")
                    return image_result
        
        # 保存された画像を表示
        saved_image_url = st.session_state.get(f"image_url_scene_{scene['scene_number']}")
        if saved_image_url:
            st.image(saved_image_url, caption=f"シーン{scene['scene_number']}")
            image_result = {'status': 'success', 'image_url': saved_image_url}
        elif not image_result:
            st.info("👆 上のボタンで画像を生成してください")
            return {'status': 'pending', 'message': '画像生成待ち'}
        
        # 動画生成セクション
        st.markdown("#### 🎥 動画生成")
        
        # 動画生成ボタン（画像が生成されている場合のみ）
        if image_result and image_result['status'] == 'success':
            # Kling動画プロンプトを編集可能にする
            edited_video_prompt = st.text_area(
                f"Kling動画プロンプト（編集可能）",
                value=scene['kling_prompt'],
                key=f"video_prompt_scene_{scene['scene_number']}",
                height=80
            )
            
            # カメラ設定
            col1, col2, col3 = st.columns(3)
            with col1:
                horizontal = st.slider(
                    "水平移動",
                    -20, 20,
                    scene['camera_movement']['horizontal'],
                    key=f"h_scene_{scene['scene_number']}"
                )
            with col2:
                vertical = st.slider(
                    "垂直移動",
                    -20, 20,
                    scene['camera_movement']['vertical'],
                    key=f"v_scene_{scene['scene_number']}"
                )
            with col3:
                zoom = st.slider(
                    "ズーム",
                    -20, 20,
                    scene['camera_movement']['zoom'],
                    key=f"z_scene_{scene['scene_number']}"
                )
            
            # 動画生成ボタン
            if st.button(f"🎥 動画生成", key=f"gen_video_{scene['scene_number']}", type="primary"):
                with st.spinner(f"🎥 Kling動画生成中（最大20分かかる場合があります）..."):
                    video_result = self.generate_video_with_kling(
                        image_url=image_result['image_url'],
                        prompt=edited_video_prompt,
                        duration=scene['duration'],
                        camera_movement={
                            "horizontal": horizontal,
                            "vertical": vertical,
                            "zoom": zoom
                        }
                    )
                    
                    if video_result['status'] == 'success':
                        st.success("✅ 動画生成成功")
                        st.session_state[f"video_url_scene_{scene['scene_number']}"] = video_result['video_url']
                    else:
                        st.error(f"❌ 動画生成失敗: {video_result.get('message')}")
            
            # 保存された動画を表示
            saved_video_url = st.session_state.get(f"video_url_scene_{scene['scene_number']}")
            if saved_video_url:
                st.video(saved_video_url)
                video_result = {'status': 'success', 'video_url': saved_video_url}
            else:
                video_result = {'status': 'pending'}
        else:
            st.info("👆 先に画像を生成してください")
            video_result = {'status': 'pending'}
        
        return {
            'scene_number': scene['scene_number'],
            'image_url': image_result.get('image_url'),
            'video_url': video_result.get('video_url'),
            'status': video_result.get('status')
        }
    
    def execute_workflow(self, title: str, description: str, duration: int = 180) -> List[Dict[str, Any]]:
        """完全なワークフローを実行"""
        
        # Step 1: 詳細台本生成
        st.markdown("## 📝 Step 1: 詳細台本生成")
        script = self.generate_detailed_script(title, description, duration)
        
        # 台本表示
        with st.expander("📜 生成された台本", expanded=False):
            for scene in script['scenes']:
                st.markdown(f"**シーン{scene['scene_number']}** ({scene['time_range']})")
                st.write(f"ナラティブ: {scene['narrative']}")
                st.write(f"キャラクター: {scene['character_description']}")
                st.write(f"Midjourneyプロンプト: {scene['midjourney_prompt'][:100]}...")
                st.write("---")
        
        # Step 2: 各シーンを処理
        st.markdown("## 🎬 Step 2: 画像生成→動画生成")
        results = []
        
        for scene in script['scenes']:
            result = self.process_scene(scene)
            results.append(result)
        
        # Step 3: 結果サマリー
        st.markdown("## 📊 Step 3: 生成結果")
        
        success_count = sum(1 for r in results if r.get('status') == 'success')
        st.metric("成功したシーン", f"{success_count}/{len(results)}")
        
        return results

# Streamlit UI
def create_image_to_video_ui():
    """Streamlit UI作成"""
    
    st.title("🎬 画像→動画ワークフロー v5.0.0")
    st.markdown("Midjourney → Kling（日本人女性キャラクター一貫性保持）")
    
    # 初期化
    if 'workflow' not in st.session_state:
        st.session_state.workflow = ImageToVideoWorkflow()
    
    # 入力フォーム
    with st.form("workflow_form"):
        title = st.text_input("PVタイトル", value="美しい日本の四季")
        description = st.text_area(
            "概要説明",
            value="日本人女性が四季の移り変わりとともに成長していく物語",
            height=100
        )
        duration = st.slider("動画の長さ（秒）", 30, 300, 180)
        
        submitted = st.form_submit_button("🚀 ワークフロー開始", type="primary")
    
    if submitted:
        with st.spinner("ワークフロー実行中..."):
            results = st.session_state.workflow.execute_workflow(title, description, duration)
            
            # 結果を保存
            st.session_state.last_results = results
            
            st.success("✅ ワークフロー完了！")
            st.balloons()

if __name__ == "__main__":
    create_image_to_video_ui()