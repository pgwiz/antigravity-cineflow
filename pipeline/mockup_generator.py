"""Visual Storyboard Mockup and Named Asset Generator for Antigravity CineFlow.

Generates named character asset dossiers, tracked object cards, and comprehensive
production storyboard mockup cards featuring 2D spatial stage blocking diagrams,
camera frustum angles, 180-degree action axes, and finely defined continuity rules.
"""

import math
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from pipeline.storyboard import Storyboard, Scene, CharacterProfile, SpatialGridPoint, StageCharacterBlocking, TrackedSceneObject


# =====================================================================
# NAMED ASSET DEFINITIONS
# =====================================================================

CHARACTER_ASSET_SPECS = [
    {
        "filename": "char_01_batman_noir.png",
        "name": "BATMAN / BRUCE WAYNE",
        "role": "Lead Forensic Detective",
        "color": (40, 50, 70),
        "accent": (255, 215, 0),
        "dna": "Matte black Kevlar tactical cowl, glowing white ocular lenses, scalloped cape, gold utility belt.",
        "anchor": "Batman in tactical cowl and wet Kevlar armor, rain-drenched Gotham neon noir, Kodak Vision3 500T",
    },
    {
        "filename": "char_02_lady_guppy_koi.png",
        "name": "LADY GUPPY (THE BRIDE)",
        "role": "Innocent Aquatic Matriarch",
        "color": (200, 60, 40),
        "accent": (0, 220, 255),
        "dna": "14-inch Japanese Kohaku koi fish, scarlet and pearl scales, spherical glass pod with brass rivets.",
        "anchor": "Japanese Kohaku koi fish inside airtight crystal glass water sphere, glowing cyan bubbles, brass fittings",
    },
    {
        "filename": "char_03_sir_longneck_giraffe.png",
        "name": "SIR LONGNECK (THE GROOM)",
        "role": "Towering Savanna Aristocrat",
        "color": (160, 110, 40),
        "accent": (255, 255, 255),
        "dna": "16-foot African giraffe in custom midnight-black velvet tuxedo with silk bowtie, wet spotted coat.",
        "anchor": "Tall savannah giraffe in elegant black velvet tuxedo and silk bowtie, rain-slicked Gotham alleyway",
    },
    {
        "filename": "char_04_the_mystery_cat.png",
        "name": "THE MYSTERY CAT (MASTERMIND)",
        "role": "Elusive Feline Phantom",
        "color": (25, 25, 30),
        "accent": (255, 180, 0),
        "dna": "Sleek tuxedo cat with glowing amber eyes, tilted miniature fedora, tiny trench coat, brass key in jaws.",
        "anchor": "Sleek tuxedo cat with glowing amber eyes wearing miniature fedora and tiny trenchcoat, perched on gargoyle",
    },
    {
        "filename": "char_05_alfred_pennyworth.png",
        "name": "ALFRED PENNYWORTH",
        "role": "Sardonic Butler & Comms",
        "color": (50, 55, 65),
        "accent": (200, 200, 210),
        "dna": "Elderly British gentleman in bespoke charcoal three-piece wool suit, silver-rimmed spectacles, deadpan cadence.",
        "anchor": "Alfred Pennyworth in tailored charcoal suit and spectacles in high-tech Batcave, glowing holographic displays",
    },
]

OBJECT_ASSET_SPECS = [
    {
        "filename": "obj_01_submerged_gold_wedding_ring.png",
        "name": "SUBMERGED GOLDEN WEDDING RING",
        "category": "Sacred Marital Relic",
        "color": (180, 140, 20),
        "accent": (255, 225, 100),
        "location": "Submerged inside crystal goblet on Center Altar table",
        "visual_state": "Heavy 24k gold band submerged in mineral saline with micro-bubbles, caustic light refractions.",
    },
    {
        "filename": "obj_02_crystal_water_orb_pod.png",
        "name": "CRYSTAL WATER ORB & LIFE-SUPPORT POD",
        "category": "Aquatic Vehicle / Habitation",
        "color": (20, 80, 120),
        "accent": (0, 255, 240),
        "location": "Center Altar surface / Hand-carried by Sir Longneck",
        "visual_state": "Airtight reinforced quartz sphere filled with glowing cyan saline, brass seals, oxygen aerator.",
    },
    {
        "filename": "obj_03_velvet_tuxedo_bowtie.png",
        "name": "CUSTOM SAVANNA TUXEDO & SILK BOWTIE",
        "category": "Formal Marital Attire",
        "color": (20, 20, 25),
        "accent": (240, 240, 255),
        "location": "Worn around Sir Longneck's 8-foot neck circumference",
        "visual_state": "Midnight velvet fabric tailored to giraffe proportions, crisp white satin bowtie.",
    },
    {
        "filename": "obj_04_brass_maritime_key.png",
        "name": "ANTIQUE BRASS MARITIME KEY",
        "category": "Crime Syndicate Cipher & Tool",
        "color": (140, 100, 30),
        "accent": (255, 200, 50),
        "location": "Clutched tightly in The Mystery Cat's jaws",
        "visual_state": "Heavy weathered nautical skeleton key with anchor insignia, dripping with saltwater.",
    },
    {
        "filename": "obj_05_sea_kelp_acacia_altar.png",
        "name": "SEA KELP & SAVANNA ACACIA WEDDING ALTAR",
        "category": "Crime Scene Centerpiece",
        "color": (35, 70, 45),
        "accent": (180, 210, 80),
        "location": "Center Sanctuary Altar (Coordinate: 0.0, 0.0, 0.8)",
        "visual_state": "Ancient stone altar decorated with intertwined green sea kelp and dry golden acacia twigs.",
    },
]


def _get_font(size: int = 14) -> ImageFont.ImageFont:
    """Safely retrieves a clean TrueType font or falls back to PIL default."""
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\consola.ttf",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


# =====================================================================
# 1. NAMED CHARACTER ASSET GENERATOR
# =====================================================================

def generate_character_assets(output_dir: Optional[Path] = None) -> List[Path]:
    """Generates standard named PNG asset cards for all season characters."""
    target_dir = output_dir or (Path("assets") / "characters")
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_files: List[Path] = []

    f_title = _get_font(22)
    f_sub = _get_font(15)
    f_body = _get_font(12)
    f_code = _get_font(11)

    for spec in CHARACTER_ASSET_SPECS:
        file_path = target_dir / spec["filename"]
        img = Image.new("RGB", (800, 600), color=(14, 16, 20))
        draw = ImageDraw.Draw(img)

        # Background gradient & card border
        draw.rectangle([10, 10, 790, 590], outline=spec["accent"], width=2)
        draw.rectangle([15, 15, 785, 75], fill=(22, 26, 34))

        # Header clapperboard
        draw.text((30, 25), spec["name"], fill=spec["accent"], font=f_title)
        draw.text((30, 50), f"ROLE: {spec['role'].upper()}", fill=(180, 190, 205), font=f_sub)

        # Silhouette / Visual Symbol Box
        box_rect = [30, 95, 350, 415]
        draw.rectangle(box_rect, fill=spec["color"], outline=(60, 70, 85), width=2)
        
        # Draw distinctive visual silhouette shapes inside portrait box
        cx, cy = 190, 255
        if "batman" in spec["filename"]:
            # Batman cowl ears and emblem
            draw.polygon([(cx - 70, cy + 80), (cx, cy - 60), (cx + 70, cy + 80)], fill=(10, 12, 16))
            draw.polygon([(cx - 45, cy - 60), (cx - 30, cy - 120), (cx - 15, cy - 50)], fill=(10, 12, 16))
            draw.polygon([(cx + 15, cy - 50), (cx + 30, cy - 120), (cx + 45, cy - 60)], fill=(10, 12, 16))
            # Glowing white slits
            draw.polygon([(cx - 35, cy - 25), (cx - 10, cy - 20), (cx - 20, cy - 15)], fill=(255, 255, 255))
            draw.polygon([(cx + 35, cy - 25), (cx + 10, cy - 20), (cx + 20, cy - 15)], fill=(255, 255, 255))
        elif "koi" in spec["filename"]:
            # Koi fish oval body and tail fin
            draw.ellipse([cx - 80, cy - 40, cx + 50, cy + 40], fill=(240, 80, 40))
            draw.ellipse([cx - 40, cy - 30, cx + 20, cy + 20], fill=(255, 255, 255))
            draw.polygon([(cx + 40, cy), (cx + 100, cy - 40), (cx + 100, cy + 40)], fill=(240, 80, 40))
            # Glass orb circle outline
            draw.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], outline=(0, 220, 255), width=4)
        elif "giraffe" in spec["filename"]:
            # Long neck rectangle and head
            draw.rectangle([cx - 20, cy - 90, cx + 20, cy + 110], fill=(190, 140, 60))
            draw.ellipse([cx - 40, cy - 120, cx + 20, cy - 80], fill=(190, 140, 60))
            # Tuxedo black collar & white bowtie
            draw.rectangle([cx - 35, cy + 40, cx + 35, cy + 120], fill=(15, 15, 20))
            draw.polygon([(cx - 25, cy + 45), (cx + 25, cy + 45), (cx, cy + 60)], fill=(255, 255, 255))
        elif "cat" in spec["filename"]:
            # Cat head, ears, miniature fedora
            draw.ellipse([cx - 50, cy - 30, cx + 50, cy + 50], fill=(15, 15, 20))
            draw.polygon([(cx - 45, cy - 20), (cx - 30, cy - 70), (cx - 10, cy - 30)], fill=(15, 15, 20))
            draw.polygon([(cx + 45, cy - 20), (cx + 30, cy - 70), (cx + 10, cy - 30)], fill=(15, 15, 20))
            # Fedora hat brim and crown
            draw.rectangle([cx - 45, cy - 55, cx + 30, cy - 40], fill=(50, 50, 55))
            draw.rectangle([cx - 35, cy - 85, cx + 20, cy - 55], fill=(40, 40, 45))
            # Amber eyes
            draw.ellipse([cx - 25, cy - 5, cx - 10, cy + 10], fill=(255, 180, 0))
            draw.ellipse([cx + 10, cy - 5, cx + 25, cy + 10], fill=(255, 180, 0))
            # Golden key in mouth
            draw.rectangle([cx - 10, cy + 30, cx + 50, cy + 40], fill=(255, 215, 0))
        else:
            # Alfred silhouette & spectacles
            draw.ellipse([cx - 40, cy - 80, cx + 40, cy], fill=(80, 85, 95))
            draw.rectangle([cx - 50, cy + 5, cx + 50, cy + 120], fill=(25, 30, 40))
            draw.ellipse([cx - 25, cy - 50, cx - 5, cy - 30], outline=(220, 220, 230), width=2)
            draw.ellipse([cx + 5, cy - 50, cx + 25, cy - 30], outline=(220, 220, 230), width=2)

        draw.text((box_rect[0] + 10, box_rect[3] - 25), "OFFICIAL CHARACTER ASSET DOSSIER", fill=(130, 140, 155), font=f_code)

        # Right Specification Box
        rx = 370
        draw.text((rx, 100), "WARDROBE & VISUAL DNA:", fill=spec["accent"], font=f_sub)
        # Word wrap DNA text
        dna_words = spec["dna"].split()
        line = ""
        y_dna = 125
        for w in dna_words:
            if len(line + " " + w) > 42:
                draw.text((rx, y_dna), line, fill=(210, 220, 230), font=f_body)
                y_dna += 20
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            draw.text((rx, y_dna), line, fill=(210, 220, 230), font=f_body)

        draw.text((rx, 220), "AI VISUAL PROMPT ANCHOR (IMMUTABLE):", fill=spec["accent"], font=f_sub)
        anchor_words = spec["anchor"].split()
        line = ""
        y_anc = 245
        for w in anchor_words:
            if len(line + " " + w) > 42:
                draw.text((rx, y_anc), line, fill=(160, 230, 175), font=f_code)
                y_anc += 18
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            draw.text((rx, y_anc), line, fill=(160, 230, 175), font=f_code)

        # Bottom Verification Strip
        draw.rectangle([30, 435, 770, 570], fill=(18, 22, 28), outline=(40, 48, 60))
        draw.text((45, 445), "SPATIAL CONTINUITY INSTRUCTIONS:", fill=spec["accent"], font=f_sub)
        draw.text((45, 470), "1. Character physical scale and wardrobe assets must remain locked across camera cuts.", fill=(180, 190, 205), font=f_body)
        draw.text((45, 492), "2. Eye-line vectors must adhere to the 180-degree line-of-action relative to other actors.", fill=(180, 190, 205), font=f_body)
        draw.text((45, 514), "3. Character stage coordinates MUST NOT jump across camera transitions without scripted motion.", fill=(180, 190, 205), font=f_body)
        draw.text((45, 540), f"FILENAME: {spec['filename']} | RESOLUTION: 800x600 | PALETTE: 35mm Cinema", fill=(110, 120, 135), font=f_code)

        img.save(file_path)
        generated_files.append(file_path)

    print(f"[MockupGen] [OK] Generated {len(generated_files)} named character assets in {target_dir}")
    return generated_files


# =====================================================================
# 2. NAMED SCENE OBJECT ASSET GENERATOR
# =====================================================================

def generate_object_assets(output_dir: Optional[Path] = None) -> List[Path]:
    """Generates standard named PNG asset cards for all tracked scene objects."""
    target_dir = output_dir or (Path("assets") / "objects")
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_files: List[Path] = []

    f_title = _get_font(20)
    f_sub = _get_font(14)
    f_body = _get_font(12)
    f_code = _get_font(11)

    for spec in OBJECT_ASSET_SPECS:
        file_path = target_dir / spec["filename"]
        img = Image.new("RGB", (800, 500), color=(14, 16, 20))
        draw = ImageDraw.Draw(img)

        # Card border
        draw.rectangle([10, 10, 790, 490], outline=spec["accent"], width=2)
        draw.rectangle([15, 15, 785, 70], fill=(22, 26, 34))

        draw.text((30, 22), spec["name"], fill=spec["accent"], font=f_title)
        draw.text((30, 48), f"CATEGORY: {spec['category'].upper()}", fill=(180, 190, 205), font=f_sub)

        # Object Illustration Box
        box = [30, 85, 320, 360]
        draw.rectangle(box, fill=spec["color"], outline=(60, 70, 85), width=2)
        cx, cy = 175, 220

        if "ring" in spec["filename"]:
            # Gold wedding ring in water goblet
            draw.polygon([(cx - 50, cy - 70), (cx + 50, cy - 70), (cx + 25, cy + 20), (cx - 25, cy + 20)], outline=(120, 200, 255), width=3)
            draw.line([(cx, cy + 20), (cx, cy + 70)], fill=(120, 200, 255), width=4)
            draw.ellipse([cx - 35, cy + 65, cx + 35, cy + 75], outline=(120, 200, 255), width=3)
            draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 15], outline=(255, 215, 0), width=6)
        elif "pod" in spec["filename"]:
            # Crystal sphere with water and koi
            draw.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], outline=(0, 240, 255), width=4)
            draw.ellipse([cx - 40, cy - 20, cx + 40, cy + 20], fill=(255, 90, 40))
        elif "bowtie" in spec["filename"]:
            # Velvet bowtie
            draw.polygon([(cx - 60, cy - 30), (cx - 10, cy), (cx - 60, cy + 30)], fill=(240, 240, 255))
            draw.polygon([(cx + 60, cy - 30), (cx + 10, cy), (cx + 60, cy + 30)], fill=(240, 240, 255))
            draw.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(20, 20, 25))
        elif "key" in spec["filename"]:
            # Brass maritime key
            draw.ellipse([cx - 50, cy - 20, cx - 10, cy + 20], outline=(255, 215, 0), width=6)
            draw.rectangle([cx - 15, cy - 6, cx + 60, cy + 6], fill=(255, 215, 0))
            draw.rectangle([cx + 35, cy + 6, cx + 45, cy + 25], fill=(255, 215, 0))
            draw.rectangle([cx + 50, cy + 6, cx + 60, cy + 30], fill=(255, 215, 0))
        else:
            # Altar stone with sea kelp & acacia twigs
            draw.rectangle([cx - 80, cy - 10, cx + 80, cy + 60], fill=(70, 75, 80))
            draw.arc([cx - 70, cy - 40, cx - 10, cy + 10], 0, 180, fill=(40, 180, 80), width=5)
            draw.line([(cx, cy - 50), (cx + 60, cy)], fill=(210, 180, 70), width=4)

        # Specifications Text
        rx = 345
        draw.text((rx, 90), "STAGE LOCATION & SURFACE ANCHOR:", fill=spec["accent"], font=f_sub)
        draw.text((rx, 115), spec["location"], fill=(210, 220, 235), font=f_body)

        draw.text((rx, 160), "VISUAL STATE & MATERIAL TEXTURE:", fill=spec["accent"], font=f_sub)
        state_words = spec["visual_state"].split()
        line = ""
        y_st = 185
        for w in state_words:
            if len(line + " " + w) > 44:
                draw.text((rx, y_st), line, fill=(180, 195, 210), font=f_body)
                y_st += 20
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            draw.text((rx, y_st), line, fill=(180, 195, 210), font=f_body)

        # Bottom info
        draw.rectangle([30, 380, 770, 475], fill=(18, 22, 28), outline=(40, 48, 60))
        draw.text((45, 390), "OBJECT TRACKING & ANTI-DISPLACEMENT LOCK:", fill=spec["accent"], font=f_sub)
        draw.text((45, 415), "* Object coordinates are permanently bound to the scene coordinate matrix.", fill=(180, 190, 205), font=f_body)
        draw.text((45, 435), "* When the camera pans or cuts, this object MUST NOT spontaneously move or vanish.", fill=(180, 190, 205), font=f_body)
        draw.text((45, 455), f"ASSET FILE: {spec['filename']} | CONTINUITY PROTOCOL: LOCKED", fill=(110, 120, 135), font=f_code)

        img.save(file_path)
        generated_files.append(file_path)

    print(f"[MockupGen] [OK] Generated {len(generated_files)} named object assets in {target_dir}")
    return generated_files


# =====================================================================
# 3. SPATIAL STAGE MAP & BLOCKING RENDERER (TOP-DOWN 2D)
# =====================================================================

def draw_spatial_stage_map(scene: Scene, width: int = 560, height: int = 340) -> Image.Image:
    """Renders a top-down architectural blocking diagram showing characters, objects, camera cone, and 180° axis."""
    img = Image.new("RGB", (width, height), color=(16, 20, 26))
    draw = ImageDraw.Draw(img)
    f_label = _get_font(10)
    f_axis = _get_font(9)

    # 1. Outer boundary & grid lines
    margin = 30
    gw = width - 2 * margin
    gh = height - 2 * margin
    cx = margin + gw // 2
    cy = margin + gh // 2

    draw.rectangle([margin, margin, margin + gw, margin + gh], outline=(45, 55, 70), width=1)
    # Stage axis lines
    draw.line([(cx, margin), (cx, margin + gh)], fill=(30, 38, 50), width=1)
    draw.line([(margin, cy), (margin + gw, cy)], fill=(30, 38, 50), width=1)

    # Compass / Stage markers
    draw.text((cx - 35, margin + 4), "UPSTAGE (BG)", fill=(110, 120, 135), font=f_axis)
    draw.text((cx - 45, margin + gh - 14), "DOWNSTAGE (FG)", fill=(110, 120, 135), font=f_axis)
    draw.text((margin + 4, cy - 6), "STAGE LEFT", fill=(110, 120, 135), font=f_axis)
    draw.text((margin + gw - 65, cy - 6), "STAGE RIGHT", fill=(110, 120, 135), font=f_axis)

    # 2. Stage Landmarks (Altar at center)
    altar_w, altar_h = 90, 45
    draw.rectangle([cx - altar_w // 2, cy - altar_h // 2, cx + altar_w // 2, cy + altar_h // 2], fill=(35, 42, 54), outline=(75, 85, 105), width=2)
    draw.text((cx - 32, cy - 6), "CENTER ALTAR", fill=(170, 185, 205), font=f_axis)

    # Helper coordinate mapper: x in [-1, 1], y in [-1, 1] (Downstage is -1, Upstage is +1)
    def map_coords(x: float, y: float) -> Tuple[int, int]:
        px = int(cx + x * (gw // 2 - 20))
        # Note: In stage blocking, Upstage (+Y) is towards top of screen, Downstage (-Y) is towards bottom
        py = int(cy - y * (gh // 2 - 20))
        return (px, py)

    # 3. Draw 180-Degree Action Axis (Prominent dotted/dashed gold line)
    axis_y = cy + 15
    for dash_x in range(margin, margin + gw, 16):
        draw.line([(dash_x, axis_y), (dash_x + 8, axis_y)], fill=(255, 80, 80), width=2)
    draw.text((margin + 10, axis_y - 12), "180° ACTION AXIS LINE (DO NOT CROSS)", fill=(255, 110, 110), font=f_axis)

    # 4. Draw Camera Position & FOV Frustum Cone
    cam_x, cam_y = 0.25, -0.75
    if scene.camera_blocking and scene.camera_blocking.camera_position:
        cam_x = scene.camera_blocking.camera_position.x
        cam_y = scene.camera_blocking.camera_position.y

    c_px, c_py = map_coords(cam_x, cam_y)

    # Draw camera frustum cone pointing towards center altar
    target_px, target_py = cx, cy
    angle_to_target = math.atan2(target_py - c_py, target_px - c_px)
    fov_half = math.radians(25)  # 50 deg FOV cone
    cone_dist = 110

    left_ray = (c_px + int(cone_dist * math.cos(angle_to_target - fov_half)), c_py + int(cone_dist * math.sin(angle_to_target - fov_half)))
    right_ray = (c_px + int(cone_dist * math.cos(angle_to_target + fov_half)), c_py + int(cone_dist * math.sin(angle_to_target + fov_half)))

    draw.polygon([(c_px, c_py), left_ray, right_ray], fill=(15, 45, 60))
    draw.line([(c_px, c_py), left_ray], fill=(0, 200, 240), width=1)
    draw.line([(c_px, c_py), right_ray], fill=(0, 200, 240), width=1)

    # Camera icon box
    draw.rectangle([c_px - 8, c_py - 8, c_px + 8, c_py + 8], fill=(0, 210, 255), outline=(255, 255, 255), width=1)
    draw.text((c_px - 26, c_py + 10), "CAM (180-DEG OK)", fill=(0, 230, 255), font=f_axis)

    # 5. Draw Characters
    char_palette = {
        "batman": ((40, 50, 70), (255, 215, 0)),
        "the_mystery_cat": ((25, 25, 30), (255, 180, 0)),
        "lady_guppy": ((200, 60, 40), (0, 240, 255)),
        "sir_longneck": ((160, 110, 40), (240, 240, 255)),
        "default": ((80, 90, 110), (200, 210, 225)),
    }

    if scene.character_blockings:
        for cb in scene.character_blockings:
            bx, by = map_coords(cb.position.x, cb.position.y)
            cid = cb.character_id.lower()
            fill_c, border_c = char_palette.get(cid, char_palette["default"])
            
            # Draw character node circle
            r = 10
            draw.ellipse([bx - r, by - r, bx + r, by + r], fill=fill_c, outline=border_c, width=2)

            # Draw directional facing pointer arrow
            angle_rad = math.radians(cb.facing_angle_deg)
            arrow_len = 16
            ax = bx + int(arrow_len * math.sin(angle_rad))
            ay = by + int(arrow_len * math.cos(angle_rad))
            draw.line([(bx, by), (ax, ay)], fill=border_c, width=2)

            # Character label
            draw.text((bx - 20, by - 22), cb.name[:12], fill=border_c, font=f_label)
    else:
        # Default character representation if none explicit
        bx, by = map_coords(-0.4, 0.1)
        draw.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=(25, 25, 30), outline=(255, 180, 0), width=2)
        draw.text((bx - 25, by - 20), "MYSTERY CAT", fill=(255, 180, 0), font=f_label)

    # 6. Draw Tracked Objects
    if scene.tracked_objects:
        for idx, ob in enumerate(scene.tracked_objects):
            ox, oy = map_coords(ob.position.x, ob.position.y)
            draw.rectangle([ox - 4, oy - 4, ox + 4, oy + 4], fill=(255, 215, 0), outline=(255, 255, 255))
            y_offset = -12 if idx % 2 == 0 else 6
            draw.text((ox + 8, oy + y_offset), ob.name[:16], fill=(255, 225, 120), font=f_axis)

    return img


# =====================================================================
# 4. STORYBOARD SHOT PRODUCTION CARD GENERATOR
# =====================================================================

def generate_scene_mockup_card(scene: Scene, episode_title: str, output_path: Path) -> Path:
    """Generates a cinema-grade 1280x720 storyboard card with 2D stage map, visual mockup, and continuity notes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    card_w, card_h = 1280, 720
    img = Image.new("RGB", (card_w, card_h), color=(14, 16, 22))
    draw = ImageDraw.Draw(img)

    f_title = _get_font(20)
    f_sub = _get_font(13)
    f_body = _get_font(10)
    f_code = _get_font(10)

    # Outer border
    draw.rectangle([10, 10, card_w - 10, card_h - 10], outline=(40, 50, 65), width=2)

    # 1. Header Clapperboard
    draw.rectangle([12, 12, card_w - 12, 70], fill=(20, 24, 32))
    draw.line([(12, 70), (card_w - 12, 70)], fill=(255, 215, 0), width=2)

    header_title = f"{episode_title.upper()} | SHOT {scene.scene_number:02d} ({scene.timecode_start} - {scene.timecode_end} | {scene.duration_seconds:.1f}s)"
    draw.text((25, 20), header_title, fill=(255, 215, 0), font=f_title)
    
    spec_summary = f"FRAMING: {scene.shot_type}  |  LENS: {scene.lens}  |  LIGHTING: {scene.lighting}  |  COLOR: {scene.color_science}"
    draw.text((25, 46), spec_summary, fill=(180, 195, 215), font=f_sub)

    # 2. Left Panel: Top-Down Spatial Stage Map (560 x 330)
    stage_map = draw_spatial_stage_map(scene, width=580, height=315)
    img.paste(stage_map, (25, 85))

    # Stage Map title banner
    draw.text((30, 88), "2D SPATIAL STAGE BLOCKING & 180-DEG ACTION AXIS", fill=(255, 215, 0), font=f_code)

    # 3. Right Panel: Visual Scene Mockup / Cinematography Render
    rx = 625
    ry = 85
    rw, rh = 625, 315
    draw.rectangle([rx, ry, rx + rw, ry + rh], fill=(22, 28, 38), outline=(60, 72, 90), width=1)

    # Render atmospheric cinema composition inside the right panel
    cx, cy = rx + rw // 2, ry + rh // 2
    draw.rectangle([rx + 2, ry + 2, rx + rw - 2, ry + rh - 2], fill=(12, 16, 24))
    
    # Gothic Cathedral arches and rain atmosphere
    draw.arc([cx - 180, cy - 120, cx - 40, cy + 120], 180, 360, fill=(40, 50, 70), width=3)
    draw.arc([cx + 40, cy - 120, cx + 180, cy + 120], 180, 360, fill=(40, 50, 70), width=3)
    draw.arc([cx - 70, cy - 150, cx + 70, cy + 90], 180, 360, fill=(60, 75, 100), width=4)

    # Neon reflection streaks
    draw.line([(cx - 150, cy + 90), (cx + 150, cy + 90)], fill=(0, 200, 240), width=2)
    draw.line([(cx - 80, cy + 110), (cx + 80, cy + 110)], fill=(255, 180, 0), width=2)

    # Mockup visual representation based on shot framing
    if "close" in scene.shot_type.lower() or "cu" in scene.shot_type.lower():
        # Close-up framing on mystery cat and goblet
        draw.ellipse([cx - 45, cy - 35, cx + 45, cy + 45], fill=(20, 22, 28), outline=(255, 180, 0), width=2)
        # Amber cat eyes
        draw.ellipse([cx - 20, cy - 10, cx - 8, cy + 5], fill=(255, 180, 0))
        draw.ellipse([cx + 8, cy - 10, cx + 20, cy + 5], fill=(255, 180, 0))
        # Goblet with gold ring
        draw.polygon([(cx + 60, cy - 20), (cx + 110, cy - 20), (cx + 85, cy + 40)], outline=(120, 220, 255), width=2)
        draw.ellipse([cx + 78, cy, cx + 92, cy + 20], outline=(255, 215, 0), width=4)
        draw.text((rx + 15, ry + 15), f"COMPOSITION: {scene.shot_type} - FOCAL PLANE ON CAT & GOBLET", fill=(255, 215, 0), font=f_code)
    else:
        # Wide / Medium framing showing cathedral altar and silhouettes
        draw.rectangle([cx - 60, cy + 30, cx + 60, cy + 85], fill=(45, 52, 65))
        draw.ellipse([cx - 20, cy + 10, cx + 20, cy + 50], outline=(0, 240, 255), width=3)
        draw.polygon([(cx + 90, cy + 20), (cx + 140, cy + 20), (cx + 115, cy - 40)], fill=(15, 20, 30))
        draw.text((rx + 15, ry + 15), f"COMPOSITION: {scene.shot_type} - FULL STAGE SPATIAL GEOMETRY", fill=(255, 215, 0), font=f_code)

    # 4. Bottom Panel: Continuity, Transitions, and Veo Prompt Box
    by = 415
    draw.rectangle([25, by, card_w - 25, card_h - 25], fill=(18, 22, 30), outline=(45, 55, 70), width=1)

    # Left Bottom: Continuity & 180-Degree Action Axis Rules
    draw.text((40, by + 10), "SPATIAL CONTINUITY & CAMERA TRANSITION RULES:", fill=(255, 215, 0), font=f_sub)

    # Vertical column separator
    draw.line([(620, by + 8), (620, card_h - 30)], fill=(45, 55, 70), width=1)

    def draw_wrapped_bullet(prefix: str, text: str, start_y: int, max_c: int = 70, fill: Tuple[int, int, int] = (180, 195, 215), max_lines: int = 2) -> int:
        full_text = f"{prefix} {text}"
        words = full_text.split()
        cur_line = ""
        cur_y = start_y
        lines_drawn = 0
        for w in words:
            if len(cur_line + " " + w) > max_c:
                draw.text((40, cur_y), cur_line, fill=fill, font=f_body)
                cur_y += 13
                lines_drawn += 1
                cur_line = "  " + w
                if lines_drawn >= max_lines:
                    break
            else:
                cur_line = f"{cur_line} {w}".strip()
        if cur_line and lines_drawn < max_lines:
            draw.text((40, cur_y), cur_line, fill=fill, font=f_body)
            cur_y += 13
        return cur_y

    cy_left = by + 30
    cy_left = draw_wrapped_bullet("* STAGE:", scene.stage_environment, cy_left, max_c=70, fill=(180, 195, 215), max_lines=2)
    
    char_summary = scene.get_spatial_summary() or "Batman on gargoyle Stage-Right; Mystery Cat on table Stage-Left; Lady Guppy at Center Altar."
    cy_left = draw_wrapped_bullet("* BLOCKING:", char_summary, cy_left, max_c=70, fill=(180, 195, 215), max_lines=2)

    obj_summary = scene.get_object_summary() or "Golden wedding ring submerged inside crystal goblet on Center Altar."
    cy_left = draw_wrapped_bullet("* OBJECTS:", obj_summary, cy_left, max_c=70, fill=(180, 195, 215), max_lines=2)

    axis_summary = scene.get_camera_axis_summary() or "180-degree axis locked on Altar-to-Nave line; camera remains strictly on East quadrant."
    cy_left = draw_wrapped_bullet("* 180-DEG AXIS:", axis_summary, cy_left, max_c=70, fill=(255, 130, 130), max_lines=2)

    trans_notes = scene.spatial_transition.spatial_carryover_notes if scene.spatial_transition else "Cut preserves left-to-right eye-line alignment."
    draw_wrapped_bullet("* TRANSITION:", trans_notes, cy_left, max_c=70, fill=(140, 230, 160), max_lines=2)

    # Right Bottom: Full Veo Visual Prompt Text
    px = 640
    draw.text((px, by + 10), "VEO / FLOW GENERATION PROMPT:", fill=(255, 215, 0), font=f_sub)
    
    prompt_words = scene.visual_prompt.split()
    p_line = ""
    py = by + 30
    for w in prompt_words:
        if len(p_line + " " + w) > 70:
            draw.text((px, py), p_line, fill=(200, 215, 230), font=f_code)
            py += 13
            p_line = w
            if py > card_h - 35:
                break
        else:
            p_line = f"{p_line} {w}".strip()
    if p_line and py <= card_h - 35:
        draw.text((px, py), p_line, fill=(200, 215, 230), font=f_code)

    img.save(output_path)
    return output_path


# =====================================================================
# 5. STORYBOARD MOCKUP BATCH SUITE
# =====================================================================

def generate_storyboard_mockups(storyboard: Storyboard, output_dir: Optional[Path] = None) -> List[Path]:
    """Generates complete visual storyboard mockup cards for every shot in a Storyboard."""
    target_dir = output_dir or (Path("mockups") / storyboard.project_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    generated_cards: List[Path] = []

    print(f"[MockupGen] Generating {len(storyboard.scenes)} production mockup cards for '{storyboard.title}'...")
    for scene in storyboard.scenes:
        slug = scene.title.lower().replace(" ", "_").replace(":", "").replace("/", "_")[:28]
        filename = f"shot_{scene.scene_number:02d}_{slug}_mockup.png"
        out_file = target_dir / filename
        generate_scene_mockup_card(scene=scene, episode_title=storyboard.title, output_path=out_file)
        generated_cards.append(out_file)

    print(f"[MockupGen] [OK] Generated {len(generated_cards)} storyboard mockup cards in {target_dir}")
    return generated_cards
