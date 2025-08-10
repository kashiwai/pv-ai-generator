"""
PIAPI統合モジュール
Hailuo, Midjourney等のAIサービスをPIAPI経由で利用
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO

class PIAPIClient:
    """PIAPI統合クライアント"""
    
    def __init__(self, api_key: str, x_key: str = None, base_url: str = "https://api.piapi.ai"):
        self.api_key = api_key
        self.x_key = x_key if x_key else api_key  # XKEYがなければメインキーを使用
        self.base_url = base_url
        
        # デバッグ: APIキーの長さを確認（デモモード以外の場合のみ）
        if self.x_key and self.x_key != 'demo':
            # デバッグモードの場合のみ表示（通常は非表示）
            pass  # st.info(f"🔑 APIキー設定: {self.x_key[:8]}...（{len(self.x_key)}文字）")
        
        self.headers = {
            "x-api-key": self.x_key,  # PIAPIはx-api-keyヘッダーを使用
            "Content-Type": "application/json"
        }
    
    def generate_image_midjourney(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Midjourney経由で画像生成
        
        Args:
            prompt: 画像生成プロンプト
            kwargs: 追加パラメータ（aspect_ratio, process_mode等）
        
        Returns:
            生成結果
        """
        endpoint = f"{self.base_url}/api/v1/task"
        
        # プロンプトが空でないか確認
        if not prompt or prompt.strip() == "":
            return {
                "status": "error",
                "message": "プロンプトが空です",
                "details": "visual_promptが設定されていません"
            }
        
        # アスペクト比の処理
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        if aspect_ratio == "16:9 (推奨)":
            aspect_ratio = "16:9"
        
        # プロンプトがすでにMidjourneyパラメータを含んでいるか確認
        if "--ar" in prompt and "--v" in prompt:
            # すでにパラメータがある場合はそのまま使用
            full_prompt = prompt
        else:
            # パラメータがない場合は追加
            full_prompt = f"{prompt} --ar {aspect_ratio} --v 6"
            if kwargs.get("style"):
                full_prompt += f" --style {kwargs.get('style')}"
            if kwargs.get("quality"):
                full_prompt += f" --q {kwargs.get('quality')}"
        
        payload = {
            "model": "midjourney",
            "task_type": "imagine",
            "input": {
                "prompt": full_prompt,
                "aspect_ratio": aspect_ratio,
                "process_mode": kwargs.get("process_mode", "relax"),  # relax, fast, turbo
                "skip_prompt_check": kwargs.get("skip_prompt_check", False)
            }
        }
        
        # デバッグ: リクエスト情報を表示（デバッグモードの場合のみ）
        DEBUG_MODE = False  # デバッグを無効化
        if DEBUG_MODE:
            with st.expander("🔍 APIリクエストデバッグ情報"):
                st.write(f"**エンドポイント:** {endpoint}")
                st.write(f"**ヘッダー:** x-api-key = {self.headers.get('x-api-key', '')[:8]}...")
                st.json(payload)
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            
            # デバッグ: レスポンス情報（デバッグモードの場合のみ）
            if DEBUG_MODE:
                st.write(f"**レスポンスステータス:** {response.status_code}")
                
                if response.status_code != 200:
                    st.error(f"❌ APIエラー: ステータスコード {response.status_code}")
                    st.code(response.text)
            
            response.raise_for_status()
            result = response.json()
            
            # デバッグ: レスポンス内容（デバッグモードの場合のみ）
            if DEBUG_MODE:
                with st.expander("📥 APIレスポンス"):
                    st.json(result)
            
            # タスクIDを返して、後でステータスを確認
            task_id = None
            if isinstance(result, dict):
                if 'data' in result and isinstance(result['data'], dict):
                    task_id = result['data'].get('task_id')
                elif 'task_id' in result:
                    task_id = result['task_id']
            
            if not task_id:
                st.warning("⚠️ レスポンスにtask_idが含まれていません")
            
            return {
                "status": "success" if task_id else "error",
                "task_id": task_id,
                "message": "画像生成を開始しました" if task_id else "task_idが取得できませんでした",
                "response": result
            }
        except requests.exceptions.RequestException as e:
            error_details = ""
            if hasattr(e, 'response') and e.response:
                error_details = e.response.text
                try:
                    error_json = e.response.json()
                    error_details = json.dumps(error_json, indent=2)
                except:
                    pass
            
            return {
                "status": "error",
                "message": f"API request failed: {str(e)}",
                "details": error_details,
                "status_code": e.response.status_code if hasattr(e, 'response') else None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "details": str(type(e))
            }
    
    def generate_video_hailuo(self, image_url: str, prompt: str, duration: int = 5) -> Dict[str, Any]:
        """
        Hailuo AI経由で動画生成
        
        Args:
            image_url: 元画像のURL
            prompt: 動画生成プロンプト
            duration: 動画の長さ（秒）
        
        Returns:
            生成結果
        """
        endpoint = f"{self.base_url}/hailuo/generate"
        
        payload = {
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
            "motion_intensity": 5,  # 1-10のスケール
            "camera_movement": "auto"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "job_id": result.get("job_id"),
                "message": "動画生成を開始しました"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def check_job_status(self, task_id: str, service: str = "midjourney") -> Dict[str, Any]:
        """
        タスクのステータスを確認
        
        Args:
            task_id: タスクID
            service: サービス名（midjourney, hailuo等）
        
        Returns:
            ステータス情報
        """
        endpoint = f"{self.base_url}/api/v1/task/{task_id}"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            # ステータスの正規化（大文字小文字の違いを吸収）
            status = result.get("status", "processing").lower()
            if status == "completed":
                status = "completed"
            elif status in ["processing", "pending", "staged"]:
                status = "processing"
            elif status == "failed":
                status = "error"
            
            # 出力データの取得
            output = result.get("output", {})
            image_url = output.get("image_url", "")
            progress = output.get("progress", 0)
            
            return {
                "status": status,
                "progress": progress,
                "result_url": image_url,
                "message": f"Status: {result.get('status', 'unknown')}",
                "raw_response": result
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Status check failed: {str(e)}",
                "details": e.response.text if hasattr(e, 'response') else None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def upload_character_photo(self, photo) -> str:
        """
        キャラクター写真をアップロードしてURLを取得
        
        Args:
            photo: アップロードする写真
        
        Returns:
            写真のURL
        """
        endpoint = f"{self.base_url}/upload/image"
        
        try:
            photo_bytes = photo.read()
            photo.seek(0)
            base64_image = base64.b64encode(photo_bytes).decode('utf-8')
            
            payload = {
                "image": f"data:image/jpeg;base64,{base64_image}",
                "purpose": "character_reference"
            }
            
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return result.get("url", "")
        except Exception as e:
            return None
    
    def generate_character_consistent_images(self, character_photos: List, scenes: List[Dict]) -> List[Dict]:
        """
        キャラクター一貫性のある画像を生成
        
        Args:
            character_photos: キャラクター写真リスト
            scenes: シーン情報リスト
        
        Returns:
            生成された画像情報リスト
        """
        generated_images = []
        
        # キャラクター写真をアップロードしてURLを取得
        character_urls = []
        for photo in character_photos[:1]:  # メイン写真1枚を使用
            url = self.upload_character_photo(photo)
            if url:
                character_urls.append(url)
        
        if not character_urls:
            # URL取得失敗の場合は通常の生成にフォールバック
            return self.generate_images_without_character(scenes)
        
        # メインキャラクターURL
        main_character_url = character_urls[0]
        
        for scene in scenes:
            # キャラクター参照を含むプロンプト生成
            # --crefがすでに含まれているか確認
            if '--cref' in scene.get('visual_prompt', ''):
                # すでにキャラクター参照がある場合はそのまま使用
                enhanced_prompt = scene['visual_prompt']
            else:
                # キャラクター参照を追加
                enhanced_prompt = f"{scene['visual_prompt']} --cref {main_character_url} --cw 100"
            
            result = self.generate_image_midjourney(enhanced_prompt)
            generated_images.append({
                "scene_id": scene['id'],
                "task_id": result.get("task_id"),  # job_idではなくtask_id
                "status": "generating",
                "prompt": enhanced_prompt,
                "character_url": main_character_url,  # キャラクターURLを保存
                "has_character": True
            })
        
        return generated_images
    
    def generate_images_without_character(self, scenes: List[Dict]) -> List[Dict]:
        """
        キャラクターなしで画像を生成
        """
        generated_images = []
        for scene in scenes:
            result = self.generate_image_midjourney(scene.get('visual_prompt', ''))
            generated_images.append({
                "scene_id": scene['id'],
                "task_id": result.get("task_id"),  # job_idではなくtask_id
                "status": "generating",
                "prompt": scene.get('visual_prompt', ''),
                "has_character": False
            })
        return generated_images
    
    def create_pv_from_images(self, images: List[Dict], music_info: Dict) -> Dict[str, Any]:
        """
        画像から完全なPVを作成
        
        Args:
            images: 生成された画像リスト
            music_info: 音楽情報
        
        Returns:
            PV生成結果
        """
        video_segments = []
        
        # 各画像から動画セグメントを生成
        for image in images:
            if image.get("result_url"):
                video_result = self.generate_video_hailuo(
                    image_url=image["result_url"],
                    prompt=f"Smooth camera movement, {image.get('prompt', '')}",
                    duration=image.get("duration", 5)
                )
                video_segments.append(video_result)
        
        # 動画セグメントを結合（PIAPIの動画結合エンドポイントを使用）
        endpoint = f"{self.base_url}/video/merge"
        
        payload = {
            "segments": [seg["job_id"] for seg in video_segments if seg.get("job_id")],
            "music_url": music_info.get("url"),
            "duration": music_info.get("duration"),
            "transitions": "smooth",
            "output_format": "mp4",
            "resolution": "1920x1080"
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "job_id": result.get("job_id"),
                "message": "PV生成を開始しました"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


def generate_images_with_piapi(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    PIAPIを使用して台本から画像を生成
    
    Args:
        script: 確定した台本
        character_photos: キャラクター写真（オプション）
    
    Returns:
        生成された画像情報リスト
    """
    # APIキーを取得（メインKEYとXKEY）
    piapi_key = st.session_state.api_keys.get('piapi', '')
    piapi_xkey = st.session_state.api_keys.get('piapi_xkey', '')
    
    # デモモード（APIキーがない場合）
    demo_mode = not piapi_key or piapi_key == 'demo'
    
    if not piapi_key:
        st.warning("⚠️ PIAPIキーが設定されていません。デモモードで実行します。")
        demo_mode = True
    
    scenes = script.get('scenes', [])
    total_scenes = len(scenes)
    
    # デバッグ情報
    st.info(f"📊 シーン数: {total_scenes}")
    
    # シーンの内容を確認
    if total_scenes > 0:
        first_scene = scenes[0]
        st.info(f"🔍 最初のシーンの内容確認:")
        st.write(f"- ID: {first_scene.get('id', 'なし')}")
        st.write(f"- visual_prompt: {first_scene.get('visual_prompt', 'なし')[:100] if first_scene.get('visual_prompt') else '❌ visual_promptがありません'}")
        st.write(f"- time: {first_scene.get('time', 'なし')}")
        st.write(f"- duration: {first_scene.get('duration', 'なし')}")
    
    # プログレスバー表示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    if demo_mode:
        # デモモード：ダミーデータを返す
        st.info("🎭 デモモードで実行中...")
        generated_images = []
        
        for i, scene in enumerate(scenes):
            status_text.text(f"デモ: シーン {scene.get('id', i+1)} を生成中... ({i+1}/{total_scenes})")
            progress_bar.progress((i + 1) / total_scenes)
            
            # デモ用のダミーデータ
            generated_images.append({
                "scene_id": scene.get('id', f'scene_{i+1}'),
                "task_id": f"demo_task_{i+1}",
                "status": "completed",
                "prompt": scene.get('visual_prompt', 'Demo prompt'),
                "time": scene.get('time', f'{i*10}-{(i+1)*10}'),
                "duration": scene.get('duration', 5),
                "result_url": "https://via.placeholder.com/1920x1080.png?text=Demo+Image+" + str(i+1)
            })
            
            time.sleep(0.1)  # デモの演出
        
        progress_bar.progress(1.0)
        status_text.success(f"✅ デモモード: {len(generated_images)}枚の画像を仮生成しました")
        return generated_images
    
    # 実際のAPI呼び出し
    try:
        client = PIAPIClient(piapi_key, piapi_xkey)
        generated_images = []
        
        if character_photos:
            # キャラクター一貫性のある画像生成
            status_text.text("キャラクター参照画像を処理中...")
            generated_images = client.generate_character_consistent_images(character_photos, scenes)
        else:
            # 通常の画像生成（2つずつバッチ処理）
            BATCH_SIZE = 2  # 一度に処理するシーン数
            
            for batch_start in range(0, len(scenes), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(scenes))
                batch_scenes = scenes[batch_start:batch_end]
                
                status_text.text(f"シーン {batch_start+1}-{batch_end} を生成中... ({batch_end}/{total_scenes})")
                
                # バッチ内のシーンを処理
                for i, scene in enumerate(batch_scenes):
                    actual_index = batch_start + i
                    scene_id = scene.get('id', f'scene_{actual_index+1}')
                    
                    # visual_promptが存在するか確認
                    if 'visual_prompt' not in scene:
                        st.warning(f"⚠️ シーン{actual_index+1}にvisual_promptがありません")
                        continue
                    
                    result = client.generate_image_midjourney(scene['visual_prompt'])
                    
                    # デバッグ情報
                    if result.get("status") == "error":
                        error_msg = result.get('message', '')
                        
                        # エラーの種類を判定
                        if "daily midjourney error limit" in error_msg.lower():
                            st.error(f"⚠️ デイリーリミットエラー")
                            st.info("本日のMidjourney APIの使用上限に達しました。明日まで待つか、プランをアップグレードしてください。")
                            return generated_images  # これ以上処理しない
                        elif "insufficient quota" in error_msg.lower():
                            st.error(f"💰 クレジット不足エラー")
                            st.info("PIAPIのクレジットが不足しています。")
                            return generated_images  # これ以上処理しない
                        else:
                            st.error(f"シーン{actual_index+1}のAPI呼び出しエラー: {error_msg}")
                        
                        if result.get('details'):
                            with st.expander("エラー詳細"):
                                st.code(result.get('details'))
                        continue
                    
                    generated_images.append({
                        "scene_id": scene_id,
                        "task_id": result.get("task_id"),  # job_idではなくtask_id
                        "status": "generating",
                        "prompt": scene['visual_prompt'],
                        "time": scene.get('time', ''),
                        "duration": scene.get('duration', 5)
                    })
                
                # プログレスバー更新
                progress_bar.progress(batch_end / total_scenes)
                
                # バッチ間の待機（API制限対策）
                if batch_end < len(scenes):
                    time.sleep(1.0)  # バッチ間は1秒待機
        
        # ジョブの完了を待つ
        if generated_images:
            status_text.text("画像生成の完了を待っています...")
            completed_images = wait_for_image_completion(client, generated_images)
        else:
            completed_images = []
        
        progress_bar.progress(1.0)
        status_text.success(f"✅ {len(completed_images)}枚の画像生成が完了しました")
        
        return completed_images
        
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 ヒント: PIAPIの2つのキー（メインKEYとXKEY）が正しく設定されているか確認してください")
        return []


def wait_for_image_completion(client: PIAPIClient, images: List[Dict], timeout: int = 300) -> List[Dict]:
    """
    画像生成の完了を待つ
    
    Args:
        client: PIAPIクライアント
        images: 生成中の画像リスト
        timeout: タイムアウト（秒）
    
    Returns:
        完成した画像リスト
    """
    start_time = time.time()
    completed_images = []
    
    while time.time() - start_time < timeout:
        all_completed = True
        
        for image in images:
            if image.get("status") != "completed":
                # task_idを使用してステータスチェック
                task_id = image.get("task_id")
                if not task_id:
                    image["status"] = "error"
                    image["error_message"] = "No task_id"
                    continue
                
                status = client.check_job_status(task_id)
                
                if status["status"] == "completed":
                    image["status"] = "completed"
                    image["result_url"] = status.get("result_url")
                    completed_images.append(image)
                elif status["status"] == "error":
                    image["status"] = "error"
                    image["error_message"] = status.get("message")
                    st.warning(f"タスク {task_id} でエラー: {status.get('message')}")
                else:
                    all_completed = False
                    # プログレス表示
                    if status.get("progress"):
                        image["progress"] = status["progress"]
        
        if all_completed:
            break
        
        time.sleep(5)  # 5秒ごとにチェック
    
    return completed_images


def create_pv_with_piapi(images: List[Dict], music_info: Dict, settings: Dict) -> Dict[str, Any]:
    """
    PIAPIを使用してPVを作成
    
    Args:
        images: 生成された画像リスト
        music_info: 音楽情報
        settings: 生成設定
    
    Returns:
        PV生成結果
    """
    # APIキーを取得（メインKEYとXKEY）
    piapi_key = st.session_state.api_keys.get('piapi', '')
    piapi_xkey = st.session_state.api_keys.get('piapi_xkey', '')
    
    if not piapi_key:
        st.error("PIAPIメインキーが設定されていません")
        return {"status": "error", "message": "APIキー未設定"}
    
    client = PIAPIClient(piapi_key, piapi_xkey)
    
    # PV作成開始
    with st.spinner("PVを生成中..."):
        result = client.create_pv_from_images(images, music_info)
    
    if result["status"] == "success":
        # 完了を待つ
        job_id = result["job_id"]
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        while True:
            status = client.check_job_status(job_id, "video")
            
            if status["status"] == "completed":
                progress_bar.progress(1.0)
                status_placeholder.success("✅ PV生成完了！")
                return {
                    "status": "success",
                    "video_url": status.get("result_url"),
                    "job_id": job_id
                }
            elif status["status"] == "error":
                status_placeholder.error(f"❌ エラー: {status.get('message')}")
                return {
                    "status": "error",
                    "message": status.get("message")
                }
            else:
                progress = status.get("progress", 0) / 100
                progress_bar.progress(progress)
                status_placeholder.info(f"処理中... {status.get('message', '')}")
            
            time.sleep(5)
    
    return result