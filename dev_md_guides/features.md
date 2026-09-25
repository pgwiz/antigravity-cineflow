# Feature Roadmap & SDD Progress Matrix
_Last updated: 2026-09-25_

## Done
- [x] **Hollywood Screenplay Scriptwriter**: Standard industry screenplay format (Scene headings / sluglines, present-tense action, character cues, parentheticals, dialogue, and sound FX cues).
- [x] **Pre-Production Character Bible**: Generates detailed character dossiers (Appearance, Wardrobe DNA, Vocal Cadence, Backstory, Want/Need, and AI Visual Prompt Anchors) *before* scene generation.
- [x] **Film Skills Cinematography Grammar**: Six-layer visual taxonomy covering Shot Composition (EWS to ECU), Camera Movement (Dolly, Crane, Orbit, Track), Optics & Lenses (35mm Anamorphic, 50mm Prime), Lighting (Chiaroscuro, Volumetric God Rays, Neon Noir), and Kodak Vision3 500T 35mm grain.
- [x] **Flawless Scene Continuation**: Automated FFmpeg last-frame extraction (`-sseof -0.1`) and Image-to-Video seed chaining for continuous camera motion across 8-10s Veo cuts.
- [x] **Google Veo Video Engine Integration**: Native integration with Google DeepMind Veo models (`veo-3.1-generate-preview`, `veo-3.1-fast-generate-preview`) via `google-genai` SDK with async polling and timeout management.
- [x] **FFmpeg 8.0.1 Assembly & Transitions**: Automatic concat demuxer stitching and customizable `xfade` optical transitions (dissolve, fade-to-black, wipe).
- [x] **Audio Engine & Soundtrack**: Background ambient synth and rain soundscape generation with audio-video multiplexing.
- [x] **YouTube Data API v3 Distribution**: Resumable chunked uploading, SEO title, description with chapter timestamps, tags, and privacy management (`private`, `unlisted`, `public`).
- [x] **FastAPI REST API Bridge**: High-performance REST endpoints (`/api/v1/storyboard/create`, `/api/v1/screenplay/{id}`, `/api/v1/characters/{id}`, `/api/v1/generate/{id}`, `/api/v1/render/{id}`, `/api/v1/publish/{id}`).
- [x] **Master CLI**: Complete command-line interface supporting scopes (`--mode shot`, `short`, `episode`), `--dry-run`, `--show-screenplay`, `--re-render-scene`, and `--stitch-only`.

## In Progress
- [ ] **Multi-character Dialogue Lip-sync & Dubbing**: Automatic phoneme alignment with generated audio tracks.
- [ ] **Interactive Visual Storyboard Web UI**: Lightweight React/Vite dashboard connecting to FastAPI bridge.

## Planned
- [ ] **Automated B-Roll Insertion**: Secondary camera cutaway generation during monologue sequences.
- [ ] **Multi-Platform Syndication**: Direct publishing to TikTok, Instagram Reels, and X alongside YouTube.

## Removed
- [x] None to date.
