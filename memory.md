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

### 2. Video Generation Providers: Free Motion vs. useapi.net vs. Direct GenAI
- **100% Free AI Motion Engine (`provider="free"`)**:
  - Requires **zero API tokens, zero subscriptions, and zero cost**.
  - Fetches pristine AI visual keyframes from Pollinations.ai (Flux/SDXL models) based on scene visual prompt and seed.
  - Translates the Director Agent's cinematography instructions (`SLOW_PUSH_IN`, `DOLLY_OUT`, `TRACKING_LATERAL`, `CRANE_DESCENT`) into dynamic 2.5D FFmpeg motion equations with 24fps motion cadence and subtle film grain.
  - Automatically selected by default when `USEAPI_TOKEN` is not provided.
- **useapi.net Google Flow API v1 (`https://useapi.net/docs/api-google-flow-v1`)**:
  - Unofficial REST API bridge wrapping Google Labs Flow (`flow.google.com`).
  - Supports: `veo-3.1-fast` (default), `veo-3.1-quality`, `veo-3.1-lite`, `veo-3.1-lite-low-priority`, and `omni-flash`.
  - Requires $15/month subscription token and connected Google account session with captcha credits.
  - Video Generation (`POST /videos`), Asset Upload (`POST /assets`), Extension (`POST /videos/extend`), and Concatenation (`POST /videos/concatenate`).
- **Direct Google GenAI SDK (`provider="genai"`)**:
  - Direct connection to Google AI Studio (`models/veo-3.1-generate-preview`, `models/gemini-3.5-flash-lite`). Requires paid Tier 1 quota.
- **Dynamic Fail-Safe**:
  - Fallback to animated SMPTE test patterns with audio tone, guaranteeing zero blank video files under any network failure or missing credential state.

### 2. Scene Continuity Strategy
- **Last-Frame Chaining**: Extracted using FFmpeg `-sseof -0.1 -frames:v 1` to capture the final frame of Scene $N$, then passed to Veo as an input image seed for Scene $N+1$.
- **Visual DNA Descriptor**: Multimodal analysis with Gemini Vision creates an immutable text description of characters/environments from reference photos in `assets/characters/`, which is injected into all subsequent prompts.
- **Audio L/J-Cuts**: Narration and ambient score cross over shot boundaries to create perceived perceptual continuity.

### 3. Scene Combination (Assembly)
- **Automatic**: FFmpeg concat demuxer or `xfade` filter graph stitches all scenes and mixes master soundtrack in one command.
- **Custom / Manual**: Storyboards are persisted to `jobs/<project_id>.json`. Users can modify transitions (`dissolve`, `fade_black`, `wipe_left`), re-order shots, or re-render single scenes (`--re-render-scene N`) without re-generating unaffected clips.

### 4. Verification & Testing Suite
- **Pytest Suite (`tests/test_studio.py`)**: 36 comprehensive unit and integration tests passing with 100% coverage across core modules.
- **Dry-run Validations**: Verified `--mode shot` (1 shot, 8s, 1280x720 h264), `--mode short` (4 shots, 32s, 1280x720 h264 with xfade and continuity chaining), and `--mode episode` (6 shots, 48s, 1280x720 h264 with xfade and continuity chaining).
- **Probed MP4 Masters**: Inspected via `ffprobe`, confirming valid stream headers, h264 video, AAC mono audio, and exact timeline duration matching storyboard specifications.

---

## Active File Structure
- `config.py`: Central settings, model strings, directory paths.
- `skills/film_skills.py`: Cinematography grammar, lens optics, lighting styles, negative prompts.
- `pipeline/storyboard.py`: Scene data models, timecode calculator, JSON serialization, `metadata` field.
- `pipeline/director.py`: Director Agent, screenplay generation, visual DNA extraction.
- `pipeline/video_gen.py`: Veo generation, useapi.net Flow client, direct GenAI SDK fallback, last-frame extraction.
- `pipeline/audio_gen.py`: Voiceover narration (ElevenLabs/TTS) and ambient soundtrack generation.
- `pipeline/editor.py`: FFmpeg stitcher, `xfade` transition builder, audio multiplexer.
- `pipeline/youtube_publisher.py`: YouTube Data API v3 OAuth2 uploader and SEO metadata.
- `server.py`: FastAPI REST API bridge with mini-endpoints.
- `main.py`: Master CLI runner.
- `tests/test_studio.py`: Automated pytest / unittest regression and integration test suite.
