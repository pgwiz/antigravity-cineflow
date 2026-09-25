# Changelog (`changelog.md`)

All notable changes to the Video Workflow Studio are documented in this file.

## [1.3.1] - 2026-09-25

### Fixed & Hardened
- **Google Flow Duration Snapping (`pipeline/video_gen.py`)**: Snapped requested durations to Google Flow supported set `[4, 6, 8, 10]` with upward tie-breaking `(abs(x - dur_int), -x)` to prevent clip truncation.
- **Aspect Ratio Normalization (`pipeline/video_gen.py`)**: Added full aspect ratio mapping and synthetic/free motion support for `1:1` (720x720), `4:3` (960x720), and `3:4` (720x960) alongside `16:9` and `9:16`.
- **Fail-Fast Polling & Error Recovery (`pipeline/video_gen.py`)**:
  - Immediate abort on polling HTTP 400/401/402/403/404 errors.
  - Detected and raised errors from `failureReasons`, `code >= 400`, or `"error"` in polling payloads without explicit `failed` status, eliminating 10-minute timeout hangs.
  - Hardened `extend_video` to raise error on completed response with empty media items.
  - Safe asset upload email quotation with `urllib.parse.quote` and size limits (20MB image, 100MB video).
  - Verified non-empty file size (`stat().st_size > 0`) in `extract_last_frame` and `download_file`.
- **FFmpeg Stitching & Transition Resilience (`pipeline/editor.py`)**:
  - Dynamically probed clip durations using `ffprobe` (`get_clip_duration`) with configurable `ffprobe_binary` in `config.py`.
  - Added null safety for `transition_to_next` when scenes lack transition configs and clamped duration to `max(0.05, min(trans_dur, dur * 0.5))`.
  - Scoped temporary files (`{output_file.stem}_temp_stitched.mp4` and `{output_path.stem}_concat_list.txt`) to prevent race collisions during concurrent stitching runs.
- **Continuity Chaining on Single-Scene Re-Renders (`main.py`, `server.py`)**:
  - Populated `target_scene.reference_image_path` from `prev_scene.last_frame_path` using robust list-index matching `target_idx` in both CLI and server background tasks.
  - Enabled line buffering on `sys.stdout` and `sys.stderr` in `main.py`.
- **FastAPI Endpoints & Aliases (`server.py`)**:
  - Provided default instances for `RenderRequest` and `PublishRequest` to prevent HTTP 422 errors on empty POST bodies.
  - Added route aliases: `/api/v1/character-bible/{project_id}`, `/health`, `/character-bible/{project_id}`, `/storyboard/{project_id}`, and `/screenplay/{project_id}`.
- **Test Suite Expansion (`tests/test_studio.py`)**:
  - Expanded test suite from 26 to 36 tests covering duration snapping, extended aspect ratios, upload limits, polling errors, route aliases, default POST bodies, safe None transitions, and CLI single-scene re-render continuity. 100% pass rate.

## [1.3.0] - 2026-09-25

### Added
- **100% Free AI Video Generation Provider (`--provider free`)**:
  - Implemented `_generate_free_motion_clip` in `pipeline/video_gen.py`.
  - Integrates free Pollinations.ai visual generation (Flux/SDXL models) requiring **zero API keys, zero subscriptions, and zero cost**.
  - Maps Director Agent camera directions (`SLOW_PUSH_IN`, `DOLLY_OUT`, `TRACKING_LATERAL`, `CRANE_DESCENT`) directly to FFmpeg 2.5D optical motion equations with cinematic 24fps motion blur and subtle celluloid grain.
  - Automatically extracts last frames for continuous scene chaining and stitches with ambient audio into finished 720p/1080p MP4 master videos.
  - Defaults to `provider="free"` when `USEAPI_TOKEN` is not present, enabling immediate out-of-the-box video creation.

## [1.2.1] - 2026-09-25

### Fixed & Hardened
- **Scene Model Metadata Field (`pipeline/storyboard.py`)**: Added `metadata: Dict[str, Any]` to `Scene` model, preventing `AttributeError` when recording `mediaGenerationId` during video generation.
- **Direct GenAI SDK Compatibility (`pipeline/video_gen.py`)**: Corrected `GenerateVideosConfig` parameter from `durationSeconds` to `duration_seconds` and updated seed image loading to use `types.Image.from_file` with binary save fallback.
- **useapi.net Google Flow Client Hardening (`pipeline/video_gen.py`)**:
  - Token whitespace trimming in `_headers()`.
  - File size validation and empty file checks in `upload_asset()`.
  - Dedicated Google account email propagation across `create_character()`, `extend_video()`, and `concatenate_videos()`.
  - Robust aspect ratio normalization (`16:9`, `landscape`, `wide` -> `landscape`; `9:16`, `portrait`, `vertical` -> `portrait`).
  - Safe JSON response parsing and dictionary validation during async polling to prevent crashes from transient non-JSON gateway responses.
  - Verification of downloaded video file size before declaring scene generation successful.
- **Video Editor & Audio Multiplexing (`pipeline/editor.py`)**:
  - Used `shutil.move` for cross-filesystem file replacement during stitching.
  - Explicit stream mapping (`-map 0:v:0 -map 1:a:0`) in `_mux_audio` to ensure master soundtrack is mixed without stream collision.
- **Dynamic Audio Fades (`pipeline/audio_gen.py`)**: Dynamically calculated fade-in/fade-out times in `_generate_ambient_bed` to support short audio segments without clipping.
- **Screenplay Guard (`pipeline/director.py`)**: Added defensive fallback scene creation in `_decompose_to_shots` when screenplay scenes are empty.
- **FastAPI Bridge Hardening (`server.py`)**: Added 400 Bad Request exception handling in `render_master_endpoint` for unrendered scenes and warning logs in background tasks.

### Added
- **Comprehensive Test Suite (`tests/test_studio.py`)**: 26 unit and integration tests verifying data models, cinematography grammar, useapi client methods, FFmpeg stitching and last-frame extraction, FastAPI endpoints, and edge-case fallbacks.
- **Git Ignore**: Added `.pytest_cache/` to `.gitignore`.

## [1.2.0] - 2026-09-25

### Added
- **useapi.net Google Flow API v1 Integration (`pipeline/video_gen.py`)**:
  - Full REST client `UseApiGoogleFlowClient` implementing official endpoints from `https://useapi.net/docs/api-google-flow-v1`.
  - Supports Google Flow AI models: `veo-3.1-fast`, `veo-3.1-quality`, `veo-3.1-lite`, `veo-3.1-lite-low-priority`, and `omni-flash`.
  - Continuation Chaining via Asset Uploads (`POST /assets`): Uploads extracted last frames from previous scenes to retrieve `mediaGenerationId` for I2V continuation (`startImage`).
  - Persistent Character Entities (`POST /characters`): Bundles reference images and personality notes into character reference strings (`@character_1`).
  - Server-Side Video Extension (`POST /videos/extend`): Extends Veo clips by 8 seconds starting from the last second of the source clip.
  - Server-Side Video Concatenation (`POST /videos/concatenate`): Combines multiple generated clips server-side with overlap trimming (`trimStart: 1.0`).
- **Dynamic Fail-Safe Preview Generation**:
  - Upgraded synthetic fallback generator to produce animated SMPTE color bars and audio test tone so dry runs and preview renders are never blank black screens.
- **Provider Switching in CLI and API**:
  - Added `--provider useapi` and `--provider genai` to `main.py`.
  - Added `--useapi-model` to select between fast, quality, lite, and omni models.
  - Updated `/api/v1/health` and `/api/v1/generate/{project_id}` in `server.py` to support dynamic provider switching.

## [1.1.0] - 2026-09-25

### Added
- **Pre-Production Character Bible**:
  - Automatically defines all characters (appearance, wardrobe fabrics, vocal cadence, backstory, Want vs. Need, and immutable AI prompt anchors) *before* writing the screenplay.
  - Injects character prompt anchors into every Veo video prompt to guarantee visual consistency across shots.
- **Standard Hollywood Screenplay Transcript Engine**:
  - Formats scripts to professional cinema standards: Sluglines (`INT./EXT. LOCATION - TIME`), present-tense action blocks, centered character cues, parentheticals, and spoken dialogue.
  - Supports sound cues (`SOUND:`, `SOUND (O.S.):`) and dramatic beats (Inciting Incident, Climax, Reveal).
- **Dual Exposure via CLI & REST API**:
  - CLI flags: `--show-screenplay` and `--show-characters`.
  - REST endpoints: `GET /api/v1/screenplay/{project_id}` and `GET /api/v1/characters/{project_id}`.
- **Configured Working API Key**:
  - Activated user Gemini API key with verified access to `gemini-3.5-flash-lite`, `veo-3.1-generate-preview`, and `veo-3.1-fast-generate-preview`.

## [1.0.0] - 2026-09-25

### Added
- **Explicit Storyboard Engine**:
  - Automatically calculates scene math based on target duration and clip length ($T \div 8.0\text{s} = N\text{ scenes}$).
  - Computes exact timecodes (`00:00 - 00:08`, `00:08 - 00:16`), framing, camera movement, lighting, lens, color science, action description, narration, and SFX cues.
  - JSON serialization/deserialization with `jobs/<project_id>.json`.
- **Hollywood Film Skills Taxonomy (`skills/film_skills.py`)**:
  - Full taxonomy for Shot Types (EWS, WS, Cowboy, MCU, Close-Up, Dutch Angle, Bird's Eye).
  - Camera Movements (Dolly In/Out, Crane Descent, Steadicam Orbit, Tracking).
  - Optics & Lenses (35mm Anamorphic, 50mm Prime, 85mm Telephoto, 24mm Wide).
  - Lighting & Color Science (Chiaroscuro, Rembrandt, Neon Cyber Noir, Volumetric Rays, Kodak Vision3 500T 35mm grain).
  - Standardized negative prompt filtering.
- **Reference Image & Visual DNA Support**:
  - Gemini Vision extraction of character and environment styles from `assets/characters/` and `assets/environments/`.
  - Continuous Visual DNA prompt injection for consistent characters across shots.
- **Flawless Scene Continuation**:
  - Automatic last-frame extraction via FFmpeg (`-sseof -0.1`) and Image-to-Video seed chaining into consecutive Veo calls.
- **Veo Video Generation Engine (`pipeline/video_gen.py`)**:
  - Direct integration with `google-genai` Veo models (`veo-3.1-generate-preview`, `veo-2.0-generate-001`).
  - Asynchronous polling with backoff and timeout handling.
  - High-fidelity synthetic preview generator for dry-run testing without expending credits.
- **Audio & Soundtrack Engine (`pipeline/audio_gen.py`)**:
  - ElevenLabs voiceover narration synthesis and ambient cinematic synth tone generator.
- **Video Assembly & Editing (`pipeline/editor.py`)**:
  - Automatic FFmpeg concat demuxer assembly.
  - Custom transition filter graph (`xfade` dissolves, fade-to-black, wipes).
  - Audio multiplexing and soundtrack synchronization.
- **YouTube Data API v3 Publisher (`pipeline/youtube_publisher.py`)**:
  - OAuth2 resumable chunked video uploading.
  - Automated SEO title, description with chapter timestamps, tags, and custom thumbnail attachment.
- **FastAPI Mini Endpoints REST Bridge (`server.py`)**:
  - Endpoints: `/api/v1/health`, `/api/v1/storyboard/create`, `/api/v1/storyboard/{id}`, `/api/v1/generate/{id}`, `/api/v1/render/{id}`, `/api/v1/publish/{id}`, `/api/v1/jobs/{id}`.
- **Master CLI (`main.py`)**:
  - Production scopes: `--mode shot`, `--mode short`, `--mode episode`.
  - Flags for `--dry-run`, `--review-storyboard`, `--re-render-scene`, `--stitch-only`, `--publish-youtube`, `--serve`.
