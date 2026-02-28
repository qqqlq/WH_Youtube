import os
import sys
import json
import re
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add current directory (src) to sys.path to ensure module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner import PlannerAgent
from agents.collector import CollectorAgent
from engine.narrator import NarratorEngine
from engine.editor import EditorEngine


def slugify(text: str) -> str:
    """Convert topic string to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:80]


def main():
    load_dotenv()

    # Validation
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "your_api_key" in api_key:
        print("[ERROR] Valid GEMINI_API_KEY not found in .env file.")
        print("Please edit .env and add your Google Gemini API Key.")
        return

    # Argument Parser
    parser = argparse.ArgumentParser(description="Antigravity Video Automation Pipeline")
    parser.add_argument("topic", nargs="?", help="Video topic (e.g. 'Los Glaciares')")
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        topic = input("Enter video topic: ")

    # ── Project directory setup ──
    slug = slugify(topic)
    project_dir = Path("workspace/projects") / slug
    assets_dir = project_dir / "assets"
    narration_dir = project_dir / "narration"
    output_dir = project_dir / "outputs"

    for d in [assets_dir, narration_dir, output_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n[START] Starting AVAP for topic: {topic}")
    print(f"[INFO] Project directory: {project_dir}")

    # ── 1. PLAN ──
    script = None
    script_path = project_dir / "script.json"
    try:
        planner = PlannerAgent()
        print("\n[PLAN] Planning video content...")
        script = planner.generate_script(topic)

        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        print(f"[OK] Script saved to {script_path}")
    except Exception as e:
        print(f"[ERROR] Planning failed: {e}")
        return

    # ── 2. COLLECT ──
    print("\n[COLLECT] Starting asset collection...")
    collector = CollectorAgent(assets_dir=str(assets_dir))
    try:
        for scene in script.get("scenes", []):
            collector.collect(scene.get("visual_query"), scene.get("id"))
        print("[OK] Collection complete.")
    except Exception as e:
        print(f"[ERROR] Collection failed: {e}")
        return

    # ── 3. NARRATE ──
    print("\n[NARRATE] Generating narration audio...")
    narration_map = {}
    try:
        narrator = NarratorEngine(narration_dir=str(narration_dir))
        narration_map = narrator.generate_all(script)
        print(f"[OK] Narration complete. {len(narration_map)} clips generated.")
    except Exception as e:
        print(f"[WARN] Narration failed (continuing without audio): {e}")

    # ── 4. EDIT ──
    print("\n[EDIT] Rendering video...")
    try:
        editor = EditorEngine(
            assets_dir=str(assets_dir),
            output_dir=str(output_dir),
        )
        output_path = editor.render_video(
            script,
            output_filename="final.mp4",
            narration_map=narration_map,
        )

        if output_path:
            print(f"\n[DONE] Pipeline Finished!")
            print(f"  Video:     {output_path}")
            print(f"  Script:    {script_path}")
            print(f"  Assets:    {assets_dir}")
            print(f"  Narration: {narration_dir}")
        else:
            print("[ERROR] Editing produced no output.")
    except Exception as e:
        print(f"[ERROR] Editing failed: {e}")


if __name__ == "__main__":
    main()
