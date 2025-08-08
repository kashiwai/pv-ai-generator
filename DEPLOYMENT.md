# Hugging Face Spaces デプロイメント手順

## デプロイメント完全ガイド

### 1. Hugging Face Spacesでの設定

#### 必要なシークレット設定
Spacesの Settings → Repository secrets から以下を設定:

```
OPENAI_API_KEY=sk-xxx...
ANTHROPIC_API_KEY=sk-ant-xxx...
GOOGLE_API_KEY=AIzaSy...
DEEPSEEK_API_KEY=xxx...
FISH_AUDIO_API_KEY=xxx...
MIDJOURNEY_API_KEY=xxx...    # 最優先
HAILUO_API_KEY=xxx...        # 推奨
VEO3_API_KEY=xxx...          # 推奨
SORA_API_KEY=xxx...
SEEDANCE_API_KEY=xxx...
DOMOAI_API_KEY=xxx...
```

### 2. 優先順位設定

#### 画像生成（最優先）
```
1. Midjourney v6 (MIDJOURNEY_API_KEY設定時)
2. DALL-E 3 (フォールバック)
```

#### 映像生成（推奨）
```
1. Hailuo 02 AI (HAILUO_API_KEY設定時)
2. VEO3 (VEO3_API_KEY設定時)
3. その他プロバイダー
```

### 3. Space設定

#### ハードウェア
- **CPU**: Basic (無料版)
- **推奨**: CPU Upgrade または GPU Small（高速処理）

#### スペース情報
```yaml
title: PV自動生成AIエージェント
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
python_version: 3.10
```

### 4. デプロイ手順

1. **GitHub経由でデプロイ**
```bash
# リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/pv-ai-generator
cd pv-ai-generator

# Hugging Faceリポジトリを追加
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/pv-ai-generator

# プッシュ
git push hf main
```

2. **直接アップロード**
- https://huggingface.co/spaces/YOUR_USERNAME/pv-ai-generator/tree/main
- ファイルをドラッグ＆ドロップ

### 5. 動作確認

#### チェックリスト
- [ ] Gradio UIが正常に表示される
- [ ] タイトル入力欄が機能する
- [ ] 音楽ファイルアップロードが機能する
- [ ] PV生成が開始される
- [ ] プログレスバーが表示される
- [ ] 生成完了後、動画が表示される

#### エラー対処

**Import Error**
```python
# requirements.txtを確認
moviepy==1.0.3  # Python 3.10互換バージョン
```

**API Key Error**
```
Settings → Repository secrets でAPIキーを設定
```

**メモリエラー**
```
ハードウェアをCPU UpgradeまたはGPU Smallに変更
```

### 6. 完全機能リスト

#### 実装済み機能（シンプル化禁止）
- ✅ 最大7分の動画生成
- ✅ 複数AIモデル対応
- ✅ Midjourney最優先画像生成
- ✅ Hailuo/VEO3推奨映像生成
- ✅ 音声合成（Google TTS/Fish Audio）
- ✅ 自動台本生成
- ✅ 映像・音声同期
- ✅ プログレスバー表示
- ✅ エラーハンドリング
- ✅ フォールバック機能

### 7. パフォーマンス最適化

#### 推奨設定
```python
# config.json
{
  "parallel_generation": false,  # Spaces環境では非推奨
  "auto_retry": true,
  "max_retries": 3,
  "scene_duration": 8,
  "output_fps": 30
}
```

### 8. モニタリング

#### ログ確認
- Spaces → Logs でリアルタイムログ確認
- エラー発生時の詳細確認

#### 使用状況
- Settings → Usage でリソース使用状況確認

### 9. トラブルシューティング

#### よくある問題

**Q: 生成が遅い**
A: ハードウェアをアップグレード、または scene_duration を短縮

**Q: APIエラー**
A: APIキーの設定確認、クォータ制限確認

**Q: メモリ不足**
A: 動画解像度を下げる、または処理を分割

### 10. 完全性の維持

**重要**: 
- シンプル化は一切禁止
- すべての機能を完全実装
- バグなしで動作確認
- ユーザー要求を完全に満たす

---

## デプロイ先URL
https://huggingface.co/spaces/mmz2501/pv-ai-generator

## サポート
問題が発生した場合は、Spacesのログを確認してください。