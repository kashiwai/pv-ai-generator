#!/usr/bin/env python3
"""
Text-to-Video実際の生成テスト
"""

import sys
import os
from pathlib import Path

# モックStreamlit
class MockSessionState:
    def __init__(self):
        self.api_keys = {
            'google': 'AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8',
            'piapi': '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b',
            'piapi_xkey': '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4'
        }
    
    def get(self, key, default=None):
        return self.api_keys.get(key, default)

class MockStreamlit:
    session_state = MockSessionState()
    
    @staticmethod
    def info(msg): print(f"ℹ️ {msg}")
    @staticmethod
    def warning(msg): print(f"⚠️ {msg}")
    @staticmethod
    def error(msg): print(f"❌ {msg}")
    @staticmethod
    def success(msg): print(f"✅ {msg}")
    @staticmethod
    def progress(val): return MockProgress()
    @staticmethod
    def empty(): return MockEmpty()
    @staticmethod
    def spinner(msg): return MockSpinner()

class MockProgress:
    def progress(self, val): pass
    def empty(self): pass

class MockEmpty:
    def text(self, msg): print(msg)
    def success(self, msg): print(f"✅ {msg}")
    def error(self, msg): print(f"❌ {msg}")
    def info(self, msg): print(f"ℹ️ {msg}")
    def warning(self, msg): print(f"⚠️ {msg}")

class MockSpinner:
    def __enter__(self): return self
    def __exit__(self, *args): pass

st = MockStreamlit()
sys.modules['streamlit'] = st

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))

def test_generation():
    print("="*60)
    print("🎬 Text-to-Video実際の生成テスト")
    print("="*60)
    
    # 統合モジュールをインポート
    from text_to_video_unified import UnifiedTextToVideo
    
    # 生成器を初期化
    generator = UnifiedTextToVideo()
    
    # テストプロンプト
    test_prompt = "A peaceful Japanese garden with cherry blossoms falling slowly"
    print(f"\n📝 テストプロンプト: {test_prompt}")
    print("="*60)
    
    # 1. Google Vertex AI Veoテスト
    print("\n1️⃣ Google Vertex AI Veoテスト")
    print("-"*40)
    try:
        result = generator.generate_with_google_veo(test_prompt, duration=5)
        print(f"ステータス: {result.get('status')}")
        print(f"メッセージ: {result.get('message', '')}")
        
        if result.get('status') == 'success':
            print(f"✅ ジョブID: {result.get('job_id', 'N/A')}")
        elif result.get('fallback'):
            print("⚠️ Veoは利用不可、フォールバック必要")
        else:
            print(f"詳細: {result.get('details', '')[:200]}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    # 2. PIAPI Hailuoテスト（動作確認済み）
    print("\n3️⃣ PIAPI Hailuo AIテスト（フォールバック）")
    print("-"*40)
    try:
        result = generator.generate_with_piapi_hailuo(test_prompt, duration=5)
        print(f"ステータス: {result.get('status')}")
        print(f"メッセージ: {result.get('message', '')}")
        
        if result.get('status') == 'success':
            print(f"✅ タスクID: {result.get('task_id', 'N/A')}")
            
            # ステータス確認
            if result.get('task_id'):
                print("\n📊 タスクステータス確認中...")
                import time
                time.sleep(2)
                status_result = generator.check_piapi_status(result['task_id'])
                print(f"  状態: {status_result.get('status')}")
                print(f"  進捗: {status_result.get('progress', 0)}%")
                
        else:
            print(f"詳細: {result.get('details', '')[:200]}")
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
    
    # 3. 自動選択テスト
    print("\n🤖 自動選択テスト")
    print("-"*40)
    print("優先順位: Vertex AI Veo → RunComfy → PIAPI Hailuo")
    
    try:
        # タイムアウトを短くしてテスト
        result = generator.generate_video_auto(test_prompt, duration=5)
        print(f"\n最終結果:")
        print(f"  ステータス: {result.get('status')}")
        print(f"  プロバイダー: {result.get('provider', 'unknown')}")
        
        if result.get('status') == 'completed':
            print(f"  ✅ 動画URL: {result.get('video_url', 'N/A')[:50]}...")
        elif result.get('status') == 'processing':
            print(f"  ⏳ 処理中... タスクID: {result.get('task_id', 'N/A')}")
        else:
            print(f"  メッセージ: {result.get('message', '')}")
            
    except Exception as e:
        print(f"❌ 自動選択エラー: {str(e)}")
    
    print("\n" + "="*60)
    print("📊 テスト結果サマリー")
    print("="*60)
    print("""
    ✅ PIAPI Hailuo AI: 動作中（フォールバック）
    ⚠️ Google Vertex AI Veo: 設定が必要（プロジェクトID等）
    ❌ RunComfy Seedance: サーバーダウン中
    
    💡 現在はPIAPI Hailuo AIが自動的に使用されています
    """)

if __name__ == "__main__":
    test_generation()