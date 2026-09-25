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
5. **Mini Endpoints / API Bridge (`server.py`)**:
   - High-performance FastAPI server providing REST endpoints for other applications, webhooks, or frontends to control the pipeline.
6. **YouTube Data API v3 Automation**:
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
# Provider: "useapi" (Google Flow via useapi.net) or "genai" (Direct Google AI Studio)
VIDEO_PROVIDER=useapi

# useapi.net Google Flow API v1 (https://useapi.net/docs/api-google-flow-v1)
USEAPI_TOKEN=your_useapi_token_here
USEAPI_MODEL=veo-3.1-fast
# Optional: USEAPI_ACCOUNT_EMAIL=your_dedicated_account@gmail.com

# Direct Google Gemini & Veo API Key (used for Director Agent & fallback)
GEMINI_API_KEY=your_gemini_api_key_here
DIRECTOR_MODEL=gemini-3.5-flash-lite

# Optional:
ELEVENLABS_API_KEY=your_elevenlabs_key
```

For YouTube publishing, place your `client_secret.json` in the root directory.

---

## CLI Usage

### A. Run an Episode / Short Film
```bash
# Generate a test shot (Dry-run with animated SMPTE color bars, zero credits consumed)
python main.py --mode shot --concept "Batman standing on a gothic gargoyle in the rain overlooking Gotham" --dry-run

# Live generation using useapi.net Google Flow API v1 (Veo 3.1 Fast)
python main.py --mode short --duration 24.0 --provider useapi --useapi-model veo-3.1-fast --concept "Cyberpunk detective inspecting neon crime scene"

# Live generation using direct Google AI Studio Veo
python main.py --mode shot --provider genai --concept "Batman descending Wayne Tower"
```

### B. Uploading Reference Images for Character Consistency
Place your reference image in `assets/characters/` and run:
```bash
python main.py --mode episode --duration 90.0 --concept "Batman confronting criminals in an alley" --character-image assets/characters/batman_suit.png
```

### C. Reviewing Storyboard Before Rendering
```bash
# Generate storyboard only for inspection/editing
python main.py --concept "Noir detective mystery" --review-storyboard

# Once edited, resume rendering using the generated Job ID:
python main.py --job-id <PROJECT_ID>
```

### D. Re-rendering a Specific Scene
If Scene 3 needs adjustments:
```bash
python main.py --job-id <PROJECT_ID> --re-render-scene 3
python main.py --job-id <PROJECT_ID> --stitch-only
```

### E. Publishing to YouTube
```bash
python main.py --job-id <PROJECT_ID> --stitch-only --publish-youtube --privacy unlisted
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
| `GET` | `/api/v1/health` | Check system status, FFmpeg availability, and API keys |
| `POST` | `/api/v1/storyboard/create` | Generates explicit shot-by-shot storyboard JSON |
| `GET` | `/api/v1/storyboard/{project_id}` | Retrieves existing storyboard |
| `PUT` | `/api/v1/storyboard/{project_id}` | Updates scene prompts, camera angles, or transitions |
| `POST` | `/api/v1/generate/{project_id}` | Dispatches Veo generation for all scenes (or single scene) |
| `POST` | `/api/v1/render/{project_id}` | Compiles master MP4 with FFmpeg transitions and soundtrack |
| `POST` | `/api/v1/publish/{project_id}` | Uploads rendered video to YouTube |
| `GET` | `/api/v1/jobs/{project_id}` | Live job status, clip paths, and progress |
