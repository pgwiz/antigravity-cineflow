# Codebase Architecture & Directory Dependency Graph
_Last regenerated: 2026-09-25 08:42:25 UTC by dev-md-compactor_

## Project Manifests & Build Tools
- `requirements.txt`

## Module Directory Topography

### `jobs/`
- **Files (3)**: `b03af6e7.json, db31433b.json, f46da2aa.json`

### `output/b03af6e7/`
- **Files (2)**: `b03af6e7_master.mp4, master_soundtrack.aac`

### `output/b03af6e7/scenes/`
- **Files (4)**: `scene_01.mp4, scene_01_last_frame.png, scene_02.mp4, scene_02_last_frame.png`

### `output/db31433b/`
- **Files (1)**: `db31433b_master.mp4`

### `output/db31433b/scenes/`
- **Files (4)**: `scene_01.mp4, scene_01_last_frame.png, scene_02.mp4, scene_02_last_frame.png`

### `output/f46da2aa/`
- **Files (2)**: `f46da2aa_master.mp4, master_soundtrack.aac`

### `output/f46da2aa/scenes/`
- **Files (4)**: `scene_01.mp4, scene_01_last_frame.png, scene_02.mp4, scene_02_last_frame.png`

### `pipeline/`
- **Files (7)**: `__init__.py, audio_gen.py, director.py, editor.py, storyboard.py, video_gen.py, youtube_publisher.py`
- **Discovered Module Dependencies**: `PIL, audio_gen, config, datetime, director, editor, elevenlabs, enum, google, google_auth_oauthlib, googleapiclient, json, os, pathlib, pipeline, pydantic, skills, storyboard, subprocess, time, typing, uuid, video_gen, youtube_publisher`

### `root/`
- **Files (8)**: `agent.md, changelog.md, config.py, main.py, memory.md, readme.md, requirements.txt, server.py`
- **Discovered Module Dependencies**: `argparse, config, dotenv, fastapi, os, pathlib, pipeline, pydantic, subprocess, sys, typing, uvicorn`

### `skills/`
- **Files (2)**: `__init__.py, film_skills.py`
- **Discovered Module Dependencies**: `enum, film_skills, pydantic, typing`

## Environment & Directory Catalog Reference
- Central Catalog: `dev_md_guides/directory.md` (sample committed as `dev_md_guides/directory.md.sample`).
- All workspace paths, servers, backend links, frontend links, and external endpoints are centralized in this catalog.
- Invariant: Never hardcode local filesystem paths or network URLs directly across project markdown files.

## Credentials & Secrets Reference
- Central Secrets Schema: `dev_md_guides/credentials.md` (sample committed as `dev_md_guides/credentials.md.sample`).
- Real secrets and sensitive tokens are kept strictly local in `credentials.md` and MUST NEVER be committed to GitHub.
- Invariant: Never commit credentials to GitHub; if the user ever specifies committing credentials, the agent must first explicitly warn the user about critical security risks.

## Architectural Invariants & Boundary Rules
- Internal modules should adhere to defined dependency boundaries without cyclic imports.
- Configuration, secrets, and environment overrides must not be hardcoded in application logic.
- Zero Hardcoded Endpoints: Do not hardcode machine directories, server IPs, backend links, or frontend links across markdown docs; resolve and reference them via directory.md (only directory.md.sample is committed to version control).
- Zero Credential Exposure: Never commit credentials.md or real secrets to git/GitHub. Only credentials.md.sample with sanitized placeholders is tracked. If the user explicitly asks to commit credentials, issue a critical security warning and require confirmation before proceeding.
