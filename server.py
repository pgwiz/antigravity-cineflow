"""FastAPI Mini Endpoints & Integration Bridge for Video Workflow Studio."""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from config import settings
from pipeline.storyboard import Storyboard, Scene, SceneStatus
from pipeline.director import DirectorAgent
from pipeline.video_gen import VideoGenerationEngine
from pipeline.audio_gen import AudioEngine
from pipeline.editor import VideoEditor
from pipeline.youtube_publisher import YouTubePublisher
from pipeline.season import SeasonOrchestrator

app = FastAPI(
    title="Video Workflow Studio API Bridge",
    description="Programmatic REST API for AI video storyboarding, Veo generation, FFmpeg editing, and YouTube publishing.",
    version="1.0.0",
)

# Active in-memory jobs cache
active_storyboards: Dict[str, Storyboard] = {}

class CreateStoryboardRequest(BaseModel):
    concept: str = Field(..., description="Narrative concept or screenplay idea")
    total_duration: float = Field(default=60.0, description="Total target length in seconds")
    clip_duration: float = Field(default=8.0, description="Target duration per shot in seconds")
    aspect_ratio: str = Field(default="16:9", description="'16:9' or '9:16'")
    genre: str = Field(default="Cinematic Drama", description="Genre or stylistic theme")
    character_reference_image: Optional[str] = Field(default=None, description="Path to uploaded character reference image")
    environment_reference_image: Optional[str] = Field(default=None, description="Path to environment reference image")

class RenderRequest(BaseModel):
    use_transitions: bool = Field(default=True, description="Whether to apply cinematic xfade transitions between clips")
    include_soundtrack: bool = Field(default=True, description="Whether to generate and mix ambient score")

class PublishRequest(BaseModel):
    privacy_status: str = Field(default="private", description="'private', 'unlisted', or 'public'")
    thumbnail_path: Optional[str] = Field(default=None, description="Optional custom thumbnail image path")

class SeasonRunRequest(BaseModel):
    episodes: int = Field(default=8, ge=1, le=8, description="Number of episodes to produce (1-8)")
    aspect_ratio: str = Field(default="16:9", description="'16:9' or '9:16'")
    provider: Optional[str] = Field(default=None, description="Generation provider: 'free', 'chrome', 'flow_internal', 'useapi'")
    dry_run: bool = Field(default=False, description="Whether to run synthetic preview clips")

@app.get("/api/v1/health")
def health_check():
    """System health and dependency check."""
    import subprocess
    ffmpeg_ok = False
    try:
        res = subprocess.run([settings.ffmpeg_binary, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ffmpeg_ok = (res.returncode == 0)
    except Exception:
        ffmpeg_ok = False

    return {
        "status": "healthy",
        "ffmpeg_available": ffmpeg_ok,
        "video_provider": settings.video_provider,
        "flow_user_index": settings.flow_user_index,
        "chrome_available": Path(settings.chrome_binary).exists(),
        "flow_internal_configured": bool(settings.google_flow_cookies),
        "useapi_configured": bool(settings.useapi_token),
        "useapi_model": settings.useapi_model,
        "gemini_api_key_configured": bool(settings.gemini_api_key),
        "youtube_secrets_configured": settings.youtube_client_secrets_file.exists(),
        "video_model": settings.video_model,
        "director_model": settings.director_model,
    }

@app.post("/api/v1/storyboard/create", response_model=Dict[str, Any])
def create_storyboard_endpoint(req: CreateStoryboardRequest):
    """Generates an explicit shot-by-shot storyboard with calculated scene math."""
    director = DirectorAgent()
    
    char_img = Path(req.character_reference_image) if req.character_reference_image else None
    env_img = Path(req.environment_reference_image) if req.environment_reference_image else None

    storyboard = director.create_storyboard(
        concept=req.concept,
        total_duration=req.total_duration,
        clip_duration=req.clip_duration,
        aspect_ratio=req.aspect_ratio,
        genre=req.genre,
        character_reference_image=char_img,
        environment_reference_image=env_img,
    )

    # Save to disk
    job_file = settings.jobs_dir / f"{storyboard.project_id}.json"
    storyboard.save(job_file)
    active_storyboards[storyboard.project_id] = storyboard

    return {
        "project_id": storyboard.project_id,
        "title": storyboard.title,
        "scene_count": len(storyboard.scenes),
        "total_target_duration": storyboard.total_target_duration,
        "character_bible": [c.model_dump() for c in storyboard.screenplay.characters] if storyboard.screenplay else [],
        "screenplay_transcript": storyboard.screenplay.format_screenplay_transcript() if storyboard.screenplay else "",
        "storyboard": storyboard.model_dump(),
        "breakdown_markdown": storyboard.format_breakdown_markdown(),
    }

@app.get("/api/v1/screenplay/{project_id}")
def get_screenplay_endpoint(project_id: str):
    """Returns the full Hollywood formatted screenplay transcript."""
    sb_data = get_storyboard_endpoint(project_id)
    sb = Storyboard.model_validate(sb_data)
    if not sb.screenplay:
        raise HTTPException(status_code=404, detail="Screenplay not attached to this storyboard")
    return {
        "project_id": project_id,
        "title": sb.screenplay.title,
        "logline": sb.screenplay.logline,
        "transcript": sb.screenplay.format_screenplay_transcript(),
        "character_bible_markdown": sb.screenplay.format_character_bible_markdown(),
    }

@app.get("/api/v1/characters/{project_id}")
def get_characters_endpoint(project_id: str):
    """Returns the pre-production Character Bible defined before shooting."""
    sb_data = get_storyboard_endpoint(project_id)
    sb = Storyboard.model_validate(sb_data)
    if not sb.screenplay:
        raise HTTPException(status_code=404, detail="Character bible not attached")
    return {
        "project_id": project_id,
        "characters": [c.model_dump() for c in sb.screenplay.characters],
        "character_bible_markdown": sb.screenplay.format_character_bible_markdown(),
    }

@app.get("/api/v1/character-bible/{project_id}")
def get_character_bible_endpoint(project_id: str):
    """Returns the pre-production Character Bible (alias for character inspection)."""
    return get_characters_endpoint(project_id)

@app.get("/health")
def health_root():
    return health_check()

@app.get("/character-bible/{project_id}")
def get_character_bible_root(project_id: str):
    return get_characters_endpoint(project_id)

@app.get("/storyboard/{project_id}")
def get_storyboard_root(project_id: str):
    return get_storyboard_endpoint(project_id)

@app.get("/screenplay/{project_id}")
def get_screenplay_root(project_id: str):
    return get_screenplay_endpoint(project_id)

@app.get("/api/v1/storyboard/{project_id}")
def get_storyboard_endpoint(project_id: str):
    """Retrieves an existing storyboard by project ID."""
    if project_id in active_storyboards:
        return active_storyboards[project_id].model_dump()
    
    job_file = settings.jobs_dir / f"{project_id}.json"
    if job_file.exists():
        sb = Storyboard.load(job_file)
        active_storyboards[project_id] = sb
        return sb.model_dump()
    
    raise HTTPException(status_code=404, detail="Project ID not found")

@app.put("/api/v1/storyboard/{project_id}")
def update_storyboard_endpoint(project_id: str, updated_storyboard: Storyboard):
    """Allows an external program to update scene prompts, camera angles, or transitions."""
    job_file = settings.jobs_dir / f"{project_id}.json"
    updated_storyboard.save(job_file)
    active_storyboards[project_id] = updated_storyboard
    return {"status": "updated", "project_id": project_id, "scenes": len(updated_storyboard.scenes)}

def _bg_generate(project_id: str, scene_number: Optional[int], dry_run: bool, provider: Optional[str] = None):
    """Background task worker for video clip generation."""
    sb = active_storyboards.get(project_id)
    if not sb:
        job_file = settings.jobs_dir / f"{project_id}.json"
        sb = Storyboard.load(job_file)
        active_storyboards[project_id] = sb

    engine = VideoGenerationEngine(provider=provider)
    project_output = settings.output_dir / project_id
    scenes_dir = project_output / "scenes"

    if scene_number is not None:
        target_idx = next((i for i, s in enumerate(sb.scenes) if s.scene_number == scene_number), None)
        if target_idx is not None:
            target_scene = sb.scenes[target_idx]
            # If continuity chaining is enabled, seed from previous scene's last frame
            if target_scene.chain_from_previous_last_frame and target_idx > 0:
                prev = sb.scenes[target_idx - 1]
                if prev.last_frame_path and Path(prev.last_frame_path).exists():
                    target_scene.reference_image_path = prev.last_frame_path
            engine.generate_scene_clip(target_scene, scenes_dir, aspect_ratio=sb.aspect_ratio, dry_run=dry_run)
        else:
            print(f"[Server bg_generate] Warning: Scene {scene_number} not found in project {project_id}")
    else:
        engine.generate_all_scenes(sb, project_output, dry_run=dry_run)

    # Save state
    job_file = settings.jobs_dir / f"{project_id}.json"
    sb.save(job_file)

@app.post("/api/v1/generate/{project_id}")
def trigger_generation_endpoint(
    project_id: str,
    background_tasks: BackgroundTasks,
    scene_number: Optional[int] = Query(None, description="Optional single scene number to re-generate"),
    dry_run: bool = Query(False, description="Whether to run in synthetic test mode"),
    provider: Optional[str] = Query(None, description="'useapi' or 'genai' (defaults to config)"),
):
    """Dispatches Veo video generation for all scenes (or a specific scene)."""
    # Verify exists
    get_storyboard_endpoint(project_id)
    background_tasks.add_task(_bg_generate, project_id, scene_number, dry_run, provider)
    return {
        "status": "dispatched",
        "project_id": project_id,
        "provider": provider or settings.video_provider,
        "target_scene": scene_number or "all",
        "dry_run": dry_run,
    }

@app.post("/api/v1/render/{project_id}")
def render_master_endpoint(project_id: str, req: RenderRequest = RenderRequest()):
    """Combines all scene clips with FFmpeg transitions and soundtrack into final master MP4."""
    if req is None:
        req = RenderRequest()
    sb = active_storyboards.get(project_id)
    if not sb:
        job_file = settings.jobs_dir / f"{project_id}.json"
        if not job_file.exists():
            raise HTTPException(status_code=404, detail="Project ID not found")
        sb = Storyboard.load(job_file)
        active_storyboards[project_id] = sb

    project_output = settings.output_dir / project_id
    final_master_path = project_output / f"{project_id}_final_master.mp4"

    # Audio generation
    soundtrack_path = None
    if req.include_soundtrack:
        audio_engine = AudioEngine()
        soundtrack_path = audio_engine.generate_soundtrack_for_storyboard(sb, project_output)

    # Video assembly
    editor = VideoEditor()
    try:
        out_video = editor.stitch_storyboard(
            storyboard=sb,
            output_file=final_master_path,
            soundtrack_path=soundtrack_path,
            use_transitions=req.use_transitions,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sb.final_video_path = str(out_video)
    sb.save(settings.jobs_dir / f"{project_id}.json")

    return {
        "status": "rendered",
        "project_id": project_id,
        "final_video_path": str(out_video),
        "file_exists": out_video.exists(),
        "file_size_bytes": out_video.stat().st_size if out_video.exists() else 0,
    }

@app.post("/api/v1/publish/{project_id}")
def publish_endpoint(project_id: str, req: PublishRequest = PublishRequest(), dry_run: bool = Query(False)):
    """Uploads rendered final master to YouTube using YouTube Data API v3."""
    if req is None:
        req = PublishRequest()
    sb = active_storyboards.get(project_id)
    if not sb:
        job_file = settings.jobs_dir / f"{project_id}.json"
        if not job_file.exists():
            raise HTTPException(status_code=404, detail="Project ID not found")
        sb = Storyboard.load(job_file)
        active_storyboards[project_id] = sb

    if not sb.final_video_path or not Path(sb.final_video_path).exists():
        raise HTTPException(status_code=400, detail="Final master video not rendered yet. Call /api/v1/render first.")

    publisher = YouTubePublisher()
    thumb = Path(req.thumbnail_path) if req.thumbnail_path else None
    
    video_id = publisher.upload_video(
        video_path=Path(sb.final_video_path),
        storyboard=sb,
        privacy_status=req.privacy_status,
        thumbnail_path=thumb,
        dry_run=dry_run,
    )

    return {
        "status": "published" if video_id else "failed",
        "project_id": project_id,
        "youtube_video_id": video_id,
        "youtube_watch_url": f"https://youtu.be/{video_id}" if video_id else None,
    }

@app.get("/api/v1/jobs/{project_id}")
def get_job_status(project_id: str):
    """Returns complete real-time status of all scene clips and rendering output."""
    return get_storyboard_endpoint(project_id)

@app.post("/api/v1/season/run")
def run_season_endpoint(req: SeasonRunRequest, background_tasks: BackgroundTasks):
    """Triggers autonomous multi-episode season production."""
    orchestrator = SeasonOrchestrator(provider=req.provider or settings.video_provider)
    manifest = orchestrator.run_season(
        episodes_count=req.episodes,
        aspect_ratio=req.aspect_ratio,
        dry_run=req.dry_run,
    )
    return {
        "status": "completed",
        "manifest": manifest,
    }
