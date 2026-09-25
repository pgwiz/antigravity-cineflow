"""YouTube Data API v3 Publisher - Resumable video uploading and SEO optimization."""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import settings
from pipeline.storyboard import Storyboard

class YouTubePublisher:
    """Manages YouTube Data API v3 OAuth2 flow, chunked video uploads,
    thumbnail attachment, and SEO metadata configuration.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
    ]

    def __init__(
        self,
        client_secrets_file: Optional[Path] = None,
        token_file: Optional[Path] = None,
    ):
        self.client_secrets_file = client_secrets_file or settings.youtube_client_secrets_file
        self.token_file = token_file or settings.youtube_token_file
        self.youtube = None

    def authenticate(self) -> bool:
        """Authenticates with YouTube Data API v3 using OAuth2 tokens."""
        if not self.client_secrets_file.exists() and not self.token_file.exists():
            print(f"[YouTubePublisher] Notice: YouTube credentials not found at {self.client_secrets_file}")
            return False

        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = None
            if self.token_file.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif self.client_secrets_file.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secrets_file), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                if creds:
                    with open(self.token_file, "w") as token:
                        token.write(creds.to_json())

            if creds:
                self.youtube = build("youtube", "v3", credentials=creds)
                return True
        except Exception as e:
            print(f"[YouTubePublisher] OAuth authentication error: {e}")
            return False
        return False

    def generate_seo_metadata(self, storyboard: Storyboard) -> Dict[str, Any]:
        """Generates SEO-optimized title, description with timecodes, and tags."""
        title = f"{storyboard.title} | Cinematic AI Short Film"
        if len(title) > 95:
            title = title[:95]

        # Generate chapter timestamps for YouTube description
        chapters = []
        for s in storyboard.scenes:
            chapters.append(f"{s.timecode_start} - {s.title} ({s.shot_type.split(' ')[0]})")

        description = (
            f"{storyboard.logline}\n\n"
            f"Created with Google Antigravity Python SDK, Veo Video Generation Engine, and Film Skills Cinematography Grammar.\n\n"
            f"🎬 Scene Chapters:\n" + "\n".join(chapters) + "\n\n"
            f"#AIFilm #Veo #GoogleGenAI #Cinematography #FilmMaking #Antigravity"
        )

        tags = [
            "AI Video", "Veo", "Google Gemini", "Cinematography",
            "Film Skills", "Short Film", storyboard.genre.lower()
        ]

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "1",  # 1 = Film & Animation
        }

    def upload_video(
        self,
        video_path: Path,
        storyboard: Storyboard,
        privacy_status: str = "private",
        thumbnail_path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> Optional[str]:
        """Performs a resumable chunked upload to YouTube."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        meta = self.generate_seo_metadata(storyboard)

        if dry_run:
            print(f"[YouTubePublisher] Dry-Run mode enabled. Skipping live upload.")
            print(f"  Title: {meta['title']}")
            print(f"  Privacy: {privacy_status}")
            return "dry-run-video-id-xyz"

        if not self.authenticate():
            print(f"[YouTubePublisher] YouTube credentials unconfigured or authentication failed at {self.client_secrets_file}.")
            return None

        try:
            from googleapiclient.http import MediaFileUpload

            body = {
                "snippet": meta,
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(
                str(video_path),
                chunksize=1024 * 1024 * 5,  # 5MB chunks
                resumable=True,
                mimetype="video/mp4",
            )

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            print(f"[YouTubePublisher] Starting resumable upload for {video_path.name}...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"  Uploaded {int(status.progress() * 100)}%...")

            video_id = response.get("id")
            print(f"[YouTubePublisher] Upload complete! Video URL: https://youtu.be/{video_id}")

            # Upload thumbnail if available
            if thumbnail_path and thumbnail_path.exists() and video_id:
                try:
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
                    ).execute()
                    print(f"[YouTubePublisher] Custom thumbnail uploaded.")
                except Exception as e:
                    print(f"[YouTubePublisher] Thumbnail upload warning: {e}")

            return video_id
        except Exception as e:
            print(f"[YouTubePublisher] Upload failed: {e}")
            return None
