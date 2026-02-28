import os
import json
from pathlib import Path
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip,
)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np


# ── Canvas constants (YouTube Shorts = 9:16) ──
CANVAS_W = 1080
CANVAS_H = 1920


class EditorEngine:
    def __init__(self, assets_dir="workspace/assets", output_dir="workspace/outputs"):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._font = self._load_font()

    # ------------------------------------------------------------------ #
    #  Image pre-processing  (fixes the tiling / wrapping issue)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _prepare_image(img_path: Path, tw: int = CANVAS_W, th: int = CANVAS_H) -> Image.Image:
        """
        Resize & crop an image to exactly (tw x th) using a
        blurred-background + center-fit compositing approach.

        1. Create a blurred, darkened version filling the full canvas.
        2. Resize the original with aspect-ratio preserved (fit inside).
        3. Paste the sharp image centered on the blurred background.
        """
        src = Image.open(img_path).convert("RGB")
        src_w, src_h = src.size

        # ── Background: blurred + darkened ──
        bg = src.resize((tw, th), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
        # Darken slightly for contrast
        from PIL import ImageEnhance
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        # ── Foreground: fit inside canvas, keep aspect ratio ──
        scale = min(tw / src_w, th / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        fg = src.resize((new_w, new_h), Image.LANCZOS)

        # Center-paste
        x_off = (tw - new_w) // 2
        y_off = (th - new_h) // 2
        bg.paste(fg, (x_off, y_off))

        return bg

    # ------------------------------------------------------------------ #
    #  Font loading (Japanese support)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_font(size: int = 64) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Try to load a Japanese-capable font, fallback to default."""
        candidates = [
            # Linux
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/google-noto-cjk/NotoSansCJKjp-Bold.otf",
            # macOS
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            # Windows
            "C:/Windows/Fonts/msgothic.ttc",
            "C:/Windows/Fonts/meiryo.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    # ------------------------------------------------------------------ #
    #  Text overlay
    # ------------------------------------------------------------------ #
    def _create_text_overlay(self, text: str, size=(CANVAS_W, CANVAS_H)) -> np.ndarray:
        """Create RGBA text image for overlay (bottom-center subtitle)."""
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Word-wrap for long text
        max_chars_per_line = 14
        lines = []
        while text:
            lines.append(text[:max_chars_per_line])
            text = text[max_chars_per_line:]

        wrapped = "\n".join(lines)

        # Position near bottom
        bbox = draw.textbbox((0, 0), wrapped, font=self._font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size[0] - text_w) // 2
        y = size[1] - text_h - 200

        # Semi-transparent background bar
        pad = 20
        draw.rectangle(
            [x - pad, y - pad, x + text_w + pad, y + text_h + pad],
            fill=(0, 0, 0, 160),
        )

        # Shadow + text
        draw.text((x + 2, y + 2), wrapped, font=self._font, fill=(0, 0, 0, 200))
        draw.text((x, y), wrapped, font=self._font, fill="white")

        return np.array(img)

    # ------------------------------------------------------------------ #
    #  Main render
    # ------------------------------------------------------------------ #
    def render_video(
        self,
        script_data: dict,
        output_filename: str = "final.mp4",
        narration_map: dict | None = None,
    ) -> str | None:
        """
        Render the final video.

        Args:
            script_data: The script JSON (with scenes list).
            output_filename: Name of the output file.
            narration_map: Optional dict from scene_id -> {"path", "duration"}.
        """
        print("Starting video rendering...")
        narration_map = narration_map or {}
        clips = []

        for scene in script_data.get("scenes", []):
            scene_id = scene.get("id")
            base_duration = scene.get("duration", 5)
            overlay_text = scene.get("overlay_text", "")

            # Duration: use narration length if available (with 0.5s padding)
            nar_info = narration_map.get(scene_id)
            if nar_info:
                duration = max(base_duration, nar_info["duration"] + 0.5)
            else:
                duration = base_duration

            # ── Image ──
            img_path = self.assets_dir / f"scene_{scene_id:02d}.jpg"
            if img_path.exists():
                pil_img = self._prepare_image(img_path)
            else:
                print(f"  Warning: {img_path} not found, using black placeholder")
                pil_img = Image.new("RGB", (CANVAS_W, CANVAS_H), color="black")

            img_clip = ImageClip(np.array(pil_img)).with_duration(duration)

            # ── Text overlay ──
            layer_clips = [img_clip]
            if overlay_text:
                txt_arr = self._create_text_overlay(overlay_text)
                txt_clip = ImageClip(txt_arr).with_duration(duration)
                layer_clips.append(txt_clip)

            composite = CompositeVideoClip(layer_clips, size=(CANVAS_W, CANVAS_H))
            composite = composite.with_duration(duration)

            # ── Narration audio ──
            if nar_info and nar_info["path"].exists():
                audio = AudioFileClip(str(nar_info["path"]))
                composite = composite.with_audio(audio)

            clips.append(composite)

        if not clips:
            print("No clips to render.")
            return None

        # Concatenate all scenes
        final = concatenate_videoclips(clips, method="compose")

        output_path = self.output_dir / output_filename
        final.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
        )
        print(f"Video saved to: {output_path}")
        return str(output_path)


if __name__ == "__main__":
    # Quick test with dummy images
    from PIL import Image as PILImage
    Path("workspace/assets").mkdir(parents=True, exist_ok=True)
    PILImage.new("RGB", (1920, 1080), color="red").save("workspace/assets/scene_01.jpg")
    PILImage.new("RGB", (1920, 1080), color="blue").save("workspace/assets/scene_02.jpg")

    editor = EditorEngine()
    mock_script = {
        "scenes": [
            {"id": 1, "duration": 3, "overlay_text": "テストシーン1"},
            {"id": 2, "duration": 3, "overlay_text": "テストシーン2"},
        ]
    }
    editor.render_video(mock_script, "test_render.mp4")
