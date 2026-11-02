"""
Motion-Kit Director: Orchestrates the 20-second 16-bit Animation Short Film.
Controls timelines, camera movements, scene transitions, VFX particles, and video export.
"""

import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .palette import PALETTE
from .sprites import (
    create_rgba_surface, draw_rect, draw_pixel, blend_surface,
    NaiwaSpriteFactory
)
from .scene import RetroCityScene
from .audio import ChiptuneSoundtrack

FPS = 30
TOTAL_SECONDS = 20
TOTAL_FRAMES = FPS * TOTAL_SECONDS # 600 frames
WIDTH = 480
HEIGHT = 270
OUT_WIDTH = 1920
OUT_HEIGHT = 1080

class AnimationDirector:
    def __init__(self):
        self.scene = RetroCityScene(WIDTH, HEIGHT)
        
        # Pre-cache Naiwa small sprites
        self.walk_frames = [NaiwaSpriteFactory.create_walk_frame(i) for i in range(4)]
        self.stop_frame = NaiwaSpriteFactory.create_stop_frame()
        self.side_eye_frame = NaiwaSpriteFactory.create_side_eye_frame(blink=False)
        self.laugh_frames = [NaiwaSpriteFactory.create_laugh_frame(i) for i in range(4)]
        
        # Pre-cache Close-up sprites for cinematic cut-in
        self.closeup_side_eye = NaiwaSpriteFactory.create_closeup_face("side_eye")
        self.closeup_laugh = NaiwaSpriteFactory.create_closeup_face("laugh")
        
    def render_frame(self, frame_idx: int) -> np.ndarray:
        """Renders one single 480x270 frame for frame_idx (0 to 599)."""
        time_sec = frame_idx / float(FPS)
        
        # ====================================================
        # SCENE 1: Slow Walking (0.0s - 7.5s, Frames 0 - 224)
        # ====================================================
        if frame_idx < 225:
            # Camera slowly pans right (retro camera tracking)
            cam_x = int(frame_idx * 0.9)
            
            # Base city render
            canvas = self.scene.render_background(cam_x, frame_idx)
            self.scene.render_foreground(canvas, cam_x, frame_idx)
            
            # Naiwa position on screen (walks slowly from left to center)
            start_x = 40
            target_x = 210
            t_prog = min(1.0, frame_idx / 210.0)
            naiwa_screen_x = int(start_x + (target_x - start_x) * t_prog)
            naiwa_screen_y = HEIGHT - 52 - 44
            
            # Ground shadow (16-bit dithered dark oval)
            for sx in range(-10, 11):
                for sy in range(-2, 3):
                    if (sx/10.0)**2 + (sy/2.0)**2 <= 1.0:
                        px = naiwa_screen_x + 24 + sx
                        py = naiwa_screen_y + 49 + sy
                        if (px + py) % 2 == 0 and 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            canvas[py, px, :3] = (canvas[py, px, :3] * 0.6).astype(np.uint8)
                            
            # Walk sprite cycle (change frame every 6 ticks)
            walk_idx = (frame_idx // 6) % 4
            blend_surface(canvas, self.walk_frames[walk_idx], naiwa_screen_x, naiwa_screen_y)
            
            # Initial Fade-In from black (frames 0 to 24)
            if frame_idx < 24:
                fade = 1.0 - (frame_idx / 24.0)
                canvas[:, :, :3] = (canvas[:, :, :3] * (1.0 - fade)).astype(np.uint8)
                
            # Retro Level Intro Title overlay (Frames 15 to 90)
            if 15 <= frame_idx <= 90:
                self._draw_pixel_text(canvas, 160, 48, "STAGE 1: NIGHT CITY", "TEXT_YELLOW")
                self._draw_pixel_text(canvas, 178, 62, "- NAIWA WALK -", "NAIWA_WHITE")
                
            return canvas

        # ====================================================
        # SCENE 2: Sudden Stop & Alert (7.5s - 9.0s, Frames 225 - 269)
        # ====================================================
        elif frame_idx < 270:
            cam_x = int(225 * 0.9) # camera freezes
            canvas = self.scene.render_background(cam_x, frame_idx)
            self.scene.render_foreground(canvas, cam_x, frame_idx)
            
            naiwa_screen_x = 210
            naiwa_screen_y = HEIGHT - 52 - 44
            
            # Shadow
            for sx in range(-12, 13):
                for sy in range(-2, 3):
                    if (sx/12.0)**2 + (sy/2.0)**2 <= 1.0:
                        px = naiwa_screen_x + 24 + sx
                        py = naiwa_screen_y + 49 + sy
                        if (px + py) % 2 == 0 and 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            canvas[py, px, :3] = (canvas[py, px, :3] * 0.6).astype(np.uint8)
                            
            # Sudden stop skid dust particles (frames 225 to 245)
            if frame_idx < 245:
                dust_age = frame_idx - 225
                for dx, dy in [(-8 - dust_age, 46 - dust_age//2), (-4 - dust_age*1.2, 48), (14 + dust_age, 47)]:
                    px = int(naiwa_screen_x + 24 + dx)
                    py = int(naiwa_screen_y + dy)
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        draw_rect(canvas, px, py, 3, 3, "TEXT_YELLOW" if dust_age < 8 else "NAIWA_WHITE")
                        
            # Sudden stop frame
            blend_surface(canvas, self.stop_frame, naiwa_screen_x, naiwa_screen_y)
            
            # Bouncing "!" Alert mark (Frames 234 to 269)
            if frame_idx >= 234:
                alert_age = frame_idx - 234
                bounce_y = int(abs(np.sin(alert_age * 0.35)) * 6)
                bubble_x = naiwa_screen_x + 30
                bubble_y = naiwa_screen_y - 18 - bounce_y
                
                # Speech bubble with exclamation point
                draw_rect(canvas, bubble_x, bubble_y, 14, 16, "TEXT_SHADOW")
                draw_rect(canvas, bubble_x + 1, bubble_y + 1, 12, 14, "ALERT_WHITE")
                # Red exclamation mark "!"
                draw_rect(canvas, bubble_x + 5, bubble_y + 3, 4, 6, "ALERT_RED")
                draw_rect(canvas, bubble_x + 5, bubble_y + 11, 4, 3, "ALERT_RED")
                # Little pointer
                draw_rect(canvas, bubble_x + 2, bubble_y + 15, 3, 2, "ALERT_WHITE")
                
            return canvas

        # ====================================================
        # SCENE 3: Cinematic Cut-in & Side-Eye (9.0s - 12.0s, Frames 270 - 359)
        # ====================================================
        elif frame_idx < 360:
            # SCENE TRANSITION: Retro Wipe / Split-Screen Cut-In!
            trans_prog = min(1.0, (frame_idx - 270) / 12.0)
            
            # Cinematic background: Dark moody night city with neon backdrop
            canvas = create_rgba_surface(WIDTH, HEIGHT)
            for y in range(HEIGHT):
                prog = y / float(HEIGHT)
                c_top = np.array(PALETTE["SKY_TOP"][:3])
                c_bot = np.array(PALETTE["SKY_BOTTOM"][:3])
                col = (c_top * (1 - prog) + c_bot * prog).astype(np.uint8)
                canvas[y, :, 0:3] = col
                canvas[y, :, 3] = 255
                
            # Distant blurred neon glow in background
            draw_rect(canvas, 60, 40, 110, 80, "MID_BLDG_BASE")
            draw_rect(canvas, 310, 30, 120, 100, "MID_BLDG_BASE")
            # Glowing neon sign in background
            neon_blink = (frame_idx // 8) % 2 == 0
            if neon_blink:
                draw_rect(canvas, 80, 50, 70, 18, "NEON_PINK")
                self._draw_pixel_text(canvas, 88, 54, "SUSPECT?", "NAIWA_WHITE")
            else:
                draw_rect(canvas, 80, 50, 70, 18, "NEON_CYAN")
                self._draw_pixel_text(canvas, 88, 54, "SUSPECT?", "TEXT_YELLOW")
                
            # Cinematic Letterbox bars (16-bit widescreen bars)
            bar_h = 32
            draw_rect(canvas, 0, 0, WIDTH, bar_h, "TEXT_SHADOW")
            draw_rect(canvas, 0, HEIGHT - bar_h, WIDTH, bar_h, "TEXT_SHADOW")
            draw_rect(canvas, 0, bar_h - 1, WIDTH, 1, "NEON_CYAN")
            draw_rect(canvas, 0, HEIGHT - bar_h, WIDTH, 1, "NEON_CYAN")
            
            # Center Dramatic Naiwa Close-Up Bust
            bust_x = WIDTH // 2 - 80
            # Subtle micro-breathing motion
            bust_y = HEIGHT // 2 - 68 + int(np.sin(frame_idx * 0.15) * 1.5)
            
            blend_surface(canvas, self.closeup_side_eye, bust_x, bust_y)
            
            # Moving pupil effect: black pupil slowly cuts hard to the side
            pupil_offset = min(12, int((frame_idx - 275) * 0.45))
            if pupil_offset > 0:
                for eye_cx in [bust_x + 80 - 28, bust_x + 80 + 28]:
                    px = eye_cx + 2 + pupil_offset
                    py = bust_y + 70 - 22
                    draw_rect(canvas, px - 3, py - 4, 6, 8, "NAIWA_PUPIL")
                    draw_rect(canvas, px - 2, py - 4, 3, 3, "NAIWA_WHITE") # catchlight
                    
            # Retro UI Dramatic Text & Suspense Dots
            dots = "." * ((frame_idx // 12) % 4)
            self._draw_pixel_text(canvas, 180, HEIGHT - 22, f"HOLD ON{dots}", "TEXT_YELLOW")
            self._draw_pixel_text(canvas, 20, 12, "TARGET ACQUIRED: SIDE-EYE", "NEON_CYAN")
            
            # Retro Transition Flash on Scene Entry (frames 270 to 275)
            if frame_idx < 276:
                flash = (276 - frame_idx) / 6.0
                canvas[:, :, :3] = np.clip(canvas[:, :, :3] + int(flash * 180), 0, 255).astype(np.uint8)
                
            return canvas

        # ====================================================
        # SCENE 4: Holding Belly Laughing Fiesta! (12.0s - 18.5s, Frames 360 - 554)
        # ====================================================
        elif frame_idx < 555:
            # CAMERA SCREEN SHAKE: Retro 16-bit impact shake
            shake_intensity = 4 if frame_idx < 410 else 2
            shake_x = int(np.random.randint(-shake_intensity, shake_intensity + 1))
            shake_y = int(np.random.randint(-shake_intensity, shake_intensity + 1))
            
            # Return to full street scene with celebration
            cam_x = int(225 * 0.9) + shake_x
            canvas = self.scene.render_background(cam_x, frame_idx)
            self.scene.render_foreground(canvas, cam_x, frame_idx)
            
            naiwa_screen_x = 210 + shake_x
            naiwa_screen_y = HEIGHT - 52 - 46 + shake_y
            
            # Ground shadow
            for sx in range(-14, 15):
                for sy in range(-3, 4):
                    if (sx/14.0)**2 + (sy/3.0)**2 <= 1.0:
                        px = naiwa_screen_x + 28 + sx
                        py = naiwa_screen_y + 51 + sy
                        if (px + py) % 2 == 0 and 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            canvas[py, px, :3] = (canvas[py, px, :3] * 0.55).astype(np.uint8)
                            
            # Laugh animation cycle: 4 frames, switching every 4 ticks for fast belly shaking
            laugh_phase = ((frame_idx - 360) // 4) % 4
            blend_surface(canvas, self.laugh_frames[laugh_phase], naiwa_screen_x, naiwa_screen_y)
            
            # Floating "HA HA HA!" Pixel text bubbles popping up
            ha_cycle = (frame_idx - 360)
            ha_positions = [
                (naiwa_screen_x - 35, naiwa_screen_y - 25 - (ha_cycle % 35)),
                (naiwa_screen_x + 45, naiwa_screen_y - 35 - ((ha_cycle + 15) % 35)),
                (naiwa_screen_x + 10, naiwa_screen_y - 50 - ((ha_cycle + 25) % 35))
            ]
            for hx, hy in ha_positions:
                if 0 <= hy < HEIGHT - 50:
                    self._draw_pixel_text(canvas, hx, hy, "HA HA HA!", "TEXT_YELLOW")
                    
            # Flying laughter tears sparkling in street light
            for i in range(4):
                tear_t = (frame_idx * 0.4 + i * 1.5) % 8.0
                tx = int(naiwa_screen_x + 28 + np.cos(i * 1.6) * (tear_t * 5))
                ty = int(naiwa_screen_y + 18 - np.sin(tear_t * 0.8) * 8 + tear_t * 3)
                if 0 <= tx < WIDTH and 0 <= ty < HEIGHT:
                    draw_rect(canvas, tx, ty, 3, 3, "VFX_TEAR")
                    draw_pixel(canvas, tx + 1, ty + 1, "NAIWA_WHITE")
                    
            # Neon celebratory flashes on street
            if (frame_idx // 6) % 2 == 0:
                self._draw_pixel_text(canvas, 170, 30, "★ ROFL ★", "NEON_PINK")
            else:
                self._draw_pixel_text(canvas, 170, 30, "★ ROFL ★", "NEON_CYAN")
                
            # Initial Laugh Hit White Flash (Frames 360 - 365)
            if frame_idx < 366:
                flash = (366 - frame_idx) / 6.0
                canvas[:, :, :3] = np.clip(canvas[:, :, :3] + int(flash * 200), 0, 255).astype(np.uint8)
                
            return canvas

        # ====================================================
        # SCENE 5: Outro & Stage Clear (18.5s - 20.0s, Frames 555 - 599)
        # ====================================================
        else:
            cam_x = int(225 * 0.9)
            canvas = self.scene.render_background(cam_x, frame_idx)
            self.scene.render_foreground(canvas, cam_x, frame_idx)
            
            naiwa_screen_x = 210
            naiwa_screen_y = HEIGHT - 52 - 46
            
            # Laughing gently
            laugh_phase = ((frame_idx - 360) // 6) % 4
            blend_surface(canvas, self.laugh_frames[laugh_phase], naiwa_screen_x, naiwa_screen_y)
            
            # "STAGE CLEAR!" Retro Banner
            banner_y = 60
            draw_rect(canvas, 120, banner_y, 240, 32, "TEXT_SHADOW")
            draw_rect(canvas, 122, banner_y + 2, 236, 28, "MID_BLDG_BASE")
            draw_rect(canvas, 124, banner_y + 4, 232, 24, "TEXT_SHADOW")
            self._draw_pixel_text(canvas, 170, banner_y + 10, "★ STAGE CLEAR! ★", "TEXT_YELLOW")
            self._draw_pixel_text(canvas, 185, banner_y + 22, "THANK YOU FOR PLAYING", "NAIWA_WHITE")
            
            # Retro Iris-Out / Circle Wipe to Black (Frames 565 to 599)
            if frame_idx >= 565:
                prog = (frame_idx - 565) / 34.0
                max_radius = int(np.sqrt(WIDTH**2 + HEIGHT**2) / 2)
                cur_radius = int(max_radius * (1.0 - prog))
                
                cx, cy = WIDTH // 2, HEIGHT // 2 - 10
                # Mask out pixels outside cur_radius with authentic 16-bit dither
                y_coords, x_coords = np.ogrid[:HEIGHT, :WIDTH]
                dist_sq = (x_coords - cx)**2 + (y_coords - cy)**2
                
                outer_mask = dist_sq > (cur_radius)**2
                canvas[outer_mask, :3] = 0
                
            return canvas

    def _draw_pixel_text(self, canvas: np.ndarray, x: int, y: int, text: str, color_key: str):
        """Draws crisp retro 5x7 bitmap font directly onto 16-bit canvas."""
        # Simple built-in 5x7 font dictionary for ASCII
        FONT_5X7 = {
            'A': ["01110", "10001", "11111", "10001", "10001"],
            'B': ["11110", "10001", "11110", "10001", "11110"],
            'C': ["01111", "10000", "10000", "10000", "01111"],
            'D': ["11110", "10001", "10001", "10001", "11110"],
            'E': ["11111", "10000", "11110", "10000", "11111"],
            'F': ["11111", "10000", "11110", "10000", "10000"],
            'G': ["01111", "10000", "10011", "10001", "01111"],
            'H': ["10001", "10001", "11111", "10001", "10001"],
            'I': ["11111", "00100", "00100", "00100", "11111"],
            'J': ["00001", "00001", "00001", "10001", "01110"],
            'K': ["10001", "10010", "11100", "10010", "10001"],
            'L': ["10000", "10000", "10000", "10000", "11111"],
            'M': ["10001", "11011", "10101", "10001", "10001"],
            'N': ["10001", "11001", "10101", "10011", "10001"],
            'O': ["01110", "10001", "10001", "10001", "01110"],
            'P': ["11110", "10001", "11110", "10000", "10000"],
            'Q': ["01110", "10001", "10001", "10011", "01111"],
            'R': ["11110", "10001", "11110", "10010", "10001"],
            'S': ["01111", "10000", "01110", "00001", "11110"],
            'T': ["11111", "00100", "00100", "00100", "00100"],
            'U': ["10001", "10001", "10001", "10001", "01110"],
            'V': ["10001", "10001", "10001", "01010", "00100"],
            'W': ["10001", "10001", "10101", "11011", "10001"],
            'X': ["10001", "01010", "00100", "01010", "10001"],
            'Y': ["10001", "01010", "00100", "00100", "00100"],
            'Z': ["11111", "00010", "00100", "01000", "11111"],
            '0': ["01110", "10011", "10101", "11001", "01110"],
            '1': ["00100", "01100", "00100", "00100", "01110"],
            ':': ["00000", "00100", "00000", "00100", "00000"],
            '!': ["00100", "00100", "00100", "00000", "00100"],
            '?': ["01110", "00001", "00110", "00000", "00100"],
            '.': ["00000", "00000", "00000", "00000", "00100"],
            '-': ["00000", "00000", "11111", "00000", "00000"],
            '★': ["00100", "11111", "01110", "10101", "00000"],
            ' ': ["00000", "00000", "00000", "00000", "00000"]
        }
        
        cur_x = x
        for ch in text.upper():
            glyph = FONT_5X7.get(ch, FONT_5X7[' '])
            for r, row in enumerate(glyph):
                for c, bit in enumerate(row):
                    if bit == '1':
                        # Drop shadow
                        draw_pixel(canvas, cur_x + c + 1, y + r + 1, "TEXT_SHADOW")
                        # Glyph pixel
                        draw_pixel(canvas, cur_x + c, y + r, color_key)
            cur_x += 6


def render_full_movie(output_mp4_path: str):
    """Renders 600 frames, synthesizes 8-bit audio, and muxes to 1920x1080 MP4."""
    temp_dir = "/tmp/motion_kit_render"
    os.makedirs(temp_dir, exist_ok=True)
    
    wav_path = os.path.join(temp_dir, "soundtrack.wav")
    print("[1/3] Synthesizing authentic 8-bit chiptune audio & SFX...")
    ChiptuneSoundtrack.save_wav(wav_path, duration=TOTAL_SECONDS)
    
    print(f"[2/3] Rendering {TOTAL_FRAMES} frames (480x270 -> 1920x1080 integer scale)...")
    director = AnimationDirector()
    
    # We pipe raw video directly into ffmpeg for ultra-fast, zero-disk bottleneck rendering
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{OUT_WIDTH}x{OUT_HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",                     # Standard input pipe
        "-i", wav_path,                # 8-bit Audio input
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]
    
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    for f in range(TOTAL_FRAMES):
        # 1. Render low-res 16-bit frame (480x270)
        low_res = director.render_frame(f)
        
        # 2. Nearest Neighbor 4x integer scaling to 1920x1080
        # NumPy repeat is blisteringly fast and preserves razor-sharp pixel edges
        high_res = np.repeat(np.repeat(low_res, 4, axis=0), 4, axis=1)
        
        # 3. Write raw RGBA bytes into ffmpeg stdin
        proc.stdin.write(high_res.tobytes())
        
        if (f + 1) % 60 == 0 or f == TOTAL_FRAMES - 1:
            print(f"  > Rendered frame {f + 1}/{TOTAL_FRAMES} ({(f+1)/FPS:.1f}s / {TOTAL_SECONDS}s)")
            
    proc.stdin.close()
    proc.wait()
    
    print(f"[3/3] Successfully generated 1920x1080 MP4 animation: {output_mp4_path}")
    
    # Verify file
    if os.path.exists(output_mp4_path) and os.path.getsize(output_mp4_path) > 100000:
        file_size_mb = os.path.getsize(output_mp4_path) / (1024 * 1024)
        print(f"Verified: Output file size is {file_size_mb:.2f} MB")
        return True
    else:
        raise RuntimeError(f"Video file generation failed or size too small: {output_mp4_path}")


if __name__ == "__main__":
    out_file = "/Users/xu.liu9/projects/fun/meme-workspace/naiwa_16bit_night_city.mp4"
    render_full_movie(out_file)
