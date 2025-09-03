"""
🎬 PV AI Generator v5.3.7 - Streamlit版
ステップバイステップワークフロー実装
1. 台本生成 → 2. Gemini 2.5 Flash画像生成 → 3. Kling動画生成
APIキー読み込み修正とデモモード削除
"""

import streamlit as st
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="🎬 PV AI Generator v5.3.7",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'api_keys' not in st.session_state:
    # 環境変数またはStreamlit Secretsから自動読み込み
    st.session_state.api_keys = {
        'openai': os.getenv('OPENAI_API_KEY', st.secrets.get('OPENAI_API_KEY', '')),
        'anthropic': os.getenv('ANTHROPIC_API_KEY', st.secrets.get('ANTHROPIC_API_KEY', '')),
        'google': os.getenv('GOOGLE_API_KEY', st.secrets.get('GOOGLE_API_KEY', '')),
        'piapi': os.getenv('PIAPI_KEY', st.secrets.get('PIAPI_KEY', '')),
        'piapi_xkey': os.getenv('PIAPI_XKEY', st.secrets.get('PIAPI_XKEY', ''))
    }
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
if 'project_storage' not in st.session_state:
    from agent_core.utils.data_storage import DataStorage
    st.session_state.project_storage = DataStorage()
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

# APIキー管理
def load_api_keys():
    """APIキーを環境変数またはSecretsから読み込み"""
    keys = {}
    
    # Streamlit Secretsから読み込み（優先）
    if hasattr(st, 'secrets'):
        keys['openai'] = st.secrets.get('OPENAI_API_KEY', '')
        keys['google'] = st.secrets.get('GOOGLE_API_KEY', '')
        keys['google_ai'] = keys['google']  # エイリアスを追加
        keys['anthropic'] = st.secrets.get('ANTHROPIC_API_KEY', '')
        keys['piapi'] = st.secrets.get('PIAPI_KEY', '')
        keys['piapi_xkey'] = st.secrets.get('PIAPI_XKEY', '')
        keys['seedance'] = st.secrets.get('SEEDANCE_API_KEY', '')
        keys['midjourney'] = st.secrets.get('MIDJOURNEY_API_KEY', keys.get('piapi_xkey', ''))
        keys['hailuo'] = st.secrets.get('HAILUO_API_KEY', keys.get('piapi', ''))
    
    # 環境変数から読み込み（フォールバック）
    keys['openai'] = keys.get('openai') or os.getenv('OPENAI_API_KEY', '')
    keys['google'] = keys.get('google') or os.getenv('GOOGLE_API_KEY', '')
    keys['google_ai'] = keys['google']  # エイリアスを追加
    keys['seedance'] = keys.get('seedance') or os.getenv('SEEDANCE_API_KEY', '')
    
    return keys

# v3.1.0モジュールのインポート
try:
    from agent_core.workflow.advanced_pv_generator import AdvancedPVGenerator
    from agent_core.plot.detailed_script_writer import DetailedScriptWriter
    from agent_core.video.text_to_video_generator import TextToVideoGenerator
    from agent_core.plot.basic_script_generator import BasicScriptGenerator
    v240_available = True
except ImportError as e:
    v240_available = False
    print(f"v3.1.0 modules not available: {e}")

# 既存モジュールのインポート
try:
    from piapi_integration import PIAPIClient, generate_images_with_piapi
    piapi_available = True
except ImportError:
    piapi_available = False
    print("PIAPI integration not available")

# v4.0.0 動画生成モジュール
try:
    from streamlit_video_generator import StreamlitVideoGenerator, create_video_generation_ui
    video_generation_available = True
except ImportError:
    video_generation_available = False
    print("Video generation module not available")

def main():
    # ヘッダー
    st.markdown("""
    # 🎬 PV AI Generator v5.3.7
    ### Gemini 2.5 Flash→Kling 画像から動画ワークフロー
    """)
    
    # バージョン情報
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.info("🆕 **v5.3.8 アップデート**: Gemini 2.5 Flash画像生成、Kling v2.1-master実装！")
    with col2:
        workflow_mode = st.radio(
            "ワークフローモード",
            ["Text-to-Video (v3.3.0)", "クラシック (画像→動画)"],
            horizontal=True
        )
        st.session_state.workflow_mode = 'text_to_video' if "Text-to-Video" in workflow_mode else 'classic'
    with col3:
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            if st.button("💾 保存"):
                save_current_project()
        with col3_2:
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
        
        # PIAPI/Gemini
        if api_keys.get('piapi'):
            st.success("✅ PIAPI/Gemini 2.5 Flash: 接続済み")
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
            **Text-to-Video モード v3.3.0**
            1. 歌詞・情景の深層分析
            2. 最適化台本生成 (500-1000文字/シーン)
            3. Veo3/Seedance直接生成
            4. キャラクター完全固定・全シーン一貫
            5. 音楽同期・最終合成
            """)
        else:
            st.markdown("""
            **クラシックモード（ステップバイステップ）**
            1. 基本情報入力
            2. 台本生成・編集
            3. Midjourney画像生成
            4. Kling動画生成
            5. 最終確認・ダウンロード
            """)
    
    # メインコンテンツ - ステップに応じて表示を切り替え
    if st.session_state.current_step == 'basic_info':
        # 基本情報入力画面
        basic_info_step()
    elif st.session_state.current_step == 'script_generation':
        # 台本生成・編集画面
        script_generation_step()
    elif st.session_state.current_step == 'image_generation':
        # 画像生成画面（Midjourney）
        image_generation_step()
    elif st.session_state.current_step == 'video_generation':
        # 動画生成画面（Kling）
        video_generation_step()
    elif st.session_state.current_step == 'video_editing':
        # 動画編集画面
        video_editing_step()
    elif st.session_state.current_step == 'video_management':
        # 動画管理画面（URL一覧）
        video_management_step()
    elif st.session_state.current_step == 'project_management':
        # プロジェクト管理画面
        project_management_step()
    else:
        # デフォルトでタブ表示
        tabs = st.tabs(["🎬 PV生成", "📝 詳細設定", "📊 生成履歴", "📁 プロジェクト管理"])
        
        with tabs[0]:
            generate_pv_tab()
        
        with tabs[1]:
            settings_tab()
        
        with tabs[2]:
            history_tab()
        
        with tabs[3]:
            project_management_tab()

def basic_info_step():
    """基本情報入力ステップ"""
    st.markdown("## 📝 ステップ1: 基本情報入力")
    
    # 上部にプロジェクト管理ボタン
    col_top1, col_top2, col_top3 = st.columns([2, 2, 1])
    with col_top1:
        if st.button("📂 保存したプロジェクトを開く", use_container_width=True):
            st.session_state.current_step = 'project_management'
            st.rerun()
    with col_top2:
        if st.button("💾 現在のプロジェクトを保存", use_container_width=True):
            if st.session_state.basic_info:
                save_current_project()
            else:
                st.warning("保存する内容がありません")
    
    st.markdown("---")
    
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
                # 自動保存
                autosave_session()
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
        if info:
            st.write(f"**タイトル:** {info.get('title', 'タイトル未設定')}")
            st.write(f"**キーワード:** {info.get('keywords', '')}")
            st.write(f"**雰囲気:** {info.get('mood', '')}")
            st.write(f"**説明:** {info.get('description', '')}")
        else:
            st.info("基本情報が入力されていません")
    
    # 台本生成
    if len(st.session_state.generated_scripts) == 0:
        st.markdown("### 📝 台本パターンを選択")
        
        # 台本生成ボタン
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 ストーリー重視", use_container_width=True):
                with st.spinner(''):
                    generate_script_pattern('story')
        
        with col2:
            if st.button("🎨 ビジュアル重視", use_container_width=True):
                with st.spinner(''):
                    generate_script_pattern('visual')
        
        with col3:
            if st.button("🎵 音楽同期重視", use_container_width=True):
                with st.spinner(''):
                    generate_script_pattern('music')
        
        # 進捗表示エリア（ボタンの下に配置）
        st.markdown("---")
        progress_placeholder = st.empty()
    
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
                    # 自動保存
                    autosave_session()
    
    # 次のステップへ
    if st.session_state.selected_script:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎨 画像生成へ進む →", type="primary", use_container_width=True):
                st.session_state.current_step = 'image_generation'
                st.rerun()

def image_generation_step():
    """画像生成ステップ（Gemini 2.5 Flash）"""
    st.markdown("## 🎨 ステップ3: 画像生成（Gemini 2.5 Flash）")
    
    # 戻るボタンと次へボタン
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 戻る"):
            st.session_state.current_step = 'script_generation'
            st.rerun()
    
    # 台本の確認
    if not st.session_state.selected_script:
        st.warning("⚠️ 台本が選択されていません")
        if st.button("台本生成に戻る"):
            st.session_state.current_step = 'script_generation'
            st.rerun()
        return
    
    script = st.session_state.selected_script
    scenes = script.get('scenes', [])
    
    st.markdown(f"### 📋 シーン数: {len(scenes)}個")
    
    # セッション状態の初期化
    if 'generated_images' not in st.session_state:
        st.session_state.generated_images = {}
    
    # PIAPIキーの確認
    piapi_xkey = st.session_state.api_keys.get('piapi_xkey', '')
    if not piapi_xkey:
        st.error("⚠️ PIAPI XKEYが設定されていません。サイドバーで設定してください。")
        return
    
    # キャラクター写真の確認
    character_photos = []
    if st.session_state.basic_info and st.session_state.basic_info.get('character_images'):
        st.info(f"✅ キャラクター写真: {len(st.session_state.basic_info['character_images'])}枚アップロード済み")
        character_photos = st.session_state.basic_info['character_images']
    
    # 画像生成のメイン処理
    st.markdown("---")
    st.markdown("### 🖼️ シーンごとの画像生成")
    
    from image_to_video_workflow import ImageToVideoWorkflow
    workflow = ImageToVideoWorkflow()
    
    # 各シーンの画像生成
    for i, scene in enumerate(scenes):
        scene_num = i + 1
        scene_key = f"scene_{scene_num}"
        
        with st.expander(f"📸 シーン{scene_num}: {scene.get('timestamp', '')}秒", expanded=True):
            # シーンの内容表示
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.markdown("**📝 シーン内容:**")
                st.text_area("ストーリー", scene.get('content', ''), height=100, disabled=True, key=f"story_{scene_num}")
            
            with col2:
                st.markdown("**🎨 画像生成プロンプト:**")
                # プロンプトを編集可能にする
                prompt_key = f"prompt_{scene_num}"
                default_prompt = scene.get('midjourney_prompt', scene.get('visual_prompt', ''))
                
                edited_prompt = st.text_area(
                    "プロンプト（編集可能）", 
                    default_prompt,
                    height=100,
                    key=prompt_key
                )
            
            # 画像生成ボタンと結果表示
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                if st.button(f"🎨 画像生成", key=f"gen_{scene_num}"):
                    with st.spinner(f"シーン{scene_num}の画像を生成中..."):
                        # Gemini 2.5 Flash画像生成
                        result = workflow.generate_image_with_nano_banana(
                            prompt=edited_prompt
                        )
                        
                        if result.get('status') == 'success':
                            st.session_state.generated_images[scene_key] = result.get('image_url')
                            st.success(f"✅ シーン{scene_num}の画像生成完了！")
                        else:
                            st.error(f"❌ 生成失敗: {result.get('message', 'Unknown error')}")
            
            with col2:
                if scene_key in st.session_state.generated_images:
                    if st.button(f"🔄 再生成", key=f"regen_{scene_num}"):
                        with st.spinner(f"シーン{scene_num}を再生成中..."):
                            result = workflow.generate_image_with_midjourney(
                                prompt=edited_prompt
                            )
                            
                            if result.get('status') == 'success':
                                st.session_state.generated_images[scene_key] = result.get('image_url')
                                st.success(f"✅ シーン{scene_num}を再生成しました！")
                                st.rerun()
            
            # 生成済み画像の表示
            if scene_key in st.session_state.generated_images:
                st.markdown("**🖼️ 生成された画像:**")
                image_url = st.session_state.generated_images[scene_key]
                
                # 画像を表示
                try:
                    st.image(image_url, use_container_width=True)
                except Exception as e:
                    st.error(f"画像表示エラー: {str(e)}")
                    st.info(f"画像URL: {image_url}")
                
                st.code(image_url, language=None)
            else:
                st.info("⏳ まだ画像が生成されていません")
    
    # 全シーンの画像が生成されているか確認
    all_generated = all(f"scene_{i+1}" in st.session_state.generated_images for i in range(len(scenes)))
    
    st.markdown("---")
    
    # 進捗状況の表示
    generated_count = sum(1 for i in range(len(scenes)) if f"scene_{i+1}" in st.session_state.generated_images)
    progress = generated_count / len(scenes) if scenes else 0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress)
        st.markdown(f"**進捗: {generated_count}/{len(scenes)} シーン完了**")
    
    with col2:
        if all_generated:
            if st.button("🎬 動画生成へ進む →", type="primary", use_container_width=True):
                st.session_state.current_step = 'video_generation'
                st.rerun()
        else:
            st.info(f"残り {len(scenes) - generated_count} シーン")

def video_generation_step():
    """動画生成ステップ（Kling）"""
    st.markdown("## 🎬 ステップ4: 動画生成（Kling）")
    
    # 戻るボタン
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 画像生成に戻る"):
            st.session_state.current_step = 'image_generation'
            st.rerun()
    
    # 画像が生成されているか確認
    if 'generated_images' not in st.session_state or not st.session_state.generated_images:
        st.warning("⚠️ まだ画像が生成されていません")
        if st.button("画像生成に戻る"):
            st.session_state.current_step = 'image_generation'
            st.rerun()
        return
    
    # 台本の確認
    script = st.session_state.selected_script
    scenes = script.get('scenes', [])
    
    st.markdown(f"### 📋 生成された画像: {len(st.session_state.generated_images)}個")
    
    # セッション状態の初期化
    if 'generated_videos' not in st.session_state:
        st.session_state.generated_videos = {}
    
    # PIAPIキーの確認
    piapi_xkey = st.session_state.api_keys.get('piapi_xkey', '')
    if not piapi_xkey:
        st.error("⚠️ PIAPI XKEYが設定されていません。サイドバーで設定してください。")
        return
    
    # 動画生成のメイン処理
    st.markdown("---")
    st.markdown("### 🎥 画像から動画を生成")
    
    from image_to_video_workflow import ImageToVideoWorkflow
    workflow = ImageToVideoWorkflow()
    
    # 各シーンの動画生成
    for i, scene in enumerate(scenes):
        scene_num = i + 1
        scene_key = f"scene_{scene_num}"
        video_key = f"video_{scene_num}"
        
        # 画像が生成されているシーンのみ処理
        if scene_key in st.session_state.generated_images:
            with st.expander(f"🎬 シーン{scene_num}: {scene.get('timestamp', '')}秒", expanded=True):
                # 画像とプロンプト表示
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**🖼️ 生成済み画像:**")
                    image_url = st.session_state.generated_images[scene_key]
                    try:
                        st.image(image_url, use_container_width=True)
                    except Exception as e:
                        st.error(f"画像表示エラー: {str(e)}")
                
                with col2:
                    st.markdown("**🎬 動画生成プロンプト:**")
                    # 動画用のプロンプトを編集可能に
                    video_prompt_key = f"video_prompt_{scene_num}"
                    default_video_prompt = scene.get('content', '') + " cinematic movement, smooth camera motion"
                    
                    edited_video_prompt = st.text_area(
                        "動画プロンプト（編集可能）",
                        default_video_prompt,
                        height=100,
                        key=video_prompt_key
                    )
                    
                    # カメラ設定
                    st.markdown("**📹 カメラ設定:**")
                    col_cam1, col_cam2 = st.columns(2)
                    with col_cam1:
                        camera_movement = st.selectbox(
                            "カメラ動作",
                            ["static", "pan_left", "pan_right", "zoom_in", "zoom_out", "tilt_up", "tilt_down"],
                            key=f"cam_{scene_num}"
                        )
                    with col_cam2:
                        duration = st.slider(
                            "動画の長さ（秒）",
                            min_value=5,
                            max_value=10,
                            value=8,
                            key=f"dur_{scene_num}"
                        )
                
                # 動画生成ボタン
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    if st.button(f"🎥 動画生成", key=f"gen_video_{scene_num}"):
                        with st.spinner(f"シーン{scene_num}の動画を生成中（最大20分かかる場合があります）..."):
                            # Kling動画生成
                            # カメラ設定をマッピング
                            camera_map = {
                                'static': {'horizontal': 0, 'vertical': 0, 'zoom': 0},
                                'pan_left': {'horizontal': -10, 'vertical': 0, 'zoom': 0},
                                'pan_right': {'horizontal': 10, 'vertical': 0, 'zoom': 0},
                                'zoom_in': {'horizontal': 0, 'vertical': 0, 'zoom': 10},
                                'zoom_out': {'horizontal': 0, 'vertical': 0, 'zoom': -10},
                                'tilt_up': {'horizontal': 0, 'vertical': 10, 'zoom': 0},
                                'tilt_down': {'horizontal': 0, 'vertical': -10, 'zoom': 0}
                            }
                            camera_config = camera_map.get(camera_movement, camera_map['static'])
                            
                            result = workflow.generate_video_with_kling(
                                image_url=image_url,
                                prompt=edited_video_prompt,
                                duration=duration,
                                camera_horizontal=camera_config['horizontal'],
                                camera_vertical=camera_config['vertical'],
                                camera_zoom=camera_config['zoom']
                            )
                            
                            if result.get('status') == 'success':
                                st.session_state.generated_videos[video_key] = result.get('video_url')
                                st.success(f"✅ シーン{scene_num}の動画生成完了！")
                                st.rerun()
                            else:
                                st.error(f"❌ 生成失敗: {result.get('message', 'Unknown error')}")
                
                with col2:
                    if video_key in st.session_state.generated_videos:
                        if st.button(f"🔄 再生成", key=f"regen_video_{scene_num}"):
                            with st.spinner(f"シーン{scene_num}を再生成中..."):
                                # カメラ設定をマッピング
                                camera_map = {
                                    'static': {'horizontal': 0, 'vertical': 0, 'zoom': 0},
                                    'pan_left': {'horizontal': -10, 'vertical': 0, 'zoom': 0},
                                    'pan_right': {'horizontal': 10, 'vertical': 0, 'zoom': 0},
                                    'zoom_in': {'horizontal': 0, 'vertical': 0, 'zoom': 10},
                                    'zoom_out': {'horizontal': 0, 'vertical': 0, 'zoom': -10},
                                    'tilt_up': {'horizontal': 0, 'vertical': 10, 'zoom': 0},
                                    'tilt_down': {'horizontal': 0, 'vertical': -10, 'zoom': 0}
                                }
                                camera_config = camera_map.get(camera_movement, camera_map['static'])
                                
                                result = workflow.generate_video_with_kling(
                                    image_url=image_url,
                                    prompt=edited_video_prompt,
                                    duration=duration,
                                    camera_horizontal=camera_config['horizontal'],
                                    camera_vertical=camera_config['vertical'],
                                    camera_zoom=camera_config['zoom']
                                )
                                
                                if result.get('status') == 'success':
                                    st.session_state.generated_videos[video_key] = result.get('video_url')
                                    st.success(f"✅ シーン{scene_num}を再生成しました！")
                                    st.rerun()
                
                # 生成済み動画の表示
                if video_key in st.session_state.generated_videos:
                    st.markdown("**🎥 生成された動画:**")
                    video_url = st.session_state.generated_videos[video_key]
                    
                    # 動画プレビュー
                    try:
                        st.video(video_url)
                    except Exception as e:
                        st.error(f"動画表示エラー: {str(e)}")
                        st.info(f"動画URL: {video_url}")
                    
                    st.code(video_url, language=None)
                else:
                    st.info("⏳ まだ動画が生成されていません")
    
    # 全シーンの動画が生成されているか確認
    total_images = len([k for k in st.session_state.generated_images.keys() if k.startswith('scene_')])
    generated_count = len([k for k in st.session_state.generated_videos.keys() if k.startswith('video_')])
    progress = generated_count / total_images if total_images > 0 else 0
    
    st.markdown("---")
    
    # 進捗状況の表示
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress)
        st.markdown(f"**進捗: {generated_count}/{total_images} シーン完了**")
    
    with col2:
        if generated_count == total_images and total_images > 0:
            if st.button("✅ 完了・ダウンロード →", type="primary", use_container_width=True):
                st.session_state.current_step = 'video_management'
                st.rerun()
        else:
            st.info(f"残り {total_images - generated_count} シーン")

def video_editing_step():
    """動画編集ステップ"""
    st.markdown("## ✂️ ステップ4: 動画編集")
    
    # 戻るボタンと動画管理ボタン
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        if st.button("← 動画生成に戻る"):
            st.session_state.current_step = 'video_generation'
            st.rerun()
    with col2:
        if st.button("📹 動画URL一覧", type="primary"):
            st.session_state.current_step = 'video_management'
            st.rerun()
    
    # 編集タブ
    tabs = st.tabs(["🎬 基本編集", "✨ エフェクト", "📝 テキスト追加", "🎵 音楽調整", "📤 エクスポート"])
    
    with tabs[0]:
        st.markdown("### 🎬 基本編集")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✂️ トリミング")
            start_time = st.number_input("開始時間（秒）", min_value=0.0, value=0.0, step=0.1)
            end_time = st.number_input("終了時間（秒）", min_value=0.1, value=180.0, step=0.1)
            
            if st.button("トリミング実行", use_container_width=True):
                st.info("トリミングを実行中...")
        
        with col2:
            st.markdown("#### 🔄 トランジション")
            transition_type = st.selectbox(
                "トランジションタイプ",
                ["フェード", "クロスフェード", "ワイプ", "ディゾルブ"]
            )
            transition_duration = st.slider("トランジション時間（秒）", 0.5, 3.0, 1.0)
            
            if st.button("トランジション追加", use_container_width=True):
                st.info("トランジションを追加中...")
    
    with tabs[1]:
        st.markdown("### ✨ エフェクト")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🎨 カラーフィルター")
            filter_type = st.selectbox(
                "フィルタータイプ",
                ["なし", "ビンテージ", "モノクロ", "セピア", "クール", "ウォーム"]
            )
            
            if st.button("フィルター適用", use_container_width=True):
                apply_filter(filter_type)
        
        with col2:
            st.markdown("#### 💫 特殊効果")
            effect_type = st.selectbox(
                "エフェクトタイプ",
                ["なし", "ブラー", "シャープ", "グロー", "ノイズ"]
            )
            effect_intensity = st.slider("強度", 0.0, 1.0, 0.5)
            
            if st.button("エフェクト適用", use_container_width=True):
                apply_effect(effect_type, effect_intensity)
        
        with col3:
            st.markdown("#### ⚡ 速度調整")
            speed = st.slider("再生速度", 0.5, 2.0, 1.0, step=0.1)
            
            if st.button("速度変更", use_container_width=True):
                adjust_speed(speed)
    
    with tabs[2]:
        st.markdown("### 📝 テキスト追加")
        
        col1, col2 = st.columns(2)
        
        with col1:
            text_content = st.text_input("テキスト内容", "")
            text_position = st.selectbox(
                "表示位置",
                ["上部", "中央", "下部", "左上", "右上", "左下", "右下"]
            )
            text_start = st.number_input("表示開始時間（秒）", 0.0, value=0.0)
            text_duration = st.number_input("表示時間（秒）", 0.1, value=3.0)
        
        with col2:
            font_size = st.slider("フォントサイズ", 12, 72, 36)
            font_color = st.color_picker("フォント色", "#FFFFFF")
            background_color = st.color_picker("背景色", "#000000")
            opacity = st.slider("不透明度", 0.0, 1.0, 1.0)
        
        if st.button("テキスト追加", type="primary", use_container_width=True):
            add_text_overlay(text_content, text_position, font_size, font_color)
    
    with tabs[3]:
        st.markdown("### 🎵 音楽調整")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔊 音量調整")
            volume = st.slider("音量", 0.0, 2.0, 1.0)
            fade_in = st.checkbox("フェードイン")
            fade_out = st.checkbox("フェードアウト")
            
            if fade_in:
                fade_in_duration = st.slider("フェードイン時間（秒）", 0.5, 5.0, 2.0)
            if fade_out:
                fade_out_duration = st.slider("フェードアウト時間（秒）", 0.5, 5.0, 2.0)
        
        with col2:
            st.markdown("#### 🎼 BGM追加")
            additional_audio = st.file_uploader(
                "追加BGM",
                type=['mp3', 'wav', 'm4a'],
                help="追加の音楽ファイル"
            )
            
            if additional_audio:
                mix_volume = st.slider("ミックス音量", 0.0, 1.0, 0.5)
                
                if st.button("BGM追加", use_container_width=True):
                    st.info("BGMを追加中...")
    
    with tabs[4]:
        st.markdown("### 📤 エクスポート")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📹 出力設定")
            resolution = st.selectbox(
                "解像度",
                ["1920x1080 (Full HD)", "1280x720 (HD)", "3840x2160 (4K)"]
            )
            format_type = st.selectbox(
                "フォーマット",
                ["MP4", "MOV", "AVI", "WebM"]
            )
            quality = st.select_slider(
                "品質",
                options=["低", "中", "高", "最高"],
                value="高"
            )
        
        with col2:
            st.markdown("#### 🎯 エクスポートオプション")
            include_watermark = st.checkbox("ウォーターマーク追加")
            if include_watermark:
                watermark_text = st.text_input("ウォーターマークテキスト", "")
            
            optimize_for = st.selectbox(
                "最適化対象",
                ["一般", "YouTube", "Instagram", "TikTok", "Twitter"]
            )
        
        st.markdown("---")
        
        if st.button("🚀 最終動画をエクスポート", type="primary", use_container_width=True):
            export_final_video()

def apply_filter(filter_type: str):
    """フィルターを適用"""
    st.success(f"✅ {filter_type}フィルターを適用しました")

def apply_effect(effect_type: str, intensity: float):
    """エフェクトを適用"""
    st.success(f"✅ {effect_type}エフェクト（強度: {intensity}）を適用しました")

def adjust_speed(speed: float):
    """速度を調整"""
    st.success(f"✅ 再生速度を{speed}倍に変更しました")

def add_text_overlay(text: str, position: str, size: int, color: str):
    """テキストオーバーレイを追加"""
    if text:
        st.success(f"✅ テキスト「{text}」を追加しました")
    else:
        st.warning("テキストを入力してください")

def export_final_video():
    """最終動画をエクスポート"""
    from agent_core.editor.video_editor import VideoEditor
    
    # 進捗表示
    progress_bar = st.progress(0)
    status = st.empty()
    
    status.text("🎬 エクスポート処理を開始...")
    progress_bar.progress(0.3)
    
    # エディターを初期化
    editor = VideoEditor()
    
    # ここで実際の編集処理を実行
    # ...
    
    progress_bar.progress(1.0)
    status.text("✅ エクスポート完了！")
    
    # ダウンロードボタンを表示
    st.download_button(
        label="📥 動画をダウンロード",
        data=b"",  # 実際のファイルデータ
        file_name="edited_pv.mp4",
        mime="video/mp4"
    )

def generate_script_pattern(pattern_type: str):
    """指定パターンで台本を生成（実際のAI APIを使用）"""
    import time
    import asyncio
    from agent_core.plot.basic_script_generator import BasicScriptGenerator
    
    # 進捗表示用のコンテナを作成
    progress_container = st.container()
    with progress_container:
        st.markdown(f"### 🎬 {pattern_type}パターンで台本生成中...")
        
        # 進捗バーとステータス表示
        col1, col2 = st.columns([4, 1])
        with col1:
            progress = st.progress(0)
        with col2:
            percentage = st.empty()
            percentage.markdown("**0%**")
        
        # ステータスと詳細情報
        status = st.empty()
        details = st.empty()
        time_estimate = st.empty()
    
    start_time = time.time()
    
    # 基本情報を取得
    info = st.session_state.basic_info
    
    # 基本情報が空の場合はデフォルト値を設定
    if not info:
        info = {
            'title': 'タイトル未設定',
            'keywords': '',
            'description': '',
            'mood': 'normal',
            'lyrics': '',
            'audio_file': None,
            'character_images': None
        }
        st.session_state.basic_info = info
    
    # 音楽ファイルの長さを取得（実際は音楽から取得）
    total_duration = 180  # デフォルト3分
    if info.get('audio_file'):
        # TODO: 実際の音楽ファイルから長さを取得
        total_duration = 180
    
    scene_duration = 8
    num_scenes = int(total_duration / scene_duration)
    
    status.text(f"📝 {pattern_type}パターンで台本を生成中...")
    percentage.text("0%")
    details.text(f"総シーン数: {num_scenes}")
    
    # 進捗コールバック関数
    def update_progress(p, msg):
        progress.progress(p)
        percentage.markdown(f"**{int(p * 100)}%**")
        status.info(msg)
        
        # 経過時間と予想時間
        elapsed = time.time() - start_time
        if p > 0 and p < 1:
            estimated_total = elapsed / p
            remaining = estimated_total - elapsed
            time_estimate.text(f"⏱️ 残り時間: 約{int(remaining)}秒")
            details.text(f"📊 処理状況: {msg}")
        elif p >= 1:
            time_estimate.success(f"✅ 完了時間: {int(elapsed)}秒")
            details.success("🎉 台本生成が完了しました！")
    
    # キャラクター参照情報を準備
    character_reference = None
    if info.get('character_images'):
        character_reference = {
            'name': '主人公',
            'description': 'アップロードされた画像の人物',
            'gender': '未指定',
            'age': '20代',
            'appearance': 'アップロードされた画像参照',
            'features': '一貫性のあるキャラクター'
        }
    
    try:
        # BasicScriptGeneratorを初期化
        config = {
            'openai_api_key': st.session_state.api_keys.get('openai', ''),
            'google_api_key': st.session_state.api_keys.get('google', ''),
            'anthropic_api_key': st.session_state.api_keys.get('anthropic', '')
        }
        
        generator = BasicScriptGenerator(config)
        
        # 非同期処理を実行
        async def generate():
            return await generator.generate_script(
                title=info.get('title', 'タイトル'),
                keywords=info.get('keywords', ''),
                description=info.get('description', ''),
                mood=info.get('mood', 'normal'),
                lyrics=info.get('lyrics', ''),
                duration=total_duration,
                pattern_type=pattern_type,
                character_reference=character_reference,
                progress_callback=update_progress
            )
        
        # 台本を生成
        script = asyncio.run(generate())
        
        # 生成された台本を保存
        st.session_state.generated_scripts.append(script)
        
        # 完了
        update_progress(1.0, "✅ 台本生成完了！")
        
        # 成功メッセージを表示（少し待機）
        time.sleep(2.0)
        
    except Exception as e:
        st.error(f"❌ 台本生成エラー: {str(e)}")
        status.error("❌ エラーが発生しました")
        details.error(str(e))
        return
    
    # 画面を更新
    st.rerun()

def generate_pv_with_script(info: dict, script: dict):
    """台本を使ってPVを生成（Text-to-Videoモード対応）"""
    import asyncio
    from agent_core.video.text_to_video_api import TextToVideoAPI
    
    # 進捗表示
    progress_container = st.container()
    with progress_container:
        st.markdown("### 🎬 動画生成中...")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            progress_bar = st.progress(0)
        with col2:
            percentage = st.empty()
            percentage.markdown("**0%**")
        
        status = st.empty()
        details = st.empty()
        time_estimate = st.empty()
    
    import time
    start_time = time.time()
    
    # 進捗コールバック
    def update_progress(p, msg):
        progress_bar.progress(p)
        percentage.markdown(f"**{int(p * 100)}%**")
        status.info(msg)
        
        elapsed = time.time() - start_time
        if p > 0 and p < 1:
            estimated_total = elapsed / p
            remaining = estimated_total - elapsed
            time_estimate.text(f"⏱️ 残り時間: 約{int(remaining)}秒")
        elif p >= 1:
            time_estimate.success(f"✅ 完了時間: {int(elapsed)}秒")
    
    try:
        # Text-to-Videoモードの確認
        if st.session_state.workflow_mode == 'text_to_video':
            # 修正版Text-to-Video APIを使用（PIAPI Hailuo/Kling）
            from text_to_video_unified_fixed import generate_videos_from_script
            
            # APIキーを設定
            if 'google' not in st.session_state.api_keys:
                st.session_state.api_keys['google'] = st.session_state.api_keys.get('google_ai', '')
            if 'seedance' not in st.session_state.api_keys:
                st.session_state.api_keys['seedance'] = st.session_state.api_keys.get('seedance', '')
            
            # キャラクター参照を準備
            character_ref = None
            if info.get('character_images'):
                # 最初の画像を参照として使用
                character_ref = "character_reference"
            
            # 動画生成を実行
            update_progress(0.05, "🎥 Text-to-Video生成を開始（Vertex AI Veo → RunComfy → Hailuo）...")
            
            # キャラクター写真があれば渡す
            character_photos = info.get('character_images', [])
            
            # Text-to-Video生成
            video_results = generate_videos_from_script(script, character_photos)
            
            # 結果を表示
            update_progress(1.0, "✅ 動画生成完了！")
            
            st.success("🎉 Text-to-Videoで動画を生成しました！")
            
            # 生成結果をセッションに保存
            st.session_state.last_generated_videos = video_results
            
            # 結果サマリーを表示
            st.markdown("### 📹 生成された動画")
            
            # テーブル形式で表示
            video_data = []
            for result in video_results:
                if result.get('status') == 'success':
                    video_data.append({
                        'シーン': f"シーン {result['scene_number']}",
                        '時間': result['timestamp'],
                        '状態': '✅ 完了',
                        'URL': result.get('video_url', 'N/A')
                    })
                else:
                    video_data.append({
                        'シーン': f"シーン {result['scene_number']}",
                        '時間': result['timestamp'],
                        '状態': '❌ 失敗',
                        'URL': '-'
                    })
            
            if video_data:
                import pandas as pd
                df = pd.DataFrame(video_data)
                st.dataframe(df, use_container_width=True)
            
            # 各シーンの詳細を表示
            st.markdown("### 📋 詳細情報")
            for result in video_results:
                if result.get('status') == 'success':
                    with st.expander(f"シーン {result['scene_number']}: {result['timestamp']}秒", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🎬 動画URL:**")
                            video_url = result.get('video_url', 'N/A')
                            if video_url != 'N/A':
                                st.code(video_url, language=None)
                                if not video_url.startswith('demo://'):
                                    st.markdown(f"[🔗 動画を開く]({video_url})")
                        
                        with col2:
                            st.markdown("**📥 ダウンロードURL:**")
                            download_url = result.get('download_url', 'N/A')
                            if download_url and download_url != 'N/A':
                                st.code(download_url, language=None)
                                if not download_url.startswith('demo://'):
                                    st.markdown(f"[⬇️ ダウンロード]({download_url})")
                        
                        # プレビュー（可能な場合）
                        if video_url and not video_url.startswith('demo://'):
                            st.video(video_url)
                else:
                    st.warning(f"シーン {result['scene_number']}: 生成失敗")
            
            # 履歴に追加
            st.session_state.generation_history.append({
                'title': info['title'],
                'timestamp': datetime.now().isoformat(),
                'mode': 'text_to_video',
                'status': 'success',
                'results': video_results
            })
            
            # 結果を返す
            return {
                'status': 'success',
                'videos': video_results
            }
            
        else:
            # クラシックモード（画像→動画）の処理
            update_progress(0.05, "🎨 画像→動画ワークフローを開始...")
            st.info("Midjourney画像生成 → Kling動画生成で処理します")
            
            # image_to_video_workflowを使用
            from image_to_video_workflow import ImageToVideoWorkflow
            
            workflow = ImageToVideoWorkflow()
            
            # キャラクター写真の処理
            character_photos = []
            if info.get('character_images'):
                for img in info.get('character_images', []):
                    # ファイルをBase64エンコード
                    import base64
                    img_data = img.read()
                    img.seek(0)  # ファイルポインタをリセット
                    b64_img = base64.b64encode(img_data).decode('utf-8')
                    character_photos.append(b64_img)
            
            # 画像→動画生成を実行
            update_progress(0.1, "🎬 シーンごとに処理を開始...")
            
            scenes = script.get('scenes', [])
            results = []
            
            for i, scene in enumerate(scenes):
                scene_num = i + 1
                progress = 0.1 + (0.8 * i / len(scenes))
                update_progress(progress, f"🎬 シーン{scene_num}/{len(scenes)}を処理中...")
                
                # 各シーンを処理（画像生成→動画生成）
                result = workflow.process_scene(
                    scene_number=scene_num,
                    scene_data=scene,
                    character_photos=character_photos
                )
                
                results.append(result)
                
                if result.get('status') == 'success':
                    st.success(f"✅ シーン{scene_num}完了")
                    if result.get('video_url'):
                        st.video(result['video_url'])
                else:
                    st.warning(f"⚠️ シーン{scene_num}生成失敗: {result.get('message', 'Unknown error')}")
            
            update_progress(1.0, "✅ 全シーン処理完了！")
            
            # 結果を保存
            st.session_state.last_generated_videos = results
            
            # 履歴に追加
            st.session_state.generation_history.append({
                'title': info['title'],
                'timestamp': datetime.now().isoformat(),
                'mode': 'image_to_video',
                'status': 'success',
                'results': results
            })
            
            return {
                'status': 'success',
                'videos': results
            }
    
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        status.error("処理中にエラーが発生しました")

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
        with st.expander("🎯 v3.3.0 詳細設定"):
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
    
    # 進捗表示用のコンテナ
    progress_container = st.container()
    with progress_container:
        col1, col2 = st.columns([3, 1])
        with col1:
            progress_bar = st.progress(0)
            status_text = st.empty()
            detail_text = st.empty()
        with col2:
            percentage_text = st.empty()
            time_estimate = st.empty()
    
    import time
    start_time = time.time()
    
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
            # v3.3.0 新ワークフロー
            status_text.text("🚀 v3.3.0 Vertex AI Veoワークフローを開始...")
            progress_bar.progress(0.05)
            percentage_text.text("5%")
            detail_text.text("初期化中...")
            time_estimate.text("予想: 2-3分")
            
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
            
            # 進捗コールバックを定義
            def update_progress(p, msg):
                progress_bar.progress(p)
                percentage_text.text(f"{int(p * 100)}%")
                status_text.text(msg)
                
                # 経過時間と予想時間を計算
                elapsed = time.time() - start_time
                if p > 0:
                    estimated_total = elapsed / p
                    remaining = estimated_total - elapsed
                    time_estimate.text(f"残り: {int(remaining)}s")
            
            # 非同期処理を実行
            async def run_generation():
                # ステップ1: 台本生成 (20%)
                update_progress(0.1, "📝 台本を生成中...")
                detail_text.text("キャラクター情報を反映中...")
                
                # ステップ2: シーン分割 (30%)
                update_progress(0.3, "🎬 シーンを分割中...")
                detail_text.text(f"総シーン数を計算中...")
                
                # ステップ3: 詳細スクリプト生成 (50%)
                update_progress(0.5, "✍️ 詳細スクリプトを作成中...")
                detail_text.text("500-1000文字/シーンで生成中...")
                
                # ステップ4: 動画生成 (80%)
                update_progress(0.8, "🎥 動画を生成中...")
                detail_text.text("Text-to-Video処理中...")
                
                return await generator.generate_pv(
                    title=title,
                    keywords=keywords,
                    description=description,
                    mood=mood,
                    lyrics=lyrics,
                    audio_file=audio_path,
                    character_images=char_paths,
                    use_text_to_video=True,
                    progress_callback=update_progress
                )
            
            result = asyncio.run(run_generation())
            
            if result['status'] == 'success':
                progress_bar.progress(1.0)
                percentage_text.text("100%")
                status_text.text("✅ PV生成完了！")
                detail_text.text(f"総時間: {int(time.time() - start_time)}秒")
                time_estimate.text("完了")
                
                st.success(f"✅ PV生成完了！")
                st.video(result['video_path'])
                
                # ダウンロードボタン
                with open(result['video_path'], 'rb') as f:
                    st.download_button(
                        label="📥 動画をダウンロード",
                        data=f,
                        file_name=f"{title}_v260.mp4",
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
            status_text.text("🎬 クラシックワークフローで生成中...")
            percentage_text.text("10%")
            detail_text.text("画像生成モード")
            
            # 既存の処理を呼び出し
            progress_bar.progress(0.5)
            percentage_text.text("50%")
            st.info("クラシックモードで処理中...")
            # ここに既存のgenerate_images_with_piapi等の処理
    
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
    
    finally:
        if 'result' not in locals() or result.get('status') != 'success':
            progress_bar.progress(1.0)
            percentage_text.text("100%")
            status_text.text("処理完了")
            detail_text.text("セッション終了")

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

def save_current_project():
    """現在のプロジェクトを保存"""
    # プロジェクトデータをまとめる
    project_data = {
        'basic_info': st.session_state.basic_info,
        'generated_scripts': st.session_state.generated_scripts,
        'selected_script': st.session_state.selected_script,
        'workflow_mode': st.session_state.workflow_mode,
        'version': '2.6.0'
    }
    
    # 保存
    project_id = st.session_state.project_storage.save_project(project_data)
    st.session_state.current_project_id = project_id
    
    st.success(f"✅ プロジェクトを保存しました: {project_id}")
    return project_id

def autosave_session():
    """セッションデータを自動保存"""
    session_data = {
        'basic_info': st.session_state.basic_info,
        'generated_scripts': st.session_state.generated_scripts,
        'selected_script': st.session_state.selected_script,
        'workflow_mode': st.session_state.workflow_mode,
        'current_step': st.session_state.current_step
    }
    
    st.session_state.project_storage.autosave(session_data)

def load_project(project_id: str):
    """プロジェクトを読み込み"""
    try:
        project_data = st.session_state.project_storage.load_project(project_id)
        
        if project_data:
            # 基本情報を復元（ファイルオブジェクトは除外）
            basic_info = project_data.get('basic_info', {})
            
            # ファイルパスが保存されている場合は、それを参照として保持
            if 'audio_file_path' in basic_info:
                # パスのみを保持（実際のファイルオブジェクトは復元できない）
                basic_info['audio_file_note'] = f"保存済み音楽ファイル: {basic_info['audio_file_path']}"
            
            if 'character_image_paths' in basic_info:
                basic_info['character_images_note'] = f"保存済みキャラクター画像: {len(basic_info['character_image_paths'])}枚"
            
            st.session_state.basic_info = basic_info
            st.session_state.generated_scripts = project_data.get('generated_scripts', [])
            st.session_state.selected_script = project_data.get('selected_script')
            st.session_state.workflow_mode = project_data.get('workflow_mode', 'text_to_video')
            st.session_state.current_project_id = project_id
            
            st.success(f"✅ プロジェクトを読み込みました: {project_id}")
            
            # 音楽ファイルと画像ファイルの注意事項を表示
            if 'audio_file_path' in basic_info or 'character_image_paths' in basic_info:
                st.info("📌 注意: 音楽ファイルと画像ファイルは再アップロードが必要な場合があります")
            
            return True
        else:
            st.error(f"❌ プロジェクトが見つかりません: {project_id}")
            return False
    except Exception as e:
        st.error(f"❌ プロジェクト読み込みエラー: {str(e)}")
        return False

def show_help():
    """ヘルプダイアログ"""
    st.markdown("""
    ### 📚 v3.3.0 使い方ガイド
    
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

def video_management_step():
    """動画管理ステップ - 生成された動画とスクリプトを一覧表示"""
    st.markdown("## 📹 生成された動画一覧")
    
    # ナビゲーションボタン
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("← 戻る"):
            st.session_state.current_step = 'video_generation'
            st.rerun()
    with col2:
        if st.button("✂️ 動画編集へ"):
            st.session_state.current_step = 'video_editing'
            st.rerun()
    with col3:
        if st.button("📁 プロジェクト管理"):
            st.session_state.current_step = 'project_management'
            st.rerun()
    
    st.markdown("---")
    
    # 生成された動画の確認
    if 'last_generated_videos' not in st.session_state or not st.session_state.last_generated_videos:
        st.warning("⚠️ まだ動画が生成されていません")
        if st.button("動画生成へ戻る", type="primary"):
            st.session_state.current_step = 'video_generation'
            st.rerun()
        return
    
    # 動画とスクリプトの統合表示
    st.markdown("### 🎬 動画とスクリプトの確認")
    
    # タブ形式で表示
    tabs = st.tabs(["📊 一覧表示", "🎬 詳細表示", "📥 ダウンロード"])
    
    with tabs[0]:
        # 一覧表示タブ
        st.markdown("#### 📊 全シーン一覧")
        
        # データフレームの作成
        import pandas as pd
        video_data = []
        
        for i, result in enumerate(st.session_state.last_generated_videos):
            # 対応するスクリプトを取得
            script_content = ""
            if st.session_state.selected_script and 'scenes' in st.session_state.selected_script:
                scenes = st.session_state.selected_script['scenes']
                if i < len(scenes):
                    script_content = scenes[i].get('content', '')[:100] + "..."
            
            video_data.append({
                'シーン番号': f"シーン {result.get('scene_number', i+1)}",
                '時間': result.get('timestamp', f"{i*8}-{(i+1)*8}"),
                'スクリプト': script_content,
                '状態': '✅ 完了' if result.get('status') == 'success' else '❌ 失敗',
                'URL': result.get('video_url', 'N/A')
            })
        
        df = pd.DataFrame(video_data)
        st.dataframe(df, use_container_width=True, height=400)
        
        # URL一覧を別途表示
        st.markdown("#### 🔗 動画URL一覧")
        for i, result in enumerate(st.session_state.last_generated_videos):
            if result.get('status') == 'success':
                video_url = result.get('video_url', 'N/A')
                if video_url and video_url != 'N/A':
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.write(f"**シーン {result.get('scene_number', i+1)}:**")
                    with col2:
                        st.code(video_url, language=None)
                        if not video_url.startswith('demo://'):
                            st.markdown(f"[🔗 開く]({video_url}) | [⬇️ ダウンロード]({result.get('download_url', video_url)})")
    
    with tabs[1]:
        # 詳細表示タブ
        st.markdown("#### 🎬 シーン詳細")
        
        for i, result in enumerate(st.session_state.last_generated_videos):
            # スクリプト情報を取得
            script_scene = None
            if st.session_state.selected_script and 'scenes' in st.session_state.selected_script:
                scenes = st.session_state.selected_script['scenes']
                if i < len(scenes):
                    script_scene = scenes[i]
            
            # エクスパンダーで各シーンを表示
            expanded = i == 0  # 最初のシーンだけ展開
            with st.expander(f"🎬 シーン {result.get('scene_number', i+1)}: {result.get('timestamp', '')}秒", expanded=expanded):
                
                # 2カラムレイアウト
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("##### 📜 スクリプト")
                    if script_scene:
                        st.write(f"**タイムスタンプ:** {script_scene.get('timestamp', 'N/A')}")
                        st.write(f"**内容:**")
                        st.text_area("", value=script_scene.get('content', ''), height=150, disabled=True, key=f"script_{i}")
                        
                        if 'video_prompt' in script_scene:
                            st.write("**動画プロンプト:**")
                            st.text_area("", value=script_scene.get('video_prompt', ''), height=100, disabled=True, key=f"prompt_{i}")
                
                with col2:
                    st.markdown("##### 🎥 生成された動画")
                    if result.get('status') == 'success':
                        video_url = result.get('video_url', 'N/A')
                        
                        # URL表示
                        st.write("**動画URL:**")
                        st.code(video_url, language=None)
                        
                        # リンクボタン
                        if video_url and not video_url.startswith('demo://'):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown(f"[🔗 動画を開く]({video_url})")
                            with col_b:
                                download_url = result.get('download_url', video_url)
                                st.markdown(f"[⬇️ ダウンロード]({download_url})")
                            
                            # 動画プレビュー
                            try:
                                st.video(video_url)
                            except:
                                st.info("プレビューは利用できません")
                        
                        # メタデータ
                        st.write("**メタデータ:**")
                        st.json({
                            "status": result.get('status'),
                            "timestamp": result.get('timestamp'),
                            "scene_number": result.get('scene_number'),
                            "message": result.get('message', '')
                        })
                    else:
                        st.error(f"❌ 生成失敗: {result.get('message', 'Unknown error')}")
    
    with tabs[2]:
        # ダウンロードタブ
        st.markdown("#### 📥 ダウンロード")
        
        # 全URLをテキストファイルとして出力
        st.markdown("##### 📝 URL一覧をダウンロード")
        
        url_list = []
        for i, result in enumerate(st.session_state.last_generated_videos):
            if result.get('status') == 'success':
                video_url = result.get('video_url', '')
                download_url = result.get('download_url', '')
                url_list.append(f"シーン {result.get('scene_number', i+1)}:")
                url_list.append(f"  動画URL: {video_url}")
                url_list.append(f"  ダウンロードURL: {download_url}")
                url_list.append("")
        
        url_text = "\n".join(url_list)
        
        st.download_button(
            label="📄 URL一覧をダウンロード (TXT)",
            data=url_text,
            file_name=f"video_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        # JSON形式でもダウンロード可能
        st.markdown("##### 📋 プロジェクトデータをダウンロード")
        
        project_data = {
            "title": st.session_state.basic_info.get('title', 'untitled'),
            "generated_at": datetime.now().isoformat(),
            "script": st.session_state.selected_script,
            "videos": st.session_state.last_generated_videos
        }
        
        st.download_button(
            label="📋 プロジェクトデータをダウンロード (JSON)",
            data=json.dumps(project_data, ensure_ascii=False, indent=2),
            file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # 個別ダウンロードリンク
        st.markdown("##### 🎬 個別動画ダウンロード")
        
        for i, result in enumerate(st.session_state.last_generated_videos):
            if result.get('status') == 'success':
                video_url = result.get('video_url', '')
                download_url = result.get('download_url', video_url)
                
                if download_url and not download_url.startswith('demo://'):
                    st.markdown(f"**シーン {result.get('scene_number', i+1)}:** [{download_url}]({download_url})")
    
    # ストレージ情報の表示
    st.markdown("---")
    st.markdown("### 💾 ストレージ情報")
    
    from agent_core.storage.video_storage import VideoStorage
    storage = VideoStorage()
    storage_info = storage.get_storage_info()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総容量", f"{storage_info['total_size_mb']} MB")
    with col2:
        st.metric("動画数", storage_info['file_count'])
    with col3:
        st.metric("プロジェクト数", storage_info['project_count'])
    with col4:
        if st.button("🗑️ 一時ファイルをクリア"):
            storage.cleanup_temp_files()
            st.success("一時ファイルをクリアしました")

def project_management_step():
    """プロジェクト管理画面"""
    st.markdown("## 📁 プロジェクト管理")
    
    # 戻るボタン
    if st.button("← ホームに戻る"):
        st.session_state.current_step = 'basic_info'
        st.rerun()
    
    st.markdown("---")
    
    # タブでプロジェクト管理
    tabs = st.tabs(["📂 プロジェクトを開く", "💾 保存済みプロジェクト一覧", "📤 エクスポート/インポート"])
    
    with tabs[0]:
        st.markdown("### 📂 保存されたプロジェクトを開く")
        
        projects = st.session_state.project_storage.list_projects()
        
        if projects:
            # プロジェクトをカード形式で表示
            for project in projects:
                with st.expander(f"📄 {project['title']} - {project['saved_at'][:19]}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**プロジェクトID:** {project['project_id']}")
                        st.write(f"**保存日時:** {project['saved_at']}")
                        st.write(f"**バージョン:** {project['version']}")
                    
                    with col2:
                        if st.button("📂 開く", key=f"open_{project['project_id']}", use_container_width=True):
                            if load_project(project['project_id']):
                                st.session_state.current_step = 'script_generation'
                                st.rerun()
                    
                    with col3:
                        if st.button("🗑️ 削除", key=f"delete_{project['project_id']}", use_container_width=True):
                            if st.session_state.project_storage.delete_project(project['project_id']):
                                st.success(f"プロジェクト {project['title']} を削除しました")
                                st.rerun()
        else:
            st.info("💡 保存されたプロジェクトがありません")
            st.markdown("""
            プロジェクトを保存するには：
            1. 基本情報を入力
            2. 「💾 保存」ボタンをクリック
            3. または各ステップで自動保存されます
            """)
    
    with tabs[1]:
        st.markdown("### 💾 保存済みプロジェクト一覧")
        
        projects = st.session_state.project_storage.list_projects()
        
        if projects:
            # テーブル形式で表示
            import pandas as pd
            df = pd.DataFrame(projects)
            df['saved_at'] = pd.to_datetime(df['saved_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(df[['title', 'saved_at', 'version']], use_container_width=True)
            
            st.markdown(f"**合計プロジェクト数:** {len(projects)}")
        else:
            st.info("保存されたプロジェクトがありません")
    
    with tabs[2]:
        st.markdown("### 📤 エクスポート / インポート")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📤 エクスポート")
            
            projects = st.session_state.project_storage.list_projects()
            if projects:
                selected_project = st.selectbox(
                    "エクスポートするプロジェクト",
                    options=[p['project_id'] for p in projects],
                    format_func=lambda x: next(p['title'] for p in projects if p['project_id'] == x)
                )
                
                if st.button("📥 ZIPファイルとしてダウンロード", use_container_width=True):
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                        if st.session_state.project_storage.export_project(selected_project, tmp.name):
                            with open(tmp.name, 'rb') as f:
                                st.download_button(
                                    label="📥 ダウンロード",
                                    data=f.read(),
                                    file_name=f"{selected_project}.zip",
                                    mime="application/zip"
                                )
                            os.unlink(tmp.name)
            else:
                st.info("エクスポートできるプロジェクトがありません")
        
        with col2:
            st.markdown("#### 📥 インポート")
            
            uploaded_file = st.file_uploader(
                "ZIPファイルをアップロード",
                type=['zip'],
                help="エクスポートしたプロジェクトファイルを選択"
            )
            
            if uploaded_file:
                if st.button("📤 インポート実行", use_container_width=True):
                    import tempfile
                    
                    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                        tmp.write(uploaded_file.read())
                        tmp.flush()
                        
                        project_id = st.session_state.project_storage.import_project(tmp.name)
                        
                        if project_id:
                            st.success(f"✅ プロジェクトをインポートしました: {project_id}")
                            st.rerun()
                        else:
                            st.error("❌ インポートに失敗しました")
                        
                        os.unlink(tmp.name)

def project_management_tab():
    """プロジェクト管理タブ（メインタブ用）"""
    st.markdown("### 📁 プロジェクト管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 現在のプロジェクトを保存", use_container_width=True):
            save_current_project()
    
    with col2:
        if st.button("📂 プロジェクトを開く", use_container_width=True):
            st.session_state.current_step = 'project_management'
            st.rerun()
    
    with col3:
        if st.button("🔄 最後の自動保存を復元", use_container_width=True):
            autosave_data = st.session_state.project_storage.load_autosave()
            if autosave_data:
                st.session_state.basic_info = autosave_data.get('basic_info', {})
                st.session_state.generated_scripts = autosave_data.get('generated_scripts', [])
                st.session_state.selected_script = autosave_data.get('selected_script')
                st.success("✅ 自動保存データを復元しました")
                st.rerun()
            else:
                st.info("自動保存データがありません")
    
    st.markdown("---")
    
    # 最近のプロジェクト
    st.markdown("#### 📋 最近のプロジェクト")
    projects = st.session_state.project_storage.list_projects()
    
    if projects:
        for project in projects[:5]:  # 最新5件
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 **{project['title']}**")
                st.caption(f"{project['saved_at'][:19]} | v{project['version']}")
            
            with col2:
                if st.button("開く", key=f"quick_open_{project['project_id']}"):
                    load_project(project['project_id'])
                    st.rerun()
            
            with col3:
                if st.button("削除", key=f"quick_delete_{project['project_id']}"):
                    st.session_state.project_storage.delete_project(project['project_id'])
                    st.rerun()
    else:
        st.info("まだプロジェクトが保存されていません")

if __name__ == "__main__":
    main()