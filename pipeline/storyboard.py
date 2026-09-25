"""Explicit Screenplay, Character Bible, and Storyboard Data Models.

Implements standard Hollywood screenplay formatting, pre-production character dossiers,
and explicit shot-by-shot production breakdowns.
"""

import json
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from skills.film_skills import (
    ShotType,
    CameraMovement,
    LightingStyle,
    OpticsLenses,
    ColorScience,
    TransitionType,
    DEFAULT_NEGATIVE_PROMPT,
)

class SceneStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class CharacterProfile(BaseModel):
    """Pre-production Character Bible Dossier defined BEFORE writing any scene."""
    character_id: str
    name: str = Field(..., description="Character name in caps, e.g., BATMAN / BRUCE WAYNE")
    role: str = Field(..., description="Protagonist, Antagonist, Mentor, Foil, Henchman")
    appearance: str = Field(..., description="Physical build, height, facial features, jawline, hair, eye color")
    wardrobe_visual_dna: str = Field(..., description="Exact costume materials, armor textures, fabrics, color palette, emblems")
    voice_and_cadence: str = Field(..., description="Vocal pitch, accent, speech cadence, dialogue mannerisms")
    backstory: str = Field(..., description="Foundational trauma, origin, and history")
    internal_conflict: str = Field(..., description="Core conflict: conscious Want vs. unconscious Need")
    prompt_anchor: str = Field(..., description="Immutable prompt snippet injected into all Veo shots featuring this character")
    reference_image_path: Optional[str] = None

class DialogueLine(BaseModel):
    """A single line of spoken dialogue in a scene."""
    character: str
    parenthetical: Optional[str] = None  # e.g., "(whispering through cowl communicator)"
    line: str

class ScreenplayScene(BaseModel):
    """A standard Hollywood screenplay scene with slugline, action, and dialogue."""
    scene_number: int
    slugline: str = Field(..., description="Standard scene heading, e.g., EXT. GOTHAM ROOFTOP - NIGHT")
    characters_present: List[str] = Field(default_factory=list)
    action: str = Field(..., description="Present-tense visual action block")
    dialogues: List[DialogueLine] = Field(default_factory=list)
    sound_cues: List[str] = Field(default_factory=list)  # e.g., "SOUND (O.S.): THUNDERCLAP shakes the gargoyles"
    dramatic_beat: str = Field(default="", description="Story purpose: Hook, Conflict, Reveal, Climax")

class Screenplay(BaseModel):
    """Complete Hollywood Screenplay containing Character Bible and full transcript."""
    title: str
    logline: str
    dramatic_theme: str = "Justice vs. Vengeance"
    genre: str = "Cinematic Neo-Noir"
    characters: List[CharacterProfile] = Field(default_factory=list)
    scenes: List[ScreenplayScene] = Field(default_factory=list)

    def format_character_bible_markdown(self) -> str:
        """Renders the comprehensive pre-production Character Bible."""
        lines = [
            f"# Pre-Production Character Bible: {self.title}",
            "All characters are defined prior to screenplay generation to ensure psychological depth and visual continuity.\n",
        ]
        for c in self.characters:
            lines.append(f"## {c.name} ({c.role})")
            lines.append(f"- **Physical Appearance:** {c.appearance}")
            lines.append(f"- **Wardrobe & Visual DNA:** {c.wardrobe_visual_dna}")
            lines.append(f"- **Voice & Speech Cadence:** {c.voice_and_cadence}")
            lines.append(f"- **Backstory & Motivation:** {c.backstory}")
            lines.append(f"- **Internal Conflict:** {c.internal_conflict}")
            lines.append(f"- **AI Visual Prompt Anchor:** `{c.prompt_anchor}`")
            if c.reference_image_path:
                lines.append(f"- **Reference Image:** `{c.reference_image_path}`")
            lines.append("")
        return "\n".join(lines)

    def format_screenplay_transcript(self) -> str:
        """Formats the script into standard Hollywood screenplay format."""
        lines = [
            f"{self.title.upper()}",
            f"Written by Director Agent",
            f"Genre: {self.genre} | Theme: {self.dramatic_theme}",
            f"Logline: {self.logline}",
            "\n" + "=" * 60 + "\n",
            "FADE IN:\n",
        ]

        for s in self.scenes:
            lines.append(f"SCENE {s.scene_number:02d}: {s.slugline}\n")
            lines.append(f"{s.action}\n")

            for cue in s.sound_cues:
                lines.append(f"    [{cue}]\n")

            for d in s.dialogues:
                lines.append(f"                    {d.character.upper()}")
                if d.parenthetical:
                    lines.append(f"              {d.parenthetical}")
                lines.append(f"        \"{d.line}\"\n")

        lines.append("FADE TO BLACK.\n")
        lines.append("\nTHE END\n")
        return "\n".join(lines)

class TransitionConfig(BaseModel):
    transition_type: TransitionType = TransitionType.HARD_CUT
    duration_seconds: float = 0.5

class Scene(BaseModel):
    """Production Shot: maps a screenplay beat to an 8-10s Veo camera generation clip."""
    scene_number: int
    title: str
    slugline_ref: str = "EXT. UNKNOWN - NIGHT"
    timecode_start: str = "00:00"
    timecode_end: str = "00:08"
    duration_seconds: float = 8.0
    
    # Cinematography specifications
    shot_type: str = ShotType.MEDIUM_SHOT.name
    camera_movement: str = CameraMovement.SLOW_PUSH_IN.name
    lighting: str = LightingStyle.CHIAROSCURO.name
    lens: str = OpticsLenses.ANAMORPHIC_35MM.name
    color_science: str = ColorScience.KODAK_VISION3_35MM.name
    
    # Prompting
    action_description: str
    characters_in_shot: List[str] = Field(default_factory=list)
    visual_prompt: str = ""
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT
    
    # Visual Continuity & Reference
    reference_image_path: Optional[str] = None
    chain_from_previous_last_frame: bool = False
    
    # Transitions & Audio
    transition_to_next: TransitionConfig = Field(default_factory=TransitionConfig)
    narration_text: Optional[str] = None
    sound_effects_cue: Optional[str] = None
    
    # Output artifacts
    output_clip_path: Optional[str] = None
    last_frame_path: Optional[str] = None
    status: SceneStatus = SceneStatus.PENDING
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Storyboard(BaseModel):
    """Master production storyboard linking Screenplay, Character Bible, and Shot List."""
    project_id: str
    title: str
    logline: str = ""
    genre: str = "Cinematic Neo-Noir"
    total_target_duration: float = 60.0
    aspect_ratio: str = "16:9"  # "16:9" or "9:16"
    resolution: str = "720p"
    screenplay: Optional[Screenplay] = None
    scenes: List[Scene] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    final_video_path: Optional[str] = None

    @classmethod
    def calculate_scene_count(cls, total_duration: float, avg_clip_duration: float = 8.0) -> int:
        """Calculates total camera shots needed based on target duration."""
        return max(1, round(total_duration / avg_clip_duration))

    def save(self, filepath: Path) -> Path:
        """Serializes complete production package to JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "Storyboard":
        """Loads production package from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def format_breakdown_markdown(self) -> str:
        """Returns the explicit shot-by-shot production breakdown."""
        lines = [
            f"# Explicit Production Shot List: {self.title}",
            f"**Logline:** {self.logline}",
            f"**Total Duration:** {self.total_target_duration:.1f}s | **Aspect Ratio:** {self.aspect_ratio} | **Total Camera Shots:** {len(self.scenes)}",
            "\n## Shot-by-Shot Timeline\n",
        ]

        for s in self.scenes:
            lines.append(f"### Shot {s.scene_number:02d} ({s.timecode_start} - {s.timecode_end} | {s.duration_seconds:.1f}s): {s.title}")
            lines.append(f"- **Slugline:** `{s.slugline_ref}`")
            lines.append(f"- **Characters Present:** {', '.join(s.characters_in_shot) if s.characters_in_shot else 'None'}")
            lines.append(f"- **Framing & Optics:** `{s.shot_type}` with `{s.lens}`")
            lines.append(f"- **Camera Movement:** `{s.camera_movement}`")
            lines.append(f"- **Lighting & Palette:** `{s.lighting}` | `{s.color_science}`")
            lines.append(f"- **Action:** {s.action_description}")
            if s.chain_from_previous_last_frame:
                lines.append(f"- **Continuity:** 🔗 *Chained directly from Shot {s.scene_number-1:02d} last frame*")
            if s.reference_image_path:
                lines.append(f"- **Reference Image:** `{s.reference_image_path}`")
            lines.append(f"- **Transition to Next:** `{s.transition_to_next.transition_type.value}` ({s.transition_to_next.duration_seconds}s)")
            if s.narration_text:
                lines.append(f"- **Dialogue/Narration:** \"{s.narration_text}\"")
            if s.sound_effects_cue:
                lines.append(f"- **Audio/SFX:** *{s.sound_effects_cue}*")
            lines.append(f"- **Veo Prompt:** ```{s.visual_prompt}```")
            lines.append("")

        return "\n".join(lines)
