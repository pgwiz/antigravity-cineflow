"""Master CLI Entrypoint for Video Workflow Studio."""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

from config import settings
from pipeline.storyboard import Storyboard, SceneStatus
from pipeline.director import DirectorAgent
from pipeline.video_gen import VideoGenerationEngine
from pipeline.audio_gen import AudioEngine
from pipeline.editor import VideoEditor
from pipeline.youtube_publisher import YouTubePublisher
from pipeline.chrome_flow import ChromeFlowAutomation
from pipeline.season import SeasonOrchestrator, SEASON_EPISODES
from pipeline.mockup_generator import (
    generate_character_assets,
    generate_object_assets,
    generate_storyboard_mockups,
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Autonomous AI Video Workflow Studio with Antigravity, Film Skills, Veo, and YouTube API."
    )
    # Mode selection
    parser.add_argument(
        "--mode",
        choices=["shot", "short", "episode"],
        default="short",
        help="Scope of production: 'shot' (single 8-10s clip), 'short' (30-60s clip), or 'episode' (2-5 min multi-scene)",
    )
    # Content & Story
    parser.add_argument("--concept", type=str, default="A lone cyberpunk detective in the rain looking at neon skyscrapers in neo-Gotham", help="High-level narrative concept or prompt")
    parser.add_argument("--title", type=str, default="Neon Noir Detective", help="Title of the project or episode")
    parser.add_argument("--genre", type=str, default="Cyberpunk Noir", help="Genre aesthetic")
    parser.add_argument("--duration", type=float, default=24.0, help="Total target duration in seconds")
    parser.add_argument("--aspect", choices=["16:9", "9:16"], default="16:9", help="Video aspect ratio")

    # Reference Assets
    parser.add_argument("--character-image", type=str, default=None, help="Path to character reference image for Visual DNA injection")
    parser.add_argument("--environment-image", type=str, default=None, help="Path to environment reference image")

    # Workflow controls
    parser.add_argument("--dry-run", action="store_true", help="Run full pipeline with synthetic preview clips without consuming API credits")
    parser.add_argument("--show-screenplay", action="store_true", help="Print the full Hollywood screenplay transcript")
    parser.add_argument("--show-characters", action="store_true", help="Print the pre-production Character Bible")
    parser.add_argument("--review-storyboard", action="store_true", help="Pause after creating storyboard.json so you can inspect/edit before rendering")
    parser.add_argument("--re-render-scene", type=int, default=None, help="Specific scene number to re-generate in an existing job")
    parser.add_argument("--stitch-only", action="store_true", help="Skip video generation and only stitch existing rendered scene clips")
    parser.add_argument("--job-id", type=str, default=None, help="Specific job ID to resume, stitch, or re-render")

    # Season Production Options
    parser.add_argument("--season", action="store_true", help="Generate complete multi-episode season (Batman & The Aquatic Mammalian Matrimony)")
    parser.add_argument("--episodes", type=int, default=8, help="Number of episodes to produce for the season (default: 8 episodes x 60s)")

    # Provider Options
    parser.add_argument(
        "--provider",
        choices=["free", "chrome", "flow_internal", "useapi", "genai"],
        default=settings.video_provider,
        help="Video generation provider: 'free' (Zero-cost AI Keyframes + 2.5D Hollywood Motion), 'chrome' (Chrome CDP Automation), 'flow_internal' (Session Cookie), 'useapi' (Google Flow API v1), or 'genai' (Direct Veo)",
    )
    parser.add_argument("--login-flow", action="store_true", help="Launch interactive Chrome window to authenticate Google Flow Ultra (Option 1)")
    parser.add_argument("--extract-cookies", action="store_true", help="Extract authenticated session cookies from Chrome and save to .env (Option 2)")
    parser.add_argument(
        "--useapi-model",
        choices=["veo-3.1-fast", "veo-3.1-quality", "veo-3.1-lite", "veo-3.1-lite-low-priority", "omni-flash"],
        default=settings.useapi_model,
        help="Google Flow AI model on useapi.net (default: veo-3.1-fast)",
    )
    parser.add_argument("--publish-youtube", action="store_true", help="Upload rendered video to YouTube upon completion")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private", help="YouTube video privacy")
    parser.add_argument("--generate-assets", action="store_true", help="Generate named character and object visual asset cards into assets/")
    parser.add_argument("--generate-mockups", action="store_true", help="Generate 2D spatial stage blocking & visual storyboard mockup cards into mockups/")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI bridge server")
    parser.add_argument("--port", type=int, default=8080, help="Port for the API bridge server")

    return parser.parse_args()

def run_server(port: int):
    """Starts Uvicorn server for API bridge."""
    import uvicorn
    print(f"🎬 Starting Video Workflow Studio API Bridge on http://localhost:{port}...")
    uvicorn.run("server:app", host=settings.server_host, port=port, reload=False)

def run_pipeline(args):
    """Executes the autonomous video generation and assembly pipeline."""
    print("=" * 70)
    print("🎬 VIDEO WORKFLOW STUDIO - AUTONOMOUS PRODUCTION PIPELINE")
    print("=" * 70)

    # Calculate target duration based on mode if not explicitly set
    total_dur = args.duration
    if args.mode == "shot":
        total_dur = 8.0
    elif args.mode == "short" and total_dur == 24.0:
        total_dur = 32.0 # 4 scenes

    char_img = Path(args.character_image) if args.character_image else None
    env_img = Path(args.environment_image) if args.environment_image else None

    # 1. Load or Generate Storyboard
    storyboard: Optional[Storyboard] = None
    job_file: Optional[Path] = None

    if args.job_id:
        job_file = settings.jobs_dir / f"{args.job_id}.json"
        if job_file.exists():
            print(f"[Pipeline] Resuming existing project: {args.job_id}")
            storyboard = Storyboard.load(job_file)
        else:
            print(f"[Pipeline] Error: Job file not found: {job_file}")
            sys.exit(1)
    else:
        print(f"\n[Step 1/5] Director Agent generating explicit storyboard...")
        print(f"  Concept: {args.concept}")
        print(f"  Mode: {args.mode.upper()} | Target Duration: {total_dur}s | Aspect Ratio: {args.aspect}")
        
        director = DirectorAgent()
        storyboard = director.create_storyboard(
            concept=args.concept,
            total_duration=total_dur,
            clip_duration=settings.default_clip_duration,
            aspect_ratio=args.aspect,
            character_reference_image=char_img,
            environment_reference_image=env_img,
            genre=args.genre,
        )
        job_file = settings.jobs_dir / f"{storyboard.project_id}.json"
        storyboard.save(job_file)

    # Print Character Bible and Screenplay if requested or present
    if storyboard.screenplay:
        if args.show_characters or True:
            print("\n" + storyboard.screenplay.format_character_bible_markdown())
        if args.show_screenplay:
            print("\n" + "=" * 60)
            print("📜 FULL SCREENPLAY TRANSCRIPT")
            print("=" * 60)
            print(storyboard.screenplay.format_screenplay_transcript())

    # Print explicit breakdown
    print("\n" + storyboard.format_breakdown_markdown())

    if args.review_storyboard:
        print("\n" + "=" * 70)
        print(f"📝 Storyboard saved to: {job_file}")
        print("You can inspect or edit prompts, camera angles, or transitions in the JSON file now.")
        print(f"To resume this project, run: python main.py --job-id {storyboard.project_id}")
        print("=" * 70)
        return

    project_output = settings.output_dir / storyboard.project_id
    project_output.mkdir(parents=True, exist_ok=True)
    scenes_dir = project_output / "scenes"
    scenes_dir.mkdir(exist_ok=True)

    # 2. Video Generation Engine
    if args.useapi_model:
        settings.useapi_model = args.useapi_model
    video_engine = VideoGenerationEngine(provider=args.provider)

    if args.re_render_scene is not None:
        print(f"\n[Step 2/5] Re-rendering Scene {args.re_render_scene:02d} only...")
        target_idx = next((i for i, s in enumerate(storyboard.scenes) if s.scene_number == args.re_render_scene), None)
        if target_idx is None:
            print(f"Scene {args.re_render_scene} not found in storyboard.")
            sys.exit(1)
        target_scene = storyboard.scenes[target_idx]
        # If continuity chaining is enabled, seed from previous scene's last frame
        if target_scene.chain_from_previous_last_frame and target_idx > 0:
            prev = storyboard.scenes[target_idx - 1]
            if prev.last_frame_path and Path(prev.last_frame_path).exists():
                print(f"[Pipeline] 🔗 Propagating Scene {prev.scene_number:02d} last frame for continuity: {prev.last_frame_path}")
                target_scene.reference_image_path = prev.last_frame_path
        video_engine.generate_scene_clip(target_scene, scenes_dir, aspect_ratio=storyboard.aspect_ratio, dry_run=args.dry_run)
        storyboard.save(job_file)
    elif not args.stitch_only:
        print(f"\n[Step 2/5] Generating video clips with Veo Engine (Dry Run: {args.dry_run})...")
        video_engine.generate_all_scenes(storyboard, project_output, dry_run=args.dry_run)
        storyboard.save(job_file)
    else:
        print("\n[Step 2/5] Skipping video clip generation (--stitch-only selected).")

    # 3. Audio & Soundtrack Generation
    print(f"\n[Step 3/5] Audio Engine composing ambient score & voiceover stems...")
    audio_engine = AudioEngine()
    soundtrack = audio_engine.generate_soundtrack_for_storyboard(storyboard, project_output)

    # 4. Assembly & Editing
    print(f"\n[Step 4/5] Video Editor compiling scenes with FFmpeg...")
    editor = VideoEditor()
    final_master = project_output / f"{storyboard.project_id}_master.mp4"
    editor.stitch_storyboard(
        storyboard=storyboard,
        output_file=final_master,
        soundtrack_path=soundtrack,
        use_transitions=True,
    )
    storyboard.save(job_file)

    # 5. YouTube Distribution
    if args.publish_youtube:
        print(f"\n[Step 5/5] YouTube Publisher uploading final master...")
        publisher = YouTubePublisher()
        vid_id = publisher.upload_video(
            video_path=final_master,
            storyboard=storyboard,
            privacy_status=args.privacy,
            dry_run=args.dry_run,
        )
        if vid_id:
            print(f"🎉 Published to YouTube: https://youtu.be/{vid_id}")
    else:
        print("\n[Step 5/5] YouTube publishing skipped (use --publish-youtube to upload).")

    print("\n" + "=" * 70)
    print("✅ PRODUCTION COMPLETE!")
    print(f"📁 Master Video: {final_master}")
    print(f"📄 Storyboard Data: {job_file}")
    print("=" * 70)

def main():
    args = parse_args()
    if args.serve:
        run_server(args.port)
    elif args.login_flow:
        chrome_bot = ChromeFlowAutomation()
        chrome_bot.login_interactive()
    elif args.extract_cookies:
        chrome_bot = ChromeFlowAutomation()
        cookies = chrome_bot.export_and_save_cookies()
        if cookies:
            print("[OK] Successfully extracted cookies and saved to .env!")
        else:
            print("[WARN] No Google cookies found. Make sure Chrome is open and logged in.")
    elif args.generate_assets:
        print("\n🎬 Generating all named character and object visual assets...")
        chars = generate_character_assets()
        objs = generate_object_assets()
        print(f"[OK] Assets generation complete: {len(chars)} character cards, {len(objs)} object cards saved to assets/.")
    elif args.generate_mockups and args.season:
        print(f"\n🎬 Generating 2D spatial storyboard mockup cards for Season ({args.episodes} episodes)...")
        orch = SeasonOrchestrator(provider=args.provider)
        for ep_data in SEASON_EPISODES[:args.episodes]:
            ep_num = ep_data["episode_number"]
            sb = orch.build_episode_storyboard(ep_data, aspect_ratio=args.aspect)
            cards = generate_storyboard_mockups(sb, output_dir=Path(f"mockups/ep{ep_num:02d}"))
            print(f"[OK] Episode {ep_num:02d}: {len(cards)} mockup cards generated in mockups/ep{ep_num:02d}/")
    elif args.season:
        orchestrator = SeasonOrchestrator(provider=args.provider)
        orchestrator.run_season(
            episodes_count=args.episodes,
            aspect_ratio=args.aspect,
            dry_run=args.dry_run,
        )
    else:
        run_pipeline(args)

if __name__ == "__main__":
    main()
