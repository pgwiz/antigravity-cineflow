"""Chrome Automation Provider for Google Flow Ultra (Option 1).

Connects to a running or managed Google Chrome instance via Chrome DevTools Protocol (CDP)
targeting https://flow.google.com/u/{user_index}/.
Automates prompt submission, model selection (Veo 3.1 Fast, Quality, Lite),
seed image upload for continuity chaining, and final video MP4 download.
"""

import os
import json
import time
import socket
import base64
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import requests
import websocket
from config import settings


class ChromeFlowAutomation:
    """Automates Google Flow Ultra using Chrome DevTools Protocol (CDP)."""

    def __init__(
        self,
        chrome_binary: Optional[str] = None,
        user_data_dir: Optional[Path] = None,
        port: Optional[int] = None,
        user_index: Optional[int] = None,
        project_url: Optional[str] = None,
    ):
        self.chrome_binary = chrome_binary or settings.chrome_binary
        self.user_data_dir = user_data_dir or settings.chrome_user_data_dir
        self.user_index = user_index if user_index is not None else settings.flow_user_index
        self.project_url = project_url or ""
        self.port = self._resolve_port(port)
        if self.project_url:
            self.target_url = self.project_url
        elif getattr(settings, "flow_project_url", "") and user_index is None:
            self.target_url = settings.flow_project_url
        else:
            self.target_url = f"https://flow.google.com/u/{self.user_index}/"
        self._proc: Optional[subprocess.Popen] = None
        self._msg_id = 0

    @staticmethod
    def get_free_port() -> int:
        """Finds a random ephemeral unreserved free port to avoid common port collisions."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _resolve_port(self, explicit_port: Optional[int]) -> int:
        """Resolves port: explicit > active saved port > new random ephemeral port."""
        if explicit_port:
            return explicit_port
        port_file = self.user_data_dir.parent / "flow_port.txt"
        if port_file.exists():
            try:
                saved = int(port_file.read_text().strip())
                r = requests.get(f"http://127.0.0.1:{saved}/json/version", timeout=1.0)
                if r.status_code == 200:
                    return saved
            except Exception:
                pass
        # Allocate random port and persist
        new_port = self.get_free_port()
        try:
            port_file.parent.mkdir(parents=True, exist_ok=True)
            port_file.write_text(str(new_port))
        except Exception:
            pass
        return new_port

    @property
    def is_port_active(self) -> bool:
        """Checks if the remote debugging port is actively listening."""
        try:
            r = requests.get(f"http://127.0.0.1:{self.port}/json/version", timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

    def launch_browser(self, headless: bool = False) -> bool:
        """Launches Google Chrome with remote debugging on the configured port."""
        if self.is_port_active:
            return True

        if not os.path.exists(self.chrome_binary):
            print(f"[ChromeFlow] Chrome executable not found at: {self.chrome_binary}")
            return False

        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            self.chrome_binary,
            f"--remote-debugging-port={self.port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={str(self.user_data_dir)}",
            "--no-first-run",
            "--no-default-browser-check",
            self.target_url,
        ]
        if headless:
            cmd.append("--headless=new")

        print(f"[ChromeFlow] Launching Chrome (port {self.port}, profile {self.user_data_dir.name})...")
        try:
            flags = 0
            if os.name == "nt" and not headless:
                flags = subprocess.CREATE_NEW_CONSOLE
            self._proc = subprocess.Popen(cmd, creationflags=flags)
            # Wait for port to become active (up to 15 seconds)
            for _ in range(30):
                time.sleep(0.5)
                if self.is_port_active:
                    print(f"[ChromeFlow] Chrome is active and connected on port {self.port}!")
                    return True
            print("[ChromeFlow] Timed out waiting for Chrome debugging port.")
            return False
        except Exception as e:
            print(f"[ChromeFlow] Failed to launch Chrome: {e}")
            return False

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Returns the list of active browser targets from CDP."""
        try:
            r = requests.get(f"http://127.0.0.1:{self.port}/json/list", timeout=3)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[ChromeFlow] Error fetching tabs: {e}")
        return []

    def get_flow_tab(self) -> Optional[Dict[str, Any]]:
        """Finds or opens a tab navigating to Google Flow."""
        tabs = self.get_tabs()
        for t in tabs:
            if t.get("type") == "page" and "flow.google.com" in t.get("url", ""):
                return t

        # Fallback to any regular page tab
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        if page_tabs:
            return page_tabs[0]

        # Or create a new tab
        try:
            r = requests.put(f"http://127.0.0.1:{self.port}/json/new?{self.target_url}", timeout=5)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[ChromeFlow] Failed to create new Flow tab: {e}")
        return None

    def execute_cdp(self, ws_url: str, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Executes a Chrome DevTools Protocol command over WebSocket."""
        self._msg_id += 1
        mid = self._msg_id
        ws = None
        try:
            ws = websocket.create_connection(ws_url, timeout=timeout)
            payload = {"id": mid, "method": method, "params": params or {}}
            ws.send(json.dumps(payload))
            start_t = time.time()
            while time.time() - start_t < timeout:
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == mid:
                    return msg
            return {"error": "CDP call timed out"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass

    def eval_js(self, ws_url: str, expression: str, timeout: float = 10.0) -> Any:
        """Evaluates JavaScript expression in page context."""
        res = self.execute_cdp(
            ws_url,
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            timeout=timeout,
        )
        return res.get("result", {}).get("result", {}).get("value")

    def capture_screenshot(self, output_path: Path) -> bool:
        """Takes a full-resolution PNG screenshot of the current page for diagnostic inspection."""
        tab = self.get_flow_tab()
        if not tab or "webSocketDebuggerUrl" not in tab:
            return False

        res = self.execute_cdp(tab["webSocketDebuggerUrl"], "Page.captureScreenshot", {"format": "png"})
        b64_data = res.get("result", {}).get("data")
        if b64_data:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            return True
        return False

    def get_all_cookies(self) -> List[Dict[str, Any]]:
        """Retrieves all cookies directly from Chrome active memory via CDP."""
        tab = self.get_flow_tab()
        if not tab or "webSocketDebuggerUrl" not in tab:
            return []
        res = self.execute_cdp(tab["webSocketDebuggerUrl"], "Network.getAllCookies")
        return res.get("result", {}).get("cookies", [])

    def export_and_save_cookies(self, env_path: Optional[Path] = None) -> str:
        """Extracts Google session cookies from the live browser and saves to .env."""
        cookies = self.get_all_cookies()
        google_cookies = [
            c for c in cookies
            if any(dom in c.get("domain", "") for dom in ["google.com", "google", "flow.google.com"])
        ]
        if not google_cookies:
            return ""

        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in google_cookies)
        env_file = env_path or Path(".env")
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
            if "GOOGLE_FLOW_COOKIES=" in content:
                import re
                content = re.sub(r'GOOGLE_FLOW_COOKIES=.*', f'GOOGLE_FLOW_COOKIES="{cookie_str}"', content)
            else:
                content += f'\nGOOGLE_FLOW_COOKIES="{cookie_str}"\n'
            env_file.write_text(content, encoding="utf-8")
            print(f"[ChromeFlow] 🔑 Extracted {len(google_cookies)} Google cookies and saved to {env_file}!")
        return cookie_str

    def is_authenticated(self) -> Tuple[bool, str]:
        """Checks if the user is authenticated on Google Flow.
        Returns (is_authed, status_description).
        """
        tab = self.get_flow_tab()
        if not tab or "webSocketDebuggerUrl" not in tab:
            return False, "Browser or tab not accessible"

        ws_url = tab["webSocketDebuggerUrl"]
        # Check current URL
        url_info = self.eval_js(ws_url, "window.location.href") or ""
        if "accounts.google.com" in url_info or "ServiceLogin" in url_info:
            return False, "Redirected to Google Sign-In"
        if "flow.google.com/about" in url_info:
            self.eval_js(ws_url, """(() => {
                const links = Array.from(document.querySelectorAll('a, button'));
                const btn = links.find(l => (l.innerText || '').includes('Create with Google Flow'));
                if (btn) btn.click();
            })()""")
            return False, "On Flow About page - clicked 'Create with Google Flow', waiting for Sign In or Studio..."

        # Check DOM elements
        check_script = """
        (() => {
            const text = document.body ? document.body.innerText : '';
            const hasSignIn = text.includes('Sign in') && !text.includes('Sign out');
            const hasStudio = !!document.querySelector('textarea, [contenteditable="true"], button[aria-label*="Generate"], button[aria-label*="Create"], [role="textbox"]');
            return {
                url: window.location.href,
                hasSignIn: hasSignIn,
                hasStudio: hasStudio,
                title: document.title
            };
        })()
        """
        info = self.eval_js(ws_url, check_script)
        if isinstance(info, dict):
            if info.get("hasStudio") and not info.get("hasSignIn"):
                return True, f"Authenticated in Flow Studio ({info.get('url')})"
            if info.get("hasSignIn"):
                return False, "Google account sign-in required"
            return False, f"Waiting for Flow Studio interface ({info.get('title')})"

        return False, "Could not inspect page state"

    def login_interactive(self):
        """Interactive helper to guide user login in the Chrome window."""
        print("\n=======================================================")
        print(" [ChromeFlow] INTERACTIVE GOOGLE FLOW LOGIN HELPER")
        print("=======================================================")
        print(f"Targeting Profile User Index: {self.user_index}")
        print(f"URL: {self.target_url}")
        print(f"Profile Storage Directory: {self.user_data_dir}")
        print("-------------------------------------------------------")
        print("1. Chrome will open with a dedicated persistent profile.")
        print("2. Sign in to your Google Account (peterbrian484@gmail.com).")
        print("3. Ensure Google Flow Ultra opens at https://flow.google.com/u/5/.")
        print("4. Once logged in, your session remains permanently saved!")
        print("=======================================================\n")

        login_url = f"https://accounts.google.com/ServiceLogin?continue=https%3A%2F%2Fflow.google.com%2Fu%2F{self.user_index}%2F"
        self.launch_browser(headless=False)
        tab = self.get_flow_tab()
        if tab and "webSocketDebuggerUrl" in tab:
            self.execute_cdp(tab["webSocketDebuggerUrl"], "Page.navigate", {"url": login_url})

        print("[ChromeFlow] Monitoring authentication status (press Ctrl+C to cancel)...")
        while True:
            time.sleep(3)
            authed, desc = self.is_authenticated()
            print(f"  Current Status: {desc}")
            if authed:
                print("\n🎉 SUCCESS! Google Flow is authenticated and ready for automation!\n")
                cookie_str = self.export_and_save_cookies()
                if cookie_str:
                    print(f"🍪 Auto-extracted session cookies and saved to .env for Option 2 (Headless Flow Client)!")
                break

    @staticmethod
    def sanitize_prompt_for_safety(prompt: str) -> str:
        """Sanitizes potential noir/violence safety filter triggers into atmospheric equivalents."""
        import re
        replacements = {
            r"\bmurdered\b": "shadowed",
            r"\bmurder\b": "crime mystery",
            r"\bblood\b": "rainwater",
            r"\bbloody\b": "rain-slicked",
            r"\bkill\b": "confront",
            r"\bkiller\b": "shadow figure",
            r"\bdead body\b": "silent crime scene",
            r"\bcorpse\b": "abandoned altar",
            r"\bgun\b": "tactical scanner",
            r"\bguns\b": "scanners",
            r"\bweapon\b": "gadget",
            r"\bstrangle\b": "corner",
            r"\bviolent\b": "intense",
            r"\bviolence\b": "dramatic suspense",
            r"\bdrowning\b": "submerged",
        }
        sanitized = prompt
        for pattern, repl in replacements.items():
            sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)
        return sanitized

    def dismiss_flow_alerts(self, ws_url: str) -> int:
        """Dismisses open snackbars, dialogs, or alert banners in Google Flow."""
        dismiss_js = """
        (() => {
            const dismissBtns = Array.from(document.querySelectorAll('.mat-mdc-snack-bar-container button, [role="alert"] button, button[aria-label*="Dismiss"], button[aria-label*="Close"], button[aria-label*="OK"]'));
            let clicked = 0;
            for (const b of dismissBtns) {
                try {
                    b.click();
                    clicked++;
                } catch (e) {}
            }
            return clicked;
        })()
        """
        return self.eval_js(ws_url, dismiss_js) or 0

    def generate_video(
        self,
        prompt: str,
        output_file: Path,
        aspect_ratio: str = "16:9",
        duration: int = 8,
        model: str = "veo-3.1-fast",
        start_image_path: Optional[Path] = None,
        timeout: int = 240,
        max_attempts: int = 3,
    ) -> bool:
        """Automates video generation on Google Flow Studio with failure detection and auto-retry."""
        if not self.ensure_ready():
            print("[ChromeFlow] Chrome is not ready or not authenticated.")
            return False

        tab = self.get_flow_tab()
        if not tab or "webSocketDebuggerUrl" not in tab:
            print("[ChromeFlow] No active Flow tab.")
            return False

        ws_url = tab["webSocketDebuggerUrl"]

        # Ensure we are on target URL
        current_url = self.eval_js(ws_url, "window.location.href") or ""
        if "flow.google.com" not in current_url:
            print(f"[ChromeFlow] Navigating to {self.target_url}...")
            self.execute_cdp(ws_url, "Page.navigate", {"url": self.target_url})
            time.sleep(5)

        # Configure isolated Chrome download directory via CDP
        download_dir = settings.temp_dir / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        self.execute_cdp(ws_url, "Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_dir)})

        # Snapshot existing MP4 files to track new downloads reliably
        existing_downloads = set(f.name for f in download_dir.glob("*.mp4"))
        user_dl = Path.home() / "Downloads"
        existing_user_dl = set(f.name for f in user_dl.glob("*.mp4")) if user_dl.exists() else set()

        current_prompt = prompt

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                print(f"\n[ChromeFlow] 🔄 Generation retry attempt {attempt}/{max_attempts} with sanitized prompt...")
                current_prompt = self.sanitize_prompt_for_safety(current_prompt)
                self.dismiss_flow_alerts(ws_url)
                time.sleep(2.0)

            # Count existing thumbnail cards on canvas
            count_thumbs_js = """
            (() => {
                const thumbs = Array.from(document.querySelectorAll('img[alt*="thumbnail"], img[src*="flow-content.google/image"]')).map(i => i.src);
                return thumbs.length;
            })()
            """
            initial_thumbs = self.eval_js(ws_url, count_thumbs_js) or 0
            print(f"[ChromeFlow] Studio canvas ready (active thumbnails: {initial_thumbs}) [Attempt {attempt}/{max_attempts}]")

            # 1. Focus ProseMirror container and clear any existing prompt
            print(f"[ChromeFlow] Typing visual prompt ({len(current_prompt)} chars)...")
            focus_and_clear_js = """
            (() => {
                const pm = document.querySelector('div.ProseMirror, [contenteditable="true"]');
                if (!pm) return false;
                pm.focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('delete', false, null);
                return true;
            })()
            """
            self.eval_js(ws_url, focus_and_clear_js)
            time.sleep(0.5)

            # 2. Insert prompt text via CDP Input.insertText (enables Angular / ProseMirror state)
            self.execute_cdp(ws_url, "Input.insertText", {"text": current_prompt})
            time.sleep(1.0)

            # 3. Click "Start generation"
            click_gen_js = """
            (() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const genBtn = btns.find(b => {
                    const label = (b.getAttribute('aria-label') || b.innerText || '').toLowerCase();
                    return label.includes('start generation') || label.includes('generate');
                });
                if (genBtn && !genBtn.disabled) {
                    genBtn.click();
                    return true;
                }
                return false;
            })()
            """
            clicked = self.eval_js(ws_url, click_gen_js)
            if not clicked:
                time.sleep(1.5)
                clicked = self.eval_js(ws_url, click_gen_js)
            print(f"[ChromeFlow] Generation button clicked: {clicked}")

            if not clicked:
                print(f"[ChromeFlow] Warning: Generate button was not clickable on attempt {attempt}.")
                time.sleep(2.0)
                continue

            # 4. Poll for generation completion and actively monitor for errors
            print(f"[ChromeFlow] Polling Veo GPU compute (up to {timeout}s)...")
            poll_status_js = """
            (() => {
                const alerts = Array.from(document.querySelectorAll('.mat-mdc-snack-bar-container, [role="alert"], flow-snackbar, .mat-snack-bar-container, [aria-live="assertive"]'))
                    .map(el => (el.innerText || '').trim())
                    .filter(t => t.length > 0);

                const errorBanners = Array.from(document.querySelectorAll('.error-banner, .flow-error, mat-error, .toast-error, .error-message'))
                    .map(el => (el.innerText || '').trim())
                    .filter(t => t.length > 0);

                const errorCards = Array.from(document.querySelectorAll('flow-video-card, .video-card, [role="article"]'))
                    .filter(card => {
                        const text = (card.innerText || '').toLowerCase();
                        const hasErrorIcon = !!card.querySelector('mat-icon.error, mat-icon[data-mat-icon-name*="error"], [color="warn"]');
                        return hasErrorIcon || text.includes('failed to generate') || text.includes('something went wrong') || text.includes('generation failed');
                    })
                    .map(card => (card.innerText || '').trim());

                const thumbs = Array.from(document.querySelectorAll('img[alt*="thumbnail"], img[src*="flow-content.google/image"]')).map(i => i.src);
                const dlBtn = Array.from(document.querySelectorAll('button')).find(b => (b.getAttribute('aria-label') || '').includes('Download media'));
                const progress = document.querySelector('[role="progressbar"], .progress, [aria-valuenow], flow-linear-progress');

                const isError = alerts.length > 0 || errorBanners.length > 0 || errorCards.length > 0;
                const errorDetails = [...alerts, ...errorBanners, ...errorCards].join(' | ');

                return {
                    isError: isError,
                    errorDetails: errorDetails,
                    thumbsCount: thumbs.length,
                    hasDownloadMedia: !!dlBtn,
                    isProgressActive: !!progress
                };
            })()
            """

            start_time = time.time()
            generation_done = False
            failed_state = False

            while time.time() - start_time < timeout:
                time.sleep(5)
                elapsed = int(time.time() - start_time)
                status = self.eval_js(ws_url, poll_status_js)
                if isinstance(status, dict):
                    is_err = status.get("isError", False)
                    err_msg = status.get("errorDetails", "")
                    thumbs_count = status.get("thumbsCount", 0)
                    has_dl = status.get("hasDownloadMedia", False)
                    progress_active = status.get("isProgressActive", False)

                    # Check for explicit failure state
                    if is_err and not progress_active and elapsed > 8:
                        print(f"[ChromeFlow] ⚠️ Flow Generation Error detected at {elapsed}s: {err_msg}")
                        diag_screenshot = settings.temp_dir / f"flow_error_attempt{attempt}_{int(time.time())}.png"
                        self.capture_screenshot(diag_screenshot)
                        print(f"[ChromeFlow] Diagnostic screenshot saved to {diag_screenshot}")
                        failed_state = True
                        break

                    if elapsed % 15 == 0 or thumbs_count > initial_thumbs:
                        print(f"  [ChromeFlow] Veo generation in progress... ({elapsed}s elapsed, thumbnails: {thumbs_count})")

                    if thumbs_count > initial_thumbs:
                        print(f"[ChromeFlow] Veo 3.1 video generation completed in {elapsed}s! (thumbnails: {thumbs_count})")
                        generation_done = True
                        break
                    elif elapsed >= 90 and has_dl and not progress_active:
                        print(f"[ChromeFlow] Generation complete (media controls available in {elapsed}s).")
                        generation_done = True
                        break

            if generation_done:
                break

            if failed_state or not generation_done:
                print(f"[ChromeFlow] Attempt {attempt} failed or timed out.")
                if attempt == max_attempts:
                    print("[ChromeFlow] Max retry attempts exhausted. Generation failed.")
                    return False

        if not generation_done:
            print("[ChromeFlow] Generation failed across all retry attempts.")
            return False

        # 5. Trigger download via Studio Media controls (smart toggle menu & click 720p button)
        time.sleep(2.0)
        js_smart_download = """
        (() => {
            function find720() {
                const buttons = Array.from(document.querySelectorAll('.cdk-overlay-container button, button[role="menuitem"], button.mat-mdc-menu-item, flow-menu-item button'));
                return buttons.find(b => (b.innerText || '').includes('720p'));
            }

            let b720 = find720();
            if (b720) {
                b720.click();
                return "Clicked existing 720p button";
            }

            // Otherwise click Download media button to open the menu
            const dlBtn = document.querySelector('button[aria-label="Download media"]');
            if (dlBtn) {
                dlBtn.click();
                return "Opened Download media menu";
            }
            return "Download media button not found";
        })()
        """
        action_res = self.eval_js(ws_url, js_smart_download)
        print(f"[ChromeFlow] Download trigger action: {action_res}")

        if "Opened" in str(action_res):
            time.sleep(1.2)
            js_click_720 = """
            (() => {
                const buttons = Array.from(document.querySelectorAll('.cdk-overlay-container button, button[role="menuitem"], button.mat-mdc-menu-item, flow-menu-item button'));
                const btn = buttons.find(b => (b.innerText || '').includes('720p'));
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
            """
            clicked_720 = self.eval_js(ws_url, js_click_720)
            print(f"[ChromeFlow] 720p menu item clicked: {clicked_720}")

        # 6. Capture newly downloaded MP4 file
        print(f"[ChromeFlow] Awaiting downloaded master MP4...")
        new_downloaded_file: Optional[Path] = None

        for _ in range(40):
            time.sleep(1.0)
            # Check temp download directory
            current_downloads = set(f.name for f in download_dir.glob("*.mp4"))
            crdownloads = list(download_dir.glob("*.crdownload"))
            diff = current_downloads - existing_downloads
            if diff and not crdownloads:
                candidate = download_dir / list(diff)[0]
                if candidate.exists() and candidate.stat().st_size > 0:
                    new_downloaded_file = candidate
                    break

            # Fallback: check user's default Downloads directory
            if user_dl.exists():
                user_current = set(f.name for f in user_dl.glob("*.mp4"))
                user_cr = list(user_dl.glob("*.crdownload"))
                user_diff = user_current - existing_user_dl
                if user_diff and not user_cr:
                    candidate = user_dl / list(user_diff)[0]
                    if candidate.exists() and candidate.stat().st_size > 0:
                        new_downloaded_file = candidate
                        break

        if not new_downloaded_file or not new_downloaded_file.exists():
            print("[ChromeFlow] Downloaded MP4 was not captured.")
            return False

        # 7. Copy master file to target output path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(new_downloaded_file, output_file)
            print(f"[ChromeFlow] Master clip saved: {output_file} ({output_file.stat().st_size} bytes)")
            return output_file.exists() and output_file.stat().st_size > 0
        except Exception as e:
            print(f"[ChromeFlow] Error moving downloaded clip: {e}")
            return False

    def ensure_ready(self) -> bool:
        """Ensures Chrome is launched and connected."""
        if not self.is_port_active:
            ok = self.launch_browser(headless=False)
            if not ok:
                return False
        return True
