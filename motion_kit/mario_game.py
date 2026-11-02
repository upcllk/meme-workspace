"""
Super Naiwa Bros. 16-bit Pixel Game Short Film (20.0 seconds).
Features:
- Naiwa Mario running across World 1-1
- Jump & hit Question Block -> Coin pop & Ding!
- Encounter Goomba -> Skid stop -> Stomp Goomba!
- Climb Green Pipe -> Try to warp -> Chubby belly gets stuck! Legs flailing!
- Pop out of pipe -> Holding belly laughing hysterically (iconic Naiwa laugh!)
- 8-bit chiptune BGM, classic SFX, 1920x1080 integer-scaled MP4.
"""

import os
import subprocess
import numpy as np
import wave
from PIL import Image
from .palette import PALETTE
from .mario_sprites import NaiwaMarioPixelArt, MARIO_PALETTE

FPS = 30
TOTAL_SECONDS = 20
TOTAL_FRAMES = FPS * TOTAL_SECONDS # 600 frames
WIDTH = 480
HEIGHT = 270
OUT_WIDTH = 1920
OUT_HEIGHT = 1080
SAMPLE_RATE = 44100

# Additional Mario World Colors
WORLD_PALETTE = {
    **MARIO_PALETTE,
    "SKY_BLUE": (107, 140, 255, 255),
    "CLOUD_WHITE": (255, 255, 255, 255),
    "CLOUD_SHADOW": (210, 225, 255, 255),
    "HILL_GREEN": (0, 168, 68, 255),
    "HILL_BORDER": (0, 120, 45, 255),
    "HILL_SPOT": (0, 205, 85, 255),
    
    "GROUND_TOP": (0, 185, 55, 255),
    "GROUND_BROWN": (200, 76, 12, 255),
    "GROUND_SHADOW": (130, 45, 8, 255),
    
    "BLOCK_BRICK": (195, 75, 20, 255),
    "BLOCK_LINE": (90, 30, 8, 255),
    "BLOCK_QUESTION": (255, 180, 20, 255),
    "BLOCK_EMPTY": (140, 110, 85, 255),
    
    "PIPE_GREEN": (0, 168, 0, 255),
    "PIPE_LIGHT": (120, 240, 60, 255),
    "PIPE_DARK": (0, 95, 0, 255),
    
    "GOOMBA_BROWN": (180, 70, 20, 255),
    "GOOMBA_FEET": (40, 20, 10, 255),
    "GOOMBA_WHITE": (250, 240, 220, 255),
    
    "COIN_GOLD": (255, 220, 30, 255),
    "COIN_ORANGE": (230, 140, 10, 255),
}

def create_surf(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.uint8)

def p_rect(surf: np.ndarray, x: int, y: int, w: int, h: int, color_key: str):
    y1, y2 = max(0, y), min(surf.shape[0], y + h)
    x1, x2 = max(0, x), min(surf.shape[1], x + w)
    if y1 < y2 and x1 < x2:
        surf[y1:y2, x1:x2] = WORLD_PALETTE[color_key]

def p_dot(surf: np.ndarray, x: int, y: int, color_key: str):
    if 0 <= y < surf.shape[0] and 0 <= x < surf.shape[1]:
        surf[y, x] = WORLD_PALETTE[color_key]

def blend_surface(dest: np.ndarray, src: np.ndarray, x: int, y: int):
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


class MarioLevelAssets:
    """Renders retro tiles: Clouds, Hills, Pipes, Blocks, Goombas."""

    @staticmethod
    def draw_cloud(surf: np.ndarray, x: int, y: int, size: int = 1):
        # Fluffy white cloud with cartoon eyes
        cw = 40 * size
        ch = 18
        p_rect(surf, x, y + 4, cw, ch - 4, "CLOUD_WHITE")
        p_rect(surf, x + 6, y, cw - 12, ch, "CLOUD_WHITE")
        p_rect(surf, x + 1, y + ch - 3, cw - 2, 3, "CLOUD_SHADOW")
        # Classic Mario eyes on cloud
        p_rect(surf, x + cw // 2 - 5, y + 6, 2, 5, "NAIWA_OUTLINE")
        p_rect(surf, x + cw // 2 + 3, y + 6, 2, 5, "NAIWA_OUTLINE")

    @staticmethod
    def draw_hill(surf: np.ndarray, cx: int, base_y: int, radius: int):
        # Round green Mario hill with spots
        for dy in range(radius):
            hw = int(np.sqrt(radius**2 - (radius - dy)**2) * 1.5)
            y = base_y - dy
            if 0 <= y < surf.shape[0]:
                p_rect(surf, cx - hw, y, hw * 2, 1, "HILL_GREEN")
                p_dot(surf, cx - hw, y, "HILL_BORDER")
                p_dot(surf, cx + hw - 1, y, "HILL_BORDER")
        # Hill eyes
        p_rect(surf, cx - 6, base_y - radius // 2, 2, 6, "NAIWA_OUTLINE")
        p_rect(surf, cx + 4, base_y - radius // 2, 2, 6, "NAIWA_OUTLINE")

    @staticmethod
    def draw_pipe(surf: np.ndarray, x: int, base_y: int, h: int, w: int = 34):
        # Pipe rim
        rim_h = 14
        rim_w = w + 6
        rx = x - 3
        ry = base_y - h
        p_rect(surf, rx - 1, ry - 1, rim_w + 2, rim_h + 2, "NAIWA_OUTLINE")
        p_rect(surf, rx, ry, rim_w, rim_h, "PIPE_GREEN")
        p_rect(surf, rx + 3, ry, 5, rim_h, "PIPE_LIGHT")
        p_rect(surf, rx + rim_w - 7, ry, 7, rim_h, "PIPE_DARK")
        
        # Pipe stem
        sx = x
        sy = ry + rim_h
        sh = h - rim_h
        p_rect(surf, sx - 1, sy, w + 2, sh, "NAIWA_OUTLINE")
        p_rect(surf, sx, sy, w, sh, "PIPE_GREEN")
        p_rect(surf, sx + 3, sy, 4, sh, "PIPE_LIGHT")
        p_rect(surf, sx + w - 6, sy, 6, sh, "PIPE_DARK")

    @staticmethod
    def draw_question_block(surf: np.ndarray, x: int, y: int, hit: bool = False, frame_idx: int = 0):
        # 16x16 Question Block
        p_rect(surf, x, y, 16, 16, "NAIWA_OUTLINE")
        if not hit:
            p_rect(surf, x + 1, y + 1, 14, 14, "BLOCK_QUESTION")
            p_rect(surf, x + 1, y + 1, 14, 2, "COIN_GOLD")
            p_rect(surf, x + 1, y + 13, 14, 2, "COIN_ORANGE")
            # Flashing "?" symbol
            p_rect(surf, x + 5, y + 4, 6, 2, "NAIWA_OUTLINE")
            p_rect(surf, x + 9, y + 6, 2, 3, "NAIWA_OUTLINE")
            p_rect(surf, x + 7, y + 8, 2, 2, "NAIWA_OUTLINE")
            p_rect(surf, x + 7, y + 11, 2, 2, "NAIWA_OUTLINE")
        else:
            p_rect(surf, x + 1, y + 1, 14, 14, "BLOCK_EMPTY")
            p_rect(surf, x + 2, y + 2, 2, 2, "NAIWA_OUTLINE")
            p_rect(surf, x + 12, y + 2, 2, 2, "NAIWA_OUTLINE")
            p_rect(surf, x + 2, y + 12, 2, 2, "NAIWA_OUTLINE")
            p_rect(surf, x + 12, y + 12, 2, 2, "NAIWA_OUTLINE")

    @staticmethod
    def draw_goomba(surf: np.ndarray, x: int, y: int, squished: bool = False, step: int = 0):
        # Classic Mario Goomba (16x16)
        if not squished:
            # Head mushroom
            p_rect(surf, x + 4, y, 8, 2, "GOOMBA_BROWN")
            p_rect(surf, x + 2, y + 2, 12, 3, "GOOMBA_BROWN")
            p_rect(surf, x, y + 5, 16, 4, "GOOMBA_BROWN")
            # Face
            p_rect(surf, x + 2, y + 9, 12, 4, "GOOMBA_WHITE")
            # Angry eyes
            p_rect(surf, x + 3, y + 8, 3, 4, "NAIWA_OUTLINE")
            p_rect(surf, x + 4, y + 9, 1, 2, "GOOMBA_WHITE")
            p_rect(surf, x + 10, y + 8, 3, 4, "NAIWA_OUTLINE")
            p_rect(surf, x + 11, y + 9, 1, 2, "GOOMBA_WHITE")
            # Black feet
            f_offset = 2 if step % 2 == 0 else -2
            p_rect(surf, x + 1, y + 13, 6, 3, "GOOMBA_FEET")
            p_rect(surf, x + 9, y + 13, 6, 3, "GOOMBA_FEET")
        else:
            # Flat pancake squished Goomba
            p_rect(surf, x, y + 11, 16, 5, "GOOMBA_BROWN")
            p_rect(surf, x + 2, y + 12, 12, 2, "GOOMBA_WHITE")
            p_rect(surf, x + 3, y + 12, 3, 1, "NAIWA_OUTLINE")
            p_rect(surf, x + 10, y + 12, 3, 1, "NAIWA_OUTLINE")


class MarioGameSoundtrack:
    """Synthesizes the complete 20.0s Super Mario 8-bit soundtrack and SFX."""

    @classmethod
    def generate_soundtrack(cls) -> np.ndarray:
        n_samples = int(SAMPLE_RATE * TOTAL_SECONDS)
        master_l = np.zeros(n_samples, dtype=np.float32)
        master_r = np.zeros(n_samples, dtype=np.float32)

        def add_clip(clip: np.ndarray, st: float, vl: float = 1.0, vr: float = 1.0):
            idx = int(st * SAMPLE_RATE)
            end = min(n_samples, idx + len(clip))
            if idx < n_samples:
                sz = end - idx
                master_l[idx:end] += clip[:sz] * vl
                master_r[idx:end] += clip[:sz] * vr

        # --- 1. Classic Mario Overworld Theme (0.0s - 7.5s & 12.0s - 18.5s) ---
        beat = 0.16 # ~188 BPM
        E5, D5, C5, G4, E4, A4, B4, F5 = 659.25, 587.33, 523.25, 392.00, 329.63, 440.00, 493.88, 698.46
        G5, A5, C6 = 783.99, 880.00, 1046.50
        C4, G3, A3, E3, F3, F4 = 261.63, 196.00, 220.00, 164.81, 174.61, 349.23

        def synth_square(freq, dur, vol=0.25):
            ns = int(SAMPLE_RATE * dur)
            t = np.linspace(0, dur, ns, endpoint=False)
            sq = np.where((t * freq) % 1.0 < 0.5, 1.0, -1.0) * vol
            env = np.linspace(1.0, 0.6, ns)**2
            return sq * env

        def synth_bass(freq, dur, vol=0.3):
            ns = int(SAMPLE_RATE * dur)
            t = np.linspace(0, dur, ns, endpoint=False)
            ph = (t * freq) % 1.0
            tri = (2.0 * np.abs(2.0 * (ph - np.floor(ph + 0.5))) - 1.0) * vol
            return tri

        # Intro triplet
        intro_notes = [(0.1, E5), (0.24, E5), (0.48, E5), (0.64, C5), (0.78, E5), (1.02, G5), (1.35, G4)]
        for st, fq in intro_notes:
            add_clip(synth_square(fq, 0.12), st, 0.7, 0.7)

        # Main loop phrase
        phrase = [
            (C5, beat*1.5), (G4, beat*1.5), (E4, beat*1.5), (A4, beat), (B4, beat),
            (A4, beat*0.8), (G4, beat*1.2), (E5, beat*1.2), (G5, beat*1.2), (A5, beat*2)
        ]
        t = 1.8
        while t < 7.2:
            for fq, d in phrase:
                if t >= 7.2: break
                add_clip(synth_square(fq, d * 0.85, vol=0.22), t, 0.7, 0.6)
                # Bass
                add_clip(synth_bass(fq / 2.0, d * 0.9, vol=0.28), t, 0.8, 0.8)
                t += d

        # --- 2. SFX: Jump (at 3.5s) ---
        jump_ns = int(SAMPLE_RATE * 0.22)
        t_j = np.linspace(0, 0.22, jump_ns)
        freq_j = np.linspace(180.0, 680.0, jump_ns)
        jump_wave = np.where((np.cumsum(freq_j)/SAMPLE_RATE % 1.0) < 0.5, 1.0, -1.0) * 0.35
        add_clip(jump_wave, 3.45, 0.9, 0.9)

        # --- 3. SFX: Coin Ding-Ding! (at 3.8s) ---
        coin1 = synth_square(987.77, 0.08, vol=0.4) # B5
        coin2 = synth_square(1318.51, 0.35, vol=0.45) # E6
        add_clip(coin1, 3.80, 0.9, 0.9)
        add_clip(coin2, 3.86, 0.9, 0.9)

        # --- 4. SFX: Skid Stop & Alert (7.4s - 8.2s) ---
        skid_ns = int(SAMPLE_RATE * 0.25)
        skid = np.random.uniform(-1, 1, skid_ns) * np.linspace(0.3, 0.0, skid_ns)
        add_clip(skid, 7.4, 0.8, 0.8)
        # Metal "!" Alert
        alert = synth_square(1600.0, 0.15, vol=0.5)
        add_clip(alert, 7.7, 1.0, 1.0)

        # --- 5. SFX: Jump & Stomp Goomba (8.3s & 8.6s) ---
        add_clip(jump_wave, 8.25, 0.8, 0.8)
        # Stomp low thud
        stomp = np.random.uniform(-1, 1, int(0.12 * SAMPLE_RATE)) * 0.4 + synth_bass(110.0, 0.12, 0.5)
        add_clip(stomp, 8.6, 1.0, 1.0)

        # --- 6. SFX: Pipe Down & STUCK! (9.5s - 11.5s) ---
        # Pipe slide down
        pipe_ns = int(SAMPLE_RATE * 0.35)
        pipe_freq = np.linspace(440.0, 120.0, pipe_ns)
        pipe_wave = np.where((np.cumsum(pipe_freq)/SAMPLE_RATE % 1.0) < 0.5, 1.0, -1.0) * 0.35
        add_clip(pipe_wave, 9.4, 0.9, 0.9)
        
        # Funny stuck struggle sounds (boing-boing flailing legs)
        for i, bt in enumerate([9.9, 10.3, 10.7, 11.1]):
            boing = synth_square(300.0 + (i%2)*150.0, 0.1, vol=0.3)
            add_clip(boing, bt, 0.8, 0.8)

        # --- 7. SFX: Pop Out "Cork POP!" (12.0s) ---
        pop_ns = int(SAMPLE_RATE * 0.15)
        pop_f = np.linspace(200.0, 950.0, pop_ns)
        pop_wave = np.where((np.cumsum(pop_f)/SAMPLE_RATE % 1.0) < 0.5, 1.0, -1.0) * 0.55
        add_clip(pop_wave, 12.0, 1.0, 1.0)

        # --- 8. Laughing Fiesta & Celebration (12.1s - 18.5s) ---
        # Naiwa Belly Laugh SFX (HA-HA-HA-HA arpeggios)
        laugh_times = [12.2, 12.8, 13.5, 14.2, 15.0, 15.8, 16.6, 17.4]
        for lt in laugh_times:
            for k, p in enumerate([659.25, 783.99, 987.77, 880.00]):
                syl = synth_square(p, 0.06, vol=0.35)
                add_clip(syl, lt + k * 0.08, 0.9 if k%2==0 else 0.5, 0.5 if k%2==0 else 0.9)

        # Upbeat Victory Party groove underneath laughter
        t_win = 12.2
        fast_b = 0.2
        idx_w = 0
        party_chord = [C4, G4, A4, F4, C4, G4, C5, G4]
        while t_win < 18.4:
            ch_freq = party_chord[idx_w % len(party_chord)]
            add_clip(synth_square(ch_freq, fast_b * 0.8, vol=0.25), t_win, 0.7, 0.7)
            add_clip(synth_bass(ch_freq / 2.0, fast_b * 0.85, vol=0.35), t_win, 0.8, 0.8)
            t_win += fast_b
            idx_w += 1

        # --- 9. Stage Clear Fanfare (18.5s - 20.0s) ---
        fanfare = [
            (18.5, G4, 0.12), (18.65, C5, 0.12), (18.8, E5, 0.12),
            (18.95, G5, 0.22), (19.2, E5, 0.15), (19.4, C6, 0.45)
        ]
        for st, fq, dur in fanfare:
            add_clip(synth_square(fq, dur, vol=0.35), st, 0.85, 0.85)

        # Master normalize
        fade_st = int(19.4 * SAMPLE_RATE)
        fade_len = n_samples - fade_st
        if fade_len > 0:
            env = np.linspace(1.0, 0.0, fade_len)
            master_l[fade_st:] *= env
            master_r[fade_st:] *= env

        mx = max(np.max(np.abs(master_l)), np.max(np.abs(master_r)), 0.01)
        scale = 0.90 / mx
        master_l = np.clip(master_l * scale, -1.0, 1.0)
        master_r = np.clip(master_r * scale, -1.0, 1.0)

        left_int = (master_l * 32767).astype(np.int16)
        right_int = (master_r * 32767).astype(np.int16)
        pcm = np.empty((n_samples * 2,), dtype=np.int16)
        pcm[0::2] = left_int
        pcm[1::2] = right_int
        return pcm

    @classmethod
    def save_wav(cls, filepath: str):
        data = cls.generate_soundtrack()
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(data.tobytes())
        print(f"[Audio] Generated 20s 8-bit Mario soundtrack to {filepath}")


class SuperNaiwaDirector:
    """Directs 600 frames of full-action Super Naiwa Mario gameplay."""

    def __init__(self):
        # Pre-cache Mario sprites
        self.sprite_idle = NaiwaMarioPixelArt.create_ingame_sprite("idle")
        self.sprite_run0 = NaiwaMarioPixelArt.create_ingame_sprite("run", 0)
        self.sprite_run1 = NaiwaMarioPixelArt.create_ingame_sprite("run", 1)
        self.sprite_run2 = NaiwaMarioPixelArt.create_ingame_sprite("run", 2)
        self.sprite_jump = NaiwaMarioPixelArt.create_ingame_sprite("jump")
        self.sprite_laugh = NaiwaMarioPixelArt.create_ingame_sprite("laugh")
        self.portrait = NaiwaMarioPixelArt.create_large_portrait()

    def render_frame(self, frame_idx: int) -> np.ndarray:
        canvas = create_surf(WIDTH, HEIGHT)
        ground_y = HEIGHT - 40 # y = 230
        
        # --- 0. Title Card on Intro (0 - 24 frames) ---
        if frame_idx < 25:
            canvas[:, :, 0:3] = [15, 15, 20]
            canvas[:, :, 3] = 255
            self._draw_pixel_text(canvas, 160, 100, "SUPER NAIWA BROS.", "BUTTON_YELLOW")
            self._draw_pixel_text(canvas, 190, 130, "WORLD  1-1", "EMBLEM_WHITE")
            self._draw_pixel_text(canvas, 205, 155, "x 3", "COIN_GOLD")
            # Mini Naiwa head icon
            blend_surface(canvas, self.sprite_idle[0:24, 12:36], 180, 150)
            return canvas

        # --- 1. Background Sky & Scenery ---
        canvas[:, :, :] = WORLD_PALETTE["SKY_BLUE"]
        
        # Camera Scroll X
        # Follow Naiwa smoothly
        if frame_idx < 105:
            cam_x = int((frame_idx - 25) * 1.5)
        elif frame_idx < 270:
            cam_x = 120 + int((frame_idx - 105) * 1.2)
        else:
            cam_x = 318 # camera locks around the pipe!

        # Clouds in sky
        MarioLevelAssets.draw_cloud(canvas, 60 - int(cam_x * 0.2), 30, size=2)
        MarioLevelAssets.draw_cloud(canvas, 240 - int(cam_x * 0.2), 45, size=1)
        MarioLevelAssets.draw_cloud(canvas, 420 - int(cam_x * 0.2), 25, size=3)
        MarioLevelAssets.draw_cloud(canvas, 620 - int(cam_x * 0.2), 40, size=2)

        # Green Hills
        MarioLevelAssets.draw_hill(canvas, 100 - int(cam_x * 0.5), ground_y, 40)
        MarioLevelAssets.draw_hill(canvas, 320 - int(cam_x * 0.5), ground_y, 65)
        MarioLevelAssets.draw_hill(canvas, 580 - int(cam_x * 0.5), ground_y, 50)

        # Ground Blocks (Brown with green grass rim)
        p_rect(canvas, 0, ground_y, WIDTH, 4, "GROUND_TOP")
        p_rect(canvas, 0, ground_y + 4, WIDTH, 36, "GROUND_BROWN")
        for gy in range(ground_y + 4, HEIGHT, 8):
            for gx in range(-int(cam_x)%16, WIDTH, 16):
                p_rect(canvas, gx, gy, 15, 1, "GROUND_SHADOW")
                p_rect(canvas, gx + 7, gy, 1, 8, "GROUND_SHADOW")

        # --- 2. Interactive Objects & Obstacles ---
        # Question Block at x = 240
        q_screen_x = 240 - cam_x
        q_screen_y = ground_y - 75 # floating brick height
        hit_block = (frame_idx >= 115) # hit at frame 115 (~3.8s)
        bounce_block_y = q_screen_y - (4 if 115 <= frame_idx <= 122 else 0)
        MarioLevelAssets.draw_question_block(canvas, q_screen_x, bounce_block_y, hit=hit_block, frame_idx=frame_idx)
        # Neighboring brown brick blocks
        p_rect(canvas, q_screen_x - 16, q_screen_y, 16, 16, "BLOCK_BRICK")
        p_rect(canvas, q_screen_x + 16, q_screen_y, 16, 16, "BLOCK_BRICK")

        # Popping Coin Animation (frames 115 to 145)
        if 115 <= frame_idx <= 145:
            coin_age = frame_idx - 115
            coin_y = q_screen_y - int(np.sin(coin_age / 30.0 * np.pi) * 35)
            p_rect(canvas, q_screen_x + 4, coin_y, 8, 12, "COIN_GOLD")
            p_rect(canvas, q_screen_x + 6, coin_y + 2, 4, 8, "COIN_ORANGE")
            self._draw_pixel_text(canvas, q_screen_x - 4, coin_y - 10, "+1000", "EMBLEM_WHITE")

        # Green Warp Pipe at x = 460
        pipe_screen_x = 460 - cam_x
        pipe_h = 55
        MarioLevelAssets.draw_pipe(canvas, pipe_screen_x, ground_y, pipe_h, w=44)

        # Goomba Enemy at x = 360
        goomba_alive = (frame_idx < 258) # stomped at 8.6s (frame 258)
        goomba_x = 360 - cam_x - (int((frame_idx - 150) * 0.6) if frame_idx > 150 and goomba_alive else 0)
        if goomba_alive:
            MarioLevelAssets.draw_goomba(canvas, goomba_x, ground_y - 16, squished=False, step=frame_idx//6)
        elif frame_idx < 280:
            # Squished flat Goomba
            MarioLevelAssets.draw_goomba(canvas, goomba_x, ground_y - 16, squished=True)
            self._draw_pixel_text(canvas, goomba_x, ground_y - 28, "+200", "BUTTON_YELLOW")

        # --- 3. Super Naiwa Mario Actor Animation ---
        # Phase 1: Run to Question Block (25 to 105 frames, 0.8s - 3.5s)
        if frame_idx < 105:
            naiwa_x = 80
            naiwa_y = ground_y - 50
            run_anim = [self.sprite_run0, self.sprite_run1, self.sprite_run2][(frame_idx // 4) % 3]
            blend_surface(canvas, run_anim, naiwa_x, naiwa_y)

        # Phase 2: Jump & Hit Block (105 to 145 frames, 3.5s - 4.8s)
        elif frame_idx < 145:
            jump_prog = (frame_idx - 105) / 40.0 # 0.0 to 1.0
            jump_h = int(np.sin(jump_prog * np.pi) * 60) # peak at block
            naiwa_x = 80 + int(jump_prog * 45)
            naiwa_y = ground_y - 50 - jump_h
            blend_surface(canvas, self.sprite_jump, naiwa_x, naiwa_y)

        # Phase 3: Run Towards Goomba & Skid Stop (145 to 240 frames, 4.8s - 8.0s)
        elif frame_idx < 240:
            if frame_idx < 220:
                # Running forward
                naiwa_x = 125
                naiwa_y = ground_y - 50
                run_anim = [self.sprite_run0, self.sprite_run1, self.sprite_run2][(frame_idx // 4) % 3]
                blend_surface(canvas, run_anim, naiwa_x, naiwa_y)
            else:
                # Sudden Skid Stop! (Frames 220 to 240)
                naiwa_x = 125
                naiwa_y = ground_y - 50
                blend_surface(canvas, self.sprite_idle, naiwa_x, naiwa_y)
                # Skid smoke
                p_rect(canvas, naiwa_x - 6, ground_y - 8, 5, 5, "EMBLEM_WHITE")
                # "!" Alert Bubble
                p_rect(canvas, naiwa_x + 30, naiwa_y - 12, 12, 14, "CLOUD_WHITE")
                p_rect(canvas, naiwa_x + 34, naiwa_y - 10, 4, 6, "CAP_RED")
                p_rect(canvas, naiwa_x + 34, naiwa_y - 2, 4, 3, "CAP_RED")

        # Phase 4: Stomp Goomba (240 to 285 frames, 8.0s - 9.5s)
        elif frame_idx < 285:
            stomp_prog = (frame_idx - 240) / 45.0
            if stomp_prog < 0.4:
                # Jump up
                sy = int(np.sin(stomp_prog / 0.4 * np.pi * 0.5) * 45)
                naiwa_x = 125 + int(stomp_prog * 40)
                naiwa_y = ground_y - 50 - sy
                blend_surface(canvas, self.sprite_jump, naiwa_x, naiwa_y)
            else:
                # Land & rebound stomp
                reb_prog = (stomp_prog - 0.4) / 0.6
                sy = int((1.0 - np.sin(reb_prog * np.pi)) * 15)
                naiwa_x = 141 + int(reb_prog * 25)
                naiwa_y = ground_y - 50 - sy
                blend_surface(canvas, self.sprite_idle, naiwa_x, naiwa_y)

        # Phase 5: Jump onto Pipe & Try to enter (285 to 360 frames, 9.5s - 12.0s)
        elif frame_idx < 360:
            if frame_idx < 305:
                # Jump onto top of pipe
                p_prog = (frame_idx - 285) / 20.0
                naiwa_x = 166 + int(p_prog * (pipe_screen_x + 6 - 166))
                naiwa_y = ground_y - 50 - int(np.sin(p_prog * np.pi) * 30) - int(p_prog * pipe_h)
                blend_surface(canvas, self.sprite_jump, naiwa_x, naiwa_y)
            else:
                # STUCK IN PIPE! Chubby Belly Too Big! (Frames 305 to 360)
                stuck_x = pipe_screen_x + 4
                stuck_y = ground_y - pipe_h - 26 # half body stuck in pipe rim
                
                # Flailing legs animation (left/right alternating)
                flail = (frame_idx // 3) % 4
                leg_offset_l = -3 if flail in [0, 1] else 3
                leg_offset_r = 3 if flail in [0, 1] else -3
                
                # Draw stuck Naiwa: Big round belly wedged on pipe rim!
                p_rect(canvas, stuck_x + 4, stuck_y + 12, 28, 14, "OVERALL_BLUE")
                p_rect(canvas, stuck_x + 8, stuck_y + 8, 20, 12, "NAIWA_BELLY_LIGHT") # belly jammed!
                
                # Boots kicking in air
                p_rect(canvas, stuck_x + 2 + leg_offset_l, stuck_y + 2, 8, 6, "BOOT_BROWN")
                p_rect(canvas, stuck_x + 24 + leg_offset_r, stuck_y + 2, 8, 6, "BOOT_BROWN")
                
                # Funny sweat drops
                p_rect(canvas, stuck_x - 4, stuck_y + 4, 3, 4, "COIN_GOLD")
                p_rect(canvas, stuck_x + 36, stuck_y + 4, 3, 4, "COIN_GOLD")
                self._draw_pixel_text(canvas, stuck_x - 10, stuck_y - 12, "STUCK!!", "CAP_RED")

        # Phase 6: Pop Out & HOLDING BELLY LAUGHING! (360 to 555 frames, 12.0s - 18.5s)
        elif frame_idx < 555:
            # Screen shake effect during hilarious laughter
            shake_x = int(np.random.randint(-2, 3))
            shake_y = int(np.random.randint(-2, 3))
            
            # Naiwa lands next to the pipe
            laugh_x = pipe_screen_x - 55 + shake_x
            laugh_y = ground_y - 50 + shake_y
            
            # Ground shadow
            for sx in range(-12, 13):
                px = laugh_x + 24 + sx
                py = ground_y - 2
                if 0 <= px < WIDTH:
                    canvas[py, px, :3] = (canvas[py, px, :3] * 0.6).astype(np.uint8)
                    
            # Belly Laugh Sprite
            blend_surface(canvas, self.sprite_laugh, laugh_x, laugh_y)
            
            # Floating "HA HA HA!" bubbles popping from laugh
            cycle = (frame_idx - 360)
            bubbles = [
                (laugh_x - 30, laugh_y - 20 - (cycle % 40)),
                (laugh_x + 40, laugh_y - 30 - ((cycle + 18) % 40)),
                (laugh_x + 10, laugh_y - 45 - ((cycle + 28) % 40))
            ]
            for bx, by in bubbles:
                if 0 <= by < ground_y - 30:
                    self._draw_pixel_text(canvas, bx, by, "HA HA HA!", "COIN_GOLD")
                    
            # Flying laughter tears
            for i in range(3):
                t_tear = (frame_idx * 0.5 + i * 2.0) % 8.0
                tx = int(laugh_x + 24 + np.cos(i * 2.1) * (t_tear * 4))
                ty = int(laugh_y + 12 - np.sin(t_tear * 0.8) * 6 + t_tear * 2)
                if 0 <= tx < WIDTH and 0 <= ty < HEIGHT:
                    p_rect(canvas, tx, ty, 3, 3, "CLOUD_SHADOW")
                    p_dot(canvas, tx + 1, ty + 1, "CLOUD_WHITE")

        # Phase 7: Stage Clear & Iris Out (555 to 599 frames, 18.5s - 20.0s)
        else:
            laugh_x = pipe_screen_x - 55
            laugh_y = ground_y - 50
            blend_surface(canvas, self.sprite_laugh, laugh_x, laugh_y)
            
            # Course Clear Banner
            p_rect(canvas, 130, 60, 220, 36, "OVERALL_BLUE_DARK")
            p_rect(canvas, 132, 62, 216, 32, "CLOUD_WHITE")
            p_rect(canvas, 134, 64, 212, 28, "OVERALL_BLUE_DARK")
            self._draw_pixel_text(canvas, 160, 72, "★ COURSE CLEAR! ★", "BUTTON_YELLOW")
            self._draw_pixel_text(canvas, 175, 84, "SCORE: 999990", "EMBLEM_WHITE")
            
            # Iris Out Circle Wipe (frames 570 - 599)
            if frame_idx >= 570:
                prog = (frame_idx - 570) / 29.0
                max_r = int(np.sqrt(WIDTH**2 + HEIGHT**2) / 2)
                cur_r = int(max_r * (1.0 - prog))
                cx, cy = WIDTH // 2, HEIGHT // 2
                y_c, x_c = np.ogrid[:HEIGHT, :WIDTH]
                outer_mask = (x_c - cx)**2 + (y_c - cy)**2 > cur_r**2
                canvas[outer_mask, :3] = 0

        # --- 4. Retro HUD (Top status bar) ---
        self._draw_pixel_text(canvas, 24, 12, "NAIWA", "EMBLEM_WHITE")
        self._draw_pixel_text(canvas, 24, 22, "001200", "EMBLEM_WHITE")
        self._draw_pixel_text(canvas, 180, 22, "* 01", "COIN_GOLD")
        self._draw_pixel_text(canvas, 280, 12, "WORLD", "EMBLEM_WHITE")
        self._draw_pixel_text(canvas, 290, 22, "1-1", "EMBLEM_WHITE")
        self._draw_pixel_text(canvas, 390, 12, "TIME", "EMBLEM_WHITE")
        time_left = max(0, 360 - int(frame_idx * 0.6))
        self._draw_pixel_text(canvas, 396, 22, f"{time_left:03d}", "EMBLEM_WHITE")

        return canvas

    def _draw_pixel_text(self, canvas: np.ndarray, x: int, y: int, text: str, color_key: str):
        """Draws retro 5x7 bitmap font."""
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
            '0': ["01110", "10011", "10101", "11001", "01110"],
            '1': ["00100", "01100", "00100", "00100", "01110"],
            '2': ["01110", "10001", "00010", "00100", "11111"],
            '3': ["11110", "00001", "01110", "00001", "11110"],
            '4': ["10001", "10001", "11111", "00001", "00001"],
            '5': ["11111", "10000", "11110", "00001", "11110"],
            '6': ["01110", "10000", "11110", "10001", "01110"],
            '7': ["11111", "00001", "00010", "00100", "00100"],
            '8': ["01110", "10001", "01110", "10001", "01110"],
            '9': ["01110", "10001", "01111", "00001", "01110"],
            ':': ["00000", "00100", "00000", "00100", "00000"],
            '!': ["00100", "00100", "00100", "00000", "00100"],
            '*': ["00000", "10101", "01110", "10101", "00000"],
            '+': ["00000", "00100", "01110", "00100", "00000"],
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
                        p_dot(canvas, cur_x + c + 1, y + r + 1, "NAIWA_OUTLINE")
                        p_dot(canvas, cur_x + c, y + r, color_key)
            cur_x += 6


def render_mario_video(output_mp4: str):
    """Renders 600 frames and muxes with 8-bit audio directly into 1920x1080 MP4."""
    temp_dir = "/tmp/mario_game_render"
    os.makedirs(temp_dir, exist_ok=True)
    wav_path = os.path.join(temp_dir, "mario_soundtrack.wav")
    
    print("[1/3] Synthesizing 20s 8-bit Super Mario audio & SFX...")
    MarioGameSoundtrack.save_wav(wav_path)
    
    print(f"[2/3] Rendering {TOTAL_FRAMES} frames (480x270 -> 1920x1080 4x integer scale)...")
    director = SuperNaiwaDirector()
    
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
        output_mp4
    ]
    
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    for f in range(TOTAL_FRAMES):
        low_res = director.render_frame(f)
        # Nearest-Neighbor 4x integer scaling: 480x270 -> 1920x1080
        high_res = np.repeat(np.repeat(low_res, 4, axis=0), 4, axis=1)
        proc.stdin.write(high_res.tobytes())
        
        if (f + 1) % 60 == 0 or f == TOTAL_FRAMES - 1:
            print(f"  > Frame {f + 1}/{TOTAL_FRAMES} rendered ({(f+1)/FPS:.1f}s / {TOTAL_SECONDS}s)")
            
    proc.stdin.close()
    proc.wait()
    
    print(f"[3/3] Output video created successfully at: {output_mp4}")
    if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 100000:
        size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"Verified: File size is {size_mb:.2f} MB")
        return True
    else:
        raise RuntimeError("Video render failed")


if __name__ == "__main__":
    out_video = "/Users/xu.liu9/projects/fun/meme-workspace/super_naiwa_bros_16bit.mp4"
    render_mario_video(out_video)
