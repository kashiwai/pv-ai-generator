#!/usr/bin/env python
"""アプリの起動テスト"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("🎬 PV自動生成AIエージェント - 起動テスト")
print("=" * 50)

# インポートテスト
print("\n1. モジュールインポートテスト...")
try:
    from agent_core.character.image_picker import ImagePicker
    print("✓ ImagePicker")
    from agent_core.character.generator import CharacterGenerator
    print("✓ CharacterGenerator")
    from agent_core.plot.script_planner import ScriptPlanner
    print("✓ ScriptPlanner")
    from agent_core.plot.script_writer import ScriptWriter
    print("✓ ScriptWriter")
    from agent_core.tts.tts_generator import TTSGenerator
    print("✓ TTSGenerator")
    from agent_core.video.scene_generator import SceneGenerator
    print("✓ SceneGenerator")
    from agent_core.composer.merge_video import VideoComposer
    print("✓ VideoComposer")
    from agent_core.utils.helpers import load_config
    print("✓ helpers")
    print("\n✅ すべてのモジュールが正常にインポートできました！")
except ImportError as e:
    print(f"\n❌ インポートエラー: {e}")
    sys.exit(1)

# Gradioアプリテスト
print("\n2. Gradioアプリ起動テスト...")
try:
    from app import create_interface
    print("✓ create_interface関数をインポート")
    
    # インターフェースを作成（起動はしない）
    demo = create_interface()
    print("✓ インターフェース作成成功")
    
    print("\n✅ アプリは正常に起動可能です！")
    print("\n起動方法:")
    print("  source venv/bin/activate")
    print("  python app.py")
    print("\nアクセス: http://localhost:7860")
    
except Exception as e:
    print(f"\n❌ アプリエラー: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("テスト完了")
print("=" * 50)