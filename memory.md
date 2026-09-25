# Video Workflow Studio Memory (`memory.md`)

## System Environment
- **Platform**: Windows 10/11 x64
- **Python**: 3.11.9
- **FFmpeg**: Version 8.0.1 (with libx264, libx265, whisper, aac, full build)
- **Active Gemini API Key**: Configured in `.env` (supports `gemini-3.5-flash-lite`, `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`)
- **Primary AI SDKs**: `google-genai` (v2.10.0), `google-api-python-client` (v2.193.0), `google-antigravity` (v0.1.18 verified)
- **Web Framework**: FastAPI (v0.115.0) + Uvicorn (v0.30.6)

---

## Architectural Decisions & Core Findings

### 1. Pre-Production Character Bible & Screenplay
- Defined *before* generating scene shots to ensure psychological authenticity and visual consistency.
- Extracts immutable **AI Visual Prompt Anchors** for each character that are permanently injected into all Veo prompts.
- Screenplays follow standard Hollywood formatting: Sluglines (`EXT. LOCATION - TIME`), action descriptions in present tense, centered character names, parentheticals, and dialogue.

### 2. Video Generation Providers
- **Option 1: Google Flow Ultra Chrome Automation (`provider="chrome"`)**:
  - Implemented in `pipeline/chrome_flow.py` using Chrome DevTools Protocol (CDP) WebSocket and Selenium.
  - Connects to user Google account by index (e.g. `https://flow.google.com/u/5/`) or persistent profile directory (`temp/flow_profile`).
  - Interactive one-time login via `python main.py --login-flow`. Sessions persist indefinitely without repeated MFA challenges.
  - Automates prompt input, model selection (`veo-3.1-fast`, `veo-3.1-lite`, `veo-3.1-quality`), seed-frame upload for continuity, and MP4 downloading.
- **Option 2: Google Flow Session Cookie Client (`provider="flow_internal"`)**:
  - Implemented in `pipeline/flow_client.py` for direct HTTP requests using session cookies (`__Secure-1PSID`, `__Secure-3PSID`, `SAPISID`).
  - Configured via `GOOGLE_FLOW_COOKIES` in `.env`.
- **Option 3: useapi.net Google Flow API v1 (`provider="useapi"`)**:
  - Unofficial REST API bridge wrapping Google Labs Flow (`flow.google.com`).
  - Supports `veo-3.1-fast` (default), `veo-3.1-quality`, `veo-3.1-lite`, `veo-3.1-lite-low-priority`, and `omni-flash`.
  - Configured via `USEAPI_TOKEN` and `USEAPI_FLOW_EMAIL` in `.env`.
- **Option 0: 100% Free AI Motion Engine (`provider="free"`)**:
  - Requires **zero API tokens, zero subscriptions, and zero cost**.
  - Fetches pristine AI visual keyframes from Pollinations.ai (Flux/SDXL models) based on scene visual prompt and seed.
  - Translates Director Agent camera directions (`SLOW_PUSH_IN`, `DOLLY_OUT`, `TRACKING_LATERAL`, `CRANE_DESCENT`) into dynamic 2.5D FFmpeg motion equations with 24fps cinema cadence and fine celluloid grain.
  - Safe automatic fallback if external cloud or browser sessions are unavailable.
- **Direct Google GenAI SDK (`provider="genai"`)**:
  - Direct connection to Google AI Studio (`models/veo-3.1-generate-preview`). Requires paid Tier 1 quota.

### 3. Scene Continuity & Season Architecture
- **Last-Frame Chaining**: Extracted using FFmpeg `-sseof -0.1 -frames:v 1` to capture the final frame of Scene $N$, then passed to Veo as an input image seed for Scene $N+1$.
- **8-Episode Ironical Batman Season Engine (`pipeline/season.py`)**:
  - Pre-Production Character Bible: Batman / Bruce Wayne, Lady Guppy (The Koi Bride in brass water-pod), Sir Longneck (The Giraffe Groom in silk bowtie), The Mystery Cat (The Mastermind in trenchcoat & fedora), and Alfred Pennyworth.
  - Full 8-episode narrative arc *"The Aquatic Mammalian Matrimony"* (60s episodes, 60 total scenes).
  - Generates individual episode masters (`output/episode_XX_master.mp4`) and concatenated season supercuts (`output/season_01_complete_master.mp4`).

### 4. Verification & Testing Suite
- **Pytest Suite (`tests/test_studio.py`)**: 44 comprehensive unit and integration tests passing (100% pass rate) covering data models, cinematography, useapi client, Chrome automation, Flow client cookies, FFmpeg stitching, last-frame chaining, FastAPI routes, and Season orchestrator math.
- **Dry-run Validations**: Verified `--mode shot` (8s), `--mode short` (32s), `--mode episode` (48s), and `--season --episodes 8` (480s / 8 minutes season).
- **Probed MP4 Masters**: Inspected via `ffprobe`, confirming valid stream headers, h264 video, AAC audio, and exact timeline duration matching storyboard specifications.

---

## Active File Structure
- `config.py`: Central settings, model strings, directory paths, flow user index, chrome debug port.
- `skills/film_skills.py`: Cinematography grammar, lens optics, lighting styles, negative prompts.
- `pipeline/storyboard.py`: Scene data models, timecode calculator, JSON serialization, `metadata` field.
- `pipeline/director.py`: Director Agent, screenplay generation, visual DNA extraction.
- `pipeline/chrome_flow.py`: Google Flow Ultra Chrome CDP automation driver.
- `pipeline/flow_client.py`: Google Flow session cookie internal client.
- `pipeline/video_gen.py`: Multi-provider video generation engine (Chrome, Flow internal, useapi.net, Free, GenAI).
- `pipeline/season.py`: 8-episode season orchestrator, screenplay builder, episode assembly.
- `pipeline/audio_gen.py`: Voiceover narration (ElevenLabs/TTS) and ambient soundtrack generation.
- `pipeline/editor.py`: FFmpeg stitcher, `xfade` transition builder, audio multiplexer, multi-episode concatenator.
- `pipeline/youtube_publisher.py`: YouTube Data API v3 OAuth2 uploader and SEO metadata.
- `server.py`: FastAPI REST API bridge with mini-endpoints (`/api/v1/season/run`, `/api/v1/health`, etc.).
- `main.py`: Master CLI runner (`--season`, `--login-flow`, `--provider`, etc.).
- `tests/test_studio.py`: Automated pytest / unittest regression and integration test suite (44 tests).
