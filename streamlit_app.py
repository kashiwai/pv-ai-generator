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
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'basic_info'
if 'basic_info' not in st.session_state:
    st.session_state.basic_info = {}
if 'generated_scripts' not in st.session_state:
    st.session_state.generated_scripts = []
if 'selected_script' not in st.session_state:
    st.session_state.selected_script = None

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
    from agent_core.plot.detailed_script_writer import DetailedScriptWriter
    from agent_core.video.text_to_video_generator import TextToVideoGenerator
    v240_available = True
except ImportError as e:
    v240_available = False
    print(f"v2.4.0 modules not available: {e}")

# 既存モジュールのインポート
try:
    from piapi_integration import PIAPIClient, generate_images_with_piapi
    piapi_available = True
except ImportError:
    piapi_available = False
    print("PIAPI integration not available")

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
    
    # メインコンテンツ - ステップに応じて表示を切り替え
    if st.session_state.current_step == 'basic_info':
        # 基本情報入力画面
        basic_info_step()
    elif st.session_state.current_step == 'script_generation':
        # 台本生成・編集画面
        script_generation_step()
    elif st.session_state.current_step == 'video_generation':
        # 動画生成画面
        video_generation_step()
    else:
        # デフォルトでタブ表示
        tabs = st.tabs(["🎬 PV生成", "📝 詳細設定", "📊 生成履歴"])
        
        with tabs[0]:
            generate_pv_tab()
        
        with tabs[1]:
            settings_tab()
        
        with tabs[2]:
            history_tab()

def basic_info_step():
    """基本情報入力ステップ"""
    st.markdown("## 📝 ステップ1: 基本情報入力")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("タイトル *", placeholder="PVのタイトルを入力", key="input_title")
        keywords = st.text_input("キーワード", placeholder="青春, 友情, 冒険 (カンマ区切り)", key="input_keywords")
        mood = st.selectbox(
            "雰囲気",
            ["明るい", "感動的", "ノスタルジック", "エネルギッシュ", 
             "ミステリアス", "ダーク", "ファンタジー", "クール"],
            key="input_mood"
        )
    
    with col2:
        description = st.text_area(
            "説明",
            placeholder="PVの概要を説明してください",
            height=120,
            key="input_description"
        )
    
    st.markdown("## 🎵 コンテンツ")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        lyrics = st.text_area(
            "歌詞 / メッセージ",
            placeholder="歌詞またはナレーション用のメッセージを入力",
            height=200,
            key="input_lyrics"
        )
    
    with col2:
        audio_file = st.file_uploader(
            "音楽ファイル *",
            type=['mp3', 'wav', 'm4a', 'aac'],
            help="最大7分まで",
            key="input_audio"
        )
        
        st.markdown("### 🎨 キャラクター")
        character_images = st.file_uploader(
            "キャラクター画像",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="同一人物を維持したい場合はアップロード",
            key="input_character"
        )
    
    # 次へボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📝 台本生成へ進む →", type="primary", use_container_width=True):
            if not title:
                st.error("❌ タイトルを入力してください")
            elif not audio_file:
                st.error("❌ 音楽ファイルをアップロードしてください")
            else:
                # 基本情報を保存
                st.session_state.basic_info = {
                    'title': title,
                    'keywords': keywords,
                    'description': description,
                    'mood': mood,
                    'lyrics': lyrics,
                    'audio_file': audio_file,
                    'character_images': character_images
                }
                # 次のステップへ
                st.session_state.current_step = 'script_generation'
                st.rerun()

def script_generation_step():
    """台本生成・編集ステップ"""
    st.markdown("## 📝 ステップ2: 台本生成・編集")
    
    # 戻るボタン
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 戻る"):
            st.session_state.current_step = 'basic_info'
            st.rerun()
    
    # 基本情報の表示
    with st.expander("📋 入力した基本情報", expanded=False):
        info = st.session_state.basic_info
        st.write(f"**タイトル:** {info['title']}")
        st.write(f"**キーワード:** {info.get('keywords', '')}")
        st.write(f"**雰囲気:** {info.get('mood', '')}")
        st.write(f"**説明:** {info.get('description', '')}")
    
    # 台本生成
    if len(st.session_state.generated_scripts) == 0:
        st.info("📝 台本を生成中...")
        
        # 台本生成ボタン
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 ストーリー重視", use_container_width=True):
                generate_script_pattern('story')
        
        with col2:
            if st.button("🎨 ビジュアル重視", use_container_width=True):
                generate_script_pattern('visual')
        
        with col3:
            if st.button("🎵 音楽同期重視", use_container_width=True):
                generate_script_pattern('music')
    
    # 生成された台本の表示
    if st.session_state.generated_scripts:
        st.markdown("### 📜 生成された台本")
        
        # 台本選択タブ
        script_tabs = st.tabs([f"パターン{i+1}" for i in range(len(st.session_state.generated_scripts))])
        
        for i, (tab, script) in enumerate(zip(script_tabs, st.session_state.generated_scripts)):
            with tab:
                st.markdown(f"**タイプ:** {script.get('type', 'standard')}")
                
                # シーンごとの編集
                for j, scene in enumerate(script.get('scenes', [])):
                    with st.expander(f"シーン {j+1}: {scene.get('timestamp', '')}秒"):
                        # 編集可能なテキストエリア
                        scene['content'] = st.text_area(
                            "ストーリー内容",
                            value=scene.get('content', ''),
                            key=f"scene_content_{i}_{j}",
                            height=100
                        )
                        
                        if st.session_state.workflow_mode == 'text_to_video':
                            scene['video_prompt'] = st.text_area(
                                "Text-to-Videoプロンプト",
                                value=scene.get('video_prompt', ''),
                                key=f"video_prompt_{i}_{j}",
                                height=150
                            )
                        else:
                            scene['visual_description'] = st.text_area(
                                "Midjourneyプロンプト",
                                value=scene.get('visual_description', ''),
                                key=f"visual_desc_{i}_{j}",
                                height=100
                            )
                
                # この台本を選択
                if st.button(f"この台本を使用 ✓", key=f"select_script_{i}", type="primary"):
                    st.session_state.selected_script = script
                    st.success("✅ 台本を選択しました")
    
    # 次のステップへ
    if st.session_state.selected_script:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎬 動画生成へ進む →", type="primary", use_container_width=True):
                st.session_state.current_step = 'video_generation'
                st.rerun()

def video_generation_step():
    """動画生成ステップ"""
    st.markdown("## 🎬 ステップ3: 動画生成")
    
    # 戻るボタン
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 台本編集に戻る"):
            st.session_state.current_step = 'script_generation'
            st.rerun()
    
    # 選択された台本の確認
    with st.expander("📜 選択した台本", expanded=False):
        if st.session_state.selected_script:
            for i, scene in enumerate(st.session_state.selected_script.get('scenes', [])):
                st.write(f"**シーン {i+1}:** {scene.get('content', '')[:100]}...")
    
    # 生成設定
    st.markdown("### ⚙️ 生成設定")
    
    if st.session_state.workflow_mode == 'text_to_video':
        col1, col2 = st.columns(2)
        with col1:
            provider = st.selectbox(
                "プロバイダー",
                ["Veo3 (高品質)", "Seedance (高速)", "自動選択"]
            )
        with col2:
            quality = st.select_slider(
                "品質",
                options=["draft", "standard", "high", "ultra"],
                value="high"
            )
    
    # 生成開始
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 動画生成を開始", type="primary", use_container_width=True):
            # 基本情報と台本を使って生成
            info = st.session_state.basic_info
            script = st.session_state.selected_script
            
            generate_pv_with_script(
                info=info,
                script=script
            )

def generate_script_pattern(pattern_type: str):
    """指定パターンで台本を生成"""
    import time
    
    # プログレスバー表示
    progress = st.progress(0)
    status = st.empty()
    
    status.text(f"{pattern_type}パターンで台本を生成中...")
    progress.progress(0.3)
    
    # ここで実際の台本生成処理を呼び出す
    # 仮の台本データ
    script = {
        'type': pattern_type,
        'scenes': [
            {
                'scene_number': 1,
                'timestamp': '0-8',
                'content': f'{pattern_type}タイプのオープニングシーン',
                'video_prompt': 'Cinematic opening shot, golden hour lighting',
                'visual_description': 'wide shot of city skyline --ar 16:9 --v 6'
            },
            {
                'scene_number': 2,
                'timestamp': '8-16',
                'content': f'{pattern_type}タイプの展開シーン',
                'video_prompt': 'Dynamic movement, character introduction',
                'visual_description': 'main character walking --ar 16:9 --v 6'
            },
            {
                'scene_number': 3,
                'timestamp': '16-24',
                'content': f'{pattern_type}タイプのクライマックス',
                'video_prompt': 'Emotional climax, dramatic lighting',
                'visual_description': 'emotional moment --ar 16:9 --v 6'
            }
        ]
    }
    
    progress.progress(0.7)
    time.sleep(0.5)
    
    # 生成された台本を保存
    st.session_state.generated_scripts.append(script)
    
    progress.progress(1.0)
    status.text("✅ 台本生成完了")
    time.sleep(1)
    
    # 画面を更新
    st.rerun()

def generate_pv_with_script(info: dict, script: dict):
    """台本を使ってPVを生成"""
    # 既存のgenerate_pv関数を活用
    generate_pv(
        title=info['title'],
        keywords=info.get('keywords', ''),
        description=info.get('description', ''),
        mood=info.get('mood', ''),
        lyrics=info.get('lyrics', ''),
        audio_file=info['audio_file'],
        character_images=info.get('character_images'),
        script=script
    )

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

def generate_pv(title, keywords, description, mood, lyrics, audio_file, character_images, script=None):
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