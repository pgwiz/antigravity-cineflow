"""Director Agent - Pre-production Character Bible, Hollywood Screenplay Scriptwriter, and Shot Decomposer."""

import os
import json
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path

from config import settings
from skills.film_skills import (
    ShotType,
    CameraMovement,
    LightingStyle,
    OpticsLenses,
    ColorScience,
    TransitionType,
    FilmPromptBuilder,
    DEFAULT_NEGATIVE_PROMPT,
)
from pipeline.storyboard import (
    Storyboard,
    Scene,
    TransitionConfig,
    SceneStatus,
    CharacterProfile,
    DialogueLine,
    ScreenplayScene,
    Screenplay,
)

class DirectorAgent:
    """The Autonomous Executive Producer, Screenwriter, and Cinematographer.
    
    Phases of Execution:
    1. Pre-Production: Defines the Character Bible (appearance, wardrobe DNA, voice, prompt anchors) BEFORE writing.
    2. Screenwriting: Writes full Hollywood screenplay with sluglines, action, dialogue, and sound cues.
    3. Production Breakdown: Decomposes screenplay into exact 8-10s Veo camera shots with Hollywood film grammar.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.client = None
        self._init_genai_client()

    def _init_genai_client(self):
        """Initializes google-genai client."""
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[DirectorAgent] Warning loading google-genai: {e}")
                self.client = None

    def analyze_reference_image(self, image_path: Path) -> str:
        """Extracts character wardrobe and visual DNA from an uploaded reference photo."""
        if not image_path.exists() or not self.client:
            return f"Visual reference matching {image_path.name}"
        try:
            from PIL import Image
            img = Image.open(image_path)
            prompt = (
                "You are an expert Hollywood costume designer and cinematographer. "
                "Analyze this image and describe the exact Visual DNA of the character: "
                "costume materials, armor plates, fabric texture, colors, emblems, silhouette, and facial structure. "
                "Be extremely specific in 2 concise sentences so a video generation AI can duplicate it."
            )
            response = self.client.models.generate_content(
                model=settings.director_model,
                contents=[img, prompt],
            )
            return response.text.strip()
        except Exception as e:
            print(f"[DirectorAgent] Image analysis note: {e}")
            return f"High-fidelity visual aesthetic matching reference in {image_path.name}"

    def build_character_bible(
        self,
        concept: str,
        genre: str,
        character_reference_image: Optional[Path] = None,
    ) -> List[CharacterProfile]:
        """Stage 1: Defines all characters in detail BEFORE writing the screenplay."""
        print("[DirectorAgent] Stage 1/3: Formulating Pre-Production Character Bible...")
        
        char_img_dna = None
        if character_reference_image and character_reference_image.exists():
            char_img_dna = self.analyze_reference_image(character_reference_image)

        if self.client:
            try:
                system_prompt = (
                    "You are a master Hollywood showrunner and character designer. "
                    "Before writing any script, you must define all key characters in depth. "
                    "Return ONLY a JSON array of character objects with the following schema:\n"
                    "- character_id: lowercase identifier (e.g. 'batman', 'antagonist')\n"
                    "- name: full character name in uppercase\n"
                    "- role: Protagonist, Antagonist, Foil, or Mentor\n"
                    "- appearance: physical traits, build, facial structure, eyes\n"
                    "- wardrobe_visual_dna: exact fabrics, armor texture, color palette, emblems\n"
                    "- voice_and_cadence: vocal pitch, dialogue mannerisms, delivery speed\n"
                    "- backstory: foundational trauma and history\n"
                    "- internal_conflict: conscious Want vs. unconscious Need\n"
                    "- prompt_anchor: a compact, highly descriptive prompt string (under 30 words) "
                    "that MUST be included in every AI video prompt featuring this character to lock in visual continuity."
                )
                user_msg = f"Story Concept: {concept}\nGenre: {genre}\n"
                if char_img_dna:
                    user_msg += f"Reference Wardrobe DNA: {char_img_dna}\n"

                response = self.client.models.generate_content(
                    model=settings.director_model,
                    contents=[user_msg],
                    config={"response_mime_type": "application/json", "system_instruction": system_prompt},
                )
                raw_chars = json.loads(response.text)
                if isinstance(raw_chars, list) and len(raw_chars) > 0:
                    profiles = [CharacterProfile.model_validate(c) for c in raw_chars]
                    if character_reference_image and profiles:
                        profiles[0].reference_image_path = str(character_reference_image)
                    return profiles
            except Exception as e:
                print(f"[DirectorAgent] LLM character generation notice ({e}), loading structured fallback...")

        # Structured cinematic fallback character bible
        return self._get_fallback_character_bible(concept, genre, character_reference_image, char_img_dna)

    def write_screenplay(
        self,
        concept: str,
        genre: str,
        characters: List[CharacterProfile],
        num_story_scenes: int = 3,
    ) -> Screenplay:
        """Stage 2: Writes the complete Hollywood screenplay using standard industry conventions."""
        print("[DirectorAgent] Stage 2/3: Authoring Hollywood Screenplay Transcript...")

        char_summary = "\n".join([f"- {c.name} ({c.role}): {c.voice_and_cadence}" for c in characters])

        if self.client:
            try:
                system_prompt = (
                    "You are an award-winning Hollywood screenwriter. "
                    "Write a standard industry-format screenplay based on the provided concept and characters. "
                    f"Create exactly {num_story_scenes} distinct scenes. "
                    "Return ONLY a JSON object matching this schema:\n"
                    "{\n"
                    "  'title': 'Short Title',\n"
                    "  'logline': 'Compelling one-sentence logline',\n"
                    "  'dramatic_theme': 'Core philosophical theme',\n"
                    "  'genre': 'Genre name',\n"
                    "  'scenes': [\n"
                    "    {\n"
                    "      'scene_number': 1,\n"
                    "      'slugline': 'Standard heading, e.g. EXT. GOTHAM ROOFTOP - NIGHT',\n"
                    "      'characters_present': ['NAME'],\n"
                    "      'action': 'Present-tense vivid visual description of what happens',\n"
                    "      'sound_cues': ['SOUND (O.S.): Description of diegetic audio'],\n"
                    "      'dialogues': [\n"
                    "        {'character': 'NAME', 'parenthetical': '(whispering)', 'line': 'Dialogue'}\n"
                    "      ],\n"
                    "      'dramatic_beat': 'Inciting Incident, Tension, Climax, etc.'\n"
                    "    }\n"
                    "  ]\n"
                    "}"
                )

                prompt = (
                    f"Concept: {concept}\n"
                    f"Genre: {genre}\n"
                    f"Characters Roster:\n{char_summary}\n"
                )

                response = self.client.models.generate_content(
                    model=settings.director_model,
                    contents=[prompt],
                    config={"response_mime_type": "application/json", "system_instruction": system_prompt},
                )
                data = json.loads(response.text)
                screenplay_scenes = [
                    ScreenplayScene(
                        scene_number=s.get("scene_number", idx),
                        slugline=s.get("slugline", "EXT. UNKNOWN LOCATION - NIGHT"),
                        characters_present=s.get("characters_present", []),
                        action=s.get("action", ""),
                        dialogues=[DialogueLine(**d) for d in s.get("dialogues", [])],
                        sound_cues=s.get("sound_cues", []),
                        dramatic_beat=s.get("dramatic_beat", ""),
                    )
                    for idx, s in enumerate(data.get("scenes", []), start=1)
                ]

                return Screenplay(
                    title=data.get("title", concept.split(".")[0][:35]),
                    logline=data.get("logline", concept),
                    dramatic_theme=data.get("dramatic_theme", "Justice vs. Vengeance"),
                    genre=genre,
                    characters=characters,
                    scenes=screenplay_scenes,
                )
            except Exception as e:
                print(f"[DirectorAgent] LLM scriptwriter notice ({e}), assembling classic screenplay template...")

        # Algorithmic fallback screenplay
        return self._get_fallback_screenplay(concept, genre, characters)

    def create_storyboard(
        self,
        concept: str,
        total_duration: float = 60.0,
        clip_duration: float = 8.0,
        aspect_ratio: str = "16:9",
        character_reference_image: Optional[Path] = None,
        environment_reference_image: Optional[Path] = None,
        genre: str = "Cinematic Neo-Noir",
    ) -> Storyboard:
        """Stage 3: Full End-to-End Generation (Character Bible -> Screenplay -> Shot List)."""
        num_shots = Storyboard.calculate_scene_count(total_duration, clip_duration)
        project_id = str(uuid.uuid4())[:8]

        # 1. Define Character Bible
        characters = self.build_character_bible(concept, genre, character_reference_image)

        # 2. Write Screenplay
        num_story_scenes = max(2, min(5, num_shots // 2))
        screenplay = self.write_screenplay(concept, genre, characters, num_story_scenes=num_story_scenes)

        # 3. Decompose into Camera Shots for Veo
        print(f"[DirectorAgent] Stage 3/3: Decomposing Screenplay into {num_shots} explicit 8-10s Veo shots...")
        shots = self._decompose_to_shots(
            screenplay=screenplay,
            num_shots=num_shots,
            total_duration=total_duration,
            clip_duration=clip_duration,
            aspect_ratio=aspect_ratio,
            char_image=character_reference_image,
        )

        return Storyboard(
            project_id=project_id,
            title=screenplay.title,
            logline=screenplay.logline,
            genre=genre,
            total_target_duration=total_duration,
            aspect_ratio=aspect_ratio,
            resolution=settings.default_resolution,
            screenplay=screenplay,
            scenes=shots,
        )

    def _decompose_to_shots(
        self,
        screenplay: Screenplay,
        num_shots: int,
        total_duration: float,
        clip_duration: float,
        aspect_ratio: str,
        char_image: Optional[Path],
    ) -> List[Scene]:
        """Translates screenplay beats into Veo generation shots with Hollywood Film Skills."""
        shots: List[Scene] = []
        current_time = 0.0

        # Mapping templates
        cinematography_flow = [
            (ShotType.EXTREME_WIDE_SHOT, CameraMovement.CRANE_DESCENT, LightingStyle.VOLUMETRIC_GOD_RAYS, OpticsLenses.WIDE_24MM),
            (ShotType.WIDE_SHOT, CameraMovement.SLOW_PUSH_IN, LightingStyle.CHIAROSCURO, OpticsLenses.ANAMORPHIC_35MM),
            (ShotType.MEDIUM_CLOSE_UP, CameraMovement.STATIC, LightingStyle.REMBRANDT, OpticsLenses.CINE_PRIME_50MM),
            (ShotType.EXTREME_CLOSE_UP, CameraMovement.SLOW_PUSH_IN, LightingStyle.SILHOUETTE_RIM, OpticsLenses.PORTRAIT_85MM),
            (ShotType.DUTCH_ANGLE, CameraMovement.TRACKING_LATERAL, LightingStyle.NEON_CYBER_NOIR, OpticsLenses.ANAMORPHIC_35MM),
            (ShotType.MEDIUM_SHOT, CameraMovement.ORBIT_STEADICAM, LightingStyle.CHIAROSCURO, OpticsLenses.ANAMORPHIC_35MM),
            (ShotType.CLOSE_UP, CameraMovement.SLOW_PUSH_IN, LightingStyle.REMBRANDT, OpticsLenses.CINE_PRIME_50MM),
            (ShotType.EXTREME_WIDE_SHOT, CameraMovement.DOLLY_OUT, LightingStyle.BLUE_HOUR, OpticsLenses.WIDE_24MM),
        ]

        main_char = screenplay.characters[0] if screenplay.characters else None
        char_anchor = main_char.prompt_anchor if main_char else "Mysterious protagonist"

        for i in range(num_shots):
            dur = clip_duration
            start_m, start_s = divmod(int(current_time), 60)
            end_time = current_time + dur
            end_m, end_s = divmod(int(end_time), 60)

            shot_type, cam_move, lighting, lens = cinematography_flow[i % len(cinematography_flow)]
            color_science = ColorScience.KODAK_VISION3_35MM

            # Connect to screenplay scene
            script_scene_idx = min(len(screenplay.scenes) - 1, i * len(screenplay.scenes) // num_shots)
            script_scene = screenplay.scenes[script_scene_idx]

            # Grab relevant dialogue line if exists
            dialogue_text = None
            if script_scene.dialogues:
                d_idx = i % len(script_scene.dialogues)
                dialogue_text = script_scene.dialogues[d_idx].line

            # Formulate action and Veo prompt
            action_snippet = f"{script_scene.action[:120]} (Beat {i+1} of {num_shots})"
            veo_prompt = FilmPromptBuilder.build_prompt(
                subject_action=action_snippet,
                shot_type=shot_type,
                camera_movement=cam_move,
                lighting=lighting,
                lens=lens,
                color_science=color_science,
                visual_dna=char_anchor,
                environmental_atmosphere="Heavy rain, wet reflective surfaces, atmospheric fog",
            )

            # Transitions: last-frame continuation every 3rd shot
            chain_continuation = (i > 0 and i % 3 == 0)
            trans_type = TransitionType.DISSOLVE if (i < num_shots - 1 and i % 2 == 1) else TransitionType.HARD_CUT

            scene_shot = Scene(
                scene_number=i + 1,
                title=f"Shot {i+1:02d} - {script_scene.slugline}",
                slugline_ref=script_scene.slugline,
                timecode_start=f"{start_m:02d}:{start_s:02d}",
                timecode_end=f"{end_m:02d}:{end_s:02d}",
                duration_seconds=dur,
                shot_type=shot_type.name,
                camera_movement=cam_move.name,
                lighting=lighting.name,
                lens=lens.name,
                color_science=color_science.name,
                action_description=action_snippet,
                characters_in_shot=[main_char.name] if main_char else [],
                visual_prompt=veo_prompt,
                negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                reference_image_path=str(char_image) if (char_image and i == 0) else None,
                chain_from_previous_last_frame=chain_continuation,
                transition_to_next=TransitionConfig(
                    transition_type=trans_type,
                    duration_seconds=0.5 if trans_type == TransitionType.DISSOLVE else 0.0,
                ),
                narration_text=dialogue_text,
                sound_effects_cue=script_scene.sound_cues[0] if script_scene.sound_cues else "Heavy rain and distant sirens",
                status=SceneStatus.PENDING,
            )
            shots.append(scene_shot)
            current_time = end_time

        return shots

    def _get_fallback_character_bible(
        self,
        concept: str,
        genre: str,
        char_img: Optional[Path],
        dna_override: Optional[str],
    ) -> List[CharacterProfile]:
        """Provides a rich Character Bible for Noir/Vigilante stories."""
        batman_dna = (
            dna_override or 
            "Matte black Kevlar-weave ballistic suit, carbon-fiber sculpted chestplate with graphite bat emblem, "
            "scalloped leather cape, pointed cowl with sharp 3-inch ears and white slit lenses, tactical bronze utility belt."
        )

        batman = CharacterProfile(
            character_id="batman",
            name="BRUCE WAYNE / BATMAN",
            role="Protagonist",
            appearance="Imposing 6'2 athletic muscular build, chiselled squared jawline with five o'clock shadow, intense brooding eyes.",
            wardrobe_visual_dna=batman_dna,
            voice_and_cadence="Deep, raspy baritone whisper. Deliberate, terse, authoritative, rarely uses contractions.",
            backstory="Witnessed his parents murdered in Crime Alley as a boy. Dedicated his life and fortune to waging war on the criminal underworld.",
            internal_conflict="Driven by vengeance to eliminate crime, but bound by a strict moral code never to become the monster he hunts.",
            prompt_anchor=f"Batman in {batman_dna}",
            reference_image_path=str(char_img) if char_img else None,
        )

        antagonist = CharacterProfile(
            character_id="shadow_operative",
            name="THE WHISPER",
            role="Antagonist",
            appearance="Tall, wiry silhouette, concealed face under a high-collared trenchcoat and cracked porcelain mask.",
            wardrobe_visual_dna="Charcoal wool trenchcoat, weathered black leather gloves, cracked white ceramic half-mask with red cipher markings.",
            voice_and_cadence="Sibilant, soft-spoken, mocking cadence. Speaks in deliberate riddles.",
            backstory="A rogue intelligence asset who believes Gotham's corruption cannot be cured, only burned to ashes.",
            internal_conflict="Seeks absolute order through absolute destruction.",
            prompt_anchor="The Whisper in charcoal trenchcoat and cracked white porcelain half-mask",
        )

        return [batman, antagonist]

    def _get_fallback_screenplay(
        self,
        concept: str,
        genre: str,
        characters: List[CharacterProfile],
    ) -> Screenplay:
        """Provides a standard Hollywood formatted screenplay."""
        scenes = [
            ScreenplayScene(
                scene_number=1,
                slugline="EXT. GOTHAM SKYLINE - NIGHT",
                characters_present=["BRUCE WAYNE / BATMAN"],
                action=(
                    "Torrential rain hammers the copper spires of Gotham City. Lightning arcs through the polluted storm clouds, "
                    "briefly illuminating the grotesque face of a stone gargoyle perched eighty stories above the street.\n\n"
                    "BATMAN crouches motionless on the precipice, rain streaming off the scalloped edges of his cape like black oil. "
                    "His white lenses narrow as a police siren echoes from the maze of alleys below."
                ),
                sound_cues=[
                    "SOUND: Continuous heavy downpour, low rumbling thunder.",
                    "SOUND (O.S.): Distant police cruiser siren wailing two miles south.",
                ],
                dialogues=[
                    DialogueLine(
                        character="BRUCE WAYNE / BATMAN",
                        parenthetical="(internal monologue, low rasp)",
                        line="Two years of nights have turned me into a nocturnal animal. The city thinks I'm hiding in the shadows. But I am the shadows."
                    )
                ],
                dramatic_beat="Cold Open / Inciting Incident",
            ),
            ScreenplayScene(
                scene_number=2,
                slugline="EXT. CRIME ALLEY - CONTINUOUS",
                characters_present=["BRUCE WAYNE / BATMAN", "THE WHISPER"],
                action=(
                    "Batman drops silently from the darkness, his cape billowing like a predatory kite before snapping shut. "
                    "His boots hit the flooded pavement with barely a splash.\n\n"
                    "At the end of the narrow corridor stands THE WHISPER, holding a ticking encrypted ledger. "
                    "A neon 'HOTEL' sign casts pulsating magenta streaks across the cracked porcelain mask."
                ),
                sound_cues=[
                    "SOUND: Ticking electronic cipher beacon.",
                    "SOUND: Footstep splash on asphalt.",
                ],
                dialogues=[
                    DialogueLine(
                        character="THE WHISPER",
                        parenthetical="(taunting, smiling behind mask)",
                        line="You're late, Dark Knight. The rot has already spread into the foundation."
                    ),
                    DialogueLine(
                        character="BRUCE WAYNE / BATMAN",
                        parenthetical="(stepping into the neon light)",
                        line="Then I'll tear down the foundation."
                    ),
                ],
                dramatic_beat="Climax & Confrontation",
            ),
        ]

        return Screenplay(
            title="Shadows of Arkham",
            logline=concept,
            dramatic_theme="The price of justice in a corrupt world",
            genre=genre,
            characters=characters,
            scenes=scenes,
        )
