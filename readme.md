# Video Workflow Studio 🎬

An autonomous AI video production studio combining the **Google Antigravity Python SDK**, **Film Skills Cinematography Grammar**, **Google DeepMind Veo Video Generation Engine**, **FFmpeg 8.0.1 Assembly**, and **YouTube Data API v3 Publishing**.

---

## Key Features

1. **Explicit Storyboard Engine**:
   - Automatically calculates scene math: $\text{Total Duration} \div \text{Clip Duration} = N \text{ scenes}$.
   - Generates precise, shot-by-shot storyboards with exact timecodes (`00:00 - 00:08`, `00:08 - 00:16`), framing, camera movement, lighting, action description, narration, and SFX cues.
2. **Hollywood Film Skills & Visual DNA**:
   - Encodes cinema grammar: Shot types (EWS, WS, Cowboy, MCU, Close-Up, Dutch Angle), camera movements (Dolly, Crane, Orbit, Track), 35mm anamorphic lenses, Chiaroscuro lighting, and Kodak 35mm film grain.
   - Extracts and enforces **Visual DNA** from uploaded character/environment reference images to ensure consistent costumes, faces, and settings across shots.
3. **Flawless Scene Continuation**:
   - Automatically extracts the final frame of each scene clip via FFmpeg (`-sseof -0.1`) and feeds it as the seed reference for the subsequent scene.
4. **Automatic or Custom Scene Assembly**:
   - **Automatic Mode**: Automatically stitches clips, renders optical transitions (`xfade` dissolves, fade-to-black), and multiplexes ambient audio/voiceover.
   - **Custom Specification Mode**: Generates `storyboard.json` allowing you to inspect, re-order, customize transitions, or re-render single scenes (`--re-render-scene 3`).
5. **3D Spatial Stage Blocking & Continuity Engine**:
   - Defines normalized 3D stage coordinates ($X, Y \in [-1.0, 1.0]$, $Z \in [0.0, 3.0]$) for character placement, facing angles ($0^\circ-360^\circ$), eye-line vectors, and physical poses.
   - Enforces the **180-Degree Action Axis** to eliminate cross-cut spatial disorientation.
   - Locks **Tracked Scene Objects** (e.g. golden wedding ring in crystal goblet, crystal water pod, velvet bowtie, brass key, kelp altar) to persistent surface anchors, preventing AI object and character teleportation across cuts.
6. **Visual Storyboard Mockups & Named Asset Generator**:
   - Generates cinema-grade 1280x720 production mockup cards (`mockups/epXX/`) featuring 2D top-down stage maps, camera FOV frustum cones, character nodes with facing arrows, tracked objects, 180° action lines, visual frame previews, and structured Veo prompt boxes.
   - Outputs named character asset cards (`assets/characters/`) and named scene object cards (`assets/objects/`).
7. **Google Flow Failure Detection & Auto-Recovery**:
   - Real-time DOM inspection for snackbars, error banners, and generation failure cards.
   - Automatic prompt sanitization to safely rewrite noir/violence trigger keywords.
   - Automatic alert dismissal and 3-attempt retry loop with diagnostic error screenshot capture.
8. **Mini Endpoints / API Bridge (`server.py`)**:
   - High-performance FastAPI server providing REST endpoints for other applications, webhooks, or frontends to control the pipeline.
9. **YouTube Data API v3 Automation**:
   - Automated resumable video upload, chapters in descriptions, SEO tags, custom thumbnail attachment, and privacy settings (`private`, `unlisted`, `public`).

---

## Quickstart

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:
```env
# Provider: "chrome", "flow_internal", "useapi", "free", or "genai"
VIDEO_PROVIDER=chrome

# Option 1: Google Flow Ultra via Chrome CDP (flow.google.com/u/5/)
FLOW_USER_INDEX=5
CHROME_DEBUG_PORT=9222

# Option 2: Google Flow Session Cookie Client
GOOGLE_FLOW_COOKIES=your_cookies_here

# Option 3: useapi.net Google Flow API v1 (https://useapi.net/docs/api-google-flow-v1)
USEAPI_TOKEN=your_useapi_token_here
USEAPI_MODEL=veo-3.1-fast

# Direct Google Gemini & Veo API Key (used for Director Agent & fallback)
GEMINI_API_KEY=your_gemini_api_key_here
DIRECTOR_MODEL=gemini-3.5-flash-lite

# Optional:
ELEVENLABS_API_KEY=your_elevenlabs_key
```

For YouTube publishing, place your `client_secret.json` in the root directory.

---

## CLI Usage

### A. Interactive Discussion & Text-First Production (Default)
By default, the studio operates in **Text-First Blueprint Mode**: it generates complete Character Bibles, full screenplays, 3D spatial stage coordinates, persistent tracked object anchors, and exact Veo prompts without consuming media compute or quota!

```bash
# 1. Interactive Writers' Room with the AI Director:
# Converse turn-by-turn to brainstorm characters, twists, and props; type 'generate' when done:
python main.py --discuss

# 2. Text-First Production Blueprint (Generates full instructions & output/<project_id>_production_dossier.txt):
python main.py --mode short --duration 24.0 --concept "Batman inspecting the aquatic marriage crime scene"

# 3. Complete 8-Episode Season Production Book (Generates output/season_01_production_book.txt):
python main.py --season --episodes 8

# 4. Generate 2D spatial storyboard mockups and asset cards:
python main.py --generate-assets
python main.py --generate-mockups --season --episodes 8
```

### B. Media Rendering (`--media` Flag Required)
When you are ready to render actual video clips, compose ambient audio scores, and stitch final master MP4s, simply pass the `--media` flag:

```bash
# 1. Option 1: Google Flow Ultra via Chrome CDP Automation (flow.google.com/u/5/)
python main.py --mode short --duration 24.0 --media --provider chrome --concept "Batman inspecting aquatic crime scene"

# 2. Option 0: 100% Free AI Video Motion Engine (Zero tokens, zero cost!)
python main.py --mode shot --media --provider free --concept "Batman on gargoyle in rain"

# 3. Produce Complete 8-Episode Season Master Videos & Supercut:
python main.py --season --episodes 8 --media --provider chrome

# 4. Resume an existing project and render media:
python main.py --job-id <PROJECT_ID> --media --provider chrome
```

### C. Reviewing & Editing Storyboards
```bash
# Generate storyboard and pause for editing:
python main.py --concept "Noir detective mystery" --review-storyboard

# Re-render a single scene with last-frame continuity chaining:
python main.py --job-id <PROJECT_ID> --re-render-scene 3
python main.py --job-id <PROJECT_ID> --media --stitch-only
```

### D. Publishing to YouTube
```bash
python main.py --job-id <PROJECT_ID> --media --stitch-only --publish-youtube --privacy unlisted
```

---

## REST API Bridge (Mini Endpoints)

Start the API bridge server:
```bash
python main.py --serve --port 8080
# Or: uvicorn server:app --host 0.0.0.0 --port 8080
```

Interactive documentation is available at `http://localhost:8080/docs`.

### Available Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Check system status, FFmpeg, Chrome, and provider keys |
| `POST` | `/api/v1/discuss` | Interactive writers' room discussion with the AI Director |
| `POST` | `/api/v1/storyboard/create` | Generates explicit shot-by-shot storyboard JSON |
| `GET` | `/api/v1/storyboard/{project_id}` | Retrieves existing storyboard |
| `GET` | `/api/v1/dossier/{project_id}` | Retrieves complete text production blueprint and instructions |
| `GET` | `/api/v1/screenplay/{project_id}` | Retrieves full Hollywood screenplay transcript |
| `GET` | `/api/v1/characters/{project_id}` | Retrieves pre-production Character Bible |
| `PUT` | `/api/v1/storyboard/{project_id}` | Updates scene prompts, camera angles, or transitions |
| `POST` | `/api/v1/generate/{project_id}` | Dispatches Veo generation for all scenes (or single scene) |
| `POST` | `/api/v1/render/{project_id}` | Compiles master MP4 with FFmpeg transitions and soundtrack |
| `POST` | `/api/v1/publish/{project_id}` | Uploads rendered video to YouTube |
| `POST` | `/api/v1/season/book` | Generates and returns Season 1 master production book (text-only) |
| `POST` | `/api/v1/season/run` | Triggers multi-episode season production (`generate_media=true` for video) |
| `GET` | `/api/v1/jobs/{project_id}` | Live job status, clip paths, and progress |

---

## Running Automated Tests

Run the full unit and integration test suite (60 tests):
```bash
python -m pytest tests/test_studio.py -v
```

