"""Audio Engine - Narration synthesis, sound effects cues, and background soundtrack generator."""

import os
import subprocess
from pathlib import Path
from typing import Optional, List

from config import settings
from pipeline.storyboard import Storyboard, Scene

class AudioEngine:
    """Handles narration generation (TTS), ambient soundscapes, and audio track alignment."""

    def __init__(self, elevenlabs_api_key: Optional[str] = None):
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")

    def generate_narration(self, text: str, output_path: Path, target_duration: float) -> bool:
        """Generates voiceover narration for a scene script."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Try ElevenLabs if configured
        if self.elevenlabs_api_key:
            try:
                from elevenlabs.client import ElevenLabs
                client = ElevenLabs(api_key=self.elevenlabs_api_key)
                audio_stream = client.text_to_speech.convert(
                    voice_id="JBFqnCBsd6RMkjVDRZzb", # Adam (deep, cinematic trailer voice)
                    text=text,
                    model_id="eleven_multilingual_v2",
                )
                with open(output_path, "wb") as f:
                    for chunk in audio_stream:
                        f.write(chunk)
                return True
            except Exception as e:
                print(f"[AudioEngine] ElevenLabs TTS failed ({e}), falling back to synthetic track...")

        # 2. Synthetic ambient cinematic drone using FFmpeg lavfi
        return self._generate_ambient_bed(output_path, target_duration)

    def _generate_ambient_bed(self, output_path: Path, duration: float) -> bool:
        """Generates a low, subtle cinematic synth drone and rain tone using FFmpeg."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fade_dur = min(1.0, max(0.1, duration / 3.0))
        fade_out_start = max(0.0, duration - fade_dur)
        cmd = [
            settings.ffmpeg_binary,
            "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=65:duration={duration}",
            "-filter_complex", f"volume=0.15,afade=t=in:ss=0:d={fade_dur:0.2f},afade=t=out:st={fade_out_start:0.2f}:d={fade_dur:0.2f}",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except Exception as e:
            print(f"[AudioEngine] Failed to generate ambient tone: {e}")
            return False

    def generate_soundtrack_for_storyboard(self, storyboard: Storyboard, output_dir: Path) -> Optional[Path]:
        """Creates synchronized audio stems for the full storyboard duration."""
        output_dir.mkdir(parents=True, exist_ok=True)
        master_audio_path = output_dir / "master_soundtrack.aac"
        total_dur = sum(s.duration_seconds for s in storyboard.scenes) or storyboard.total_target_duration

        # Generate continuous ambient score
        self._generate_ambient_bed(master_audio_path, total_dur)
        return master_audio_path if master_audio_path.exists() else None
