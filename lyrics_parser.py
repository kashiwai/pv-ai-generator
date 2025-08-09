"""
歌詞解析モジュール
歌詞を解析してシーンに分割
"""

import re
from typing import List, Dict, Optional


def parse_lyrics_to_scenes(lyrics: str, num_scenes: int) -> List[str]:
    """
    歌詞を指定されたシーン数に分割
    
    Args:
        lyrics: 歌詞テキスト
        num_scenes: シーン数
    
    Returns:
        各シーンに対応する歌詞のリスト
    """
    if not lyrics:
        return [""] * num_scenes
    
    # 歌詞のパート（[Verse], [Chorus]など）を検出
    parts = parse_lyrics_structure(lyrics)
    
    if parts:
        # 構造化された歌詞の場合
        return distribute_parts_to_scenes(parts, num_scenes)
    else:
        # 構造化されていない歌詞の場合
        return split_lyrics_evenly(lyrics, num_scenes)


def parse_lyrics_structure(lyrics: str) -> List[Dict[str, str]]:
    """
    歌詞の構造（Verse, Chorus等）を解析
    
    Args:
        lyrics: 歌詞テキスト
    
    Returns:
        パートごとの歌詞リスト
    """
    # パートのパターン（[Verse 1], [Chorus], [Bridge]など）
    part_pattern = r'\[(.*?)\]'
    
    parts = []
    current_part = None
    current_content = []
    
    for line in lyrics.split('\n'):
        # パートヘッダーを検出
        match = re.match(part_pattern, line)
        if match:
            # 前のパートを保存
            if current_part:
                parts.append({
                    'name': current_part,
                    'content': '\n'.join(current_content).strip()
                })
            # 新しいパート開始
            current_part = match.group(1)
            current_content = []
        else:
            # パートの内容を追加
            if line.strip():  # 空行を除外
                current_content.append(line)
    
    # 最後のパートを保存
    if current_part:
        parts.append({
            'name': current_part,
            'content': '\n'.join(current_content).strip()
        })
    
    return parts


def distribute_parts_to_scenes(parts: List[Dict[str, str]], num_scenes: int) -> List[str]:
    """
    歌詞のパートをシーンに配分
    
    Args:
        parts: パートごとの歌詞
        num_scenes: シーン数
    
    Returns:
        各シーンに対応する歌詞のリスト
    """
    scene_lyrics = []
    
    if len(parts) >= num_scenes:
        # パート数がシーン数以上の場合、各シーンに1パート割り当て
        for i in range(num_scenes):
            if i < len(parts):
                scene_lyrics.append(parts[i]['content'])
            else:
                scene_lyrics.append("")
    else:
        # パート数がシーン数より少ない場合
        scenes_per_part = num_scenes // len(parts)
        remainder = num_scenes % len(parts)
        
        for i, part in enumerate(parts):
            # 各パートを複数シーンに分割
            part_lines = part['content'].split('\n')
            scenes_for_this_part = scenes_per_part + (1 if i < remainder else 0)
            
            if len(part_lines) >= scenes_for_this_part:
                # 行数が十分ある場合、均等に分割
                lines_per_scene = len(part_lines) // scenes_for_this_part
                for j in range(scenes_for_this_part):
                    start_idx = j * lines_per_scene
                    end_idx = start_idx + lines_per_scene if j < scenes_for_this_part - 1 else len(part_lines)
                    scene_lyrics.append('\n'.join(part_lines[start_idx:end_idx]))
            else:
                # 行数が少ない場合、同じパートを繰り返し使用
                for j in range(scenes_for_this_part):
                    scene_lyrics.append(part['content'])
    
    # シーン数に合わせて調整
    while len(scene_lyrics) < num_scenes:
        scene_lyrics.append("")
    
    return scene_lyrics[:num_scenes]


def split_lyrics_evenly(lyrics: str, num_scenes: int) -> List[str]:
    """
    歌詞を均等にシーン数で分割
    
    Args:
        lyrics: 歌詞テキスト
        num_scenes: シーン数
    
    Returns:
        各シーンに対応する歌詞のリスト
    """
    lines = [line for line in lyrics.split('\n') if line.strip()]
    
    if not lines:
        return [""] * num_scenes
    
    # 各シーンの行数を計算
    lines_per_scene = max(1, len(lines) // num_scenes)
    
    scene_lyrics = []
    for i in range(num_scenes):
        start_idx = i * lines_per_scene
        end_idx = start_idx + lines_per_scene if i < num_scenes - 1 else len(lines)
        
        if start_idx < len(lines):
            scene_content = '\n'.join(lines[start_idx:end_idx])
            scene_lyrics.append(scene_content)
        else:
            scene_lyrics.append("")
    
    return scene_lyrics


def identify_key_moments(lyrics: str) -> Dict[str, List[str]]:
    """
    歌詞から重要なモーメント（サビ、クライマックス等）を特定
    
    Args:
        lyrics: 歌詞テキスト
    
    Returns:
        モーメントタイプごとの歌詞リスト
    """
    parts = parse_lyrics_structure(lyrics)
    
    key_moments = {
        'opening': [],
        'verse': [],
        'chorus': [],
        'bridge': [],
        'climax': [],
        'ending': []
    }
    
    for i, part in enumerate(parts):
        part_name = part['name'].lower()
        
        # 最初のパートはオープニング
        if i == 0:
            key_moments['opening'].append(part['content'])
        
        # 最後のパートはエンディング
        if i == len(parts) - 1:
            key_moments['ending'].append(part['content'])
        
        # パートタイプで分類
        if 'verse' in part_name:
            key_moments['verse'].append(part['content'])
        elif 'chorus' in part_name or 'サビ' in part_name:
            key_moments['chorus'].append(part['content'])
            # サビの最後のものをクライマックスとする
            if i >= len(parts) * 0.6:  # 後半のサビ
                key_moments['climax'].append(part['content'])
        elif 'bridge' in part_name:
            key_moments['bridge'].append(part['content'])
    
    return key_moments


def suggest_scene_emotion(lyrics_part: str) -> str:
    """
    歌詞の内容から感情・雰囲気を推測
    
    Args:
        lyrics_part: 歌詞の一部
    
    Returns:
        推測された感情・雰囲気
    """
    if not lyrics_part:
        return "neutral"
    
    lyrics_lower = lyrics_part.lower()
    
    # 感情キーワードマッピング
    emotion_keywords = {
        'energetic': ['走', 'run', 'jump', '飛', 'dance', '踊', '叫', 'shout'],
        'romantic': ['愛', 'love', '恋', 'kiss', 'heart', '抱', 'hug'],
        'sad': ['涙', 'tear', 'cry', '泣', '悲', 'sad', 'lonely', '寂'],
        'hopeful': ['希望', 'hope', '夢', 'dream', '明日', 'tomorrow', '未来', 'future'],
        'nostalgic': ['思い出', 'memory', '昔', 'past', '懐', 'remember'],
        'powerful': ['強', 'strong', '力', 'power', '勝', 'win', '戦', 'fight'],
        'peaceful': ['静', 'quiet', '平和', 'peace', '優', 'gentle', '穏', 'calm']
    }
    
    # 各感情のスコアを計算
    emotion_scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(1 for keyword in keywords if keyword in lyrics_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    # 最も高いスコアの感情を返す
    if emotion_scores:
        return max(emotion_scores, key=emotion_scores.get)
    
    return "neutral"