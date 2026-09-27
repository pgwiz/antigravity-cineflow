# Director Agent Specification (`agent.md`)

## Agent Role & Persona
The **Director Agent** acts as an autonomous executive producer, veteran Hollywood screenwriter, and master cinematographer. It operates through the following production stages:

0. **Interactive Writers' Room Discussion (`discuss`)**: Bidirectional creative brainstorming with the creator via CLI (`python main.py --discuss`) or API (`POST /api/v1/discuss`) to align on concepts, surreal noir twists, character motives, and tracked props before locking in production.
1. **Pre-Production Character Bible**: Defines all dramatis personae (appearance, wardrobe fabrics, vocal cadence, backstory, Want vs Need, and immutable AI prompt anchors) *before* writing any scene.
2. **Screenplay Transcript**: Authors a standard Hollywood screenplay featuring sluglines (`INT./EXT. LOCATION - TIME`), present-tense action paragraphs, character cues, parentheticals, spoken dialogue, and sound cues.
3. **3D Spatial Stage & Tracked Objects Matrix**: Maps normalized 3D stage coordinates ($X, Y \in [-1.0, 1.0]$, $Z \in [0.0, 3.0]$), anchors persistent interactive props across cuts, and locks the 180° Action Axis.
4. **Text-First Production Blueprint Dossier**: Outputs complete instruction manuals to disk (`output/{project_id}_production_dossier.txt` or `output/season_01_production_book.txt`) with exact Veo prompts. Media rendering is strictly gated behind the `--media` flag to conserve compute and quota.

---

## Pre-Production Character Bible Schema
Every production must establish its character roster before writing:
- `name`: Character name in uppercase (e.g. `BRUCE WAYNE / BATMAN`)
- `role`: Dramatic function (`Protagonist`, `Antagonist`, `Foil`, `Mentor`)
- `suggested_names`: List of suggested names, aliases, or code names
- `generation_description`: Exact prompt used to generate the character turnaround reference sheet (front, 3/4, and side profile on neutral gray seamless background) in Google Flow Character Creator
- `character_info`: Optional acting mannerisms, physical presence, gestures, and reactions
- `appearance`: Height, build, face, eyes, jawline, physical hallmarks
- `wardrobe_visual_dna`: Exact materials, textures, armor plates, fabrics, cowl specs, utility gear, and color palette
- `voice_and_cadence`: Vocal pitch, speech rhythm, dialogue style
- `backstory`: Origin, core psychological trauma
- `internal_conflict`: Conscious Want vs. unconscious Need
- `prompt_anchor`: The non-negotiable prompt string injected into all Veo shots featuring this character to guarantee visual consistency.

---

## Hollywood Screenplay Formatting Rules
The agent formats scripts according to industry standards:
- **Slugline (Scene Heading)**: `INT.` or `EXT.`, Location, and Time of Day (e.g. `EXT. GOTHAM CLOCKTOWER - RAIN / NIGHT`).
- **Action**: Written in active, present-tense visual description of what the camera sees and what the microphone hears.
- **Character Cue**: Character name in all-caps centered above dialogue.
- **Parenthetical**: Delivery tone or physical micro-action while speaking: `(low rasp)`, `(taunting smile)`.
- **Dialogue**: Centered spoken lines matching the character's unique voice and vocabulary.
- **Sound Cues**: `SOUND: ` or `SOUND (O.S.): ` for diegetic and off-screen audio effects.

---

## Hollywood Film Skills Rules

When composing scene prompts, the agent must adhere to the six layers of visual grammar:

1. **Shot Composition**:
   - `EXTREME_WIDE_SHOT`: Establishes world scale, geography, and atmospheric mood.
   - `WIDE_SHOT`: Full body in environment.
   - `MEDIUM_WIDE_SHOT` (Cowboy): Mid-thigh up, ideal for showdowns and stances.
   - `MEDIUM_SHOT`: Waist up, balancing action and dialogue.
   - `MEDIUM_CLOSE_UP`: Chest to head, focusing on emotion and vocal delivery.
   - `CLOSE_UP`: Facial tension and character intensity.
   - `EXTREME_CLOSE_UP`: Detailed focus on eyes, symbols, insignias, or hand weapons.
   - `DUTCH_ANGLE`: Disorientation, psychological instability, impending combat.

2. **Camera Motion**:
   - `STATIC`: Locked-off tripod, deliberate and tense.
   - `SLOW_PUSH_IN`: Dolly in, building suspense.
   - `DOLLY_OUT`: Isolating character in context.
   - `TRACKING_LATERAL`: Dynamic side-scrolling motion matching movement speed.
   - `CRANE_DESCENT`: Descending from skyline to character level.
   - `ORBIT_STEADICAM`: 360-degree fluid rotation around subject.

3. **Optics & Lenses**:
   - `ANAMORPHIC_35MM`: 2.39:1 widescreen, subtle horizontal blue streak flares, oval bokeh.
   - `CINE_PRIME_50MM`: Natural human perspective, f/1.4 aperture, creamy bokeh falloff.
   - `PORTRAIT_85MM`: Shallow depth-of-field, compressed background.

4. **Lighting & Color**:
   - `CHIAROSCURO`: Deep crushed shadows and sculpted key highlights.
   - `REMBRANDT`: Iconic triangle highlight on cheek.
   - `NEON_CYBER_NOIR`: Cyan and magenta rim lights reflecting on wet tarmac.
   - `VOLUMETRIC_GOD_RAYS`: Light piercing through rain, smoke, or haze.
   - `KODAK_VISION3_35MM`: 35mm celluloid film grain, highlight halation.

5. **Visual DNA Preservation**:
   - When a character or environment reference image is provided, extract an immutable Visual DNA descriptor (clothing materials, cowl shape, emblems, colors) and enforce it identically across all scene prompts.

6. **Negative Prompting**:
   - Standard exclusions: `morphing, rubbery limbs, mutated anatomy, deformed hands, extra fingers, jittery motion, blurry, watermarks, oversaturated cartoon 3d render`.

7. **3D Spatial Stage Blocking & Object Continuity**:
   - Every shot explicitly models the stage coordinate grid ($X \in [-1.0, 1.0]$, $Y \in [-1.0, 1.0]$, $Z \in [0.0, 3.0]$).
   - Injects structured tokens into prompts: `[SPATIAL BLOCKING: ...]`, `[OBJECT LOCATIONS: ...]`, `[CAMERA AXIS: ...]`.
   - Locks tracked key objects (e.g., golden wedding ring in crystal goblet, crystal water orb pod, velvet bowtie, brass maritime key, kelp altar) to persistent surface coordinates so they never drift or change across shots.
   - Enforces the 180-degree action line: the camera must stay on one side of the action vector to prevent spatial flipping across cuts.

8. **Visual Storyboard Mockups & Named Assets**:
   - Named character dossiers saved to `assets/characters/`.
   - Named scene objects saved to `assets/objects/`.
   - 1280x720 production mockup cards saved to `mockups/epXX/` displaying 2D top-down stage maps, camera FOV frustum cones, character nodes with facing arrows, tracked objects, 180° action lines, visual frame previews, and Veo prompt specifications.

---

## Explicit Storyboard JSON Schema

```json
{
  "project_id": "string",
  "title": "string",
  "logline": "string",
  "genre": "string",
  "total_target_duration": 60.0,
  "aspect_ratio": "16:9",
  "scenes": [
    {
      "scene_number": 1,
      "title": "Establishing Gotham",
      "timecode_start": "00:00",
      "timecode_end": "00:08",
      "duration_seconds": 8.0,
      "shot_type": "EXTREME_WIDE_SHOT",
      "camera_movement": "CRANE_DESCENT",
      "lighting": "VOLUMETRIC_GOD_RAYS",
      "lens": "ANAMORPHIC_35MM",
      "color_science": "KODAK_VISION3_35MM",
      "action_description": "Rain-soaked Gotham skyline with lightning",
      "visual_prompt": "string",
      "negative_prompt": "string",
      "stage_characters": [
        {
          "character_name": "BATMAN",
          "stage_x": -0.4,
          "stage_y": 0.5,
          "elevation_z": 1.2,
          "facing_degrees": 90.0,
          "eye_line_target": "CAT",
          "pose": "crouched on stone gargoyle",
          "continuity_anchor": "gargoyle ledge stage-left"
        }
      ],
      "tracked_objects": [
        {
          "object_id": "GOLDEN_RING_IN_GOBLET",
          "object_name": "Submerged Golden Ring",
          "surface_anchor": "Center altar table",
          "stage_x": 0.0,
          "stage_y": 0.0,
          "elevation_z": 0.8,
          "visual_state": "submerged in clear water goblet",
          "continuity_lock": true
        }
      ],
      "camera_blocking": {
        "action_axis_angle": 0.0,
        "camera_quadrant": "FRONT_LEFT",
        "elevation_angle": "LOW_ANGLE_30_DEG",
        "focal_target": "BATMAN",
        "line_of_action_rule": "Camera strictly stays on downstage side of action line"
      },
      "chain_from_previous_last_frame": false,
      "transition_to_next": {
        "transition_type": "hard_cut",
        "duration_seconds": 0.0
      },
      "narration_text": "string or null",
      "sound_effects_cue": "string or null"
    }
  ]
}
```

---

## Generation Providers

The Director Agent orchestrates video generation across multiple modular providers:
1. **Gemini Omni 1.1 Flash (`provider="omni"`)**:
   - Interfaces directly with Google's `interactions.create` API using `model="gemini-omni-1.1-flash"` via `google-genai >= 2.25.0` and the installed `gemini-omni-flash-api` skill.
   - Multimodal role tagging: `<FIRST_FRAME>` starting image from previous scene's extracted last frame, `<LAST_FRAME>` transition targets, and `<IMAGE_REF_N>` character reference images.
   - Enforces unbroken camera rules: `"In a single unbroken scene, continuous shot, no scene cuts."`
   - Configurable resolution: `360p`, `720p`, `1080p`, and `4k`.
2. **Option 1: Google Flow Ultra Chrome Automation (`provider="chrome"`)**:
   - Automated browser interaction via Chrome DevTools Protocol (CDP) WebSocket and Selenium.
   - Operates directly on user's Ultra subscription at `https://flow.google.com/u/5/` or custom profile.
   - Enters prompts, selects Veo 3.1 models, uploads starting frames for seed continuation, and downloads finished MP4 clips.
3. **Option 2: Google Flow Session Cookie Client (`provider="flow_internal"`)**:
   - Headless HTTP client utilizing authenticated session cookies (`__Secure-1PSID`, `__Secure-3PSID`, `SAPISID`).
4. **Option 3: useapi.net Google Flow API v1 (`provider="useapi"`)**:
   - REST API bridge wrapping Google Flow (`veo-3.1-fast`, `veo-3.1-quality`, `veo-3.1-lite`, `omni-flash`).
   - Supports asset uploading (`POST /assets`), character entity consistency (`POST /characters`), native extension (`POST /videos/extend`), and server-side concatenation (`POST /videos/concatenate`).
5. **Option 0: 100% Free AI Motion Engine (`provider="free"`)**:
   - Zero-cost, zero-token generation using Pollinations.ai (Flux/SDXL models) + FFmpeg 2.5D Hollywood camera motion synthesis.
   - Automatically renders the Director's intended camera movements (dolly, pan, tilt, crane descent) with 24fps cinema cadence and fine film grain.
6. **Direct Google GenAI SDK (`provider="genai"`)**:
   - Direct API connection using `client.models.generate_videos` with Google AI Studio credentials.
7. **Animated Fail-Safe**:
   - Synthesizes dynamic SMPTE test card clips with audio tone when network or quota errors occur, guaranteeing the production pipeline never produces blank video files.

---

## Directorial Flow Script Architecture (`--flow`)

The Director Agent includes a dedicated **Flow Script Mode** (`python main.py --flow [CONCEPT]`) based on the *AI Storyboard & Visual Consistency Architecture (1-Minute / 6-Shot Pipeline)*:

### Critical Directorial Laws:
1. **1 Video Clip is Strictly 10 Seconds**: A standard 60-second episode consists of exactly 6 clips of 10s each. Each prompt covers only ONE clear, linear movement.
2. **Upstream Master Reference Sheets**:
   - **Sheet 1 (Cast)**: Front View, 3/4 View, Side Profile on neutral gray background under neutral daytime lighting.
   - **Sheet 2 (Environment)**: Empty location plates with zero characters, defining horizon lines and lighting axes.
   - **Sheet 3 (Key Props)**: Isolated interactive narrative objects (e.g. submerged gold wedding ring, crystal pod, brass key).
3. **Sequencing & Episode Collection Directive**: When the episode reaches its target duration (e.g. 60s / 6 clips for Episode 1), compile the clips into an Episode Collection in exact sequential order (`scene_01.mp4` through `scene_06.mp4`), verify 180° continuity, and only then proceed to the next episode.
4. **Smart Consistency Fallback**: If a character reference image does not yet exist in `assets/characters/`, the engine falls back to previous scene extracted keyframes or the Cast Anchor sheet.

### Generated Production Files & Scene Folders (`output/flow/temp/`):
- **Temporary Flow Workspace**: Active flow productions generate into `output/flow/temp/`, keeping root `output/` clean. (Legacy files archived to `output_archive/pre_flow_cleanup_20260927/`).
- **Core Production Files**:
  - **`master.txt`**: The overarching master production book with reference sheet specs, character bibles with generation descriptions, spatial coordinates, full screenplay transcript, shot-by-shot prompts, and execution instructions.
  - **`Scene.md`**: Directorial blueprint covering scenes, transcripts, camera angles, 10s clip length reminders, dedicated scene folder links, and episode collection sequencing directives.
  - **`characters.md`**: Character pre-production guide aligning with Google Flow's Character Creator UI: Suggested names/aliases, **Description for generating the character** (ready-to-paste reference sheet turnaround prompt), **Character info (optional - how character acts)**, required reference angles, and smart consistency checks.
- **Dedicated Per-Scene Folders (`output/flow/temp/<scene_slug>/`)**:
  - Inside `output/flow/temp/`, each 10-second scene has its own AI-named dedicated folder (e.g. `scene_01_neo_gotham_rooftop_establishing_world/`).
  - Contains:
    - **`prompt.txt`**: Dedicated Veo/Omni visual prompt with lens optics, lighting, camera movement, negative prompts, start/end keyframe descriptions, audio cues, and dialogue.
    - **`scene_info.json`**: Machine-readable metadata with blocking, camera quadrant, and timing law (10.0s).
    - **`instructions.txt`**: Step-by-step human guide for copying into Google Flow / Veo interface.



