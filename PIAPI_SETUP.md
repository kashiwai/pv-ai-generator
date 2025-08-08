# PiAPI 統合設定ガイド - Midjourney + Hailuo 02

## PiAPIとは

PiAPIは、複数のAIサービスへの統一APIアクセスを提供するプラットフォームです。
このシステムでは、**1つのPiAPIキー**で以下を利用します：
- **Midjourney v6.1** - 高品質画像生成
- **Hailuo 02 AI** - 高品質動画生成

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

#### Repository Secretsに追加（重要：1つのキーでOK）

1. Spaceの設定ページを開く:
   ```
   https://huggingface.co/spaces/mmz2501/pv-ai-generator/settings
   ```

2. "Repository secrets"セクションで設定:
   ```
   PIAPI_KEY = あなたのPiAPIキー
   ```
   
   **この1つのキーで：**
   - ✅ Midjourney v6.1 画像生成
   - ✅ Hailuo 02 動画生成
   - ✅ その他PiAPI対応サービス

### 3. PiAPIで利用可能なサービス

#### Midjourney (画像生成)

**サポート機能：**
- Imagine (テキストから画像生成)
- Upscale (高解像度化)
- Variation (バリエーション生成)
- Reroll (再生成)
- Describe (画像説明)
- Blend (画像ブレンド)
- Inpaint/Outpaint (画像編集)

**モデルバージョン：**
- v6.1 (最新・推奨)
- v6.0
- v5.2
- Niji (アニメスタイル)

#### Hailuo (動画生成)

**テキストから動画生成（推奨）**
- **t2v-02** - 最新・高品質モデル（デフォルト）
- **t2v-01** - 安定版モデル

**画像から動画生成**
- **i2v-02** - 高品質画像アニメーション
- **i2v-01** - 基本画像アニメーション

**被写体参照動画**
- **s2v-01** - キャラクター一貫性重視

### 4. 価格情報

#### Midjourney 価格
| 機能 | 価格 |
|------|------|
| Imagine (4枚生成) | $0.08-0.12 |
| Upscale | $0.02-0.03 |
| Variation | $0.08-0.12 |

#### Hailuo 価格
| モデル | 解像度 | 長さ | 価格 |
|--------|--------|------|------|
| t2v-02 | 768p | 5秒 | $0.40 |
| t2v-02 | 768p | 10秒 | $0.80 |
| t2v-01 | 540p | 5秒 | $0.20 |
| i2v-02 | 768p | 5秒 | $0.40 |

### 5. 制限事項

#### Midjourney
- **プロンプト**: 最大4000文字
- **画像サイズ**: 256x256～2048x2048
- **アスペクト比**: 1:2～2:1

#### Hailuo
- **プロンプト**: 最大2000文字
- **動画長**: 最大10秒/クリップ
- **解像度**: 540p～768p
- **画像入力**: JPG/PNG、300-4096px、最大10MB

### 6. デバッグ情報

#### APIキーの確認
```python
# config.jsonで確認
{
  "piapi_key": "your-piapi-key-here",
  ...
}
```

#### ログで確認
Spacesのログで以下のメッセージを確認:
```
Using Midjourney via PiAPI for character generation (Priority)
Using Hailuo 02 AI for video generation (Recommended)
Midjourney task status: PROCESSING
Hailuo task status: SUCCESS
```

### 7. トラブルシューティング

#### "Invalid API Key"エラー
- PiAPIキーが正しく設定されているか確認
- Repository secretsで`PIAPI_KEY`として設定

#### "Task Failed"エラー
- クレジットが残っているか確認（PiAPIダッシュボード）
- プロンプトが文字数制限内か確認
- 動画長が10秒以内か確認

#### 生成が遅い
- Midjourney: 通常30-60秒
- Hailuo: 通常1-3分
- 高負荷時は5分程度かかる場合あり

### 8. 最適な設定

#### Midjourney設定
```json
{
  "model_version": "6.1",    // 最新バージョン
  "quality": 2,              // 高品質
  "style": "raw",            // 自然なスタイル
  "aspect_ratio": "1:1",     // 正方形
  "stylize": 100,            // スタイル強度
  "chaos": 0                 // 一貫性重視
}
```

#### Hailuo設定
```json
{
  "model": "t2v-02",         // 最高品質モデル
  "resolution": 768,         // 高解像度
  "expand_prompt": true,     // AIプロンプト拡張
  "duration": 8,            // シーン長
  "service_mode": "public"   // 公開モード
}
```

### 9. APIクレジット管理

- PiAPIダッシュボードでクレジット残高を確認
- 自動チャージ設定も可能
- 使用量の詳細レポートあり

### 10. サポート

- PiAPI公式ドキュメント: https://piapi.ai/docs
- Midjourney API: https://piapi.ai/docs/midjourney-api
- Hailuo API: https://piapi.ai/docs/hailuo-api
- サポート: support@piapi.ai

### 11. 統合のメリット

- **1つのキーで管理**: PIAPI_KEYだけでMidjourneyとHailuoを利用
- **コスト効率**: 統一課金で管理が簡単
- **API管理**: 1つのダッシュボードですべて管理
- **サポート**: PiAPIの統一サポート

---

**注意**: PiAPIキーは秘密情報です。GitHubなどの公開リポジトリにコミットしないでください。