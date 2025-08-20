"""
🎬 PV AI Generator v2.4.0 - Streamlit版
Text-to-Video直接生成対応の最新版
"""

import streamlit as st
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# ページ設定
st.set_page_config(
    page_title="🎬 PV AI Generator v2.4.0",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {}
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = 'text_to_video'
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

# APIキー管理
def load_api_keys():
    """APIキーを環境変数またはSecretsから読み込み"""
    keys = {}
    
    # Streamlit Secretsから読み込み（優先）
    if hasattr(st, 'secrets'):
        keys['openai'] = st.secrets.get('OPENAI_API_KEY', '')
        keys['google'] = st.secrets.get('GOOGLE_API_KEY', '')
        keys['anthropic'] = st.secrets.get('ANTHROPIC_API_KEY', '')
        keys['piapi'] = st.secrets.get('PIAPI_KEY', '')
        keys['piapi_xkey'] = st.secrets.get('PIAPI_XKEY', '')
        keys['veo3'] = st.secrets.get('VEO3_API_KEY', '')
        keys['seedance'] = st.secrets.get('SEEDANCE_API_KEY', '')
        keys['midjourney'] = st.secrets.get('MIDJOURNEY_API_KEY', keys.get('piapi_xkey', ''))
        keys['hailuo'] = st.secrets.get('HAILUO_API_KEY', keys.get('piapi', ''))
    
    # 環境変数から読み込み（フォールバック）
    keys['openai'] = keys.get('openai') or os.getenv('OPENAI_API_KEY', '')
    keys['google'] = keys.get('google') or os.getenv('GOOGLE_API_KEY', '')
    keys['veo3'] = keys.get('veo3') or os.getenv('VEO3_API_KEY', '')
    keys['seedance'] = keys.get('seedance') or os.getenv('SEEDANCE_API_KEY', '')
    
    return keys

# v2.4.0モジュールのインポート
try:
    from agent_core.workflow.advanced_pv_generator import AdvancedPVGenerator
    from agent_core.plot.advanced_script_analyzer import AdvancedScriptAnalyzer
    from agent_core.plot.detailed_script_writer import DetailedScriptWriter
    from agent_core.video.text_to_video_generator import TextToVideoGenerator
    v240_available = True
except ImportError:
    v240_available = False
    st.warning("⚠️ v2.4.0モジュールが見つかりません。クラシックモードで動作します。")

# 既存モジュールのインポート
from agent_core.character.generator import CharacterGenerator
from agent_core.character.image_picker import ImagePicker
from piapi_integration import PIAPIClient, generate_images_with_piapi

def main():
    # ヘッダー
    st.markdown("""
    # 🎬 PV AI Generator v2.4.0
    ### Text-to-Video直接生成対応の最新版
    """)
    
    # バージョン情報
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.info("🆕 **v2.4.0 新機能**: 詳細台本(2000-3000文字/シーン) → Text-to-Video直接生成")
    with col2:
        workflow_mode = st.radio(
            "ワークフローモード",
            ["Text-to-Video (v2.4.0)", "クラシック (画像→動画)"],
            horizontal=True
        )
        st.session_state.workflow_mode = 'text_to_video' if "Text-to-Video" in workflow_mode else 'classic'
    with col3:
        if st.button("📚 ヘルプ"):
            show_help()
    
    # サイドバー: API設定
    with st.sidebar:
        st.markdown("## 🔑 API設定")
        
        # APIキーの読み込み
        api_keys = load_api_keys()
        st.session_state.api_keys = api_keys
        
        # 接続状態の表示
        st.markdown("### 📡 接続状態")
        
        # Text-to-Video APIs
        if st.session_state.workflow_mode == 'text_to_video':
            st.markdown("#### Text-to-Video APIs")
            
            # Veo3
            if api_keys.get('veo3'):
                st.success("✅ Veo3: 接続済み")
            else:
                veo3_key = st.text_input("Veo3 API Key", type="password", key="veo3_input")
                if veo3_key:
                    st.session_state.api_keys['veo3'] = veo3_key
            
            # Seedance
            if api_keys.get('seedance'):
                st.success("✅ Seedance: 接続済み")
            else:
                seedance_key = st.text_input("Seedance API Key", type="password", key="seedance_input")
                if seedance_key:
                    st.session_state.api_keys['seedance'] = seedance_key
        
        # 既存APIs
        st.markdown("#### 基本APIs")
        
        # PIAPI/Midjourney
        if api_keys.get('piapi') and api_keys.get('piapi_xkey'):
            st.success("✅ PIAPI/Midjourney: 接続済み")
        else:
            st.warning("⚠️ PIAPI: 未設定")
        
        # OpenAI
        if api_keys.get('openai'):
            st.success("✅ OpenAI: 接続済み")
        else:
            st.warning("⚠️ OpenAI: 未設定")
        
        # Google
        if api_keys.get('google'):
            st.success("✅ Google: 接続済み")
        else:
            st.warning("⚠️ Google: 未設定")
        
        st.markdown("---")
        
        # ワークフロー情報
        st.markdown("### 📊 ワークフロー情報")
        if st.session_state.workflow_mode == 'text_to_video':
            st.markdown("""
            **Text-to-Video モード**
            1. 歌詞・情景の深層分析
            2. 詳細台本生成 (2000-3000文字)
            3. Veo3/Seedance直接生成
            4. キャラクター一貫性維持
            5. 音楽同期・最終合成
            """)
        else:
            st.markdown("""
            **クラシックモード**
            1. 台本生成
            2. Midjourney画像生成
            3. Hailuo動画化
            4. 音楽同期・合成
            """)
    
    # メインコンテンツ
    tabs = st.tabs(["🎬 PV生成", "📝 詳細設定", "📊 生成履歴"])
    
    with tabs[0]:
        generate_pv_tab()
    
    with tabs[1]:
        settings_tab()
    
    with tabs[2]:
        history_tab()

def generate_pv_tab():
    """PV生成タブ"""
    
    st.markdown("## 📝 基本情報")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("タイトル *", placeholder="PVのタイトルを入力")
        keywords = st.text_input("キーワード", placeholder="青春, 友情, 冒険 (カンマ区切り)")
        mood = st.selectbox(
            "雰囲気",
            ["明るい", "感動的", "ノスタルジック", "エネルギッシュ", 
             "ミステリアス", "ダーク", "ファンタジー", "クール"]
        )
    
    with col2:
        description = st.text_area(
            "説明",
            placeholder="PVの概要を説明してください",
            height=120
        )
    
    st.markdown("## 🎵 コンテンツ")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        lyrics = st.text_area(
            "歌詞 / メッセージ",
            placeholder="歌詞またはナレーション用のメッセージを入力",
            height=200
        )
    
    with col2:
        audio_file = st.file_uploader(
            "音楽ファイル *",
            type=['mp3', 'wav', 'm4a', 'aac'],
            help="最大7分まで"
        )
        
        st.markdown("### 🎨 キャラクター")
        character_images = st.file_uploader(
            "キャラクター画像",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="同一人物を維持したい場合はアップロード"
        )
    
    # v2.4.0 詳細設定
    if st.session_state.workflow_mode == 'text_to_video' and v240_available:
        with st.expander("🎯 v2.4.0 詳細設定"):
            col1, col2 = st.columns(2)
            with col1:
                scene_duration = st.slider("シーン長(秒)", 5, 10, 8)
                script_detail = st.slider("台本詳細度", 1000, 3000, 2000, step=100)
            with col2:
                char_consistency = st.checkbox("キャラクター一貫性を最大化", value=True)
                provider_priority = st.selectbox(
                    "優先プロバイダー",
                    ["Veo3 (高品質)", "Seedance (高速)", "自動選択"]
                )
    
    # 生成ボタン
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 PV生成開始", type="primary", use_container_width=True):
            if not title:
                st.error("❌ タイトルを入力してください")
            elif not audio_file:
                st.error("❌ 音楽ファイルをアップロードしてください")
            else:
                generate_pv(
                    title=title,
                    keywords=keywords,
                    description=description,
                    mood=mood,
                    lyrics=lyrics,
                    audio_file=audio_file,
                    character_images=character_images
                )

def generate_pv(title, keywords, description, mood, lyrics, audio_file, character_images):
    """PV生成処理"""
    
    # プログレスバーとステータス
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 音楽ファイルを保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_file.name) as tmp_audio:
            tmp_audio.write(audio_file.read())
            audio_path = tmp_audio.name
        
        # キャラクター画像を保存
        char_paths = []
        if character_images:
            for img in character_images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=img.name) as tmp_img:
                    tmp_img.write(img.read())
                    char_paths.append(tmp_img.name)
        
        if st.session_state.workflow_mode == 'text_to_video' and v240_available:
            # v2.4.0 新ワークフロー
            status_text.text("v2.4.0 Text-to-Videoワークフローを開始...")
            progress_bar.progress(0.1)
            
            # 設定を準備
            config = {
                'openai_api_key': st.session_state.api_keys.get('openai', ''),
                'google_api_key': st.session_state.api_keys.get('google', ''),
                'anthropic_api_key': st.session_state.api_keys.get('anthropic', ''),
                'veo3_api_key': st.session_state.api_keys.get('veo3', ''),
                'seedance_api_key': st.session_state.api_keys.get('seedance', ''),
                'piapi_key': st.session_state.api_keys.get('piapi', ''),
                'use_advanced_workflow': True,
                'workflow_mode': 'advanced'
            }
            
            # AdvancedPVGeneratorを使用
            generator = AdvancedPVGenerator(config)
            
            # 非同期処理を実行
            async def run_generation():
                return await generator.generate_pv(
                    title=title,
                    keywords=keywords,
                    description=description,
                    mood=mood,
                    lyrics=lyrics,
                    audio_file=audio_path,
                    character_images=char_paths,
                    use_text_to_video=True,
                    progress_callback=lambda p, msg: (
                        progress_bar.progress(p),
                        status_text.text(msg)
                    )
                )
            
            result = asyncio.run(run_generation())
            
            if result['status'] == 'success':
                st.success(f"✅ PV生成完了！")
                st.video(result['video_path'])
                
                # ダウンロードボタン
                with open(result['video_path'], 'rb') as f:
                    st.download_button(
                        label="📥 動画をダウンロード",
                        data=f,
                        file_name=f"{title}_v240.mp4",
                        mime="video/mp4"
                    )
                
                # 履歴に追加
                st.session_state.generation_history.append({
                    'title': title,
                    'timestamp': datetime.now().isoformat(),
                    'mode': 'text_to_video',
                    'status': 'success',
                    'path': result['video_path']
                })
            else:
                st.error(f"❌ エラー: {result.get('message', 'Unknown error')}")
        
        else:
            # クラシックワークフロー
            status_text.text("クラシックワークフローで生成中...")
            
            # 既存の処理を呼び出し
            st.info("クラシックモードで処理中...")
            # ここに既存のgenerate_images_with_piapi等の処理
    
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
    
    finally:
        progress_bar.progress(1.0)
        status_text.text("処理完了")

def settings_tab():
    """詳細設定タブ"""
    st.markdown("## ⚙️ 詳細設定")
    
    if st.session_state.workflow_mode == 'text_to_video':
        st.markdown("### Text-to-Video設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Veo3設定")
            veo3_quality = st.select_slider(
                "品質",
                options=["draft", "standard", "high", "ultra"],
                value="high"
            )
            veo3_consistency = st.slider("キャラクター一貫性", 0.0, 1.0, 0.9)
            
        with col2:
            st.markdown("#### Seedance設定")
            seedance_speed = st.select_slider(
                "生成速度",
                options=["slow", "normal", "fast", "turbo"],
                value="normal"
            )
            seedance_face_swap = st.slider("顔交換強度", 0.0, 1.0, 0.95)
    
    st.markdown("### 共通設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.number_input("最大動画長(秒)", 60, 420, 180)
    
    with col2:
        st.selectbox("出力解像度", ["1920x1080", "1280x720", "854x480"])
    
    with col3:
        st.number_input("FPS", 24, 60, 30)

def history_tab():
    """生成履歴タブ"""
    st.markdown("## 📊 生成履歴")
    
    if st.session_state.generation_history:
        for item in reversed(st.session_state.generation_history):
            with st.expander(f"📹 {item['title']} - {item['timestamp'][:10]}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"モード: {item['mode']}")
                    st.write(f"状態: {item['status']}")
                with col2:
                    if item.get('path') and Path(item['path']).exists():
                        st.button("再生", key=f"play_{item['timestamp']}")
    else:
        st.info("まだ生成履歴がありません")

def show_help():
    """ヘルプダイアログ"""
    st.markdown("""
    ### 📚 v2.4.0 使い方ガイド
    
    #### 🆕 新機能
    - **詳細台本生成**: 各シーン2000-3000文字の詳細な描写
    - **Text-to-Video直接生成**: Veo3/Seedanceで直接動画化
    - **キャラクター一貫性**: 同一人物を全シーンで維持
    
    #### 🚀 クイックスタート
    1. タイトルと音楽ファイルをアップロード
    2. 歌詞・説明を入力
    3. キャラクター画像をアップロード（オプション）
    4. 「PV生成開始」をクリック
    
    #### 🔑 必要なAPIキー
    - **Text-to-Video**: Veo3またはSeedance
    - **画像生成**: PIAPI (Midjourney)
    - **台本生成**: OpenAI/Google/Anthropic
    """)

if __name__ == "__main__":
    main()