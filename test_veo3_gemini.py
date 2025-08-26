#!/usr/bin/env python3
"""
Google Gemini API経由でVeo機能をテスト
現在Veo 3.0は限定アクセスのため、代替手段を実装
"""

import google.generativeai as genai
import time
import os
from pathlib import Path

def test_veo_with_gemini():
    """Gemini API経由でVeo相当機能をテスト"""
    
    print("=" * 60)
    print("🎬 Google Gemini API - Video Generation Test")
    print("=" * 60)
    
    # APIキーを設定
    api_key = "AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8"
    genai.configure(api_key=api_key)
    
    print(f"✅ APIキー設定完了")
    
    # 利用可能なモデルを確認
    print("\n📋 利用可能なモデル:")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
    
    # Gemini 1.5 Flashで動画プロンプト生成
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    test_prompt = """
    Create a detailed video generation prompt for:
    "大空に新しい太陽が昇る、美しい朝焼けの風景"
    
    Include:
    - Camera movements
    - Color palette
    - Lighting
    - Duration: 5 seconds
    - Aspect ratio: 16:9
    """
    
    print(f"\n📝 プロンプト生成中...")
    
    try:
        response = model.generate_content(test_prompt)
        print(f"\n✅ Gemini応答成功:")
        print(response.text[:500])
        
        # 注意: Veo 3.0は現在限定アクセス
        print("\n" + "=" * 60)
        print("⚠️ 注意事項:")
        print("Veo 3.0は現在限定プレビューです")
        print("プロジェクトがアクセスリストに登録される必要があります")
        print("\n📋 次のステップ:")
        print("1. Veo 3.0アクセスを申請")
        print("2. 承認後、google-genaiパッケージで利用可能")
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

def check_veo_access():
    """Veoアクセス状況を確認"""
    
    print("\n" + "=" * 60)
    print("🔍 Veoアクセス確認")
    print("=" * 60)
    
    import requests
    
    # プロジェクトIDとAPIキー
    project_id = "medent-9167b"
    api_key = "AIzaSyAECKBO-BicCvXijRrZQvErEDXrrLOxxn8"
    
    # Veoモデルの利用可能性を確認
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            veo_models = [m for m in models if 'veo' in m.get('name', '').lower()]
            
            if veo_models:
                print("✅ Veoモデルが見つかりました:")
                for model in veo_models:
                    print(f"  - {model['name']}")
            else:
                print("❌ Veoモデルは利用できません")
                print(f"Project ID: {project_id}")
                print("アクセス申請が必要です")
        else:
            print(f"❌ API確認エラー: {response.status_code}")
    except Exception as e:
        print(f"❌ 確認エラー: {e}")

if __name__ == "__main__":
    # Gemini APIテスト
    success = test_veo_with_gemini()
    
    # Veoアクセス確認
    check_veo_access()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Gemini APIテスト成功")
    print("\n🎬 動画生成の代替手段:")
    print("1. Stability AI API（安定）")
    print("2. RunComfy Seedance（高品質）")
    print("3. PIAPI Hailuo（コスト効率）")
    print("4. Veo 3.0アクセス申請（将来）")
    print("=" * 60)