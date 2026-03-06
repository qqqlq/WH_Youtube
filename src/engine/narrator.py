import os
import wave
import requests
from pathlib import Path
from gtts import gTTS
from mutagen.mp3 import MP3


class NarratorEngine:
    """Generates narration audio from script text using specified TTS engine (gTTS or VOICEVOX)."""

    def __init__(self, narration_dir: str = "workspace/narration", engine: str = "gtts", voicevox_host: str = "127.0.0.1:50021", speaker_id: int = 3):
        self.narration_dir = Path(narration_dir)
        self.narration_dir.mkdir(parents=True, exist_ok=True)
        self.engine = engine
        self.voicevox_host = voicevox_host
        self.speaker_id = speaker_id

    def _get_wav_duration(self, wav_path: Path) -> float:
        with wave.open(str(wav_path), 'rb') as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / float(rate)

    def _generate_voicevox(self, text: str, output_path: Path) -> float:
        # 1. create audio_query
        query_payload = {'text': text, 'speaker': self.speaker_id}
        resp = requests.post(f"http://{self.voicevox_host}/audio_query", params=query_payload)
        resp.raise_for_status()
        query_data = resp.json()
        
        # 2. synthesis
        synth_payload = {'speaker': self.speaker_id}
        resp2 = requests.post(
            f"http://{self.voicevox_host}/synthesis",
            params=synth_payload,
            json=query_data,
            headers={'Content-Type': 'application/json'}
        )
        resp2.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(resp2.content)
            
        return self._get_wav_duration(output_path)

    def _generate_gtts(self, text: str, output_path: Path) -> float:
        tts = gTTS(text=text, lang="ja", slow=False)
        tts.save(str(output_path))
        audio = MP3(str(output_path))
        return audio.info.length

    def generate_all(self, script_data: dict, force_engine: str = None) -> dict:
        """
        Generate narration audio for each scene using the selected engine.
        Returns a dict mapping scene_id -> {"path": Path, "duration": float}.
        """
        results = {}
        use_engine = force_engine or self.engine
        
        for scene in script_data.get("scenes", []):
            scene_id = scene.get("id")
            text = scene.get("narration", "")
            if not text:
                continue

            # VOICEVOX outputs WAV (faster to generate/process), gTTS outputs MP3
            ext = ".wav" if use_engine == "voicevox" else ".mp3"
            audio_path = self.narration_dir / f"scene_{scene_id:02d}{ext}"
            
            try:
                if use_engine == "voicevox":
                    duration = self._generate_voicevox(text, audio_path)
                else:
                    duration = self._generate_gtts(text, audio_path)

                results[scene_id] = {
                    "path": audio_path,
                    "duration": duration,
                }
                print(f"    ✓ Narration scene {scene_id:02d} ({use_engine}): {duration:.1f}s")
            except Exception as e:
                print(f"    ✗ Narration scene {scene_id:02d} ({use_engine}) failed: {e}")

        return results


if __name__ == "__main__":
    # Quick test for both engines
    mock = {
        "scenes": [
            {"id": 1, "narration": "これはテスト音声です。ナレーションが正しく生成されるか確認します。"},
        ]
    }
    
    print("Testing gTTS...")
    n_gtts = NarratorEngine(engine="gtts")
    res_gtts = n_gtts.generate_all(mock)
    print(res_gtts)
    
    print("\nTesting VOICEVOX...")
    n_vv = NarratorEngine(engine="voicevox")
    res_vv = n_vv.generate_all(mock)
    print(res_vv)
