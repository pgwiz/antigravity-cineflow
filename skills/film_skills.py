"""Cinematography and Film Grammar Taxonomy for AI Video Generation."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

class ShotType(str, Enum):
    EXTREME_WIDE_SHOT = "Extreme Wide Shot (EWS) establishing immense scale, geographic context, and environmental grandeur"
    WIDE_SHOT = "Wide Shot (WS) framing subjects full body within the surrounding environment"
    MEDIUM_WIDE_SHOT = "Medium Wide Shot (Cowboy Shot) framing character from mid-thigh up"
    MEDIUM_SHOT = "Medium Shot (MS) capturing character from waist up with balanced focus on action and expression"
    MEDIUM_CLOSE_UP = "Medium Close-Up (MCU) focusing from mid-chest to head, highlighting dialogue and emotion"
    CLOSE_UP = "Close-Up (CU) tightly framing face and expression, capturing intimate emotion and tension"
    EXTREME_CLOSE_UP = "Extreme Close-Up (ECU) focusing intensely on a single detail such as glowing eyes, lips, or a hand gripping a weapon"
    OVER_THE_SHOULDER = "Over-The-Shoulder (OTS) shot emphasizing conversational confrontation, depth, and spatial connection"
    POINT_OF_VIEW = "First-Person Point-Of-View (POV) immersive camera seeing directly through the protagonist's perspective"
    DUTCH_ANGLE = "Dutch Angle (Canted angle) tilted off-axis to convey disorientation, tension, psychological instability, or imminent chaos"
    BIRDS_EYE_VIEW = "God's Eye / Bird's Eye View overhead shot looking directly down from ninety degrees"

class CameraMovement(str, Enum):
    STATIC = "Locked-off static cinema tripod camera, absolute stability, deliberate composure"
    SLOW_PUSH_IN = "Slow, creeping cinematic push-in (dolly-in), intensifying dramatic tension"
    DOLLY_OUT = "Smooth dolly-out revealing context and isolating the subject in the frame"
    PAN_LEFT = "Slow cinematic horizontal pan from right to left"
    PAN_RIGHT = "Slow cinematic horizontal pan from left to right"
    TILT_UP = "Cinematic vertical tilt up, revealing height, stature, and vertical architectural scale"
    TILT_DOWN = "Cinematic vertical tilt down from sky to ground level"
    TRACKING_LATERAL = "Smooth lateral tracking shot moving parallel to the moving subject, capturing dynamic speed"
    CRANE_DESCENT = "Majestic crane / jib descent floating smoothly down from overhead to eye level"
    ORBIT_STEADICAM = "Fluid 360-degree steadicam circular orbit around the subject, dynamic and cinematic"
    DYNAMIC_FPV = "Dynamic high-speed FPV tracking motion with fluid cinematic stabilization"
    WHIP_PAN = "Rapid motion-blurred whip pan transition"

class LightingStyle(str, Enum):
    CHIAROSCURO = "Chiaroscuro high-contrast lighting with deep, rich shadows and sculpted highlights"
    REMBRANDT = "Rembrandt portrait lighting with iconic triangular highlight on the shadow cheek"
    GOLDEN_HOUR = "Warm golden hour natural backlighting with soft sun flares, warm rim glow, and long shadows"
    BLUE_HOUR = "Cold twilight blue hour atmospheric lighting with subtle melancholic contrast"
    NEON_CYBER_NOIR = "High-contrast cyber noir with vivid cyan and magenta neon rim lights reflecting off wet asphalt"
    VOLUMETRIC_GOD_RAYS = "Volumetric god rays piercing through dense atmospheric haze, dust motes, and foggy air"
    PRACTICAL_LIGHTING = "Authentic in-scene practical streetlights, flickering sodium vapor bulbs, and car headlights"
    SILHOUETTE_RIM = "Dark moody silhouette with an intense backlight and razor-sharp glowing rim light"

class OpticsLenses(str, Enum):
    ANAMORPHIC_35MM = "Cinematic 35mm anamorphic prime lens, 2.39:1 widescreen, subtle horizontal blue streak flares, oval bokeh"
    CINE_PRIME_50MM = "Cooke 50mm cinema prime lens, natural human field of view, f/1.4 aperture, creamy bokeh falloff"
    PORTRAIT_85MM = "Arri Zeiss 85mm portrait telephoto lens, ultra-shallow depth of field, heavily compressed background"
    WIDE_24MM = "24mm wide-angle cine lens with minimal distortion, deep foreground perspective"

class ColorScience(str, Enum):
    KODAK_VISION3_35MM = "Shot on Kodak Vision3 500T 35mm celluloid film, authentic subtle film grain, organic halation on highlights"
    TEAL_AND_ORANGE = "Modern Hollywood blockbuster color grade with teal-tinted shadows and warm golden skin tones"
    NOIR_MONOCHROME = "High-contrast black-and-white film noir, silver halide tone curve, deep crushed blacks and crisp white highlights"
    BLEACH_BYPASS = "Bleach bypass chemical process, desaturated palette with harsh contrast and gritty metallic edge"
    VIBRANT_SATURATED = "Rich, painterly, hyper-saturated cinematic color with deep contrast and vibrant primary hues"

class TransitionType(str, Enum):
    HARD_CUT = "hard_cut"                  # Instant instantaneous cut between shots
    MATCH_CUT = "match_cut"                # Matches movement vector or graphic shape across cut
    DISSOLVE = "dissolve"                  # 0.5s - 1.0s smooth optical cross-dissolve
    FADE_BLACK = "fade_black"              # Dip to black and emerge into next scene
    WIPE_LEFT = "wipe_left"                # Directional motion wipe
    CONTINUATION_CHAIN = "continuation"    # Frame-chained continuation (using last frame as seed)

DEFAULT_NEGATIVE_PROMPT = (
    "morphing, rubbery limbs, mutated anatomy, deformed hands, extra fingers, "
    "jittery motion, sudden unnatural cuts, blurry, low resolution, grainy pixelation, "
    "watermarks, stock footage overlay, signature, oversaturated cartoon 3d render, "
    "stuttering framerate, flickers, plastic skin texture"
)

class FilmPromptBuilder:
    """Combines narrative action with Hollywood cinematography parameters into Veo-ready prompts."""

    @staticmethod
    def build_prompt(
        subject_action: str,
        shot_type: ShotType = ShotType.MEDIUM_SHOT,
        camera_movement: CameraMovement = CameraMovement.SLOW_PUSH_IN,
        lighting: LightingStyle = LightingStyle.CHIAROSCURO,
        lens: OpticsLenses = OpticsLenses.ANAMORPHIC_35MM,
        color_science: ColorScience = ColorScience.KODAK_VISION3_35MM,
        visual_dna: Optional[str] = None,
        environmental_atmosphere: Optional[str] = None,
    ) -> str:
        """Assembles a multi-layered cinematic prompt for Veo video generation."""
        components: List[str] = []

        # 1. Shot Composition & Lens
        components.append(f"{shot_type.value}, {lens.value}.")

        # 2. Subject Action & Character DNA
        if visual_dna:
            components.append(f"Subject Visual DNA: {visual_dna}.")
        components.append(f"Scene Action: {subject_action}.")

        # 3. Camera Movement
        components.append(f"Camera: {camera_movement.value}.")

        # 4. Lighting & Color Science
        components.append(f"Lighting & Palette: {lighting.value}, {color_science.value}.")

        # 5. Environment & Atmosphere (rain, fog, wind, sparks)
        if environmental_atmosphere:
            components.append(f"Atmospheric Elements: {environmental_atmosphere}.")

        # 6. Cinematic Polish Directive
        components.append("Hyper-detailed cinematic photorealism, professional motion picture quality, 24fps motion cadence.")

        return " ".join(components)
