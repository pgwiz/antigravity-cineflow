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

### 2. Google Flow vs. Google Veo
- The generative video engine powering Google Flow is **Veo** (`veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`).
- The pipeline directly calls the official `google-genai` Veo API via `client.models.generate_videos(...)`, providing native programmatic access to the exact Flow video generation models.

### 2. Scene Continuity Strategy
- **Last-Frame Chaining**: Extracted using FFmpeg `-sseof -0.1 -frames:v 1` to capture the final frame of Scene $N$, then passed to Veo as an input image seed for Scene $N+1$.
- **Visual DNA Descriptor**: Multimodal analysis with Gemini Vision creates an immutable text description of characters/environments from reference photos in `assets/characters/`, which is injected into all subsequent prompts.
- **Audio L/J-Cuts**: Narration and ambient score cross over shot boundaries to create perceived perceptual continuity.

### 3. Scene Combination (Assembly)
- **Automatic**: FFmpeg concat demuxer or `xfade` filter graph stitches all scenes and mixes master soundtrack in one command.
- **Custom / Manual**: Storyboards are persisted to `jobs/<project_id>.json`. Users can modify transitions (`dissolve`, `fade_black`, `wipe_left`), re-order shots, or re-render single scenes (`--re-render-scene N`) without re-generating unaffected clips.

---

## Active File Structure
- `config.py`: Central settings, model strings, directory paths.
- `skills/film_skills.py`: Cinematography grammar, lens optics, lighting styles, negative prompts.
- `pipeline/storyboard.py`: Scene data models, timecode calculator, JSON serialization.
- `pipeline/director.py`: Director Agent, screenplay generation, visual DNA extraction.
- `pipeline/video_gen.py`: Veo generation, async polling, last-frame extraction.
- `pipeline/audio_gen.py`: Voiceover narration (ElevenLabs/TTS) and ambient soundtrack generation.
- `pipeline/editor.py`: FFmpeg stitcher, `xfade` transition builder, audio multiplexer.
- `pipeline/youtube_publisher.py`: YouTube Data API v3 OAuth2 uploader and SEO metadata.
- `server.py`: FastAPI REST API bridge with mini-endpoints.
- `main.py`: Master CLI runner.
