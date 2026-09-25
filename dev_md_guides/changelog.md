# Session Operational Changelog
_Append-only. Newest first. Never edit past entries._

## [2026-09-25 09:05:00 UTC] — Branch `main` (HEAD: `origin/main`)
- **Event**: useapi.net Google Flow API v1 & Animated SMPTE Fail-Safe Integration
- **Operational Scope**: Implemented `UseApiGoogleFlowClient` in `pipeline/video_gen.py`, added provider switching to CLI and REST server, added SMPTE test bar generator, updated docs and environment configurations.

### AST & Code Modifications
- `config.py`: Added `video_provider`, `useapi_token`, `useapi_model`, `useapi_base_url`, `useapi_account_email`.
- `pipeline/video_gen.py`: Implemented `UseApiGoogleFlowClient` and dual-provider support in `VideoGenerationEngine`.
- `main.py`: Added `--provider` and `--useapi-model` CLI flags.
- `server.py`: Added provider parameter to `/api/v1/generate/{project_id}` and provider telemetry to `/api/v1/health`.
- `.env.sample`: Added useapi.net Google Flow configuration variables.
- `readme.md`, `changelog.md`, `memory.md`, `agent.md`: Synced documentation.

---

## [2026-09-25 08:42:25 UTC] — Branch `not-a-git-repo` (HEAD: `none`)
- **Event**: Automated Context Compaction
- **Operational Scope**: Synchronized repository ground-truth into `dev_md_guides/`

### AST & Code Modifications
- *No AST code modifications detected in active diff.*

---
