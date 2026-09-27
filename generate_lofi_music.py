import math
import numpy as np
import wave

SAMPLE_RATE = 44100
DURATION = 32.0  # seconds
BPM = 85.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4

total_samples = int(SAMPLE_RATE * DURATION)
audio = np.zeros((total_samples, 2), dtype=np.float32)
t_array = np.linspace(0, DURATION, total_samples, endpoint=False)

# Chords (frequencies in Hz): Cmaj7, Am9, Fmaj7, G9
chords = [
    [261.63, 329.63, 392.00, 493.88],  # Cmaj7
    [220.00, 261.63, 329.63, 392.00, 493.88],  # Am9
    [174.61, 220.00, 261.63, 329.63],  # Fmaj7
    [196.00, 246.94, 293.66, 349.23, 440.00]   # G9
]

# Vinyl crackle background
np.random.seed(42)
vinyl = np.random.normal(0, 0.005, total_samples)
pops = (np.random.random(total_samples) > 0.9997).astype(np.float32) * np.random.uniform(0.03, 0.08, total_samples)
vinyl += pops

audio[:, 0] += vinyl
audio[:, 1] += vinyl

# Synthesize drums & chords over time
for i in range(total_samples):
    t = t_array[i]
    bar = int(t / BAR_DUR)
    bar_pos = t % BAR_DUR
    beat_pos = bar_pos % BEAT_DUR
    beat_num = int(bar_pos / BEAT_DUR)

    # 1. Warm Rhodes Chords
    chord_idx = bar % len(chords)
    chord_freqs = chords[chord_idx]
    chord_env = math.exp(-1.5 * beat_pos) + 0.25 * math.sin(math.pi * bar_pos / BAR_DUR)
    chord_val = 0.0
    for f in chord_freqs:
        chord_val += 0.08 * math.sin(2 * math.pi * f * t) + 0.02 * math.sin(4 * math.pi * f * t)
    chord_sig = chord_val * max(0.0, min(1.0, chord_env))
    audio[i, 0] += chord_sig
    audio[i, 1] += chord_sig * 0.9

    # 2. Sub-Bass
    root_freq = chord_freqs[0] / 2.0
    bass_env = math.exp(-1.2 * beat_pos)
    bass_sig = 0.16 * math.sin(2 * math.pi * root_freq * t) * bass_env
    audio[i, 0] += bass_sig
    audio[i, 1] += bass_sig

    # 3. Kick Drum
    if (beat_num == 0 and beat_pos < 0.15) or (beat_num == 2 and beat_pos > 0.45 and beat_pos < 0.6):
        sub_t = beat_pos if beat_num == 0 else (beat_pos - 0.5)
        kick_freq = 110.0 * math.exp(-25.0 * sub_t) + 42.0
        kick_env = math.exp(-12.0 * sub_t)
        kick_sig = 0.35 * math.sin(2 * math.pi * kick_freq * sub_t) * kick_env
        audio[i, 0] += kick_sig
        audio[i, 1] += kick_sig

    # 4. Snare Drum
    if beat_num in (1, 3) and beat_pos < 0.2:
        snare_env = math.exp(-22.0 * beat_pos)
        snare_noise = np.random.uniform(-0.12, 0.12) * snare_env
        snare_body = 0.14 * math.sin(2 * math.pi * 185.0 * beat_pos) * snare_env
        audio[i, 0] += snare_noise + snare_body
        audio[i, 1] += snare_noise + snare_body

    # 5. Hi-Hats
    eighth_pos = beat_pos % (BEAT_DUR / 2.0)
    if eighth_pos < 0.08:
        hat_env = math.exp(-45.0 * eighth_pos)
        hat_noise = np.random.uniform(-0.04, 0.04) * hat_env
        audio[i, 0] += hat_noise
        audio[i, 1] += hat_noise * 0.85

# Normalize
max_val = np.max(np.abs(audio))
if max_val > 0:
    audio = (audio / max_val) * 0.85

audio_int16 = (audio * 32767).astype(np.int16)
with wave.open("demo_videos/lofi_music.wav", "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_int16.tobytes())

print("Upbeat lo-fi track successfully generated: demo_videos/lofi_music.wav")
