"""
OpenAI DALL-E 3 統合モジュール
Midjourneyの代替として画像生成
"""

import streamlit as st
import requests
import json
import time
from typing import Dict, Any, List, Optional
import base64
from io import BytesIO
from openai import OpenAI

class DALLEClient:
    """DALL-E 3 統合クライアント"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key and api_key != 'demo':
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        DALL-E 3で画像生成
        
        Args:
            prompt: 画像生成プロンプト
            kwargs: 追加パラメータ（size, quality, style等）
        
        Returns:
            生成結果
        """
        if not self.client:
            return {
                "status": "error",
                "message": "OpenAI APIキーが設定されていません"
            }
        
        try:
            # DALL-E 3のパラメータ
            size = kwargs.get("size", "1792x1024")  # 16:9に近いサイズ
            quality = kwargs.get("quality", "standard")  # standard or hd
            style = kwargs.get("style", "natural")  # natural or vivid
            
            # Midjourneyスタイルのパラメータを削除（DALL-Eには不要）
            clean_prompt = prompt
            if "--" in prompt:
                # --ar, --v, --style等のパラメータを削除
                clean_prompt = prompt.split("--")[0].strip()
            
            # DALL-E 3で画像生成
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=clean_prompt,
                size=size,
                quality=quality,
                style=style,
                n=1  # DALL-E 3は1枚ずつしか生成できない
            )
            
            # 画像URLを取得
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            return {
                "status": "success",
                "image_url": image_url,
                "revised_prompt": revised_prompt,
                "message": "画像生成完了"
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # エラーの種類を判定
            if "quota" in error_msg.lower() or "limit" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "OpenAI APIの使用制限に達しました",
                    "details": error_msg
                }
            elif "api_key" in error_msg.lower():
                return {
                    "status": "error",
                    "message": "APIキーが無効です",
                    "details": error_msg
                }
            else:
                return {
                    "status": "error",
                    "message": f"画像生成エラー: {error_msg}",
                    "details": error_msg
                }


def generate_images_with_dalle(script: Dict, character_photos: Optional[List] = None) -> List[Dict]:
    """
    DALL-E 3を使用して台本から画像を生成
    
    Args:
        script: 確定した台本
        character_photos: キャラクター写真（DALL-Eでは参照画像は使用不可）
    
    Returns:
        生成された画像情報リスト
    """
    # APIキーを取得
    openai_key = st.session_state.api_keys.get('openai', '')
    
    # デモモード（APIキーがない場合）
    demo_mode = not openai_key or openai_key == 'demo'
    
    if demo_mode:
        st.warning("⚠️ OpenAI APIキーが設定されていません。デモモードで実行します。")
    
    scenes = script.get('scenes', [])
    total_scenes = len(scenes)
    
    # デバッグ情報
    st.info(f"📊 シーン数: {total_scenes}")
    
    if character_photos:
        st.warning("⚠️ DALL-E 3では参照画像による一貫性は保持できません")
    
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
                "status": "completed",
                "prompt": scene.get('visual_prompt', 'Demo prompt'),
                "time": scene.get('time', f'{i*10}-{(i+1)*10}'),
                "duration": scene.get('duration', 5),
                "result_url": f"https://via.placeholder.com/1792x1024.png?text=DALL-E+Demo+Scene+{i+1}",
                "generator": "dalle-demo"
            })
            
            time.sleep(0.1)  # デモの演出
        
        progress_bar.progress(1.0)
        status_text.success(f"✅ デモモード: {len(generated_images)}枚の画像を仮生成しました")
        return generated_images
    
    # 実際のDALL-E API呼び出し
    try:
        client = DALLEClient(openai_key)
        generated_images = []
        
        # DALL-Eは1枚ずつ生成（並列処理不可）
        for i, scene in enumerate(scenes):
            scene_id = scene.get('id', f'scene_{i+1}')
            status_text.text(f"DALL-E 3でシーン {scene_id} を生成中... ({i+1}/{total_scenes})")
            progress_bar.progress((i + 1) / total_scenes)
            
            # visual_promptが存在するか確認
            if 'visual_prompt' not in scene:
                st.warning(f"⚠️ シーン{i+1}にvisual_promptがありません")
                continue
            
            # サイズ設定（16:9に近い）
            size_options = {
                "16:9": "1792x1024",
                "9:16": "1024x1792",
                "1:1": "1024x1024"
            }
            
            result = client.generate_image(
                scene['visual_prompt'],
                size=size_options.get("16:9", "1792x1024"),
                quality="standard",  # hdは2倍のコスト
                style="natural"  # より写実的
            )
            
            if result.get("status") == "error":
                st.error(f"シーン{i+1}の生成エラー: {result.get('message')}")
                if "limit" in result.get('message', '').lower():
                    st.info("💡 OpenAIの使用制限に達しました。しばらく待つか、他のモデルを使用してください。")
                    break
                continue
            
            generated_images.append({
                "scene_id": scene_id,
                "status": "completed",
                "prompt": scene['visual_prompt'],
                "revised_prompt": result.get('revised_prompt', ''),
                "time": scene.get('time', ''),
                "duration": scene.get('duration', 5),
                "result_url": result.get('image_url'),
                "generator": "dalle-3"
            })
            
            # API制限対策（DALL-E 3は1分あたりの制限あり）
            if i < len(scenes) - 1:
                time.sleep(2)  # 2秒待機
        
        progress_bar.progress(1.0)
        status_text.success(f"✅ DALL-E 3で{len(generated_images)}枚の画像生成が完了しました")
        
        return generated_images
        
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("💡 ヒント: OpenAI APIキーが正しく設定されているか確認してください")
        return []