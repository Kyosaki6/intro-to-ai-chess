import struct
import math
import wave as wav_module


def make_wav(filename, freq, duration, vol=0.3):
    sr = 22050
    n = int(sr * duration)
    with wav_module.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for i in range(n):
            t = i / sr
            v = int(vol * 32767 * math.sin(2 * math.pi * freq * t))
            f.writeframes(struct.pack('<h', v))


def make_background_wav(filename, sr=22050, duration=10.0):
    n = int(sr * duration)
    freqs = [(130.81, 0.12), (164.81, 0.08), (196.00, 0.10),
             (261.63, 0.06), (329.63, 0.04), (392.00, 0.05)]
    fade = 0.3
    with wav_module.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        for i in range(n):
            t = i / sr
            env = 1.0
            if t < fade:
                env = t / fade
            elif t > duration - fade:
                env = (duration - t) / fade
            sample = sum(vol * math.sin(2 * math.pi * freq * t) for freq, vol in freqs)
            sample *= env * 0.5
            sample = max(-1, min(1, sample))
            f.writeframes(struct.pack('<h', int(sample * 32767 * 0.4)))
