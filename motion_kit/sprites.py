"""
Naiwa 16-bit Pixel Art Sprites Generator.
Supports:
- Walking Cycle (4-frame loop)
- Sudden Stop Frame
- Idle / Breathing Frame
- Side-Eye Suspicious Frame
- Laughing / Holding Belly Cycle (4-frame loop)
- Close-Up Face / Bust Sprites for Scene Cuts
"""

from typing import Dict, List, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .palette import PALETTE

def create_rgba_surface(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.uint8)

def draw_pixel(surf: np.ndarray, x: int, y: int, color_key: str):
    if 0 <= y < surf.shape[0] and 0 <= x < surf.shape[1]:
        surf[y, x] = PALETTE[color_key]

def draw_rect(surf: np.ndarray, x: int, y: int, w: int, h: int, color_key: str):
    y1, y2 = max(0, y), min(surf.shape[0], y + h)
    x1, x2 = max(0, x), min(surf.shape[1], x + w)
    if y1 < y2 and x1 < x2:
        surf[y1:y2, x1:x2] = PALETTE[color_key]

def blend_surface(dest: np.ndarray, src: np.ndarray, x: int, y: int):
    """Alpha blends src surface onto dest at (x, y)."""
    h, w = src.shape[:2]
    dh, dw = dest.shape[:2]
    
    x1_dest, y1_dest = max(0, x), max(0, y)
    x2_dest, y2_dest = min(dw, x + w), min(dh, y + h)
    
    if x1_dest >= x2_dest or y1_dest >= y2_dest:
        return
        
    x1_src, y1_src = x1_dest - x, y1_dest - y
    x2_src, y2_src = x1_src + (x2_dest - x1_dest), y1_src + (y2_dest - y1_dest)
    
    src_crop = src[y1_src:y2_src, x1_src:x2_src]
    dest_crop = dest[y1_dest:y2_dest, x1_dest:x2_dest]
    
    alpha_src = src_crop[:, :, 3].astype(np.float32) / 255.0
    alpha_dest = dest_crop[:, :, 3].astype(np.float32) / 255.0
    
    out_alpha = alpha_src + alpha_dest * (1.0 - alpha_src)
    mask = out_alpha > 0.001
    
    for c in range(3):
        color_src = src_crop[:, :, c].astype(np.float32)
        color_dest = dest_crop[:, :, c].astype(np.float32)
        out_color = np.zeros_like(color_src)
        out_color[mask] = (color_src[mask] * alpha_src[mask] + color_dest[mask] * alpha_dest[mask] * (1.0 - alpha_src[mask])) / out_alpha[mask]
        dest_crop[:, :, c] = np.clip(out_color, 0, 255).astype(np.uint8)
        
    dest_crop[:, :, 3] = np.clip(out_alpha * 255.0, 0, 255).astype(np.uint8)


class NaiwaSpriteFactory:
    """Generates authentic 16-bit sprites for Naiwa the Yellow Frog."""
    
    @staticmethod
    def draw_naiwa_body(surf: np.ndarray, cx: int, cy: int, w: int, h: int, crouch: int = 0):
        """Draws pear-shaped yellow body with outline and shading."""
        # Main pear body
        for y in range(h):
            prog = y / float(h)
            # pear shape: narrower at top (0.5), wider at bottom (1.0)
            cur_w = int(w * (0.45 + 0.55 * np.sin(prog * np.pi * 0.85)))
            x_start = cx - cur_w // 2
            
            # outline
            draw_rect(surf, x_start - 1, cy + y + crouch, cur_w + 2, 1, "NAIWA_OUTLINE")
            # main yellow
            draw_rect(surf, x_start, cy + y + crouch, cur_w, 1, "NAIWA_YELLOW_MID")
            # left highlight
            hl_w = max(1, cur_w // 4)
            draw_rect(surf, x_start + 1, cy + y + crouch, hl_w, 1, "NAIWA_YELLOW_LIGHT")
            # bottom/right shadow
            if prog > 0.6:
                sh_w = max(1, cur_w // 4)
                draw_rect(surf, x_start + cur_w - sh_w, cy + y + crouch, sh_w, 1, "NAIWA_YELLOW_DARK")

    @staticmethod
    def draw_naiwa_belly(surf: np.ndarray, cx: int, cy: int, bw: int, bh: int, offset_x: int = 0):
        """Draws cream-white oval belly patch."""
        for y in range(bh):
            prog = y / float(bh)
            cur_w = int(bw * np.sin(prog * np.pi))
            if cur_w > 0:
                x_start = cx + offset_x - cur_w // 2
                draw_rect(surf, x_start, cy + y, cur_w, 1, "NAIWA_BELLY_LIGHT")
                # bottom shadow for belly
                if prog > 0.7:
                    draw_rect(surf, x_start + 1, cy + y, cur_w - 2, 1, "NAIWA_BELLY_SHADOW")

    @staticmethod
    def draw_naiwa_eyes(surf: np.ndarray, cx: int, cy: int, eye_r: int = 4, pupil_dir: str = "forward"):
        """Draws prominent bulging green round eyes with dark green rim and black pupil."""
        left_ex = cx - 7
        right_ex = cx + 7
        ey = cy
        
        for ex in [left_ex, right_ex]:
            # Outline
            for dy in range(-eye_r - 1, eye_r + 2):
                for dx in range(-eye_r - 1, eye_r + 2):
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= (eye_r + 1.2)**2:
                        draw_pixel(surf, ex + dx, ey + dy, "NAIWA_EYE_OUTLINE")
            # Green eyeball
            for dy in range(-eye_r, eye_r + 1):
                for dx in range(-eye_r, eye_r + 1):
                    dist_sq = dx*dx + dy*dy
                    if dist_sq <= eye_r**2:
                        draw_pixel(surf, ex + dx, ey + dy, "NAIWA_EYE_GREEN_MID")
            # Green highlight (top left)
            draw_pixel(surf, ex - 1, ey - 2, "NAIWA_EYE_GREEN_LIGHT")
            draw_pixel(surf, ex - 2, ey - 1, "NAIWA_EYE_GREEN_LIGHT")
            
            # Pupil placement
            px, py = ex, ey
            if pupil_dir == "forward":
                px, py = ex + 1, ey
            elif pupil_dir == "side_right": # Side-eye to the right
                px, py = ex + 2, ey
            elif pupil_dir == "side_left":
                px, py = ex - 2, ey
            elif pupil_dir == "down":
                px, py = ex + 1, ey + 2
                
            draw_rect(surf, px - 1, py - 1, 2, 2, "NAIWA_PUPIL")
            # Catchlight
            draw_pixel(surf, px - 1, py - 1, "NAIWA_WHITE")

    @staticmethod
    def draw_squint_eyes(surf: np.ndarray, cx: int, cy: int):
        """Draws laughing squinted eyes (^_^ / curved happy arcs)."""
        for ex in [cx - 7, cx + 7]:
            draw_pixel(surf, ex - 3, cy + 1, "NAIWA_EYE_OUTLINE")
            draw_pixel(surf, ex - 2, cy, "NAIWA_EYE_OUTLINE")
            draw_pixel(surf, ex - 1, cy - 1, "NAIWA_EYE_OUTLINE")
            draw_pixel(surf, ex, cy - 1, "NAIWA_EYE_OUTLINE")
            draw_pixel(surf, ex + 1, cy, "NAIWA_EYE_OUTLINE")
            draw_pixel(surf, ex + 2, cy + 1, "NAIWA_EYE_OUTLINE")
            
            # green surrounding eyelid
            draw_pixel(surf, ex - 1, cy - 2, "NAIWA_EYE_GREEN_MID")
            draw_pixel(surf, ex, cy - 2, "NAIWA_EYE_GREEN_MID")

    @classmethod
    def create_walk_frame(cls, frame_idx: int) -> np.ndarray:
        """4-frame walking cycle."""
        surf = create_rgba_surface(48, 52)
        cx, cy = 24, 16
        
        # Bobbing
        bob = 0 if frame_idx % 2 == 0 else -1
        
        # Dark grey legs / feet positions
        # frame 0: right leg forward, left leg back
        # frame 1: passing stance
        # frame 2: left leg forward, right leg back
        # frame 3: passing stance
        leg_phase = frame_idx % 4
        if leg_phase == 0:
            l_foot_x, l_foot_y = cx - 8, cy + 30 + bob
            r_foot_x, r_foot_y = cx + 8, cy + 30 + bob
            l_arm_y, r_arm_y = cy + 18, cy + 14
        elif leg_phase == 1:
            l_foot_x, l_foot_y = cx - 4, cy + 29 + bob
            r_foot_x, r_foot_y = cx + 4, cy + 31 + bob
            l_arm_y, r_arm_y = cy + 16, cy + 16
        elif leg_phase == 2:
            l_foot_x, l_foot_y = cx - 2, cy + 30 + bob
            r_foot_x, r_foot_y = cx + 6, cy + 30 + bob
            l_arm_y, r_arm_y = cy + 14, cy + 18
        else:
            l_foot_x, l_foot_y = cx - 4, cy + 31 + bob
            r_foot_x, r_foot_y = cx + 4, cy + 29 + bob
            l_arm_y, r_arm_y = cy + 16, cy + 16
            
        # Draw feet (dark grey)
        draw_rect(surf, l_foot_x - 3, l_foot_y, 6, 3, "NAIWA_LIMB_DARK")
        draw_rect(surf, l_foot_x - 2, l_foot_y, 4, 1, "NAIWA_LIMB_LIGHT")
        draw_rect(surf, r_foot_x - 3, r_foot_y, 6, 3, "NAIWA_LIMB_DARK")
        draw_rect(surf, r_foot_x - 2, r_foot_y, 4, 1, "NAIWA_LIMB_LIGHT")
        
        # Draw Pear Body
        cls.draw_naiwa_body(surf, cx, cy + bob, 22, 28)
        # Belly
        cls.draw_naiwa_belly(surf, cx + 1, cy + 12 + bob, 14, 14)
        # Eyes
        cls.draw_naiwa_eyes(surf, cx, cy + 3 + bob, eye_r=4, pupil_dir="forward")
        
        # Subtle smiling mouth
        draw_pixel(surf, cx + 2, cy + 11 + bob, "NAIWA_OUTLINE")
        draw_pixel(surf, cx + 3, cy + 11 + bob, "NAIWA_OUTLINE")
        draw_pixel(surf, cx + 4, cy + 10 + bob, "NAIWA_OUTLINE")
        
        # Dark grey arms swinging
        draw_rect(surf, cx - 11, l_arm_y + bob, 3, 8, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 9, r_arm_y + bob, 3, 8, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx - 12, l_arm_y + 6 + bob, 4, 3, "NAIWA_LIMB_DARK") # hand
        draw_rect(surf, cx + 9, r_arm_y + 6 + bob, 4, 3, "NAIWA_LIMB_DARK")
        
        return surf

    @classmethod
    def create_stop_frame(cls) -> np.ndarray:
        """Sudden stop pose: bracing feet, slightly leaning back."""
        surf = create_rgba_surface(48, 52)
        cx, cy = 24, 17
        
        # Sliding feet
        draw_rect(surf, cx - 10, cy + 29, 7, 3, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 5, cy + 29, 8, 3, "NAIWA_LIMB_DARK")
        
        # Body (slight crouch)
        cls.draw_naiwa_body(surf, cx - 2, cy, 23, 27)
        cls.draw_naiwa_belly(surf, cx - 1, cy + 11, 14, 14)
        
        # Wide alert eyes
        cls.draw_naiwa_eyes(surf, cx - 2, cy + 2, eye_r=4, pupil_dir="forward")
        
        # Little startled mouth "o"
        draw_rect(surf, cx, cy + 10, 2, 2, "NAIWA_MOUTH_DARK")
        
        # Arms thrown back in surprise
        draw_rect(surf, cx - 12, cy + 14, 3, 8, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx - 14, cy + 19, 4, 4, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 8, cy + 15, 3, 7, "NAIWA_LIMB_DARK")
        
        return surf

    @classmethod
    def create_side_eye_frame(cls, blink: bool = False) -> np.ndarray:
        """Standing with a comical, suspicious side-eye."""
        surf = create_rgba_surface(48, 52)
        cx, cy = 24, 16
        
        # Balanced standing feet
        draw_rect(surf, cx - 7, cy + 30, 6, 3, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 2, cy + 30, 6, 3, "NAIWA_LIMB_DARK")
        
        # Body
        cls.draw_naiwa_body(surf, cx, cy, 22, 28)
        cls.draw_naiwa_belly(surf, cx, cy + 12, 14, 14)
        
        # Eyes looking hard to the right (side-eye)
        if not blink:
            cls.draw_naiwa_eyes(surf, cx, cy + 3, eye_r=4, pupil_dir="side_right")
            # Slightly lowered upper eyelid for that suspicious look
            draw_rect(surf, cx - 10, cy - 1, 7, 2, "NAIWA_EYE_GREEN_DARK")
            draw_rect(surf, cx + 4, cy - 1, 7, 2, "NAIWA_EYE_GREEN_DARK")
        else:
            cls.draw_squint_eyes(surf, cx, cy + 3)
            
        # Smirking mouth to the side
        draw_pixel(surf, cx + 1, cy + 11, "NAIWA_OUTLINE")
        draw_pixel(surf, cx + 2, cy + 11, "NAIWA_OUTLINE")
        draw_pixel(surf, cx + 3, cy + 10, "NAIWA_OUTLINE")
        draw_pixel(surf, cx + 4, cy + 9, "NAIWA_OUTLINE")
        
        # Hands resting casually
        draw_rect(surf, cx - 9, cy + 17, 3, 7, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 7, cy + 17, 3, 7, "NAIWA_LIMB_DARK")
        
        return surf

    @classmethod
    def create_laugh_frame(cls, phase: int) -> np.ndarray:
        """Holding belly laughing animation cycle (4 phases).
        Phase 0: Tilted back, mouth wide open, hands touching belly.
        Phase 1: Bending forward, clutching belly tightly, eyes squinted shut.
        Phase 2: Shaking with laughter, belly expanded, tears flying.
        Phase 3: Bouncing rebound.
        """
        surf = create_rgba_surface(56, 56)
        cx, cy = 28, 18
        
        # Feet planted firmly
        draw_rect(surf, cx - 8, cy + 28, 6, 3, "NAIWA_LIMB_DARK")
        draw_rect(surf, cx + 3, cy + 28, 6, 3, "NAIWA_LIMB_DARK")
        
        if phase == 0:
            # Leaning back slightly, laughing out loud
            cls.draw_naiwa_body(surf, cx - 2, cy - 1, 23, 27)
            cls.draw_naiwa_belly(surf, cx, cy + 11, 15, 14)
            cls.draw_squint_eyes(surf, cx - 1, cy + 2)
            
            # Big open mouth laughing
            draw_rect(surf, cx - 1, cy + 8, 6, 4, "NAIWA_MOUTH_DARK")
            draw_rect(surf, cx, cy + 10, 4, 2, "NAIWA_TONGUE")
            
            # Hands holding side of belly
            draw_rect(surf, cx - 8, cy + 15, 4, 4, "NAIWA_LIMB_DARK")
            draw_rect(surf, cx + 5, cy + 15, 4, 4, "NAIWA_LIMB_DARK")
            
        elif phase == 1:
            # Bent forward, clutching belly
            cls.draw_naiwa_body(surf, cx, cy + 2, 25, 25) # squashed & bent
            cls.draw_naiwa_belly(surf, cx + 1, cy + 12, 16, 13)
            cls.draw_squint_eyes(surf, cx, cy + 5)
            
            # Grinning/shaking mouth
            draw_rect(surf, cx - 2, cy + 10, 7, 3, "NAIWA_MOUTH_DARK")
            draw_rect(surf, cx - 1, cy + 11, 5, 2, "NAIWA_TONGUE")
            
            # Hands clutching front belly
            draw_rect(surf, cx - 4, cy + 16, 4, 4, "NAIWA_LIMB_DARK")
            draw_rect(surf, cx + 2, cy + 16, 4, 4, "NAIWA_LIMB_DARK")
            
        elif phase == 2:
            # Belly shaking, tears popping out
            cls.draw_naiwa_body(surf, cx - 1, cy, 26, 26)
            cls.draw_naiwa_belly(surf, cx, cy + 11, 17, 14)
            cls.draw_squint_eyes(surf, cx, cy + 3)
            
            # Huge laugh mouth
            draw_rect(surf, cx - 2, cy + 9, 8, 5, "NAIWA_MOUTH_DARK")
            draw_rect(surf, cx - 1, cy + 11, 6, 3, "NAIWA_TONGUE")
            
            # Hands clutching belly
            draw_rect(surf, cx - 5, cy + 16, 4, 4, "NAIWA_LIMB_DARK")
            draw_rect(surf, cx + 3, cy + 16, 4, 4, "NAIWA_LIMB_DARK")
            
            # Laughter tear droplets flying
            draw_pixel(surf, cx - 9, cy + 2, "VFX_TEAR")
            draw_pixel(surf, cx - 10, cy + 1, "VFX_TEAR")
            draw_pixel(surf, cx + 10, cy + 2, "VFX_TEAR")
            draw_pixel(surf, cx + 11, cy + 1, "VFX_TEAR")
            
        else: # phase == 3
            # Rebound
            cls.draw_naiwa_body(surf, cx, cy - 1, 24, 27)
            cls.draw_naiwa_belly(surf, cx + 1, cy + 11, 15, 14)
            cls.draw_squint_eyes(surf, cx, cy + 2)
            
            draw_rect(surf, cx - 1, cy + 8, 6, 4, "NAIWA_MOUTH_DARK")
            draw_rect(surf, cx, cy + 10, 4, 2, "NAIWA_TONGUE")
            
            draw_rect(surf, cx - 6, cy + 15, 4, 4, "NAIWA_LIMB_DARK")
            draw_rect(surf, cx + 4, cy + 15, 4, 4, "NAIWA_LIMB_DARK")
            
        return surf

    @classmethod
    def create_closeup_face(cls, mood: str = "side_eye") -> np.ndarray:
        """High-resolution 16-bit bust (160x140) for dramatic cinematic cut-in."""
        surf = create_rgba_surface(160, 140)
        cx, cy = 80, 70
        
        # Big pear shape head/body
        for y in range(-55, 65):
            prog = (y + 55) / 120.0
            cur_w = int(110 * (0.65 + 0.35 * np.sin(prog * np.pi * 0.9)))
            x_start = cx - cur_w // 2
            
            draw_rect(surf, x_start - 2, cy + y, cur_w + 4, 1, "NAIWA_OUTLINE")
            draw_rect(surf, x_start, cy + y, cur_w, 1, "NAIWA_YELLOW_MID")
            # Highlight on left
            draw_rect(surf, x_start + 2, cy + y, cur_w // 4, 1, "NAIWA_YELLOW_LIGHT")
            # Shadow on right
            draw_rect(surf, x_start + cur_w - cur_w // 5, cy + y, cur_w // 5, 1, "NAIWA_YELLOW_DARK")
            
        # Large cream belly at bottom
        for y in range(15, 65):
            prog = (y - 15) / 50.0
            cur_w = int(76 * np.sin(prog * np.pi * 0.9))
            if cur_w > 0:
                draw_rect(surf, cx - cur_w // 2, cy + y, cur_w, 1, "NAIWA_BELLY_LIGHT")
                if prog > 0.6:
                    draw_rect(surf, cx - cur_w // 2 + 2, cy + y, cur_w - 4, 1, "NAIWA_BELLY_SHADOW")
                    
        if mood == "side_eye":
            # Bulging green eyes looking sharply to the side
            for ex in [cx - 28, cx + 28]:
                ey = cy - 22
                r = 16
                # Eye outline
                for dy in range(-r - 2, r + 3):
                    for dx in range(-r - 2, r + 3):
                        if dx*dx + dy*dy <= (r + 2)**2:
                            draw_pixel(surf, ex + dx, ey + dy, "NAIWA_EYE_OUTLINE")
                # Green sclera
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dx*dx + dy*dy <= r**2:
                            draw_pixel(surf, ex + dx, ey + dy, "NAIWA_EYE_GREEN_MID")
                # Highlight ring
                for dy in range(-r + 2, -r + 6):
                    for dx in range(-r + 2, -r + 6):
                        draw_pixel(surf, ex + dx, ey + dy, "NAIWA_EYE_GREEN_LIGHT")
                        
                # Dark pupils shifted all the way to the right
                px = ex + 7
                py = ey
                for dy in range(-6, 7):
                    for dx in range(-5, 6):
                        if dx*dx + dy*dy <= 30:
                            draw_pixel(surf, px + dx, py + dy, "NAIWA_PUPIL")
                # Specular white dot
                draw_rect(surf, px - 2, py - 3, 3, 3, "NAIWA_WHITE")
                
                # Heavy half-lidded eyelid (suspicious side-eye)
                draw_rect(surf, ex - r, ey - r, 2 * r + 1, 9, "NAIWA_EYE_GREEN_DARK")
                draw_rect(surf, ex - r, ey - r + 9, 2 * r + 1, 2, "NAIWA_OUTLINE")
                
            # Smirking side mouth
            for i in range(16):
                my = cy + 12 - int(np.sqrt(i) * 2)
                draw_rect(surf, cx + 4 + i, my, 2, 3, "NAIWA_OUTLINE")
                
        elif mood == "laugh":
            # Huge squinting laughing eyes
            for ex in [cx - 28, cx + 28]:
                ey = cy - 20
                for dx in range(-14, 15):
                    # curved arch
                    dy = int(-6 * np.cos(dx / 14.0 * np.pi / 2)) + 3
                    draw_rect(surf, ex + dx, ey + dy, 2, 4, "NAIWA_EYE_OUTLINE")
                    draw_rect(surf, ex + dx, ey + dy - 3, 2, 2, "NAIWA_EYE_GREEN_LIGHT")
                    
            # Giant open laughing mouth
            for y in range(0, 24):
                prog = y / 24.0
                cur_w = int(44 * np.sin(prog * np.pi * 0.9))
                if cur_w > 0:
                    draw_rect(surf, cx - cur_w // 2, cy + 6 + y, cur_w, 1, "NAIWA_MOUTH_DARK")
                    # Pink tongue at bottom
                    if y >= 12:
                        tw = int(cur_w * 0.75)
                        draw_rect(surf, cx - tw // 2, cy + 6 + y, tw, 1, "NAIWA_TONGUE")
                        
            # Big flying laughter tear gems
            draw_rect(surf, cx - 52, cy - 18, 6, 8, "VFX_TEAR")
            draw_rect(surf, cx + 48, cy - 18, 6, 8, "VFX_TEAR")
            
        return surf
