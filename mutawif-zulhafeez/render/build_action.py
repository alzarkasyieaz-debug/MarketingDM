"""ACTION CINEMATIC trailer cut – testimoni jemaah, Mutawif Ustaz Zulhafeez (1080x1920, 30 fps).

Movie-trailer grammar: presents card, teaser montage, metallic intertitles, jemaah voices as voice-over on
slow-motion B-roll, freeze-frame character intros, tension build (lost jemaah at Masjid Quba), braam hits,
action montage of one-liners, film title card, CTA. Letterbox, teal-orange grade, grain, flares, shake.
All speech = the jemaah's own words (edl_testi.WORDS); only pauses are cut.

Usage: SRC_DIR=... OUT_DIR=... python3 build_action.py audio|video|report|preview T1,T2
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B
import build_testi as BT
from build import (W, H, FPS, SRC, OUT, F, GOLD, GOLD_L, NAVY, WHITE, clamp, ease_out, ease_io, ease_back,
                   set_alpha, scaled, paste_c, text_img, stack, glow_sprite, load_photo, cover, view, grade_photo,
                   rim_light, El, Fx, VideoSeg)
from build_testi import SyncSeg, Memory, floating_card, counter, S, ft, ph, ct
from build_gempak import SRCW
from edl_testi import M1, M2, M3

NAME = "DM_Testimoni_ACTION_UstazZulhafeez_9x16"
BAR_T, BAR_B = 190, 250                      # letterbox
ORANGE = (255, 150, 40)
HOT = (255, 210, 110)

# ================================================================== timeline
# ("card", id, dur, kind, args) | ("broll", id, dur, src, ss, speed, z0, z1, cx, cy)
# ("spk", id, src, a, b, z0, z1, cy) | ("vo", id, vsrc, a, b, bsrc, ss, speed, z0, z1, cx, cy)
TL = [
    ("card", "PRESENTS", 2.6, "inter", dict(lines=["DARUL MUBARAK", "TRAVEL & TOURS"], small="MEMPERSEMBAHKAN")),
    ("broll", "T1", 0.9, ft("IMG_2048.MOV"), 13.35, 0.5, 1.15, 1.25, 0.55, 0.42),
    ("broll", "T2", 0.6, ft("991cf9ec.mp4"), 1.0, 1.0, 1.20, 1.30, 0.5, 0.40),
    ("broll", "T3", 0.7, ft("IMG_2032.MOV"), 0.0, 0.25, 1.30, 1.40, 0.62, 0.45),
    ("broll", "T4", 0.6, ft("89b65111.mp4"), 0.4, 1.0, 1.20, 1.30, 0.45, 0.45),
    ("card", "IT1", 1.5, "inter", dict(lines=["SATU PERJALANAN"], small="KE TANAH SUCI")),
    ("vo", "VO1a", M2, 28.65, 31.75, ft("IMG_2031.MOV"), 0.0, 0.4, 1.35, 1.12, 0.5, 0.36),
    ("spk", "VO1b", M2, 32.75, 34.90, 1.18, 1.28, 0.27),
    ("card", "FZ1", 0.9, "freeze", dict(src=M2, t=34.85, z=1.28, cy=0.27, tag="JEMAAH", role="FIRST TIME UMRAH")),
    ("vo", "VO2", M2, 35.38, 37.66, ft("e6576e55.mp4"), 0.0, 0.6, 1.05, 1.18, 0.5, 0.5),
    ("spk", "VO3", M2, 37.66, 43.42, 1.05, 1.22, 0.27),
    ("card", "IT2", 1.4, "inter", dict(lines=["MASJID QUBA"], small="MADINAH")),
    ("spk", "VO4", M3, 21.25, 25.30, 1.05, 1.15, 0.30),
    ("spk", "VO5", M3, 28.50, 33.12, 1.10, 1.30, 0.30),
    ("card", "BLK", 0.45, "black", {}),
    ("spk", "VO6", M3, 33.14, 35.30, 1.20, 1.10, 0.30),
    ("spk", "Q1", M2, 1.75, 3.70, 1.10, 1.22, 0.27),
    ("spk", "Q2", M3, 11.80, 13.85, 1.15, 1.30, 0.29),
    ("spk", "Q3a", M1, 11.90, 13.60, 1.05, 1.15, 0.30),
    ("spk", "Q3b", M1, 14.95, 17.80, 1.20, 1.28, 0.28),
    ("spk", "Q4", M2, 61.95, 64.84, 1.12, 1.30, 0.27),
    ("spk", "Q5", M3, 67.05, 72.60, 1.05, 1.25, 0.30),
    ("card", "TITLE", 4.0, "title", {}),
    ("card", "TAG", 3.0, "inter", dict(lines=["SETIAP PERJALANAN UMRAH", "MENINGGALKAN", "SERIBU KENANGAN"], small=None, bg=ft("IMG_2031.MOV"))),
    ("card", "CTA", 4.2, "cta", {}),
]
T = {}; _t = 0.0
for e in TL:
    d = e[2] if e[0] in ("card", "broll") else e[4] - e[3]
    T[e[1]] = (_t, d, e); _t += d
TOTAL = round(_t, 2)
def tc(i): return T[i][0]
def te(i): return T[i][0] + T[i][1]
def at(i, s):
    t0, d, e = T[i]; a = e[3]; return t0 + (s - a)
def voice_specs():
    out = []
    for e in TL:
        if e[0] == "spk": out.append((tc(e[1]), e[2], e[3], e[4], e[1]))
        if e[0] == "vo": out.append((tc(e[1]), e[2], e[3], e[4], e[1]))
    return out

HITS = []          # (time, strength, kind) kind: braam|boom|hit
def hit(t, s=0.6, kind="hit"): HITS.append((t, s, kind))

# ================================================================== look
def metal_text(txt, size, font="serif", tracking=6, glow=True):
    f = F(font, size)
    base = text_img(txt, f, WHITE, shadow=False, tracking=tracking)
    a = np.asarray(base, np.float32)
    h = a.shape[0]; y = np.linspace(0, 1, h)[:, None]
    top = np.array([255, 244, 214], np.float32); mid = np.array([236, 182, 84], np.float32); bot = np.array([150, 92, 30], np.float32)
    g = np.where(y < 0.5, top * (1 - y * 2) + mid * (y * 2), mid * (1 - (y - 0.5) * 2) + bot * ((y - 0.5) * 2))
    a[..., :3] = g[:, None, :].repeat(a.shape[1], 1)
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    pad = 40
    out = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    if glow:
        gl = Image.new("RGBA", out.size, (0, 0, 0, 0)); gm = Image.new("RGBA", im.size, ORANGE + (0,)); gm.putalpha(im.getchannel("A"))
        gl.alpha_composite(gm, (pad, pad)); out = Image.alpha_composite(out, gl.filter(ImageFilter.GaussianBlur(16)))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0)); sm = Image.new("RGBA", im.size, (0, 0, 0, 200)); sm.putalpha(im.getchannel("A"))
    sh.alpha_composite(sm, (pad, pad + 5)); out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(6)))
    out.alpha_composite(im, (pad, pad))
    return out.crop(out.getbbox())

def teal_orange(a):
    """a float32 HxWx3 0..255 -> graded."""
    x = a / 255.0
    lum = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)[..., None]
    x = lum + (x - lum) * 0.85                                     # slight desat
    x = np.clip((x - 0.5) * 1.18 + 0.5, 0, 1)                      # contrast
    sh = (1 - lum) ** 2; hi = lum ** 2
    x = x + sh * np.array([-0.05, 0.03, 0.07]) + hi * np.array([0.08, 0.02, -0.07])
    return np.clip(x, 0, 1) * 255.0

GRAIN = None
def grain(i):
    global GRAIN
    if GRAIN is None:
        rng = np.random.default_rng(1)
        GRAIN = [rng.normal(0, 7.5, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) for _ in range(6)]
    return GRAIN[i % 6]

FLARE = None
def flare():
    global FLARE
    if FLARE is None:
        w, h = 1600, 120; y, x = np.mgrid[-h // 2:h // 2, -w // 2:w // 2].astype(np.float32)
        core = np.exp(-(y / 6) ** 2) * np.exp(-(np.abs(x) / 520) ** 1.2)
        halo = np.exp(-(x ** 2 + y ** 2) / (2 * 60 ** 2))
        al = np.clip(core * 1.0 + halo * 0.8, 0, 1)
        arr = np.zeros((h, w, 4), np.uint8); arr[..., 0] = 255; arr[..., 1] = 190; arr[..., 2] = 120; arr[..., 3] = (al * 255).astype(np.uint8)
        FLARE = Image.fromarray(arr, "RGBA")
    return FLARE

# ================================================================== cards
class Black:
    def __init__(self, t0, dur): self.t0, self.dur = t0, dur
    def frame(self, t, punch=0.0): return Image.new("RGB", (W, H), (0, 0, 0))

class Inter:
    """Black (or dim B-roll) intertitle with metallic serif text, slow push-in, embers."""
    def __init__(self, t0, dur, lines, small=None, bg=None):
        self.t0, self.dur = t0, dur
        self.lines = [metal_text(l, 92 if len(l) < 16 else 70) for l in lines]
        self.small = text_img(small, F("bold", 34), (220, 200, 170), shadow=False, tracking=14) if small else None
        self.bg = SyncSeg(t0, dur, bg, 0.0, 0.35, 1.25, 1.05, 0.5, 0.38) if bg else None
        self.emb = Embers(t0, n=40)
    def frame(self, t, punch=0.0):
        lt = t - self.t0
        if self.bg:
            a = np.asarray(self.bg.frame(t), np.float32) * 0.42
            c = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
        else:
            c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        self.emb.draw(c, t, 0.7)
        fade = clamp(lt / 0.35) * clamp((self.dur - lt) / 0.3)
        s = 1.0 + 0.05 * lt / self.dur
        y = H / 2 - (sum(l.height for l in self.lines) + 12 * (len(self.lines) - 1)) / 2 - (30 if self.small else 0)
        for i, l in enumerate(self.lines):
            li = clamp((lt - i * 0.35) / 0.35) if len(self.lines) > 1 else 1
            paste_c(c, set_alpha(scaled(l, s), fade * li), W / 2, y + l.height / 2); y += l.height + 12
        if self.small: paste_c(c, set_alpha(self.small, fade * clamp((lt - 0.3) / 0.3)), W / 2, y + 40)
        return c.convert("RGB")
    def close(self):
        if self.bg: self.bg.close()

class Freeze:
    """Action-movie character intro: frozen frame, desaturated, name tag slams in."""
    def __init__(self, t0, dur, src, t, z, cy, tag, role):
        self.t0, self.dur = t0, dur
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", S(src), "-frames:v", "1", "-vf",
                              f"scale={int(W * z)}:{int(H * z)}:force_original_aspect_ratio=increase,crop={int(W * z)}:{int(H * z)}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        im = Image.frombuffer("RGB", (int(W * z), int(H * z)), raw)
        self.img = view(im, z, z, 0.5, cy)
        g = ImageOps.grayscale(self.img).convert("RGB")
        self.gray = Image.blend(self.img, g, 0.75)
        self.tag = metal_text(tag, 110, "black", tracking=4)
        self.role = text_img(role, F("black", 44), WHITE, tracking=3)
    def frame(self, t, punch=0.0):
        lt = t - self.t0
        c = Image.blend(self.img, self.gray, clamp(lt / 0.1)).convert("RGBA")
        d = ImageDraw.Draw(c)
        e = ease_out(lt / 0.25); x = -700 * (1 - e)
        d.polygon([(x + 0, 1150), (x + 760, 1150), (x + 700, 1370), (x + 0, 1370)], fill=(0, 0, 0, 190))
        d.rectangle((x + 0, 1150, x + 14, 1370), fill=ORANGE)
        c.alpha_composite(self.tag, (int(x + 50), 1165))
        c.alpha_composite(self.role, (int(x + 56), 1165 + self.tag.height + 6))
        return c.convert("RGB")

class TitleCard:
    def __init__(self, t0, dur):
        self.t0, self.dur = t0, dur
        fg = Image.open(ct("IMG_9620.png")).convert("RGBA"); fg = fg.crop(fg.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
        rgb = grade_photo(fg.convert("RGB")).convert("RGBA"); rgb.putalpha(fg.getchannel("A"))
        self.fg = rim_light(rgb.resize((int(rgb.width * 1100 / rgb.height), 1100), Image.LANCZOS), col=ORANGE, r=30, a=0.9)
        self.name1 = metal_text("USTAZ", 120, "serif", tracking=20)
        self.name2 = metal_text("ZULHAFEEZ", 150, "serif", tracking=10)
        if self.name2.width > 1000: self.name2 = scaled(self.name2, 1000 / self.name2.width)
        self.sub = text_img("MUTAWIF  •  DARUL MUBARAK TRAVEL & TOURS", F("bold", 30), (230, 215, 190), shadow=False, tracking=4)
        self.emb = Embers(t0, n=70); self.halo = glow_sprite(520, ORANGE, 110)
    def frame(self, t, punch=0.0):
        lt = t - self.t0
        c = Image.new("RGBA", (W, H), (6, 6, 10, 255))
        paste_c(c, set_alpha(self.halo, clamp(lt / 0.5) * 0.9), W / 2, 820)
        fg = set_alpha(scaled(self.fg, 1.08 - 0.06 * ease_out(lt / self.dur)), clamp(lt / 0.6) * 0.95)
        paste_c(c, fg, W / 2, 1310 - fg.height / 2 + 30)
        self.emb.draw(c, t, 1.0)
        if lt > 0.25:
            s = 1 + 0.25 * (1 - ease_out((lt - 0.25) / 0.5)); a = clamp((lt - 0.25) / 0.3)
            paste_c(c, set_alpha(scaled(self.name1, s), a), W / 2, 1230)
        if lt > 0.5:
            s = 1 + 0.3 * (1 - ease_out((lt - 0.5) / 0.5)); a = clamp((lt - 0.5) / 0.3)
            paste_c(c, set_alpha(scaled(self.name2, s), a), W / 2, 1380)
        if lt > 1.1: paste_c(c, set_alpha(self.sub, clamp((lt - 1.1) / 0.4)), W / 2, 1500)
        return c.convert("RGB")

class CTA:
    def __init__(self, t0, dur):
        self.t0, self.dur = t0, dur
        logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
        self.badge = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        ImageDraw.Draw(self.badge).ellipse((0, 0, 259, 259), fill=(255, 255, 255, 250), outline=GOLD + (255,), width=6)
        self.badge.alpha_composite(logo.resize((216, 216), Image.LANCZOS), (22, 20))
        self.l1 = metal_text("NAK RASAI", 80, "black", tracking=4)
        self.l2 = metal_text("PENGALAMAN INI?", 86, "black", tracking=2)
        if self.l2.width > 980: self.l2 = scaled(self.l2, 980 / self.l2.width)
        bt = text_img("HUBUNGI KAMI", F("black", 56), (20, 10, 0), shadow=False, tracking=3)
        self.btn = B.rounded_card(bt.width + 120, bt.height + 50, 48, HOT, 255); self.btn.alpha_composite(bt, (34 + 60, 34 + 25))
        self.sub = text_img("untuk maklumat pakej umrah", F("semi", 40), WHITE)
        self.dm = text_img("DARUL MUBARAK TRAVEL & TOURS", F("bold", 34), (230, 215, 190), tracking=5)
        self.emb = Embers(t0, n=50); self.halo = glow_sprite(300, ORANGE, 120)
    def frame(self, t, punch=0.0):
        lt = t - self.t0; c = Image.new("RGBA", (W, H), (8, 6, 12, 255)); self.emb.draw(c, t, 0.8)
        paste_c(c, set_alpha(self.halo, clamp(lt / 0.4)), W / 2, 560)
        paste_c(c, set_alpha(scaled(self.badge, 0.7 + 0.3 * ease_back(lt / 0.4)), clamp(lt / 0.15)), W / 2, 560)
        paste_c(c, set_alpha(self.dm, clamp((lt - 0.3) / 0.3)), W / 2, 760)
        for i, (im, y) in enumerate([(self.l1, 930), (self.l2, 1040)]):
            l = lt - 0.5 - i * 0.2
            if l > 0: paste_c(c, set_alpha(scaled(im, 1 + 0.4 * (1 - ease_out(l / 0.2))), clamp(l / 0.12)), W / 2, y)
        if lt > 1.1: paste_c(c, set_alpha(scaled(self.btn, (0.6 + 0.4 * ease_back((lt - 1.1) / 0.4)) * (1 + 0.035 * math.sin(lt * 6))), clamp((lt - 1.1) / 0.15)), W / 2, 1230)
        if lt > 1.4: paste_c(c, set_alpha(self.sub, clamp((lt - 1.4) / 0.3)), W / 2, 1350)
        return c.convert("RGB")

class Embers:
    def __init__(self, t0, n=50, seed=11):
        rng = np.random.default_rng(seed); self.t0 = t0
        self.p = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 7), rng.uniform(80, 260), rng.uniform(0, 6.3), rng.uniform(0.4, 1.0)) for _ in range(n)]
        self.spr = {r: glow_sprite(r * 3, ORANGE) for r in range(2, 8)}
    def draw(self, c, t, k=1.0):
        lt = t - self.t0
        for (x, y, r, v, ph_, a) in self.p:
            yy = (y - v * lt) % (H + 40) - 20; xx = x + 30 * math.sin(lt * 1.5 + ph_)
            paste_c(c, set_alpha(self.spr[int(r)], a * k * (0.6 + 0.4 * math.sin(lt * 7 + ph_))), xx, yy)

# ================================================================== segments
def make_segments():
    segs, cuts = [], []
    for e in TL:
        t0, d, _ = T[e[1]]
        if e[0] == "card":
            k, a = e[3], e[4]
            seg = {"inter": lambda: Inter(t0, d, **a), "black": lambda: Black(t0, d), "title": lambda: TitleCard(t0, d),
                   "cta": lambda: CTA(t0, d), "freeze": lambda: Freeze(t0, d, **a)}[k]()
        elif e[0] == "broll":
            _, i, dur, src, ss, sp, z0, z1, cx, cy = e; seg = SyncSeg(t0, dur, src, ss, sp, z0, z1, cx, cy)
        elif e[0] == "spk":
            _, i, src, a_, b_, z0, z1, cy = e; seg = SyncSeg(t0, b_ - a_, S(src), a_, 1.0, z0, z1, 0.5, cy); seg.kind = "speaker"
        else:
            _, i, vs, a_, b_, bsrc, ss, sp, z0, z1, cx, cy = e; seg = SyncSeg(t0, b_ - a_, bsrc, ss, sp, z0, z1, cx, cy)
        seg.id = e[1]; segs.append(seg)
    def cut(seg): cuts.append(seg)
    # VO3 "berkat mutawif" -> Ustaz slow-mo character intro
    cut(SyncSeg(at("VO3", 39.90), 2.4, ft("IMG_2032.MOV"), 0.0, 0.23, 1.0, 1.16, 0.62, 0.45))
    cut(B.KenBurns(at("VO3", 39.90) + 2.4, te("VO3") - at("VO3", 39.90) - 2.4, ph("IMG_2177.jpg"), 1.05, 1.15, 0.5, 0.35))
    # VO4 "Masjid Quba" -> Quba night slow-mo
    cut(SyncSeg(at("VO4", 22.85), te("VO4") - at("VO4", 22.85), ft("IMG_2048.MOV"), 13.35, 0.5, 1.12, 1.26, 0.55, 0.45))
    # VO5 tension: flash cut-aways to Quba
    cut(SyncSeg(at("VO5", 30.45), 0.6, ft("IMG_2031.MOV"), 1.0, 0.6, 1.3, 1.4, 0.5, 0.40))
    cut(SyncSeg(at("VO5", 31.95), 0.5, ft("IMG_2048.MOV"), 2.0, 1.0, 1.5, 1.6, 0.4, 0.30))
    # VO6 "mutawif kita boleh cari" -> memory of Ustaz over Quba
    mv = SyncSeg(at("VO6", 34.20), te("VO6") - at("VO6", 34.20), ft("IMG_2031.MOV"), 0.0, 0.5, 1.25, 1.10, 0.5, 0.38)
    cut(Memory(mv.t0, mv.dur, mv, ct("IMG_2177.png")))
    # Q1 "mutawif" flash of Ustaz with jemaah
    cut(B.KenBurns(at("Q1", 1.80), 0.6, ph("IMG_3195.jpg"), 1.25, 1.35, 0.30, 0.45))
    return segs, cuts

# ================================================================== overlays
def slam(txt, size=130, font="black", y=None, x=W / 2, t0=0, t1=0, s=0.6, kind="hit"):
    im = metal_text(txt, size, font, tracking=4)
    if im.width > 960: im = scaled(im, 960 / im.width)
    hit(t0, s, kind)
    return El(t0, t1, im, x, y, "crash", 0.14, 0.12)

def char_tag(tag, role, y0=1110):
    tg = metal_text(tag, 92, "black", tracking=4); rl = text_img(role, F("black", 40), WHITE, tracking=3)
    def fn(c, lt, a):
        e = ease_out(lt / 0.25); x = -700 * (1 - e); d = ImageDraw.Draw(c)
        d.polygon([(x, y0), (x + 700, y0), (x + 650, y0 + 190), (x, y0 + 190)], fill=(0, 0, 0, int(180 * a)))
        d.rectangle((x, y0, x + 12, y0 + 190), fill=ORANGE + (int(255 * a),))
        c.alpha_composite(set_alpha(tg, a), (int(x + 44), y0 + 12)); c.alpha_composite(set_alpha(rl, a), (int(x + 50), y0 + 12 + tg.height + 4))
    return fn

class Subs:
    """Cinematic subtitles in the bottom letterbox bar."""
    def __init__(self):
        self.ch = []
        for (t0, src, a, b, i) in voice_specs():
            ws = [(t0 + (s - a), w) for s, w in SRCW[src] if a - 0.02 <= s < b - 0.05]
            cur = []
            for j, (tt, w) in enumerate(ws):
                nxt = ws[j + 1][0] if j + 1 < len(ws) else t0 + (b - a)
                cur.append((tt, min(nxt, tt + 0.9), w))
                if len(cur) >= 4 or w[-1] in ".,…?" or j + 1 == len(ws) or nxt - tt > 1.2: self.ch.append(cur); cur = []
        self.f = F("bold", 54); self._c = {}
    def img(self, ci, act):
        k = (ci, act)
        if k in self._c: return self._c[k]
        ch = self.ch[ci]; f = self.f; sp = f.getlength(" ")
        toks = [w for (_, _, w) in ch]; tw = sum(f.getlength(x) for x in toks) + sp * (len(toks) - 1)
        im = Image.new("RGBA", (int(tw) + 40, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
        for j, tk in enumerate(toks):
            d.text((x, 12), tk, font=f, fill=(HOT if j == act else (235, 235, 235)) + (255,)); x += f.getlength(tk) + sp
        if im.width > 1020: im = scaled(im, 1020 / im.width)
        self._c[k] = im; return im
    def draw(self, c, t):
        for ci, ch in enumerate(self.ch):
            t0, t1 = ch[0][0] - 0.05, ch[-1][1] + 0.12
            if ci + 1 < len(self.ch): t1 = min(t1, self.ch[ci + 1][0][0] - 0.03)
            if t0 <= t < t1:
                act = max([j for j, (wt, _, _) in enumerate(ch) if wt <= t] or [0])
                paste_c(c, self.img(ci, act), W / 2, H - BAR_B / 2); return

def overlays():
    E = []
    def add(*a, **k): E.append(El(*a, **k))
    def fx(*a, **k): E.append(Fx(*a, **k))
    Y = 1230
    hit(0.15, 0.8, "boom")
    for i in ("T1", "T2", "T3", "T4"): hit(tc(i), 0.5, "hit")
    hit(tc("IT1"), 1.0, "braam")
    E.append(slam("PALING SUCI", 140, y=Y, t0=at("VO1b", 33.36), t1=te("VO1b"), s=0.5))
    hit(tc("FZ1"), 0.7, "hit")
    E.append(slam("TAKUT", 170, y=Y, t0=at("VO2", 35.72), t1=te("VO2"), s=0.4))
    E.append(slam("BERKAT MUTAWIF", 120, y=Y, t0=at("VO3", 39.96), t1=at("VO3", 41.70), s=1.0, kind="braam"))
    fx(at("VO3", 40.75), at("VO3", 42.6), char_tag("USTAZ ZULHAFEEZ", "MUTAWIF  •  DARUL MUBARAK"), out=0.2)
    hit(tc("IT2"), 0.8, "boom")
    fx(tc("VO4") + 0.05, tc("VO4") + 1.9, char_tag("JEMAAH", "PAKEJ SUPER JIMAT", 260), out=0.2); hit(tc("VO4"), 0.5)
    E.append(slam("JEMAAH HILANG", 130, y=Y, t0=at("VO4", 21.34), t1=at("VO4", 22.8), s=0.7, kind="boom"))
    E.append(slam("TAK MASUK AKAL", 120, y=Y, t0=at("VO5", 29.85), t1=at("VO5", 30.45), s=0.6))
    E.append(slam("DIA ADA KAT MANA?", 110, y=Y, t0=at("VO5", 32.18), t1=te("VO5"), s=0.6))
    E.append(slam("BOLEH CARI!", 160, y=Y, t0=at("VO6", 34.70), t1=te("VO6"), s=1.0, kind="braam"))
    E.append(slam("SEMPOI!", 170, y=Y, t0=at("Q1", 2.90), t1=te("Q1"), s=0.7, kind="boom"))
    E.append(slam("KOMITMEN TERBAIK", 116, y=Y, t0=at("Q2", 12.34), t1=at("Q2", 13.40), s=0.6))
    E.append(slam("STEADY!", 170, y=Y, t0=at("Q2", 13.42), t1=te("Q2"), s=0.8, kind="boom"))
    fx(tc("Q3a") + 0.05, tc("Q3a") + 1.6, char_tag("JEMAAH", "PERTAMA KALI KE TANAH SUCI", 260), out=0.2); hit(tc("Q3a"), 0.5)
    fx(at("Q3b", 16.70), te("Q3b"), floating_card(ph("IMG_9620.jpg"), 230, 1050, 300, -7, None), out=0.15)
    E.append(slam("MUTAWIF YANG SAMA", 104, y=Y + 60, x=600, t0=at("Q3b", 16.78), t1=te("Q3b"), s=0.9, kind="boom"))
    fx(at("Q4", 63.55), te("Q4"), counter(100, "%", 1130), out=0.15); hit(at("Q4", 64.30), 0.9, "boom")
    fx(at("Q5", 68.20), at("Q5", 69.55), BT.cutout_reveal(ct("IMG_2177.png"), 800, 980), out=0.2); hit(at("Q5", 68.24), 0.8, "boom")
    E.append(slam("A LAH TERBAIK!", 140, y=Y, t0=at("Q5", 69.62), t1=at("Q5", 70.65), s=0.8, kind="boom"))
    for st, wd, x in [(70.70, "SEMPOI.", 200), (71.54, "PADU.", 520), (72.16, "BAHANG!", 840)]:
        im = metal_text(wd, 74, "black", tracking=2); hit(at("Q5", st), 0.7, "boom"); add(at("Q5", st), te("Q5"), im, x, Y, "crash", 0.14, 0.1)
    hit(tc("TITLE"), 1.0, "braam"); hit(tc("TITLE") + 0.5, 0.6, "boom"); hit(tc("CTA"), 0.8, "boom")
    E.append(Subs())
    return E

# ================================================================== render
def cut_list():
    return sorted({round(tc(e[1]), 3) for e in TL} | {0.0})

def render(times=None):
    HITS.clear()
    segs, cuts = make_segments(); ovl = overlays(); vig = B.vignette()
    CUTS = cut_list()[1:]
    big = [(t, s) for (t, s, k) in HITS]
    n = int(round(TOTAL * FPS)); frames = range(n) if times is None else [int(round(x * FPS)) for x in times]
    enc = None
    if times is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{OUT}/mix_action.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "256k", "-shortest",
                                "-movflags", "+faststart", f"{OUT}/{NAME}.mp4"], stdin=subprocess.PIPE)
    fl = flare()
    for fi in frames:
        t = fi / FPS
        base = [s for s in segs if s.t0 <= t + 1e-6][-1]
        cutseg = next((c for c in cuts if c.t0 <= t < c.t0 + c.dur), None)
        if cutseg is not None and isinstance(base, VideoSeg): base.frame(t)
        seg = cutseg or base
        for s in segs + cuts:
            if isinstance(s, VideoSeg) and s.proc and t > s.t0 + s.dur + 0.1: s.close()
            if isinstance(s, Inter) and t > s.t0 + s.dur + 0.1: s.close()
        # impact envelope
        imp = 0.0; hit_t = None
        for (ht, hs) in big:
            if 0 <= t - ht < 0.4:
                v = hs * math.exp(-(t - ht) * 9)
                if v > imp: imp, hit_t = v, ht
        frame = seg.frame(t, punch=0.07 * imp)
        a = np.asarray(frame, np.float32)
        a = teal_orange(a) * vig
        # flash on cuts / hits
        fl_amt = 0.0
        for c_ in CUTS:
            if 0 <= t - c_ < 0.1: fl_amt = max(fl_amt, 0.55 * (1 - (t - c_) / 0.1))
        if hit_t is not None and t - hit_t < 0.07: fl_amt = max(fl_amt, 0.8 * imp)
        if fl_amt > 0: a = a + (255 - a) * fl_amt
        # chromatic aberration on impact
        if imp > 0.25:
            k = int(10 * imp); a = a.copy(); a[..., 0] = np.roll(a[..., 0], k, 1); a[..., 2] = np.roll(a[..., 2], -k, 1)
        a = a + grain(fi)
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        if imp > 0.15: paste_c(c, set_alpha(fl, min(1, imp * 1.2)), W / 2, 700 + 300 * math.sin(hit_t * 3))
        for e in ovl:
            if not isinstance(e, Subs): e.draw(c, t)
        # shake
        if imp > 0.1:
            dx = 26 * imp * math.sin(t * 90); dy = 20 * imp * math.cos(t * 77)
            c = c.transform((W, H), Image.AFFINE, (1 / 1.04, 0, W * 0.02 - dx, 0, 1 / 1.04, H * 0.02 - dy), Image.BILINEAR)
        # letterbox + subtitles + watermark
        d = ImageDraw.Draw(c); d.rectangle((0, 0, W, BAR_T), fill=(0, 0, 0, 255)); d.rectangle((0, H - BAR_B, W, H), fill=(0, 0, 0, 255))
        ovl[-1].draw(c, t)
        if t > TOTAL - 0.7: c = Image.fromarray((np.asarray(c.convert("RGB"), np.float32) * clamp((TOTAL - t) / 0.7)).astype(np.uint8)).convert("RGBA")
        rgb = c.convert("RGB")
        if enc: enc.stdin.write(rgb.tobytes())
        else: rgb.save(f"{OUT}/aprev_{t:06.2f}.png"); print("preview", round(t, 2), flush=True)
        if enc and fi % 300 == 0: print(f"frame {fi}/{n}", flush=True)
    if enc: enc.stdin.close(); enc.wait(); print("video ok", f"{OUT}/{NAME}.mp4")

# ================================================================== audio (trailer sound design)
SR = 48000
def audio():
    HITS.clear(); overlays()
    import islamic_music as IM
    rng = np.random.default_rng(21); N = int(TOTAL * SR); tt = np.arange(N) / SR
    def place(buf, clip, t, g):
        s = int(t * SR)
        if 0 <= s < N: c = clip[:N - s]; buf[s:s + len(c)] += c * g
    # voices
    voice = np.zeros(N); gains = {}
    for src in {v[1] for v in voice_specs()}:
        v = B.read_audio(S(src), 0, 999, B.VOICE_AF); gains[src] = 0.16 / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9)
    for (t0, src, a, b, i) in voice_specs():
        v = B.read_audio(S(src), a, b - a, B.VOICE_AF) * gains[src]
        f = int(0.02 * SR); v[:f] *= np.linspace(0, 1, f); v[-f:] *= np.linspace(1, 0, f)
        place(voice, v, t0, 1.0)
    # --- instruments
    def braam(d=3.2, f0=49.0):
        n = int(d * SR); x = np.arange(n) / SR
        env = np.minimum(1, x / 0.04) * np.exp(-x * 0.9)
        bright = 2 + 26 * np.exp(-x * 1.6)
        out = np.zeros(n)
        for k in range(1, 36):
            amp = (1 / k) * np.exp(-k / bright)
            for det in (1.0, 1.006, 0.994):
                out += amp * np.sin(2 * np.pi * f0 * det * k * x + k)
        out = np.tanh(out * 1.6) * env
        sub = np.sin(2 * np.pi * (f0 / 2) * x) * np.exp(-x * 1.2)
        return (out * 0.7 + sub * 0.6) / 1.2
    def boom():
        n = int(2.0 * SR); x = np.arange(n) / SR
        b_ = np.sin(2 * np.pi * (32 + 90 * np.exp(-x * 14)) * x) * np.exp(-x * 2.4)
        z = rng.standard_normal(n) * np.exp(-x * 30); z = np.convolve(z, np.ones(30) / 30, "same")
        return np.tanh((b_ + z * 0.6) * 1.4)
    def hitsfx():
        n = int(0.5 * SR); x = np.arange(n) / SR; z = rng.standard_normal(n) * np.exp(-x * 25)
        return np.sin(2 * np.pi * (70 + 60 * np.exp(-x * 30)) * x) * np.exp(-x * 9) + z * 0.35
    def tick():
        n = int(0.05 * SR); x = np.arange(n) / SR; return (np.sin(2 * np.pi * 2400 * x) + 0.5 * np.sin(2 * np.pi * 3600 * x)) * np.exp(-x * 140)
    def heart():
        n = int(0.7 * SR); x = np.arange(n) / SR
        def th(o): y = np.zeros(n); s = int(o * SR); xx = x[:n - s]; y[s:] = np.sin(2 * np.pi * 50 * xx) * np.exp(-xx * 18); return y
        return th(0) + 0.7 * th(0.22)
    def taiko():
        n = int(0.8 * SR); x = np.arange(n) / SR; z = rng.standard_normal(n) * np.exp(-x * 60)
        return np.tanh((np.sin(2 * np.pi * (58 + 50 * np.exp(-x * 20)) * x) * np.exp(-x * 6) + z * 0.3) * 1.5)
    def riser(d=1.6):
        n = int(d * SR); x = np.arange(n) / SR; z = rng.standard_normal(n); b_ = np.fft.rfft(z)
        b_ *= np.exp(-np.fft.rfftfreq(n, 1 / SR) / 4000); z = np.fft.irfft(b_, n); z /= np.abs(z).max()
        return (np.sin(2 * np.pi * np.cumsum(180 * 8 ** (x / d)) / SR) * 0.3 + z * 0.8) * (x / d) ** 2.5
    def whoosh(d=0.4):
        n = int(d * SR); z = rng.standard_normal(n); b_ = np.fft.rfft(z); b_ *= np.exp(-np.fft.rfftfreq(n, 1 / SR) / 3000)
        y = np.fft.irfft(b_, n); return y / np.abs(y).max() * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    # --- beds
    drone = (np.sin(2 * np.pi * 36.7 * tt) * 0.5 + np.sin(2 * np.pi * 55.0 * tt + 0.3) * 0.3)
    nz = rng.standard_normal(N); B_ = np.fft.rfft(nz); B_ *= np.exp(-np.fft.rfftfreq(N, 1 / SR) / 500); pad = np.fft.irfft(B_, N); pad /= np.abs(pad).max()
    bed = (drone * 0.5 + pad * 0.5) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * tt) ** 2)
    IM.BPM = 120; IM.BEAT = 0.5
    melody = IM.compose(TOTAL, [(tc("VO3"), tc("IT2"), "calm"), (tc("Q1"), tc("TITLE"), "full"), (tc("TITLE"), TOTAL, "end")])
    mel_env = np.zeros(N)
    for (a_, b_) in [(tc("VO3"), tc("IT2")), (tc("Q1"), TOTAL - 0.5)]: mel_env[(tt >= a_) & (tt < b_)] = 1
    mel_env = np.convolve(mel_env, np.ones(int(0.4 * SR)) / int(0.4 * SR), "same")
    perc = np.zeros(N)
    x = tc("Q1"); k = 0
    while x < tc("TITLE") - 0.2:                                   # action montage: taiko pattern @120 bpm
        if k % 4 in (0, 3) or k % 8 == 6: place(perc, taiko(), x, 0.6)
        place(perc, tick(), x + 0.25, 0.12)
        x += 0.5; k += 1
    clock = np.zeros(N)
    for (a_, b_, r0, r1) in [(tc("T1"), tc("IT1"), 0.25, 0.25), (tc("VO4"), tc("BLK"), 0.5, 0.16)]:
        x = a_
        while x < b_:
            place(clock, tick(), x, 0.22); p = (x - a_) / (b_ - a_); x += r0 + (r1 - r0) * p
    for x in np.arange(tc("VO2"), te("VO2"), 0.75): place(clock, heart(), x, 0.5)
    sfx = np.zeros(N)
    for (t_, s_, k_) in HITS:
        if k_ == "braam": place(sfx, braam(), t_, 0.55 * s_)
        elif k_ == "boom": place(sfx, boom(), t_, 0.45 * s_)
        else: place(sfx, hitsfx(), t_, 0.25 * s_)
    for c_ in cut_list()[1:]: place(sfx, whoosh(), c_ - 0.2, 0.06)
    for t_ in (tc("IT1"), at("VO3", 39.96), at("VO6", 34.70), tc("TITLE")): place(sfx, riser(), t_ - 1.6, 0.16)
    # mix: music bed under everything, ducked by voice; total silence in BLK
    win = int(0.05 * SR); ve = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
    act = np.convolve((ve > 0.015).astype(float), np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
    duck = 10 ** ((-8.0 * np.clip(act * 1.6, 0, 1)) / 20)
    music = (bed * 0.22 + perc * 0.6 + clock * 0.5)[:, None] + melody * (mel_env * 0.35)[:, None]
    music *= duck[:, None]
    silent = (tt >= tc("BLK")) & (tt < te("BLK")); music[silent] *= 0.05
    tail = tt > TOTAL - 1.0; music[tail] *= (np.linspace(1, 0, tail.sum()) ** 2)[:, None]
    st = music + (voice + sfx)[:, None]
    st /= max(1.0, np.abs(st).max() / 0.95)
    raw = f"{OUT}/mix_action_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                    f"{OUT}/mix_action.wav"], check=True)
    print("audio ok")

def report():
    def f(x): return f"{int(x // 60)}:{x % 60:05.2f}"
    print("TOTAL", TOTAL)
    for e in TL: print(f"{e[1]:9s} {f(tc(e[1]))}-{f(te(e[1]))}", e[2:5] if e[0] in ("spk", "vo") else e[3] if e[0] == "card" else e[3])

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    {"audio": audio, "video": render, "report": report}.get(cmd, lambda: render([float(x) for x in sys.argv[2].split(",")]))()
