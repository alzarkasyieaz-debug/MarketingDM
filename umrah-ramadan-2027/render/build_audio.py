"""Step 2: cleaned voice + self-synthesised ambient pad (royalty-free) + SFX, with voice ducking -> mix.wav

The pad is a placeholder bed generated here (no third-party music). Replace with a licensed
Islamic cinematic instrumental / nasyid track in CapCut if desired (keep ducking ~ -20 dB under voice).
"""
import os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from timeline import MASTER, OUT, VOICE, TOTAL, INTER, END, seg_starts

SR = 48000
N = int(TOTAL * SR)
rng = np.random.default_rng(7)

def read_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels()).mean(1)

def env_ad(n, a, d):
    e = np.ones(n)
    ai, di = int(a * SR), int(d * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if di: e[-di:] *= np.linspace(1, 0, di)
    return e

def voice_track():
    v = np.zeros(N)
    for i, (m0, m1, t0) in enumerate(VOICE):
        p = f"{OUT}/voice{i}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(m0), "-t", str(m1 - m0), "-i", MASTER, "-vn",
                        "-af", "highpass=f=80,lowpass=f=12000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
                               "loudnorm=I=-16:TP=-2:LRA=9",
                        "-ar", str(SR), "-ac", "1", p], check=True)
        a = read_wav(p)
        a *= env_ad(len(a), 0.04, 0.25)
        s = int(t0 * SR)
        a = a[: N - s]
        v[s:s + len(a)] += a
    return v

def pad():
    # Dm - Bb - F - C (slow, 6 s per chord), soft sines with slow attack/release
    chords = [[146.83, 174.61, 220.0, 293.66], [116.54, 146.83, 174.61, 233.08],
              [130.81, 174.61, 220.0, 261.63], [130.81, 164.81, 196.0, 261.63]]
    out = np.zeros(N)
    t = np.arange(N) / SR
    L = 6.0
    k = 0
    start = 0.0
    while start < TOTAL:
        c = chords[k % 4]
        s0 = int(max(0, start - 1.5) * SR); s1 = min(N, int((start + L + 1.5) * SR))
        tt = t[s0:s1]
        seg = np.zeros(s1 - s0)
        for j, f in enumerate(c):
            for det in (-0.6, 0.6):
                seg += np.sin(2 * np.pi * (f + det) * tt + j) * (0.22 if j else 0.3)
            seg += 0.05 * np.sin(2 * np.pi * 2 * f * tt)              # gentle shimmer
        seg *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * tt)              # slow swell
        e = np.ones(len(seg)); r = int(1.5 * SR)
        e[:r] = np.linspace(0, 1, r) ** 2; e[-r:] = np.linspace(1, 0, r) ** 2
        out[s0:s1] += seg * e
        start += L; k += 1
    drone = 0.35 * np.sin(2 * np.pi * 73.42 * t) + 0.15 * np.sin(2 * np.pi * 36.71 * t)
    out = out + drone
    return out / np.abs(out).max()

def pulse(t0, t1, bpm=80):
    out = np.zeros(N)
    beat = 60 / bpm
    n = int(0.5 * SR); tt = np.arange(n) / SR
    kick = np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    t = t0
    while t < t1:
        s = int(t * SR); out[s:s + n] += kick[: N - s] if s + n > N else kick
        t += beat
    return out

def impact():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 90 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.2)
    noise = rng.standard_normal(n) * np.exp(-tt * 18) * 0.25
    noise = np.convolve(noise, np.ones(12) / 12, "same")
    return (boom + noise) / 1.1

def whoosh(d=0.7):
    n = int(d * SR); tt = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    out = np.zeros(n); y = 0.0
    a = 0.02 + 0.25 * np.sin(np.pi * tt)            # moving one-pole lowpass = sweep
    for i in range(n):
        y += a[i] * (x[i] - y); out[i] = y
    return out * np.sin(np.pi * tt) ** 2 * 1.6

def riser(d=2.0):
    n = int(d * SR); tt = np.arange(n) / SR
    f = 200 * (8 ** (tt / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    x = rng.standard_normal(n); y = np.zeros(n); acc = 0.0
    for i in range(n):
        acc += (0.01 + 0.3 * tt[i] / d) * (x[i] - acc); y[i] = acc
    return (tone + y * 1.2) * (tt / d) ** 2

def sparkle():
    n = int(1.0 * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    for k, f in enumerate([2093, 2637, 3136, 4186]):
        s = int(k * 0.06 * SR)
        out[s:] += np.sin(2 * np.pi * f * tt[: n - s]) * np.exp(-tt[: n - s] * 7) * 0.25
    return out

def place(buf, clip, t, g):
    s = int(t * SR)
    if s >= N: return
    c = clip[: N - s]
    buf[s:s + len(c)] += c * g

def main():
    v = voice_track()
    music = pad()
    music += 0.5 * pulse(INTER[0], INTER[1]) + 0.35 * pulse(52.2, 80.7)
    # music level curve (dB): base under voice handled by ducking
    lvl = np.full(N, -14.0)
    t = np.arange(N) / SR
    lvl[(t >= INTER[0]) & (t < INTER[1])] = -9.0
    lvl[t >= END[0]] = -8.0
    lvl[t > TOTAL - 1.5] -= np.linspace(0, 40, (t > TOTAL - 1.5).sum())
    # ducking from voice envelope
    win = int(0.05 * SR)
    ve = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, "same"))
    act = (ve > 0.02).astype(float)
    sm = int(0.25 * SR)
    act = np.convolve(act, np.ones(sm) / sm, "same")
    duck_db = -12.0 * np.clip(act * 1.5, 0, 1)
    music *= 10 ** ((lvl + duck_db) / 20)

    sfx = np.zeros(N)
    for tt in (0.0, 33.3, 48.9, 52.2, END[0]):
        place(sfx, impact(), tt, 0.55)
    cuts = seg_starts()
    for c in cuts[1:]:
        if min(abs(c - x) for x in (33.3, 52.2, END[0])) > 0.3:
            place(sfx, whoosh(), c - 0.35, 0.22)
    place(sfx, riser(), INTER[0] - 2.0, 0.35)
    place(sfx, riser(), END[0] - 2.0, 0.35)
    for tt in (59.4, 62.5, 63.8, 68.8):
        place(sfx, sparkle(), tt, 0.35)

    mix = v * 0.9 + music + sfx
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    st = np.stack([mix, mix], 1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    raw = f"{OUT}/mix_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-ar", str(SR), f"{OUT}/mix.wav"], check=True)
    print("audio ok")

if __name__ == "__main__":
    main()
