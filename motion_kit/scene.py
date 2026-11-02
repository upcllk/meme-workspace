"""
16-bit Retro Night City Scene with Multi-layer Parallax Scrolling.
"""

from typing import List, Tuple
import numpy as np
from .palette import PALETTE
from .sprites import create_rgba_surface, draw_rect, draw_pixel, blend_surface

class RetroCityScene:
    def __init__(self, width: int = 480, height: int = 270):
        self.w = width
        self.h = height
        
        # Pre-generate stars (x, y, brightness_seed, twinkle_speed)
        np.random.seed(42)
        self.stars = []
        for _ in range(70):
            sx = np.random.randint(0, width * 3)
            sy = np.random.randint(5, 110)
            spd = np.random.uniform(0.08, 0.25)
            self.stars.append((sx, sy, spd))
            
        # Pre-render static Far Skyline layer
        self.far_width = width * 4
        self.far_skyline = create_rgba_surface(self.far_width, height)
        self._build_far_skyline()
        
        # Pre-render Mid Neon District layer
        self.mid_width = width * 4
        self.mid_city = create_rgba_surface(self.mid_width, height)
        self._build_mid_city()
        
    def _build_far_skyline(self):
        """Builds silhouette skyscrapers with twinkling windows."""
        surf = self.far_skyline
        bx = 0
        np.random.seed(101)
        while bx < self.far_width:
            bw = np.random.randint(30, 65)
            bh = np.random.randint(70, 140)
            by = self.h - 55 - bh
            
            # building body
            draw_rect(surf, bx, by, bw, bh, "BG_FAR_BLDG")
            draw_rect(surf, bx, by, 2, bh, "BG_FAR_BLDG_SHADOW")
            
            # antenna on top
            if np.random.rand() > 0.5:
                ant_h = np.random.randint(10, 25)
                draw_rect(surf, bx + bw // 2, by - ant_h, 1, ant_h, "BG_FAR_BLDG")
                draw_pixel(surf, bx + bw // 2, by - ant_h, "ALERT_RED") # blinking beacon
                
            # tiny windows
            for wy in range(by + 8, self.h - 60, 8):
                for wx in range(bx + 4, bx + bw - 4, 6):
                    r = np.random.rand()
                    if r > 0.65:
                        color = "WINDOW_YELLOW" if r > 0.8 else "WINDOW_CYAN"
                        draw_rect(surf, wx, wy, 2, 3, color)
                    elif r > 0.4:
                        draw_rect(surf, wx, wy, 2, 3, "WINDOW_OFF")
            bx += bw + np.random.randint(4, 16)

    def _build_mid_city(self):
        """Builds midground buildings with retro arcade and diner signs."""
        surf = self.mid_city
        bx = 20
        np.random.seed(202)
        while bx < self.mid_width:
            bw = np.random.randint(55, 95)
            bh = np.random.randint(90, 160)
            by = self.h - 50 - bh
            
            # building wall
            draw_rect(surf, bx, by, bw, bh, "MID_BLDG_BASE")
            draw_rect(surf, bx + bw - 3, by, 3, bh, "MID_BLDG_HIGHLIGHT")
            
            # roof trim
            draw_rect(surf, bx - 2, by, bw + 4, 3, "MID_BLDG_HIGHLIGHT")
            
            # brick dither lines
            for ly in range(by + 10, self.h - 50, 12):
                for lx in range(bx, bx + bw, 4):
                    draw_pixel(surf, lx, ly, "MID_BLDG_HIGHLIGHT")
                    
            # Windows
            for wy in range(by + 14, self.h - 55, 14):
                for wx in range(bx + 6, bx + bw - 10, 12):
                    if np.random.rand() > 0.35:
                        draw_rect(surf, wx, wy, 6, 7, "WINDOW_YELLOW")
                        draw_rect(surf, wx + 1, wy + 1, 4, 5, "NAIWA_WHITE")
                    else:
                        draw_rect(surf, wx, wy, 6, 7, "WINDOW_OFF")
                        
            # Neon billboards on select rooftops
            if np.random.rand() > 0.4:
                sign_type = np.random.choice(["ARCADE", "NAIWA", "HOTEL", "NEON"])
                self._draw_neon_sign(surf, bx + 10, by - 26, sign_type)
                
            bx += bw + np.random.randint(15, 35)

    def _draw_neon_sign(self, surf: np.ndarray, x: int, y: int, text: str):
        # Scaffold posts
        draw_rect(surf, x + 4, y + 16, 2, 10, "LAMPOST_METAL")
        draw_rect(surf, x + 36, y + 16, 2, 10, "LAMPOST_METAL")
        # Sign board
        draw_rect(surf, x, y, 46, 16, "ROAD_DARK")
        draw_rect(surf, x, y, 46, 1, "NEON_PINK")
        draw_rect(surf, x, y + 15, 46, 1, "NEON_PINK")
        draw_rect(surf, x, y, 1, 16, "NEON_PINK")
        draw_rect(surf, x + 45, y, 1, 16, "NEON_PINK")
        
        # Stylized neon glyphs
        if text == "NAIWA":
            # Stylized glowing frog or letters
            draw_rect(surf, x + 6, y + 4, 8, 8, "NEON_YELLOW")
            draw_rect(surf, x + 18, y + 4, 8, 8, "NEON_CYAN")
            draw_rect(surf, x + 30, y + 4, 8, 8, "NEON_PINK")
        elif text == "ARCADE":
            draw_rect(surf, x + 4, y + 5, 38, 6, "NEON_CYAN")
            draw_rect(surf, x + 8, y + 7, 30, 2, "NAIWA_WHITE")
        else:
            draw_rect(surf, x + 5, y + 4, 36, 8, "NEON_PURPLE")

    def render_background(self, cam_x: int, frame_idx: int) -> np.ndarray:
        """Renders sky, moon, stars, and parallax buildings into a 480x270 frame."""
        frame = create_rgba_surface(self.w, self.h)
        
        # 1. Sky Gradient
        for y in range(self.h):
            prog = y / float(self.h)
            if prog < 0.4:
                t = prog / 0.4
                c1, c2 = np.array(PALETTE["SKY_TOP"][:3]), np.array(PALETTE["SKY_MID"][:3])
            else:
                t = (prog - 0.4) / 0.6
                c1, c2 = np.array(PALETTE["SKY_MID"][:3]), np.array(PALETTE["SKY_BOTTOM"][:3])
            col = (c1 * (1 - t) + c2 * t).astype(np.uint8)
            frame[y, :, 0:3] = col
            frame[y, :, 3] = 255
            
        # 2. Pixel Moon (fixed in sky, subtle drift)
        moon_x = 380 - int(cam_x * 0.02) % self.w
        moon_y = 42
        r = 18
        for dy in range(-r - 1, r + 2):
            for dx in range(-r - 1, r + 2):
                dist_sq = dx*dx + dy*dy
                if dist_sq <= r**2:
                    px, py = moon_x + dx, moon_y + dy
                    if 0 <= px < self.w and 0 <= py < self.h:
                        if (dx - 4)**2 + (dy + 2)**2 < 14: # crater
                            frame[py, px] = PALETTE["MOON_SHADOW"]
                        elif (dx + 6)**2 + (dy - 5)**2 < 20: # crater 2
                            frame[py, px] = PALETTE["MOON_SHADOW"]
                        else:
                            frame[py, px] = PALETTE["MOON_LIGHT"]
                # 16-bit moon glow dither
                elif dist_sq <= (r + 4)**2:
                    px, py = moon_x + dx, moon_y + dy
                    if 0 <= px < self.w and 0 <= py < self.h:
                        if (px + py) % 2 == 0:
                            frame[py, px] = PALETTE["MOON_LIGHT"]
                            
        # 3. Twinkling Stars
        for sx, sy, spd in self.stars:
            star_screen_x = int(sx - cam_x * 0.04) % (self.w + 40) - 20
            if 0 <= star_screen_x < self.w and 0 <= sy < self.h:
                twinkle = int(np.sin(frame_idx * spd + sx) * 2)
                if twinkle > 0:
                    frame[sy, star_screen_x] = PALETTE["STAR_BRIGHT"]
                elif twinkle == 0:
                    frame[sy, star_screen_x] = PALETTE["STAR_DIM"]

        # 4. Far Skyline Parallax (speed = 0.20)
        far_scroll = int(round(cam_x * 0.20)) % (self.far_width - self.w)
        blend_surface(frame, self.far_skyline[:, far_scroll:far_scroll + self.w], 0, 0)
        
        # 5. Mid City Parallax (speed = 0.50)
        mid_scroll = int(round(cam_x * 0.50)) % (self.mid_width - self.w)
        blend_surface(frame, self.mid_city[:, mid_scroll:mid_scroll + self.w], 0, 0)
        
        return frame

    def render_foreground(self, frame: np.ndarray, cam_x: int, frame_idx: int):
        """Draws the foreground street, sidewalk tiles, and retro lamp posts."""
        ground_y = self.h - 52
        
        # Sidewalk Top surface (tile pattern)
        for y in range(ground_y, ground_y + 14):
            frame[y, :, :] = PALETTE["SIDEWALK_TOP"]
            
        # Sidewalk tile lines moving with camera (speed 1.0)
        tile_offset = int(cam_x) % 24
        for x in range(-tile_offset, self.w, 24):
            if 0 <= x < self.w:
                frame[ground_y:ground_y + 14, x, :] = PALETTE["SIDEWALK_LINE"]
                
        # Sidewalk curb
        frame[ground_y + 14, :, :] = PALETTE["SIDEWALK_SIDE"]
        frame[ground_y + 15, :, :] = PALETTE["SIDEWALK_LINE"]
        
        # Asphalt Street
        for y in range(ground_y + 16, self.h):
            prog = (y - ground_y - 16) / float(self.h - ground_y - 16)
            c = PALETTE["ROAD_DARK"] if (y % 4 < 2) else PALETTE["ROAD_MID"]
            frame[y, :, :] = c
            
        # Street dashed yellow lines
        dash_offset = int(cam_x) % 40
        dash_y = ground_y + 28
        for x in range(-dash_offset, self.w, 40):
            draw_rect(frame, x, dash_y, 22, 3, "TEXT_YELLOW")
            
        # Retro Street Lamp Posts (spaced every 160 pixels)
        lamp_spacing = 160
        first_lamp = - (int(cam_x) % lamp_spacing)
        for lx in range(first_lamp - 20, self.w + lamp_spacing, lamp_spacing):
            self._draw_street_lamp(frame, lx, ground_y, frame_idx)

    def _draw_street_lamp(self, frame: np.ndarray, x: int, base_y: int, frame_idx: int):
        """Draws classic ornate retro street lamp with glowing light cone."""
        pole_h = 75
        top_y = base_y - pole_h
        
        # Cast warm pixel glow cone onto street (dithered semi-transparent)
        glow_center_x = x + 3
        glow_top_y = top_y + 10
        for dy in range(0, 95, 2):
            w_at_y = int(dy * 0.75)
            y_curr = glow_top_y + dy
            if 0 <= y_curr < self.h:
                for dx in range(-w_at_y, w_at_y + 1, 2):
                    px = glow_center_x + dx
                    if 0 <= px < self.w:
                        # checkerboard dither for authentic 16-bit translucency
                        if (px + y_curr) % 2 == 0:
                            # subtle warm lighting
                            orig = frame[y_curr, px, :3].astype(np.int32)
                            boost = np.array([35, 30, 8]) * (1.0 - dy / 100.0)
                            frame[y_curr, px, :3] = np.clip(orig + boost, 0, 255).astype(np.uint8)
                            
        # Lamp Pole Metal
        draw_rect(frame, x + 2, top_y + 10, 3, pole_h, "LAMPOST_METAL")
        draw_rect(frame, x + 3, top_y + 10, 1, pole_h, "LAMPOST_HIGHLIGHT")
        
        # Base mount
        draw_rect(frame, x, base_y - 4, 7, 5, "LAMPOST_METAL")
        
        # Lamp lantern housing
        draw_rect(frame, x - 2, top_y + 2, 11, 2, "LAMPOST_METAL") # cap
        draw_rect(frame, x - 1, top_y + 4, 9, 8, "LAMP_LIGHT")      # glowing glass bulb
        draw_rect(frame, x + 1, top_y + 5, 5, 6, "NAIWA_WHITE")     # bright center
        draw_rect(frame, x, top_y + 12, 7, 2, "LAMPOST_METAL")      # bottom collar
