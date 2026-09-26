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

class SpatialGridPoint(BaseModel):
    """3D Stage Coordinate representation (-1.0 to 1.0 for X/Y, 0.0 to 3.0 for Z)."""
    x: float = Field(0.0, description="Horizontal axis: -1.0 (Stage Left) to +1.0 (Stage Right), 0.0 (Center)")
    y: float = Field(0.0, description="Depth axis: -1.0 (Downstage/Foreground) to +1.0 (Upstage/Background), 0.0 (Center)")
    z: float = Field(0.0, description="Vertical axis: 0.0 (Floor level) to 3.0 (Elevated/Perched)")
    named_zone: str = Field("CENTER_STAGE", description="Human-readable stage location, e.g. STAGE_LEFT_ALTAR_TABLE")

class StageCharacterBlocking(BaseModel):
    """Explicit physical placement and eye-line vector for a character in a shot."""
    character_id: str
    name: str
    position: SpatialGridPoint
    facing_angle_deg: float = Field(0.0, description="0=Facing Camera/Downstage, 90=Stage Right, 180=Upstage, 270=Stage Left")
    facing_description: str = Field(..., description="e.g. Facing 45 degrees Downstage-Right towards center altar")
    eyeline_vector: str = Field(..., description="e.g. Focused on the submerged wedding ring in the goblet")
    physical_pose: str = Field(..., description="e.g. Crouched motionless on mahogany table surface, paws tucked, tail still")
    continuity_anchor: str = Field(..., description="e.g. Anchored on Table Surface Stage-Left; MUST NOT relocate without scripted cut")

class TrackedSceneObject(BaseModel):
    """Persistent object state and physical anchor across cuts to prevent AI hallucination."""
    object_id: str
    name: str
    position: SpatialGridPoint
    container_or_surface: str = Field(..., description="e.g. Submerged inside crystal goblet on Center Altar table")
    visual_state: str = Field(..., description="e.g. Sparkling golden ring in saline water with micro-bubbles")
    holder_character: Optional[str] = None
    continuity_lock: str = Field(..., description="e.g. Permanent fixture on Center Altar; must remain visible when camera faces altar")

class CameraBlocking(BaseModel):
    """Explicit camera position, 180-degree action line, and focal plane."""
    axis_of_action_180: str = Field(..., description="180-degree action line, e.g. Locked between Nave Entrance and Altar")
    camera_position: SpatialGridPoint
    camera_elevation_angle: str = Field("Eye-level", description="e.g. Low-Angle 20 degrees upward tilt from 30 inches off water surface")
    camera_fov: str = Field("35mm anamorphic wide-angle (65-degree horizontal FOV)")
    focal_target: str = Field(..., description="Focal plane locked on subject; background elements in soft bokeh")

class SpatialTransition(BaseModel):
    """Finely defined optical and spatial continuity rules across shot cuts."""
    transition_type: TransitionType = TransitionType.HARD_CUT
    duration_seconds: float = 0.5
    spatial_carryover_notes: str = Field(..., description="e.g. Preserves Cat on Screen-Left, Altar at Screen-Center across the cut")
    match_vector: Optional[str] = None

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
    
    # Spatial Stage Blocking & Continuity
    stage_environment: str = Field(default="Flooded Gothic Cathedral sanctuary with central stone altar and stained glass")
    character_blockings: List[StageCharacterBlocking] = Field(default_factory=list)
    tracked_objects: List[TrackedSceneObject] = Field(default_factory=list)
    camera_blocking: Optional[CameraBlocking] = None
    spatial_transition: Optional[SpatialTransition] = None

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

    def get_spatial_summary(self) -> str:
        """Returns compact spatial blocking summary for prompt injection."""
        if not self.character_blockings:
            return ""
        items = []
        for cb in self.character_blockings:
            items.append(f"{cb.name} positioned at {cb.position.named_zone} (facing {cb.facing_description}, stance: {cb.physical_pose})")
        return "; ".join(items)

    def get_object_summary(self) -> str:
        """Returns compact object locations summary for prompt injection."""
        if not self.tracked_objects:
            return ""
        items = []
        for ob in self.tracked_objects:
            items.append(f"{ob.name} anchored at {ob.position.named_zone} [{ob.container_or_surface}, visual state: {ob.visual_state}]")
        return "; ".join(items)

    def get_camera_axis_summary(self) -> str:
        """Returns camera 180-degree axis guidelines for prompt injection."""
        if not self.camera_blocking:
            return ""
        cb = self.camera_blocking
        return f"{cb.axis_of_action_180}; Camera at {cb.camera_position.named_zone}, elevation: {cb.camera_elevation_angle}, targeting {cb.focal_target}"

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
            lines.append(f"- **Stage Environment:** {s.stage_environment}")
            if s.character_blockings:
                lines.append(f"- **Spatial Blocking & Poses:** {s.get_spatial_summary()}")
            if s.tracked_objects:
                lines.append(f"- **Tracked Objects & Anchors:** {s.get_object_summary()}")
            if s.camera_blocking:
                lines.append(f"- **Camera Axis & 180° Rule:** {s.get_camera_axis_summary()}")
            lines.append(f"- **Action:** {s.action_description}")
            if s.spatial_transition:
                lines.append(f"- **Spatial Transition Carryover:** {s.spatial_transition.spatial_carryover_notes}")
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

    def generate_production_dossier_text(self) -> str:
        """Compiles a complete, publication-grade text production blueprint and instruction manual."""
        sep = "=" * 80
        sub_sep = "-" * 80
        lines = [
            sep,
            f"🎬 PRODUCTION BLUEPRINT & INSTRUCTION DOSSIER: {self.title.upper()}",
            f"Project ID: {self.project_id} | Created: {self.created_at}",
            sep,
            "\n[SECTION 1: EXECUTIVE PRODUCTION BRIEF & SCENE MATH]",
            sub_sep,
            f"Title:               {self.title}",
            f"Logline:             {self.logline}",
            f"Genre / Style:       {self.genre}",
            f"Target Duration:     {self.total_target_duration:.1f} seconds",
            f"Aspect Ratio:        {self.aspect_ratio}",
            f"Total Camera Shots:  {len(self.scenes)} shots",
            f"Average Shot Length: {self.total_target_duration / max(1, len(self.scenes)):.1f} seconds/shot",
        ]

        # Section 2: Character Bible
        lines.extend([
            f"\n[SECTION 2: PRE-PRODUCTION CHARACTER BIBLE]",
            sub_sep,
        ])
        if self.screenplay and self.screenplay.characters:
            for idx, c in enumerate(self.screenplay.characters, start=1):
                lines.extend([
                    f"\nCHARACTER #{idx:02d}: {c.name} ({c.role.upper()})",
                    f"  * Physical Hallmarks:   {c.appearance}",
                    f"  * Wardrobe / Visual DNA:{c.wardrobe_visual_dna}",
                    f"  * Vocal Cadence & Tone: {c.voice_and_cadence}",
                    f"  * Backstory & Trauma:   {c.backstory}",
                    f"  * Want vs. Need:        {c.internal_conflict}",
                    f"  * IMMUTABLE VEO ANCHOR: \"{c.prompt_anchor}\"",
                ])
        else:
            lines.append("  (No discrete character profiles loaded; standard ensemble cast)")

        # Section 3: 3D Spatial Grid & Tracked Scene Objects
        lines.extend([
            f"\n[SECTION 3: 3D SPATIAL STAGE & TRACKED OBJECTS MATRIX]",
            sub_sep,
            "Spatial Coordinate Reference System:",
            "  - X-Axis: -1.0 (Stage Left) to +1.0 (Stage Right), 0.0 (Center Stage)",
            "  - Y-Axis: -1.0 (Downstage / Foreground) to +1.0 (Upstage / Background)",
            "  - Z-Axis:  0.0 (Floor Level) to +3.0 (Elevated Perch / Ledge in meters)",
            "  - 180° Action Axis: Camera must remain on downstage side of vector to avoid disorientation.",
            "\nTracked Scene Objects Across Cuts:",
        ])
        all_objects = {}
        for s in self.scenes:
            for ob in s.tracked_objects:
                if ob.object_id not in all_objects:
                    all_objects[ob.object_id] = ob

        if all_objects:
            for ob in all_objects.values():
                lines.extend([
                    f"  * OBJECT: {ob.name} (ID: {ob.object_id})",
                    f"    - Stage Zone:        {ob.position.named_zone} (X: {ob.position.x:+.1f}, Y: {ob.position.y:+.1f}, Z: {ob.position.z:.1f}m)",
                    f"    - Container/Surface: {ob.container_or_surface}",
                    f"    - Visual State:      {ob.visual_state}",
                    f"    - Continuity Lock:   {ob.continuity_lock}",
                ])
        else:
            lines.append("  (Standard set dressing; no persistent tracked interactive props)")

        # Section 4: Hollywood Screenplay Transcript
        lines.extend([
            f"\n[SECTION 4: FULL HOLLYWOOD SCREENPLAY TRANSCRIPT]",
            sub_sep,
        ])
        if self.screenplay:
            lines.append(self.screenplay.format_screenplay_transcript().strip())
        else:
            lines.append("  (Screenplay transcript not attached)")

        # Section 5: Shot-by-Shot Production Breakdown & Exact Prompts
        lines.extend([
            f"\n[SECTION 5: SHOT-BY-SHOT CAMERA INSTRUCTIONS & VEO PROMPTS]",
            sub_sep,
        ])
        for s in self.scenes:
            lines.extend([
                f"\n--- SHOT {s.scene_number:02d} [{s.timecode_start} - {s.timecode_end} | {s.duration_seconds:.1f}s] ---",
                f"Title:               {s.title}",
                f"Slugline Reference:  {s.slugline_ref}",
                f"Framing & Optics:    {s.shot_type} on {s.lens}",
                f"Camera Motion:       {s.camera_movement}",
                f"Lighting & Film:     {s.lighting} | {s.color_science}",
                f"Stage Environment:   {s.stage_environment}",
            ])
            if s.character_blockings:
                lines.append(f"Stage Characters:    {s.get_spatial_summary()}")
            if s.tracked_objects:
                lines.append(f"Tracked Objects:     {s.get_object_summary()}")
            if s.camera_blocking:
                lines.append(f"Camera Axis:         {s.get_camera_axis_summary()}")
            if s.spatial_transition:
                lines.append(f"Transition Carryover:{s.spatial_transition.spatial_carryover_notes}")
            lines.extend([
                f"Action Description:  {s.action_description}",
                f"Audio / SFX Cue:     {s.sound_effects_cue or 'None'}",
                f"Dialogue Line:       \"{s.narration_text or 'None'}\"",
                f"EXACT VEO PROMPT:\n{s.visual_prompt}",
                f"NEGATIVE PROMPT:     {s.negative_prompt}",
            ])

        # Section 6: Execution Instructions
        lines.extend([
            f"\n[SECTION 6: HUMAN & AI EXECUTION INSTRUCTIONS]",
            sub_sep,
            "Option A (Manual Web Interface - Google Flow Ultra / Veo):",
            f"  1. Log into your Google Flow account (e.g. flow.google.com/u/5/).",
            f"  2. For each shot above, copy the 'EXACT VEO PROMPT' into the prompt box.",
            f"  3. Set aspect ratio to {self.aspect_ratio} and select Veo 3.1 Fast / Quality.",
            f"  4. Ensure character visual DNA and object locations match the specifications.",
            "\nOption B (Automated CLI Media Generation):",
            f"  Run the following command to render actual video clips and master MP4:",
            f"    python main.py --job-id {self.project_id} --media --provider chrome",
            f"  Or with free offline motion engine:",
            f"    python main.py --job-id {self.project_id} --media --provider free",
            sep,
        ])

        return "\n".join(lines)

