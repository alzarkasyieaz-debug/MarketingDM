"""Self-generated (royalty-free) Islamic-style instrumental bed.

Oud-like plucked melody (Karplus-Strong) in maqam Hijaz on D, with risha tremolo on long notes,
a soft drone (D + A), a daf frame-drum rhythm in the energetic sections, and a stereo hall reverb.
Returns a stereo float array (N, 2), peak-normalised.
"""
import numpy as np

SR = 48000
BPM = 72
BEAT = 60 / BPM

# maqam Hijaz on D: D Eb F# G A Bb C D (two octaves, index 0 = D3)
HIJAZ = [146.83, 155.56, 185.00, 196.00, 220.00, 233.08, 261.63,
         293.66, 311.13, 369.99, 392.00, 440.00, 466.16, 523.25, 587.33]

# phrases: (scale index, beats). Upper register (7+) for the melody.
PHRASES = [
    [(11, 1), (10, .5), (9, .5), (8, 1), (7, 3)],
    [(7, .5), (8, .5), (9, 1), (10, .5), (11, .5), (12, 1), (11, 2)],
    [(14, 1), (13, .5), (12, .5), (11, 1), (10, .5), (9, .5), (8, 1), (7, 3)],
    [(9, .5), (10, .5), (11, 1), (11, .5), (12, .5), (11, .5), (10, .5), (9, 1), (8, .5), (7, 1.5)],
    [(11, 2), (12, .5), (11, .5), (10, 1), (9, 2)],
    [(9, .5), (8, .5), (9, .5), (10, .5), (11, 1), (10, .5), (9, .5), (8, 1), (7, 3)],
]

rng = np.random.default_rng(11)

def pluck(f, dur, vel=1.0, bright=0.5):
    """Karplus-Strong string, vectorised per period."""
    n = int(dur * SR)
    P = max(2, int(round(SR / f)))
    exc = rng.uniform(-1, 1, P)
    k = int(2 + (1 - bright) * 6)
    exc = np.convolve(exc, np.ones(k) / k, "same")          # softer attack (oud, not steel)
    out = np.zeros(n + P + 1)
    out[:P] = exc
    decay = 0.996 ** (440 / f)                                # lower strings ring longer
    i = P
    while i < n:
        j = min(i + P, n)
        prev = out[i - P:j - P]
        prev1 = out[i - P - 1:j - P - 1] if i - P - 1 >= 0 else np.concatenate([[0], out[i - P:j - P - 1]])
        out[i:j] = decay * 0.5 * (prev + prev1)
        i = j
    y = out[:n]
    env = np.ones(n); r = min(n, int(0.08 * SR)); env[-r:] = np.linspace(1, 0, r)
    body = np.convolve(y, [0.6, 0.3, 0.1], "same")           # a touch of body warmth
    return body * env * vel

def drone(N):
    t = np.arange(N) / SR
    sw = 0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t)
    d = (np.sin(2 * np.pi * 73.42 * t) + 0.5 * np.sin(2 * np.pi * 146.83 * t)
         + 0.35 * np.sin(2 * np.pi * 110.0 * t) + 0.12 * np.sin(2 * np.pi * 220.0 * t + 1))
    return d * sw

def daf_dum():
    n = int(0.45 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (62 + 40 * np.exp(-t * 25)) * t) * np.exp(-t * 8)
    skin = rng.standard_normal(n) * np.exp(-t * 40) * 0.25
    skin = np.convolve(skin, np.ones(20) / 20, "same")
    return body + skin

def daf_tek():
    n = int(0.12 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n); x = x - np.convolve(x, np.ones(6) / 6, "same")   # crude highpass
    jingle = np.sin(2 * np.pi * 5200 * t) * 0.15 + np.sin(2 * np.pi * 7300 * t) * 0.1
    return (x * 0.5 + jingle) * np.exp(-t * 45)

def reverb(x, seconds=2.4, decay=0.55, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / decay)
    ir = np.convolve(ir, np.ones(8) / 8, "same"); ir[0] = 0
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]

def compose(total, sections):
    """sections: list of (t0, t1, mode) with mode in {'sparse','full','calm','end'}."""
    N = int(total * SR)
    mel = np.zeros(N); perc = np.zeros(N)
    def put(buf, clip, t, g, pan=0.0):
        s = int(t * SR)
        if s >= N: return
        c = clip[:N - s]; buf[s:s + len(c)] += c * g
    pi = 0
    for (t0, t1, mode) in sections:
        t = t0
        while t < t1 - 0.5:
            ph = PHRASES[pi % len(PHRASES)]; pi += 1
            for (deg, b) in ph:
                d = b * BEAT
                if t >= t1 - 0.2: break
                f = HIJAZ[deg]
                vel = {"sparse": 0.55, "full": 0.85, "calm": 0.6, "end": 0.8}[mode]
                if b >= 2 and mode != "sparse":                 # risha tremolo on long notes
                    k = 0; tt = t
                    while tt < t + d * 0.9:
                        put(mel, pluck(f, 0.5, vel * (0.75 if k else 1.0)), tt, 1.0); tt += 0.11; k += 1
                else:
                    put(mel, pluck(f, max(0.6, d * 1.6), vel), t, 1.0)
                    if mode in ("full", "end") and deg in (7, 11):  # octave support on strong tones
                        put(mel, pluck(HIJAZ[deg - 7], max(0.8, d * 2), vel * 0.45, 0.3), t, 1.0)
                t += d
            if mode in ("sparse", "calm"):
                t += 2 * BEAT                                     # breathing space
        if mode in ("full", "end"):                               # maqsum-like daf: D T - T D - T -
            bar = 4 * BEAT; tb = t0
            pat = [(0, "D"), (1, "T"), (1.5, "T"), (2, "D"), (3, "T")]
            while tb < t1 - 0.2:
                for (o, kind) in pat:
                    tt = tb + o * BEAT
                    if tt < t1:
                        put(perc, daf_dum() if kind == "D" else daf_tek(), tt, 0.9 if kind == "D" else 0.45)
                tb += bar
    dr = drone(N) * 0.18
    melL = reverb(mel, seed=1) * 0.55 + mel * 0.8
    melR = reverb(mel, seed=2) * 0.55 + np.concatenate([np.zeros(int(0.012 * SR)), mel])[:N] * 0.8
    percR = reverb(perc, 1.2, 0.3, seed=3) * 0.3
    L = melL + dr + perc * 0.6 + percR
    R = melR + dr + perc * 0.6 + percR
    st = np.stack([L, R], 1)
    return st / np.abs(st).max()
