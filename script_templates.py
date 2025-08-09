"""
台本テンプレート - 詳細な情景描写と生成AI向け指示
"""

from typing import Dict, List, Optional
import random


def generate_narrative_scene(scene_type: str, scene_lyrics: str, scene_num: int, total_scenes: int) -> Dict[str, str]:
    """
    ストーリー重視の詳細なシーン生成
    """
    if scene_type == "オープニング":
        if scene_lyrics:
            return {
                "story": f"【歌詞】{scene_lyrics[:100]}\n【物語の始まり】主人公が日常から非日常へと踏み出す瞬間。朝靄の中、街が目覚める。主人公の部屋、壁には夢を示す写真やポスター。ベッドから起き上がり、窓の外を見つめる。新しい一日への期待と不安が入り混じる表情。",
                "detailed_action": "1. カメラは窓の外から室内へゆっくりとパン\n2. 主人公の寝顔から目覚めるまでをクローズアップ\n3. 起き上がって窓に歩み寄る全身ショット\n4. 窓越しに見える朝日に手をかざす",
                "environment": "早朝5:30、薄暗い部屋、カーテンの隙間から差し込む朝日、静寂の中に時計の音だけが響く",
                "emotion": "期待70%、不安20%、決意10%",
                "color_mood": "青みがかった朝の光、オレンジ色の朝日、全体的に低彩度",
                "camera_work": "スローモーション、手持ちカメラで親密感を演出、浅い被写界深度",
                "props": "目覚まし時計、写真立て、ギター、ノート、コーヒーカップ",
                "sound_design": "環境音：鳥のさえずり、遠くの車の音、時計の秒針"
            }
        else:
            return {
                "story": "無音の世界から音が生まれる瞬間。真っ暗な空間に一筋の光が差し込み、徐々に世界が形作られていく。",
                "detailed_action": "1. 完全な暗闇（3秒）\n2. 中央に小さな光点が現れる\n3. 光が波紋のように広がる\n4. 光の中から主人公のシルエットが浮かび上がる",
                "environment": "抽象的空間から具体的な場所へ変化",
                "emotion": "神秘的、誕生、始まり",
                "color_mood": "黒→深い青→明るい青→白",
                "camera_work": "固定カメラ、超スローモーション",
                "props": "光のパーティクル、霧、水面の反射",
                "sound_design": "完全な無音から徐々に音が生まれる"
            }
    
    elif scene_type == "クライマックス":
        if scene_lyrics and "愛" in scene_lyrics or "love" in scene_lyrics.lower():
            return {
                "story": f"【歌詞】{scene_lyrics[:100]}\n【感情の爆発】すべての感情が最高潮に達する。雨の中、主人公が叫ぶ。これまでの葛藤がすべて解放される瞬間。",
                "detailed_action": "1. 土砂降りの雨の中、主人公が立ち尽くす\n2. 顔を上げて空を見上げる\n3. 両手を広げて雨を受け止める\n4. 叫び声を上げる（無音で口の動きだけ）\n5. 膝をついて泣き崩れる\n6. ゆっくりと立ち上がり、前を向く",
                "environment": "夜の街、土砂降りの雨、街灯の光が雨に反射、誰もいない交差点",
                "emotion": "解放感50%、悲しみ30%、希望20%",
                "color_mood": "青と紫のグラデーション、街灯のオレンジ、雨に濡れた路面の反射",
                "camera_work": "360度回転ショット、超ハイスピード撮影（雨粒が止まって見える）、ローアングルからハイアングルへ",
                "props": "傘（使わずに持っているだけ）、水たまり、街灯、信号機",
                "sound_design": "雨音、雷鳴、心臓の鼓動、呼吸音"
            }
        else:
            return {
                "story": "決断の瞬間。すべてが止まったかのような静寂の中、主人公が一歩を踏み出す。",
                "detailed_action": "1. 崖の端に立つ主人公\n2. 後ろを振り返る\n3. 深呼吸\n4. 目を閉じる\n5. 目を開けて決意の表情\n6. 走り出す",
                "environment": "夕暮れ時の崖、オレンジ色の空、風が強い",
                "emotion": "決意90%、恐怖10%",
                "color_mood": "黄金色の夕日、紫の空、黒いシルエット",
                "camera_work": "ドローンショット、主人公を中心に旋回",
                "props": "なびく髪、服、落ち葉",
                "sound_design": "風の音、心臓の鼓動"
            }
    
    elif scene_type == "エンディング":
        return {
            "story": f"【歌詞】{scene_lyrics[:50] if scene_lyrics else '静寂'}\n【物語の終わりと新たな始まり】すべてが終わり、そして始まる。主人公は振り返らずに歩いていく。",
            "detailed_action": "1. 主人公の後ろ姿\n2. ゆっくりと歩き始める\n3. 徐々に歩調が速くなる\n4. 立ち止まって空を見上げる\n5. 微笑む横顔\n6. また歩き始める（カメラは止まる）\n7. 主人公が小さくなっていく",
            "environment": "朝の海岸線、波の音、カモメの鳴き声、地平線に昇る太陽",
            "emotion": "達成感40%、寂しさ20%、希望40%",
            "color_mood": "パステルカラーの空、金色の砂浜、青い海",
            "camera_work": "長回し、固定カメラ、最後はドローンで上昇",
            "props": "足跡、打ち寄せる波、飛ぶカモメ",
            "sound_design": "波の音が徐々に小さくなる"
        }
    
    else:  # 展開シーン
        scene_variations = [
            {
                "story": f"【歌詞】{scene_lyrics[:50] if scene_lyrics else '間奏'}\n【日常の中の非日常】街を歩く主人公。ふと立ち止まり、空を見上げる。雲が流れ、時間が加速する。",
                "detailed_action": "1. 雑踏を歩く主人公\n2. 突然立ち止まる\n3. 周りの人々がスローモーションに\n4. 主人公だけ通常速度\n5. 空を見上げる\n6. 雲がタイムラプスで流れる",
                "environment": "昼下がりの繁華街、人々の往来、ビルの谷間",
                "emotion": "孤独感60%、自由40%",
                "color_mood": "都市の無機質なグレー、空の青、主人公の服だけ鮮やか",
                "camera_work": "ブレットタイム効果、タイムラプスとスローモーションの組み合わせ",
                "props": "行き交う人々、ビルの反射、飛ぶ鳥",
                "sound_design": "都市の喧騒が徐々にフェードアウト"
            },
            {
                "story": f"【歌詞】{scene_lyrics[:50] if scene_lyrics else '間奏'}\n【記憶の断片】過去の思い出がフラッシュバックする。写真が風に舞い、思い出が蘇る。",
                "detailed_action": "1. 古いアルバムを開く\n2. 写真が風で飛ばされる\n3. 空中で写真が動き出す\n4. 過去の場面が現実と重なる\n5. 主人公が手を伸ばす\n6. 写真が手をすり抜ける",
                "environment": "古い部屋、埃の舞う光、夕方の斜光",
                "emotion": "懐かしさ70%、切なさ30%",
                "color_mood": "セピア調からカラーへの変化",
                "camera_work": "マクロレンズ、フォーカスシフト",
                "props": "古い写真、アルバム、埃、カーテン",
                "sound_design": "古い時計の音、ページをめくる音"
            }
        ]
        return scene_variations[scene_num % len(scene_variations)]


def generate_visual_scene(scene_type: str, scene_lyrics: str, scene_num: int) -> Dict[str, str]:
    """
    ビジュアル重視の美的なシーン生成
    """
    if scene_type == "オープニング":
        return {
            "story": "視覚的インパクトで始まる。万華鏡のような色彩の爆発",
            "detailed_action": "1. 真っ白な画面\n2. 中心から色が染み出す\n3. 色が螺旋を描いて広がる\n4. 幾何学模様を形成\n5. 模様が人の形になる",
            "environment": "抽象空間、無重力",
            "emotion": "驚き、美しさ",
            "color_mood": "虹色グラデーション、ネオンカラー",
            "camera_work": "カレイドスコープ効果、対称構図",
            "props": "光の粒子、プリズム、水晶",
            "sound_design": "シンセサイザー、電子音"
        }
    
    elif scene_type == "クライマックス":
        return {
            "story": "色彩と形の爆発。すべての要素が渦を巻いて中心に収束",
            "detailed_action": "1. 無数の光の線が画面を横切る\n2. 線が絡み合い渦を作る\n3. 渦の中心が輝く\n4. 爆発\n5. 粒子が舞う\n6. 再構成",
            "environment": "デジタル空間、サイバースペース",
            "emotion": "エクスタシー",
            "color_mood": "ネオンピンク、エレクトリックブルー、ライムグリーン",
            "camera_work": "急速ズーム、回転、ストロボ効果",
            "props": "ホログラム、レーザー、デジタルノイズ",
            "sound_design": "電子ビート、グリッチ音"
        }
    
    elif scene_type == "エンディング":
        return {
            "story": "すべての色が白に収束。そして新たな色が生まれる",
            "detailed_action": "1. カラフルな世界\n2. 色が薄れていく\n3. 白になる\n4. 中心に小さな色点\n5. その色が脈動\n6. フェードアウト",
            "environment": "白い無限空間",
            "emotion": "浄化、再生",
            "color_mood": "白へのグラデーション",
            "camera_work": "超スローズームアウト",
            "props": "光のオーブ",
            "sound_design": "ホワイトノイズから無音へ"
        }
    
    else:
        visual_variations = [
            {
                "story": "液体と光の融合。水面に落ちる絵の具が広がる",
                "detailed_action": "1. 静かな水面\n2. 一滴の絵の具が落ちる\n3. 波紋と色が広がる\n4. 複数の色が混ざる\n5. 渦を巻く\n6. 新しい模様",
                "environment": "マクロ撮影空間",
                "emotion": "流動性、変化",
                "color_mood": "水彩画のような透明感",
                "camera_work": "超マクロレンズ、スローモーション",
                "props": "水、インク、油、光",
                "sound_design": "水滴音、泡の音"
            },
            {
                "story": "フラクタル構造の探索。無限に続く幾何学模様",
                "detailed_action": "1. 三角形\n2. 分裂して複数の三角形\n3. さらに分裂\n4. フラクタル構造\n5. ズームイン\n6. 新たなパターン",
                "environment": "数学的空間",
                "emotion": "無限、精密さ",
                "color_mood": "モノクロからカラーへ",
                "camera_work": "無限ズーム",
                "props": "幾何学図形、フラクタル",
                "sound_design": "数学的リズム"
            }
        ]
        return visual_variations[scene_num % len(visual_variations)]


def generate_music_sync_scene(scene_type: str, scene_lyrics: str, bpm: int, beat_count: int) -> Dict[str, str]:
    """
    音楽同期重視のリズミカルなシーン生成
    """
    beat_timing = 60.0 / bpm  # 1ビートの秒数
    
    if scene_type == "オープニング":
        return {
            "story": f"【ビート同期】{bpm}BPMのリズムに完全同期。鼓動から始まる",
            "detailed_action": f"1. 黒画面に心電図の波形（{beat_timing:.2f}秒ごと）\n2. 波形が大きくなる\n3. ビートに合わせて光が点滅\n4. 光が人型になる\n5. 人が動き出す\n6. ビートに合わせてステップ",
            "environment": "黒背景にネオンライン",
            "emotion": "リズム、鼓動",
            "color_mood": "黒地にネオン色の線",
            "camera_work": f"ビートごとにカット（{beat_timing:.2f}秒間隔）",
            "props": "心電図、ネオンライト、スピーカー",
            "sound_design": "キックドラムに同期した視覚効果"
        }
    
    elif scene_type == "クライマックス":
        if scene_lyrics:
            return {
                "story": f"【サビ】歌詞「{scene_lyrics[:30]}」の各音節で画面が変化",
                "detailed_action": "1. 歌詞の音節ごとに色が変わる\n2. ドロップで画面分割\n3. ビートで画面回転\n4. ブレイクで静止\n5. ビルドアップで加速\n6. ドロップで爆発",
                "environment": "ライブステージ、レーザーショー",
                "emotion": "最高潮、エネルギー爆発",
                "color_mood": "ストロボライト、レインボー",
                "camera_work": "ビートマッチカット、フラッシュ編集",
                "props": "レーザー、ストロボ、煙",
                "sound_design": "ビート、ベース、シンセ"
            }
        else:
            return {
                "story": f"【ドロップ】{bpm}BPMの最強ビート。すべてが同期",
                "detailed_action": f"1. ビルドアップ（加速）\n2. 一瞬の静寂\n3. ドロップ（爆発）\n4. {beat_timing:.2f}秒ごとのフラッシュ\n5. カメラシェイク\n6. 色の爆発",
                "environment": "クラブ、フェスティバル",
                "emotion": "解放、エクスタシー",
                "color_mood": "UV光、ネオン",
                "camera_work": "シェイク、ストロボカット",
                "props": "レーザー、紙吹雪、煙",
                "sound_design": "ベースドロップ"
            }
    
    elif scene_type == "エンディング":
        return {
            "story": "ビートが徐々に遅くなり、静寂へ",
            "detailed_action": f"1. {bpm}BPMから開始\n2. 徐々にスローダウン\n3. 映像もスローモーションに\n4. 最後の一打\n5. 残響\n6. 無音",
            "environment": "夜明けのクラブ、空っぽのダンスフロア",
            "emotion": "終わり、余韻",
            "color_mood": "薄明かり、青い朝",
            "camera_work": "スローモーション、ロングテイク",
            "props": "空のグラス、散らばった紙吹雪",
            "sound_design": "エコー、リバーブ"
        }
    
    else:
        return {
            "story": f"【{beat_count}ビート】リズムパターンに完全同期",
            "detailed_action": f"1. キック（地面）\n2. スネア（ジャンプ）\n3. ハイハット（手拍子）\n4. {beat_timing:.2f}秒サイクル\n5. パターン変化\n6. ブレイク",
            "environment": "都市、ストリート",
            "emotion": "グルーヴ、ノリ",
            "color_mood": "コントラスト強め",
            "camera_work": f"{beat_timing:.2f}秒カット",
            "props": "影、光、動き",
            "sound_design": "リズムトラック"
        }


def create_detailed_midjourney_prompt(scene_details: Dict[str, str], has_character: bool, character_url: str = None) -> str:
    """
    詳細なMidjourney用プロンプト生成
    
    Args:
        scene_details: シーンの詳細情報
        has_character: キャラクター写真の有無
        character_url: キャラクター写真のURL（Midjourney参照用）
    """
    base_prompt = ""
    
    # 環境設定
    if scene_details.get("environment"):
        base_prompt += f"{scene_details['environment']}, "
    
    # アクション
    if scene_details.get("detailed_action"):
        # 最初の重要なアクションを抽出
        first_action = scene_details["detailed_action"].split('\n')[0].split('. ')[-1]
        base_prompt += f"{first_action}, "
    
    # 色とムード
    if scene_details.get("color_mood"):
        base_prompt += f"{scene_details['color_mood']}, "
    
    # カメラワーク
    if scene_details.get("camera_work"):
        camera = scene_details["camera_work"].split(',')[0]
        base_prompt += f"{camera}, "
    
    # 感情
    if scene_details.get("emotion"):
        emotion = scene_details["emotion"].split(',')[0].split('%')[0]
        base_prompt += f"{emotion} atmosphere, "
    
    # 技術的なパラメータ
    base_prompt += "cinematic lighting, ultra detailed, photorealistic, 8k resolution"
    
    # Midjourneyパラメータ
    params = " --ar 16:9 --v 6"
    
    if "オープニング" in scene_details.get("story", ""):
        params += " --style raw --stylize 100"
    elif "クライマックス" in scene_details.get("story", ""):
        params += " --stylize 750 --chaos 20"
    elif "エンディング" in scene_details.get("story", ""):
        params += " --style raw --stylize 250"
    else:
        params += " --stylize 500"
    
    if has_character and character_url:
        # キャラクター参照を追加
        params += f" --cref {character_url} --cw 100"  # キャラクター一貫性
    elif has_character:
        params += " --cw 100"  # キャラクター重み
    
    return base_prompt + params


def create_character_reference_prompt(base_prompt: str, character_photo_url: str, consistency_weight: int = 100) -> str:
    """
    キャラクター写真を使った一貫性のあるプロンプト生成
    
    Args:
        base_prompt: 基本プロンプト
        character_photo_url: キャラクター写真のURL
        consistency_weight: 一貫性の重み (0-100)
    
    Returns:
        キャラクター参照付きプロンプト
    """
    # Midjourneyの--crefパラメータを使用
    # --cref: キャラクターリファレンス
    # --cw: キャラクターウェイト（一貫性の強さ）
    return f"{base_prompt} --cref {character_photo_url} --cw {consistency_weight}"


def prepare_character_for_midjourney(character_photos: list) -> Dict[str, str]:
    """
    キャラクター写真をMidjourney用に準備
    
    Args:
        character_photos: アップロードされた写真リスト
    
    Returns:
        キャラクター情報
    """
    if not character_photos:
        return None
    
    # 最初の写真をメインリファレンスとして使用
    main_photo = character_photos[0]
    
    return {
        'main_reference': main_photo,  # メインキャラクター参照
        'additional_refs': character_photos[1:3] if len(character_photos) > 1 else [],  # 追加参照（最大2枚）
        'consistency_weight': 100,  # デフォルトは最大一貫性
        'description': '同一人物を維持'  # 説明
    }