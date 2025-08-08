# PiAPI を使用した Hailuo 02 AI の設定ガイド

## PiAPIとは

PiAPIは、Hailuo 02 AIを含む複数のAIサービスへの統一APIアクセスを提供するプラットフォームです。
このシステムでは、PiAPI経由でHailuo 02の高品質な動画生成機能を利用します。

## セットアップ手順

### 1. PiAPIアカウントの作成

1. **PiAPIにアクセス**
   ```
   https://piapi.ai
   ```

2. **アカウント登録**
   - "Sign Up"をクリック
   - メールアドレスとパスワードを入力
   - メール認証を完了

3. **APIキーの取得**
   - ダッシュボードにログイン
   - "API Keys"セクションに移動
   - "Create New Key"をクリック
   - キーをコピー（一度しか表示されません）

### 2. Hugging Face Spacesでの設定

#### Repository Secretsに追加

1. Spaceの設定ページを開く:
   ```
   https://huggingface.co/spaces/mmz2501/pv-ai-generator/settings
   ```

2. "Repository secrets"セクションで以下のいずれかを設定:
   ```
   PIAPI_KEY = あなたのPiAPIキー
   ```
   または
   ```
   HAILUO_API_KEY = あなたのPiAPIキー
   ```
   （どちらでも動作します）

### 3. 利用可能なHailuoモデル

PiAPI経由で以下のモデルが利用可能:

#### テキストから動画生成（推奨）
- **t2v-02** - 最新・高品質モデル（デフォルト）
- **t2v-01** - 安定版モデル

#### 画像から動画生成
- **i2v-02** - 高品質画像アニメーション
- **i2v-01** - 基本画像アニメーション

#### 被写体参照動画
- **s2v-01** - キャラクター一貫性重視

### 4. 価格情報

| モデル | 解像度 | 長さ | 価格 |
|--------|--------|------|------|
| t2v-02 | 768p | 5秒 | $0.40 |
| t2v-02 | 768p | 10秒 | $0.80 |
| t2v-01 | 540p | 5秒 | $0.20 |
| i2v-02 | 768p | 5秒 | $0.40 |

### 5. 制限事項

- **プロンプト**: 最大2000文字
- **動画長**: 最大10秒/クリップ
- **解像度**: 540p〜768p
- **画像入力**: JPG/PNG、300-4096px、最大10MB

### 6. デバッグ情報

#### APIキーの確認
```python
# config.jsonで確認
{
  "hailuo_api_key": "your-piapi-key-here",
  ...
}
```

#### ログで確認
Spacesのログで以下のメッセージを確認:
```
Using Hailuo 02 AI for video generation (Recommended)
Hailuo task status: PROCESSING
Hailuo task status: SUCCESS
```

### 7. トラブルシューティング

#### "Invalid API Key"エラー
- PiAPIキーが正しく設定されているか確認
- Repository secretsで`PIAPI_KEY`または`HAILUO_API_KEY`として設定

#### "Task Failed"エラー
- クレジットが残っているか確認（PiAPIダッシュボード）
- プロンプトが2000文字以内か確認
- 動画長が10秒以内か確認

#### 生成が遅い
- PiAPIの処理時間は通常1-3分
- 高負荷時は5分程度かかる場合あり

### 8. 最適な設定

システムは以下の設定で最適化済み:
```json
{
  "model": "t2v-02",        // 最高品質モデル
  "resolution": 768,         // 高解像度
  "expand_prompt": true,     // AI によるプロンプト拡張
  "duration": 8,            // シーンごとの長さ
  "service_mode": "public"   // 公開モード
}
```

### 9. APIクレジット管理

- PiAPIダッシュボードでクレジット残高を確認
- 自動チャージ設定も可能
- 使用量の詳細レポートあり

### 10. サポート

- PiAPI公式ドキュメント: https://piapi.ai/docs
- Hailuo API詳細: https://piapi.ai/docs/hailuo-api
- サポート: support@piapi.ai

---

**注意**: PiAPIキーは秘密情報です。GitHubなどの公開リポジトリにコミットしないでください。