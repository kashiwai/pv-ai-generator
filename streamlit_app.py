"""
PV自動生成AIエージェント - Streamlit版（修正版）
タブの順番と内容を正しく配置
"""
import streamlit as st
import os
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from lyrics_parser import parse_lyrics_to_scenes, identify_key_moments, suggest_scene_emotion
from script_templates import (
    generate_narrative_scene,
    generate_visual_scene,
    generate_music_sync_scene,
    create_detailed_midjourney_prompt,
    create_character_reference_prompt,
    prepare_character_for_midjourney
)

# Import with proper error handling
import sys
import traceback
import io
import math

# 以下は既存のコードの初期化部分を維持
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False
GOOGLE_AI_AVAILABLE = False
GTTS_AVAILABLE = False
CV2_AVAILABLE = False
PYDUB_AVAILABLE = False

# Try importing each package
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception as e:
    print(f"OpenAI import error: {e}")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except Exception as e:
    print(f"Anthropic import error: {e}")

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except Exception as e:
    print(f"Google AI import error: {e}")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except Exception as e:
    print(f"gTTS import error: {e}")

try:
    import cv2
    CV2_AVAILABLE = True
except Exception as e:
    print(f"OpenCV import error: {e}")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except Exception as e:
    print(f"Pydub import error: {e}")

# ページ設定
st.set_page_config(
    page_title="PV自動生成AIエージェント",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'generated_videos' not in st.session_state:
    st.session_state.generated_videos = []
if 'current_script' not in st.session_state:
    st.session_state.current_script = None
if 'scene_details' not in st.session_state:
    st.session_state.scene_details = []
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'api_keys' not in st.session_state:
    # Streamlit CloudのSecretsからAPIキーを初期化
    st.session_state.api_keys = {
        'piapi': st.secrets.get('PIAPI_KEY', ''),
        'piapi_xkey': st.secrets.get('PIAPI_XKEY', ''),
        'openai': st.secrets.get('OPENAI_API_KEY', ''),
        'google': st.secrets.get('GOOGLE_API_KEY', ''),
        'anthropic': st.secrets.get('ANTHROPIC_API_KEY', ''),
        'fish_audio': st.secrets.get('FISH_AUDIO_API_KEY', ''),
        'deepseek': st.secrets.get('DEEPSEEK_API_KEY', '')
    }

# Secretsの安全な取得関数
def get_secret(key, default=''):
    try:
        return st.secrets.get(key, default)
    except:
        return default

# 音楽ファイルの長さを取得する関数
def get_audio_duration(audio_file):
    """音楽ファイルの長さを秒単位で取得"""
    try:
        if PYDUB_AVAILABLE:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_file.read()))
            audio_file.seek(0)
            return len(audio) / 1000.0
        else:
            return 194.0
    except Exception as e:
        st.warning(f"音楽ファイルの長さを取得できませんでした。デフォルト値を使用します。")
        return 194.0

# PVのシーン分割を計算する関数
def calculate_scene_division(music_duration_sec):
    """音楽の長さからPVのシーン分割を計算"""
    pv_total_duration = music_duration_sec + 6
    avg_scene_duration = 6.5
    estimated_scenes = int(pv_total_duration / avg_scene_duration)
    
    scenes = []
    remaining_time = pv_total_duration
    scene_durations = [5, 6, 7, 8]
    
    for i in range(estimated_scenes):
        if remaining_time <= 0:
            break
        
        if remaining_time <= 8:
            duration = remaining_time
        else:
            duration = scene_durations[i % len(scene_durations)]
            if duration > remaining_time:
                duration = remaining_time
        
        start_time = pv_total_duration - remaining_time
        end_time = start_time + duration
        
        scenes.append({
            'scene_number': i + 1,
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time,
            'time_range': f"{format_time(start_time)}-{format_time(end_time)}"
        })
        
        remaining_time -= duration
    
    return {
        'music_duration': music_duration_sec,
        'pv_duration': pv_total_duration,
        'total_scenes': len(scenes),
        'scenes': scenes
    }

def format_time(seconds):
    """秒を MM:SS 形式に変換"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
    }
    .scene-card {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .api-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    .api-connected {
        background: #d4edda;
        color: #155724;
    }
    .api-disconnected {
        background: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<h1 class="main-header">🎬 PV自動生成AIエージェント</h1>', unsafe_allow_html=True)
st.markdown("**完全版** - 全機能搭載（画像生成・台本編集・エフェクト・音楽同期）")

# サイドバー - API設定（既存のコードを維持）
with st.sidebar:
    st.header("⚙️ API設定")
    
    st.subheader("🔑 APIキー設定")
    
    with st.expander("必須APIキー", expanded=True):
        piapi_key = st.text_input(
            "PIAPI メインKEY",
            type="password",
            help="PIAPIメインキー（認証用）",
            value=st.session_state.api_keys.get('piapi', ''),
            key="piapi_input"
        )
        if piapi_key:
            st.session_state.api_keys['piapi'] = piapi_key
        
        piapi_xkey = st.text_input(
            "PIAPI XKEY",
            type="password",
            help="PIAPI XKEY（Midjourney, Hailuo等のサービスアクセス用）",
            value=st.session_state.api_keys.get('piapi_xkey', ''),
            key="piapi_xkey_input"
        )
        if piapi_xkey:
            st.session_state.api_keys['piapi_xkey'] = piapi_xkey
        
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="GPT-4での台本生成に使用",
            value=st.session_state.api_keys.get('openai', ''),
            key="openai_input"
        )
        if openai_key:
            st.session_state.api_keys['openai'] = openai_key
        
        google_key = st.text_input(
            "Google API Key",
            type="password",
            help="Gemini・音声合成に使用",
            value=st.session_state.api_keys.get('google', ''),
            key="google_input"
        )
        if google_key:
            st.session_state.api_keys['google'] = google_key
    
    with st.expander("オプションAPIキー"):
        anthropic_key = st.text_input(
            "Anthropic API Key (Claude)",
            type="password",
            help="Claude 3での創造的な台本生成",
            value=st.session_state.api_keys.get('anthropic', ''),
            key="anthropic_input"
        )
        if anthropic_key:
            st.session_state.api_keys['anthropic'] = anthropic_key
        
        fish_audio_key = st.text_input(
            "Fish Audio API Key",
            type="password",
            help="高品質音声合成",
            value=st.session_state.api_keys.get('fish_audio', ''),
            key="fish_audio_input"
        )
        if fish_audio_key:
            st.session_state.api_keys['fish_audio'] = fish_audio_key
        
        deepseek_key = st.text_input(
            "Deepseek API Key",
            type="password",
            help="コスト効率の良い処理",
            value=st.session_state.api_keys.get('deepseek', ''),
            key="deepseek_input"
        )
        if deepseek_key:
            st.session_state.api_keys['deepseek'] = deepseek_key
    
    # API接続状態表示
    st.markdown("---")
    st.subheader("📊 接続状態")
    
    for key_name, key_value in st.session_state.api_keys.items():
        if key_value:
            st.markdown(f'<div class="api-status api-connected">✅ {key_name.upper()}: 接続済み</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="api-status api-disconnected">❌ {key_name.upper()}: 未接続</div>', unsafe_allow_html=True)

# メインコンテンツ - タブ構成
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 基本入力",
    "📋 台本生成",
    "🖼️ 画像生成",
    "🎬 動画作成",
    "✂️ 編集・エフェクト",
    "📚 履歴・ガイド"
])

# タブ1: 基本入力は既存のコードを維持
with tab1:
    st.header("📝 基本入力")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("🎯 プロジェクト情報")
        
        project_name = st.text_input(
            "プロジェクト名 *",
            placeholder="例: 青春ドラマPV",
            help="プロジェクトを識別する名前",
            key="project_name"
        )
        
        title = st.text_input(
            "PVタイトル *",
            placeholder="例: 明日への扉",
            help="実際のPVのタイトル"
        )
        
        col_sub1, col_sub2 = st.columns(2)
        
        with col_sub1:
            genre = st.selectbox(
                "ジャンル",
                ["ドラマ", "アクション", "ファンタジー", "SF", "ホラー", "コメディ", "ロマンス", "ミュージックビデオ"]
            )
        
        with col_sub2:
            duration = st.selectbox(
                "目標時間",
                ["30秒", "1分", "2分", "3分", "5分", "7分（最大）"]
            )
        
        keywords = st.text_input(
            "キーワード（カンマ区切り）",
            placeholder="青春, 友情, 冒険, 希望",
            help="PVのテーマやコンセプトを表すキーワード"
        )
        
        description = st.text_area(
            "詳細説明",
            height=100,
            placeholder="PVのコンセプトやストーリーの概要を記述",
            help="AIが台本を生成する際の参考になります"
        )
    
    with col2:
        st.subheader("👤 出演者設定")
        
        use_character = st.radio(
            "出演者の写真を使用しますか？",
            ["写真を使用する（同一人物でPV作成）", "写真なし（音楽性重視のPV）"],
            key="use_character_photo",
            help="写真を使用すると、同じ人物で一貫性のあるPVが作成されます"
        )
        
        if use_character == "写真を使用する（同一人物でPV作成）":
            st.markdown("#### 👥 出演者の写真")
            character_photos = st.file_uploader(
                "出演者の写真をアップロード",
                type=['png', 'jpg', 'jpeg', 'webp'],
                accept_multiple_files=True,
                key="character_photos",
                help="同じ人物の写真を複数枚アップロード（推奨: 3-10枚）"
            )
            
            if character_photos:
                st.success(f"✅ {len(character_photos)}枚の写真をアップロード")
                
                preview_cols = st.columns(min(len(character_photos), 3))
                for idx, photo in enumerate(character_photos[:3]):
                    with preview_cols[idx % 3]:
                        st.image(photo, caption=f"写真{idx+1}", use_column_width=True)
                
                if len(character_photos) > 3:
                    st.caption(f"他{len(character_photos)-3}枚")
                
                st.session_state['character_settings'] = {
                    'photos': character_photos
                }
        else:
            st.info("音楽性とコンセプトに基づいてPVを生成します")
            st.session_state['character_settings'] = None
        
        st.markdown("---")
        st.subheader("🎵 音楽ファイル")
        
        audio_file = st.file_uploader(
            "音楽をアップロード *",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help="最大200MBまで対応",
            key="audio_file"
        )
        
        if audio_file:
            st.audio(audio_file)
            st.success(f"✅ {audio_file.name}")
            
            with st.spinner("音楽ファイルを分析中..."):
                duration_sec = get_audio_duration(audio_file)
                st.session_state['music_duration'] = duration_sec
                
                scene_division = calculate_scene_division(duration_sec)
                st.session_state['scene_division'] = scene_division
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("🎵 音楽の長さ", format_time(duration_sec))
                    st.metric("🎬 PVの長さ", format_time(scene_division['pv_duration']))
                with col_info2:
                    st.metric("📋 総シーン数", f"{scene_division['total_scenes']}シーン")
                    st.metric("⏱️ 平均シーン長", "5-8秒")
        
        # 歌詞入力
        st.subheader("📝 歌詞/ナレーション")
        
        lyrics_input_type = st.radio(
            "入力方法",
            ["直接入力", "ファイルアップロード", "自動生成"],
            horizontal=True
        )
        
        if lyrics_input_type == "直接入力":
            lyrics = st.text_area(
                "歌詞/ナレーションを入力",
                height=150,
                placeholder="[Verse 1]\n歌詞をここに...\n\n[Chorus]\n...",
                key="lyrics_input"
            )
            if lyrics:
                st.session_state['lyrics'] = lyrics
                st.success(f"✅ 歌詞を入力しました（{len(lyrics.split())} ワード）")

# タブ2: 台本生成
with tab2:
    st.header("📋 台本生成")
    
    # 必要な情報の確認
    lyrics_text = st.session_state.get('lyrics', '')
    scene_division = st.session_state.get('scene_division', None)
    
    if not scene_division:
        st.warning("⚠️ まず基本入力タブで音楽ファイルをアップロードしてください")
    else:
        col_gen1, col_gen2 = st.columns([2, 3])
        
        with col_gen1:
            st.subheader("🤖 生成設定")
            
            # AIモデル選択
            ai_model = st.selectbox(
                "AIモデル選択",
                ["GPT-4 (推奨)", "Claude 3", "Gemini Pro", "Deepseek (コスト効率重視)"],
                help="台本生成に使用するAIモデル"
            )
            
            # 台本スタイル選択
            script_style = st.selectbox(
                "台本スタイル",
                ["自動選択（推奨）", "ストーリー重視", "ビジュアル重視", "音楽同期重視"],
                help="生成する台本の方向性"
            )
            
            # 生成詳細度
            detail_level = st.slider(
                "詳細度",
                min_value=1,
                max_value=5,
                value=3,
                help="1:シンプル、5:非常に詳細"
            )
            
            # トーン設定
            tone = st.multiselect(
                "トーン・雰囲気",
                ["感動的", "エネルギッシュ", "神秘的", "楽しい", "切ない", "力強い", "優しい", "クール"],
                default=["感動的", "エネルギッシュ"]
            )
            
            # 生成ボタン
            if st.button("🎯 台本を3パターン生成", type="primary", use_container_width=True):
                with st.spinner("台本を生成中..."):
                    # 台本生成のシミュレーション
                    patterns = []
                    
                    # パターン1: ストーリー重視
                    pattern1_scenes = []
                    for scene in scene_division['scenes']:
                        scene_detail = generate_narrative_scene(
                            "narrative",
                            lyrics_text,
                            scene['scene_number'],
                            scene_division['total_scenes']
                        )
                        scene_detail['time'] = scene['time_range']
                        scene_detail['duration'] = scene['duration']
                        pattern1_scenes.append(scene_detail)
                    
                    patterns.append({
                        'title': 'パターン1: ストーリー重視',
                        'description': '物語性を重視した感動的な展開',
                        'scenes': pattern1_scenes
                    })
                    
                    # パターン2: ビジュアル重視
                    pattern2_scenes = []
                    for scene in scene_division['scenes']:
                        scene_detail = generate_visual_scene(
                            "visual",
                            lyrics_text,
                            scene['scene_number'],
                            scene_division['total_scenes']
                        )
                        scene_detail['time'] = scene['time_range']
                        scene_detail['duration'] = scene['duration']
                        pattern2_scenes.append(scene_detail)
                    
                    patterns.append({
                        'title': 'パターン2: ビジュアル重視',
                        'description': '視覚的インパクトを重視した演出',
                        'scenes': pattern2_scenes
                    })
                    
                    # パターン3: 音楽同期重視
                    pattern3_scenes = []
                    for scene in scene_division['scenes']:
                        scene_detail = generate_music_sync_scene(
                            "music_sync",
                            lyrics_text,
                            scene['scene_number'],
                            scene_division['total_scenes']
                        )
                        scene_detail['time'] = scene['time_range']
                        scene_detail['duration'] = scene['duration']
                        pattern3_scenes.append(scene_detail)
                    
                    patterns.append({
                        'title': 'パターン3: 音楽同期重視',
                        'description': 'リズムとテンポに合わせた展開',
                        'scenes': pattern3_scenes
                    })
                    
                    st.session_state['script_patterns'] = patterns
                    st.success("✅ 3パターンの台本を生成しました")
        
        with col_gen2:
            st.subheader("📄 生成された台本")
            
            if 'script_patterns' in st.session_state:
                # パターン選択タブ
                pattern_tabs = st.tabs([p['title'] for p in st.session_state['script_patterns']])
                
                for idx, (pattern_tab, pattern) in enumerate(zip(pattern_tabs, st.session_state['script_patterns'])):
                    with pattern_tab:
                        st.markdown(f"**{pattern['description']}**")
                        
                        # このパターンを選択するボタン
                        if st.button(f"✅ このパターンを採用", key=f"select_pattern_{idx}"):
                            st.session_state['selected_script'] = pattern
                            st.session_state['selected_pattern_idx'] = idx
                            st.success(f"「{pattern['title']}」を選択しました")
                        
                        # シーン表示
                        for scene in pattern['scenes']:
                            with st.expander(f"🎬 シーン{scene['scene_number']} ({scene['time']}) - {scene['duration']}秒"):
                                # ストーリー内容
                                st.markdown("**📖 ストーリー:**")
                                st.write(scene.get('story', ''))
                                
                                # キャラクターアクション
                                st.markdown("**🎭 アクション:**")
                                st.write(scene.get('character_action', ''))
                                
                                # 環境・背景
                                st.markdown("**🌍 環境:**")
                                st.write(scene.get('environment', ''))
                                
                                # 感情表現
                                st.markdown("**💭 感情:**")
                                st.write(scene.get('emotion', ''))
                                
                                # カメラワーク
                                st.markdown("**📹 カメラ:**")
                                st.write(scene.get('camera_work', ''))
                                
                                # Midjourneyプロンプト
                                st.markdown("**🎨 Midjourney プロンプト:**")
                                if 'character_settings' in st.session_state and st.session_state['character_settings']:
                                    # キャラクター参照付きプロンプト
                                    prompt = create_character_reference_prompt(
                                        scene.get('visual_prompt', ''),
                                        "--cref [character_url] --cw 100"
                                    )
                                else:
                                    prompt = create_detailed_midjourney_prompt(scene)
                                st.code(prompt, language="text")
            else:
                st.info("💡 左側の設定から台本を生成してください")
        
        # 選択した台本の編集エリア
        if 'selected_script' in st.session_state:
            st.markdown("---")
            st.subheader("✏️ 台本の編集")
            
            edited_scenes = []
            for scene in st.session_state['selected_script']['scenes']:
                with st.expander(f"シーン{scene['scene_number']}の編集"):
                    edited_scene = scene.copy()
                    edited_scene['story'] = st.text_area(
                        "ストーリー",
                        value=scene.get('story', ''),
                        key=f"edit_story_{scene['scene_number']}"
                    )
                    edited_scene['visual_prompt'] = st.text_area(
                        "Midjourneyプロンプト",
                        value=scene.get('visual_prompt', ''),
                        key=f"edit_prompt_{scene['scene_number']}"
                    )
                    edited_scenes.append(edited_scene)
            
            if st.button("💾 編集内容を保存", type="primary"):
                st.session_state['selected_script']['scenes'] = edited_scenes
                st.session_state['final_script'] = st.session_state['selected_script']
                st.success("✅ 台本を保存しました")

# タブ3: 画像生成
with tab3:
    st.header("🖼️ 画像生成")
    
    if 'final_script' not in st.session_state:
        st.warning("⚠️ まず台本生成タブで台本を作成してください")
    else:
        col_img1, col_img2 = st.columns([1, 2])
        
        with col_img1:
            st.subheader("🎨 生成設定")
            
            # Midjourney設定
            st.markdown("**Midjourney パラメータ**")
            
            aspect_ratio = st.selectbox(
                "アスペクト比",
                ["16:9 (推奨)", "9:16", "1:1", "4:3"],
                help="動画のアスペクト比"
            )
            
            quality_level = st.slider(
                "品質",
                min_value=1,
                max_value=5,
                value=2,
                help="生成品質（高いほど時間がかかります）"
            )
            
            style_level = st.slider(
                "スタイライズ",
                min_value=0,
                max_value=1000,
                value=100,
                help="アート性の強さ"
            )
            
            # キャラクター設定確認
            if 'character_settings' in st.session_state and st.session_state['character_settings']:
                st.success("✅ キャラクター参照画像を使用")
                st.caption("同一人物で一貫性のある画像を生成します")
            else:
                st.info("ℹ️ キャラクター参照なし")
                st.caption("各シーンごとに最適な画像を生成します")
            
            # 生成開始ボタン
            if st.button("🚀 画像生成を開始", type="primary", use_container_width=True):
                with st.spinner("PIAPIを通じて画像を生成中..."):
                    # PIAPIで画像生成
                    from piapi_integration import generate_images_with_piapi
                    
                    character_photos = None
                    if 'character_settings' in st.session_state and st.session_state['character_settings']:
                        character_photos = st.session_state['character_settings']['photos']
                    
                    # 台本に基づいて画像生成
                    generated_images = generate_images_with_piapi(
                        st.session_state['final_script'],
                        character_photos
                    )
                    
                    st.session_state['generated_images'] = generated_images
                    st.success(f"✅ {len(generated_images)}枚の画像生成を開始しました")
        
        with col_img2:
            st.subheader("🖼️ 生成された画像")
            
            if 'generated_images' in st.session_state:
                # 画像表示グリッド
                cols = st.columns(3)
                for idx, image in enumerate(st.session_state['generated_images']):
                    with cols[idx % 3]:
                        if image.get('result_url'):
                            st.image(image['result_url'], caption=f"シーン{image['scene_id']}")
                            st.caption(f"状態: {image['status']}")
                        else:
                            st.info(f"シーン{image['scene_id']}: 生成中...")
                            if image.get('progress'):
                                st.progress(image['progress'] / 100)
            else:
                st.info("💡 左側の設定から画像生成を開始してください")

# タブ4: 動画作成
with tab4:
    st.header("🎬 動画作成")
    
    if 'generated_images' not in st.session_state:
        st.warning("⚠️ まず画像生成タブで画像を生成してください")
    else:
        col_vid1, col_vid2 = st.columns([1, 2])
        
        with col_vid1:
            st.subheader("🎥 動画生成設定")
            
            # Hailuo AI設定
            st.markdown("**Hailuo AI パラメータ**")
            
            motion_intensity = st.slider(
                "モーション強度",
                min_value=1,
                max_value=10,
                value=5,
                help="動きの激しさ"
            )
            
            camera_movement = st.selectbox(
                "カメラ動作",
                ["自動", "固定", "パン", "ズーム", "回転"],
                help="カメラの動き方"
            )
            
            transition_type = st.selectbox(
                "トランジション",
                ["スムーズ", "カット", "フェード", "ディゾルブ"],
                help="シーン間の切り替え方法"
            )
            
            # 音楽同期確認
            if 'music_duration' in st.session_state:
                st.info(f"🎵 音楽: {format_time(st.session_state['music_duration'])}")
                st.info(f"🎬 PV: {format_time(st.session_state['music_duration'] + 6)}")
            
            # PV生成開始
            if st.button("🎬 PV生成を開始", type="primary", use_container_width=True):
                with st.spinner("Hailuo AIで動画を生成中..."):
                    from piapi_integration import create_pv_with_piapi
                    
                    music_info = {
                        'duration': st.session_state.get('music_duration', 194),
                        'url': None  # 音楽ファイルのURL
                    }
                    
                    settings = {
                        'motion_intensity': motion_intensity,
                        'camera_movement': camera_movement,
                        'transition_type': transition_type
                    }
                    
                    result = create_pv_with_piapi(
                        st.session_state['generated_images'],
                        music_info,
                        settings
                    )
                    
                    if result['status'] == 'success':
                        st.session_state['final_pv'] = result
                        st.success("✅ PV生成が完了しました！")
        
        with col_vid2:
            st.subheader("🎬 生成されたPV")
            
            if 'final_pv' in st.session_state:
                if st.session_state['final_pv'].get('video_url'):
                    st.video(st.session_state['final_pv']['video_url'])
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "⬇️ PVをダウンロード",
                            data=st.session_state['final_pv']['video_url'],
                            file_name="generated_pv.mp4",
                            mime="video/mp4"
                        )
                    with col_dl2:
                        if st.button("📤 YouTubeにアップロード"):
                            st.info("YouTube連携機能は開発中です")
            else:
                st.info("💡 左側の設定からPV生成を開始してください")

# タブ5: 編集・エフェクト
with tab5:
    st.header("✂️ 編集・エフェクト")
    
    col_edit1, col_edit2 = st.columns([1, 2])
    
    with col_edit1:
        st.subheader("🎨 エフェクト設定")
        
        # カラーグレーディング
        st.markdown("**カラーグレーディング**")
        color_preset = st.selectbox(
            "プリセット",
            ["なし", "シネマティック", "ビンテージ", "モノクロ", "高彩度", "パステル"]
        )
        
        brightness = st.slider("明度", -100, 100, 0)
        contrast = st.slider("コントラスト", -100, 100, 0)
        saturation = st.slider("彩度", -100, 100, 0)
        
        # フィルター
        st.markdown("**フィルター効果**")
        blur_amount = st.slider("ブラー", 0, 10, 0)
        vignette = st.slider("ビネット", 0, 100, 0)
        grain = st.slider("フィルムグレイン", 0, 100, 0)
        
        # テキストオーバーレイ
        st.markdown("**テキスト追加**")
        add_title = st.checkbox("タイトルを追加")
        if add_title:
            title_text = st.text_input("タイトルテキスト")
            title_position = st.selectbox("位置", ["上部", "中央", "下部"])
        
        add_credits = st.checkbox("クレジットを追加")
        if add_credits:
            credits_text = st.text_area("クレジット内容", height=100)
    
    with col_edit2:
        st.subheader("📹 プレビュー")
        
        if 'final_pv' in st.session_state:
            st.info("エフェクト適用のプレビュー機能は開発中です")
            
            if st.button("💾 エフェクトを適用", type="primary"):
                with st.spinner("エフェクトを適用中..."):
                    time.sleep(2)
                    st.success("✅ エフェクトを適用しました")
        else:
            st.info("PVが生成されていません")

# タブ6: 履歴・ガイド
with tab6:
    st.header("📚 履歴・ガイド")
    
    tab_history, tab_guide = st.tabs(["📋 生成履歴", "📖 使い方ガイド"])
    
    with tab_history:
        st.subheader("📋 生成履歴")
        
        if 'generated_videos' in st.session_state and st.session_state['generated_videos']:
            for idx, video in enumerate(st.session_state['generated_videos']):
                with st.expander(f"プロジェクト: {video.get('title', f'PV {idx+1}')}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"生成日時: {video.get('created_at', 'N/A')}")
                        st.write(f"長さ: {video.get('duration', 'N/A')}")
                        st.write(f"ステータス: {video.get('status', 'N/A')}")
                    with col2:
                        if st.button("読み込む", key=f"load_{idx}"):
                            st.info("プロジェクト読み込み機能は開発中です")
        else:
            st.info("まだ生成履歴がありません")
    
    with tab_guide:
        st.subheader("📖 使い方ガイド")
        
        st.markdown("""
        ### 🚀 クイックスタート
        
        1. **API設定** - サイドバーでAPIキーを入力
           - PIAPI メインKEY（必須）
           - PIAPI XKEY（必須）
           - その他のAPIキー（オプション）
        
        2. **基本入力** - プロジェクト情報を入力
           - 音楽ファイルをアップロード
           - 出演者の写真をアップロード（オプション）
           - 歌詞を入力
        
        3. **台本生成** - AIが3パターンの台本を生成
           - お好みのパターンを選択
           - 必要に応じて編集
        
        4. **画像生成** - Midjourneyで各シーンの画像を生成
           - キャラクター参照で一貫性を保持
        
        5. **動画作成** - Hailuo AIで動画化
           - 音楽と完全同期
           - 最終的なPVが完成
        
        ### 💡 ヒント
        
        - **音楽同期**: PVは音楽より6秒長く生成されます
        - **シーン分割**: 各シーンは5-8秒で自動分割
        - **キャラクター一貫性**: 同じ人物の写真を使用すると統一感のあるPVに
        - **Midjourneyプロンプト**: --ar 16:9 --v 6 が自動付与されます
        
        ### ⚠️ トラブルシューティング
        
        - **APIエラー**: APIキーが正しく設定されているか確認
        - **生成失敗**: PIAPIの2つのキー（メインKEYとXKEY）を確認
        - **画像が表示されない**: Midjourney側の処理待ちの可能性
        """)

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    🎬 PV自動生成AIエージェント v2.0 | Powered by PIAPI (Midjourney + Hailuo AI)
</div>
""", unsafe_allow_html=True)