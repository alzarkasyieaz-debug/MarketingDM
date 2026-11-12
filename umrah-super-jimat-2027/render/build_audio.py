"""Audio: cleaned original voice + self-generated Islamic instrumental (royalty-free) + SFX + ducking -> mix.wav,
then mux with the silent picture -> final MP4."""
import os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from timeline import MASTER, WORK, VOICE, TOTAL, END0, HOOK, o
from islamic_music import compose

SR = 48000
N = int(TOTAL * SR)
rng = np.random.default_rng(7)
OUTV = os.environ.get("OUTV", f"{WORK}/video_silent.mp4")
FINAL = os.environ.get("FINAL", f"{WORK}/DM_UmrahSuperJimat_9x16.mp4")


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


def voice_track():
    v = np.zeros(N)
    for i, (m0, m1, t0) in enumerate(VOICE):
        p = f"{WORK}/voice{i}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(m0), "-t", str(m1 - m0), "-i", MASTER, "-vn",
                        "-af", "highpass=f=80,lowpass=f=12000,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
                               "loudnorm=I=-16:TP=-2:LRA=9",
                        "-ar", str(SR), "-ac", "1", p], check=True)
        a = read_wav(p); a = a * env_ad(len(a), 0.03, 0.08)
        s = int(t0 * SR); a = a[: N - s]
        v[s:s + len(a)] += a
    return v


def main():
    v = voice_track()
    music = compose(TOTAL, [(0.0, o(20.75), "sparse"), (o(20.75), o(55.1), "full"), (o(55.1), o(63.3), "calm"),
                            (o(63.3), TOTAL, "end")])
    t = np.arange(N) / SR
    lvl = np.full(N, -15.0)
    lvl[t < HOOK] = -7.0
    lvl[t >= END0] = -6.0
    tail = t > TOTAL - 1.2
    lvl[tail] -= np.linspace(0, 40, tail.sum())
    win = int(0.05 * SR)
    ve = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, "same"))
    act = np.convolve((ve > 0.02).astype(float), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    music *= (10 ** ((lvl - 7.0 * np.clip(act * 1.5, 0, 1)) / 20))[:, None]

    sfx = np.zeros(N)
    # big impacts: hook, 3D title reveals, stamps
    for tt, g in [(0.0, 0.32), (HOOK + 0.05, 0.22), (o(14.85), 0.16), (o(20.8), 0.2), (o(31.3), 0.24),
                  (o(38.16), 0.2), (o(40.44), 0.14), (o(43.96), 0.2), (o(63.4), 0.22), (END0, 0.18)]:
        place(sfx, impact(), tt, g)
    for tt in [o(12.75) - 0.3, o(17.0) - 0.3, o(23.15) - 0.3, o(26.65) - 0.3, o(32.6) - 0.3, o(36.15) - 0.3,
               o(46.9) - 0.3, o(49.8) - 0.3, o(52.2) - 0.3, o(55.1) - 0.3, o(58.0) - 0.3, o(60.6) - 0.3,
               o(23.35), o(23.6), o(33.6), o(33.95), o(34.3)]:
        place(sfx, whoosh(), tt, 0.09)
    place(sfx, riser(1.8), o(20.75) - 1.8, 0.13)
    place(sfx, riser(1.8), o(63.3) - 1.8, 0.13)
    for tt in [o(21.9), o(28.84), o(31.4), o(52.4), o(64.0)]:
        place(sfx, sparkle(), tt, 0.13)

    st = music + (v * 0.92 + sfx)[:, None]
    st /= max(1.0, np.abs(st).max() / 0.95)
    raw = f"{WORK}/mix_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                    f"{WORK}/mix.wav"], check=True)
    if os.path.exists(OUTV):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUTV, "-i", f"{WORK}/mix.wav", "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", FINAL], check=True)
        print("final", FINAL)
    print("audio ok")


if __name__ == "__main__":
    main()
