# WH_Youtube

## 概要
Gemini API をオーケストレーターとし、YouTube ショート動画の「企画→素材収集→ナレーション生成→粗編集」を自動化するパイプライン。
最終的な仕上げ（演出・微調整）は人間が DaVinci Resolve 等で行う「Human-in-the-loop」型ワークフロー。

## パイプライン

```
[Human] テーマ入力
    ↓
[Planner Agent] Gemini API → 構成台本 (JSON)
    ↓
[Collector Agent] Pexels API → フリー素材画像
    ↓
[Narrator Engine] gTTS → ナレーション音声 (MP3)
    ↓
[Editor Engine] MoviePy → 粗編集動画 (MP4)
    ↓
[Human] DaVinci Resolve 等で仕上げ
```

## 技術スタック
| 項目 | 技術 |
|------|------|
| 言語 | Python 3.11+ |
| 企画 | Gemini API (`google-generativeai`) |
| 素材収集 | Pexels API (+ Unsplash / Pixabay フォールバック) |
| TTS | gTTS (Google Text-to-Speech) |
| 動画編集 | MoviePy v2 + Pillow |
| データ検証 | Pydantic |

## ディレクトリ構造

```
WH_youtube/
├── docs/                   # [NEW] 今後のアーキテクチャやロードマップなどの構想ドキュメントを格納
├── server/                 # FastAPI バックエンド
├── frontend/               # React (Vite) フロントエンド
├── src/                    # Python コアロジック (Agents / Engine)
└── workspace/projects/     # 生成動画の出力フォルダ
```

## セットアップ

```bash
# 1. 依存インストール
pip install -e .
pip install gTTS mutagen

# 2. API キー設定 (.env)
GEMINI_API_KEY=your_key
PEXELS_API_KEY=your_key   # https://www.pexels.com/api/

# 3. 実行
python src/main.py "Los Glaciares National Park"
```

## 今後の拡張予定
- [x] 高品質 TTS (VOICEVOX / ElevenLabs) への切り替え と複数キャラの動的使い分け
- [x] BGM 自動選定・効果音(SE)の合成
- [x] Ken Burns エフェクト（ズーム・パン）
- [ ] YouTube API 連携（自動アップロード）

## チェンジログ

### v0.8.0 — 2026-03-08
- **Dynamic Visuals & Performance (アニメーションと動画統合・高速化)**
  - **Ken Burns エフェクト**: すべての静止画シーンに対して、ズームイン・ズームアウト・左右パンの滑らかなアニメーションをランダムで自動適用。
  - **Pexels Video API 統合**: AIの判断により、静止画ではなく数秒の動画素材（Bロール）をダウンロードし、背景としてループ再生する機能を実装。
  - **オーバーレイ画像合成機能**: `workspace/assets/overlays/` 内に置かれた透過画像（ミームやいらすとや素材など）を、UIからのキーワード指定によって動画の右下にポン出しする機能を実装。
  - **リッチテロップ（**強調**対応）**: 台本の `**` で囲まれたキーワードを検知し、テロップのその部分だけをアクセントカラー（黄色）で描画する機能を実装。
  - **パイプラインの並列化と高速化**: 素材収集(`collect_all`)とナレーション生成(VOICEVOX)をマルチスレッド化(最大6並列)。またPILの`stroke_width`を利用したテロップ描画の抜本的最適化により、レンダリング時間を大幅削減。

### v0.7.0 — 2026-03-08
- **Audio/Visual Polish (演出と音声の強化)**
  - **BGMとSEの自動合成機能**: `audio_catalog.json` を用いたBGMのマッピング管理（キーワード→実ファイル名）、およびシーンプロンプトからの効果音自動配置に対応。
  - **TTSマルチキャラクター対応**: VOICEVOXAPIを活用し、シーン単位でずんだもん・めたん・つむぎ等のキャラクターを柔軟に切り替えられるUI・バックエンドロジックを追加。キャラの一括変更機能も実装。
  - **YouTube Shorts風自動テロップ**: 各シーンのナレーションテキストを、YouTubeショートなどでよく使われる太字の白文字＋黒縁取りスタイル（下部中央配置）で自動合成する機能を追加。
  - **プログレスバーUIと非同期ジョブ状況のリアルタイム表示**: 動画レンダリングの状況（素材収集→ナレーション→合成）をパーセンテージとステータスで表示する Animated Stripes UI を導入。
  - **トランジション**: クリップ間のクロスフェード(CrossFadeIn)機能を追加。

### v0.6.0 — 2026-03-08
- **プロジェクト履歴・途中再開機能の追加 (UX改善)**
  - 過去に作成したプロジェクトを振り返る「履歴一覧画面」をReactフロント側に実装。
  - プロジェクトを選択すると、完了した動画のプレビューや、当時の台本データを復元して再編集・再出力が可能になった。
- **ハイブリッド画像生成アプローチの確立**
  - **手動アップロード機能**: 台本編集画面の各シーンに、外部生成AIで作った画像などを直接アップロード・差し替えできる機能とAPIを追加 (`/api/upload_image`)。
  - **外部AI用プロンプトの自動生成**: Pexels等のフリー素材向け検索クエリとは別に、Midjourney等で使える「高画質AI画像用長文プロンプト（英語）」を Gemini に自動生成・提示させるよう改修。
  - **素材適用の優先度変更**: ユーザーが手動でアップロードした画像（上書き）が存在する場合、バックエンドのパイプライン（`collector.py` および `editor.py`）が自動で既存素材をスキップし、手動画像を最優先で適用するロジックを実装。

### v0.5.0 — 2026-03-07
- **Vercel デプロイ対応とタイムアウト回避**
  - フロントエンドをVercelへデプロイできるようCORS設定および環境変数（`VITE_API_BASE`）を整備
  - Vercel/Cloudflareの100秒タイムアウト制限を回避するため、FastAPIに非同期ジョブ管理（`BackgroundTasks`）を導入し、動画生成APIをポーリング方式（`render_status`）に全面刷新
- **VOICEVOX（ずんだもん）エンジンの統合**
  - 高品質なナレーション生成のため、Docker経由でVOICEVOX APIを連携（Phase B）
  - フロントエンドにナレーション音声（VOICEVOX / gTTS）の選択ドロップダウンを追加
- **Gemini SDK移行**
  - 廃止予定の `google-generativeai` から公式の最新 `google-genai` SDK へ完全移行（Phase C）
  - Cloudflare Tunnelを前提としたインフラガイド (`docs/infrastructure_setup_guide.md`) などのドキュメントを拡充

### v0.4.0 — 2026-03-01
- **Web アプリケーション化 (MVP)**
- FastAPI バックエンド (`server/`): チャット・台本生成・動画レンダリング API
- React フロントエンド (`frontend/`): 3ステップウィザード UI（企画→台本編集→プレビュー）
- Vite dev proxy で開発時 API 連携
- 音声エンジン抽象化の設計（Strategy パターン）を策定

### v0.3.0 — 2026-03-01
- オーバーレイテキスト（字幕）を動画から削除（DaVinci Resolve で別途追加する運用に変更）
- パイプライン完了時に `sources.md`（素材ソースレポート）を自動生成
  - 各画像の提供元・撮影者・ライセンス・ソースURL を一覧表示
  - ナレーションテキスト一覧（字幕作成の参考用）

### v0.2.0 — 2026-03-01
- 画像タイリング問題を修正（PIL ブラー背景 + センターフィット方式に変更）
- ナレーション機能追加（gTTS による日本語 TTS 自動生成）
- ディレクトリ構造をプロジェクト単位に分離（`workspace/projects/<slug>/`）
- `narrator.py` 新規作成
- ドキュメント全面更新

### v0.1.0 — 2026-03-01
- 素材収集を Google Images スクレイピングから Pexels API に切り替え
- Playwright / BeautifulSoup4 依存を削除
- IMAGE NOT FOUND 問題を解消

### v0.0.1 — 初期プロトタイプ
- Gemini API による構成台本自動生成（`planner.py`）
- Playwright による Google Images スクレイピング（`collector.py`）
- MoviePy による動画結合（`editor.py`）