"""
16-bit Retro Color Palette and Pixel Graphics Primitives
Designed for SNES / 16-bit Arcade Aesthetics.
"""
from typing import Tuple, List, Dict
import numpy as np

# RGB Color definitions
PALETTE = {
    "TRANSPARENT": (0, 0, 0, 0),
    
    # Naiwa Frog Colors
    "NAIWA_OUTLINE": (60, 40, 10, 255),
    "NAIWA_YELLOW_DARK": (212, 139, 20, 255),
    "NAIWA_YELLOW_MID": (245, 197, 24, 255),
    "NAIWA_YELLOW_LIGHT": (255, 230, 109, 255),
    
    "NAIWA_BELLY_SHADOW": (216, 210, 194, 255),
    "NAIWA_BELLY_LIGHT": (254, 252, 243, 255),
    
    "NAIWA_EYE_OUTLINE": (20, 50, 30, 255),
    "NAIWA_EYE_GREEN_DARK": (35, 115, 60, 255),
    "NAIWA_EYE_GREEN_MID": (56, 176, 0, 255),
    "NAIWA_EYE_GREEN_LIGHT": (126, 217, 87, 255),
    "NAIWA_PUPIL": (18, 18, 22, 255),
    "NAIWA_WHITE": (255, 255, 255, 255),
    "NAIWA_MOUTH_DARK": (130, 30, 40, 255),
    "NAIWA_TONGUE": (255, 110, 140, 255),
    
    "NAIWA_LIMB_DARK": (36, 38, 46, 255),
    "NAIWA_LIMB_LIGHT": (70, 74, 88, 255),
    
    # City Night Scene Colors
    "SKY_TOP": (8, 8, 22, 255),
    "SKY_MID": (22, 18, 48, 255),
    "SKY_BOTTOM": (40, 30, 75, 255),
    
    "MOON_LIGHT": (255, 248, 220, 255),
    "MOON_SHADOW": (220, 205, 150, 255),
    
    "STAR_BRIGHT": (255, 255, 255, 255),
    "STAR_DIM": (160, 170, 220, 255),
    
    "BG_FAR_BLDG": (24, 25, 48, 255),
    "BG_FAR_BLDG_SHADOW": (16, 17, 34, 255),
    "WINDOW_YELLOW": (240, 200, 90, 255),
    "WINDOW_CYAN": (80, 220, 240, 255),
    "WINDOW_OFF": (35, 38, 65, 255),
    
    "MID_BLDG_BASE": (42, 30, 60, 255),
    "MID_BLDG_HIGHLIGHT": (62, 45, 85, 255),
    
    # Neon Signs
    "NEON_PINK": (255, 42, 133, 255),
    "NEON_CYAN": (0, 245, 212, 255),
    "NEON_YELLOW": (255, 230, 0, 255),
    "NEON_PURPLE": (157, 78, 221, 255),
    
    # Street & Foreground
    "ROAD_DARK": (24, 25, 32, 255),
    "ROAD_MID": (38, 40, 52, 255),
    "SIDEWALK_TOP": (65, 68, 85, 255),
    "SIDEWALK_SIDE": (45, 48, 62, 255),
    "SIDEWALK_LINE": (25, 27, 36, 255),
    
    "LAMPOST_METAL": (55, 60, 75, 255),
    "LAMPOST_HIGHLIGHT": (90, 98, 120, 255),
    "LAMP_LIGHT": (255, 240, 140, 255),
    "LAMP_GLOW": (255, 225, 100, 120),
    
    # VFX / UI
    "ALERT_RED": (240, 45, 55, 255),
    "ALERT_WHITE": (255, 255, 255, 255),
    "VFX_SWEAT": (100, 210, 255, 255),
    "VFX_TEAR": (120, 225, 255, 255),
    "TEXT_YELLOW": (255, 235, 60, 255),
    "TEXT_SHADOW": (20, 20, 30, 255),
}

def hex_to_rgba(hex_str: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (r, g, b, alpha)
