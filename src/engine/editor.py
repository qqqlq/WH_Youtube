import os
import json
from pathlib import Path
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip, VideoClip, VideoFileClip,
    concatenate_videoclips, CompositeAudioClip,
    afx, vfx
)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import random


# ── Canvas constants (YouTube Shorts = 9:16) ──
CANVAS_W = 1080
CANVAS_H = 1920


class EditorEngine:
    def __init__(self, assets_dir="workspace/assets", output_dir="workspace/outputs"):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._font = self._load_font()
        # Global audio assets directory (shared across all projects)
        self.global_assets = Path("workspace/assets")
        self._audio_catalog = self._load_audio_catalog()

    def _load_audio_catalog(self) -> dict:
        """Load audio_catalog.json that maps keywords to real filenames."""
        catalog_path = self.global_assets / "audio_catalog.json"
        if catalog_path.exists():
            import json
            with open(catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"bgm": {}, "se": {}}

    def _resolve_bgm(self, keyword: str) -> Path | None:
        """Resolve a BGM keyword to an actual file path using the catalog."""
        bgm_dir = self.global_assets / "bgm"
        # 1. Check catalog mapping
        filename = self._audio_catalog.get("bgm", {}).get(keyword)
        if filename:
            p = bgm_dir / filename
            if p.exists():
                return p
        # 2. Fallback: try keyword.mp3 directly
        p = bgm_dir / f"{keyword}.mp3"
        if p.exists():
            return p
        # 3. Fallback: pick the first mp3 in the bgm dir
        if bgm_dir.exists():
            mp3s = list(bgm_dir.glob("*.mp3"))
            if mp3s:
                print(f"  BGM fallback: using {mp3s[0].name}")
                return mp3s[0]
        return None

    def _resolve_se(self, keyword: str) -> Path | None:
        """Resolve an SE keyword to an actual file path using the catalog."""
        se_dir = self.global_assets / "se"
        # 1. Check catalog mapping
        filename = self._audio_catalog.get("se", {}).get(keyword)
        if filename:
            p = se_dir / filename
            if p.exists():
                return p
        # 2. Fallback: try keyword.mp3 directly
        p = se_dir / f"{keyword}.mp3"
        if p.exists():
            return p
        return None

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

    @staticmethod
    def _load_font_bold(size: int = 72) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Load a bold Japanese font for telop/subtitles."""
        candidates = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/google-noto-cjk/NotoSansCJKjp-Bold.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
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
    #  Animation
    # ------------------------------------------------------------------ #
    def _apply_ken_burns(self, pil_img: Image.Image, duration: float) -> VideoClip:
        """Applies a random Ken Burns effect (zoom/pan) to a PIL Image."""
        w, h = pil_img.size
        # zoom in/out by 10%
        zoom_factor = 0.10
        mode = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
        
        def make_frame(t):
            progress = t / max(duration, 0.1)
            if progress > 1.0: progress = 1.0
            
            if mode == "zoom_in":
                # scale shrinks from 1.0 to 0.9 (zoom in effect)
                scale = 1.0 - (zoom_factor * progress)
                cw, ch = int(w * scale), int(h * scale)
                x = (w - cw) // 2
                y = (h - ch) // 2
            elif mode == "zoom_out":
                scale = (1.0 - zoom_factor) + (zoom_factor * progress)
                cw, ch = int(w * scale), int(h * scale)
                x = (w - cw) // 2
                y = (h - ch) // 2
            elif mode == "pan_left":
                scale = 1.0 - zoom_factor
                cw, ch = int(w * scale), int(h * scale)
                max_x = w - cw
                x = int(max_x * (1.0 - progress))
                y = (h - ch) // 2
            else: # pan_right
                scale = 1.0 - zoom_factor
                cw, ch = int(w * scale), int(h * scale)
                max_x = w - cw
                x = int(max_x * progress)
                y = (h - ch) // 2
                
            crop_box = (x, y, x + cw, y + ch)
            res_img = pil_img.crop(crop_box).resize((w, h), Image.Resampling.BICUBIC)
            return np.array(res_img)
            
        return VideoClip(make_frame, duration=duration)

    # ------------------------------------------------------------------ #
    #  Text overlay
    # ------------------------------------------------------------------ #
    def _create_text_overlay(self, text: str, size=(CANVAS_W, CANVAS_H)) -> np.ndarray:
        """
        Create RGBA text image for overlay.
        YouTube Shorts style: white bold text with black outline.
        Words wrapped in **double asterisks** are rendered in accent color (yellow).
        """
        import re

        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._load_font_bold(52)

        COLOR_NORMAL = (255, 255, 255, 255)
        COLOR_HIGHLIGHT = (255, 230, 50, 255)   # Yellow accent
        COLOR_OUTLINE = (0, 0, 0, 220)
        outline_width = 4

        # Parse **highlight** markers into segments: [(text, is_highlight), ...]
        segments = []
        pattern = re.compile(r'\*\*(.+?)\*\*')
        last_end = 0
        for m in pattern.finditer(text):
            if m.start() > last_end:
                segments.append((text[last_end:m.start()], False))
            segments.append((m.group(1), True))
            last_end = m.end()
        if last_end < len(text):
            segments.append((text[last_end:], False))
        if not segments:
            segments = [(text, False)]

        # Build plain text (no markers) for layout measurement
        plain = "".join(s[0] for s in segments)

        # Word-wrap
        max_chars = 16
        lines_raw = []
        while plain:
            lines_raw.append(plain[:max_chars])
            plain = plain[max_chars:]

        # Measure total block height for vertical centering
        line_height = font.size + 12  # approx line spacing
        total_h = line_height * len(lines_raw)
        base_y = int(size[1] * 0.68) - total_h // 2

        # Flatten segments into a char-level color list
        char_colors = []
        for seg_text, is_hl in segments:
            for ch in seg_text:
                char_colors.append(COLOR_HIGHLIGHT if is_hl else COLOR_NORMAL)

        # Draw line by line
        char_idx = 0
        for line_num, line_text in enumerate(lines_raw):
            # Center this line horizontally
            line_bbox = draw.textbbox((0, 0), line_text, font=font)
            line_w = line_bbox[2] - line_bbox[0]
            cx = (size[0] - line_w) // 2
            cy = base_y + line_num * line_height

            # Draw each character with its color (using stroke_width for fast outline)
            cur_x = cx
            for ch in line_text:
                color = char_colors[char_idx] if char_idx < len(char_colors) else COLOR_NORMAL
                draw.text((cur_x, cy), ch, font=font, fill=color,
                          stroke_width=outline_width, stroke_fill=COLOR_OUTLINE)
                # Advance x
                ch_bbox = draw.textbbox((0, 0), ch, font=font)
                cur_x += ch_bbox[2] - ch_bbox[0]
                char_idx += 1

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
        
        # Audio tracks: [0] BGM, [1] Narration, [2] SE
        audio_clips = []
        current_time = 0.0

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

            # ── Image / Video ──
            manual_matches = list(self.assets_dir.glob(f"scene_{scene_id:02d}_manual.*"))
            if manual_matches:
                img_path = manual_matches[0]
                print(f"  Using manual override media: {img_path}")
            else:
                vid_path = self.assets_dir / f"scene_{scene_id:02d}.mp4"
                jpg_path = self.assets_dir / f"scene_{scene_id:02d}.jpg"
                img_path = vid_path if vid_path.exists() else jpg_path

            if img_path.suffix.lower() == ".mp4":
                print(f"  Using video asset: {img_path}")
                vid = VideoFileClip(str(img_path))
                # Loop if shorter than duration, else subclip
                if vid.duration and vid.duration < duration:
                    vid = vid.with_effects([vfx.Loop(duration=duration)])
                else:
                    vid = vid.subclipped(0, duration)
                # Resize and crop to fill CANVAS
                w, h = vid.size
                if w / h > CANVAS_W / CANVAS_H: # Wider
                    vid = vid.resized(height=CANVAS_H)
                    nw, nh = vid.size
                    vid = vid.cropped(x_center=nw/2, y_center=nh/2, width=CANVAS_W, height=CANVAS_H)
                else: # Taller or exact
                    vid = vid.resized(width=CANVAS_W)
                    nw, nh = vid.size
                    vid = vid.cropped(x_center=nw/2, y_center=nh/2, width=CANVAS_W, height=CANVAS_H)
                
                # Strip original audio from B-roll
                img_clip = vid.without_audio()
            else:
                if img_path.exists():
                    pil_img = self._prepare_image(img_path)
                else:
                    print(f"  Warning: {img_path} not found, using black placeholder")
                    pil_img = Image.new("RGB", (CANVAS_W, CANVAS_H), color="black")
                img_clip = self._apply_ken_burns(pil_img, duration)

            # ── Overlay Image ──
            overlay_clips = []
            overlay_keyword = scene.get("overlay_image_keyword", "")
            if overlay_keyword:
                overlay_path = self.assets_dir / "overlays" / f"{overlay_keyword}.png"
                if overlay_path.exists():
                    try:
                        ov_img = ImageClip(str(overlay_path)).with_duration(duration)
                        # Resize width to 450px max
                        w, h = ov_img.size
                        if w > 450:
                            ov_img = ov_img.with_effects([vfx.Resize(width=450)])
                        # Apply a simple slide-in from bottom effect or just position it
                        # For now, position at bottom-right (above the telop)
                        # The telop base is at 68% height. Image height is approx up to 500px.
                        ov_img = ov_img.with_position(("center", 0.45), relative=True)
                        overlay_clips.append(ov_img)
                    except Exception as e:
                        print(f"  Warning: Failed to load overlay {overlay_path}: {e}")
                else:
                    print(f"  Warning: Overlay image '{overlay_path}' not found.")

            # ── Telop (short overlay text) ──
            telop_text = scene.get("overlay_text", "")
            if telop_text:
                overlay_arr = self._create_text_overlay(telop_text)
                telop_clip = ImageClip(overlay_arr).with_duration(duration)
                overlay_clips.append(telop_clip)

            if overlay_clips:
                composite = CompositeVideoClip([img_clip] + overlay_clips)
            else:
                composite = img_clip

            # ── Audio Compositing Preparation ──
            scene_audio_clips = []

            # 1. Narration audio
            if nar_info and nar_info["path"].exists():
                audio = AudioFileClip(str(nar_info["path"]))
                scene_audio_clips.append(audio.with_start(current_time))
                composite = composite.with_audio(audio) # Keep it on the clip for safety or mix it later
            
            # 2. Sound Effect
            se_keyword = scene.get("sound_effect", "")
            if se_keyword:
                se_path = self._resolve_se(se_keyword)
                if se_path and se_path.exists():
                    se_audio = AudioFileClip(str(se_path)).with_start(current_time).with_effects([afx.MultiplyVolume(0.8)])
                    scene_audio_clips.append(se_audio)
                else:
                    print(f"  Warning: SE '{se_keyword}' not found.")

            audio_clips.extend(scene_audio_clips)

            # ── Transition (Crossfade) ──
            # Apply a 0.5s crossfade-in to all clips except the first
            if len(clips) > 0:
                composite = composite.with_effects([vfx.CrossFadeIn(0.5)])
                # When crossfading by 0.5s, the actual start time of the next clip overlaps
                current_time += (duration - 0.5)
            else:
                current_time += duration

            clips.append(composite)

        if not clips:
            print("No clips to render.")
            return None

        # Concatenate all scenes (with overlapping for crossfade)
        final = concatenate_videoclips(clips, method="compose", padding=-0.5)

        # ── Global BGM ──
        bgm_keyword = script_data.get("bgm_keyword", "lofi")
        bgm_path = self._resolve_bgm(bgm_keyword)
        
        if bgm_path and bgm_path.exists():
            print(f"Applying BGM: {bgm_keyword} -> {bgm_path}")
            bgm = AudioFileClip(str(bgm_path)).with_effects([afx.AudioLoop(duration=final.duration), afx.MultiplyVolume(0.15)])
            audio_clips.insert(0, bgm)
        else:
            print(f"Warning: BGM for keyword '{bgm_keyword}' not found.")

        # If we collected discrete audio tracks, mix them
        if audio_clips:
            # MoviePy 2: final.audio already contains the narration from concatenate_videoclips 
            # if we attached it to the ImageClips. We overwrite it with a full mix.
            mixed_audio = CompositeAudioClip(audio_clips)
            final = final.with_audio(mixed_audio)

        output_path = self.output_dir / output_filename
        final.write_videofile(
            str(output_path),
            fps=15,
            codec="libx264",
            audio_codec="aac",
            threads=6,
            preset="fast",
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
