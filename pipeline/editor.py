"""Video Editor - FFmpeg stitcher supporting automatic concatenation, xfade transitions, and custom edit specs."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from config import settings
from skills.film_skills import TransitionType
from pipeline.storyboard import Storyboard, Scene

class VideoEditor:
    """Combines individual scene clips into a unified cinematic master.
    
    Supports:
    1. Fully Automatic Stitching (concat demuxer or xfade transitions)
    2. User-Specified Custom Transitions (per-cut control from storyboard.json)
    3. Audio-Video multiplexing (soundtrack & voiceover sync)
    """

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg = ffmpeg_path or settings.ffmpeg_binary

    def stitch_storyboard(
        self,
        storyboard: Storyboard,
        output_file: Path,
        soundtrack_path: Optional[Path] = None,
        use_transitions: bool = True,
    ) -> Path:
        """Stitches all completed scenes from a storyboard into the final video file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        valid_scenes = [s for s in storyboard.scenes if s.output_clip_path and Path(s.output_clip_path).exists()]

        if not valid_scenes:
            raise ValueError("[VideoEditor] No rendered scene clips found to stitch!")

        print(f"[VideoEditor] Assembling {len(valid_scenes)} scenes into final master: {output_file.name}")

        # Check if transitions are requested and there are >= 2 scenes
        has_special_transitions = any(
            s.transition_to_next.transition_type != TransitionType.HARD_CUT for s in valid_scenes[:-1]
        )

        if use_transitions and has_special_transitions and len(valid_scenes) > 1:
            try:
                temp_video = self._stitch_with_xfade(valid_scenes, output_file.with_name("temp_stitched.mp4"))
            except Exception as e:
                print(f"[VideoEditor] xfade transition filter failed ({e}), falling back to direct concat...")
                temp_video = self._stitch_direct_concat(valid_scenes, output_file.with_name("temp_stitched.mp4"))
        else:
            temp_video = self._stitch_direct_concat(valid_scenes, output_file.with_name("temp_stitched.mp4"))

        # Multiplex audio soundtrack if available
        if soundtrack_path and soundtrack_path.exists():
            print(f"[VideoEditor] Multiplexing audio soundtrack from {soundtrack_path.name}...")
            self._mux_audio(temp_video, soundtrack_path, output_file)
            if temp_video.exists():
                temp_video.unlink()
        else:
            if temp_video != output_file:
                if output_file.exists():
                    output_file.unlink()
                temp_video.rename(output_file)

        storyboard.final_video_path = str(output_file)
        print(f"[VideoEditor] Final master compiled successfully: {output_file}")
        return output_file

    def _stitch_direct_concat(self, scenes: List[Scene], output_path: Path) -> Path:
        """Fast, lossless concatenation using FFmpeg concat demuxer."""
        concat_txt = output_path.parent / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for s in scenes:
                # Format path with forward slashes for ffmpeg concat
                p = Path(s.output_clip_path).resolve().as_posix()
                f.write(f"file '{p}'\n")

        cmd = [
            self.ffmpeg,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if concat_txt.exists():
                concat_txt.unlink()
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"[VideoEditor] Concat error: {e.stderr.decode('utf-8', errors='ignore')}")
            raise

    def _stitch_with_xfade(self, scenes: List[Scene], output_path: Path) -> Path:
        """Builds an FFmpeg complex filtergraph to render transitions (dissolve, fadeblack, wipe) between clips."""
        inputs = []
        filter_parts = []
        
        # Calculate offset timings
        current_offset = 0.0
        last_out = "[0:v]"

        for i, s in enumerate(scenes):
            inputs.extend(["-i", str(Path(s.output_clip_path).resolve())])
            if i == 0:
                current_offset = s.duration_seconds
                continue

            prev_scene = scenes[i - 1]
            trans = prev_scene.transition_to_next
            trans_dur = trans.duration_seconds if trans.transition_type != TransitionType.HARD_CUT else 0.1
            
            # Map transition type to FFmpeg xfade filter
            xfade_name = "fade"
            if trans.transition_type == TransitionType.FADE_BLACK:
                xfade_name = "fadeblack"
            elif trans.transition_type == TransitionType.WIPE_LEFT:
                xfade_name = "wipeleft"

            offset_point = max(0.0, current_offset - trans_dur)
            next_out = f"[v{i}]" if i < len(scenes) - 1 else "[outv]"
            
            filter_parts.append(
                f"{last_out}[{i}:v]xfade=transition={xfade_name}:duration={trans_dur}:offset={offset_point:0.2f}{next_out}"
            )
            last_out = next_out
            current_offset = offset_point + s.duration_seconds

        filter_graph = ";".join(filter_parts)

        cmd = [
            self.ffmpeg,
            "-y",
            *inputs,
            "-filter_complex", filter_graph,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return output_path

    def _mux_audio(self, video_path: Path, audio_path: Path, output_path: Path):
        """Merges video stream with master soundtrack and cuts to video duration."""
        cmd = [
            self.ffmpeg,
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
