"""
Authentic 8-bit / 16-bit Chiptune Audio Synthesizer.
Synthesizes square waves, triangle bass, retro noise percussion, and retro game SFX.
Outputs standard 44.1kHz 16-bit WAV audio.
"""

import numpy as np
import wave
import struct

SAMPLE_RATE = 44100

def square_wave(freq: float, duration: float, duty: float = 0.5, volume: float = 0.5) -> np.ndarray:
    """Generates a retro square/pulse wave."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    phase = (t * freq) % 1.0
    wave = np.where(phase < duty, 1.0, -1.0) * volume
    return wave

def triangle_wave(freq: float, duration: float, volume: float = 0.5) -> np.ndarray:
    """Generates a smooth retro triangle wave (NES style bass)."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    phase = (t * freq) % 1.0
    wave = (2.0 * np.abs(2.0 * (phase - np.floor(phase + 0.5))) - 1.0) * volume
    return wave

def noise_burst(duration: float, volume: float = 0.3, decay: bool = True) -> np.ndarray:
    """Generates 8-bit pseudo-random noise burst for percussion and skid."""
    n_samples = int(SAMPLE_RATE * duration)
    # 8-bit stepped random values
    noise = np.random.choice([-1.0, -0.5, 0.0, 0.5, 1.0], size=n_samples)
    if decay:
        env = np.linspace(1.0, 0.0, n_samples)**2
        noise = noise * env
    return noise * volume

def pitch_slide_square(f_start: float, f_end: float, duration: float, volume: float = 0.5) -> np.ndarray:
    """Frequency-modulated square wave for slides, chirps, and laughing vibrato."""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    freqs = np.linspace(f_start, f_end, n_samples)
    phase = np.cumsum(freqs) / SAMPLE_RATE
    wave = np.where((phase % 1.0) < 0.5, 1.0, -1.0) * volume
    env = np.linspace(1.0, 0.2, n_samples)
    return wave * env

def apply_envelope(signal: np.ndarray, attack: float = 0.01, decay: float = 0.05, sustain: float = 0.7, release: float = 0.05) -> np.ndarray:
    """ADSR envelope for clean retro note articulation."""
    n_total = len(signal)
    n_att = int(attack * SAMPLE_RATE)
    n_dec = int(decay * SAMPLE_RATE)
    n_rel = int(release * SAMPLE_RATE)
    n_sus = max(0, n_total - n_att - n_dec - n_rel)
    
    env = []
    if n_att > 0:
        env.append(np.linspace(0.0, 1.0, n_att))
    if n_dec > 0:
        env.append(np.linspace(1.0, sustain, n_dec))
    if n_sus > 0:
        env.append(np.full(n_sus, sustain))
    if n_rel > 0:
        env.append(np.linspace(sustain, 0.0, n_rel))
        
    full_env = np.concatenate(env)
    if len(full_env) < n_total:
        full_env = np.pad(full_env, (0, n_total - len(full_env)))
    else:
        full_env = full_env[:n_total]
        
    return signal * full_env

def add_track_at(master: np.ndarray, clip: np.ndarray, start_time: float, master_vol: float = 1.0):
    start_idx = int(start_time * SAMPLE_RATE)
    end_idx = min(len(master), start_idx + len(clip))
    if start_idx < len(master):
        clip_slice = clip[:end_idx - start_idx] * master_vol
        master[start_idx:end_idx] += clip_slice


class ChiptuneSoundtrack:
    """Builds the complete 20.0s 8-bit soundtrack and SFX."""
    
    @classmethod
    def generate_full_soundtrack(cls, total_duration: float = 20.0) -> np.ndarray:
        n_samples = int(SAMPLE_RATE * total_duration)
        master_left = np.zeros(n_samples, dtype=np.float32)
        master_right = np.zeros(n_samples, dtype=np.float32)
        
        # Note frequencies (Hz)
        C3, D3, E3, F3, G3, A3, B3 = 130.81, 146.83, 164.81, 174.61, 196.00, 220.00, 246.94
        C4, D4, E4, F4, G4, A4, B4 = 261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88
        C5, D5, E5, F5, G5, A5, B5 = 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77
        C6, D6, E6 = 1046.50, 1174.66, 1318.51
        
        # ----------------------------------------------------
        # SECTION 1: Walking Groove (0.0s to 7.4s)
        # ----------------------------------------------------
        beat_len = 0.28 # ~107 BPM
        
        # Bassline (Triangle wave)
        bass_notes = [C3, C3, G3, C3,  F3, F3, C3, F3,  G3, G3, D3, G3,  C3, E3, G3, C4]
        t = 0.0
        idx = 0
        while t < 7.2:
            freq = bass_notes[idx % len(bass_notes)]
            note = triangle_wave(freq, beat_len * 0.9, volume=0.35)
            note = apply_envelope(note, attack=0.01, decay=0.05, sustain=0.8, release=0.05)
            add_track_at(master_left, note, t, 0.8)
            add_track_at(master_right, note, t, 0.8)
            
            # Percussion: hi-hat on every beat, snare on offbeat
            hat = noise_burst(0.04, volume=0.15)
            add_track_at(master_left, hat, t, 0.6)
            add_track_at(master_right, hat, t, 0.6)
            if idx % 2 == 1:
                snare = noise_burst(0.09, volume=0.25)
                add_track_at(master_left, snare, t, 0.9)
                add_track_at(master_right, snare, t, 0.9)
                
            t += beat_len
            idx += 1
            
        # Melody (Pulse wave 25%)
        melody_events = [
            (0.0, E4, beat_len), (0.28, G4, beat_len), (0.56, C5, beat_len * 1.5),
            (1.12, D5, beat_len), (1.40, C5, beat_len), (1.68, A4, beat_len * 1.5),
            (2.24, G4, beat_len), (2.52, A4, beat_len), (2.80, C5, beat_len), (3.08, D5, beat_len),
            (3.36, E5, beat_len * 2),
            (4.20, G5, beat_len), (4.48, E5, beat_len), (4.76, D5, beat_len), (5.04, C5, beat_len * 1.5),
            (5.60, A4, beat_len), (5.88, C5, beat_len), (6.16, D5, beat_len), (6.44, C5, beat_len * 2)
        ]
        for start, freq, dur in melody_events:
            if start < 7.2:
                lead = square_wave(freq, dur * 0.85, duty=0.25, volume=0.28)
                lead = apply_envelope(lead, attack=0.01, decay=0.04, sustain=0.7, release=0.05)
                add_track_at(master_left, lead, start, 0.9)
                add_track_at(master_right, lead, start, 0.7) # slight pan
                
        # Naiwa walking footsteps (cute tap-tap SFX)
        for step_t in np.arange(0.2, 7.2, 0.35):
            foot_sfx = square_wave(440.0, 0.03, duty=0.5, volume=0.18)
            foot_sfx = foot_sfx * np.linspace(1.0, 0.1, len(foot_sfx))
            add_track_at(master_left, foot_sfx, step_t, 0.8)
            add_track_at(master_right, foot_sfx, step_t, 0.8)

        # ----------------------------------------------------
        # SECTION 2: Sudden Stop & Alert (7.5s - 9.0s)
        # ----------------------------------------------------
        # Skid sound (skidding stop noise + pitch drop)
        skid_noise = noise_burst(0.28, volume=0.35)
        skid_pitch = pitch_slide_square(320.0, 90.0, 0.28, volume=0.3)
        skid_total = (skid_noise + skid_pitch) * 0.5
        add_track_at(master_left, skid_total, 7.5, 1.0)
        add_track_at(master_right, skid_total, 7.5, 1.0)
        
        # Metal "!" Alert Chirp (at 7.8s)
        alert1 = square_wave(1320.0, 0.08, duty=0.5, volume=0.45)
        alert2 = square_wave(1760.0, 0.18, duty=0.5, volume=0.55)
        add_track_at(master_left, alert1, 7.8, 1.0)
        add_track_at(master_right, alert1, 7.8, 1.0)
        add_track_at(master_left, alert2, 7.86, 1.0)
        add_track_at(master_right, alert2, 7.86, 1.0)
        
        # Suspense low drone (7.9s - 9.0s)
        drone = triangle_wave(73.42, 1.1, volume=0.3) # D2 drone
        add_track_at(master_left, drone, 7.9, 0.7)
        add_track_at(master_right, drone, 7.9, 0.7)

        # ----------------------------------------------------
        # SECTION 3: Side-Eye Suspicious Close-Up (9.0s - 12.0s)
        # ----------------------------------------------------
        # Scene transition Whoosh at 9.0s
        trans_whoosh = noise_burst(0.25, volume=0.25) * np.linspace(0.1, 1.0, int(0.25 * SAMPLE_RATE))
        add_track_at(master_left, trans_whoosh, 8.95, 0.8)
        add_track_at(master_right, trans_whoosh, 8.95, 0.8)
        
        # Side-eye comical slide whistle (Pitch bend from 500Hz up to 980Hz and down)
        slide_up = pitch_slide_square(420.0, 920.0, 0.45, volume=0.32)
        add_track_at(master_left, slide_up, 9.4, 0.9)
        add_track_at(master_right, slide_up, 9.4, 0.7)
        
        # Subtle comical ticking / eye pupil moving sound
        pupil_tick1 = square_wave(880.0, 0.04, duty=0.5, volume=0.25)
        pupil_tick2 = square_wave(1174.0, 0.06, duty=0.5, volume=0.30)
        add_track_at(master_right, pupil_tick1, 9.9, 1.0)
        add_track_at(master_right, pupil_tick2, 10.1, 1.0)
        
        # Hesitant funny notes
        hesitant_notes = [(10.5, F4, 0.15), (10.8, F4, 0.15), (11.2, G4, 0.25), (11.5, B4, 0.3)]
        for st, fq, dur in hesitant_notes:
            sn = square_wave(fq, dur, duty=0.25, volume=0.25)
            sn = apply_envelope(sn, attack=0.01, decay=0.05, sustain=0.5, release=0.05)
            add_track_at(master_left, sn, st, 0.8)
            add_track_at(master_right, sn, st, 0.8)

        # ----------------------------------------------------
        # SECTION 4: Holding Belly Burst of Laughter! (12.0s - 18.5s)
        # ----------------------------------------------------
        # Laughter explosion hit at 12.0s
        hit_sfx = noise_burst(0.2, volume=0.4) + square_wave(261.63, 0.2, duty=0.5, volume=0.4)
        add_track_at(master_left, hit_sfx, 12.0, 1.0)
        add_track_at(master_right, hit_sfx, 12.0, 1.0)
        
        # Synthesized 8-bit Naiwa Laughing SFX (Ha-Ha-Ha-Ha bursts!)
        # Fast repeating arpeggios simulating belly laughs
        laugh_starts = [12.1, 12.6, 13.2, 13.8, 14.5, 15.2, 15.9, 16.6, 17.3, 17.9]
        for l_t in laugh_starts:
            # 4 rapid staccato syllables per laugh pulse: "HA-HA-HA-HA!"
            for i, pitch in enumerate([659.25, 783.99, 987.77, 880.00]):
                syllable_t = l_t + i * 0.08
                syl = square_wave(pitch, 0.06, duty=0.5, volume=0.35)
                syl = apply_envelope(syl, attack=0.005, decay=0.02, sustain=0.4, release=0.01)
                # pan alternating left and right for chaotic stereo laugh
                pan_l = 0.9 if i % 2 == 0 else 0.5
                pan_r = 0.5 if i % 2 == 0 else 0.9
                add_track_at(master_left, syl, syllable_t, pan_l)
                add_track_at(master_right, syl, syllable_t, pan_r)
                
            # Belly slap / bounce sound
            slap = square_wave(180.0, 0.05, duty=0.5, volume=0.25)
            add_track_at(master_left, slap, l_t, 0.7)
            add_track_at(master_right, slap, l_t, 0.7)
            
        # Joyful, energetic Party Chiptune BGM underneath the laughter
        fast_beat = 0.22 # ~136 BPM
        t_laugh = 12.2
        idx_l = 0
        party_bass = [C3, G3, A3, E3, F3, C3, F3, G3]
        while t_laugh < 18.4:
            # energetic bass
            fb = triangle_wave(party_bass[idx_l % len(party_bass)], fast_beat * 0.85, volume=0.4)
            add_track_at(master_left, fb, t_laugh, 0.8)
            add_track_at(master_right, fb, t_laugh, 0.8)
            
            # upbeat percussion
            if idx_l % 2 == 0:
                kick = square_wave(85.0, 0.08, duty=0.5, volume=0.3)
                add_track_at(master_left, kick, t_laugh, 0.9)
                add_track_at(master_right, kick, t_laugh, 0.9)
            else:
                snr = noise_burst(0.08, volume=0.28)
                add_track_at(master_left, snr, t_laugh, 0.9)
                add_track_at(master_right, snr, t_laugh, 0.9)
                
            t_laugh += fast_beat
            idx_l += 1

        # ----------------------------------------------------
        # SECTION 5: Outro & Stage Clear Fanfare (18.5s - 20.0s)
        # ----------------------------------------------------
        fanfare = [
            (18.5, G4, 0.12), (18.65, C5, 0.12), (18.8, E5, 0.12),
            (18.95, G5, 0.22), (19.2, E5, 0.15), (19.4, C6, 0.45)
        ]
        for st, fq, dur in fanfare:
            fn = square_wave(fq, dur, duty=0.5, volume=0.32)
            fn = apply_envelope(fn, attack=0.01, decay=0.05, sustain=0.8, release=0.05)
            add_track_at(master_left, fn, st, 0.85)
            add_track_at(master_right, fn, st, 0.85)
            
        # Final fade out on master to prevent any clipping/pop
        fade_start = int(19.4 * SAMPLE_RATE)
        fade_len = n_samples - fade_start
        if fade_len > 0:
            fade_curve = np.linspace(1.0, 0.0, fade_len)**1.5
            master_left[fade_start:] *= fade_curve
            master_right[fade_start:] *= fade_curve
            
        # Normalize and clamp to 16-bit PCM
        max_peak = max(np.max(np.abs(master_left)), np.max(np.abs(master_right)), 0.01)
        scale = 0.92 / max_peak
        master_left = np.clip(master_left * scale, -1.0, 1.0)
        master_right = np.clip(master_right * scale, -1.0, 1.0)
        
        # Interleave stereo 16-bit
        left_int = (master_left * 32767).astype(np.int16)
        right_int = (master_right * 32767).astype(np.int16)
        stereo_pcm = np.empty((n_samples * 2,), dtype=np.int16)
        stereo_pcm[0::2] = left_int
        stereo_pcm[1::2] = right_int
        
        return stereo_pcm

    @classmethod
    def save_wav(cls, filepath: str, duration: float = 20.0):
        pcm_data = cls.generate_full_soundtrack(duration)
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(2)      # Stereo
            wav_file.setsampwidth(2)      # 16-bit
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(pcm_data.tobytes())
        print(f"[Soundtrack] Saved 8-bit audio to {filepath} ({duration}s)")
