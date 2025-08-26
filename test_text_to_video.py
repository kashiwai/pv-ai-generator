#!/usr/bin/env python3
"""
Text-to-Video機能のテストスクリプト
"""

import sys
import os
from pathlib import Path

# Streamlit モジュールをモック
class MockSessionState:
    def __init__(self):
        self.api_keys = {}
    
    def get(self, key, default=None):
        return self.api_keys.get(key, default)

class MockStreamlit:
    session_state = MockSessionState()
    
    @staticmethod
    def warning(msg): print(f"⚠️ {msg}")
    @staticmethod
    def info(msg): print(f"ℹ️ {msg}")
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
    @staticmethod
    def subheader(msg): print(f"\n### {msg}")
    @staticmethod
    def expander(msg, expanded=False): return MockExpander()
    @staticmethod
    def text(msg): print(msg)
    @staticmethod
    def video(url): print(f"[Video: {url}]")
    @staticmethod
    def columns(spec): return [MockColumn(), MockColumn()]

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

class MockExpander:
    def __enter__(self): return self
    def __exit__(self, *args): pass

class MockColumn:
    def __enter__(self): return self
    def __exit__(self, *args): pass

st = MockStreamlit()

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent))

def test_text_to_video():
    """Text-to-Video機能をテスト"""
    
    print("=" * 60)
    print("🎬 Text-to-Video テスト開始")
    print("=" * 60)
    
    # セッション状態をモック
    if not hasattr(st.session_state, 'api_keys'):
        st.session_state.api_keys = {}
    
    # APIキーを設定（環境変数から読み込み）
    st.session_state.api_keys['google'] = os.getenv('GOOGLE_API_KEY', 'AIzaSyCUDhyex-CRvb4ad9V90rW_Kvn9a_RmRvU')
    st.session_state.api_keys['seedance'] = os.getenv('SEEDANCE_API_KEY', '6a28ac0141124793b1823df53cdd2207')
    st.session_state.api_keys['piapi'] = os.getenv('PIAPI_KEY', '328fcfae00e3efcfb895f1d0c916ce6a2657daecff3f748f174b12bd03402f6b')
    st.session_state.api_keys['piapi_xkey'] = os.getenv('PIAPI_XKEY', '5e6dd612b7acee46b055acf37d314c90f1c118fde228c218c3722c132ae79bf4')
    
    print("✅ APIキー設定完了")
    print(f"  - Google API: {'設定済み' if st.session_state.api_keys.get('google') else '未設定'}")
    print(f"  - Seedance API: {'設定済み' if st.session_state.api_keys.get('seedance') else '未設定'}")
    print(f"  - PIAPI: {'設定済み' if st.session_state.api_keys.get('piapi') else '未設定'}")
    print(f"  - PIAPI XKEY: {'設定済み' if st.session_state.api_keys.get('piapi_xkey') else '未設定'}")
    print()
    
    # Text-to-Videoモジュールをインポート
    try:
        from text_to_video_veo3_seedance import TextToVideoVeo3Seedance
        print("✅ Text-to-Videoモジュールのインポート成功")
    except Exception as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return
    
    # 生成器を初期化
    print("\n📹 Text-to-Video生成器を初期化...")
    generator = TextToVideoVeo3Seedance()
    
    # テストプロンプト
    test_prompt = "A beautiful sunrise over mountains with clouds moving slowly"
    print(f"\n🎯 テストプロンプト: {test_prompt}")
    
    # テスト1: Google Veo3/Gemini
    print("\n--- テスト1: Google API ---")
    if generator.google_api_key:
        result = generator.generate_video_with_veo3(test_prompt, duration=5)
        print(f"結果: {result['status']}")
        print(f"メッセージ: {result.get('message', '')}")
        if result['status'] == 'success':
            print(f"✅ Google API呼び出し成功")
        else:
            print(f"⚠️ Google API呼び出し失敗: {result.get('details', '')[:200]}")
    else:
        print("⚠️ Google APIキーが設定されていません")
    
    # テスト2: Seedance
    print("\n--- テスト2: Seedance API ---")
    if generator.seedance_api_key:
        result = generator.generate_video_with_seedance(test_prompt, duration=5)
        print(f"結果: {result['status']}")
        print(f"メッセージ: {result.get('message', '')}")
        if result['status'] == 'success':
            print(f"✅ Seedance API呼び出し成功")
        else:
            print(f"⚠️ Seedance API呼び出し失敗")
    else:
        print("⚠️ Seedance APIキーが設定されていません")
    
    # テスト3: PIAPIフォールバック
    print("\n--- テスト3: PIAPI Hailuoフォールバック ---")
    result = generator.generate_video_with_piapi_fallback(test_prompt, duration=5)
    print(f"結果: {result['status']}")
    print(f"メッセージ: {result.get('message', '')}")
    if result['status'] == 'success':
        print(f"✅ PIAPI Hailuo呼び出し成功")
        print(f"タスクID: {result.get('task_id', 'N/A')}")
    else:
        print(f"⚠️ PIAPI呼び出し失敗")
    
    # テスト4: 自動選択
    print("\n--- テスト4: 自動API選択 ---")
    result = generator.generate_video_auto(test_prompt, duration=5)
    print(f"結果: {result['status']}")
    print(f"メッセージ: {result.get('message', '')}")
    if result['status'] == 'success':
        print(f"✅ 自動選択成功")
        print(f"使用プロバイダー: {result.get('provider', 'unknown')}")
    else:
        print(f"⚠️ 自動選択での生成失敗")
    
    # サンプル台本でテスト
    print("\n--- テスト5: 台本からの動画生成 ---")
    sample_script = {
        'scenes': [
            {
                'id': 'scene_1',
                'visual_prompt': 'A peaceful morning in a Japanese garden with cherry blossoms',
                'duration': 5
            },
            {
                'id': 'scene_2',
                'visual_prompt': 'Modern Tokyo cityscape at night with neon lights',
                'duration': 5
            }
        ]
    }
    
    from text_to_video_veo3_seedance import generate_videos_from_script
    
    print("台本のシーン数:", len(sample_script['scenes']))
    videos = generate_videos_from_script(sample_script)
    
    print(f"\n生成結果:")
    for i, video in enumerate(videos, 1):
        print(f"  シーン{i}: {video.get('status', 'unknown')}")
        if video.get('status') == 'completed':
            print(f"    - URL: {video.get('video_url', 'N/A')[:50]}...")
        else:
            print(f"    - エラー: {video.get('error', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("🎬 Text-to-Video テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    # streamlitモジュールをモックとして設定
    sys.modules['streamlit'] = st
    test_text_to_video()