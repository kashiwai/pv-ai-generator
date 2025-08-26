# Changelog

All notable changes to PV AI Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [3.0.0] - 2025-08-26

### Added
- test_piapi_midjourney.py
- test_midjourney_simple.py
- app_hf.py
- debug_video_generation.py
- test_midjourney.py
- ...他93件

## [2.6.2] - 2025-08-26

### Fixed
- 動画生成のタイムアウト問題を修正
  - タイムアウトを300秒から600秒に延長
  - ステータスチェック間隔を5秒から2秒に短縮
  - デフォルト処理モードをrelaxからfastに変更（有料プラン用）
- パフォーマンス最適化
  - 有料PIAPIプランに最適化
  - レスポンス時間の改善

## [2.6.1] - 2025-08-26

### Added
- MCP (Model Context Protocol) サーバー実装
  - 10分ごとの自動記録機能
  - タスク管理システム
  - API接続状態モニタリング
- 自動実行フック設定 (`.claude-code-hooks`)
  - ファイル変更の自動記録
  - ビルド・テスト実行の記録
- PIAPI/Midjourney診断ツール
  - 接続テスト機能
  - エラー診断機能
  - 設定状態確認
- APIキー管理システム
  - セキュアな設定管理
  - 環境変数自動読み込み
  - Streamlit secrets統合

### Fixed
- PIAPI接続の安定性向上
- Midjourney画像生成のタスクID取得処理
- 環境変数読み込みの改善

### Changed
- テストスクリプトの分離（Streamlit依存を除去）
- ログディレクトリ構造の整理
- 起動スクリプトの改良

## [2.6.0] - 2025-08-25

### Added
- 動画URL管理強化
- 台本連携表示機能
- URL一覧表示・ダウンロード機能

## [2.5.0] - 2025-08-20

### Added
- Midjourney統合修正
- キャラクター一貫性機能実装
- PIAPI v1エンドポイント対応

## [2.4.0] - 2025-08-13

### Added
- DALL-E 3統合
- 基本的なMidjourney連携

## バージョン規則

- **メジャーバージョン (X.0.0)**: 大規模な機能追加、互換性のない変更
- **マイナーバージョン (0.X.0)**: 新機能追加、後方互換性のある改善
- **パッチバージョン (0.0.X)**: バグ修正、小規模な改修