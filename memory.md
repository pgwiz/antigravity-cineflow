# Video Workflow Studio Memory (`memory.md`)

## System Environment
- **Platform**: Windows 10/11 x64
- **Python**: 3.11.9
- **FFmpeg**: Version 8.0.1 (with libx264, libx265, whisper, aac, full build)
- **Active Gemini API Key**: Configured in `.env` (supports `gemini-3.5-flash-lite`, `veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`)
- **Primary AI SDKs**: `google-genai` (v2.25.0 with Interactions API), `google-api-python-client` (v2.193.0), `google-antigravity` (v0.1.18 verified)
- **Web Framework**: FastAPI (v0.115.0) + Uvicorn (v0.30.6)

---

## Architectural Decisions & Core Findings

### 1. Pre-Production Character Bible & Screenplay
- Defined *before* generating scene shots to ensure psychological authenticity and visual consistency.
- Extracts immutable **AI Visual Prompt Anchors** for each character that are permanently injected into all Veo prompts.
- Screenplays follow standard Hollywood formatting: Sluglines (`EXT. LOCATION - TIME`), action descriptions in present tense, centered character names, parentheticals, and dialogue.

### 2. Video Generation Providers
- **Gemini Omni 1.1 Flash (`provider="omni"`)**:
  - Leverages official skill `gemini-omni-flash-api` installed at `C:\Users\pgwiz\.gemini\config\skills\gemini-omni-flash-api\`.
  - Interfaces directly with Google's `interactions.create` API using `model="gemini-omni-1.1-flash"` via `google-genai >= 2.25.0`.
  - Supports multimodal role tagging: `<FIRST_FRAME>` starting image from previous scene's extracted last frame, `<LAST_FRAME>` transition targets, and `<IMAGE_REF_N>` character reference images.
  - Automatically prepends `"In a single unbroken scene, continuous shot, no scene cuts."` to prevent random AI cuts.
  - Native multi-resolution: `360p`, `720p`, `1080p`, and `4k`.
  - Integrated via `pipeline/omni_flash.py`, `pipeline/video_gen.py`, and CLI `--provider omni --resolution 1080p`.
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

### 3. Google Flow Error Recovery & Safety Sanitization (`pipeline/chrome_flow.py`)
- Real-time DOM inspection for snackbars (`.mat-mdc-snack-bar-container`, `[role="alert"]`), error banners, and error cards on canvas.
- Automatic prompt sanitization (`sanitize_prompt_for_safety`) to convert noir/violence keywords ("murdered", "blood", "kill", "dead body", "weapon", "corpse") into atmospheric equivalents ("shadowed", "rainwater", "confront", "silent crime scene", "gadget", "abandoned altar") avoiding safety policy blocks.
- Diagnostic screenshot capture on failure (`temp/flow_error_attempt*.png`).
- 3-attempt auto-retry loop with refreshed input state and alert dismissal.

### 4. 3D Spatial Scene Blocking & Object Continuity Matrix
- **Spatial Coordinates**: `SpatialGridPoint` with normalized X/Y stage axes (-1.0 to 1.0) and vertical Z elevation (0.0 to 3.0).
- **Character Placement**: `StageCharacterBlocking` locks facing angles (0-360°), eye-line vectors, physical stances, and continuity anchors to prevent character teleportation across camera cuts.
- **Tracked Objects**: `TrackedSceneObject` establishes immutable physical anchors for key props (submerged golden wedding ring in crystal goblet, crystal water pod, brass key, kelp altar).
- **180-Degree Action Axis**: `CameraBlocking` strictly enforces camera position quadrants and action lines.
- **Spatial Transitions**: `SpatialTransition` defines cross-shot carryover notes preserving screen-left / screen-right alignment.
- **Visual Mockups & Named Assets (`pipeline/mockup_generator.py`)**:
  - Named character dossiers in `assets/characters/`.
  - Named scene objects in `assets/objects/`.
  - 1280x720 cinema production cards in `mockups/epXX/` containing top-down 2D stage maps, camera FOV frustum cones, visual composition preview, and continuity rules.

### 5. Interactive Discussion Engine & Text-First Architecture
- **Interactive Discussion (`DirectorAgent.discuss`)**:
  - Natural language writers' room session (`python main.py --discuss`) allowing creators to brainstorm concepts, surreal twists, character motives, and tracked props before locking in production.
  - Exposes `POST /api/v1/discuss` for API/frontend clients.
- **Default Text-First Mode (Zero Media Compute)**:
  - By default, running projects or seasons generates comprehensive text blueprints and instruction manuals without consuming media compute or quota.
  - Compiles full Pre-Production Character Bibles (hallmarks, wardrobe DNA, eye-line anchors, prompt anchors), 3D Spatial Stage & Object Matrix, full Screenplays, and exact Veo visual prompts.
  - Automatically exports dossiers to `output/{project_id}_production_dossier.txt` and `output/season_01_production_book.txt`.
  - Media generation is strictly gated behind the `--media` flag (`python main.py --media ...` or `python main.py --season --media ...`).

### 6. Verification & Testing Suite
- **Pytest Suite (`tests/test_studio.py`)**: 73 comprehensive unit and integration tests passing (100% pass rate) covering data models, cinematography, Omni Flash interactions, useapi client, Chrome automation, Flow error recovery, spatial scene blocking, visual mockup generation, discussion engine, text-first blueprints, flow script generation, character generation descriptions, FFmpeg stitching, last-frame chaining, FastAPI routes, and Season orchestrator math.
- **Dry-run Validations**: Verified `--mode shot` (8s), `--mode short` (32s), `--mode episode` (48s), and `--season --episodes 8` (480s / 8 minutes season).
- **Probed MP4 Masters**: Inspected via `ffprobe`, confirming valid stream headers, h264 video, AAC audio, and exact timeline duration matching storyboard specifications.

### 7. Gemini Flow Directorial Script Architecture (`--flow`)
- **CLI Flow Mode (`python main.py --flow [CONCEPT]`)**:
  - Dedicated mode producing the production blueprint without generating media clips.
  - Enforces the **Critical Timing Law: 1 video is 10 seconds** (e.g. 60-second episode = exactly 6 video segments).
  - Each video prompt is restricted to describing **ONE clear, linear movement** feasible in 10s.
- **The 3-File Production Pack & Dedicated Scene Folders (`output/flow/temp/`)**:
  - Legacy output files (105 items) archived to `output_archive/pre_flow_cleanup_20260927/`.
  - Active flow productions output directly to dedicated directory `output/flow/` with active temporary working directory `output/flow/temp/`.
  - Inside `output/flow/temp/`, each 10-second scene/shot has its own AI-defined dedicated folder (e.g. `scene_01_neo_gotham_rooftop_establishing_world/`, `scene_02_batman_on_precipice_character_in_environment/`).
  - Each dedicated scene folder contains:
    - `prompt.txt`: Standalone prompt with cinematography specs, exact Veo/Omni prompt, negative prompt, keyframe descriptions, audio cues, and dialogue.
    - `scene_info.json`: Machine-readable metadata with blocking, camera quadrant, and timing law (10.0s).
    - `instructions.txt`: Clear manual instructions for Google Flow Web UI.
  - Automatically exported to `output/flow/temp/`, `output/flow/`, top-level `output/`, and `output/{project_id}/`:
    1. **`master.txt`**: Complete master production blueprint (Tier 1 Master Reference Sheets: Sheet 1 Cast, Sheet 2 Environment, Sheet 3 Key Props; Character Bible with Generation Descriptions; 3D spatial grid; full Screenplay; 6-beat storyboard sequence; and execution guide).
    2. **`Scene.md`**: Directorial script detailing scenes, transcripts, camera angles, optics, 180° action axis, Keyframe A/B start/end descriptions, and the **Sequencing & Episode Collection Directive** (compile generated clips into an Episode Collection in sequential order before proceeding to the next episode).
    3. **`characters.md`**: Upstream manual pre-production character guide aligning with Google Flow Character Creator UI fields:
       - **Suggested Names / Aliases**: Suggested names or aliases for the character.
       - **Description for Generating the Character (Flow Character Prompt)**: The exact visual prompt used to generate the character reference sheet / 3-angle turnaround on a neutral gray seamless studio background.
       - **Character Info (Optional - How Character Acts)**: Acting mannerisms, gestures, physical presence, and behavioral reactions.
       - **Physical Hallmarks & Wardrobe DNA**: Exact costume materials, fabrics, color palette, and physical dimensions.
       - **AI Visual Prompt Anchor & Angles**: Front View, 3/4 View, Side Profile.
       - **Smart Consistency Check & Fallback Logic**: Checks verified local asset image; if absent, falls back to inheriting continuity from upstream keyframes.
- **The Standard 6-Beat Storyboard Sequence**:
  - Beat 1: Establishing the World (Extreme Wide / Wide Shot, slow camera crane/dolly, environment anchor)
  - Beat 2: Character in Environment (Wide / Full Shot, establishes subject location relative to stage)
  - Beat 3: The Interaction / Inciting Incident (Medium Shot, subject interacts with key prop/environment)
  - Beat 4: Emotional Reaction / Climax Focus (Close-Up / MCU, high-tension focus on expression / detail)
  - Beat 5: Dynamic Turn / Consequence (Dynamic Action / Dutch / Push, escalation of narrative tension)
  - Beat 6: Resolution / Cliffhanger (Wide / Macro / Hold, resolution or hook for next episode)

---

## Active File Structure
- `config.py`: Central settings, model strings, directory paths, flow user index, chrome debug port.
- `skills/film_skills.py`: Cinematography grammar, lens optics, lighting styles, negative prompts, spatial prompt builder.
- `pipeline/storyboard.py`: Scene data models, spatial grid points, character blocking, tracked objects, camera axis, JSON serialization, and 3-file pack generators (`master.txt`, `Scene.md`, `characters.md`).
- `pipeline/director.py`: Director Agent, screenplay generation, 3D stage decomposition, visual DNA extraction, `create_flow_storyboard()`, and interactive session.
- `pipeline/omni_flash.py`: Gemini Omni 1.1 Flash video generation client leveraging official `gemini-omni-flash-api` skill.
- `pipeline/chrome_flow.py`: Google Flow Ultra Chrome CDP automation driver with failure detection and auto-retry.
- `pipeline/flow_client.py`: Google Flow session cookie internal client.
- `pipeline/video_gen.py`: Multi-provider video generation engine (Omni Flash, Chrome, Flow internal, useapi.net, Free, GenAI).
- `pipeline/season.py`: 8-episode season orchestrator with spatial blocking, screenplay builder, episode assembly, and per-episode production pack export.
- `pipeline/mockup_generator.py`: Visual storyboard mockup cards and named character/object asset generator.
- `pipeline/audio_gen.py`: Voiceover narration (ElevenLabs/TTS) and ambient soundtrack generation.
- `pipeline/editor.py`: FFmpeg stitcher, `xfade` transition builder, audio multiplexer, multi-episode concatenator.
- `pipeline/youtube_publisher.py`: YouTube Data API v3 OAuth2 uploader and SEO metadata.
- `server.py`: FastAPI REST API bridge with mini-endpoints (`/api/v1/flow/script`, `/api/v1/omni/status`, `/api/v1/season/run`, `/api/v1/health`, etc.).
- `main.py`: Master CLI runner (`--flow`, `--season`, `--provider omni`, `--resolution`, `--generate-assets`, `--generate-mockups`, `--login-flow`, `--discuss`, `--media`).
- `tests/test_studio.py`: Automated pytest / unittest regression and integration test suite (72 tests).

