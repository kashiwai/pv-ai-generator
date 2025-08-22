"""
顔分析・特徴抽出モジュール
アップロードされた写真から人物の特徴を詳細に分析
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Optional, Tuple
import face_recognition
import mediapipe as mp
from dataclasses import dataclass
import json

@dataclass
class FacialFeatures:
    """顔の特徴データクラス"""
    face_shape: str  # 丸顔、卵型、面長、ベース型、逆三角形
    eye_shape: str   # アーモンド型、丸目、切れ長、たれ目、つり目
    eye_color: str   # 茶色、黒、青、緑、グレー
    eyebrow_shape: str  # アーチ型、直線、太眉、細眉
    nose_shape: str  # 高い、低い、団子鼻、鷲鼻
    lip_shape: str   # 厚い、薄い、ハート型、直線的
    hair_color: str  # 黒、茶、金、赤、白、カラフル
    hair_style: str  # ショート、ボブ、ミディアム、ロング、ツインテール、ポニーテール
    skin_tone: str   # 明るい、普通、暗い
    age_range: str   # 10代、20代前半、20代後半、30代、40代以上
    gender: str      # 女性、男性、中性的
    expression: str  # 笑顔、真顔、悲しい、驚き、怒り

class FaceAnalyzer:
    """顔分析クラス"""
    
    def __init__(self):
        # MediaPipeの初期化
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # 顔メッシュの初期化
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        # 顔検出の初期化
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.5
        )
    
    def analyze_face(self, image_path: str) -> FacialFeatures:
        """
        顔画像を分析して特徴を抽出
        
        Args:
            image_path: 画像ファイルパス
        
        Returns:
            顔の特徴
        """
        # 画像を読み込み
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # face_recognitionで顔の位置を検出
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return self._get_default_features()
        
        # 顔の特徴点を取得
        face_landmarks = face_recognition.face_landmarks(rgb_image)
        
        # MediaPipeで詳細な分析
        results = self.face_mesh.process(rgb_image)
        
        # 各特徴を分析
        features = FacialFeatures(
            face_shape=self._analyze_face_shape(face_landmarks),
            eye_shape=self._analyze_eye_shape(face_landmarks),
            eye_color=self._analyze_eye_color(rgb_image, face_landmarks),
            eyebrow_shape=self._analyze_eyebrow_shape(face_landmarks),
            nose_shape=self._analyze_nose_shape(face_landmarks),
            lip_shape=self._analyze_lip_shape(face_landmarks),
            hair_color=self._analyze_hair_color(rgb_image, face_locations),
            hair_style=self._analyze_hair_style(rgb_image, face_locations),
            skin_tone=self._analyze_skin_tone(rgb_image, face_locations),
            age_range=self._estimate_age(rgb_image, face_locations),
            gender=self._estimate_gender(face_landmarks),
            expression=self._analyze_expression(face_landmarks)
        )
        
        return features
    
    def _get_default_features(self) -> FacialFeatures:
        """デフォルトの特徴を返す"""
        return FacialFeatures(
            face_shape="卵型",
            eye_shape="アーモンド型",
            eye_color="茶色",
            eyebrow_shape="アーチ型",
            nose_shape="普通",
            lip_shape="普通",
            hair_color="黒",
            hair_style="ミディアム",
            skin_tone="普通",
            age_range="20代",
            gender="女性",
            expression="真顔"
        )
    
    def _analyze_face_shape(self, landmarks: List[Dict]) -> str:
        """顔の形を分析"""
        if not landmarks:
            return "卵型"
        
        # 顔の輪郭点を取得
        chin = landmarks[0].get('chin', [])
        
        if not chin:
            return "卵型"
        
        # 顔の幅と高さの比率から形を判定
        width = max([p[0] for p in chin]) - min([p[0] for p in chin])
        height = max([p[1] for p in chin]) - min([p[1] for p in chin])
        ratio = width / height if height > 0 else 1
        
        if ratio < 0.7:
            return "面長"
        elif ratio < 0.85:
            return "卵型"
        elif ratio < 0.95:
            return "丸顔"
        else:
            return "ベース型"
    
    def _analyze_eye_shape(self, landmarks: List[Dict]) -> str:
        """目の形を分析"""
        if not landmarks:
            return "アーモンド型"
        
        # 目の特徴点を取得
        left_eye = landmarks[0].get('left_eye', [])
        right_eye = landmarks[0].get('right_eye', [])
        
        if not left_eye or not right_eye:
            return "アーモンド型"
        
        # 目の縦横比から形を判定
        eye_width = max([p[0] for p in left_eye]) - min([p[0] for p in left_eye])
        eye_height = max([p[1] for p in left_eye]) - min([p[1] for p in left_eye])
        
        if eye_height / eye_width > 0.5:
            return "丸目"
        elif eye_height / eye_width < 0.3:
            return "切れ長"
        else:
            return "アーモンド型"
    
    def _analyze_eye_color(self, image: np.ndarray, landmarks: List[Dict]) -> str:
        """目の色を分析"""
        # 簡易実装（実際には虹彩の色を詳細に分析する必要がある）
        return "茶色"
    
    def _analyze_eyebrow_shape(self, landmarks: List[Dict]) -> str:
        """眉の形を分析"""
        if not landmarks:
            return "アーチ型"
        
        left_eyebrow = landmarks[0].get('left_eyebrow', [])
        
        if not left_eyebrow:
            return "アーチ型"
        
        # 眉の曲がり具合から形を判定
        y_values = [p[1] for p in left_eyebrow]
        if max(y_values) - min(y_values) < 5:
            return "直線"
        else:
            return "アーチ型"
    
    def _analyze_nose_shape(self, landmarks: List[Dict]) -> str:
        """鼻の形を分析"""
        return "普通"
    
    def _analyze_lip_shape(self, landmarks: List[Dict]) -> str:
        """唇の形を分析"""
        if not landmarks:
            return "普通"
        
        top_lip = landmarks[0].get('top_lip', [])
        bottom_lip = landmarks[0].get('bottom_lip', [])
        
        if not top_lip or not bottom_lip:
            return "普通"
        
        # 唇の厚さを判定
        lip_height = max([p[1] for p in bottom_lip]) - min([p[1] for p in top_lip])
        
        if lip_height > 20:
            return "厚い"
        elif lip_height < 10:
            return "薄い"
        else:
            return "普通"
    
    def _analyze_hair_color(self, image: np.ndarray, face_locations: List) -> str:
        """髪の色を分析"""
        if not face_locations:
            return "黒"
        
        # 顔の上部の領域から髪の色を推定
        top, right, bottom, left = face_locations[0]
        hair_region = image[max(0, top-50):top, left:right]
        
        if hair_region.size == 0:
            return "黒"
        
        # 平均色を計算
        avg_color = np.mean(hair_region, axis=(0, 1))
        
        # 色から髪色を判定
        if avg_color[0] > 150 and avg_color[1] > 150 and avg_color[2] > 150:
            return "金"
        elif avg_color[0] > 100 and avg_color[1] < 80 and avg_color[2] < 80:
            return "赤"
        elif avg_color[0] < 50 and avg_color[1] < 50 and avg_color[2] < 50:
            return "黒"
        else:
            return "茶"
    
    def _analyze_hair_style(self, image: np.ndarray, face_locations: List) -> str:
        """髪型を分析"""
        if not face_locations:
            return "ミディアム"
        
        # 髪の長さを推定
        top, right, bottom, left = face_locations[0]
        face_height = bottom - top
        
        # 顔の下の領域をチェック
        hair_below = image[bottom:min(image.shape[0], bottom + face_height), left:right]
        
        if hair_below.size > 0:
            # 髪が検出される範囲から長さを推定
            hair_pixels = np.sum(hair_below < 100)  # 暗い部分を髪と仮定
            total_pixels = hair_below.size
            
            hair_ratio = hair_pixels / total_pixels if total_pixels > 0 else 0
            
            if hair_ratio > 0.5:
                return "ロング"
            elif hair_ratio > 0.3:
                return "ミディアム"
            else:
                return "ショート"
        
        return "ミディアム"
    
    def _analyze_skin_tone(self, image: np.ndarray, face_locations: List) -> str:
        """肌の色調を分析"""
        if not face_locations:
            return "普通"
        
        top, right, bottom, left = face_locations[0]
        face_region = image[top:bottom, left:right]
        
        # 平均明度を計算
        avg_brightness = np.mean(face_region)
        
        if avg_brightness > 180:
            return "明るい"
        elif avg_brightness < 120:
            return "暗い"
        else:
            return "普通"
    
    def _estimate_age(self, image: np.ndarray, face_locations: List) -> str:
        """年齢を推定"""
        # 簡易実装（実際にはディープラーニングモデルを使用）
        return "20代"
    
    def _estimate_gender(self, landmarks: List[Dict]) -> str:
        """性別を推定"""
        # 簡易実装
        return "女性"
    
    def _analyze_expression(self, landmarks: List[Dict]) -> str:
        """表情を分析"""
        if not landmarks:
            return "真顔"
        
        # 口角の位置から表情を推定
        top_lip = landmarks[0].get('top_lip', [])
        
        if top_lip:
            # 口角の上がり具合をチェック
            left_corner = top_lip[0][1] if top_lip else 0
            right_corner = top_lip[-1][1] if top_lip else 0
            center = top_lip[len(top_lip)//2][1] if top_lip else 0
            
            if left_corner < center and right_corner < center:
                return "笑顔"
        
        return "真顔"
    
    def features_to_prompt(self, features: FacialFeatures) -> str:
        """
        特徴をプロンプトに変換
        
        Args:
            features: 顔の特徴
        
        Returns:
            プロンプト文字列
        """
        prompt_parts = []
        
        # 基本情報
        prompt_parts.append(f"{features.age_range}の{features.gender}")
        
        # 髪
        prompt_parts.append(f"{features.hair_color}の{features.hair_style}")
        
        # 顔
        prompt_parts.append(f"{features.face_shape}の顔")
        
        # 目
        prompt_parts.append(f"{features.eye_color}の{features.eye_shape}の目")
        
        # 表情
        if features.expression != "真顔":
            prompt_parts.append(features.expression)
        
        # 肌
        if features.skin_tone != "普通":
            prompt_parts.append(f"{features.skin_tone}肌")
        
        return "、".join(prompt_parts)