# Antigravity Video Automation Pipeline (AVAP)

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