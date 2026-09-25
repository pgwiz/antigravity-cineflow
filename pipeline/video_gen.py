"""Veo Video Generation Engine with Last-Frame Extraction and Continuity Chaining."""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from config import settings
from pipeline.storyboard import Storyboard, Scene, SceneStatus

class VideoGenerationEngine:
    """Manages Google Veo API calls, asynchronous polling, downloading,
    and last-frame extraction for seamless scene chaining.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initializes google-genai client."""
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[VideoEngine] Error loading google-genai: {e}")
                self.client = None

    def extract_last_frame(self, video_path: Path, output_image_path: Path) -> bool:
        """Extracts the very last frame of a video using FFmpeg for chaining continuation."""
        if not video_path.exists():
            return False
        
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            settings.ffmpeg_binary,
            "-y",
            "-sseof", "-0.1",
            "-i", str(video_path),
            "-update", "1",
            "-frames:v", "1",
            str(output_image_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_image_path.exists()
        except Exception as e:
            print(f"[VideoEngine] Error extracting last frame from {video_path}: {e}")
            return False

    def generate_scene_clip(
        self,
        scene: Scene,
        output_dir: Path,
        aspect_ratio: str = "16:9",
        dry_run: bool = False,
    ) -> Path:
        """Generates a single scene clip using Google Veo or synthetic fallback."""
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_path = output_dir / f"scene_{scene.scene_number:02d}.mp4"
        last_frame_path = output_dir / f"scene_{scene.scene_number:02d}_last_frame.png"

        # Check if dry-run or client missing
        if dry_run or not self.client:
            print(f"[VideoEngine] Generating synthetic preview clip for Scene {scene.scene_number:02d}...")
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        scene.status = SceneStatus.GENERATING
        print(f"[VideoEngine] Dispatching Veo Generation for Scene {scene.scene_number:02d} ({scene.duration_seconds}s)...")
        print(f"  Prompt: {scene.visual_prompt[:90]}...")

        try:
            from google.genai.types import GenerateVideosConfig
            from PIL import Image

            # Prepare configuration
            config = GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                negative_prompt=scene.negative_prompt,
                durationSeconds=int(scene.duration_seconds),
            )

            # Determine if starting from a reference image (last-frame chain or character photo)
            image_input = None
            if scene.reference_image_path and Path(scene.reference_image_path).exists():
                print(f"  Using reference seed image: {scene.reference_image_path}")
                image_input = Image.open(scene.reference_image_path)

            # Call Veo model
            operation = self.client.models.generate_videos(
                model=settings.video_model,
                prompt=scene.visual_prompt,
                image=image_input,
                config=config,
            )

            # Poll for completion
            print("  Waiting for Veo GPU compute...")
            poll_interval = 10
            max_wait_seconds = 600
            elapsed = 0

            while not operation.done and elapsed < max_wait_seconds:
                time.sleep(poll_interval)
                elapsed += poll_interval
                operation = self.client.operations.get(operation)
                print(f"  Elapsed: {elapsed}s...")

            if not operation.done:
                raise TimeoutError(f"Video generation timed out after {max_wait_seconds}s")

            # Retrieve generated video
            generated_video = operation.response.generated_videos[0]
            self.client.files.download(file=generated_video.video)
            generated_video.video.save(str(clip_path))
            print(f"[VideoEngine] Successfully saved: {clip_path.name}")

            # Extract last frame for smooth continuation chaining
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        except Exception as e:
            print(f"[VideoEngine] Veo generation error on Scene {scene.scene_number:02d}: {e}")
            scene.status = SceneStatus.FAILED
            scene.error_message = str(e)
            # Fall back to synthetic clip so pipeline doesn't break
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            return clip_path

    def _generate_synthetic_clip(self, scene: Scene, output_path: Path, aspect_ratio: str):
        """Generates an unmistakable animated test pattern with audio tone so previews are NEVER blank."""
        width, height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)
        dur = scene.duration_seconds

        # Animated SMPTE test pattern + countdown timer to make it visually obvious it is a test preview
        cmd = [
            settings.ffmpeg_binary,
            "-y",
            "-f", "lavfi",
            "-i", f"smptebars=size={width}x{height}:rate=24:duration={dur}",
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={dur}",
            "-filter_complex", (
                f"[0:v]boxblur=luma_radius=2:luma_power=1[vbg];"
                f"[1:a]volume=0.05[aout]"
            ),
            "-map", "[vbg]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception:
            # Fallback test pattern
            simple_cmd = [
                settings.ffmpeg_binary,
                "-y",
                "-f", "lavfi",
                "-i", f"testsrc=size={width}x{height}:rate=24:duration={dur}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
            subprocess.run(simple_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def generate_all_scenes(
        self,
        storyboard: Storyboard,
        output_dir: Path,
        dry_run: bool = False,
    ):
        """Iterates through storyboard scenes, managing last-frame propagation for continuous shots."""
        output_dir.mkdir(parents=True, exist_ok=True)
        scenes_dir = output_dir / "scenes"
        scenes_dir.mkdir(exist_ok=True)

        for i, scene in enumerate(storyboard.scenes):
            # Check if this scene should be chained from the previous scene's last frame
            if scene.chain_from_previous_last_frame and i > 0:
                prev_scene = storyboard.scenes[i - 1]
                if prev_scene.last_frame_path and Path(prev_scene.last_frame_path).exists():
                    print(f"[VideoEngine] 🔗 Chaining Scene {scene.scene_number:02d} from Scene {prev_scene.scene_number:02d} last frame")
                    scene.reference_image_path = prev_scene.last_frame_path

            self.generate_scene_clip(
                scene=scene,
                output_dir=scenes_dir,
                aspect_ratio=storyboard.aspect_ratio,
                dry_run=dry_run,
            )
