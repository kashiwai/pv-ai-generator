"""
画像生成と動画作成のワークフロー実装
"""

import streamlit as st
import time
from piapi_integration import generate_images_with_piapi, create_pv_with_piapi

def render_image_generation_tab():
    """画像生成タブの内容を表示"""
    st.header("🖼️ シーンごとの画像生成")
    
    # 台本が確定しているか確認
    if 'confirmed_script' not in st.session_state:
        st.warning("⚠️ まず台本を確定してください（台本生成タブで）")
        return
    
    script = st.session_state['confirmed_script']
    has_character = script.get('has_character', False)
    character_photos = st.session_state.get('character_settings', {}).get('photos') if has_character else None
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("⚙️ 画像生成設定")
        
        # スタイル設定
        st.markdown("### 🎨 ビジュアルスタイル")
        
        if has_character:
            st.success("✅ 出演者の写真を使用")
            consistency_level = st.slider(
                "一貫性レベル",
                min_value=0.5,
                max_value=1.0,
                value=0.8,
                help="出演者の見た目の一貫性"
            )
        else:
            visual_style = st.selectbox(
                "ビジュアルスタイル",
                ["リアリスティック", "アニメ", "イラスト", "3DCG", "アート", "シネマティック"]
            )
        
        # カラーパレット
        color_palette = st.selectbox(
            "カラーパレット",
            ["自動（曲調に合わせる）", "暖色系", "寒色系", "モノクロ", "ビビッド", "パステル"]
        )
        
        # 画質設定
        image_quality = st.select_slider(
            "画質",
            options=["標準", "高品質", "最高品質"],
            value="高品質"
        )
        
        st.markdown("---")
        
        # 生成開始ボタン
        if st.button("🚀 画像生成を開始", type="primary", use_container_width=True):
            st.session_state['generating_images'] = True
            st.session_state['image_settings'] = {
                'consistency_level': consistency_level if has_character else None,
                'visual_style': visual_style if not has_character else None,
                'color_palette': color_palette,
                'image_quality': image_quality
            }
    
    with col2:
        st.subheader("📸 生成状況")
        
        if st.session_state.get('generating_images'):
            # PIAPIを使用した実際の画像生成
            if st.session_state.api_keys.get('piapi'):
                # PIAPI統合での画像生成
                generated_images = generate_images_with_piapi(script, character_photos)
                
                # プレビュー表示
                if generated_images:
                    st.success(f"✅ {len(generated_images)}枚の画像生成が完了しました！")
                    
                    # 最初の3枚をプレビュー
                    preview_cols = st.columns(3)
                    for i, img in enumerate(generated_images[:3]):
                        with preview_cols[i]:
                            if img.get('result_url'):
                                st.image(img['result_url'], caption=f"シーン {img['scene_id']}")
                            else:
                                st.image("https://via.placeholder.com/200x150", 
                                       caption=f"シーン {img['scene_id']} (生成中)")
            else:
                # デモモード（APIキーなし）
                total_scenes = len(script['scenes'])
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                generated_images = []
                
                for i, scene in enumerate(script['scenes']):
                    status_text.text(f"シーン {scene['id']} を生成中... ({i+1}/{total_scenes})")
                    progress_bar.progress((i + 1) / total_scenes)
                    
                    time.sleep(0.5)
                    
                    generated_images.append({
                        'scene_id': scene['id'],
                        'time': scene['time'],
                        'status': '✅ 完了',
                        'prompt': scene['visual_prompt'],
                        'result_url': None  # デモモード
                    })
                    
                    # プレビュー表示（最新3件）
                    if i < 3:
                        col_preview = st.columns(3)
                        for j, img in enumerate(generated_images[-3:]):
                            with col_preview[j]:
                                st.image("https://via.placeholder.com/200x150", 
                                       caption=f"シーン {img['scene_id']}")
            
            st.session_state['generated_images'] = generated_images
            st.session_state['generating_images'] = False
            
            # 次のステップへ
            if st.button("🎬 動画作成へ進む", type="primary", use_container_width=True):
                st.session_state['ready_for_video'] = True
                st.info("動画作成タブに移動してください")
        
        elif 'generated_images' in st.session_state:
            # 生成済み画像の表示
            st.success("✅ 画像生成完了")
            
            # サムネイル表示
            images = st.session_state['generated_images']
            cols = st.columns(4)
            for i, img in enumerate(images[:8]):
                with cols[i % 4]:
                    st.image("https://via.placeholder.com/150x100", 
                           caption=f"シーン {img['scene_id']}")
            
            if len(images) > 8:
                st.caption(f"他 {len(images) - 8} シーン")
        else:
            st.info("画像生成を開始してください")

def render_video_creation_tab():
    """動画作成タブの内容を表示"""
    st.header("🎬 動画作成")
    
    # 画像が生成されているか確認
    if 'generated_images' not in st.session_state:
        st.warning("⚠️ まず画像を生成してください（画像生成タブで）")
        return
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("🎥 動画生成設定")
        
        # 音楽分析
        st.markdown("### 🎵 音楽分析")
        if st.session_state.get('music_duration'):
            music_genre = st.selectbox(
                "音楽ジャンル（自動検出）",
                ["ポップス", "ロック", "バラード", "ダンス", "ヒップホップ", "その他"],
                help="音楽のジャンルに応じて編集スタイルが変わります"
            )
            
            edit_style = st.selectbox(
                "編集スタイル",
                ["音楽同期（推奨）", "スムーズ", "ダイナミック", "シネマティック", "エモーショナル"]
            )
        
        # トランジション設定
        st.markdown("### 🔄 トランジション")
        transition_type = st.selectbox(
            "基本トランジション",
            ["自動（曲調に合わせる）", "カット", "フェード", "ディゾルブ", "ワイプ"]
        )
        
        transition_speed = st.slider(
            "トランジション速度",
            min_value=0.3,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="秒"
        )
        
        # エフェクト
        st.markdown("### ✨ エフェクト")
        apply_effects = st.multiselect(
            "適用するエフェクト",
            ["カラーグレーディング", "モーションブラー", "光エフェクト", "パーティクル"]
        )
        
        # 出力設定
        st.markdown("### 📤 出力設定")
        output_quality = st.selectbox(
            "出力品質",
            ["720p (HD)", "1080p (Full HD)", "4K"]
        )
        
        output_format = st.selectbox(
            "出力形式",
            ["MP4", "MOV", "AVI"]
        )
        
        st.markdown("---")
        
        # 動画生成開始
        if st.button("🎬 動画生成を開始", type="primary", use_container_width=True):
            st.session_state['generating_video'] = True
            st.session_state['video_settings'] = {
                'music_genre': music_genre if st.session_state.get('music_duration') else None,
                'edit_style': edit_style if st.session_state.get('music_duration') else None,
                'transition_type': transition_type,
                'transition_speed': transition_speed,
                'effects': apply_effects,
                'output_quality': output_quality,
                'output_format': output_format
            }
    
    with col2:
        st.subheader("🎞️ 生成状況")
        
        if st.session_state.get('generating_video'):
            # PIAPIを使用した実際の動画生成
            if st.session_state.api_keys.get('piapi') and st.session_state.get('generated_images'):
                # 音楽情報を準備
                music_info = {
                    'duration': st.session_state.get('music_duration', 180),
                    'url': None  # 実際の実装では音楽ファイルのURLを設定
                }
                
                # 動画生成設定
                settings = st.session_state.get('video_settings', {})
                
                # PIAPI統合での動画生成
                result = create_pv_with_piapi(
                    st.session_state['generated_images'],
                    music_info,
                    settings
                )
                
                if result['status'] == 'success':
                    st.success("✅ PV動画の生成が完了しました！")
                    st.session_state['video_url'] = result.get('video_url')
                else:
                    st.error(f"動画生成エラー: {result.get('message')}")
            else:
                # デモモード（APIキーなし）
                progress = st.progress(0)
                status = st.empty()
                
                steps = [
                    "画像を動画化中...",
                    "音楽と同期中...",
                    "トランジション適用中...",
                    "エフェクト処理中...",
                    "最終レンダリング中..."
                ]
                
                for i, step in enumerate(steps):
                    status.info(f"🔄 {step}")
                    progress.progress((i + 1) / len(steps))
                    time.sleep(1)
                
                st.success("✅ PV動画の生成が完了しました！")
            
            # プレビュー
            if st.session_state.get('video_url'):
                st.video(st.session_state['video_url'])
            else:
                st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # デモ用
            
            # ダウンロード
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 動画をダウンロード",
                    data=b"dummy video data",
                    file_name="generated_pv.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            with col_dl2:
                if st.button("📤 SNSに共有", use_container_width=True):
                    st.info("共有機能は準備中です")
            
            st.session_state['generating_video'] = False
            st.session_state['video_completed'] = True
        
        elif st.session_state.get('video_completed'):
            st.success("✅ 動画生成完了")
            st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # デモ用
        else:
            st.info("動画生成を開始してください")