# WH_Youtube

## 概要
Gemini API をオーケストレーターとし、YouTube ショート動画の「企画→素材収集→ナレーション生成→効果音/BGM合成→動画編集」を全自動化するフルスタックWebアプリケーションパイプライン。
静止画だけでなくKen Burnsエフェクトによるアニメーション、数秒の動画素材（Bロール）、オーバーレイ画像合成、YouTube Shorts風リッチテロップなどを自動生成し、ブラウザ上で直感的に動画をプロデュースできます。
最終的な仕上げ（演出・微調整）は人間が DaVinci Resolve 等で行う「Human-in-the-loop」型ワークフローを想定しています。

## システムアーキテクチャ
動画レンダリングという高負荷の処理を実行するため、「フロントエンドはクラウド、バックエンドは自宅サーバー」という分離アーキテクチャを採用しています。
- **フロントエンド (Vercel)**: React (Vite) で構築されたWeb UI。場所を選ばずどこからでもスマホやPCで動画の企画・編集・生成指示が可能。
- **バックエンド (自宅ミニPC / Ubuntu Server)**: FastAPIベースのREST API。Cloudflare Tunnelsを用いて安全に外部公開され、AIエージェントによる処理やMoviePyによる動画エンコード、VOICEVOXコンテナ等の数分単位で高負荷がかかる処理を担当します。

## パイプライン

```text
[Human] WebUIからテーマ入力・台本修正
    ↓ (API Request via Cloudflare Tunnel)
[Planner Agent] Gemini API → 構成台本生成 (動画/静止画の判定、プロンプト、演出指定)
    ↓
[Collector Agent] Pexels API等 → Bロール動画・フリー素材画像収集
    ↓
[Narrator Engine] VOICEVOX (Docker) → 複数キャラクターによるナレーション音声生成
    ↓
[Editor Engine] MoviePy → Ken Burns効果、BGM/SE、オーバーレイ画像、リッチテロップを合成した動画出力 (MP4)
    ↓
[Human] WebUIからプレビュー＆ダウンロード
```

## 技術スタック
| 項目 | 技術 |
|------|------|
| 共通言語 | Python 3.11+ (Backend) / Node.js (Frontend) |
| フロントエンド | React, Vite, CSS |
| APIサーバー | FastAPI, Pydantic, Uvicorn |
| AI連携 | Gemini API (`google-genai` 公式SDK) |
| 素材収集 | Pexels API (画像/動画), Unsplash, Pixabay |
| 音声合成 (TTS) | VOICEVOX (Docker), gTTS |
| 動画・画像処理 | MoviePy v2, Pillow, FFmpeg (マルチスレッド最適化) |
| インフラ・通信 | Cloudflare Tunnels (アクセス制御), Vercel (ホスティング) |

## ディレクトリ構造

```text
WH_youtube/
├── docs/                   # 構想・アーキテクチャ・インフラ設定などのドキュメント群
├── server/                 # FastAPI バックエンド
│   ├── routers/            # APIエンドポイント (video, upload, history等)
│   └── services/           # バックグラウンドジョブ制御、パイプライン呼び出し
├── frontend/               # React (Vite) フロントエンド
│   ├── src/components/     # UIコンポーネント (ScriptEditor, UIProgressBar等)
│   └── .env.local          # VITE_API_BASE (Cloudflare TunnelのURL) 等の設定
├── src/                    # Python コアロジック (Pipeline / Agents / Engine)
│   ├── agents/             # PlannerAgent (企画), CollectorAgent (素材収集)
│   └── engine/             # NarratorEngine (音声生成), EditorEngine (動画編集合成)
└── workspace/              # 動的生成データの出力先
    ├── assets/             # ダウンロードした画像・動画素材・BGM・効果音
    │   └── overlays/       # ユーザー手動配置のポン出し用透過PNG画像フォルダ
    └── projects/           # 各生成プロジェクトごとの台本、音声、出力動画フォルダ
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