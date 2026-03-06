"""
Pipeline service — orchestrates Collector → Narrator → Editor.
Thin wrapper around the existing src/ modules.
"""
import re
import json
from pathlib import Path

from agents.collector import CollectorAgent
from engine.narrator import NarratorEngine
from engine.editor import EditorEngine


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:80]


def run_pipeline(script_data: dict, engine: str = "gtts") -> dict:
    """
    Run the full video generation pipeline.
    Returns a dict with status, video_url, project_slug, and sources.
    """
    title = script_data.get("title", "untitled")
    slug = slugify(title)
    project_dir = Path("workspace/projects") / slug
    assets_dir = project_dir / "assets"
    narration_dir = project_dir / "narration"
    output_dir = project_dir / "outputs"

    for d in [assets_dir, narration_dir, output_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Save script
    script_path = project_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)

    # ── 1. COLLECT ──
    collector = CollectorAgent(assets_dir=str(assets_dir))
    for scene in script_data.get("scenes", []):
        collector.collect(scene.get("visual_query", ""), scene.get("id"))

    # ── 2. NARRATE ──
    narrator = NarratorEngine(narration_dir=str(narration_dir), engine=engine)
    narration_map = narrator.generate_all(script_data)

    # ── 3. EDIT ──
    editor = EditorEngine(
        assets_dir=str(assets_dir),
        output_dir=str(output_dir),
    )
    editor.render_video(
        script_data,
        output_filename="final.mp4",
        narration_map=narration_map,
    )

    # ── 4. Collect source info ──
    sources = []
    for scene in script_data.get("scenes", []):
        sid = scene.get("id")
        meta_path = assets_dir / f"scene_{sid:02d}_meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            sources.append({
                "scene_id": sid,
                "query": meta.get("query", ""),
                "provider": meta.get("provider", "unknown"),
                "photographer": meta.get("photographer", "unknown"),
                "source_url": meta.get("source_url", ""),
            })

    # ── 5. Source report (Markdown) ──
    _generate_source_report(project_dir, assets_dir, script_data)

    return {
        "status": "done",
        "video_url": f"/outputs/{slug}/outputs/final.mp4",
        "project_slug": slug,
        "sources": sources,
    }


def _generate_source_report(project_dir: Path, assets_dir: Path, script_data: dict):
    """Generate sources.md — same logic as main.py."""
    lines = [
        "# 素材ソースレポート",
        "",
        f"**トピック:** {script_data.get('title', 'N/A')}",
        "",
        "| シーン | 検索クエリ | 提供元 | 撮影者 | ライセンス | ソースURL |",
        "|--------|-----------|--------|--------|-----------|----------|",
    ]
    for scene in script_data.get("scenes", []):
        sid = scene.get("id")
        meta_path = assets_dir / f"scene_{sid:02d}_meta.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            query = meta.get("query", "N/A")
            provider = meta.get("provider", "不明")
            photographer = meta.get("photographer", "不明")
            license_info = meta.get("license", "不明")
            source_url = meta.get("source_url", "")
            url_link = f"[Link]({source_url})" if source_url else "N/A"
        else:
            query = scene.get("visual_query", "N/A")
            provider = photographer = license_info = "N/A"
            url_link = "N/A"
        lines.append(f"| {sid:02d} | {query} | {provider} | {photographer} | {license_info} | {url_link} |")

    lines.extend(["", "---", "", "## ナレーションテキスト（字幕参考用）", "",
                   "| シーン | ナレーション | オーバーレイテキスト |",
                   "|--------|------------|-------------------|"])
    for scene in script_data.get("scenes", []):
        sid = scene.get("id")
        lines.append(f"| {sid:02d} | {scene.get('narration', '')} | {scene.get('overlay_text', '')} |")

    with open(project_dir / "sources.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
