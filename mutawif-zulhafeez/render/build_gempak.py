"""GEMPAK cut: "3 SEBAB JEMAAH KATA DIA TERBAIK" – testimoni jemaah, Mutawif Ustaz Zulhafeez (1080x1920, 30 fps).

Fast cold open (3 real one-liners), title slam, 3 numbered chapters, verdict, CTA.
All speech is the jemaah's own words (see edl_testi.WORDS); only pauses are cut.

Usage: SRC_DIR=... OUT_DIR=... python3 build_gempak.py audio|video|report|preview T1,T2
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B
import build_testi as BT
from build import (W, H, FPS, SRC, OUT, F, GOLD, GOLD_L, NAVY, PURPLE, WHITE, clamp, ease_out, ease_io, ease_back,
                   set_alpha, scaled, paste_c, text_img, two_tone, stack, rounded_card, ornament, glow_sprite,
                   load_photo, cover, view, grade_photo, rim_light, light_sweep, El, Fx, Particles, location_pin, Gallery, EndBg)
from build_testi import SyncSeg, Memory, SplitLive, kw, name_tag, floating_card, memory_cards, counter, S, ft, ph, ct
from edl_testi import PIECES as TP, WORDS as TW, M1, M2, M3

NAME = "DM_Testimoni_GEMPAK_UstazZulhafeez_9x16"
DM_PURPLE = (120, 24, 140)
HOT = (255, 214, 90)

# ================================================================== edit list
# ("voice", id, src, in, out, z0, z1, cy)   or   ("card", id, dur)
EDL = [
    ("voice", "C1", M3, 69.50, 70.60, 1.10, 1.32, 0.30),   # "A lah terbaik."
    ("voice", "C2", M2, 63.55, 64.84, 1.10, 1.32, 0.27),   # "memang 100 peratus lah"
    ("voice", "C3", M3, 70.62, 72.60, 1.05, 1.30, 0.30),   # "Sempoi, padu, bahang."
    ("card", "TITLE", 3.2),
    ("card", "CH1", 1.1),
    ("voice", "S1a", M2, 1.75, 6.05, 1.00, 1.08, 0.28),    # mutawif pun memang sempoi ... mengopi sekali
    ("voice", "S1b", M2, 6.70, 10.45, 1.16, 1.22, 0.26),   # banyak belajar daripada mutawif sendiri
    ("card", "CH2", 1.1),
    ("voice", "S2a", M3, 5.12, 11.25, 1.00, 1.08, 0.30),   # kali ini ... bersama Ustaz Zulhafeez
    ("voice", "S2b", M3, 11.80, 13.85, 1.20, 1.25, 0.28),  # komitmen yang terbaik lah, steady
    ("voice", "S2c", M3, 21.25, 25.30, 1.04, 1.12, 0.30),  # jemaah hilang di Masjid Quba
    ("voice", "S2d", M3, 28.50, 35.30, 1.00, 1.10, 0.30),  # tak masuk akal ... mutawif kita boleh cari
    ("card", "CH3", 1.1),
    ("voice", "S3a", M2, 23.65, 25.55, 1.10, 1.18, 0.27),  # kita first time ni takut lah
    ("voice", "S3b", M2, 35.38, 46.45, 1.00, 1.14, 0.27),  # ... berkat mutawif ... berjalan lancar
    ("voice", "V1", M1, 5.70, 13.60, 1.00, 1.08, 0.30),    # peluang kedua ... saya akan minta
    ("voice", "V2", M1, 14.95, 17.80, 1.18, 1.24, 0.28),   # dari Darul Mubarak mutawif yang sama
    ("voice", "V3", M2, 61.95, 66.75, 1.10, 1.24, 0.27),   # kalau 100 itu memang 100 peratus ... Darul Mubarak
    ("card", "END", 5.5),
]
T0 = {}; t = 0.0
for e in EDL:
    if e[0] == "voice": T0[e[1]] = (t, e[3], e[4]); t += e[4] - e[3]
    else: T0[e[1]] = (t, 0, e[2]); t += e[2]
TOTAL = round(t, 2)
def at(pid, s): t0, a, _ = T0[pid]; return t0 + (s - a)
def tc(pid): return T0[pid][0]
def te(pid): t0, a, b = T0[pid]; return t0 + (b - a)

# all known words by source (from edl_testi) + a few extra
SRCW = {}
for (pid, src, *_r) in TP: SRCW.setdefault(src, []).extend(TW[pid])
SRCW[M2] += [(23.70, "Kita"), (24.12, "first"), (24.42, "time"), (24.60, "ni"), (24.78, "takut"), (25.52, "lah.")]
SRCW[M2] += [(35.42, "Kita")] if (35.42, "Kita") not in SRCW[M2] else []
for k in SRCW: SRCW[k] = sorted(set(SRCW[k]))
def words(pid):
    e = next(x for x in EDL if x[1] == pid); src, a, b = e[2], e[3], e[4]
    return [(at(pid, s), w) for s, w in SRCW[src] if a - 0.02 <= s < b - 0.05]

IMPACTS = []        # (time, strength) -> screen shake + sub boom

# ================================================================== full-frame cards
def speed_lines(t, cx=W / 2, cy=H * 0.45, n=46, col=(255, 230, 160), seed=3):
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(260, 520) + (t * 2400 + rng.uniform(0, 900)) % 900
        ln = rng.uniform(120, 380); w = rng.uniform(2, 7)
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0
        x1, y1 = cx + math.cos(ang) * (r0 + ln), cy + math.sin(ang) * (r0 + ln)
        d.line((x0, y0, x1, y1), fill=col + (int(rng.uniform(60, 170)),), width=int(w))
    return im

def grad_bg(c1, c2, diag=True):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    k = ((y / H) * 0.75 + (x / W) * 0.25) if diag else y / H
    a = np.array(c1, np.float32) * (1 - k[..., None]) + np.array(c2, np.float32) * k[..., None]
    return Image.fromarray(a.astype(np.uint8))

class TitleCard:
    def __init__(self, t0, dur):
        self.t0, self.dur = t0, dur
        self.bg = grad_bg((40, 8, 60), (8, 14, 40))
        fg = Image.open(ct("IMG_9620.png")).convert("RGBA"); fg = fg.crop(fg.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
        rgb = grade_photo(fg.convert("RGB")).convert("RGBA"); rgb.putalpha(fg.getchannel("A"))
        self.fg = rim_light(rgb.resize((int(rgb.width * 1250 / rgb.height), 1250), Image.LANCZOS), r=26, a=0.95)
        self.halo = glow_sprite(560, GOLD, 170)
        self.l0 = text_img("KATA JEMAAH, INILAH", F("bold", 46), WHITE, tracking=6)
        self.name = text_img("USTAZ ZULHAFEEZ", F("black", 100), HOT, glow=GOLD, glow_r=22)
        if self.name.width > 1000: self.name = scaled(self.name, 1000 / self.name.width)
        self.role = text_img("MUTAWIF  •  DARUL MUBARAK TRAVEL & TOURS", F("bold", 30), WHITE, tracking=3)
        self.n3 = text_img("3", F("black", 300), HOT, glow=GOLD, glow_r=30)
        self.s1 = text_img("SEBAB JEMAAH KATA", F("black", 70), WHITE)
        self.s2 = text_img("DIA TERBAIK!", F("black", 96), HOT, glow=GOLD)
    def frame(self, t, punch=0.0):
        lt = t - self.t0
        c = self.bg.copy().convert("RGBA")
        c.alpha_composite(speed_lines(lt))
        if lt < 1.9:
            e = ease_out(lt / 0.35)
            paste_c(c, set_alpha(self.halo, e), W / 2, 760)
            fg = scaled(self.fg, 1.35 - 0.35 * e + 0.03 * lt)
            paste_c(c, set_alpha(fg, clamp(lt / 0.08)), W / 2, 1920 - fg.height / 2 - 380 + 160 * (1 - e))
            if lt > 0.15: paste_c(c, set_alpha(self.l0, clamp((lt - 0.15) / 0.2)), W / 2, 1450)
            if lt > 0.3:
                s = 1 + 0.5 * (1 - ease_out((lt - 0.3) / 0.18)); paste_c(c, scaled(self.name, s), W / 2, 1560)
            if lt > 0.6: paste_c(c, set_alpha(self.role, clamp((lt - 0.6) / 0.25)), W / 2, 1665)
            if lt > 1.6:                                                   # flash out
                a = np.asarray(c.convert("RGB"), np.float32); k = (lt - 1.6) / 0.3
                c = Image.fromarray((a + (255 - a) * clamp(k) * 0.9).astype(np.uint8)).convert("RGBA")
        else:
            l2 = lt - 1.9
            s = 1 + 1.6 * (1 - ease_out(l2 / 0.2))
            paste_c(c, set_alpha(self.halo, 0.8), W / 2, 820)
            paste_c(c, scaled(self.n3, s), W / 2, 760)
            if l2 > 0.15: paste_c(c, scaled(self.s1, 1 + 0.6 * (1 - ease_out((l2 - 0.15) / 0.18))), W / 2, 1010)
            if l2 > 0.35: paste_c(c, scaled(self.s2, 1 + 0.6 * (1 - ease_out((l2 - 0.35) / 0.18))), W / 2, 1120)
        return c.convert("RGB")

class ChapterCard:
    def __init__(self, t0, dur, num, title, sub, photo):
        self.t0, self.dur = t0, dur
        self.bg = Image.fromarray((np.asarray(cover(load_photo(photo, 1600), W, H), np.float32) * 0.28 +
                                   np.array(DM_PURPLE, np.float32) * 0.45).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
        self.num = text_img(f"#{num}", F("black", 340), HOT, glow=GOLD, glow_r=30)
        self.t1 = [text_img(x, F("black", 104 if len(x) < 12 else 88), WHITE, glow=None) for x in title]
        self.sub = text_img(sub, F("bold", 40), GOLD_L, tracking=2)
    def frame(self, t, punch=0.0):
        lt = t - self.t0
        c = self.bg.copy().convert("RGBA")
        d = ImageDraw.Draw(c)                                           # diagonal gold stripes sweeping
        off = int(lt * 900)
        for k in range(-3, 6):
            x = (k * 320 + off) % 1700 - 300
            d.polygon([(x, 0), (x + 90, 0), (x - 500, H), (x - 590, H)], fill=GOLD + (28,))
        s = 1 + 1.5 * (1 - ease_out(lt / 0.18))
        paste_c(c, scaled(self.num, s), W / 2, 720)
        y = 980
        for i, im in enumerate(self.t1):
            l = lt - 0.12 - i * 0.08
            if l > 0: paste_c(c, scaled(im, 1 + 0.7 * (1 - ease_out(l / 0.16))), W / 2 + (1 - ease_out(l / 0.2)) * (-500 if i % 2 == 0 else 500), y)
            y += im.height + 6
        if lt > 0.35: paste_c(c, set_alpha(self.sub, clamp((lt - 0.35) / 0.2)), W / 2, y + 40)
        return c.convert("RGB")

# ================================================================== segments
SPK = {}
def make_segments():
    segs, cuts = [], []
    for e in EDL:
        if e[0] == "voice":
            _, pid, src, a, b, z0, z1, cy = e
            s = SyncSeg(tc(pid), b - a, S(src), a, 1.0, z0, z1, 0.5, cy); s.kind = "speaker"; SPK[pid] = s; segs.append(s)
    segs.append(TitleCard(tc("TITLE"), T0["TITLE"][2]))
    segs.append(ChapterCard(tc("CH1"), 1.1, 1, ["SEMPOI &", "BANYAK BELAJAR"], "KATA JEMAAH #1", ph("IMG_3195.jpg")))
    segs.append(ChapterCard(tc("CH2"), 1.1, 2, ["KOMITMEN", "TERBAIK"], "JEMAAH HILANG PUN DAPAT DICARI", ph("IMG_2178.jpg")))
    segs.append(ChapterCard(tc("CH3"), 1.1, 3, ["FIRST TIME", "PUN LANCAR"], "BERKAT TUNJUK AJAR MUTAWIF", ph("IMG_9497.jpg")))
    g = EndBg(tc("END"), 5.5, ph("IMG_2177.jpg")); segs.append(g)
    def cut(seg): cuts.append(seg)
    cut(SplitLive(at("S1a", 1.80), 2.3, SPK["S1a"], ph("IMG_3195.jpg"), (0.30, 0.55)))                       # "mutawif pun memang sempoi"
    cut(SyncSeg(at("S1b", 8.95), te("S1b") - at("S1b", 8.95), ft("IMG_2048.MOV"), 0.6, 1.0, 1.06, 1.16, 0.57, 0.42))  # "daripada mutawif"
    cut(SyncSeg(at("S2c", 22.80), te("S2c") - at("S2c", 22.80), ft("IMG_2048.MOV"), 13.35, 0.5, 1.10, 1.24, 0.55, 0.45))  # Masjid Quba
    mv = SyncSeg(at("S2d", 33.30), te("S2d") - at("S2d", 33.30), ft("IMG_2031.MOV"), 0.0, 0.5, 1.25, 1.10, 0.5, 0.38)
    cut(Memory(mv.t0, mv.dur, mv, ct("IMG_2177.png")))                                                        # "mutawif kita boleh cari"
    cut(SyncSeg(at("S3b", 44.70), te("S3b") - at("S3b", 44.70), ft("89b65111.mp4"), 0.0, 1.0, 1.12, 1.0, 0.45, 0.45))  # berjalan lancar
    cut(SyncSeg(at("V1", 10.40), 1.9, ft("991cf9ec.mp4"), 0.3, 1.0, 1.05, 1.15, 0.5, 0.42))                    # ke Tanah Suci
    segs.sort(key=lambda s: s.t0)
    return segs, cuts

# ================================================================== overlays
def slam(txt_parts, size=150, maxw=1020, sub=None):
    im = two_tone(txt_parts, F("black", size), glow=GOLD)
    if im.width > maxw: im = scaled(im, maxw / im.width)
    if sub: im = stack([im, text_img(sub, F("black", int(size * 0.42)), WHITE)], 0)
    return im

class Slam(El):
    def __init__(self, t0, t1, img, cx, cy, hit=0.6):
        super().__init__(t0, t1, img, cx, cy, "crash", 0.16, 0.12); IMPACTS.append((t0, hit))

class Bar:
    """Top progress bar 1-2-3 + current chapter tag (appears after title)."""
    def __init__(self):
        self.t0 = tc("CH1"); self.t1 = tc("END")
        self.marks = [(tc("CH1"), te("S1b")), (tc("CH2"), te("S2d")), (tc("CH3"), te("S3b"))]
        self.lab = text_img("TESTIMONI JEMAAH", F("black", 30), WHITE, tracking=5)
        self.nums = [text_img(str(i + 1), F("black", 34), NAVY, shadow=False) for i in range(3)]
        logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
        self.badge = Image.new("RGBA", (78, 78), (0, 0, 0, 0))
        ImageDraw.Draw(self.badge).ellipse((0, 0, 77, 77), fill=(255, 255, 255, 245), outline=GOLD + (255,), width=3)
        self.badge.alpha_composite(logo.resize((64, 64), Image.LANCZOS), (7, 6))
    def draw(self, c, t):
        if not (self.t0 <= t < self.t1): return
        a = clamp((t - self.t0) / 0.3)
        d = ImageDraw.Draw(c)
        x0, y0, seg, gap = 170, 175, 270, 14
        c.alpha_composite(set_alpha(self.badge, a), (60, 136))
        c.alpha_composite(set_alpha(self.lab, a), (x0, 118))
        for i, (s, e) in enumerate(self.marks):
            x = x0 + i * (seg + gap)
            d.rounded_rectangle((x, y0, x + seg, y0 + 22), 11, fill=(255, 255, 255, int(70 * a)))
            p = clamp((t - s) / (e - s)) if t >= s else 0
            if p > 0: d.rounded_rectangle((x, y0, x + max(22, int(seg * p)), y0 + 22), 11, fill=HOT + (int(255 * a),))
            cx = x + 6
            done = t >= s
            d.ellipse((cx - 4, y0 - 12, cx + 42, y0 + 34), fill=(HOT if done else (200, 200, 210)) + (int(255 * a),))
            c.alpha_composite(set_alpha(self.nums[i], a), (int(cx + 19 - self.nums[i].width / 2), int(y0 + 11 - self.nums[i].height / 2)))

def overlays():
    E = []
    def add(*a, **k): E.append(El(*a, **k))
    def sl(*a, **k): E.append(Slam(*a, **k))
    def fx(*a, **k): E.append(Fx(*a, **k))
    K3, KY = 1350, 1260
    # ---- COLD OPEN: three one-liners, giant slams
    sl(at("C1", 69.62), te("C1"), slam([("A LAH", WHITE), ("TERBAIK!", HOT)], 170), W / 2, K3, 0.9)
    sl(at("C2", 63.86), te("C2"), slam([("100", HOT), ("PERATUS!", WHITE)], 170), W / 2, KY, 0.9)
    for st, wd, x in [(70.70, "SEMPOI!", 210), (71.54, "PADU!", 530), (72.16, "BAHANG!", 845)]:
        sl(at("C3", st), te("C3"), text_img(wd, F("black", 76), HOT if wd == "PADU!" else WHITE, glow=GOLD), x, K3, 0.7)
    IMPACTS.append((tc("TITLE") + 0.3, 1.0)); IMPACTS.append((tc("TITLE") + 1.9, 1.0))
    for ch in ("CH1", "CH2", "CH3"): IMPACTS.append((tc(ch), 1.0))
    E.append(Bar())

    # ---- #1 SEMPOI & BANYAK BELAJAR (M2)
    sl(at("S1a", 2.70), at("S1a", 3.75), slam([("SEMPOI", HOT), ("LAH!", WHITE)], 150), W / 2, 850, 0.5)
    sl(at("S1a", 4.76), te("S1a"), slam([("BOLEH", WHITE), ("MENGOPI", HOT)], 140, sub="SEKALI!"), W / 2, KY, 0.5)
    sl(at("S1b", 7.90), at("S1b", 8.95), slam([("BANYAK", WHITE), ("BELAJAR", HOT)], 140), W / 2, KY, 0.5)
    sl(at("S1b", 9.00), te("S1b"), slam([("DARIPADA", WHITE), ("MUTAWIF", HOT)], 120), W / 2, KY, 0.4)
    add(at("S1b", 9.05), te("S1b"), location_pin("USTAZ ZULHAFEEZ", "Masjid Quba, Madinah"), 360, 380, "left", 0.3, 0.15)

    # ---- #2 KOMITMEN TERBAIK (M3)
    fx(at("S2a", 8.18), te("S2b"), BT.cutout_reveal(ct("IMG_2177.png"), 800, 1040), out=0.25)
    sl(at("S2a", 8.22), at("S2a", 9.40), slam([("USTAZ", WHITE)], 150), 330, 1300, 0.8)
    sl(at("S2a", 9.42), at("S2a", 11.25), slam([("ZULHAFEEZ", HOT)], 130), 380, 1300, 0.6)
    fx(at("S2a", 8.18), at("S2a", 9.2), lambda c, lt, a: c.alpha_composite(set_alpha(speed_lines(lt, 800, 1300), a * 0.8)), out=0.3)
    sl(at("S2b", 12.34), at("S2b", 13.40), slam([("KOMITMEN", WHITE), ("TERBAIK", HOT)], 130), W / 2, K3, 0.6)
    sl(at("S2b", 13.42), te("S2b"), slam([("STEADY!", HOT)], 170), W / 2, K3, 0.8)
    sl(at("S2c", 21.34), at("S2c", 22.80), slam([("JEMAAH", WHITE), ("HILANG!", HOT)], 150), W / 2, K3, 0.9)
    add(at("S2c", 22.85), te("S2c"), location_pin("MASJID QUBA", "Madinah"), 300, 380, "left", 0.3, 0.2)
    sl(at("S2d", 29.85), at("S2d", 30.55), slam([("TAK MASUK", WHITE), ("AKAL!", HOT)], 140), W / 2, K3, 0.6)
    sl(at("S2d", 31.40), at("S2d", 33.20), slam([("DIA ADA", WHITE), ("KAT MANA?", HOT)], 120), W / 2, K3, 0.4)
    sl(at("S2d", 33.45), at("S2d", 34.20), slam([("ALHAMDULILLAH", HOT)], 120), W / 2, KY - 80, 0.5)
    sl(at("S2d", 34.26), te("S2d"), slam([("MUTAWIF KITA", WHITE)], 110, sub="BOLEH CARI!"), W / 2, KY - 60, 0.9)

    # ---- #3 FIRST TIME PUN LANCAR (M2)
    sl(at("S3a", 24.12), te("S3a"), slam([("FIRST TIME", WHITE), ("TAKUT!", HOT)], 130), W / 2, KY, 0.6)
    sl(at("S3b", 36.28), at("S3b", 38.50), slam([("TAHU DIRI", WHITE), ("KITA", HOT)], 130), W / 2, KY, 0.3)
    fx(at("S3b", 40.70), at("S3b", 44.70), memory_cards([ph("IMG_2178.jpg"), ph("IMG_9497.jpg"), ph("IMG_7005.jpg")], 1060), out=0.3)
    sl(at("S3b", 39.96), at("S3b", 43.00), slam([("BERKAT", WHITE), ("MUTAWIF", HOT)], 130), W / 2, 1400, 0.8)
    sl(at("S3b", 43.98), at("S3b", 44.70), slam([("ALHAMDULILLAH", HOT)], 120), W / 2, KY, 0.4)
    sl(at("S3b", 45.68), te("S3b"), slam([("BERJALAN", WHITE), ("LANCAR!", HOT)], 140), W / 2, KY, 0.8)

    # ---- VERDICT
    add(tc("V1"), tc("V1") + 2.2, stack([text_img("DAN JEMAAH NI KATA…", F("black", 64), WHITE)], 0), W / 2, 1300, "up", 0.25, 0.2)
    sl(at("V1", 9.46), at("V1", 10.40), slam([("PELUANG", WHITE), ("KEDUA", HOT)], 140), W / 2, KY, 0.5)
    sl(at("V1", 10.45), at("V1", 12.30), slam([("KE", WHITE), ("TANAH SUCI", HOT)], 140), W / 2, KY, 0.4)
    fx(at("V2", 16.70), te("V2"), floating_card(ph("IMG_9620.jpg"), 215, 1150, 320, -7, "USTAZ ZULHAFEEZ"), out=0.2)
    sl(at("V2", 16.78), te("V2"), slam([("MUTAWIF", HOT)], 120, sub="YANG SAMA!"), 640, 1360, 1.0)
    fx(at("V3", 63.80), at("V3", 65.40), counter(100, "%", 1180), out=0.2)
    sl(at("V3", 65.44), te("V3"), slam([("TERBAIK", HOT)], 160, sub="DARUL MUBARAK"), W / 2, KY, 1.0)

    E.append(GSubs())

    # ---- END / CTA
    e0 = tc("END"); IMPACTS.append((e0, 1.0))
    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 279, 279), fill=(255, 255, 255, 250), outline=GOLD + (255,), width=6)
    badge.alpha_composite(logo.resize((232, 232), Image.LANCZOS), (24, 21))
    add(e0, TOTAL, glow_sprite(250, GOLD, 150), W / 2, 420, "fade", 0.5, 0)
    add(e0, TOTAL, badge, W / 2, 420, "pop", 0.35, 0)
    E.append(Slam(e0 + 0.25, TOTAL, text_img("UMRAH BERSAMA", F("black", 78), WHITE), W / 2, 680, 0.5))
    E.append(Slam(e0 + 0.45, TOTAL, text_img("USTAZ ZULHAFEEZ", F("black", 104), HOT, glow=GOLD), W / 2, 790, 0.8))
    add(e0 + 0.7, TOTAL, text_img("DARUL MUBARAK TRAVEL & TOURS", F("bold", 38), WHITE, tracking=4), W / 2, 880, "fade", 0.3, 0)
    add(e0 + 1.0, TOTAL, stack([text_img("NAK RASAI PENGALAMAN", F("black", 66), WHITE),
                                text_img("UMRAH SEPERTI INI?", F("black", 78), HOT, glow=GOLD)], 0), W / 2, 1090, "pop", 0.35, 0)
    bt = text_img("HUBUNGI KAMI SEKARANG", F("black", 52), NAVY, shadow=False, tracking=1)
    btn = rounded_card(bt.width + 110, bt.height + 50, 48, HOT, 255); btn.alpha_composite(bt, (34 + 55, 34 + 25))
    fx(e0 + 1.4, TOTAL, lambda c, lt, a: paste_c(c, set_alpha(scaled(btn, (0.6 + 0.4 * ease_back(lt / 0.4)) * (1 + 0.04 * math.sin(lt * 6))), clamp(lt / 0.15)), W / 2, 1300), out=0)
    add(e0 + 1.7, TOTAL, text_img("untuk maklumat pakej umrah", F("semi", 40), WHITE), W / 2, 1420, "fade", 0.4, 0)
    E.append(Particles([(tc("TITLE"), tc("CH1")), (e0, TOTAL)], n=34))
    return E

class GSubs:
    """Word-by-word subtitles for every voice piece (shares the look of build_testi)."""
    def __init__(self, y=1560):
        self.y = y; self.ch = []
        for e in EDL:
            if e[0] != "voice": continue
            ws = words(e[1]); end = te(e[1]); cur = []
            for i, (t0, w) in enumerate(ws):
                nxt = ws[i + 1][0] if i + 1 < len(ws) else end
                cur.append((t0, min(nxt, t0 + 0.9), w))
                if len(cur) >= 3 or w[-1] in ".,…?" or i + 1 == len(ws) or nxt - t0 > 1.2: self.ch.append(cur); cur = []
    def draw(self, c, t):
        for ci, ch in enumerate(self.ch):
            t0, t1 = ch[0][0] - 0.05, ch[-1][1] + 0.12
            if ci + 1 < len(self.ch): t1 = min(t1, self.ch[ci + 1][0][0] - 0.03)
            if t0 <= t < t1:
                act = max([j for j, (wt, _, _) in enumerate(ch) if wt <= t] or [0])
                paste_c(c, scaled(BT.sub_img(5000 + ci, ch, act), 0.9 + 0.1 * ease_back((t - t0) / 0.15)), W / 2, self.y); return

# ================================================================== frame effects
def whip_times():
    ts = []
    prev = None
    for e in EDL:
        t0 = tc(e[1])
        if prev is not None and (e[0] == "card" or prev[0] == "card" or e[2] != prev[2]): ts.append(t0)
        prev = e
    return ts

def motion_blur(arr, amount, horizontal=True):
    if amount < 0.05: return arr
    n = 7; step = int(18 * amount) + 1; acc = np.zeros_like(arr)
    for k in range(n):
        acc += np.roll(arr, (k - n // 2) * step, axis=1 if horizontal else 0)
    return acc / n

def shake(t):
    dx = dy = 0.0
    for (ti, s) in IMPACTS:
        d = t - ti
        if 0 <= d < 0.35:
            amp = 22 * s * math.exp(-d * 12)
            dx += amp * math.sin(d * 95 + ti); dy += amp * math.cos(d * 80 + ti * 2)
    return dx, dy

def render(times=None):
    segs, cuts = make_segments(); ovl = overlays(); vig = B.vignette(); WH = whip_times()
    n = int(round(TOTAL * FPS)); frames = range(n) if times is None else [int(round(x * FPS)) for x in times]
    enc = None
    if times is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{OUT}/mix_gempak.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "256k", "-shortest",
                                "-movflags", "+faststart", f"{OUT}/{NAME}.mp4"], stdin=subprocess.PIPE)
    kw_hits = sorted(t for t, _ in IMPACTS)
    for fi in frames:
        t = fi / FPS
        base_seg = [s for s in segs if s.t0 <= t + 1e-6][-1]
        cut_seg = next((c for c in cuts if c.t0 <= t < c.t0 + c.dur), None)
        if getattr(base_seg, "kind", "") == "speaker" and cut_seg is not None and not isinstance(cut_seg, SplitLive): base_seg.frame(t)
        seg = cut_seg or base_seg
        for s in segs + cuts:
            if isinstance(s, B.VideoSeg) and s.proc and t > s.t0 + s.dur + 0.1: s.close()
        # zoom punch on every slam
        pz = 0.0
        for h in kw_hits:
            if 0 <= t - h < 0.25: pz = max(pz, 0.06 * (1 - (t - h) / 0.25) ** 2)
        base = seg.frame(t, punch=pz) if not isinstance(seg, SplitLive) else seg.frame(t)
        a = np.asarray(base, np.float32) * vig
        wb = 0.0
        for w in WH:
            if -0.12 < t - w < 0.14: wb = max(wb, 1 - abs(t - w) / 0.14)
        if wb > 0: a = motion_blur(a, wb)
        if t > TOTAL - 0.6: a *= clamp((TOTAL - t) / 0.6)
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        for e in ovl: e.draw(c, t)
        dx, dy = shake(t)
        if abs(dx) + abs(dy) > 0.5:
            c = c.transform((W, H), Image.AFFINE, (1 / 1.03, 0, W * 0.015 - dx, 0, 1 / 1.03, H * 0.015 - dy), Image.BILINEAR)
        rgb = c.convert("RGB")
        if enc: enc.stdin.write(rgb.tobytes())
        else: rgb.save(f"{OUT}/gprev_{t:06.2f}.png"); print("preview", round(t, 2), flush=True)
        if enc and fi % 300 == 0: print(f"frame {fi}/{n}", flush=True)
    if enc: enc.stdin.close(); enc.wait(); print("video ok", f"{OUT}/{NAME}.mp4")

# ================================================================== audio
SR = 48000
def audio():
    import islamic_music as IM
    IM.BPM = 100; IM.BEAT = 60 / IM.BPM                     # faster, more energetic bed
    overlays()                                              # fills IMPACTS
    rng = np.random.default_rng(9); N = int(TOTAL * SR); tt = np.arange(N) / SR
    def place(buf, clip, t, g):
        s = int(t * SR)
        if 0 <= s < N: c = clip[:N - s]; buf[s:s + len(c)] += c * g
    voice = np.zeros(N); gains = {}
    for src in {e[2] for e in EDL if e[0] == "voice"}:
        v = B.read_audio(S(src), 0, 999, B.VOICE_AF); gains[src] = 0.15 / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9)
    for e in EDL:
        if e[0] != "voice": continue
        _, pid, src, a, b, *_r = e
        v = B.read_audio(S(src), a, b - a, B.VOICE_AF) * gains[src]
        f = int(0.02 * SR); v[:f] *= np.linspace(0, 1, f); v[-f:] *= np.linspace(1, 0, f)
        place(voice, v, tc(pid), 1.0)
    music = IM.compose(TOTAL, [(0.0, tc("TITLE"), "full"), (tc("TITLE"), tc("S3a"), "full"),
                               (tc("S3a"), tc("V1"), "calm"), (tc("V1"), TOTAL, "end")])
    # driving percussion: kick on every beat, clap on 2 & 4 (outside the emotional chapter)
    beat = 60 / 100
    def kick():
        n = int(0.35 * SR); x = np.arange(n) / SR
        return np.sin(2 * np.pi * (48 + 110 * np.exp(-x * 30)) * x) * np.exp(-x * 9)
    def clap():
        n = int(0.18 * SR); x = np.arange(n) / SR; z = rng.standard_normal(n)
        b_ = np.fft.rfft(z); f = np.fft.rfftfreq(n, 1 / SR); b_ *= ((f > 900) & (f < 6000)); z = np.fft.irfft(b_, n)
        return z / np.abs(z).max() * np.exp(-x * 28)
    drums = np.zeros(N); k = 0; x = 0.0
    while x < TOTAL - 1.5:
        calm = tc("S3a") <= x < tc("V1")
        if not calm or k % 2 == 0: place(drums, kick(), x, 0.55 if not calm else 0.3)
        if k % 2 == 1 and not calm: place(drums, clap(), x, 0.18)
        x += beat; k += 1
    lvl = np.full(N, -12.0)
    for nm in ("TITLE", "CH1", "CH2", "CH3", "END"): lvl[(tt >= tc(nm)) & (tt < te(nm))] = -3.5
    win = int(0.05 * SR); ve = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
    act = np.convolve((ve > 0.015).astype(float), np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
    g = 10 ** ((lvl - 9.0 * np.clip(act * 1.6, 0, 1)) / 20); g = np.convolve(g, np.ones(int(0.15 * SR)) / int(0.15 * SR), "same")
    tail = tt > TOTAL - 1.2; g[tail] *= np.linspace(1, 0, tail.sum()) ** 2
    bed = (music * 0.55 + drums[:, None] * 0.5) * g[:, None]

    def boom():
        n = int(1.6 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * (34 + 70 * np.exp(-x * 10)) * x) * np.exp(-x * 2.4)
    def whoosh(d=0.45):
        n = int(d * SR); z = rng.standard_normal(n); b_ = np.fft.rfft(z); b_ *= np.exp(-np.fft.rfftfreq(n, 1 / SR) / 3000)
        y = np.fft.irfft(b_, n); return y / np.abs(y).max() * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    def hit():
        n = int(0.25 * SR); x = np.arange(n) / SR; z = rng.standard_normal(n) * np.exp(-x * 40)
        return (np.sin(2 * np.pi * 90 * x) * np.exp(-x * 18) + z * 0.4)
    def riser(d=1.4):
        n = int(d * SR); x = np.arange(n) / SR
        return (np.sin(2 * np.pi * np.cumsum(240 * 6 ** (x / d)) / SR) * 0.25 + whoosh(d) * 0.8) * (x / d) ** 2
    def shimmer():
        n = int(1.2 * SR); x = np.arange(n) / SR; o = np.zeros(n)
        for j, fq in enumerate([1568, 2093, 2637, 3136, 4186]):
            s = int(j * 0.06 * SR); o[s:] += np.sin(2 * np.pi * fq * x[:n - s]) * np.exp(-x[:n - s] * 4) * 0.2
        return o
    def tick():
        n = int(0.04 * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 120)
    sfx = np.zeros(N)
    for w in whip_times(): place(sfx, whoosh(), w - 0.22, 0.10)
    for (t, s) in IMPACTS:
        if s >= 0.9: place(sfx, boom(), t, 0.28 * s)
        else: place(sfx, hit(), t, 0.10 * s)
    place(sfx, riser(), tc("TITLE") - 1.4 + 0.3, 0.10)
    for (pid, s_) in [("S1a", 1.84), ("S1b", 9.0), ("S2a", 8.22), ("S2d", 34.26), ("S3b", 40.78), ("V2", 16.78)]:
        place(sfx, shimmer(), at(pid, s_) - 0.05, 0.09)
    for j in range(25): place(sfx, tick(), at("V3", 63.80) + j * 0.7 / 24, 0.04)
    st = bed + (voice + sfx)[:, None]
    st /= max(1.0, np.abs(st).max() / 0.95)
    raw = f"{OUT}/mix_gempak_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                    f"{OUT}/mix_gempak.wav"], check=True)
    print("audio ok")

def report():
    def f(x): return f"{int(x // 60)}:{x % 60:05.2f}"
    print("TOTAL", TOTAL)
    for e in EDL: print(f"{e[1]:6s} {f(tc(e[1]))}-{f(te(e[1]))}", e[2:5] if e[0] == "voice" else "")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    {"audio": audio, "video": render, "report": report}.get(cmd, lambda: render([float(x) for x in sys.argv[2].split(",")]))()
