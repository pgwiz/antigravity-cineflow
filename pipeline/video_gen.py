"""Google Flow / Veo Video Generation Engine with Last-Frame Extraction and Continuity Chaining.

Supports:
1. useapi.net Google Flow API v1 (Veo 3.1 Fast, Quality, Lite, and Omni 1.1 Flash)
   Docs: https://useapi.net/docs/api-google-flow-v1
2. Google GenAI SDK (models/veo-3.1-generate-preview)
"""

import os
import time
import base64
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import quote

import requests
from config import settings
from pipeline.storyboard import Storyboard, Scene, SceneStatus


class UseApiGoogleFlowClient:
    """Client for useapi.net Google Flow API v1 (Veo 3.1 & Omni 1.1 Flash).
    Official documentation: https://useapi.net/docs/api-google-flow-v1
    """

    def __init__(self, api_token: Optional[str] = None, base_url: Optional[str] = None):
        self.api_token = api_token or settings.useapi_token
        self.base_url = (base_url or settings.useapi_base_url).rstrip("/")
        self.email = settings.useapi_account_email

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid USEAPI_TOKEN is provided."""
        return bool(self.api_token and self.api_token.strip())

    def _headers(self, content_type: Optional[str] = "application/json") -> Dict[str, str]:
        token = (self.api_token or "").strip()
        headers = {"Authorization": f"Bearer {token}"}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def upload_asset(self, file_path: Path, content_type: Optional[str] = None) -> Optional[str]:
        """Uploads an image or video asset to Google Flow and returns its mediaGenerationId.
        Supports PNG, JPEG, WebP (up to 20MB) and MP4 (up to 100MB).
        Reference: https://useapi.net/docs/api-google-flow-v1/post-google-flow-assets-email.html
        """
        if not file_path.exists() or not file_path.is_file():
            print(f"[UseApiClient] Asset file not found or is a directory: {file_path}")
            return None

        file_size = file_path.stat().st_size
        if file_size == 0:
            print(f"[UseApiClient] Asset file is empty: {file_path}")
            return None

        is_video = file_path.suffix.lower() == ".mp4"
        max_size = 100 * 1024 * 1024 if is_video else 20 * 1024 * 1024
        if file_size > max_size:
            max_mb = 100 if is_video else 20
            print(f"[UseApiClient] Asset file exceeds {max_mb}MB limit: {file_path}")
            return None

        if not self.is_configured:
            print("[UseApiClient] USEAPI_TOKEN not configured for asset upload.")
            return None

        # Determine MIME type
        if not content_type:
            ext = file_path.suffix.lower()
            if ext == ".png":
                content_type = "image/png"
            elif ext in [".jpg", ".jpeg"]:
                content_type = "image/jpeg"
            elif ext == ".webp":
                content_type = "image/webp"
            elif ext == ".mp4":
                content_type = "video/mp4"
            else:
                content_type = "application/octet-stream"

        endpoint = f"{self.base_url}/assets/{quote(self.email)}" if self.email else f"{self.base_url}/assets"

        try:
            with open(file_path, "rb") as f:
                data = f.read()

            headers = self._headers(content_type=content_type)
            print(f"[UseApiClient] Uploading asset ({len(data)} bytes, {content_type}) to {endpoint}...")
            resp = requests.post(endpoint, headers=headers, data=data, timeout=60)

            if resp.status_code not in [200, 201]:
                print(f"[UseApiClient] Asset upload failed [{resp.status_code}]: {resp.text}")
                return None

            res_json = resp.json()
            # Response format: {"mediaGenerationId": {"mediaGenerationId": "user:...-image:..."}} or string
            gen_id = res_json.get("mediaGenerationId")
            if isinstance(gen_id, dict):
                mid = gen_id.get("mediaGenerationId")
            elif isinstance(gen_id, str):
                mid = gen_id
            else:
                mid = None

            print(f"[UseApiClient] Asset uploaded successfully. mediaGenerationId: {mid}")
            return mid

        except Exception as e:
            print(f"[UseApiClient] Exception uploading asset: {e}")
            return None

    def create_character(
        self,
        display_name: str,
        image_generation_ids: List[str],
        personality_notes: str = "",
        voice_ref: Optional[str] = None,
    ) -> Optional[str]:
        """Creates a persistent character entity on Google Flow.
        Reference: https://useapi.net/docs/api-google-flow-v1/post-google-flow-characters.html
        Returns the character reference string (e.g. 'user:...-character:...-imgs:1').
        """
        if not self.is_configured or not image_generation_ids:
            return None

        endpoint = f"{self.base_url}/characters"
        body: Dict[str, Any] = {
            "displayName": display_name,
            "imageReference_1": image_generation_ids[0],
            "personalityNotes": personality_notes[:2000],
        }
        if self.email:
            body["email"] = self.email
        if len(image_generation_ids) > 1:
            body["imageReference_2"] = image_generation_ids[1]
        if voice_ref:
            body["voice"] = voice_ref

        try:
            resp = requests.post(endpoint, headers=self._headers(), json=body, timeout=30)
            if resp.status_code in [200, 201]:
                char_json = resp.json()
                char_ref = char_json.get("character") or char_json.get("ref")
                print(f"[UseApiClient] Character '{display_name}' created: {char_ref}")
                return char_ref
            else:
                print(f"[UseApiClient] Failed to create character [{resp.status_code}]: {resp.text}")
                return None
        except Exception as e:
            print(f"[UseApiClient] Exception creating character: {e}")
            return None

    def generate_video(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        duration: int = 8,
        model: Optional[str] = None,
        start_image_id: Optional[str] = None,
        end_image_id: Optional[str] = None,
        character_ref: Optional[str] = None,
        poll_interval: int = 10,
        max_wait_seconds: int = 600,
    ) -> Optional[Dict[str, Any]]:
        """Generates a video via Google Flow using Veo 3.1 or Omni 1.1 Flash.
        Dispatches request with async=True and polls job until complete.
        Returns dict containing 'videoUrl' and 'mediaGenerationId'.
        Reference: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos.html
        """
        if not self.is_configured:
            raise ValueError("USEAPI_TOKEN is not configured in environment or settings.")

        target_model = model or settings.useapi_model
        # Map aspect ratio: "16:9" -> "landscape", "9:16" -> "portrait", "1:1", "4:3", "3:4"
        ar_lower = (aspect_ratio or "16:9").strip().lower()
        if ar_lower in ["16:9", "16/9", "landscape", "wide"]:
            ar = "landscape"
        elif ar_lower in ["9:16", "9/16", "portrait", "vertical", "tall"]:
            ar = "portrait"
        elif ar_lower in ["1:1", "square"]:
            ar = "1:1"
        elif ar_lower in ["4:3", "4/3"]:
            ar = "4:3"
        elif ar_lower in ["3:4", "3/4"]:
            ar = "3:4"
        else:
            ar = "landscape"

        # Snap duration to Google Flow supported values: [4, 6, 8, 10]
        valid_durations = [4, 6, 8, 10]
        try:
            dur_int = int(duration)
        except (ValueError, TypeError):
            dur_int = 8
        target_dur = min(valid_durations, key=lambda x: abs(x - dur_int))

        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": target_model,
            "aspectRatio": ar,
            "duration": target_dur,
            "async": True,
        }
        if self.email:
            body["email"] = self.email
        if start_image_id:
            body["startImage"] = start_image_id
        if end_image_id:
            body["endImage"] = end_image_id
        if character_ref:
            body["character_1"] = character_ref

        endpoint = f"{self.base_url}/videos"
        print(f"[UseApiClient] POST {endpoint} (model: {target_model}, dur: {target_dur}s, aspect: {ar})...")
        resp = requests.post(endpoint, headers=self._headers(), json=body, timeout=60)

        if resp.status_code not in [200, 201]:
            raise RuntimeError(f"Google Flow video request failed [{resp.status_code}]: {resp.text}")

        res_json = resp.json()

        # If synchronous response (200) returned media directly
        if resp.status_code == 200 and "media" in res_json and len(res_json["media"]) > 0:
            item = res_json["media"][0]
            return {
                "videoUrl": item.get("videoUrl"),
                "mediaGenerationId": item.get("mediaGenerationId"),
            }

        job_id = res_json.get("jobid") or res_json.get("jobId")
        if not job_id:
            raise RuntimeError(f"Unexpected response, missing job id: {res_json}")

        print(f"[UseApiClient] Job dispatched: {job_id}. Polling Google Flow GPU compute...")
        elapsed = 0
        job_endpoint = f"{self.base_url}/jobs/{job_id}"

        while elapsed < max_wait_seconds:
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                poll_resp = requests.get(job_endpoint, headers=self._headers(), timeout=30)
            except Exception as e:
                print(f"[UseApiClient] Poll request error: {e}")
                continue

            if poll_resp.status_code in [400, 401, 402, 403, 404]:
                raise RuntimeError(f"Google Flow poll failed [{poll_resp.status_code}]: {poll_resp.text}")

            if poll_resp.status_code != 200:
                print(f"[UseApiClient] Poll warning [{poll_resp.status_code}]: {poll_resp.text}")
                continue

            try:
                job_data = poll_resp.json()
            except Exception as e:
                print(f"[UseApiClient] Poll warning: failed to parse JSON ({e})")
                continue

            status = job_data.get("status")
            print(f"  [UseApiClient] Job status: {status} ({elapsed}s elapsed)")

            resp_obj = job_data.get("response") if isinstance(job_data.get("response"), dict) else {}
            if status == "completed":
                media_list = resp_obj.get("media") or job_data.get("media", [])
                if media_list and len(media_list) > 0:
                    first = media_list[0]
                    return {
                        "videoUrl": first.get("videoUrl"),
                        "mediaGenerationId": first.get("mediaGenerationId"),
                    }
                raise RuntimeError("Job marked completed but no media items found in payload.")

            elif (
                status in ["failed", "error"]
                or "error" in job_data
                or resp_obj.get("failureReasons")
                or job_data.get("code", 0) >= 400
            ):
                reasons = (
                    resp_obj.get("failureReasons")
                    or job_data.get("error")
                    or f"Failure code {job_data.get('code')}"
                )
                raise RuntimeError(f"Google Flow generation failed: {reasons}")

        raise TimeoutError(f"Google Flow generation timed out after {max_wait_seconds} seconds.")

    def extend_video(
        self,
        media_generation_id: str,
        prompt: str,
        model: Optional[str] = None,
        poll_interval: int = 10,
        max_wait_seconds: int = 600,
    ) -> Optional[Dict[str, Any]]:
        """Extends an existing Veo clip by 8 seconds from the source's last second.
        Reference: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-extend.html
        """
        if not self.is_configured:
            raise ValueError("USEAPI_TOKEN is not configured.")

        body: Dict[str, Any] = {
            "mediaGenerationId": media_generation_id,
            "prompt": prompt,
            "model": model or settings.useapi_model,
            "async": True,
        }
        if self.email:
            body["email"] = self.email

        endpoint = f"{self.base_url}/videos/extend"
        print(f"[UseApiClient] POST {endpoint} (extending {media_generation_id[:30]}...)...")
        resp = requests.post(endpoint, headers=self._headers(), json=body, timeout=60)
        if resp.status_code not in [200, 201]:
            raise RuntimeError(f"Video extend failed [{resp.status_code}]: {resp.text}")

        res_json = resp.json()
        job_id = res_json.get("jobid") or res_json.get("jobId")

        elapsed = 0
        job_endpoint = f"{self.base_url}/jobs/{job_id}"
        while elapsed < max_wait_seconds:
            time.sleep(poll_interval)
            elapsed += poll_interval
            try:
                poll_resp = requests.get(job_endpoint, headers=self._headers(), timeout=30)
            except Exception as e:
                print(f"[UseApiClient] Extend poll request error: {e}")
                continue

            if poll_resp.status_code in [400, 401, 402, 403, 404]:
                raise RuntimeError(f"Extend poll failed [{poll_resp.status_code}]: {poll_resp.text}")

            if poll_resp.status_code == 200:
                try:
                    data = poll_resp.json()
                except Exception as e:
                    print(f"[UseApiClient] Extend poll JSON parse warning: {e}")
                    continue

                resp_obj = data.get("response") if isinstance(data.get("response"), dict) else {}
                if data.get("status") == "completed":
                    media = resp_obj.get("media") or data.get("media", [])
                    if media:
                        return {
                            "videoUrl": media[0].get("videoUrl"),
                            "mediaGenerationId": media[0].get("mediaGenerationId"),
                        }
                elif (
                    data.get("status") in ["failed", "error"]
                    or "error" in data
                    or resp_obj.get("failureReasons")
                    or data.get("code", 0) >= 400
                ):
                    reasons = (
                        resp_obj.get("failureReasons")
                        or data.get("error")
                        or f"Failure code {data.get('code')}"
                    )
                    raise RuntimeError(f"Video extend failed: {reasons}")

        raise TimeoutError(f"Video extend timed out after {max_wait_seconds}s")

    def concatenate_videos(self, media_generation_ids: List[str], output_path: Path, trim_overlap: bool = True) -> bool:
        """Concatenates multiple Google Flow clips server-side.
        Reference: https://useapi.net/docs/api-google-flow-v1/post-google-flow-videos-concatenate.html
        """
        if not self.is_configured or len(media_generation_ids) < 2:
            return False

        media_items = []
        for i, mid in enumerate(media_generation_ids):
            item: Dict[str, Any] = {"mediaGenerationId": mid}
            # Trim 1.0s overlap from subsequent clips if they were extended
            if trim_overlap and i > 0:
                item["trimStart"] = 1.0
            media_items.append(item)

        body: Dict[str, Any] = {"media": media_items}
        if self.email:
            body["email"] = self.email

        endpoint = f"{self.base_url}/videos/concatenate"
        print(f"[UseApiClient] POST {endpoint} (combining {len(media_items)} clips server-side)...")
        try:
            resp = requests.post(endpoint, headers=self._headers(), json=body, timeout=120)
            if resp.status_code == 200:
                res_json = resp.json()
                encoded_video = res_json.get("encodedVideo")
                if encoded_video:
                    raw_bytes = base64.b64decode(encoded_video)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(raw_bytes)
                    print(f"[UseApiClient] Cloud concatenate saved to: {output_path}")
                    return True
                else:
                    print(f"[UseApiClient] Cloud concatenate response missing encodedVideo: {res_json.get('error') or res_json.get('status')}")
            else:
                print(f"[UseApiClient] Cloud concatenate failed [{resp.status_code}]: {resp.text}")
            return False
        except Exception as e:
            print(f"[UseApiClient] Exception during concatenate_videos: {e}")
            return False

    def download_file(self, url: str, output_path: Path) -> bool:
        """Streams and saves remote video to local destination with cleanup on failure."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            print(f"[UseApiClient] Downloading video from Google Cloud Storage signed URL...")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"[UseApiClient] Saved to: {output_path} ({output_path.stat().st_size} bytes)")
                return True
            else:
                if output_path.exists():
                    output_path.unlink()
                return False
        except Exception as e:
            print(f"[UseApiClient] Error downloading file from {url}: {e}")
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            return False


class VideoGenerationEngine:
    """Manages video generation across providers (useapi.net Google Flow vs direct Google GenAI),
    asynchronous polling, downloading, and last-frame extraction for seamless scene chaining.
    """

    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = (provider or settings.video_provider).lower()
        self.api_key = api_key or settings.gemini_api_key
        self.useapi_client = UseApiGoogleFlowClient()
        self.genai_client = None
        self._init_genai_client()

    def _init_genai_client(self):
        """Initializes google-genai client if key is present."""
        if self.api_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[VideoEngine] Error initializing google-genai: {e}")
                self.genai_client = None

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
        """Generates a single scene clip using configured provider or synthetic fallback."""
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_path = output_dir / f"scene_{scene.scene_number:02d}.mp4"
        last_frame_path = output_dir / f"scene_{scene.scene_number:02d}_last_frame.png"

        # Check for dry-run or unconfigured credentials
        if dry_run:
            print(f"[VideoEngine] Generating synthetic preview clip for Scene {scene.scene_number:02d} (--dry-run enabled)...")
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        # -------------------------------------------------------------
        # PROVIDER 0: Free AI Keyframes + 2.5D Hollywood Motion Engine
        # 100% Free, Zero Tokens, Instant Generation via Pollinations.ai + FFmpeg
        # -------------------------------------------------------------
        if self.provider == "free":
            print(f"\n[VideoEngine] 🌟 Dispatching FREE AI Generation for Scene {scene.scene_number:02d} ({scene.duration_seconds}s)...")
            return self._generate_free_motion_clip(scene, clip_path, last_frame_path, aspect_ratio)

        # -------------------------------------------------------------
        # PROVIDER 1: useapi.net Google Flow API v1 (Veo 3.1 & Omni)
        # -------------------------------------------------------------
        if self.provider == "useapi":
            if not self.useapi_client.is_configured:
                print(f"[VideoEngine] USEAPI_TOKEN is not set in environment or .env!")
                print(f"[VideoEngine] Generating synthetic animated test clip for Scene {scene.scene_number:02d} as fallback.")
                self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
                self.extract_last_frame(clip_path, last_frame_path)
                scene.output_clip_path = str(clip_path)
                scene.last_frame_path = str(last_frame_path)
                scene.status = SceneStatus.COMPLETED
                return clip_path

            scene.status = SceneStatus.GENERATING
            print(f"\n[VideoEngine] Dispatching useapi.net Google Flow Veo for Scene {scene.scene_number:02d} ({scene.duration_seconds}s)...")
            print(f"  Visual Prompt: {scene.visual_prompt[:90]}...")

            start_image_id: Optional[str] = None
            if scene.reference_image_path and Path(scene.reference_image_path).exists():
                ref_p = Path(scene.reference_image_path)
                print(f"  Uploading continuity seed frame for I2V chaining: {ref_p.name}...")
                start_image_id = self.useapi_client.upload_asset(ref_p)

            try:
                res = self.useapi_client.generate_video(
                    prompt=scene.visual_prompt,
                    aspect_ratio=aspect_ratio,
                    duration=int(scene.duration_seconds),
                    model=settings.useapi_model,
                    start_image_id=start_image_id,
                )
                if not res or not res.get("videoUrl"):
                    raise RuntimeError("useapi.net returned no videoUrl")

                # Download video to local disk
                download_ok = self.useapi_client.download_file(res["videoUrl"], clip_path)
                if not download_ok or not clip_path.exists() or clip_path.stat().st_size == 0:
                    raise RuntimeError(f"Failed to download generated video from {res['videoUrl']} to {clip_path}")
                scene.metadata["mediaGenerationId"] = res.get("mediaGenerationId")

                # Extract last frame for seamless next-scene continuation
                self.extract_last_frame(clip_path, last_frame_path)
                scene.output_clip_path = str(clip_path)
                scene.last_frame_path = str(last_frame_path)
                scene.status = SceneStatus.COMPLETED
                print(f"[VideoEngine] Scene {scene.scene_number:02d} generated successfully via Google Flow!")
                return clip_path

            except Exception as e:
                print(f"[VideoEngine] Error generating Scene {scene.scene_number:02d} via useapi: {e}")
                scene.status = SceneStatus.FAILED
                scene.error_message = str(e)
                # Fallback so pipeline can complete
                self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
                self.extract_last_frame(clip_path, last_frame_path)
                scene.output_clip_path = str(clip_path)
                scene.last_frame_path = str(last_frame_path)
                return clip_path

        # -------------------------------------------------------------
        # PROVIDER 2: Direct Google GenAI SDK (Google AI Studio)
        # -------------------------------------------------------------
        if not self.genai_client:
            print(f"[VideoEngine] Direct GenAI client not available. Falling back to synthetic clip for Scene {scene.scene_number:02d}.")
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        scene.status = SceneStatus.GENERATING
        print(f"[VideoEngine] Dispatching Direct GenAI Veo Generation for Scene {scene.scene_number:02d} ({scene.duration_seconds}s)...")
        print(f"  Prompt: {scene.visual_prompt[:90]}...")

        try:
            from google.genai.types import GenerateVideosConfig
            from PIL import Image

            genai_aspect = "9:16" if (aspect_ratio or "").strip().lower() in ["9:16", "9/16", "portrait", "vertical", "tall"] else "16:9"
            config = GenerateVideosConfig(
                aspect_ratio=genai_aspect,
                negative_prompt=scene.negative_prompt,
                duration_seconds=int(scene.duration_seconds),
            )

            image_input = None
            if scene.reference_image_path and Path(scene.reference_image_path).exists():
                print(f"  Using reference seed image: {scene.reference_image_path}")
                from google.genai import types
                try:
                    image_input = types.Image.from_file(location=str(scene.reference_image_path))
                except Exception:
                    image_input = Image.open(scene.reference_image_path)

            operation = self.genai_client.models.generate_videos(
                model=settings.video_model,
                prompt=scene.visual_prompt,
                image=image_input,
                config=config,
            )

            print("  Waiting for Veo GPU compute...")
            poll_interval = 10
            max_wait_seconds = 600
            elapsed = 0

            while not operation.done and elapsed < max_wait_seconds:
                time.sleep(poll_interval)
                elapsed += poll_interval
                operation = self.genai_client.operations.get(operation)
                print(f"  Elapsed: {elapsed}s...")

            if not operation.done:
                raise TimeoutError(f"Video generation timed out after {max_wait_seconds}s")

            if getattr(operation, "error", None):
                raise RuntimeError(f"Google GenAI video generation failed: {operation.error}")

            if not getattr(operation, "response", None) or not getattr(operation.response, "generated_videos", None):
                raise RuntimeError(f"Google GenAI returned no generated videos: {operation}")

            generated_video = operation.response.generated_videos[0]
            if hasattr(generated_video.video, "save"):
                generated_video.video.save(str(clip_path))
            else:
                raw_bytes = self.genai_client.files.download(file=generated_video.video)
                with open(clip_path, "wb") as f:
                    f.write(raw_bytes)
            print(f"[VideoEngine] Successfully saved: {clip_path.name}")

            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        except Exception as e:
            print(f"[VideoEngine] Direct Veo generation error on Scene {scene.scene_number:02d}: {e}")
            scene.status = SceneStatus.FAILED
            scene.error_message = str(e)
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            return clip_path

    def _generate_synthetic_clip(self, scene: Scene, output_path: Path, aspect_ratio: str):
        """Generates an unmistakable animated test pattern with audio tone so previews are NEVER blank."""
        ar_clean = (aspect_ratio or "16:9").strip().lower()
        if ar_clean in ["9:16", "9/16", "portrait", "vertical", "tall"]:
            width, height = (720, 1280)
        elif ar_clean in ["1:1", "square"]:
            width, height = (720, 720)
        else:
            width, height = (1280, 720)
        dur = scene.duration_seconds

        # Animated SMPTE test pattern + audio tone
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

    def _generate_free_motion_clip(
        self,
        scene: Scene,
        clip_path: Path,
        last_frame_path: Path,
        aspect_ratio: str = "16:9",
    ) -> Path:
        """Generates a high-resolution AI visual frame using free Pollinations.ai (Flux/SDXL),
        then renders cinematic Hollywood camera motion (Push-in, Dolly, Pan, Crane) using FFmpeg.
        Zero cost, zero API keys required, completely free.
        """
        import urllib.parse
        import urllib.request

        ar_clean = (aspect_ratio or "16:9").strip().lower()
        if ar_clean in ["9:16", "9/16", "portrait", "vertical", "tall"]:
            width, height = (720, 1280)
        elif ar_clean in ["1:1", "square"]:
            width, height = (720, 720)
        else:
            width, height = (1280, 720)
        dur = int(scene.duration_seconds or 8)
        fps = settings.default_fps or 24

        keyframe_path = clip_path.parent / f"scene_{scene.scene_number:02d}_keyframe.jpg"

        # 1. Fetch AI Keyframe from Pollinations (100% Free, no keys required)
        encoded_prompt = urllib.parse.quote(scene.visual_prompt[:400])
        pollinations_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&nologo=true&seed={scene.scene_number * 100 + 42}"
        )

        try:
            print(f"  [FreeEngine] Generating AI Visual Keyframe from Pollinations...")
            req = urllib.request.Request(pollinations_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                with open(keyframe_path, "wb") as f:
                    f.write(resp.read())
            print(f"  [FreeEngine] AI Keyframe generated ({keyframe_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [FreeEngine] Pollinations download warning: {e}. Using fallback generator.")
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

        # 2. Map Camera Movement to FFmpeg 2.5D Motion Formula
        cam_move = (scene.camera_movement or "SLOW_PUSH_IN").upper()
        total_frames = int(dur * fps)

        if "DOLLY_OUT" in cam_move or "PULL_OUT" in cam_move:
            zoom_filter = f"zoompan=z='if(lte(zoom,1.0),1.30,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"
        elif "TRACKING" in cam_move or "PAN" in cam_move or "LATERAL" in cam_move:
            zoom_filter = f"zoompan=z=1.2:x='if(lte(on,1),(iw-iw/zoom)*0.2,min(iw-iw/zoom,x+1.2))':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"
        elif "CRANE" in cam_move or "BOOM" in cam_move or "TILT" in cam_move:
            zoom_filter = f"zoompan=z=1.2:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(ih-ih/zoom,y+1.2))':d={total_frames}:s={width}x{height}:fps={fps}"
        else:
            zoom_filter = f"zoompan=z='min(zoom+0.0015,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"

        print(f"  [FreeEngine] Rendering {cam_move} camera movement with FFmpeg...")
        cmd = [
            settings.ffmpeg_binary,
            "-y",
            "-loop", "1",
            "-i", str(keyframe_path),
            "-filter_complex", f"{zoom_filter},format=yuv420p",
            "-t", str(dur),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(clip_path),
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            print(f"[FreeEngine] Scene {scene.scene_number:02d} rendered successfully! ({clip_path.name})")
            return clip_path
        except Exception as e:
            print(f"[FreeEngine] Error rendering motion clip: {e}")
            self._generate_synthetic_clip(scene, clip_path, aspect_ratio)
            self.extract_last_frame(clip_path, last_frame_path)
            scene.output_clip_path = str(clip_path)
            scene.last_frame_path = str(last_frame_path)
            scene.status = SceneStatus.COMPLETED
            return clip_path

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
            # Check if this scene should be chained from previous scene's last frame
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
