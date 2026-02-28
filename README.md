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
├── .env                    # API キー
├── pyproject.toml          # 依存関係
├── src/
│   ├── main.py             # エントリーポイント
│   ├── agents/
│   │   ├── planner.py      # 構成作家 (Gemini)
│   │   └── collector.py    # 素材収集 (Pexels API)
│   └── engine/
│       ├── editor.py       # 動画編集 (MoviePy)
│       └── narrator.py     # ナレーション (gTTS)
└── workspace/
    └── projects/
        └── <topic_slug>/   # 動画ごとのプロジェクト
            ├── script.json
            ├── assets/     # 画像素材
            ├── narration/  # TTS音声
            └── outputs/    # 生成動画
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
- [ ] 高品質 TTS (VOICEVOX / ElevenLabs) への切り替え
- [ ] BGM 自動選定・合成
- [ ] Ken Burns エフェクト（ズーム・パン）
- [ ] YouTube API 連携（自動アップロード）

## チェンジログ

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