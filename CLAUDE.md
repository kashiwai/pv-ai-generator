# PV自動生成AIエージェント - プロジェクト情報

## 📋 プロジェクト概要
ビジネス向けPV（プロモーショナルビデオ）自動生成システム。
音楽ファイルと画像から、AIを使って自動的にPVを生成します。

## 🔑 API設定の重要事項

### PIAPI設定（最重要）
PIAPIは**2つのキー**が必要です：

1. **メインKEY** - 認証用のメインキー
2. **XKEY** - Midjourney、Hailuo等のサービスアクセス用

**設定方法：**
```toml
# Streamlit Cloud Secretsに以下を設定
PIAPI_KEY = "あなたのメインKEY"
PIAPI_XKEY = "あなたのXKEY"
```

### その他のAPIキー（オプション）
- `OPENAI_API_KEY` - GPT-4での台本生成
- `GOOGLE_API_KEY` - Gemini・音声合成
- `ANTHROPIC_API_KEY` - Claude 3での創造的な台本生成

## 🎯 主要機能

### 1. 音楽同期
- PV長さ = 音楽の長さ + 6秒
- 各シーン: 5-8秒で自動分割

### 2. 台本生成
- 3種類のパターン自動生成：
  - ストーリー重視
  - ビジュアル重視
  - 音楽同期重視
- 各シーンに詳細なストーリー内容
- Midjourney用の最適化されたプロンプト（--ar 16:9 --v 6）

### 3. キャラクター一貫性
- 出演者の写真をアップロード
- 同一人物で一貫性のあるPV生成
- --cref, --cw パラメータを使用

### 4. 画像生成（Midjourney経由）
- PIAPIのXKEYを使用してMidjourneyで生成
- シーンごとに最適化されたプロンプト
- キャラクター参照で一貫性を保持

### 5. 動画生成（Hailuo AI経由）
- 各画像から5-8秒の動画を生成
- 音楽と完全同期
- スムーズなトランジション

## 🚀 使用手順

1. **API設定**
   - サイドバーでPIAPIのメインKEYとXKEYを入力
   - その他のAPIキー（オプション）を入力

2. **基本入力**
   - プロジェクト名とタイトルを入力
   - 音楽ファイルをアップロード
   - 出演者の写真をアップロード（オプション）

3. **台本生成**
   - 3種類のパターンから選択
   - ストーリー内容とMidjourneyプロンプトを確認
   - 必要に応じて編集

4. **画像生成**
   - PIAPIを通じてMidjourneyで画像生成
   - キャラクター写真がある場合は一貫性を保持

5. **動画作成**
   - Hailuo AIで各シーンを動画化
   - 音楽と同期して最終的なPVを生成

## 📝 重要な注意事項

### APIキーを設定したら必ず確認すること：
1. **PIAPI メインKEY** - 認証が通るか
2. **PIAPI XKEY** - MidjourneyとHailuoにアクセスできるか
3. **接続状態** - サイドバーで「接続済み」と表示されるか

### トラブルシューティング：
- 画像生成が始まらない → PIAPIのXKEYを確認
- 動画生成が失敗する → PIAPIの両方のキーを確認
- 台本が生成されない → OpenAI APIキーを確認

## ⚠️ 重要：APIキーの永続化

### APIキーは消えません
- Streamlit Cloudの**Secrets**に保存済み
- コード更新しても**維持されます**
- 再デプロイしても**消えません**
- `IMPORTANT_API_KEYS.md`ファイルを**削除禁止**

## 🔧 技術仕様

### ファイル構成：
- `streamlit_app.py` - メインアプリケーション
- `piapi_integration.py` - PIAPI統合（Midjourney、Hailuo）
- `image_video_workflow.py` - 画像・動画生成ワークフロー
- `workflow_functions.py` - ワークフロー関数

### デプロイ情報：
- URL: https://pv-ai-generator-8tfxczsibmrquxq9ybjxgi.streamlit.app/
- Platform: Streamlit Cloud
- Python: 3.13

## 📌 今後必ず実行すること

**APIキーを登録したら：**
1. 接続状態を確認（サイドバー）
2. テスト生成を実行
3. エラーが出たらキーを再確認
4. 特にPIAPIの2つのキー（メインKEYとXKEY）が正しいか確認

## 🆘 サポート

問題が発生した場合：
1. まずAPIキーを確認（特にPIAPIの2つのキー）
2. 接続状態をチェック
3. デモモードで動作確認
4. エラーメッセージを確認