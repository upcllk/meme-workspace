"""
Polished 16-bit Pixel-Art Code Generator for "Super Naiwa Mario" (超级奶里奥).
Generates pixel-perfect sprites matching the confirmed concept:
- Red Mario cap with crisp green "N" emblem
- Bulging green round eyes, pure clean smiling mouth (no mustache)
- Yellow pear-shaped chubby body, big cream-white belly cutout
- Blue denim overalls with yellow buttons, white cartoon gloves, brown boots
"""

import numpy as np
from PIL import Image
from .palette import PALETTE

# Mario palette extension
MARIO_PALETTE = {
    **PALETTE,
    "CAP_RED": (228, 38, 48, 255),
    "CAP_RED_DARK": (155, 18, 28, 255),
    "CAP_RED_LIGHT": (255, 95, 105, 255),
    "EMBLEM_WHITE": (255, 255, 255, 255),
    "EMBLEM_GREEN": (40, 180, 50, 255),
    
    "OVERALL_BLUE": (36, 90, 215, 255),
    "OVERALL_BLUE_DARK": (18, 48, 130, 255),
    "OVERALL_BLUE_LIGHT": (80, 140, 250, 255),
    "BUTTON_YELLOW": (255, 225, 30, 255),
    
    "GLOVE_WHITE": (250, 252, 255, 255),
    "GLOVE_SHADOW": (180, 190, 210, 255),
    
    "BOOT_BROWN": (140, 70, 30, 255),
    "BOOT_BROWN_DARK": (85, 38, 15, 255),
}

def create_surf(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.uint8)

def p_rect(surf: np.ndarray, x: int, y: int, w: int, h: int, color_key: str):
    y1, y2 = max(0, y), min(surf.shape[0], y + h)
    x1, x2 = max(0, x), min(surf.shape[1], x + w)
    if y1 < y2 and x1 < x2:
        surf[y1:y2, x1:x2] = MARIO_PALETTE[color_key]

def p_dot(surf: np.ndarray, x: int, y: int, color_key: str):
    if 0 <= y < surf.shape[0] and 0 <= x < surf.shape[1]:
        surf[y, x] = MARIO_PALETTE[color_key]


class NaiwaMarioPixelArt:
    """Procedural generator for authentic 16-bit Super Naiwa Mario."""

    @classmethod
    def create_large_portrait(cls) -> np.ndarray:
        """High-definition 16-bit character portrait (160x170), transparent BG."""
        surf = create_surf(160, 170)
        cx, cy = 80, 85
        
        # 1. Yellow Pear Body (smooth curvy egg/pear shape)
        for y in range(-45, 60):
            prog = (y + 45) / 105.0
            cur_w = int(96 * (0.55 + 0.45 * np.sin(prog * np.pi * 0.9)))
            xs = cx - cur_w // 2
            p_rect(surf, xs - 2, cy + y, cur_w + 4, 1, "NAIWA_OUTLINE")
            p_rect(surf, xs, cy + y, cur_w, 1, "NAIWA_YELLOW_MID")
            # Left lighting & right shadow
            p_rect(surf, xs + 2, cy + y, cur_w // 4, 1, "NAIWA_YELLOW_LIGHT")
            p_rect(surf, xs + cur_w - cur_w // 5, cy + y, cur_w // 5, 1, "NAIWA_YELLOW_DARK")
            
        # 2. Cream-White Belly (round belly patch)
        for y in range(8, 54):
            prog = (y - 8) / 46.0
            cur_w = int(68 * np.sin(prog * np.pi * 0.95))
            if cur_w > 0:
                p_rect(surf, cx - cur_w // 2, cy + y, cur_w, 1, "NAIWA_BELLY_LIGHT")
                if prog > 0.65:
                    p_rect(surf, cx - cur_w // 2 + 2, cy + y, cur_w - 4, 1, "NAIWA_BELLY_SHADOW")
                    
        # 3. Denim Overalls
        # Lower pants
        p_rect(surf, cx - 44, cy + 36, 88, 25, "OVERALL_BLUE")
        p_rect(surf, cx - 44, cy + 36, 88, 2, "NAIWA_OUTLINE")
        # Straps (left and right framing the belly)
        p_rect(surf, cx - 34, cy - 2, 10, 40, "OVERALL_BLUE")
        p_rect(surf, cx + 24, cy - 2, 10, 40, "OVERALL_BLUE")
        p_rect(surf, cx - 35, cy - 2, 1, 40, "NAIWA_OUTLINE")
        p_rect(surf, cx - 24, cy - 2, 1, 40, "NAIWA_OUTLINE")
        p_rect(surf, cx + 23, cy - 2, 1, 40, "NAIWA_OUTLINE")
        p_rect(surf, cx + 34, cy - 2, 1, 40, "NAIWA_OUTLINE")
        
        # Yellow Buttons
        for bx in [cx - 30, cx + 28]:
            p_rect(surf, bx - 1, cy + 22, 6, 6, "NAIWA_OUTLINE")
            p_rect(surf, bx, cy + 23, 4, 4, "BUTTON_YELLOW")
            p_dot(surf, bx + 1, cy + 24, "NAIWA_WHITE")
            
        # 4. Bulging Green Eyes (smooth round circles)
        for ex in [cx - 22, cx + 22]:
            ey = cy - 20
            r = 13
            # Outline
            for dy in range(-r - 1, r + 2):
                for dx in range(-r - 1, r + 2):
                    if dx*dx + dy*dy <= (r + 1.3)**2:
                        p_dot(surf, ex + dx, ey + dy, "NAIWA_EYE_OUTLINE")
            # Green eyeball
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r**2:
                        p_dot(surf, ex + dx, ey + dy, "NAIWA_EYE_GREEN_MID")
            # Top-left highlight
            for dy in range(-r + 2, -r + 6):
                for dx in range(-r + 2, -r + 6):
                    p_dot(surf, ex + dx, ey + dy, "NAIWA_EYE_GREEN_LIGHT")
            # Pupil + catchlight
            p_rect(surf, ex - 1, ey - 2, 5, 5, "NAIWA_PUPIL")
            p_rect(surf, ex - 1, ey - 2, 2, 2, "NAIWA_WHITE")
            
        # 5. Clean smiling mouth (NO mustache)
        for i in range(12):
            my = cy - 2 + int(np.sin(i / 11.0 * np.pi) * 3)
            p_rect(surf, cx - 6 + i, my, 1, 2, "NAIWA_OUTLINE")
            
        # 6. Red Mario Cap with "N" Badge
        # Puffy dome
        for y in range(-42, -18):
            prog = (y + 42) / 24.0
            cw = int(82 * (0.8 + 0.35 * np.sin(prog * np.pi * 0.85)))
            xs = cx - cw // 2
            p_rect(surf, xs - 1, cy + y, cw + 2, 1, "NAIWA_OUTLINE")
            p_rect(surf, xs, cy + y, cw, 1, "CAP_RED")
            p_rect(surf, xs + 2, cy + y, cw // 4, 1, "CAP_RED_LIGHT")
            p_rect(surf, xs + cw - cw // 4, cy + y, cw // 4, 1, "CAP_RED_DARK")
            
        # Visor bill
        p_rect(surf, cx - 44, cy - 19, 88, 4, "CAP_RED_DARK")
        p_rect(surf, cx - 42, cy - 20, 84, 2, "CAP_RED")
        
        # White round badge
        badge_r = 10
        by = cy - 31
        for dy in range(-badge_r, badge_r + 1):
            for dx in range(-badge_r, badge_r + 1):
                if dx*dx + dy*dy <= badge_r**2:
                    p_dot(surf, cx + dx, by + dy, "EMBLEM_WHITE")
                elif dx*dx + dy*dy <= (badge_r + 1.2)**2:
                    p_dot(surf, cx + dx, by + dy, "NAIWA_OUTLINE")
                    
        # Green "N" letter
        p_rect(surf, cx - 5, by - 6, 3, 13, "EMBLEM_GREEN")
        p_rect(surf, cx + 3, by - 6, 3, 13, "EMBLEM_GREEN")
        p_rect(surf, cx - 2, by - 3, 2, 3, "EMBLEM_GREEN")
        p_rect(surf, cx, by - 1, 2, 3, "EMBLEM_GREEN")
        p_rect(surf, cx + 1, by + 1, 2, 3, "EMBLEM_GREEN")
        
        # 7. White Cartoon Gloves on hips
        for gx in [cx - 52, cx + 42]:
            p_rect(surf, gx - 1, cy + 18, 12, 16, "NAIWA_OUTLINE")
            p_rect(surf, gx, cy + 19, 10, 14, "GLOVE_WHITE")
            p_rect(surf, gx + 2, cy + 25, 6, 6, "GLOVE_SHADOW")
            
        # 8. Brown Work Boots
        p_rect(surf, cx - 40, cy + 61, 32, 14, "BOOT_BROWN")
        p_rect(surf, cx - 42, cy + 70, 36, 5, "BOOT_BROWN_DARK")
        p_rect(surf, cx + 8, cy + 61, 32, 14, "BOOT_BROWN")
        p_rect(surf, cx + 6, cy + 70, 36, 5, "BOOT_BROWN_DARK")
        
        return surf

    @classmethod
    def create_ingame_sprite(cls, action: str = "idle", frame_idx: int = 0) -> np.ndarray:
        """In-game 48x54 action sprites."""
        surf = create_surf(48, 54)
        cx, cy = 24, 25
        
        if action == "idle":
            bob = 0 if frame_idx % 2 == 0 else -1
            
            # Boots
            p_rect(surf, cx - 10, cy + 22 + bob, 8, 5, "BOOT_BROWN")
            p_rect(surf, cx + 2, cy + 22 + bob, 8, 5, "BOOT_BROWN")
            
            # Yellow Body
            for y in range(-12, 18):
                prog = (y + 12) / 30.0
                cur_w = int(24 * (0.65 + 0.35 * np.sin(prog * np.pi * 0.9)))
                xs = cx - cur_w // 2
                p_rect(surf, xs - 1, cy + y + bob, cur_w + 2, 1, "NAIWA_OUTLINE")
                p_rect(surf, xs, cy + y + bob, cur_w, 1, "NAIWA_YELLOW_MID")
                
            # Belly
            p_rect(surf, cx - 7, cy + 2 + bob, 14, 12, "NAIWA_BELLY_LIGHT")
            
            # Overalls
            p_rect(surf, cx - 10, cy + 12 + bob, 20, 8, "OVERALL_BLUE")
            p_rect(surf, cx - 8, cy + 2 + bob, 3, 11, "OVERALL_BLUE")
            p_rect(surf, cx + 5, cy + 2 + bob, 3, 11, "OVERALL_BLUE")
            p_dot(surf, cx - 7, cy + 9 + bob, "BUTTON_YELLOW")
            p_dot(surf, cx + 6, cy + 9 + bob, "BUTTON_YELLOW")
            
            # Green round eyes
            for ex in [cx - 6, cx + 6]:
                ey = cy - 8 + bob
                p_rect(surf, ex - 3, ey - 3, 7, 7, "NAIWA_EYE_OUTLINE")
                p_rect(surf, ex - 2, ey - 2, 5, 5, "NAIWA_EYE_GREEN_MID")
                p_rect(surf, ex, ey - 1, 2, 2, "NAIWA_PUPIL")
                p_dot(surf, ex, ey - 1, "NAIWA_WHITE")
                
            # Clean smiling mouth (NO mustache)
            p_rect(surf, cx - 2, cy - 2 + bob, 4, 1, "NAIWA_OUTLINE")
            
            # Red Cap
            p_rect(surf, cx - 11, cy - 19 + bob, 22, 9, "CAP_RED")
            p_rect(surf, cx - 12, cy - 19 + bob, 1, 9, "NAIWA_OUTLINE")
            p_rect(surf, cx + 11, cy - 19 + bob, 1, 9, "NAIWA_OUTLINE")
            p_rect(surf, cx - 10, cy - 20 + bob, 20, 1, "NAIWA_OUTLINE")
            p_rect(surf, cx - 13, cy - 11 + bob, 26, 2, "CAP_RED_DARK") # visor
            # White badge + Green N
            p_rect(surf, cx - 4, cy - 18 + bob, 8, 6, "EMBLEM_WHITE")
            p_dot(surf, cx - 2, cy - 17 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx - 2, cy - 16 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx - 2, cy - 15 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx - 1, cy - 16 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx, cy - 15 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx + 1, cy - 17 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx + 1, cy - 16 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx + 1, cy - 15 + bob, "EMBLEM_GREEN")
            
            # White gloves
            p_rect(surf, cx - 13, cy + 6 + bob, 4, 6, "GLOVE_WHITE")
            p_rect(surf, cx + 9, cy + 6 + bob, 4, 6, "GLOVE_WHITE")
            
        elif action == "run":
            phase = frame_idx % 3
            bob = -1 if phase == 1 else 0
            
            if phase == 0:
                p_rect(surf, cx - 13, cy + 20 + bob, 8, 5, "BOOT_BROWN")
                p_rect(surf, cx + 5, cy + 22 + bob, 8, 5, "BOOT_BROWN")
            elif phase == 1:
                p_rect(surf, cx - 7, cy + 22 + bob, 7, 5, "BOOT_BROWN")
                p_rect(surf, cx + 1, cy + 21 + bob, 7, 5, "BOOT_BROWN")
            else:
                p_rect(surf, cx - 5, cy + 22 + bob, 8, 5, "BOOT_BROWN")
                p_rect(surf, cx + 7, cy + 19 + bob, 8, 5, "BOOT_BROWN")
                
            for y in range(-12, 18):
                prog = (y + 12) / 30.0
                cur_w = int(24 * (0.65 + 0.35 * np.sin(prog * np.pi * 0.9)))
                xs = cx - cur_w // 2
                p_rect(surf, xs - 1, cy + y + bob, cur_w + 2, 1, "NAIWA_OUTLINE")
                p_rect(surf, xs, cy + y + bob, cur_w, 1, "NAIWA_YELLOW_MID")
                
            p_rect(surf, cx - 7, cy + 2 + bob, 14, 12, "NAIWA_BELLY_LIGHT")
            p_rect(surf, cx - 10, cy + 12 + bob, 20, 8, "OVERALL_BLUE")
            p_rect(surf, cx - 8, cy + 2 + bob, 3, 11, "OVERALL_BLUE")
            p_rect(surf, cx + 5, cy + 2 + bob, 3, 11, "OVERALL_BLUE")
            
            for ex in [cx - 6, cx + 6]:
                ey = cy - 8 + bob
                p_rect(surf, ex - 3, ey - 3, 7, 7, "NAIWA_EYE_OUTLINE")
                p_rect(surf, ex - 2, ey - 2, 5, 5, "NAIWA_EYE_GREEN_MID")
                p_rect(surf, ex, ey - 1, 2, 2, "NAIWA_PUPIL")
                p_dot(surf, ex, ey - 1, "NAIWA_WHITE")
                
            p_rect(surf, cx - 2, cy - 2 + bob, 4, 1, "NAIWA_OUTLINE")
            p_rect(surf, cx - 11, cy - 19 + bob, 22, 9, "CAP_RED")
            p_rect(surf, cx - 13, cy - 11 + bob, 26, 2, "CAP_RED_DARK")
            p_rect(surf, cx - 4, cy - 18 + bob, 8, 6, "EMBLEM_WHITE")
            p_dot(surf, cx - 2, cy - 17 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx - 2, cy - 15 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx + 1, cy - 17 + bob, "EMBLEM_GREEN")
            p_dot(surf, cx + 1, cy - 15 + bob, "EMBLEM_GREEN")
            
            if phase == 0:
                p_rect(surf, cx - 14, cy + 9 + bob, 5, 5, "GLOVE_WHITE")
                p_rect(surf, cx + 9, cy + 3 + bob, 5, 5, "GLOVE_WHITE")
            else:
                p_rect(surf, cx - 12, cy + 3 + bob, 5, 5, "GLOVE_WHITE")
                p_rect(surf, cx + 10, cy + 9 + bob, 5, 5, "GLOVE_WHITE")
                
        elif action == "jump":
            p_rect(surf, cx - 9, cy + 18, 7, 6, "BOOT_BROWN")
            p_rect(surf, cx + 2, cy + 20, 7, 5, "BOOT_BROWN")
            
            for y in range(-14, 16):
                prog = (y + 14) / 30.0
                cur_w = int(23 * (0.7 + 0.3 * np.sin(prog * np.pi * 0.9)))
                xs = cx - cur_w // 2
                p_rect(surf, xs - 1, cy + y, cur_w + 2, 1, "NAIWA_OUTLINE")
                p_rect(surf, xs, cy + y, cur_w, 1, "NAIWA_YELLOW_MID")
                
            p_rect(surf, cx - 6, cy, 14, 13, "NAIWA_BELLY_LIGHT")
            p_rect(surf, cx - 9, cy + 10, 18, 8, "OVERALL_BLUE")
            p_rect(surf, cx - 7, cy, 3, 11, "OVERALL_BLUE")
            p_rect(surf, cx + 4, cy, 3, 11, "OVERALL_BLUE")
            
            for ex in [cx - 6, cx + 6]:
                ey = cy - 10
                p_rect(surf, ex - 3, ey - 3, 7, 7, "NAIWA_EYE_OUTLINE")
                p_rect(surf, ex - 2, ey - 2, 5, 5, "NAIWA_EYE_GREEN_MID")
                p_rect(surf, ex, ey - 2, 2, 2, "NAIWA_PUPIL") # looking up
                
            p_rect(surf, cx - 2, cy - 3, 4, 3, "NAIWA_MOUTH_DARK")
            p_rect(surf, cx - 11, cy - 21, 22, 9, "CAP_RED")
            p_rect(surf, cx - 13, cy - 13, 26, 2, "CAP_RED_DARK")
            p_rect(surf, cx - 4, cy - 20, 8, 6, "EMBLEM_WHITE")
            
            # Fist punch in air
            p_rect(surf, cx + 9, cy - 21, 6, 6, "GLOVE_WHITE")
            p_rect(surf, cx + 8, cy - 15, 4, 11, "NAIWA_YELLOW_MID")
            p_rect(surf, cx - 14, cy + 3, 5, 5, "GLOVE_WHITE")
            
        elif action == "laugh":
            p_rect(surf, cx - 9, cy + 22, 8, 5, "BOOT_BROWN")
            p_rect(surf, cx + 2, cy + 22, 8, 5, "BOOT_BROWN")
            
            for y in range(-12, 18):
                prog = (y + 12) / 30.0
                cur_w = int(26 * (0.6 + 0.4 * np.sin(prog * np.pi * 0.9)))
                xs = cx - cur_w // 2
                p_rect(surf, xs - 1, cy + y, cur_w + 2, 1, "NAIWA_OUTLINE")
                p_rect(surf, xs, cy + y, cur_w, 1, "NAIWA_YELLOW_MID")
                
            p_rect(surf, cx - 8, cy + 3, 16, 13, "NAIWA_BELLY_LIGHT")
            p_rect(surf, cx - 10, cy + 13, 20, 8, "OVERALL_BLUE")
            
            # Laughing curved eyes (^_^)
            for ex in [cx - 6, cx + 6]:
                p_dot(surf, ex - 2, cy - 7, "NAIWA_OUTLINE")
                p_dot(surf, ex - 1, cy - 8, "NAIWA_OUTLINE")
                p_dot(surf, ex, cy - 8, "NAIWA_OUTLINE")
                p_dot(surf, ex + 1, cy - 7, "NAIWA_OUTLINE")
                
            p_rect(surf, cx - 3, cy - 4, 7, 5, "NAIWA_MOUTH_DARK")
            p_rect(surf, cx - 2, cy - 2, 5, 3, "NAIWA_TONGUE")
            
            p_rect(surf, cx - 11, cy - 19, 22, 9, "CAP_RED")
            p_rect(surf, cx - 13, cy - 11, 26, 2, "CAP_RED_DARK")
            p_rect(surf, cx - 4, cy - 18, 8, 6, "EMBLEM_WHITE")
            
            # White gloves clutching belly
            p_rect(surf, cx - 6, cy + 6, 5, 6, "GLOVE_WHITE")
            p_rect(surf, cx + 2, cy + 6, 5, 6, "GLOVE_WHITE")
            
        return surf


def generate_character_sheet(output_path: str):
    """Assembles a clean, presentation-ready 16-bit Super Naiwa Mario character sheet."""
    w, h = 640, 360
    sheet = np.full((h, w, 4), [20, 22, 32, 255], dtype=np.uint8)
    
    # Grid pattern for retro game feel
    for y in range(0, h, 16):
        sheet[y, :, :3] = (sheet[y, :, :3] * 0.9).astype(np.uint8)
    for x in range(0, w, 16):
        sheet[:, x, :3] = (sheet[:, x, :3] * 0.9).astype(np.uint8)
        
    # Top Title Banner
    p_rect(sheet, 20, 16, 600, 32, "OVERALL_BLUE_DARK")
    p_rect(sheet, 20, 16, 600, 2, "CAP_RED")
    p_rect(sheet, 20, 46, 600, 2, "CAP_RED")
    
    # 1. High-Res Portrait on left (Clean transparent blend)
    portrait = NaiwaMarioPixelArt.create_large_portrait()
    ph, pw = portrait.shape[:2]
    px_pos, py_pos = 45, 80
    
    # Portrait frame
    p_rect(sheet, px_pos - 8, py_pos - 8, pw + 16, ph + 16, "OVERALL_BLUE_DARK")
    p_rect(sheet, px_pos - 6, py_pos - 6, pw + 12, ph + 12, "ROAD_DARK")
    
    alpha = portrait[:, :, 3] / 255.0
    for c in range(3):
        sheet[py_pos:py_pos+ph, px_pos:px_pos+pw, c] = (
            portrait[:, :, c] * alpha + sheet[py_pos:py_pos+ph, px_pos:px_pos+pw, c] * (1.0 - alpha)
        ).astype(np.uint8)
        
    # 2. In-game action sprites on right
    idle = NaiwaMarioPixelArt.create_ingame_sprite("idle")
    run1 = NaiwaMarioPixelArt.create_ingame_sprite("run", 0)
    run2 = NaiwaMarioPixelArt.create_ingame_sprite("run", 1)
    jump = NaiwaMarioPixelArt.create_ingame_sprite("jump")
    laugh = NaiwaMarioPixelArt.create_ingame_sprite("laugh")
    
    sprites_to_show = [
        (idle, 250, 95),
        (run1, 345, 95),
        (run2, 440, 95),
        (jump, 535, 90),
        (laugh, 390, 215),
    ]
    
    for spr, sx, sy in sprites_to_show:
        sh, sw = spr.shape[:2]
        p_rect(sheet, sx - 10, sy - 10, sw + 20, sh + 20, "OVERALL_BLUE_DARK")
        p_rect(sheet, sx - 8, sy - 8, sw + 16, sh + 16, "ROAD_DARK")
        
        alpha = spr[:, :, 3] / 255.0
        for c in range(3):
            sheet[sy:sy+sh, sx:sx+sw, c] = (
                spr[:, :, c] * alpha + sheet[sy:sy+sh, sx:sx+sw, c] * (1.0 - alpha)
            ).astype(np.uint8)
            
    # Nearest-Neighbor 2x integer upscale to 1280x720
    img = Image.fromarray(sheet, mode="RGBA")
    img_2x = img.resize((w * 2, h * 2), Image.NEAREST)
    img_2x.save(output_path)
    print(f"[Pixel Sheet Updated] Saved to: {output_path}")


if __name__ == "__main__":
    generate_character_sheet("/Users/xu.liu9/projects/fun/meme-workspace/naiwa_mario_pixel_preview.png")
