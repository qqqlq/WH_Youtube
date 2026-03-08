import os
import time
import json
import requests
from pathlib import Path
from PIL import Image, ImageDraw
from dotenv import load_dotenv


class CollectorAgent:
    """Collects free-to-use images from stock photo APIs (Pexels, Unsplash, Pixabay)."""

    def __init__(self, assets_dir: str = "workspace/assets"):
        load_dotenv()
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        # API keys (Pexels is primary; others are optional fallbacks)
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")
        self.unsplash_key = os.getenv("UNSPLASH_API_KEY", "")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "")

        self._http = requests.Session()
        self._http.headers.update({
            "User-Agent": "AntigravityVideoAutomation/1.0"
        })

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def collect(self, query: str, scene_id: int):
        """Download an image for *query* and save it as scene_{scene_id:02d}.jpg."""
        print(f"  Collecting asset for Scene {scene_id}: {query}")

        image_path = self.assets_dir / f"scene_{scene_id:02d}.jpg"
        meta_path = self.assets_dir / f"scene_{scene_id:02d}_meta.json"

        # --- Check for manual override first ---
        manual_matches = list(self.assets_dir.glob(f"scene_{scene_id:02d}_manual.*"))
        if manual_matches:
            print(f"    Skipping automation: manual override found -> {manual_matches[0].name}")
            self._save_meta(meta_path, {
                "query": query,
                "scene_id": scene_id,
                "provider": "manual_upload",
                "photographer": "user",
                "source_url": "",
                "license": "user_provided",
                "timestamp": time.time(),
            })
            return

        result = None

        # --- Try each provider in order ---
        providers = [
            ("Pexels", self._search_pexels),
            ("Unsplash", self._search_unsplash),
            ("Pixabay", self._search_pixabay),
        ]

        for provider_name, search_fn in providers:
            try:
                result = search_fn(query)
                if result:
                    result["provider"] = provider_name
                    break
            except Exception as e:
                print(f"    [{provider_name}] Error: {e}")

        # --- Download or placeholder ---
        if result:
            ok = self._download_image(result["download_url"], image_path)
            if ok:
                metadata = {
                    "query": query,
                    "scene_id": scene_id,
                    "provider": result["provider"],
                    "photographer": result.get("photographer", "unknown"),
                    "source_url": result.get("source_url", ""),
                    "license": result.get("license", "free"),
                    "timestamp": time.time(),
                }
                self._save_meta(meta_path, metadata)
                print(f"    ✓ Saved {image_path.name}  (via {result['provider']})")
                return

        # All providers failed → placeholder
        print(f"    ✗ All providers failed for '{query}' — creating placeholder")
        self._save_placeholder(image_path, query)
        self._save_meta(meta_path, {"query": query, "error": "all_providers_failed"})

    # ------------------------------------------------------------------ #
    #  Pexels  (https://www.pexels.com/api/documentation/)
    # ------------------------------------------------------------------ #
    def _search_pexels(self, query: str) -> dict | None:
        if not self.pexels_key:
            return None

        resp = self._http.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": self.pexels_key},
            params={"query": query, "per_page": 5, "orientation": "portrait"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        photos = data.get("photos", [])
        if not photos:
            return None

        # Pick the first photo; prefer 'large2x' for high quality
        photo = photos[0]
        return {
            "download_url": photo["src"].get("large2x") or photo["src"]["original"],
            "photographer": photo.get("photographer", "unknown"),
            "source_url": photo.get("url", ""),
            "license": "Pexels License (free for commercial use)",
        }

    # ------------------------------------------------------------------ #
    #  Unsplash  (https://unsplash.com/documentation)
    # ------------------------------------------------------------------ #
    def _search_unsplash(self, query: str) -> dict | None:
        if not self.unsplash_key:
            return None

        resp = self._http.get(
            "https://api.unsplash.com/search/photos",
            headers={"Authorization": f"Client-ID {self.unsplash_key}"},
            params={"query": query, "per_page": 5, "orientation": "portrait"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return None

        photo = results[0]
        return {
            "download_url": photo["urls"].get("full") or photo["urls"]["regular"],
            "photographer": photo.get("user", {}).get("name", "unknown"),
            "source_url": photo.get("links", {}).get("html", ""),
            "license": "Unsplash License (free for commercial use)",
        }

    # ------------------------------------------------------------------ #
    #  Pixabay  (https://pixabay.com/api/docs/)
    # ------------------------------------------------------------------ #
    def _search_pixabay(self, query: str) -> dict | None:
        if not self.pixabay_key:
            return None

        resp = self._http.get(
            "https://pixabay.com/api/",
            params={
                "key": self.pixabay_key,
                "q": query,
                "per_page": 5,
                "image_type": "photo",
                "orientation": "vertical",
                "safesearch": "true",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            return None

        photo = hits[0]
        return {
            "download_url": photo.get("largeImageURL") or photo["webformatURL"],
            "photographer": photo.get("user", "unknown"),
            "source_url": photo.get("pageURL", ""),
            "license": "Pixabay License (free for commercial use)",
        }

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def _download_image(self, url: str, save_path: Path, retries: int = 3) -> bool:
        """Download *url* to *save_path* with retry logic."""
        for attempt in range(1, retries + 1):
            try:
                resp = self._http.get(url, timeout=30, stream=True)
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                # Quick sanity check — file should be > 10 KB for a real image
                if save_path.stat().st_size > 10_000:
                    return True
                print(f"    Attempt {attempt}: file too small ({save_path.stat().st_size} B)")
            except Exception as e:
                print(f"    Attempt {attempt}: download failed — {e}")
            time.sleep(1)
        return False

    @staticmethod
    def _save_placeholder(save_path: Path, text: str):
        img = Image.new("RGB", (1080, 1920), color=(50, 50, 50))
        d = ImageDraw.Draw(img)
        d.text((50, 960), f"IMAGE NOT FOUND:\n{text}", fill=(200, 200, 200))
        img.save(save_path)

    @staticmethod
    def _save_meta(path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    c = CollectorAgent()
    c.collect("Patagonia mountains landscape", 1)
