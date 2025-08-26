#!/usr/bin/env python3
"""
Google GenAI SDK経由でVeo 3.0を使用
"""

import time
import os
from pathlib import Path

def test_veo3_with_genai():
    """Google GenAI SDKでVeo 3.0をテスト"""
    
    print("=" * 60)
    print("🎬 Google GenAI SDK - Veo 3.0テスト")
    print("=" * 60)
    
    try:
        # Google GenAI SDKをインポート
        from google import genai
        from google.genai import types
        
        print("✅ Google GenAI SDKインポート成功")
        
    except ImportError:
        print("⚠️ Google GenAI SDKがインストールされていません")
        print("\n📦 インストールコマンド:")
        print("pip install google-genai")
        return False
    
    # APIキーを設定
    api_key = "AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8"
    os.environ["GOOGLE_API_KEY"] = api_key
    
    print(f"🔑 APIキー設定完了")
    
    # クライアントを初期化
    try:
        client = genai.Client(api_key=api_key)
        print("✅ GenAIクライアント初期化成功")
    except Exception as e:
        print(f"❌ クライアント初期化エラー: {e}")
        return False
    
    # テストプロンプト
    test_prompt = "大空に新しい太陽が昇る、美しい朝焼けの風景、雲がゆっくりと流れる"
    
    print(f"\n📝 プロンプト: {test_prompt}")
    print("\n🎥 Veo 3.0で動画生成を開始...")
    
    try:
        # Veo 3.0で動画生成
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=test_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                duration_seconds=5,
                enhance_prompt=True,
                generate_audio=True,
                sample_count=1,
                negative_prompt=""
            ),
        )
        
        print(f"✅ 生成リクエスト送信成功")
        print(f"Operation ID: {operation.name if hasattr(operation, 'name') else 'N/A'}")
        
        # 動画生成を待機
        print("\n⏳ 動画生成中...")
        wait_count = 0
        max_wait = 30  # 最大10分待機
        
        while not operation.done:
            wait_count += 1
            print(f"  [{wait_count}/{max_wait}] 処理中... (20秒待機)")
            time.sleep(20)
            
            try:
                operation = client.operations.get(operation)
            except Exception as e:
                print(f"⚠️ ステータス取得エラー: {e}")
                
            if wait_count >= max_wait:
                print("\n⏱️ タイムアウト（10分）")
                return False
        
        # 結果を取得
        if hasattr(operation, 'result') and operation.result:
            generated_videos = operation.result.generated_videos
            
            if generated_videos and len(generated_videos) > 0:
                print(f"\n🎉 動画生成完了!")
                generated_video = generated_videos[0]
                
                # 動画をダウンロード
                output_path = Path("veo3_test_video.mp4")
                
                try:
                    # 動画ファイルをダウンロード
                    client.files.download(file=generated_video.video)
                    generated_video.video.save(str(output_path))
                    
                    print(f"✅ 動画を保存しました: {output_path}")
                    print(f"ファイルサイズ: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
                    
                except Exception as e:
                    print(f"⚠️ ダウンロードエラー: {e}")
                    print(f"動画URL: {generated_video.video.uri if hasattr(generated_video.video, 'uri') else 'N/A'}")
                
                return True
            else:
                print("\n❌ 生成された動画がありません")
                return False
        else:
            if hasattr(operation, 'error'):
                print(f"\n❌ エラー: {operation.error}")
            else:
                print("\n❌ 不明なエラー")
            return False
            
    except Exception as e:
        print(f"\n❌ 生成エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラーの詳細を確認
        if "not allowlisted" in str(e):
            print("\n⚠️ Veo 3.0はアクセス許可が必要です")
            print("代替案を試します...")
            
            # Veo 2.0を試す
            return test_veo2_fallback(client, test_prompt)
        
        return False

def test_veo2_fallback(client, prompt):
    """Veo 2.0にフォールバック"""
    
    print("\n" + "=" * 60)
    print("🔄 Veo 2.0フォールバック")
    print("=" * 60)
    
    try:
        from google.genai import types
        
        # Veo 2.0で試す
        operation = client.models.generate_videos(
            model="veo-generate",  # Veo 2.0
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="16:9",
                duration_seconds=3,
                sample_count=1
            ),
        )
        
        print("✅ Veo 2.0リクエスト送信成功")
        
        # 待機
        wait_count = 0
        while not operation.done and wait_count < 15:
            wait_count += 1
            print(f"  [{wait_count}/15] 処理中...")
            time.sleep(20)
            operation = client.operations.get(operation)
        
        if operation.done and hasattr(operation, 'result'):
            print("✅ Veo 2.0で生成成功")
            return True
        else:
            print("❌ Veo 2.0でも失敗")
            return False
            
    except Exception as e:
        print(f"❌ Veo 2.0エラー: {e}")
        return False

def install_genai_sdk():
    """Google GenAI SDKをインストール"""
    
    print("\n📦 Google GenAI SDKをインストール中...")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ["pip", "install", "google-genai"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ インストール成功")
            return True
        else:
            print(f"❌ インストール失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ インストールエラー: {e}")
        return False

if __name__ == "__main__":
    # GenAI SDKがない場合はインストール
    try:
        from google import genai
    except ImportError:
        if install_genai_sdk():
            print("\n🔄 SDKをインストールしました。再実行してください。")
        else:
            print("\n❌ SDKのインストールに失敗しました")
            print("手動でインストールしてください: pip install google-genai")
        exit(1)
    
    # テスト実行
    success = test_veo3_with_genai()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Veo動画生成テスト成功！")
    else:
        print("⚠️ 動画生成に失敗しました")
        print("\n代替手段：")
        print("1. Veo 3.0へのアクセス申請")
        print("2. Stability AI API")
        print("3. RunComfy API")
        print("4. PIAPI Hailuo")
    print("=" * 60)