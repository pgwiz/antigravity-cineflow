"""Gemini Omni 1.1 Flash Video Client & Interactions API Integration.

Directly integrates Google Gemini's Omni 1.1 Flash model (gemini-omni-1.1-flash)
for text-to-video, first-frame continuation, first-and-last frame transitions,
character reference consistency, video extension, and multi-resolution rendering (360p-4k).
Interfaces with the installed skill at ~/.gemini/config/skills/gemini-omni-flash-api/.
"""

import os
import re
import sys
import json
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from config import settings


VALID_RESOLUTIONS = {"360p", "720p", "1080p", "4k"}


def sanitize_omni_prompt(prompt: str) -> str:
    """Cleans whitespace and ensures prompt is safe for video generation."""
    if not prompt:
        return ""
    return re.sub(r"\s+", " ", prompt).strip()


class GeminiOmniFlashClient:
    """Client for Gemini Omni 1.1 Flash video generation using the Google GenAI Interactions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        resolution: Optional[str] = None,
        timeout: Optional[int] = None,
        skill_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or getattr(settings, "omni_model", "gemini-omni-1.1-flash")
        self.resolution = (resolution or getattr(settings, "omni_resolution", "720p")).lower()
        self.timeout = timeout or getattr(settings, "omni_timeout", 600)
        self.skill_dir = skill_dir or getattr(
            settings,
            "omni_skill_dir",
            Path(r"C:\Users\pgwiz\.gemini\config\skills\gemini-omni-flash-api"),
        )
        self._genai_client = None

    @property
    def is_configured(self) -> bool:
        """Returns True if a GEMINI_API_KEY is available."""
        return bool(self.api_key and self.api_key.strip())

    @property
    def is_skill_available(self) -> bool:
        """Returns True if the installed gemini-omni-flash-api skill scripts exist."""
        script_path = self.skill_dir / "scripts" / "video" / "generate_video.py"
        return script_path.exists() and script_path.is_file()

    def _get_genai_client(self):
        """Lazy initializer for google-genai client."""
        if self._genai_client is None and self.is_configured:
            try:
                from google import genai
                from google.genai import types
                self._genai_client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=self.timeout * 1000),
                )
            except Exception as e:
                print(f"[OmniClient] Warning: Failed to initialize genai.Client: {e}")
                self._genai_client = None
        return self._genai_client

    def validate_resolution(self, res: Optional[str]) -> str:
        """Validates and normalizes resolution to 360p, 720p, 1080p, or 4k."""
        if not res:
            return self.resolution
        clean = res.strip().lower()
        if clean in VALID_RESOLUTIONS:
            return clean
        return "720p"

    def format_omni_prompt(
        self,
        base_prompt: str,
        unbroken_shot: bool = True,
        sound_cues: Optional[List[str]] = None,
        first_frame: Optional[Path] = None,
        last_frame: Optional[Path] = None,
        ref_images: Optional[List[Path]] = None,
    ) -> str:
        """Formats prompt adhering to Omni Flash's best practices:
        - Injects unbroken single shot rule to avoid random AI cuts.
        - Injects sound design directives if cues provided.
        - Adds role tags (<FIRST_FRAME>, <LAST_FRAME>, <IMAGE_REF_N>) if needed.
        """
        parts = []

        if unbroken_shot and "unbroken" not in base_prompt.lower() and "continuous shot" not in base_prompt.lower():
            parts.append("In a single unbroken scene, continuous shot, no scene cuts.")

        # Role declarations
        if first_frame and last_frame:
            if "<FIRST_FRAME>" not in base_prompt and "<LAST_FRAME>" not in base_prompt:
                parts.append("<FIRST_FRAME> <LAST_FRAME>")
        elif first_frame:
            if "<FIRST_FRAME>" not in base_prompt:
                parts.append("<FIRST_FRAME>")

        if ref_images:
            for idx in range(len(ref_images)):
                tag = f"<IMAGE_REF_{idx}>"
                if tag not in base_prompt:
                    parts.append(f"in the style of {tag}")

        parts.append(sanitize_omni_prompt(base_prompt))

        if sound_cues:
            clean_cues = ", ".join(c.replace("SOUND (O.S.):", "").strip() for c in sound_cues if c.strip())
            if clean_cues and "sound design" not in base_prompt.lower():
                parts.append(f"Sound design: {clean_cues}. No dialogue.")

        return " ".join(parts).strip()

    def generate_video(
        self,
        prompt: str,
        output_file: Path,
        first_frame_path: Optional[Path] = None,
        last_frame_path: Optional[Path] = None,
        reference_images: Optional[List[Path]] = None,
        reference_videos: Optional[List[Path]] = None,
        extend_video_path: Optional[Path] = None,
        aspect_ratio: str = "16:9",
        duration: Optional[int] = 8,
        resolution: Optional[str] = None,
        strip_audio: bool = False,
        unbroken_shot: bool = True,
        sound_cues: Optional[List[str]] = None,
    ) -> bool:
        """Generates a video clip using Gemini Omni 1.1 Flash.
        Tries direct SDK Interactions API first, with graceful fallback to skill CLI script.
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        res = self.validate_resolution(resolution)
        clean_aspect = "9:16" if (aspect_ratio or "").strip().lower() in ["9:16", "9/16", "portrait", "vertical"] else "16:9"
        duration_s = max(3, min(10, int(duration or 8)))

        formatted_prompt = self.format_omni_prompt(
            base_prompt=prompt,
            unbroken_shot=unbroken_shot,
            sound_cues=sound_cues,
            first_frame=first_frame_path,
            last_frame=last_frame_path,
            ref_images=reference_images,
        )

        print(f"[OmniClient] Preparing Omni Flash Video Generation:")
        print(f"  Model: {self.model} | Resolution: {res} | Aspect: {clean_aspect} | Duration: {duration_s}s")
        print(f"  Prompt: {formatted_prompt[:120]}...")

        # Strategy 1: Direct SDK Interactions API
        client = self._get_genai_client()
        if client is not None:
            try:
                input_parts = []

                # 1. First Frame (<FIRST_FRAME>)
                if first_frame_path and Path(first_frame_path).exists():
                    print(f"  [OmniClient] Uploading first frame: {first_frame_path.name}")
                    f1 = client.files.upload(file=str(first_frame_path))
                    input_parts.append({
                        "type": "image",
                        "uri": f1.uri,
                        "mime_type": getattr(f1, "mime_type", "image/png"),
                    })

                # 2. Last Frame (<LAST_FRAME>)
                if last_frame_path and Path(last_frame_path).exists():
                    print(f"  [OmniClient] Uploading last frame: {last_frame_path.name}")
                    f2 = client.files.upload(file=str(last_frame_path))
                    input_parts.append({
                        "type": "image",
                        "uri": f2.uri,
                        "mime_type": getattr(f2, "mime_type", "image/png"),
                    })

                # 3. Reference Images (<IMAGE_REF_0>, ...)
                if reference_images:
                    for img_p in reference_images:
                        if Path(img_p).exists():
                            print(f"  [OmniClient] Uploading reference image: {img_p.name}")
                            ref_f = client.files.upload(file=str(img_p))
                            input_parts.append({
                                "type": "image",
                                "uri": ref_f.uri,
                                "mime_type": getattr(ref_f, "mime_type", "image/png"),
                            })

                # 4. Source Video to extend
                if extend_video_path and Path(extend_video_path).exists():
                    print(f"  [OmniClient] Uploading source video to extend: {extend_video_path.name}")
                    ext_f = client.files.upload(file=str(extend_video_path))
                    input_parts.append({
                        "type": "video",
                        "uri": ext_f.uri,
                        "mime_type": getattr(ext_f, "mime_type", "video/mp4"),
                    })

                # 5. Text prompt
                input_parts.append({
                    "type": "text",
                    "text": formatted_prompt,
                })

                video_config = {
                    "type": "video",
                    "delivery": "uri",
                    "aspect_ratio": clean_aspect,
                    "duration": f"{duration_s}s",
                    "resolution": res,
                }

                print("  [OmniClient] Sending request to interactions.create...")
                interaction = client.interactions.create(
                    model=self.model,
                    input=input_parts,
                    response_format=video_config,
                )

                if getattr(interaction, "output_video", None) and getattr(interaction.output_video, "uri", None):
                    video_uri = interaction.output_video.uri
                    print(f"  [OmniClient] Generation success! Downloading {video_uri[:60]}...")
                    raw_bytes = client.files.download(file=video_uri)
                    with open(output_file, "wb") as f:
                        f.write(raw_bytes)

                    if output_file.exists() and output_file.stat().st_size > 0:
                        print(f"  [OmniClient] Saved video to {output_file} ({output_file.stat().st_size} bytes)")
                        return True

            except Exception as e:
                print(f"[OmniClient] Direct SDK Interactions API failed: {e}")

        # Strategy 2: Installed Skill CLI Script
        if self.is_skill_available:
            script_path = self.skill_dir / "scripts" / "video" / "generate_video.py"
            print(f"[OmniClient] Falling back to installed skill CLI: {script_path.name}")
            cmd = [
                sys.executable,
                str(script_path),
                formatted_prompt,
                "--output", str(output_file),
                "--aspect-ratio", clean_aspect,
                "--duration", str(duration_s),
                "--resolution", res,
                "--model", self.model,
                "--timeout", str(self.timeout),
            ]
            if first_frame_path and Path(first_frame_path).exists():
                cmd.extend(["--first-frame", str(first_frame_path)])
            if last_frame_path and Path(last_frame_path).exists():
                cmd.extend(["--last-frame", str(last_frame_path)])
            if reference_images:
                for img_p in reference_images:
                    if Path(img_p).exists():
                        cmd.extend(["--image", str(img_p)])
            if extend_video_path and Path(extend_video_path).exists():
                cmd.extend(["--extend", str(extend_video_path)])
            if strip_audio:
                cmd.append("--strip-audio")

            try:
                env = os.environ.copy()
                if self.api_key:
                    env["GEMINI_API_KEY"] = self.api_key
                res_proc = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=self.timeout)
                if res_proc.returncode == 0 and output_file.exists() and output_file.stat().st_size > 0:
                    print(f"[OmniClient] Video successfully generated via skill CLI!")
                    return True
                else:
                    print(f"[OmniClient] Skill CLI failed (code {res_proc.returncode}): {res_proc.stderr[:200]}")
            except Exception as e:
                print(f"[OmniClient] Error running skill CLI: {e}")

        return False

    def generate_scene(
        self,
        scene: Any,
        output_file: Path,
        start_frame: Optional[Path] = None,
        last_frame: Optional[Path] = None,
        character_reference_images: Optional[List[Path]] = None,
        aspect_ratio: str = "16:9",
        resolution: Optional[str] = None,
    ) -> bool:
        """High-level generator for a CineFlow Storyboard Scene."""
        # Extract sound cues from screenplay / scene if present
        sound_cues = getattr(scene, "sound_cues", None)
        prompt = getattr(scene, "visual_prompt", "") or getattr(scene, "action_description", "")
        duration = int(getattr(scene, "duration_seconds", 8))

        return self.generate_video(
            prompt=prompt,
            output_file=output_file,
            first_frame_path=start_frame,
            last_frame_path=last_frame,
            reference_images=character_reference_images,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution or self.resolution,
            unbroken_shot=True,
            sound_cues=sound_cues,
        )

    def inspect_video(self, video_path: Path) -> Dict[str, Any]:
        """Inspects video metadata (duration, resolution, fps, audio) via skill's inspect_video.py or ffprobe."""
        inspect_script = self.skill_dir / "scripts" / "video" / "inspect_video.py"
        if inspect_script.exists():
            cmd = [sys.executable, str(inspect_script), str(video_path), "--json"]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                if proc.returncode == 0:
                    return json.loads(proc.stdout)
            except Exception:
                pass

        # Fallback to direct ffprobe
        cmd = [
            settings.ffprobe_binary,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            if proc.returncode == 0:
                data = json.loads(proc.stdout)
                duration = float(data.get("format", {}).get("duration", 0.0))
                video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
                has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
                return {
                    "duration": duration,
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "has_audio": has_audio,
                    "codec": video_stream.get("codec_name"),
                }
        except Exception as e:
            return {"error": str(e)}

        return {}
