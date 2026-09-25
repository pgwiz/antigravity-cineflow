# Changelog (`changelog.md`)

All notable changes to the Video Workflow Studio are documented in this file.

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
