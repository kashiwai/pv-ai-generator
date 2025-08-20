#!/usr/bin/env python3
"""
ミッドジャーニー画像生成とキャラクター一貫性のテストスクリプト
"""

import asyncio
import json
from pathlib import Path
from agent_core.character.generator import CharacterGenerator
from agent_core.character.image_picker import ImagePicker

async def test_midjourney_generation():
    """ミッドジャーニーの画像生成をテスト"""
    
    # 設定を読み込み
    config_path = Path("config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # APIキーの確認
    if not config.get("midjourney_api_key"):
        print("❌ エラー: ミッドジャーニーAPIキーが設定されていません")
        print("config.jsonにmidjourney_api_keyを設定してください")
        return
    
    print("✅ ミッドジャーニーAPIキー検出")
    print(f"   キー: {config['midjourney_api_key'][:10]}...")
    
    # CharacterGeneratorの初期化
    generator = CharacterGenerator(config)
    generator.provider = "midjourney"  # ミッドジャーニーを強制使用
    
    print("\n📝 テスト1: 単純な画像生成")
    print("-" * 50)
    
    # 基本的な画像生成テスト
    test_prompt = "beautiful anime girl, long hair, smile, high quality"
    print(f"プロンプト: {test_prompt}")
    
    try:
        result = await generator.generate_with_midjourney(test_prompt)
        if result:
            print(f"✅ 画像生成成功: {result}")
        else:
            print("❌ 画像生成失敗")
    except Exception as e:
        print(f"❌ エラー発生: {e}")
    
    print("\n📝 テスト2: キャラクター一貫性テスト")
    print("-" * 50)
    
    # 参照画像がある場合のテスト
    reference_image = Path("assets/characters/sample.png")
    if reference_image.exists():
        print(f"参照画像: {reference_image}")
        
        try:
            # 参照画像をアップロード
            ref_url = await generator.upload_image_for_reference(reference_image)
            if ref_url:
                print(f"✅ 参照画像アップロード成功: {ref_url[:50]}...")
                
                # キャラクター一貫性のある画像を生成
                consistent_prompt = "same character, different pose, outdoor scene"
                result = await generator.generate_with_midjourney(consistent_prompt, ref_url)
                
                if result:
                    print(f"✅ 一貫性のある画像生成成功: {result}")
                else:
                    print("❌ 一貫性のある画像生成失敗")
            else:
                print("❌ 参照画像のアップロード失敗")
                
        except Exception as e:
            print(f"❌ エラー発生: {e}")
    else:
        print("⚠️ 参照画像が見つかりません: assets/characters/sample.png")
    
    print("\n📝 テスト3: 複数キャラクター生成")
    print("-" * 50)
    
    # 複数のキャラクターを生成
    try:
        characters = await generator.generate_characters(
            keywords="友情, 青春, 学校",
            mood="明るい",
            description="高校生の友達グループ"
        )
        
        print(f"生成されたキャラクター数: {len(characters)}")
        for i, char in enumerate(characters):
            print(f"  {i+1}. ID: {char['id']}")
            print(f"     パス: {char['original_path']}")
            print(f"     一貫性: {char.get('has_consistency', False)}")
            
    except Exception as e:
        print(f"❌ エラー発生: {e}")

async def test_image_picker():
    """ImagePickerのテスト"""
    
    print("\n📝 ImagePickerテスト")
    print("-" * 50)
    
    picker = ImagePicker()
    
    # テスト画像の登録
    test_images = list(Path("assets/characters").glob("*.png"))[:2]
    
    if test_images:
        print(f"テスト画像数: {len(test_images)}")
        
        character_refs = picker.process_images([str(img) for img in test_images])
        
        print(f"登録されたキャラクター数: {len(character_refs)}")
        for ref in character_refs:
            print(f"  - ID: {ref['id']}")
            print(f"    サムネイル: {ref.get('thumbnail_path', 'なし')}")
            
            # Midjourney用の準備
            mj_path = picker.prepare_for_midjourney(ref['id'])
            if mj_path:
                print(f"    MJ準備完了: {mj_path}")
    else:
        print("⚠️ テスト用の画像が見つかりません")

if __name__ == "__main__":
    print("🎬 ミッドジャーニー統合テスト開始")
    print("=" * 60)
    
    # 非同期実行
    asyncio.run(test_midjourney_generation())
    asyncio.run(test_image_picker())
    
    print("\n✅ テスト完了")
    print("=" * 60)