import os
import json
from pathlib import Path
from gtts import gTTS
from mutagen.mp3 import MP3


class NarratorEngine:
    """Generates narration audio from script text using gTTS."""

    def __init__(self, narration_dir: str = "workspace/narration"):
        self.narration_dir = Path(narration_dir)
        self.narration_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, script_data: dict) -> dict:
        """
        Generate narration MP3 for each scene.
        Returns a dict mapping scene_id -> {"path": Path, "duration": float}.
        """
        results = {}
        for scene in script_data.get("scenes", []):
            scene_id = scene.get("id")
            text = scene.get("narration", "")
            if not text:
                continue

            mp3_path = self.narration_dir / f"scene_{scene_id:02d}.mp3"
            try:
                tts = gTTS(text=text, lang="ja", slow=False)
                tts.save(str(mp3_path))

                # Get actual audio duration
                audio = MP3(str(mp3_path))
                duration = audio.info.length

                results[scene_id] = {
                    "path": mp3_path,
                    "duration": duration,
                }
                print(f"    ✓ Narration scene {scene_id:02d}: {duration:.1f}s")
            except Exception as e:
                print(f"    ✗ Narration scene {scene_id:02d} failed: {e}")

        return results


if __name__ == "__main__":
    # Quick test
    mock = {
        "scenes": [
            {"id": 1, "narration": "これはテスト音声です。ナレーションが正しく生成されるか確認します。"},
        ]
    }
    n = NarratorEngine()
    res = n.generate_all(mock)
    print(res)
