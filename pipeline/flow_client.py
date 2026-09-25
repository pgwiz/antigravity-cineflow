"""Google Flow Internal Labs Session Cookie Client (Option 2).

Communicates with Google Flow / Google Labs internal generation endpoints using
authenticated browser session cookies (__Secure-1PSID, __Secure-3PSID, SAPISID, etc.).
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import quote

import requests
from config import settings


class GoogleFlowInternalClient:
    """Session Cookie-based direct client for Google Flow Ultra."""

    def __init__(
        self,
        cookies: Optional[str] = None,
        user_index: Optional[int] = None,
    ):
        self.raw_cookies = (cookies or settings.google_flow_cookies or "").strip()
        self.user_index = user_index if user_index is not None else settings.flow_user_index
        self.base_url = f"https://flow.google.com/u/{self.user_index}"
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Configures requests session headers and cookies."""
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            "Origin": "https://flow.google.com",
            "Referer": f"https://flow.google.com/u/{self.user_index}/",
            "Accept": "application/json, text/plain, */*",
        })

        if self.raw_cookies:
            cookie_dict = self._parse_cookie_string(self.raw_cookies)
            self.session.cookies.update(cookie_dict)

    @staticmethod
    def _parse_cookie_string(cookie_str: str) -> Dict[str, str]:
        """Parses a standard Cookie header string into a dictionary."""
        cookies = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if not item or "=" not in item:
                continue
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
        return cookies

    @property
    def is_configured(self) -> bool:
        """Checks if session cookies are configured."""
        return bool(self.raw_cookies)

    def check_health(self) -> Tuple[bool, str]:
        """Checks if the session cookies are valid and authenticated."""
        if not self.is_configured:
            return False, "GOOGLE_FLOW_COOKIES is not set in environment or .env"

        try:
            r = self.session.get(self.base_url, timeout=10, allow_redirects=False)
            if r.status_code in [200, 302]:
                loc = r.headers.get("Location", "")
                if "accounts.google.com" in loc or "ServiceLogin" in loc:
                    return False, "Cookies expired or invalid (redirected to Google Sign-In)"
                return True, f"Session active at {self.base_url}"
            return False, f"Unexpected response: HTTP {r.status_code}"
        except Exception as e:
            return False, f"Connection error: {e}"

    def upload_asset(self, file_path: Path) -> Optional[str]:
        """Uploads an image asset to Google Flow and returns media id."""
        if not file_path.exists() or not self.is_configured:
            return None

        # Internal upload endpoint
        endpoint = f"{self.base_url}/_/upload"
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "image/png")}
                r = self.session.post(endpoint, files=files, timeout=45)
                if r.status_code == 200:
                    data = r.json()
                    return data.get("mediaId") or data.get("id")
        except Exception as e:
            print(f"[FlowInternalClient] Asset upload error: {e}")
        return None

    def generate_video(
        self,
        prompt: str,
        output_file: Path,
        aspect_ratio: str = "16:9",
        duration: int = 8,
        model: str = "veo-3.1-fast",
        start_image_id: Optional[str] = None,
        timeout: int = 240,
    ) -> bool:
        """Submits video generation task and polls for resulting MP4."""
        if not self.is_configured:
            print("[FlowInternalClient] GOOGLE_FLOW_COOKIES not configured.")
            return False

        print(f"[FlowInternalClient] Submitting prompt to Google Flow: {prompt[:80]}...")
        # Dispatch generation request
        gen_endpoint = f"{self.base_url}/_/generate"
        payload = {
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
            "durationSeconds": duration,
            "model": model,
            "startMediaId": start_image_id,
        }

        try:
            r = self.session.post(gen_endpoint, json=payload, timeout=30)
            if r.status_code not in [200, 201]:
                print(f"[FlowInternalClient] Generation request failed [{r.status_code}]: {r.text[:200]}")
                return False

            resp_data = r.json()
            task_id = resp_data.get("taskId") or resp_data.get("id")
            video_url = resp_data.get("videoUrl")

            if not video_url and task_id:
                # Poll task status
                start_t = time.time()
                while time.time() - start_t < timeout:
                    time.sleep(5)
                    poll_res = self.session.get(f"{self.base_url}/_/tasks/{task_id}", timeout=15)
                    if poll_res.status_code == 200:
                        p_data = poll_res.json()
                        if p_data.get("status") in ["COMPLETED", "DONE", "SUCCESS"]:
                            video_url = p_data.get("videoUrl")
                            break
                        if p_data.get("status") in ["FAILED", "ERROR"]:
                            print(f"[FlowInternalClient] Generation failed: {p_data.get('error')}")
                            return False

            if not video_url:
                print("[FlowInternalClient] Timed out waiting for video generation.")
                return False

            # Download MP4
            output_file.parent.mkdir(parents=True, exist_ok=True)
            v_resp = self.session.get(video_url, stream=True, timeout=60)
            if v_resp.status_code == 200:
                with open(output_file, "wb") as f:
                    for chunk in v_resp.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            f.write(chunk)
                return output_file.exists() and output_file.stat().st_size > 0

        except Exception as e:
            print(f"[FlowInternalClient] Error generating video: {e}")

        return False
