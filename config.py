"""Configuration settings and environment loading for Video Workflow Studio."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env if present in root or parent
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseModel):
    # API Credentials
    gemini_api_key: str = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    google_cloud_project: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLOUD_PROJECT", "")
    )
    youtube_client_secrets_file: Path = Field(
        default_factory=lambda: Path(os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", BASE_DIR / "client_secret.json"))
    )
    youtube_token_file: Path = Field(
        default_factory=lambda: Path(os.getenv("YOUTUBE_TOKEN_FILE", BASE_DIR / "youtube_token.json"))
    )

    # Models & Providers: "free" (Zero-cost AI Keyframes + 2.5D Hollywood Motion), "useapi" (Google Flow), "genai" (Direct Veo)
    video_provider: str = Field(
        default_factory=lambda: os.getenv("VIDEO_PROVIDER", "free" if not os.getenv("USEAPI_TOKEN") else "useapi")
    )
    video_model: str = Field(
        default_factory=lambda: os.getenv("VIDEO_MODEL", "veo-3.1-generate-preview")
    )
    director_model: str = Field(
        default_factory=lambda: os.getenv("DIRECTOR_MODEL", "gemini-2.5-flash")
    )

    # useapi.net Google Flow API v1 Settings
    useapi_token: str = Field(
        default_factory=lambda: os.getenv("USEAPI_TOKEN", "")
    )
    useapi_model: str = Field(
        default_factory=lambda: os.getenv("USEAPI_MODEL", "veo-3.1-fast")  # veo-3.1-fast, veo-3.1-quality, veo-3.1-lite, omni-flash
    )
    useapi_base_url: str = Field(
        default_factory=lambda: os.getenv("USEAPI_BASE_URL", "https://api.useapi.net/v1/google-flow")
    )
    useapi_account_email: Optional[str] = Field(
        default_factory=lambda: os.getenv("USEAPI_ACCOUNT_EMAIL", None)
    )

    # Paths
    base_dir: Path = BASE_DIR
    assets_dir: Path = BASE_DIR / "assets"
    output_dir: Path = BASE_DIR / "output"
    jobs_dir: Path = BASE_DIR / "jobs"
    temp_dir: Path = BASE_DIR / "temp"

    # Video Defaults
    default_clip_duration: float = 8.0
    default_aspect_ratio: str = "16:9"  # "16:9" or "9:16"
    default_resolution: str = "720p"    # "720p" or "1080p"
    default_fps: int = 24
    ffmpeg_binary: str = "ffmpeg"

    # Server Defaults
    server_host: str = "0.0.0.0"
    server_port: int = 8080

    def init_directories(self):
        """Ensure all required runtime directories exist."""
        for p in [self.assets_dir, self.output_dir, self.jobs_dir, self.temp_dir]:
            p.mkdir(parents=True, exist_ok=True)
            
        # Assets subdirectories for character and environment reference images
        (self.assets_dir / "characters").mkdir(exist_ok=True)
        (self.assets_dir / "environments").mkdir(exist_ok=True)
        (self.assets_dir / "audio").mkdir(exist_ok=True)

settings = Settings()
settings.init_directories()
