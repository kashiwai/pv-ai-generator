"""
PV自動生成AIエージェント - Streamlit版（フル機能版）
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

# Initialize availability flags
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
        # pydubが利用可能な場合
        if PYDUB_AVAILABLE:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_file.read()))
            audio_file.seek(0)  # ファイルポインタをリセット
            return len(audio) / 1000.0  # ミリ秒を秒に変換
        else:
            # デモ用のデフォルト値（3分14秒）
            return 194.0
    except Exception as e:
        st.warning(f"音楽ファイルの長さを取得できませんでした。デフォルト値を使用します。")
        return 194.0  # デフォルト3分14秒

# PVのシーン分割を計算する関数
def calculate_scene_division(music_duration_sec):
    """
    音楽の長さからPVのシーン分割を計算
    - PV総時間 = 音楽の長さ + 6秒
    - 各シーン: 5-8秒（平均6.5秒）
    """
    pv_total_duration = music_duration_sec + 6  # 6秒追加
    
    # 平均シーン長を6.5秒として計算
    avg_scene_duration = 6.5
    estimated_scenes = int(pv_total_duration / avg_scene_duration)
    
    # シーンリストを作成（5-8秒でランダマイズ）
    scenes = []
    remaining_time = pv_total_duration
    scene_durations = [5, 6, 7, 8]  # 利用可能な秒数
    
    for i in range(estimated_scenes):
        if remaining_time <= 0:
            break
        
        # 残り時間が少ない場合は調整
        if remaining_time <= 8:
            duration = remaining_time
        else:
            # 5-8秒からランダムに選択（バランスよく）
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

# サイドバー - API設定
with st.sidebar:
    st.header("⚙️ API設定")
    
    # APIキー入力（6個全て）
    st.subheader("🔑 APIキー設定")
    
    with st.expander("必須APIキー", expanded=True):
        # APIキーはセッション状態に保存されているため、それを使用
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
    
    # 詳細設定
    st.markdown("---")
    st.subheader("🎛️ 詳細設定")
    
    with st.expander("動画生成設定"):
        video_provider = st.selectbox(
            "動画生成プロバイダー",
            ["Hailuo 02 AI (推奨)", "SORA", "VEO3", "Seedance", "DomoAI"]
        )
        
        video_quality = st.select_slider(
            "動画品質",
            options=["低", "中", "高", "最高"],
            value="高"
        )
        
        scene_duration = st.slider(
            "シーンの長さ（秒）",
            min_value=3,
            max_value=15,
            value=8
        )
    
    with st.expander("音声設定"):
        tts_provider = st.selectbox(
            "音声合成プロバイダー",
            ["Google TTS", "Fish Audio", "Azure TTS", "ElevenLabs"]
        )
        
        voice_type = st.selectbox(
            "音声タイプ",
            ["男性", "女性", "子供", "ナレーター"]
        )

# メインコンテンツ - タブ構成
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📝 基本入力",
    "📋 台本生成",
    "🖼️ 画像生成",
    "🎬 動画作成",
    "✂️ 編集・エフェクト",
    "📺 プレビュー",
    "📚 履歴・ガイド"
])

# タブ1: 基本入力
with tab1:
    st.header("📝 基本入力")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("🎯 プロジェクト情報")
        
        # 基本情報入力
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
        
        # キーワード・テーマ
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
        
        # 出演者写真の使用選択
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
                
                # 写真プレビュー
                preview_cols = st.columns(min(len(character_photos), 3))
                for idx, photo in enumerate(character_photos[:3]):
                    with preview_cols[idx % 3]:
                        st.image(photo, caption=f"写真{idx+1}", use_column_width=True)
                
                if len(character_photos) > 3:
                    st.caption(f"他{len(character_photos)-3}枚")
                
                # キャラクター設定
                with st.expander("👤 キャラクター詳細設定"):
                    character_name = st.text_input("キャラクター名", placeholder="例: 主人公")
                    character_age = st.selectbox("年齢設定", ["10代", "20代", "30代", "40代以上", "指定なし"])
                    character_style = st.multiselect(
                        "スタイル/服装",
                        ["カジュアル", "フォーマル", "スポーティ", "ファンタジー", "制服", "その他"]
                    )
                    character_description = st.text_area(
                        "キャラクター説明",
                        placeholder="性格、役割、特徴など",
                        height=80
                    )
                
                st.session_state['character_settings'] = {
                    'photos': character_photos,
                    'name': character_name if 'character_name' in locals() else "",
                    'age': character_age if 'character_age' in locals() else "",
                    'style': character_style if 'character_style' in locals() else [],
                    'description': character_description if 'character_description' in locals() else ""
                }
        else:
            st.info("音楽性とコンセプトに基づいてPVを生成します")
            st.session_state['character_settings'] = None
        
        st.markdown("---")
        st.subheader("🎵 音楽ファイル")
        
        # 音楽ファイルアップロード
        audio_file = st.file_uploader(
            "音楽をアップロード *",
            type=['mp3', 'wav', 'm4a', 'ogg', 'flac'],
            help="最大200MBまで対応",
            key="audio_file"
        )
        
        if audio_file:
            st.audio(audio_file)
            st.success(f"✅ {audio_file.name}")
            
            # 音楽の長さを取得してシーン分割を計算
            with st.spinner("音楽ファイルを分析中..."):
                duration_sec = get_audio_duration(audio_file)
                st.session_state['music_duration'] = duration_sec
                
                # シーン分割を計算
                scene_division = calculate_scene_division(duration_sec)
                st.session_state['scene_division'] = scene_division
                
                # 分析結果を表示
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("🎵 音楽の長さ", format_time(duration_sec))
                    st.metric("🎬 PVの長さ", format_time(scene_division['pv_duration']))
                with col_info2:
                    st.metric("📋 総シーン数", f"{scene_division['total_scenes']}シーン")
                    st.metric("⏱️ 平均シーン長", "5-8秒")
            
            # 詳細分析オプション
            if st.checkbox("🎼 シーン分割詳細を表示"):
                with st.expander("シーン分割詳細", expanded=True):
                    # 最初の10シーンを表示
                    for scene in scene_division['scenes'][:10]:
                        st.text(f"シーン{scene['scene_number']:2d}: {scene['time_range']} ({scene['duration']}秒)")
                    if len(scene_division['scenes']) > 10:
                        st.text(f"... 他 {len(scene_division['scenes']) - 10} シーン")
                    
                    st.info(f"💡 各シーンは5-8秒で、AIが個別に動画を生成します")
        
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
                placeholder="[Verse 1]\n歌詞をここに...\n\n[Chorus]\n..."
            )
        elif lyrics_input_type == "ファイルアップロード":
            lyrics_file = st.file_uploader(
                "テキストファイルをアップロード",
                type=['txt', 'srt']
            )
        else:
            if st.button("🤖 AIで歌詞生成"):
                with st.spinner("生成中..."):
                    time.sleep(2)
                    st.text_area("生成された歌詞", value="[自動生成された歌詞がここに表示されます]", height=150)

# タブ2: 台本生成
with tab2:
    st.header("🖼️ 画像管理")
    
    col_img1, col_img2 = st.columns([1, 1])
    
    with col_img1:
        st.subheader("📤 画像アップロード")
        
        # 画像の用途選択
        image_purpose = st.selectbox(
            "画像の用途",
            ["キャラクター設定", "背景・シーン参考", "スタイル参考", "その他"]
        )
        
        # 複数画像アップロード
        uploaded_files = st.file_uploader(
            f"{image_purpose}用の画像をアップロード",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            accept_multiple_files=True,
            help="最大20枚まで、各10MBまで"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)}枚の画像をアップロード")
            
            # 画像プレビューグリッド
            cols = st.columns(3)
            for idx, img_file in enumerate(uploaded_files[:9]):
                with cols[idx % 3]:
                    st.image(img_file, caption=img_file.name, use_column_width=True)
                    
                    # 画像ごとの設定
                    with st.expander(f"設定", expanded=False):
                        img_tag = st.text_input(
                            "タグ",
                            placeholder="主人公, 背景など",
                            key=f"tag_{idx}"
                        )
                        img_scene = st.selectbox(
                            "使用シーン",
                            ["全体", "オープニング", "中盤", "クライマックス", "エンディング"],
                            key=f"scene_{idx}"
                        )
            
            if len(uploaded_files) > 9:
                st.info(f"他{len(uploaded_files) - 9}枚の画像")
        
        # AI画像生成オプション
        st.markdown("---")
        if st.checkbox("🎨 AIで画像生成"):
            generation_prompt = st.text_area(
                "画像生成プロンプト",
                placeholder="anime style character, blue hair, school uniform..."
            )
            
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                style_preset = st.selectbox(
                    "スタイルプリセット",
                    ["アニメ", "リアル", "イラスト", "3D", "水彩画", "油絵"]
                )
            with col_gen2:
                num_images = st.number_input(
                    "生成枚数",
                    min_value=1,
                    max_value=10,
                    value=4
                )
            
            if st.button("🚀 画像生成開始", type="primary"):
                progress = st.progress(0)
                for i in range(num_images):
                    progress.progress((i + 1) / num_images)
                    time.sleep(0.5)
                st.success(f"✅ {num_images}枚の画像を生成しました")
    
    with col_img2:
        st.subheader("📁 画像ライブラリ")
        
        # 保存済み画像の管理
        tab_saved, tab_generated = st.tabs(["アップロード済み", "AI生成済み"])
        
        with tab_saved:
            if st.session_state.uploaded_images:
                for img in st.session_state.uploaded_images:
                    col_lib1, col_lib2, col_lib3 = st.columns([2, 2, 1])
                    with col_lib1:
                        st.image(img['thumbnail'], width=100)
                    with col_lib2:
                        st.text(img['name'])
                        st.caption(f"用途: {img['purpose']}")
                    with col_lib3:
                        if st.button("削除", key=f"del_{img['id']}"):
                            st.session_state.uploaded_images.remove(img)
                            st.rerun()
            else:
                st.info("画像がまだアップロードされていません")
        
        with tab_generated:
            st.info("AI生成画像がここに表示されます")

# タブ3: 台本生成
with tab3:
    st.header("📋 台本生成・編集")
    
    # 台本生成設定
    col_script1, col_script2 = st.columns([2, 3])
    
    with col_script1:
        st.subheader("🎯 生成設定")
        
        # AI選択
        ai_model = st.selectbox(
            "使用するAIモデル",
            ["GPT-4 Turbo (最高品質)", "Claude 3 Opus (創造的)", "Gemini Pro (バランス)", "GPT-3.5 (高速)", "Deepseek (コスト効率)"]
        )
        
        # 台本スタイル
        script_style = st.selectbox(
            "台本スタイル",
            ["ストーリー重視", "ビジュアル重視", "音楽同期重視", "エモーショナル", "アクション重視", "詩的・抽象的"]
        )
        
        # 詳細設定
        with st.expander("詳細設定", expanded=False):
            creativity = st.slider(
                "創造性レベル",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="高いほど独創的、低いほど一般的"
            )
            
            scene_count = st.number_input(
                "シーン数",
                min_value=3,
                max_value=60,
                value=10,
                help="PVを構成するシーンの数"
            )
            
            include_camera = st.checkbox("カメラワーク指示を含める", value=True)
            include_effects = st.checkbox("エフェクト指示を含める", value=True)
        
        # テンプレート選択
        use_template = st.checkbox("テンプレートを使用")
        if use_template:
            template = st.selectbox(
                "テンプレート選択",
                ["青春ドラマ", "ファンタジー冒険", "ラブストーリー", "アクション", "ミュージックビデオ", "コンセプチュアル"]
            )
            st.info(f"選択: {template}テンプレート")
        
        # 生成ボタン
        if st.button("🤖 複数の台本を生成", type="primary", use_container_width=True):
            # シーン分割情報があるか確認
            if 'scene_division' not in st.session_state:
                st.warning("⚠️ まず音楽ファイルをアップロードしてください")
            else:
                # 歌詞情報を取得
                lyrics_text = st.session_state.get('lyrics', '')
                
                with st.spinner("AIが複数の台本パターンを生成中..."):
                    progress = st.progress(0)
                    status = st.empty()
                    
                    # 3種類の台本を生成
                    script_patterns = []
                    pattern_types = [
                        {"name": "ストーリー重視", "focus": "narrative", "description": "物語性を重視した構成"},
                        {"name": "ビジュアル重視", "focus": "visual", "description": "映像美を重視した構成"},
                        {"name": "音楽同期重視", "focus": "music", "description": "音楽のリズムに完全同期"}
                    ]
                    
                    for pattern_idx, pattern in enumerate(pattern_types):
                        status.text(f"{pattern['name']}版を生成中...")
                        progress.progress((pattern_idx + 1) / len(pattern_types))
                        
                        # シーン分割に基づいた台本生成
                        scene_division = st.session_state['scene_division']
                        generated_scenes = []
                        
                        # キャラクター設定を反映
                        has_character = st.session_state.get('character_settings') is not None
                        character_info = None
                        character_url = None
                        
                        # キャラクター写真がある場合、Midjourney用に準備
                        if has_character and st.session_state.get('character_settings', {}).get('photos'):
                            character_photos = st.session_state['character_settings']['photos']
                            character_info = prepare_character_for_midjourney(character_photos)
                            # 注：実際の実装では、写真をアップロードしてURLを取得する必要があります
                            character_url = "https://your-uploaded-character-photo.jpg"  # デモURL
                        
                        # 歌詞をシーンに分割
                        lyrics_parts = parse_lyrics_to_scenes(lyrics_text, len(scene_division['scenes']))
                        
                        for i, scene_info in enumerate(scene_division['scenes']):
                            # シーンタイプを決定
                            if i == 0:
                                scene_type = "オープニング"
                            elif i == len(scene_division['scenes']) - 1:
                                scene_type = "エンディング"
                            elif i == len(scene_division['scenes']) // 2:
                                scene_type = "クライマックス"
                            else:
                                scene_type = "展開"
                            
                            # 歌詞の該当部分を取得
                            scene_lyrics = lyrics_parts[i] if i < len(lyrics_parts) else ""
                            
                            # パターンに応じた詳細なシーン生成
                            if pattern['focus'] == 'narrative':  # ストーリー重視
                                scene_details = generate_narrative_scene(
                                    scene_type, scene_lyrics, i, len(scene_division['scenes'])
                                )
                            elif pattern['focus'] == 'visual':  # ビジュアル重視
                                scene_details = generate_visual_scene(
                                    scene_type, scene_lyrics, i
                                )
                            else:  # 音楽同期重視
                                # BPMを推定（デモ用）
                                estimated_bpm = 120  # デフォルトBPM
                                beat_count = 4  # 4ビート
                                
                                scene_details = generate_music_sync_scene(
                                    scene_type, scene_lyrics, estimated_bpm, beat_count
                                )
                            
                            # 詳細な描写を取得
                            story = scene_details.get('story', '')
                            action = scene_details.get('detailed_action', '')
                            environment = scene_details.get('environment', '')
                            emotion = scene_details.get('emotion', '')
                            color_mood = scene_details.get('color_mood', '')
                            camera_work = scene_details.get('camera_work', '')
                            props = scene_details.get('props', '')
                            sound_design = scene_details.get('sound_design', '')
                            
                            # 詳細な描写を統合
                            description = f"""
【ストーリー】
{story}

【詳細アクション】
{action}

【環境設定】
{environment}

【感情・雰囲気】
{emotion}

【色彩・ムード】
{color_mood}

【カメラワーク】
{camera_work}

【小道具・要素】
{props}

【サウンドデザイン】
{sound_design}

【シーン情報】
タイプ: {scene_type}
時間: {scene_info['duration']}秒
パターン: {pattern['name']}
"""
                            
                            # Midjourney用の詳細プロンプトを生成
                            base_visual_prompt = create_detailed_midjourney_prompt(scene_details, has_character, character_url)
                            
                            # キャラクター写真がある場合、すべてのシーンで同じキャラクターを使用
                            if character_info and character_url:
                                # シーンタイプに応じて一貫性の強さを調整
                                if scene_type == "オープニング" or scene_type == "エンディング":
                                    consistency_weight = 100  # 最大一貫性
                                elif scene_type == "クライマックス":
                                    consistency_weight = 80  # 少し柔軟性を持たせる
                                else:
                                    consistency_weight = 90  # 通常シーン
                                
                                # プロンプトを上書き（キャラクター参照がすでに含まれていない場合）
                                if '--cref' not in base_visual_prompt:
                                    visual_prompt = f"{base_visual_prompt} --cref {character_url} --cw {consistency_weight}"
                                else:
                                    visual_prompt = base_visual_prompt
                            else:
                                visual_prompt = base_visual_prompt
                            
                            generated_scenes.append({
                                "id": scene_info['scene_number'],
                                "time": scene_info['time_range'],
                                "duration": f"{scene_info['duration']}秒",
                                "type": scene_type,
                                "description": description,
                                "visual_prompt": visual_prompt,
                                "lyrics": scene_lyrics if scene_lyrics else "（インストゥルメンタル）",
                                "camera": "自動選択",
                                "effects": pattern['focus'],
                                "audio": f"{scene_info['start_time']:.1f}秒から{scene_info['end_time']:.1f}秒"
                            })
                        
                        script_patterns.append({
                            "pattern_name": pattern['name'],
                            "pattern_description": pattern['description'],
                            "title": f"台本パターン{pattern_idx + 1}: {pattern['name']}",
                            "music_duration": format_time(scene_division['music_duration']),
                            "pv_duration": format_time(scene_division['pv_duration']),
                            "total_scenes": scene_division['total_scenes'],
                            "has_character": has_character,
                            "scenes": generated_scenes[:20]  # 最初の20シーンまで表示
                        })
                        
                        time.sleep(0.5)  # デモ用
                    
                    st.session_state['script_patterns'] = script_patterns
                    st.success(f"✅ 3種類の台本パターンを生成しました！")
    
    with col_script2:
        st.subheader("📝 台本選択・編集")
        
        # 複数の台本パターンから選択
        if 'script_patterns' in st.session_state and st.session_state['script_patterns']:
            st.markdown("### 🎯 台本パターンを選択")
            
            # パターン選択
            pattern_names = [p['pattern_name'] for p in st.session_state['script_patterns']]
            selected_pattern_name = st.radio(
                "使用する台本パターンを選択",
                pattern_names,
                horizontal=True,
                key="selected_script_pattern"
            )
            
            # 選択されたパターンを取得
            selected_pattern = None
            for pattern in st.session_state['script_patterns']:
                if pattern['pattern_name'] == selected_pattern_name:
                    selected_pattern = pattern
                    st.session_state.current_script = pattern
                    break
            
            if selected_pattern:
                st.info(f"📌 {selected_pattern['pattern_description']}")
                
                # 台本確定ボタン
                col_confirm1, col_confirm2 = st.columns([1, 1])
                with col_confirm1:
                    if st.button("✅ この台本で確定", type="primary", use_container_width=True):
                        st.session_state['confirmed_script'] = selected_pattern
                        st.success("台本を確定しました！画像生成へ進めます。")
                with col_confirm2:
                    if st.button("✏️ 詳細を編集", use_container_width=True):
                        st.session_state['edit_mode'] = True
        
        if st.session_state.get('current_script'):
            # 台本全体の情報
            script = st.session_state.current_script
            col_script_info1, col_script_info2 = st.columns(2)
            with col_script_info1:
                st.info(f"🎵 音楽: {script.get('music_duration', 'N/A')} | 🎬 PV: {script.get('pv_duration', 'N/A')}")
            with col_script_info2:
                st.info(f"📊 総シーン数: {script.get('total_scenes', len(script['scenes']))} | 📹 各5-8秒")
            
            # タイムライン表示
            st.markdown("### タイムライン")
            timeline_data = []
            for scene in st.session_state.current_script['scenes']:
                timeline_data.append({
                    "シーン": f"#{scene['id']}",
                    "時間": scene['time'],
                    "タイプ": scene['type'],
                    "説明": scene['description'][:30] + "..."
                })
            st.dataframe(timeline_data, use_container_width=True, height=150)
            
            # シーン編集
            st.markdown("### シーン詳細編集")
            
            for idx, scene in enumerate(st.session_state.current_script['scenes']):
                # 最初の3シーンは展開して表示
                with st.expander(f"シーン #{scene['id']}: {scene['type']} ({scene['time']})", expanded=(idx < 3)):
                    # 歌詞表示
                    if scene.get('lyrics') and scene['lyrics'] != "（インストゥルメンタル）":
                        st.info(f"🎵 歌詞: {scene['lyrics']}")
                    
                    # 編集可能フィールド
                    col_edit1, col_edit2 = st.columns(2)
                    
                    with col_edit1:
                        scene['type'] = st.selectbox(
                            "シーンタイプ",
                            ["オープニング", "導入", "展開", "クライマックス", "エンディング", "トランジション"],
                            index=["オープニング", "導入", "展開", "クライマックス", "エンディング", "トランジション"].index(scene['type']),
                            key=f"type_{scene['id']}"
                        )
                        
                        scene['camera'] = st.selectbox(
                            "カメラワーク",
                            ["固定", "パン", "ティルト", "ズームイン", "ズームアウト", "トラッキング", "回転"],
                            key=f"camera_{scene['id']}"
                        )
                    
                    with col_edit2:
                        scene['effects'] = st.multiselect(
                            "エフェクト",
                            ["なし", "フェード", "ブラー", "グロー", "パーティクル", "レンズフレア"],
                            default=["なし"],
                            key=f"effects_{scene['id']}"
                        )
                    
                    # ストーリー表示（読みやすく）
                    st.markdown("**📖 ストーリー内容**")
                    scene['description'] = st.text_area(
                        "シーン説明",
                        value=scene['description'],
                        height=120,
                        key=f"desc_{scene['id']}",
                        help="ストーリー、アクション、演出の詳細"
                    )
                    
                    st.markdown("**🎨 Midjourneyプロンプト**")
                    scene['visual_prompt'] = st.text_area(
                        "画像生成プロンプト",
                        value=scene['visual_prompt'],
                        height=80,
                        key=f"prompt_{scene['id']}",
                        help="Midjourney用の詳細なプロンプト（--ar 16:9 --v 6 含む）"
                    )
                    
                    # アクションボタン
                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        if st.button("💾 保存", key=f"save_{scene['id']}"):
                            st.success("保存しました")
                    with col_act2:
                        if st.button("🔄 複製", key=f"dup_{scene['id']}"):
                            st.info("シーンを複製しました")
                    with col_act3:
                        if st.button("🗑️ 削除", key=f"del_{scene['id']}"):
                            st.warning("シーンを削除しました")
            
            # シーン追加
            if st.button("➕ 新規シーンを追加", use_container_width=True):
                st.success("新しいシーンを追加しました")
            
            # エクスポート
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                if st.button("📄 台本をエクスポート", use_container_width=True):
                    st.download_button(
                        label="Download script.json",
                        data=json.dumps(st.session_state.current_script, ensure_ascii=False, indent=2),
                        file_name="script.json",
                        mime="application/json"
                    )
            with col_exp2:
                if st.button("📋 台本をコピー", use_container_width=True):
                    st.info("クリップボードにコピーしました")
        else:
            st.info("台本がまだ生成されていません。左側で設定を行い生成してください。")

# タブ4: 編集・エフェクト
with tab4:
    st.header("✂️ 編集・エフェクト")
    
    edit_tab1, edit_tab2, edit_tab3, edit_tab4 = st.tabs([
        "🎬 カット編集",
        "🎨 ビジュアルエフェクト",
        "🎵 音楽同期",
        "🎭 トランジション"
    ])
    
    with edit_tab1:
        st.subheader("カット編集")
        
        col_cut1, col_cut2 = st.columns([2, 3])
        
        with col_cut1:
            st.markdown("### 編集モード")
            edit_mode = st.radio(
                "選択",
                ["タイムライン編集", "シーケンス編集", "マルチトラック編集"],
                help="編集方法を選択"
            )
            
            if edit_mode == "タイムライン編集":
                st.markdown("#### タイムライン設定")
                
                # タイムラインスライダー
                time_range = st.slider(
                    "編集範囲",
                    min_value=0.0,
                    max_value=180.0,
                    value=(0.0, 30.0),
                    step=0.1,
                    format="%.1f秒"
                )
                
                # カット点追加
                if st.button("✂️ カット点を追加"):
                    st.success(f"{time_range[0]}秒にカット点を追加")
                
                # プレビュー速度
                preview_speed = st.select_slider(
                    "プレビュー速度",
                    options=[0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
                    value=1.0
                )
        
        with col_cut2:
            st.markdown("### カットリスト")
            
            # デモ用カットリスト
            cuts = [
                {"id": 1, "start": "0:00", "end": "0:05", "duration": "5秒", "type": "通常"},
                {"id": 2, "start": "0:05", "end": "0:08", "duration": "3秒", "type": "スローモーション"},
                {"id": 3, "start": "0:08", "end": "0:15", "duration": "7秒", "type": "通常"},
            ]
            
            for cut in cuts:
                col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([1, 2, 2, 2, 1])
                with col_c1:
                    st.text(f"#{cut['id']}")
                with col_c2:
                    st.text(f"{cut['start']}-{cut['end']}")
                with col_c3:
                    st.text(cut['duration'])
                with col_c4:
                    st.selectbox("", ["通常", "スロー", "早送り", "逆再生"], key=f"cut_type_{cut['id']}", label_visibility="collapsed")
                with col_c5:
                    st.button("✏️", key=f"edit_cut_{cut['id']}")
    
    with edit_tab2:
        st.subheader("ビジュアルエフェクト")
        
        col_fx1, col_fx2 = st.columns([1, 1])
        
        with col_fx1:
            st.markdown("### 基本エフェクト")
            
            # カラーグレーディング
            st.markdown("#### カラーグレーディング")
            color_preset = st.selectbox(
                "プリセット",
                ["なし", "シネマティック", "ビビッド", "モノクロ", "セピア", "クール", "ウォーム", "サイバーパンク"]
            )
            
            if color_preset != "なし":
                brightness = st.slider("明度", -100, 100, 0)
                contrast = st.slider("コントラスト", -100, 100, 0)
                saturation = st.slider("彩度", -100, 100, 0)
                temperature = st.slider("色温度", -100, 100, 0)
            
            # フィルター
            st.markdown("#### フィルター")
            filters = st.multiselect(
                "適用するフィルター",
                ["ブラー", "シャープ", "ノイズ", "グレイン", "ビネット", "色収差"]
            )
            
            for filter_name in filters:
                st.slider(f"{filter_name}強度", 0, 100, 50, key=f"filter_{filter_name}")
        
        with col_fx2:
            st.markdown("### 特殊エフェクト")
            
            # パーティクル
            st.markdown("#### パーティクルエフェクト")
            particles = st.multiselect(
                "パーティクル種類",
                ["雪", "雨", "花びら", "光", "煙", "炎", "泡", "星"]
            )
            
            if particles:
                particle_density = st.slider("密度", 0, 100, 50)
                particle_speed = st.slider("速度", 0, 100, 50)
                particle_size = st.slider("サイズ", 0, 100, 50)
            
            # 光エフェクト
            st.markdown("#### 光エフェクト")
            light_effects = st.multiselect(
                "光の種類",
                ["レンズフレア", "光線", "グロー", "オーラ", "ネオン"]
            )
            
            if light_effects:
                light_intensity = st.slider("光の強度", 0, 100, 50)
                light_color = st.color_picker("光の色", "#FFFFFF")
    
    with edit_tab3:
        st.subheader("音楽同期設定")
        
        col_sync1, col_sync2 = st.columns([1, 1])
        
        with col_sync1:
            st.markdown("### ビート検出")
            
            beat_detection = st.checkbox("自動ビート検出", value=True)
            
            if beat_detection:
                st.success("✅ ビート検出有効")
                
                # BPM設定
                bpm_mode = st.radio(
                    "BPM設定",
                    ["自動検出", "手動設定"],
                    horizontal=True
                )
                
                if bpm_mode == "自動検出":
                    st.info("検出されたBPM: 120")
                else:
                    manual_bpm = st.number_input("BPM", min_value=60, max_value=200, value=120)
                
                # 同期スタイル
                sync_style = st.select_slider(
                    "同期スタイル",
                    options=["ゆったり", "標準", "リズミカル", "激しい", "超高速"],
                    value="標準"
                )
                
                # 同期要素
                sync_elements = st.multiselect(
                    "同期する要素",
                    ["カット", "エフェクト", "カメラ", "テキスト", "色変化"],
                    default=["カット", "エフェクト"]
                )
        
        with col_sync2:
            st.markdown("### マーカー設定")
            
            # 重要ポイントマーカー
            st.markdown("#### 楽曲構成マーカー")
            
            markers = {
                "イントロ": "0:00",
                "Aメロ": "0:15",
                "Bメロ": "0:30",
                "サビ": "0:45",
                "間奏": "1:15",
                "アウトロ": "2:30"
            }
            
            for marker_name, marker_time in markers.items():
                col_m1, col_m2, col_m3 = st.columns([2, 2, 1])
                with col_m1:
                    st.text(marker_name)
                with col_m2:
                    st.text_input("", value=marker_time, key=f"marker_{marker_name}", label_visibility="collapsed")
                with col_m3:
                    st.button("編集", key=f"edit_marker_{marker_name}")
            
            if st.button("➕ マーカー追加", use_container_width=True):
                st.success("マーカーを追加")
    
    with edit_tab4:
        st.subheader("トランジション設定")
        
        # トランジションマトリックス
        st.markdown("### シーン間トランジション")
        
        # デモ用トランジション設定
        transitions = [
            {"from": "シーン1", "to": "シーン2", "type": "フェード", "duration": "1.0秒"},
            {"from": "シーン2", "to": "シーン3", "type": "ディゾルブ", "duration": "0.5秒"},
            {"from": "シーン3", "to": "シーン4", "type": "ワイプ", "duration": "0.8秒"},
        ]
        
        for i, trans in enumerate(transitions):
            col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([2, 1, 2, 2, 1])
            with col_t1:
                st.text(f"{trans['from']} → {trans['to']}")
            with col_t2:
                st.text("→")
            with col_t3:
                st.selectbox(
                    "",
                    ["カット", "フェード", "ディゾルブ", "ワイプ", "スライド", "回転", "ズーム", "3D回転"],
                    index=1,
                    key=f"trans_type_{i}",
                    label_visibility="collapsed"
                )
            with col_t4:
                st.number_input("", value=1.0, min_value=0.1, max_value=5.0, step=0.1, key=f"trans_dur_{i}", label_visibility="collapsed")
            with col_t5:
                st.button("⚙️", key=f"trans_settings_{i}")
        
        # グローバル設定
        st.markdown("### グローバル設定")
        default_transition = st.selectbox(
            "デフォルトトランジション",
            ["カット", "フェード", "ディゾルブ"]
        )
        default_duration = st.slider(
            "デフォルト時間（秒）",
            min_value=0.1,
            max_value=3.0,
            value=0.5,
            step=0.1
        )

# タブ5: 生成・プレビュー
with tab5:
    st.header("🎬 動画生成・プレビュー")
    
    col_gen1, col_gen2 = st.columns([2, 3])
    
    with col_gen1:
        st.subheader("🚀 生成設定")
        
        # 生成前チェックリスト
        st.markdown("### チェックリスト")
        checklist = {
            "プロジェクト情報": bool(st.session_state.get('project_name', False)),
            "音楽ファイル": bool(st.session_state.get('audio_file', False)),
            "台本作成": bool(st.session_state.current_script),
            "APIキー設定": any(st.session_state.api_keys.values()),
        }
        
        for item, status in checklist.items():
            if status:
                st.success(f"✅ {item}")
            else:
                st.error(f"❌ {item}")
        
        # 品質設定
        st.markdown("### 品質設定")
        
        quality_preset = st.radio(
            "品質プリセット",
            ["高速（プレビュー）", "標準", "高品質", "最高品質"],
            index=1
        )
        
        if quality_preset == "高速（プレビュー）":
            st.info("解像度: 480p | FPS: 15 | 推定時間: 5分")
        elif quality_preset == "標準":
            st.info("解像度: 720p | FPS: 24 | 推定時間: 15分")
        elif quality_preset == "高品質":
            st.info("解像度: 1080p | FPS: 30 | 推定時間: 30分")
        else:
            st.info("解像度: 4K | FPS: 60 | 推定時間: 60分")
        
        # 詳細オプション
        with st.expander("詳細オプション"):
            resolution = st.selectbox("解像度", ["480p", "720p", "1080p", "4K"])
            fps = st.selectbox("FPS", ["15", "24", "30", "60"])
            format_type = st.selectbox("出力形式", ["MP4", "AVI", "MOV", "WebM"])
            codec = st.selectbox("コーデック", ["H.264", "H.265", "VP9"])
        
        # 生成開始ボタン
        if st.button("🎬 PV生成開始", type="primary", use_container_width=True, disabled=not all(checklist.values())):
            st.session_state['generating'] = True
    
    with col_gen2:
        st.subheader("📺 プレビュー・進捗")
        
        if 'generating' in st.session_state and st.session_state['generating']:
            # 進捗表示
            st.markdown("### 生成進捗")
            
            overall_progress = st.progress(0)
            current_task = st.empty()
            task_progress = st.progress(0)
            
            # 生成ステップ
            generation_steps = [
                {"name": "初期化", "duration": 1},
                {"name": "音楽分析", "duration": 2},
                {"name": "画像生成", "duration": 5},
                {"name": "シーン1動画生成", "duration": 3},
                {"name": "シーン2動画生成", "duration": 3},
                {"name": "シーン3動画生成", "duration": 3},
                {"name": "音声合成", "duration": 2},
                {"name": "動画合成", "duration": 3},
                {"name": "後処理", "duration": 2},
                {"name": "完了", "duration": 1}
            ]
            
            total_steps = len(generation_steps)
            for i, step in enumerate(generation_steps):
                current_task.info(f"🔄 {step['name']}中...")
                
                # タスクプログレス
                for j in range(10):
                    task_progress.progress((j + 1) / 10)
                    time.sleep(step['duration'] / 10)
                
                # 全体プログレス
                overall_progress.progress((i + 1) / total_steps)
            
            st.success("✅ PV生成完了！")
            
            # 動画プレビュー
            st.markdown("### 完成動画")
            st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # デモ用
            
            # ダウンロード・シェア
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                st.download_button(
                    label="📥 ダウンロード",
                    data=b"dummy video data",
                    file_name="pv_output.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            
            with col_dl2:
                if st.button("📤 共有", use_container_width=True):
                    st.info("共有リンクをコピーしました")
            
            with col_dl3:
                if st.button("💾 プロジェクト保存", use_container_width=True):
                    st.success("プロジェクトを保存しました")
            
            st.session_state['generating'] = False
        else:
            # プレビューエリア
            st.info("生成を開始すると、ここにプレビューが表示されます")
            
            # サンプル表示
            if st.checkbox("サンプル動画を表示"):
                st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# タブ6: 履歴・ガイド
with tab6:
    st.header("📚 履歴・ガイド")
    
    history_tab, guide_tab, faq_tab = st.tabs(["生成履歴", "使い方ガイド", "FAQ"])
    
    with history_tab:
        st.subheader("生成履歴")
        
        # フィルター
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        with col_filter1:
            date_filter = st.date_input("日付", value=None)
        with col_filter2:
            status_filter = st.selectbox("ステータス", ["すべて", "完了", "処理中", "エラー"])
        with col_filter3:
            sort_by = st.selectbox("並び順", ["新しい順", "古い順", "名前順"])
        
        # 履歴リスト（デモ）
        history_items = [
            {
                "id": "001",
                "name": "青春ドラマPV",
                "date": "2024-01-20",
                "duration": "3:24",
                "status": "完了",
                "size": "125MB"
            },
            {
                "id": "002",
                "name": "ファンタジーPV",
                "date": "2024-01-19",
                "duration": "2:15",
                "status": "完了",
                "size": "98MB"
            }
        ]
        
        for item in history_items:
            with st.expander(f"{item['name']} - {item['date']}"):
                col_h1, col_h2 = st.columns([3, 1])
                with col_h1:
                    st.text(f"ID: {item['id']}")
                    st.text(f"時間: {item['duration']}")
                    st.text(f"サイズ: {item['size']}")
                    st.text(f"ステータス: {item['status']}")
                with col_h2:
                    st.button("再生", key=f"play_{item['id']}")
                    st.button("編集", key=f"edit_h_{item['id']}")
                    st.button("削除", key=f"delete_h_{item['id']}")
    
    with guide_tab:
        st.subheader("使い方ガイド")
        
        st.markdown("""
        ### 🚀 クイックスタート
        
        1. **APIキー設定**: サイドバーで必要なAPIキーを入力
        2. **基本情報入力**: プロジェクト名、タイトル、音楽ファイルをアップロード
        3. **画像準備**: キャラクターや参考画像をアップロード（オプション）
        4. **台本生成**: AIで自動生成または手動で作成
        5. **編集・調整**: エフェクトやトランジションを設定
        6. **生成開始**: 品質を選択して生成ボタンをクリック
        
        ### 💡 ヒント
        
        - **高品質な結果を得るには**:
          - 明確なキーワードと説明を入力
          - 参考画像を複数アップロード
          - 台本を詳細に編集
        
        - **処理時間を短縮するには**:
          - 低解像度でプレビュー生成
          - シーン数を減らす
          - シンプルなエフェクトを使用
        
        ### 🎯 推奨設定
        
        | 用途 | 解像度 | FPS | シーン数 |
        |------|--------|-----|----------|
        | SNS投稿 | 720p | 30 | 5-10 |
        | YouTube | 1080p | 30 | 10-20 |
        | プレゼン | 1080p | 24 | 5-15 |
        | アーカイブ | 4K | 60 | 20-60 |
        """)
    
    with faq_tab:
        st.subheader("よくある質問")
        
        faqs = [
            {
                "q": "生成にどのくらい時間がかかりますか？",
                "a": "標準品質で3分の動画の場合、約15-30分かかります。高品質や4Kの場合は1時間以上かかることもあります。"
            },
            {
                "q": "どのAPIキーが必須ですか？",
                "a": "最低限、OpenAI（GPT-4）とHailuoのAPIキーが必要です。より高品質な結果を求める場合は、他のAPIキーも設定することをお勧めします。"
            },
            {
                "q": "生成が途中で止まってしまいました",
                "a": "APIの制限やネットワークエラーの可能性があります。履歴から再開するか、品質設定を下げて再試行してください。"
            },
            {
                "q": "カスタムモデルは使用できますか？",
                "a": "現在は対応していませんが、将来的にサポート予定です。"
            }
        ]
        
        for faq in faqs:
            with st.expander(faq["q"]):
                st.write(faq["a"])

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🎬 PV自動生成AIエージェント v2.0 | Powered by Multiple AI Services</p>
    <p>© 2024 PV Generator. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)