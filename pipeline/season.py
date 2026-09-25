"""Season Production Engine for Antigravity CineFlow.

Orchestrates multi-episode season arcs, Hollywood screenplays, Character Bibles,
scene math decomposition (60s / 8s = 7-8 shots per episode), episode assembly,
and season supercut compilation.

Featured Season:
"Batman: The Aquatic Mammalian Matrimony" (8 Episodes x 60 seconds)
Logline: In rain-drenched Gotham, Batman investigates the utterly absurd, ironical
mystery of a Japanese koi fish married to a savannah giraffe, framed by a mysterious tuxedo cat.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings
from pipeline.storyboard import (
    Storyboard,
    Scene,
    SceneStatus,
    Screenplay,
    CharacterProfile,
    SpatialGridPoint,
    StageCharacterBlocking,
    TrackedSceneObject,
    CameraBlocking,
    SpatialTransition,
    TransitionConfig,
)
from skills.film_skills import (
    FilmPromptBuilder,
    ShotType,
    CameraMovement,
    LightingStyle,
    OpticsLenses,
    ColorScience,
    TransitionType,
    DEFAULT_NEGATIVE_PROMPT,
)
from pipeline.video_gen import VideoGenerationEngine
from pipeline.editor import VideoEditor


# =====================================================================
# PRE-PRODUCTION CHARACTER BIBLE
# =====================================================================
SEASON_CHARACTERS = {
    "Batman": {
        "full_name": "Bruce Wayne / The Batman",
        "role": "Lead Detective / Forensic Investigator",
        "appearance": "6'2\", rugged square jaw, matte-black carbon fiber tactical cowl with glowing white ocular lenses, rain-slicked Kevlar armor with gold utility belt, scalloped bat cape draped over shoulders.",
        "wardrobe_dna": "Dark charcoal battle plate, matte black cowl, wet rain texture, chiaroscuro lighting.",
        "vocal_cadence": "Deep, gravelly, ultra-serious hardboiled noir baritone. Never cracks a smile.",
        "want_need": "To bring forensic reason to an absurd, surreal Gotham underworld conspiracy.",
        "prompt_anchor": "cinematic 35mm film still, Batman in tactical cowl and wet Kevlar armor, rain-drenched Gotham neon noir, 8k resolution, Kodak Vision3 500T, dramatic chiaroscuro lighting",
    },
    "Lady Guppy": {
        "full_name": "Lady Guppy (The Bride)",
        "role": "The Innocent Aquatic Matriarch",
        "appearance": "A magnificent 14-inch Japanese Kohaku koi fish, vibrant fiery scarlet-orange and pearl-white scales, swimming serenely inside a brass-reinforced spherical glass water pod filled with bubbling mineral saline.",
        "wardrobe_dna": "Spherical crystalline water orb, brass rivets, soft cyan bioluminescent water glow.",
        "vocal_cadence": "Silent bubbles and subtle, rhythmic gill movements.",
        "want_need": "To preserve her ancestral oceanic coral sanctuary from feline smugglers.",
        "prompt_anchor": "cinematic 35mm film still, Japanese Kohaku koi fish with vibrant orange and white scales inside an airtight crystal glass water sphere, glowing cyan bubbles, brass fittings, anamorphic lens flare",
    },
    "Sir Longneck": {
        "full_name": "Sir Longneck (The Groom)",
        "role": "The Towering Savanna Aristocrat",
        "appearance": "A regal 16-foot African savannah giraffe draped in a custom-tailored midnight-black velvet tailcoat with a white satin bowtie around its neck, calmly chewing acacia leaves in the Gotham rain.",
        "wardrobe_dna": "Geometric chestnut spots, tailored Victorian tuxedo coat, silk bowtie, tall silhouettes.",
        "vocal_cadence": "Dignified ear flicking, low sub-audible ruminations.",
        "want_need": "To fulfill his diplomatic cross-species vows despite overwhelming legal scrutiny.",
        "prompt_anchor": "cinematic 35mm film still, tall savannah giraffe in elegant black velvet tuxedo and silk bowtie, standing in rain-slicked Gotham alleyway, neon street reflections, anamorphic depth of field",
    },
    "The Mystery Cat": {
        "full_name": "The Mystery Cat (The Mastermind)",
        "role": "The Elusive Feline Phantom",
        "appearance": "A sleek, muscular black-and-white tuxedo feline with piercing golden-amber eyes, wearing a tiny tilted charcoal fedora and a miniature waterproof trench coat, clutching a brass key in its jaws.",
        "wardrobe_dna": "Sleek obsidian fur, white chest patch, miniature fedora, glowing amber eyes.",
        "vocal_cadence": "A low, mocking purr followed by vanishing smoke.",
        "want_need": "To swipe the diamond-crusted aquatic dowry and frame the Gotham underworld.",
        "prompt_anchor": "cinematic 35mm film still, sleek tuxedo cat with glowing amber eyes wearing a miniature charcoal fedora and tiny trenchcoat, perched on stone gargoyle in pouring rain, neon smoke, cinematic 35mm",
    },
    "Alfred Pennyworth": {
        "full_name": "Alfred Pennyworth",
        "role": "Sardonic Butler & Batcave Comms",
        "appearance": "Impeccably groomed elderly gentleman in three-piece Savile Row wool suit with silver pocket watch, silver-rimmed spectacles reflecting Batcomputer monitors.",
        "wardrobe_dna": "Charcoal vest, pressed white collared shirt, silver tie, polished leather.",
        "vocal_cadence": "Dry, impeccably deadpan British sarcasm.",
        "want_need": "To maintain sanity in Wayne Manor while Master Bruce chases aquatic marriage licenses.",
        "prompt_anchor": "cinematic 35mm film still, Alfred Pennyworth in tailored charcoal suit and spectacles in high-tech Batcave, glowing holographic displays, cold atmospheric blue lighting",
    },
}


# =====================================================================
# 8-EPISODE SEASON ARC & SCENE DECOMPOSITION
# =====================================================================
SEASON_EPISODES = [
    {
        "episode_number": 1,
        "title": "The Wet Savannah",
        "logline": "Batman arrives at an abandoned cathedral in Gotham Harbor to investigate a bizarre crime: an altar strewn with kelp, acacia twigs, and an inter-species wedding ring.",
        "screenplay": """
EXT. GOTHAM HARBOR - NIGHT (0:00 - 0:18)
Rain lashes against rusted pier pilings. Neon signs flicker in green and amber puddles.
BATMAN (V.O.)
3:14 AM. Gotham City. A city drowning in rain and delirium. The distress call came from Pier 42: an unauthorized domestic sanctuary breach.

INT. FLOODED CATHEDRAL - NIGHT (0:18 - 0:38)
Batman steps through shattered stained-glass doors into ankle-deep water.
On the stone altar: sea kelp draped across acacia branches. A golden wedding ring sits submerged in a crystal goblet of saltwater.
BATMAN (V.O.)
A union consecrated between water and sky. A koi fish. A savannah giraffe. And then... the unmistakable scent of dried catnip.

EXT. CATHEDRAL ROOFTOP - NIGHT (0:38 - 1:00)
A shadow darts across the slate roof tiles. Glowing amber eyes vanish into the smog.
BATMAN
Alfred. Pull up all Gotham maritime registries. We have an uninvited wedding crasher.
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "Slow cinematic crane down",
                "description": "Rain-drenched Gotham Harbor pier at midnight, neon reflections in saltwater puddles, Wayne Tower in background with lightning flash.",
                "lighting": "Chiaroscuro, deep blue shadows with amber neon accents",
                "audio": "Thunder rumble, heavy rainfall, distant harbor foghorn",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Low angle slow push-in",
                "description": "Batman crouching on stone gargoyle in tactical cowl, rain dripping from chin guard, white optical lenses glowing softly.",
                "lighting": "Edge-lit cyan neon on matte black cowl",
                "audio": "Gravelly voiceover: '3:14 AM. Gotham City. A city drowning in delirium.'",
            },
            {
                "scene_number": 3,
                "duration": 9.0,
                "scale": "MLS",
                "movement": "Tracking dolly forward",
                "description": "Batman walking through shattered cathedral doors into flooded nave, boots splashing through ankle-deep water.",
                "lighting": "Backlit moonlight through gothic arched window",
                "audio": "Splashing boots, somber cello notes, rain on glass",
            },
            {
                "scene_number": 4,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Slow tilt down",
                "description": "Ancient stone altar decorated with wet green sea kelp intertwined with dry yellow savannah acacia twigs.",
                "lighting": "Subtle candle flicker, warm amber vs cool teal",
                "audio": "Low orchestral suspense swell, soft water ripples",
            },
            {
                "scene_number": 5,
                "duration": 9.0,
                "scale": "ECU",
                "movement": "Macro rack focus",
                "description": "A heavy golden wedding ring submerged inside a crystal water goblet, bubbles rising around the gold band.",
                "lighting": "Sparkling crystal caustic reflections",
                "audio": "Subtle underwater harmonic drone, bubble fizz",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "MS",
                "movement": "Whip pan to high rafters",
                "description": "High cathedral ceiling beams where a sleek tuxedo cat in tiny fedora perches, glowing amber eyes staring down.",
                "lighting": "Deep silhouette, glowing amber eyes",
                "audio": "High-pitched feline purr, sudden violin sting",
            },
            {
                "scene_number": 7,
                "duration": 9.0,
                "scale": "MCU",
                "movement": "Fast zoom out to wide shot",
                "description": "Batman looking up, cape flaring as a puff of green catnip smoke bursts on the rafter, cat vanishing into shadows.",
                "lighting": "Eerie neon green smoke flare against dark stonework",
                "audio": "Batman: 'Alfred. Pull the maritime registries.' Cat hiss.",
            },
        ],
    },
    {
        "episode_number": 2,
        "title": "Fin and Hoof",
        "logline": "Batman interrogates underworld contact Sal 'The Gills' at the Gotham Aquarium. The fish's dowry contract is missing, and claw marks scar the bulletproof tanks.",
        "screenplay": """
INT. GOTHAM AQUARIUM - NIGHT (0:00 - 0:25)
Massive curved acrylic tanks cast rippling cyan caustics across the tile floor.
BATMAN corners SAL 'THE GILLS' MARONI against a coral display.
BATMAN
Who officiated the ceremony, Sal? Speak before I test your buoyancy.
SAL
I swear on the sunken city, Bat! It was a real wedding! The giraffe brought acacia foliage, the fish brought pearls! But then the cat showed up with claws!

INT. PRIVATE HOLDING TANK - CONTINUOUS (0:25 - 0:45)
Batman shines a forensic UV light on a shattered glass case. Deep feline claw scratches glow violet on the reinforced acrylic.
BATMAN
Precision incisions. He didn't just crash the wedding. He stole the dowry.

EXT. AQUARIUM ROOF - NIGHT (0:45 - 1:00)
A tiny tuxedo cat silhouette leaps across rooftop air vents, clutching a glowing pearl pendant in its jaws.
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "Slow lateral pan",
                "description": "Gotham Aquarium main exhibition hall at night, giant luminous blue shark tanks glowing in darkness.",
                "lighting": "Deep aquatic cyan and underwater caustic ripples",
                "audio": "Humming water filtration systems, deep hydrophone bass",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MS",
                "movement": "Low angle Dutch tilt",
                "description": "Batman holding nervous mobster Sal against a glass tank, water caustics dancing on Batman's cowl.",
                "lighting": "Contrasting neon green and aquatic cyan",
                "audio": "Sal stammers: 'It was true love, Bat! Fin and hoof!'",
            },
            {
                "scene_number": 3,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Slow zoom in",
                "description": "Lady Guppy the koi fish swimming gracefully inside a illuminated water sphere, scarlet scales catching the light.",
                "lighting": "Radiant warm crimson scales against cyan water",
                "audio": "Soft aquatic bubbles, melancholic oboe melody",
            },
            {
                "scene_number": 4,
                "duration": 9.0,
                "scale": "MCU",
                "movement": "Slow pedestal up",
                "description": "Sir Longneck the giraffe standing politely behind the tank, wearing black silk bowtie, chewing leaves calmly.",
                "lighting": "Warm overhead tungsten spotlight",
                "audio": "Gentle chewing rustle, surreal comedic silence",
            },
            {
                "scene_number": 5,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Forensic scanner sweep",
                "description": "Batman activating forensic blue UV light on glass tank, revealing razor-sharp four-toed feline claw scratches.",
                "lighting": "Fluorescent violet UV glow in deep shadow",
                "audio": "Forensic electronic beep, resonant synthesizer tone",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "MS",
                "movement": "Quick push in",
                "description": "Empty velvet pedestal where the dowry pearl necklace was stolen, only a silver fish scale and cat hair remain.",
                "lighting": "Dramatic chiaroscuro spotlight on empty velvet",
                "audio": "Batman: 'He didn't just crash. He stole the dowry.'",
            },
            {
                "scene_number": 7,
                "duration": 9.0,
                "scale": "EWS",
                "movement": "Tracking pan across skyline",
                "description": "Aquarium exterior roof under pouring rain, tiny silhouette of Mystery Cat dashing along ledge clutching glowing pearls.",
                "lighting": "Gotham neon billboard glow, flashing lightning",
                "audio": "Thunderclap, rain crescendo, frantic brass horn swell",
            },
        ],
    },
    {
        "episode_number": 3,
        "title": "Whispering Whiskers",
        "logline": "A midnight stakeout in Crime Alley leads to Batman's first face-to-face encounter with the enigmatic Mystery Cat, who leaves behind an encrypted audio tape.",
        "screenplay": """
EXT. CRIME ALLEY - MIDNIGHT (0:00 - 0:25)
Steam rises from Gotham storm drains. Rain pours in sheets.
Batman crouches in the deep shadows of an iron fire escape.
BATMAN (V.O.)
The pearls were worth six million. But a fish has no offshore accounts. The giraffe has no bank routing number. Someone else is pulling the strings.

A low, rhythmic scratching sound echoes down the alley.
On a green dumpster, THE MYSTERY CAT sits perched, wearing a drenched charcoal fedora. It tilts its head, amber eyes unblinking.
BATMAN
You're not Selina's. Who sent you?

The cat paws a miniature vintage microcassette player on the dumpster lid and hits PLAY with its front paw.
TAPE VOICE (DISTORTED)
The marriage was legal, Batman! Check the salt content!
The cat bats a smoke capsule—PUFF!—vanishing into lavender mist.
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "High angle slow push down",
                "description": "Crime Alley bathed in pouring rain, flickering neon streetlights reflecting in oily black puddles.",
                "lighting": "Sodium vapor yellow and moody noir shadow",
                "audio": "Heavy raindrops splashing, steam vent hissing",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Profile tracking shot",
                "description": "Batman crouching in rain, raindrops rolling down the smooth black curves of his tactical cowl.",
                "lighting": "Cold blue rim lighting on Kevlar armor",
                "audio": "Batman V.O.: 'The pearls were worth six million...'",
            },
            {
                "scene_number": 3,
                "duration": 7.0,
                "scale": "MS",
                "movement": "Static hold",
                "description": "A green industrial dumpster where The Mystery Cat sits poised like a miniature detective in a damp fedora.",
                "lighting": "Backlit neon sign creating glowing silhouette",
                "audio": "Rhythmic claw scratching on steel dumpster",
            },
            {
                "scene_number": 4,
                "duration": 8.0,
                "scale": "CU",
                "movement": "Slow macro zoom",
                "description": "The Mystery Cat's face: tuxedo white whiskers, tiny tilted charcoal fedora, piercing amber feline eyes.",
                "lighting": "Amber eye reflection reflecting Batman's cowl",
                "audio": "Deep, rumbling feline purr like an idling engine",
            },
            {
                "scene_number": 5,
                "duration": 7.0,
                "scale": "CU",
                "movement": "Downward tilt",
                "description": "The cat's white-gloved paw deliberately pressing PLAY button on a miniature vintage microcassette recorder.",
                "lighting": "Red recording LED light glowing on fur",
                "audio": "Mechanical cassette click, tape hiss",
            },
            {
                "scene_number": 6,
                "duration": 7.0,
                "scale": "MCU",
                "movement": "Over-the-shoulder shot",
                "description": "Batman stepping forward with batarang ready as distorted voice broadcasts: 'Check the salt content, Batman!'",
                "lighting": "Flickering streetlight creating harsh shadows",
                "audio": "Distorted tape voice, rising orchestral tension",
            },
            {
                "scene_number": 7,
                "duration": 7.0,
                "scale": "MS",
                "movement": "Explosive snap zoom",
                "description": "The Mystery Cat swiping a smoke pellet with its tail, bursting into thick lavender catnip smoke.",
                "lighting": "Brilliant purple and lavender flash in the dark alley",
                "audio": "Hissing smoke grenade burst, cat meow echo",
            },
            {
                "scene_number": 8,
                "duration": 8.0,
                "scale": "MLS",
                "movement": "Crane up into rain",
                "description": "Batman standing alone in dissipating purple smoke, holding the microcassette recorder as rain washes the alley.",
                "lighting": "Atmospheric noir street illumination",
                "audio": "Somber piano melody, fading tape hiss, rain",
            },
        ],
    },
    {
        "episode_number": 4,
        "title": "Deep Water, High Foliage",
        "logline": "Inside the Batcave, Batman and Alfred run biochemical cross-analysis on the wedding evidence, discovering an impossible genetic and financial paper trail.",
        "screenplay": """
INT. BATCAVE - NIGHT (0:00 - 0:30)
Giant multi-panel Batcomputer displays glow in ice-blue and amber.
On one screen: molecular structure of Japanese Koi scales.
On the other: cellular taxonomy of African Savannah Acacia foliage.
Batman taps furiously at the console. ALFRED approaches with silver tea service.
ALFRED
Master Bruce. Forgive my botanical ignorance, but is the Wayne Enterprises quantum satellite currently tracking a goldfish's prenuptial agreement?
BATMAN
Not just a goldfish, Alfred. Look at the water salinity in the bridal pod. It contains trace enzymes found only in the Arctic Iceberg Lounge vault.

INT. BATCAVE FORENSIC LAB - (0:30 - 1:00)
A robotic centrifuge spins down a vial of water and cat hair.
BATMAN
The marriage wasn't romantic folly. It was a legal merger. Under Gotham Maritime Law, an aquatic-terrestrial union grants joint diplomatic immunity.
ALFRED
How delightfully progressive. And the feline?
BATMAN
The cat is the executor.
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "Sweeping crane across Batcave",
                "description": "Cavernous Batcave with massive waterfalls cascading in background, glowing supercomputer arrays reflecting on stalactites.",
                "lighting": "Deep cobalt blue cave shadows, luminous amber screens",
                "audio": "Rushing underground waterfall, computer humming",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Slow tracking shot",
                "description": "Batman at the Batcomputer console, typing with black gauntlets, glowing code cascading across his lenses.",
                "lighting": "Screen glow illuminating Batman's focused jawline",
                "audio": "Rapid mechanical keyboard clicks, data processing beeps",
            },
            {
                "scene_number": 3,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Screen screen graphic zoom",
                "description": "Holographic display showing 3D wireframe of koi fish skeleton overlapping a 3D wireframe of giraffe vertebrae.",
                "lighting": "Vibrant cyan wireframe and orange biometric pulse",
                "audio": "Digital processing chime, synthetic pulse tone",
            },
            {
                "scene_number": 4,
                "duration": 9.0,
                "scale": "MS",
                "movement": "Medium two-shot",
                "description": "Alfred Pennyworth pouring Earl Grey tea from a silver pot into a porcelain teacup beside the analysis terminal.",
                "lighting": "Warm side key light on Alfred's tailored suit",
                "audio": "Tea pouring into cup, Alfred: 'Is this a goldfish prenup?'",
            },
            {
                "scene_number": 5,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Macro rack focus",
                "description": "Forensic test tube spinning in centrifuge, separating glowing luminescent water from a single black cat hair.",
                "lighting": "High-tech sterile blue and white LED illumination",
                "audio": "High-speed centrifuge whir, centrifuge spin-down",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Slow push in on Batman's eyes",
                "description": "Batman's cowl lenses narrowing as analysis pops up: 'DIPLOMATIC IMMUNITY CONFERRED - GOTHAM MARITIME CODE 84.1'.",
                "lighting": "Dramatic red alert reflection in white lenses",
                "audio": "Batman: 'The marriage wasn't folly. It was a merger.'",
            },
            {
                "scene_number": 7,
                "duration": 9.0,
                "scale": "MLS",
                "movement": "Pull back to wide Batmobile bay",
                "description": "Batman grabbing his cape and striding toward the sleek jet-black Batmobile as turbine engines ignite with orange fire.",
                "lighting": "Orange jet turbine exhaust illuminating dark cave floor",
                "audio": "Jet turbine spool-up roar, cape swoosh, driving drums",
            },
        ],
    },
    {
        "episode_number": 5,
        "title": "The Dowry Heist",
        "logline": "At the opulent Iceberg Lounge reception, Sir Longneck and Lady Guppy arrive in lavish gala attire, but the Mystery Cat executes an aerial heist from the crystal chandeliers.",
        "screenplay": """
INT. ICEBERG LOUNGE BALLROOM - NIGHT (0:00 - 0:30)
Gotham's corrupt elite in black tie sip champagne beneath colossal crystal chandeliers.
SIR LONGNECK towers above the crowd, wearing a bespoke silk tuxedo.
LADY GUPPY floats in a mobile crystal carriage filled with champagne-colored water.
On her orb rests the legendary Star of Atlantis diamond.

SUDDENLY—THE LIGHTS FLICKER!
From the main chandelier, fifty feet above, THE MYSTERY CAT drops on a thin nylon thread!
It snatches the diamond in its teeth with acrobatic grace.
GUESTS SCREAM.

EXT. BALLROOM GLASS SKYLIGHT - CONTINUOUS (0:30 - 1:00)
CRASH! Batman smashes through the ceiling glass, grappling hook firing into the chandelier.
BATMAN
Down, cat!
The cat winks, releases the wire, and lands on Sir Longneck's antlers!
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 7.0,
                "scale": "EWS",
                "movement": "Slow descending crane",
                "description": "Opulent art-deco ballroom of the Iceberg Lounge, high ceilings, glittering crystal chandeliers, elite guests in black tie.",
                "lighting": "Warm golden champagne glow, glistening crystal refractions",
                "audio": "Clinking champagne flutes, jazz swing band music",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MLS",
                "movement": "Tracking shot through crowd",
                "description": "Sir Longneck the giraffe wearing a magnificent black tuxedo, head gently nodding above the sea of tuxedoed guests.",
                "lighting": "Gilded chandeliers casting warm glow on patterned fur",
                "audio": "Crowd murmurs, soft brass trumpet melody",
            },
            {
                "scene_number": 3,
                "duration": 7.0,
                "scale": "CU",
                "movement": "Slow orbital move",
                "description": "Lady Guppy the koi fish floating in a gilded water carriage, a sparkling blue diamond necklace secured to her orb.",
                "lighting": "Prismatic diamond sparkles shimmering through water",
                "audio": "Ethereal harp glissando, bubbly water hum",
            },
            {
                "scene_number": 4,
                "duration": 8.0,
                "scale": "MS",
                "movement": "High angle looking down",
                "description": "High in the crystal chandelier, The Mystery Cat in trenchcoat crouching on brass armature, adjusting its fedora.",
                "lighting": "Gleaming crystal prism lights framing the feline",
                "audio": "Creaking brass chain, faint feline chitter",
            },
            {
                "scene_number": 5,
                "duration": 7.0,
                "scale": "MLS",
                "movement": "Fast whip down",
                "description": "The Mystery Cat repelling down on a black thread, swiping the diamond in its mouth right off the glass orb.",
                "lighting": "Strobe flash as ballroom lights flicker violently",
                "audio": "High-speed wire zip, glass clink, crowd gasps",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "Dynamic upward tilt",
                "description": "Glass skylight shattering in explosive shower as Batman crashes through, black cape billowing like giant wings.",
                "lighting": "Exploding ceiling glass catching moonlight and amber neon",
                "audio": "Glass explosion crash, thunderous percussion hit",
            },
            {
                "scene_number": 7,
                "duration": 7.0,
                "scale": "MCU",
                "movement": "Action tracking pan",
                "description": "The Mystery Cat landing gracefully on Sir Longneck's giraffe antlers, balancing on one paw while holding the diamond.",
                "lighting": "Chiaroscuro spotlight tracking the acrobatic landing",
                "audio": "Surreal comedic cartoon brass hit, cat landing thud",
            },
            {
                "scene_number": 8,
                "duration": 8.0,
                "scale": "MS",
                "movement": "Low angle hero hold",
                "description": "Batman landing in three-point stance on dancefloor, cape swirling, eyes locked upward at the cat atop the giraffe.",
                "lighting": "Dramatic blue backlight through shattered ceiling",
                "audio": "Batman: 'Down, cat.' Heavy boots on marble.",
            },
        ],
    },
    {
        "episode_number": 6,
        "title": "Arkham Sub-Aquatic",
        "logline": "Batman dives into Arkham Asylum's submerged detention block to interrogate the Feline Syndicate's imprisoned accountant, exposing the true mastermind.",
        "screenplay": """
INT. ARKHAM ASYLUM - SUB-AQUATIC WARD - NIGHT (0:00 - 0:30)
Water drips constantly through cracked concrete foundations.
Submerged prison cells hold Gotham's aquatic freaks.
Batman walks past rusted iron bars to CELL 104: THE GREAT WHITE SHARK.
BATMAN
Who drafted the marriage papers, Warren?
WARREN
(Laughs, water spraying)
You don't get it, Bats! The fish owns the harbor rights! The giraffe owns the savanna shipping lanes! And the Cat... the Cat is the only one who can sign for both!

Batman slams his gauntlet on the iron cell door.
BATMAN
Where is the drop-off?
WARREN
The clock tower. Dawn. When the tide changes!
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 8.0,
                "scale": "EWS",
                "movement": "Slow dolly down damp hallway",
                "description": "Arkham Asylum sub-aquatic ward, cracked green tiles, rusted iron pipes dripping water into murky floor drains.",
                "lighting": "Flickering sickly fluorescent green and deep black shadow",
                "audio": "Dripping water echo, eerie distant metallic clanging",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Low angle slow track",
                "description": "Batman striding down the prison corridor, cowl wet, cape trailing in water puddles, stern expression.",
                "lighting": "Intermittent overhead light blinking across Kevlar",
                "audio": "Echoing boot footsteps, low cello drone",
            },
            {
                "scene_number": 3,
                "duration": 9.0,
                "scale": "MS",
                "movement": "Push in through bars",
                "description": "Underworld convict behind reinforced iron bars, sharp pointed teeth grinning through shadows.",
                "lighting": "Harsh slit-light across grinning face",
                "audio": "Convict laughing: 'You don't get it, Bats!'",
            },
            {
                "scene_number": 4,
                "duration": 9.0,
                "scale": "CU",
                "movement": "Rapid zoom in on gauntlet",
                "description": "Batman slamming armored gauntlet onto rusted iron bars, sparks scattering across the wet cell floor.",
                "lighting": "Electric blue sparks illuminating the gloom",
                "audio": "Deafening metallic impact boom, reverb tail",
            },
            {
                "scene_number": 5,
                "duration": 9.0,
                "scale": "MCU",
                "movement": "Tight two-shot profile",
                "description": "Batman leaning in close to the bars: 'Where is the drop-off?' Convict shivering: 'The clock tower at dawn!'",
                "lighting": "Extreme chiaroscuro noir lighting on faces",
                "audio": "Tense whispered dialogue, rising strings crescendo",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "MLS",
                "movement": "Quick turn and walk away",
                "description": "Batman turning sharply, cape swirling in a black vortex as he exits the submerged ward.",
                "lighting": "Silhouette retreating down green illuminated corridor",
                "audio": "Cape whoosh, distant asylum alarm buzz",
            },
            {
                "scene_number": 7,
                "duration": 9.0,
                "scale": "EWS",
                "movement": "Ascending tilt up exterior",
                "description": "Exterior Arkham Asylum Gothic fortress towering over stormy ocean waves crashing against jagged cliffs.",
                "lighting": "Lightning illuminating jagged stone spires and churning surf",
                "audio": "Massive ocean wave crash, thunder roll, brass finale",
            },
        ],
    },
    {
        "episode_number": 7,
        "title": "The Slate Rooftop Pursuit",
        "logline": "A high-octane chase across Gotham's rain-slicked rooftops and gargoyles. Batman pursues the Mystery Cat, who navigates sheer spires clutching the wedding loot.",
        "screenplay": """
EXT. GOTHAM SKYLINE - 5:00 AM (0:00 - 0:30)
Rain pours over gothic slate rooftops. Fog rolls between skyscrapers.
The Mystery Cat races along an impossibly narrow stone parapet, leaping from gargoyle to gargoyle with acrobatic ease, the diamond ledger secured in its jaws.

Behind it—THE BATCYCLE roars along an elevated suspension skyway, tires spraying rooster-tails of water!
Batman launches off the motorcycle seat into mid-air!
GRAPPLE GUN FIRES—THWIP!
Batman swings beneath the clock tower face, skimming the wet roof tiles.
BATMAN
End of the line, Whiskers.
The cat screeches, doing a backflip onto the giant clock hand!
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 7.0,
                "scale": "EWS",
                "movement": "Fast tracking aerial flyover",
                "description": "Gotham City skyline before dawn, towering art-deco skyscrapers, rain pouring across slate roofs, neon glow.",
                "lighting": "Pre-dawn violet twilight and flashing crimson tower beacons",
                "audio": "Wind howling, heavy rain roar, pounding timpani",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MLS",
                "movement": "High-speed lateral tracking",
                "description": "The Mystery Cat sprinting at full speed along an ornate stone roof parapet, tiny fedora flying, leaping over gaps.",
                "lighting": "Streaking city neon reflections on wet stone",
                "audio": "Rapid feline claws clicking on slate, urgent brass fanfare",
            },
            {
                "scene_number": 3,
                "duration": 7.0,
                "scale": "MS",
                "movement": "Low angle forward track",
                "description": "The Batcycle tearing down a rain-slicked elevated bridge, twin headlights slicing through fog, water spray.",
                "lighting": "Piercing white headlights, blue neon bridge cables",
                "audio": "High-octane motorcycle engine roar, tire screech",
            },
            {
                "scene_number": 4,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Action camera side-mount",
                "description": "Batman on the Batcycle, one hand on throttle, raising magnetic grapple gun with the other, aiming high.",
                "lighting": "Strobe flashes of passing streetlights on cowl",
                "audio": "Pneumatic grapple locking click, engine rev",
            },
            {
                "scene_number": 5,
                "duration": 7.0,
                "scale": "MLS",
                "movement": "Dynamic swing tracking",
                "description": "Batman ejecting from bike, grapple line hooking gargoyle, swinging through misty air with cape extended.",
                "lighting": "Backlit against massive illuminated clock tower dial",
                "audio": "High-tension wire hum, cape aerodynamic flap",
            },
            {
                "scene_number": 6,
                "duration": 8.0,
                "scale": "CU",
                "movement": "Slow motion acrobatics",
                "description": "The Mystery Cat mid-air backflip, claws splayed, clutching the golden wedding ledger tightly in its teeth.",
                "lighting": "Moonlight rim lighting on flying tuxedo fur",
                "audio": "Graceful orchestral slow-motion string harmony",
            },
            {
                "scene_number": 7,
                "duration": 7.0,
                "scale": "MS",
                "movement": "Hard impact landing",
                "description": "The cat landing with all four paws onto the giant minute hand of Wayne Clock Tower, 400 feet above the street.",
                "lighting": "Glowing white frosted glass clock face beneath cat",
                "audio": "Mechanical clock gear clank, sudden brass chord",
            },
            {
                "scene_number": 8,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Reverse angle confrontational hold",
                "description": "Batman landing on the hour hand, blocking the cat's exit, rain cascading off both figures high above Gotham.",
                "lighting": "Silhouette standoff against the giant glowing clock",
                "audio": "Deep grandfather clock chime: DONG! Rain.",
            },
        ],
    },
    {
        "episode_number": 8,
        "title": "The Midnight Annulment",
        "logline": "Dawn breaks over Gotham. The Mystery Cat is cornered, the absurd marriage is peacefully annulled, and Batman reflects on the city's strange justice.",
        "screenplay": """
EXT. WAYNE TOWER CLOCK - DAWN (0:00 - 0:30)
Golden sunrise rays pierce through Gotham's purple smog.
The Mystery Cat sits surrounded. It slowly lowers the diamond ledger onto the clock hand, raises two front paws in surrender, and offers a contrite meow.
Batman retrieves the ledger.

EXT. GOTHAM HARBOR DOCKS - DAWN (0:30 - 0:50)
Sir Longneck the giraffe bows his long neck gracefully. He steps forward and stamps an official ink-pad with his giant hoof onto the annulment parchment.
Lady Guppy inside her crystal water sphere releases a stream of joyful bubbles.
The sphere opens gently into the ocean harbor. Lady Guppy swims into the sparkling sunrise waves.

EXT. GOTHAM ROOFTOP - DAWN (0:50 - 1:00)
Batman stands on a stone gargoyle, cape catching the morning golden light.
BATMAN (V.O.)
The giraffe returns to the savanna. The koi returns to the bay. The cat... assigned to sixty hours of community mousetrap patrol.
Justice is cold, Gotham. Sometimes it smells like tuna.
But tonight... you sleep.
""",
        "scenes": [
            {
                "scene_number": 1,
                "duration": 7.0,
                "scale": "EWS",
                "movement": "Majestic wide sunrise pull-back",
                "description": "Dawn breaking over Gotham City, golden orange and rose-tinted sunlight piercing through heavy storm clouds.",
                "lighting": "Warm morning gold contrasting with cool night purple",
                "audio": "Gentle choir swell, fading rain, morning bird cry",
            },
            {
                "scene_number": 2,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Slow downward tilt",
                "description": "The Mystery Cat sitting contritely on the giant clock hand, pushing the diamond ledger forward with its nose, paws up.",
                "lighting": "Warm sunrise glow on tuxedo fur and miniature fedora",
                "audio": "Soft, innocent feline meow, warm oboe notes",
            },
            {
                "scene_number": 3,
                "duration": 8.0,
                "scale": "MS",
                "movement": "Low angle ground shot",
                "description": "At the harbor docks, Sir Longneck the giraffe politely dipping front hoof in blue ink and stamping an official document.",
                "lighting": "Warm golden light glistening on wet dock timbers",
                "audio": "Firm stamp thud, dry paper rustle, gentle giraffe snort",
            },
            {
                "scene_number": 4,
                "duration": 7.0,
                "scale": "CU",
                "movement": "Document macro view",
                "description": "Official Gotham court parchment with an ink giraffe hoof-print beside a tiny golden fish scale: 'MARRIAGE DISSOLVED'.",
                "lighting": "Morning sun catching gold foil seal on legal paper",
                "audio": "Legal gavel strike echo, warm acoustic guitar",
            },
            {
                "scene_number": 5,
                "duration": 8.0,
                "scale": "MLS",
                "movement": "Gentle pedestal down to water",
                "description": "Lady Guppy's crystal pod releasing into the open harbor water, the red-and-white koi swimming freely into the sunrise bay.",
                "lighting": "Glittering golden ocean surface and dancing sunbeams",
                "audio": "Gentle water splash, bubbling joyful harmonics",
            },
            {
                "scene_number": 6,
                "duration": 7.0,
                "scale": "CU",
                "movement": "Playful side pan",
                "description": "The Mystery Cat sitting in Gotham animal shelter wearing a tiny orange safety vest, swatting a toy mouse.",
                "lighting": "Bright cheerful morning light through shelter window",
                "audio": "Playful toy squeak, lighthearted pizzicato strings",
            },
            {
                "scene_number": 7,
                "duration": 8.0,
                "scale": "MCU",
                "movement": "Slow low-angle pedestal up",
                "description": "Batman perched high on gargoyle overlooking waking city, golden sunrise washing across battle-scarred cowl.",
                "lighting": "Majestic golden hour key light on black tactical armor",
                "audio": "Batman V.O.: 'Justice is cold. Sometimes it smells like tuna.'",
            },
            {
                "scene_number": 8,
                "duration": 7.0,
                "scale": "EWS",
                "movement": "Grand cinematic pull-back into sky",
                "description": "Batman's silhouette standing sentinel as golden sunlight bathes all of Gotham City. Title card: 'THE END'.",
                "lighting": "Spectacular golden sunrise over Gotham bay and towers",
                "audio": "Triumphant full orchestral brass crescendo, final piano chord",
            },
        ],
    },
]


class SeasonOrchestrator:
    """Manages season-wide story creation, episode generation, and master stitching."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or settings.video_provider).lower()
        self.video_engine = VideoGenerationEngine(provider=self.provider)
        self.editor = VideoEditor()

    def build_episode_storyboard(self, ep_data: Dict[str, Any], aspect_ratio: str = "16:9") -> Storyboard:
        """Constructs a Storyboard instance from curated episode data."""
        ep_num = ep_data["episode_number"]
        characters_list = [
            CharacterProfile(
                character_id=k.lower().replace(" ", "_"),
                name=k.upper(),
                role=v["role"],
                appearance=v["appearance"],
                wardrobe_visual_dna=v["wardrobe_dna"],
                voice_and_cadence=v["vocal_cadence"],
                backstory="Key figure in Gotham's aquatic marital mystery.",
                internal_conflict=v["want_need"],
                prompt_anchor=v["prompt_anchor"],
            )
            for k, v in SEASON_CHARACTERS.items()
        ]
        screenplay = Screenplay(
            title=f"Batman: Ep {ep_num:02d} - {ep_data['title']}",
            logline=ep_data["logline"],
            dramatic_theme="Absurdist Domestic Noir",
            genre="Cinematic Neo-Noir",
            characters=characters_list,
            scenes=[],
        )
        storyboard = Storyboard(
            project_id=f"season_ep{ep_num:02d}_{int(time.time())}",
            title=f"Batman: Ep {ep_num:02d} - {ep_data['title']}",
            logline=ep_data["logline"],
            genre="Cinematic Neo-Noir",
            total_target_duration=60.0,
            aspect_ratio=aspect_ratio,
            screenplay=screenplay,
        )

        for sc in ep_data["scenes"]:
            desc = sc["description"]
            desc_lower = desc.lower()

            # Determine character blockings for this specific shot
            char_blockings: List[StageCharacterBlocking] = []
            chars_in_shot: List[str] = []

            if "cat" in desc_lower or "feline" in desc_lower or "whiskers" in desc_lower:
                chars_in_shot.append("The Mystery Cat")
                char_blockings.append(
                    StageCharacterBlocking(
                        character_id="the_mystery_cat",
                        name="The Mystery Cat",
                        position=SpatialGridPoint(x=-0.45, y=0.0, z=0.8, named_zone="STAGE_LEFT_ALTAR_TABLE"),
                        facing_angle_deg=45.0,
                        facing_description="Facing 45 degrees Downstage-Right towards center altar goblet",
                        eyeline_vector="Piercing amber eyes fixed on the golden wedding ring",
                        physical_pose="Curled on mahogany table surface beside goblet, paws tucked, tail still",
                        continuity_anchor="Permanently anchored on Altar Table Stage-Left; MUST NOT relocate without scripted cut",
                    )
                )

            if "koi" in desc_lower or "fish" in desc_lower or "lady guppy" in desc_lower or "bride" in desc_lower:
                chars_in_shot.append("Lady Guppy")
                char_blockings.append(
                    StageCharacterBlocking(
                        character_id="lady_guppy",
                        name="Lady Guppy",
                        position=SpatialGridPoint(x=0.0, y=0.0, z=0.8, named_zone="CENTER_ALTAR_POD"),
                        facing_angle_deg=0.0,
                        facing_description="Facing Downstage through spherical crystal lens",
                        eyeline_vector="Looking serenely through saline water bubbles",
                        physical_pose="Swimming gracefully inside reinforced glass sphere filled with mineral saline",
                        continuity_anchor="Stationary at Center Altar surface; glass sphere remains anchored",
                    )
                )

            if "giraffe" in desc_lower or "sir longneck" in desc_lower or "groom" in desc_lower:
                chars_in_shot.append("Sir Longneck")
                char_blockings.append(
                    StageCharacterBlocking(
                        character_id="sir_longneck",
                        name="Sir Longneck",
                        position=SpatialGridPoint(x=-0.65, y=0.45, z=0.0, named_zone="UPSTAGE_LEFT_TUXEDO"),
                        facing_angle_deg=315.0,
                        facing_description="Bowing 16-foot neck down towards the altar pod",
                        eyeline_vector="Dignified gaze resting upon the aquatic bride pod",
                        physical_pose="Standing tall in black velvet tuxedo coat and silk bowtie",
                        continuity_anchor="Positioned Upstage-Left towering over altar; maintain screen-left height",
                    )
                )

            if "batman" in desc_lower or "bruce" in desc_lower or "detective" in desc_lower or "cowl" in desc_lower or not chars_in_shot:
                chars_in_shot.append("Batman")
                char_blockings.append(
                    StageCharacterBlocking(
                        character_id="batman",
                        name="Batman",
                        position=SpatialGridPoint(x=0.5, y=-0.5, z=0.9, named_zone="STAGE_RIGHT_GARGOYLE"),
                        facing_angle_deg=315.0,
                        facing_description="Facing Downstage-Left toward the wedding crime scene",
                        eyeline_vector="Lenses zoomed on the table evidence and feline paw prints",
                        physical_pose="Brooding low crouch, scalloped cape draped over gargoyle ledge, rain dripping from cowl",
                        continuity_anchor="Anchored on Elevated Gargoyle Stage-Right; maintains high-angle vantage",
                    )
                )

            # Define persistent tracked scene objects
            tracked_objs = [
                TrackedSceneObject(
                    object_id="obj_01_submerged_gold_wedding_ring",
                    name="Submerged Golden Wedding Ring",
                    position=SpatialGridPoint(x=0.0, y=0.0, z=0.8, named_zone="CENTER_ALTAR_GOBLET"),
                    container_or_surface="Submerged in crystal goblet on Center Altar table",
                    visual_state="24k gold band submerged in mineral saline with micro-bubbles and caustic light rings",
                    continuity_lock="Permanent fixture at Center Altar; must remain visible when camera faces altar",
                ),
                TrackedSceneObject(
                    object_id="obj_04_brass_maritime_key",
                    name="Antique Brass Maritime Key",
                    position=SpatialGridPoint(x=-0.45, y=0.0, z=0.8, named_zone="STAGE_LEFT_TABLE"),
                    container_or_surface="Held in Mystery Cat's jaws or resting beside paw on table",
                    visual_state="Weathered nautical brass skeleton key with anchor crest, dripping with seawater",
                    continuity_lock="Bound to Mystery Cat's immediate physical vicinity",
                ),
                TrackedSceneObject(
                    object_id="obj_05_sea_kelp_acacia_altar",
                    name="Kelp & Acacia Wedding Altar",
                    position=SpatialGridPoint(x=0.0, y=0.0, z=0.8, named_zone="CENTER_ALTAR_SURFACE"),
                    container_or_surface="Ancient stone altar surface",
                    visual_state="Intertwined wet green sea kelp and dry golden acacia twigs draped across stone",
                    continuity_lock="Permanent architectural centerpiece",
                ),
            ]

            # Define camera 180-degree action line and blocking
            cam_blocking = CameraBlocking(
                axis_of_action_180="180-degree axis locked on the line between Downstage Entrance and Center Altar; camera strictly operates in South-East quadrant",
                camera_position=SpatialGridPoint(x=0.25, y=-0.75, z=1.0, named_zone="DOWNSTAGE_RIGHT_CINE_CRANE"),
                camera_elevation_angle="Low-Angle 20 degrees upward tilt from 30 inches off water surface",
                camera_fov="35mm anamorphic prime (65-degree horizontal FOV)",
                focal_target=f"{chars_in_shot[0]} at {char_blockings[0].position.named_zone}",
            )

            # Spatial Transition continuity
            spatial_trans = SpatialTransition(
                transition_type=TransitionType.HARD_CUT if sc["scene_number"] % 2 == 0 else TransitionType.DISSOLVE,
                duration_seconds=0.5 if sc["scene_number"] % 2 != 0 else 0.0,
                spatial_carryover_notes=(
                    "Cat remains strictly on Altar Table Stage-Left; Ring remains in Center Goblet; "
                    "Batman maintains Stage-Right screen presence. 180-degree axis preserved across cut."
                ),
            )

            # Build multi-layered prompt with Hollywood Film Skills and explicit spatial blocking
            scale_enum = ShotType.MEDIUM_SHOT
            for st in ShotType:
                if st.name.startswith(sc["scale"]) or sc["scale"] in st.value:
                    scale_enum = st
                    break

            visual_prompt = FilmPromptBuilder.build_prompt(
                subject_action=desc,
                shot_type=scale_enum,
                camera_movement=CameraMovement.SLOW_PUSH_IN if "push" in sc["movement"].lower() else CameraMovement.STATIC,
                lighting=LightingStyle.CHIAROSCURO if "chiaroscuro" in sc["lighting"].lower() else LightingStyle.NEON_CYBER_NOIR,
                lens=OpticsLenses.ANAMORPHIC_35MM,
                color_science=ColorScience.KODAK_VISION3_35MM,
                visual_dna="; ".join(SEASON_CHARACTERS[c]["prompt_anchor"] for c in chars_in_shot if c in SEASON_CHARACTERS),
                environmental_atmosphere="Heavy rain, wet reflective surfaces, atmospheric fog, Gotham neon reflections",
                spatial_blocking="; ".join(f"{cb.name} at {cb.position.named_zone} ({cb.facing_description}, stance: {cb.physical_pose})" for cb in char_blockings),
                object_locations="; ".join(f"{ob.name} anchored at {ob.position.named_zone}" for ob in tracked_objs),
                camera_axis=cam_blocking.axis_of_action_180,
            )

            scene = Scene(
                scene_number=sc["scene_number"],
                title=f"Scene {sc['scene_number']:02d}: {sc['scale']}",
                slugline_ref=ep_data["title"],
                action_description=sc["description"],
                shot_type=sc["scale"],
                camera_movement=sc["movement"],
                lighting=sc["lighting"],
                stage_environment=f"Flooded Gothic Cathedral sanctuary and Gotham Harbor pier for {ep_data['title']}",
                character_blockings=char_blockings,
                tracked_objects=tracked_objs,
                camera_blocking=cam_blocking,
                spatial_transition=spatial_trans,
                characters_in_shot=chars_in_shot,
                sound_effects_cue=sc["audio"],
                visual_prompt=visual_prompt,
                negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                duration_seconds=float(sc["duration"]),
                transition_to_next=TransitionConfig(
                    transition_type=TransitionType.DISSOLVE if sc["scene_number"] % 2 != 0 else TransitionType.HARD_CUT,
                    duration_seconds=0.5 if sc["scene_number"] % 2 != 0 else 0.0,
                ),
            )
            storyboard.scenes.append(scene)

        return storyboard

    def run_season(
        self,
        episodes_count: int = 8,
        aspect_ratio: str = "16:9",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Executes generation of all requested episodes and assembles the season supercut."""
        print("\n=======================================================")
        print(f" 🎬 LAUNCHING SEASON 1: BATMAN & THE AQUATIC CONSPIRACY")
        print(f" Episodes: {episodes_count} | Mode: 60s/Episode | Provider: {self.provider.upper()}")
        print(f" Dry-Run: {dry_run} | Aspect Ratio: {aspect_ratio}")
        print("=======================================================\n")

        rendered_episodes: List[Path] = []
        season_manifest = {
            "title": "Batman: The Aquatic Mammalian Matrimony",
            "episodes": [],
            "completed_at": None,
        }

        # Select episodes to produce
        episodes_to_run = SEASON_EPISODES[:episodes_count]

        for ep_data in episodes_to_run:
            ep_num = ep_data["episode_number"]
            ep_title = ep_data["title"]
            print(f"\n>>> [SEASON] Starting Episode {ep_num:02d}: '{ep_title}' <<<")

            # 1. Build Storyboard
            storyboard = self.build_episode_storyboard(ep_data, aspect_ratio=aspect_ratio)
            job_file = settings.jobs_dir / f"{storyboard.project_id}.json"
            storyboard.save(job_file)

            ep_output_dir = settings.output_dir / f"season_ep{ep_num:02d}"
            ep_output_dir.mkdir(parents=True, exist_ok=True)

            # 2. Generate Scene Clips with Last-Frame Continuity
            scene_clips: List[Path] = []
            prev_last_frame: Optional[Path] = None

            for scene in storyboard.scenes:
                if prev_last_frame and prev_last_frame.exists():
                    scene.reference_image_path = str(prev_last_frame)

                clip_p = self.video_engine.generate_scene_clip(
                    scene=scene,
                    output_dir=ep_output_dir,
                    aspect_ratio=aspect_ratio,
                    dry_run=dry_run,
                )
                scene_clips.append(clip_p)

                if scene.last_frame_path and Path(scene.last_frame_path).exists():
                    prev_last_frame = Path(scene.last_frame_path)

            storyboard.save(job_file)

            # 3. Assemble Episode Master with Transitions & Soundtrack
            ep_master_path = settings.output_dir / f"episode_{ep_num:02d}_{ep_title.lower().replace(' ', '_')}.mp4"
            print(f"[SEASON] Assembling Episode {ep_num:02d} Master -> {ep_master_path.name}...")

            try:
                self.editor.stitch_storyboard(
                    storyboard=storyboard,
                    output_file=ep_master_path,
                    use_transitions=True,
                )
                assembled_ok = ep_master_path.exists() and ep_master_path.stat().st_size > 0
            except Exception as e:
                print(f"[SEASON] Error assembling episode {ep_num:02d}: {e}")
                assembled_ok = False

            if assembled_ok and ep_master_path.exists() and ep_master_path.stat().st_size > 0:
                rendered_episodes.append(ep_master_path)
                print(f"✅ Episode {ep_num:02d} Complete: {ep_master_path}")
                season_manifest["episodes"].append({
                    "episode_number": ep_num,
                    "title": ep_title,
                    "path": str(ep_master_path),
                    "size_bytes": ep_master_path.stat().st_size,
                    "scenes_count": len(storyboard.scenes),
                })
            else:
                print(f"⚠️ Episode {ep_num:02d} assembly failed.")

        # 4. Assemble Full Season Compilation Supercut
        if len(rendered_episodes) > 1:
            season_supercut = settings.output_dir / "season_01_complete_master.mp4"
            print(f"\n[SEASON] Compiling full Season Supercut ({len(rendered_episodes)} episodes) -> {season_supercut.name}...")
            # Use concatenate
            concat_ok = self.editor.concatenate_videos(rendered_episodes, season_supercut)
            if concat_ok and season_supercut.exists():
                print(f"🎉 FULL SEASON MASTER COMPILED: {season_supercut} ({season_supercut.stat().st_size} bytes)")
                season_manifest["season_supercut"] = str(season_supercut)

        season_manifest["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        manifest_path = settings.output_dir / "season_01_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(season_manifest, f, indent=2)

        print("\n=======================================================")
        print(f" 🏆 SEASON PRODUCTION SUMMARY")
        print(f" Total Episodes Produced: {len(rendered_episodes)} / {episodes_count}")
        print(f" Output Manifest: {manifest_path}")
        print("=======================================================\n")

        return season_manifest
