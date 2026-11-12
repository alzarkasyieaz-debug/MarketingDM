"""Main compositor: Master Video + AI cut-out + background replacement + 3D titles behind presenter +
real B-roll + kinetic overlays + subtitles -> silent 1080x1920 video (audio muxed by build_audio.py)."""
import math, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from timeline import *  # noqa
from fx import *        # noqa

PREVIEW = os.environ.get("PREVIEW")          # e.g. "3.0,8.5,21.0" -> write stills only
T_RANGE = os.environ.get("RANGE")            # e.g. "0,10" -> partial render
OUTV = os.environ.get("OUTV", f"{WORK}/video_silent.mp4")
GIFT = f"{SRC}/gifts"


# ------------------------------------------------------------------------------------------- sources
class Reader:
    def __init__(self, path, ss=0.0, vf=None):
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", path]
        if vf: cmd += ["-vf", vf]
        cmd += ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=W * H * 3 * 2)
        self.k, self.fr = -1, None

    def at(self, k):
        while self.k < k:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3:
                break
            self.fr = b; self.k += 1
        return np.frombuffer(self.fr, np.uint8).reshape(H, W, 3).astype(np.float32) / 255

    def close(self):
        try: self.p.kill()
        except Exception: pass


MASTER_VF = "eq=contrast=1.13:brightness=-0.035:saturation=1.22:gamma=0.97,colorbalance=rs=0.03:bs=-0.035:rh=0.02:bh=-0.03"
M0 = 1.6
master = None
MASKS = np.load(f"{WORK}/masks.npy", mmap_mode="r")


def master_frame(src):
    """graded master frame + refined alpha for master time `src`"""
    global master
    fi = int(round(src * FPS))
    k = fi - int(round(M0 * FPS))
    img = master.at(k)
    m = MASKS[fi - 1:fi + 2].astype(np.float32)
    a = (m[0] + 2 * m[1] + m[2]) / (4 * 255) if len(m) == 3 else MASKS[fi].astype(np.float32) / 255
    a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    a = np.clip((a - 0.12) / 0.76, 0, 1)
    a = cv2.erode(a, np.ones((3, 3), np.uint8), iterations=1)
    a = cv2.GaussianBlur(a, (0, 0), 1.3)
    return img, a


def decontaminate(img, a):
    """remove bright-sky spill on the matte edge: replace edge colour by nearby interior colour"""
    hard = (a > 0.97).astype(np.float32)
    num = cv2.blur(img * hard[..., None], (21, 21)); den = cv2.blur(hard, (21, 21))[..., None]
    inner = num / np.maximum(den, 1e-3)
    wgt = np.clip(4 * a * (1 - a) * 1.4, 0, 1)[..., None] * (den > 0.02)
    return img * (1 - wgt) + inner * wgt


studio = StudioAnim()
readers = {}


def clip_frame(name, ss, t_local, speed=1.0):
    key = (name, ss)
    if key not in readers:
        readers[key] = Reader(f"{BR}/{name}.mp4", ss)
    return readers[key].at(int(t_local * speed * FPS))


def zoom(img, s, cx=540, cy=960):
    if abs(s - 1) < 1e-4: return img
    A = np.float32([[s, 0, cx - cx * s], [0, s, cy - cy * s]])
    return cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def soft(img, sigma):
    if sigma <= 0: return img
    sm = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    sm = cv2.GaussianBlur(sm, (0, 0), sigma / 4)
    return cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)


def keys(t, ks):
    """piecewise eased interpolation of [(t, v), ...]"""
    if t <= ks[0][0]: return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease_io((t - t0) / max(1e-6, t1 - t0))
    return ks[-1][1]


# ------------------------------------------------------------------------------------------- scenes
LIGHT = {  # environment matching of the cut-out presenter: (exposure, rgb gain, rim colour, rim strength, wrap)
    "night": (0.80, (1.04, 0.98, 0.92), (1.0, 0.82, 0.55), 0.55, 0.35),
    "day": (1.00, (1.0, 1.0, 1.0), (1.0, 0.97, 0.9), 0.30, 0.30),
    "studio": (0.93, (1.02, 1.0, 0.96), (1.0, 0.80, 0.42), 0.60, 0.25),
}

S = []
def scene(t0, t1, kind, **kw):
    S.append(dict(t0=t0, t1=t1, kind=kind, **kw))

T3 = []  # (scene-independent) 3D titles, drawn only in cut-out scenes, between background and presenter
def title(txt, t0, t1, cy, size=210, face="gold"):
    T3.append(Title3D(txt, t0, t1, cy, size=size, face=face))

# 1 HOOK
scene(0.0, HOOK, "broll", clip="kaabah", ss=0.0, z=[(0, 1.22), (0.35, 1.06), (HOOK, 1.03)])
# 2 salam – cut-out over Kaabah, 3D "UMRAH / SUPER JIMAT" behind
scene(HOOK, o(4.05), "cut", bg=("clip", "kaabah", 1.5), blur=5, light="night", ps=[(HOOK, 0.86), (o(4.05), 0.9)],
      dx=[(HOOK, 0), (o(2.4), 0), (o(3.3), -120)],
      bz=[(HOOK, 1.04), (o(4.05), 1.08)])
title("UMRAH", HOOK + 0.05, o(4.05), 360, 250)
title("SUPER JIMAT", HOOK + 0.35, o(4.05), 590, 190)
# 3 presenter (original plate) + punch zoom on "terbaik"
scene(o(9.2), o(12.75), "pres", z=[(o(9.2), 1.0), (o(10.38), 1.03), (o(10.52), 1.13), (o(12.75), 1.16)])
# 4 cut-out transition -> Masjidil Haram, 3D "JANUARI / 2027"
scene(o(12.75), o(17.0), "cut", bg=("clip", "haram", 4.0), freeze=True, blur=3, gblur=(640, 920, 26), light="day", from_orig=True, banchor=(700, 300),
      ps=[(o(12.75), 0.92), (o(13.3), 0.88), (o(17.0), 0.92)], bz=[(o(12.75), 1.15), (o(17.0), 1.24)])
title("JANUARI", o(14.85), o(17.0), 370, 220)
title("2027", o(15.95), o(17.0), 600, 260)
# 5 B-roll: real Darul Mubarak pilgrims (slow motion)
scene(o(17.0), o(20.75), "broll", clip="jemaah1", ss=0.0, z=[(o(17.0), 1.0), (o(20.75), 1.07)])
# 6 cut-out on studio, 3D "HADIAH / PERCUMA" + backpack
scene(o(20.75), o(23.15), "cut", bg=("studio",), light="studio", dx=170, ps=[(o(20.75), 0.84), (o(23.15), 0.87)])
title("HADIAH", o(20.8), o(23.15), 360, 230)
title("PERCUMA", o(21.1), o(23.15), 590, 230, face="white")
# 7 gifts: ihram + telekung split screen
scene(o(23.15), o(26.65), "studio", sz=[(o(23.15), 1.0), (o(26.65), 1.06)])
# 8 Zamzam
scene(o(26.65), o(32.6), "studio", sz=[(o(26.65), 1.06), (o(32.6), 1.0)])
# 9 cut-out on studio: register & receive all gifts
scene(o(32.6), o(36.15), "cut", bg=("studio",), light="studio", dx=170, ps=[(o(32.6), 0.86), (o(36.15), 0.9)])
# 10 cut-out on studio: 3D "YEAR END / SALE"
scene(o(36.15), o(43.2), "cut", bg=("studio",), light="studio", ps=[(o(36.15), 0.86), (o(43.2), 0.93)])
title("YEAR END", o(38.16), o(43.2), 370, 200)
title("SALE", o(38.70), o(43.2), 600, 270, face="white")
# 11 presenter: urgency
scene(o(43.2), o(46.9), "pres", z=[(o(43.2), 1.0), (o(43.9), 1.02), (o(44.05), 1.15), (o(46.9), 1.18)])
# 12-13 B-roll
scene(o(46.9), o(49.8), "broll", clip="jalan", ss=1.9, z=[(o(46.9), 1.08), (o(49.8), 1.0)])
scene(o(49.8), o(52.2), "broll", clip="lobi", ss=0.0, z=[(o(49.8), 1.0), (o(52.2), 1.06)])
# 14 cut-out on studio: company
scene(o(52.2), o(55.1), "cut", bg=("studio",), light="studio", ps=[(o(52.2), 0.86), (o(55.1), 0.9)])
# 15-17 emotional B-roll
scene(o(55.1), o(58.0), "broll", clip="jemaah2", ss=0.0, z=[(o(55.1), 1.0), (o(58.0), 1.06)])
scene(o(58.0), o(60.6), "broll", clip="jemaah3", ss=0.0, z=[(o(58.0), 1.0), (o(60.6), 1.08)])
scene(o(60.6), o(63.3), "broll", clip="kaabah", ss=0.3, z=[(o(60.6), 1.14), (o(63.3), 1.0)])
# 18 CTA: cut-out on studio, 3D "DAFTAR / SEGERA!"
scene(o(63.3), END0, "cut", bg=("studio",), light="studio", ps=[(o(63.3), 0.86), (END0, 0.9)])
title("DAFTAR", o(63.4), END0, 370, 240)
title("SEGERA!", o(63.75), END0, 600, 240, face="white")
# 19 end card
scene(END0, TOTAL, "end")

FLASH = [HOOK, o(12.75), o(20.75), o(31.3), o(38.16), o(63.3), END0]
PUNCH = [s["t0"] for s in S[1:]]


# ------------------------------------------------------------------------------------------- overlays
E = []
def add(*a, **k): E.append(El(*a, **k))

fB = lambda s: F("InterDisplay-Black", s)
fX = lambda s: F("InterDisplay-ExtraBold", s)
fS = lambda s: F("serif", s)

def headline(l1, l2=None, s1=110, s2=110, c2=GOLD):
    items = [text_img(l1, fB(s1), WHITE, stroke=3, glow=(0, 0, 0), glow_r=18)]
    if l2: items.append(text_img(l2, fB(s2), c2, stroke=3, glow=(120, 70, 0), glow_r=18, grad=(GOLD_L, (214, 150, 40)) if c2 == GOLD else None))
    return stack(items, gap=-40)

def chip(txt, size=46, fill=(8, 60, 40, 235), border=GOLD, col=WHITE, padx=40, h=None):
    t = text_img(txt, fX(size), col, shadow=False)
    w = t.size[0] - 80 + 2 * padx; hh = h or (t.size[1] - 80 + 44)
    c = rounded(w, hh, hh // 2, fill, border, 4)
    return paste_c(c, t, c.size[0] / 2, c.size[1] / 2)

# hook
add(0.08, HOOK, headline("NAK UMRAH", None, 150), 540, 330, "stamp", dur=0.25, out=0.12)
add(0.42, HOOK, headline(" ", "SUPER JIMAT?", 20, 150), 540, 500, "stamp", dur=0.25, out=0.12)
# lower third: company
lt = chip("DARUL MUBARAK TRAVEL & TOURS", 40)
add(HOOK + 0.3, o(4.05), lt, 540, 1250, "up")
# scene 4 label
add(o(12.85), o(17.0), chip("PAKEJ UMRAH SUPER JIMAT", 48), 540, 1250, "up")
# scene 5
add(o(17.1), o(20.75), headline("PELUANG", "UNTUK ANDA", 120, 120), 540, 380, "up", drift=0.01)
add(o(17.4), o(20.75), chip("Jemaah Darul Mubarak", 36, fill=(0, 0, 0, 150), border=None), 540, 1250, "fade")
# scene 6 backpack
bag = Image.open(f"{GIFT}/bag.png").convert("RGBA"); bag.thumbnail((560, 560))
add(o(21.9), o(23.15), bag, 290, 1000, "pop", drift=0.02)
add(o(22.2), o(23.15), chip("BACKPACK ISTIMEWA", 42), 300, 1265, "up")
# scene 7 ihram + telekung
add(o(23.2), o(26.65), headline("+ PERCUMA", None, 96), 540, 300, "up")
add(o(23.35), o(26.65), photo_card(f"{GIFT}/ihram.jpg", 450, 640, focus=(0.5, 0.35)), 285, 820, "left", dur=0.5, drift=0.012, bumps=(o(26.06),))
add(o(23.6), o(26.65), photo_card(f"{GIFT}/telekung.jpg", 450, 640, focus=(0.5, 0.3)), 795, 820, "right", dur=0.5, drift=0.012, bumps=(o(25.18),))
add(o(23.8), o(26.65), chip("KAIN IHRAM", 42), 285, 1215, "up")
add(o(24.0), o(26.65), chip("TELEKUNG", 42), 795, 1215, "up")
# scene 8 zamzam
add(o(26.75), o(32.6), photo_card(f"{SRC}/poster_new.jpg", 560, 760, focus=(0.5, 0.45)), 540, 830, "zoomin", dur=0.6, drift=0.01)
add(o(28.84), o(32.6), headline("AIR ZAM-ZAM", "500ML", 110, 120), 540, 300, "pop")
stamp = text_img("PERCUMA!", fB(190), GOLD, stroke=8, stroke_fill=(70, 20, 0), glow=(255, 200, 80), glow_r=26, grad=(GOLD_L, (214, 150, 40)))
stamp = stamp.rotate(8, resample=Image.BICUBIC, expand=True)
add(o(31.3), o(32.6), stamp, 540, 900, "stamp", dur=0.22, out=0.15, pulse=0.015)
# scene 9 – register, receive all
add(o(32.65), o(36.15), headline("DAFTAR &", "TERIMA SEMUA!", 104, 104), 540, 330, "up")
def gift_chip(path, l1, l2, crop_focus=(0.5, 0.35)):
    im = Image.open(path).convert("RGBA")
    if path.endswith("bag.png"):
        th = Image.new("RGBA", (140, 140), (255, 255, 255, 255)); b = im.copy(); b.thumbnail((128, 128)); paste_c(th, b, 70, 70)
    else:
        sc = 140 / min(im.size); im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
        x0 = int((im.width - 140) * crop_focus[0]); y0 = int((im.height - 140) * crop_focus[1]); th = im.crop((x0, y0, x0 + 140, y0 + 140))
    m = Image.new("L", (140, 140), 0); ImageDraw.Draw(m).ellipse((0, 0, 139, 139), fill=255); th.putalpha(m)
    c = rounded(470, 160, 80, (8, 60, 40, 240), GOLD, 4)
    c.alpha_composite(th, (40, 40))
    c.alpha_composite(text_img(l1, fX(38), WHITE, shadow=False), (170, 40))
    c.alpha_composite(text_img(l2, fX(32), GOLD, shadow=False), (170, 88))
    return c
gifts = [gift_chip(f"{GIFT}/bag.png", "Backpack", "Istimewa"),
         gift_chip(f"{GIFT}/ihram.jpg", "Kain Ihram /", "Telekung", (0.5, 0.25)),
         gift_chip(f"{SRC}/poster_new.jpg", "Air Zam-Zam", "500ml", (0.5, 0.45))]
for i, g in enumerate(gifts):
    add(o(33.6) + 0.35 * i, o(36.15), g, 290, 830 + 175 * i, "left", dur=0.45, bumps=(o(34.8),))
# scene 10
rib = chip("BERAKHIR DISEMBER 2026", 52, fill=(150, 20, 30, 240), border=GOLD)
add(o(40.44), o(43.2), rib, 540, 1250, "stamp", dur=0.25, pulse=0.025)
add(o(36.3), o(38.1), chip("PROMOSI", 46), 540, 1250, "up")
# scene 11 urgency
add(o(43.96), o(46.9), headline("REBUT", "SEGERA!", 150, 150), 540, 260, "stamp", dur=0.25)
add(o(46.2), o(46.9), chip("SELAGI STOK MASIH ADA", 46, fill=(150, 20, 30, 240)), 540, 1250, "up")
add(o(46.95), o(49.8), chip("SELAGI STOK MASIH ADA", 46, fill=(150, 20, 30, 240)), 540, 1250, "fade", dur=0.01)
# scene 13
add(o(50.3), o(52.2), headline("PENGALAMAN UMRAH", "SUPER JIMAT", 84, 120), 540, 360, "up")
# scene 14 company badge
logo = Image.open(f"{SRC}/logo.png").convert("RGBA"); logo.thumbnail((300, 300))
badge = rounded(330, 330, 60, (255, 255, 255, 250), GOLD, 6); paste_c(badge, logo, badge.size[0] / 2, badge.size[1] / 2)
add(o(52.4), o(55.1), badge, 540, 300, "pop", drift=0.01)
add(o(53.3), o(55.1), chip("DARUL MUBARAK TRAVEL & TOURS", 40), 540, 1250, "up")
# scene 16-17 emotional serif
add(o(59.6), o(60.6), text_img("Impian anda...", fS(110), WHITE, glow=(0, 0, 0), glow_r=16), 540, 380, "fade", dur=0.5)
add(o(60.9), o(63.3), text_img("Menjadi", fS(100), WHITE, glow=(0, 0, 0), glow_r=16), 540, 300, "fade", dur=0.5)
add(o(61.5), o(63.3), text_img("TETAMU ALLAH", fS(130), GOLD, glow=(0, 0, 0), glow_r=18, grad=(GOLD_L, (214, 150, 40))), 540, 430, "zoomin", dur=0.8)
# scene 18 CTA – WhatsApp button
def wa_button(w=900, h=190):
    c = rounded(w, h, h // 2, WA_GREEN + (255,), (255, 255, 255), 5)
    d = ImageDraw.Draw(c)
    cx, cy, r = 30 + 100, 30 + h // 2, 58
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255))
    d.polygon([(cx - 40, cy + 30), (cx - 52, cy + 62), (cx - 14, cy + 48)], fill=(255, 255, 255))
    d.ellipse((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), fill=WA_GREEN)
    d.rounded_rectangle((cx - 22, cy - 26, cx + 22, cy + 26), 12, outline=(255, 255, 255), width=8)
    c.alpha_composite(text_img("KLIK WHATSAPP SEKARANG", fB(44), WHITE, shadow=False), (210, 32))
    c.alpha_composite(text_img("016-524 7001  |  016-524 3001", fX(42), (8, 50, 30), shadow=False), (212, 100))
    return c
add(o(64.0), END0, wa_button(), 540, 1215, "pop", pulse=0.02)


# end card (built as a single overlay over the studio)
def end_card():
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste_c(c, badge, 540, 330)
    paste_c(c, text_img("UMRAH", fB(150), WHITE, stroke=2, glow=(0, 0, 0)), 540, 610)
    paste_c(c, text_img("SUPER JIMAT", fB(140), GOLD, stroke=2, glow=(100, 60, 0), grad=(GOLD_L, (214, 150, 40))), 540, 740)
    paste_c(c, chip("JANUARI 2027", 54), 540, 880)
    paste_c(c, text_img("HADIAH PERCUMA:", fX(44), GOLD, shadow=True), 540, 1000)
    paste_c(c, text_img("Backpack  •  Kain Ihram / Telekung  •  Air Zam-Zam 500ml", fX(32), WHITE), 540, 1058)
    paste_c(c, text_img("Promosi Year End Sale – berakhir Disember 2026", F("Inter-Medium", 32), (230, 230, 230)), 540, 1110)
    paste_c(c, wa_button(), 540, 1260)
    paste_c(c, text_img("www.darulmubarak.com", fX(40), WHITE), 540, 1420)
    paste_c(c, text_img("DARUL MUBARAK TRAVEL & TOURS", fX(34), GOLD), 540, 1480)
    return to_np(c)
ENDC = end_card()


# ------------------------------------------------------------------------------------------- subtitles
CH = subtitle_chunks()
_subcache = {}
def sub_img(ci, active):
    key = (ci, active)
    if key in _subcache: return _subcache[key]
    words = CH[ci][2]
    f = fB(62)
    imgs = []
    for j, (_, w) in enumerate(words):
        is_key = w.strip(".,!?").upper() in KEY
        col = GOLD if (j == active and is_key) else (GOLD_L if j == active else WHITE)
        if is_key and j != active: col = (255, 236, 190)
        imgs.append(text_img(w.upper() if is_key else w, f, col, stroke=7, stroke_fill=(0, 0, 0), shadow=True))
    gap = -62
    tw = sum(i.size[0] for i in imgs) + gap * (len(imgs) - 1)
    lines = [imgs]
    if tw > 1000 and len(imgs) > 1:
        lines = [imgs[:2], imgs[2:]] if len(imgs) > 2 else [imgs[:1], imgs[1:]]
    rows = []
    for ln in lines:
        lw = sum(i.size[0] for i in ln) + gap * (len(ln) - 1); lh = max(i.size[1] for i in ln)
        r = Image.new("RGBA", (lw, lh), (0, 0, 0, 0)); x = 0
        for i in ln:
            r.alpha_composite(i, (x, (lh - i.size[1]) // 2)); x += i.size[0] + gap
        rows.append(r)
    im = to_np(stack(rows, gap=-70))
    _subcache[key] = im
    return im


def draw_subs(canvas, t):
    if t < HOOK or t >= END0: return
    for ci, (t0, t1, words) in enumerate(CH):
        if t0 <= t < t1:
            act = max(j for j, (wt, _) in enumerate(words) if wt <= t + 0.02) if words[0][0] <= t else 0
            im = sub_img(ci, act)
            p = clamp((t - t0) / 0.12)
            blit(canvas, im, 540, 1430, 0.9 + 0.1 * ease_back(p), clamp(p * 2))
            return


# ------------------------------------------------------------------------------------------- render
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.32 * (((xx - 540) / 760) ** 2 + ((yy - 900) / 1250) ** 2)).clip(0.55, 1)[..., None]
rng = np.random.default_rng(1)
GRAIN = [rng.normal(0, 0.007, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
LAST_ORIG = {}


def render_cut(sc, t):
    lt = t - sc["t0"]
    src = src_at(t)
    img, a = master_frame(src)
    img = decontaminate(img, a)
    # background
    bz = keys(t, sc.get("bz", [(sc["t0"], 1.0), (sc["t1"], 1.05)]))
    if sc["bg"][0] == "studio":
        bg = studio.frame(t, zoom=bz)
    else:
        _, name, ss = sc["bg"]
        bx, by = sc.get("banchor", (540, 760))
        bg = zoom(clip_frame(name, ss, 0 if sc.get("freeze") else lt), bz, bx, by)
        if sc.get("gblur"):                                   # graded DOF: crowd (lower plate) heavily defocused
            y0g, y1g, sg = sc["gblur"]
            ramp = np.clip((yy - y0g) / (y1g - y0g), 0, 1)[..., None]
            bg = soft(bg, sc.get("blur", 4)) * (1 - ramp) + soft(bg, sg) * ramp
        else:
            bg = soft(bg, sc.get("blur", 4))
        bg = bg * 0.92
    if sc.get("from_orig") and lt < 0.55:                     # cut-out transition: background revealed behind presenter
        r = ease_io(lt / 0.55) * 1500
        circ = np.clip((r - np.sqrt((xx - 540) ** 2 + (yy - 700) ** 2)) / 60, 0, 1)[..., None]
        bg = img * (1 - circ) + bg * circ
    canvas = bg.copy()
    # 3D titles behind the presenter (they share the camera push-in -> parallax)
    for T in T3:
        T.draw(canvas, t, cam=1.0)
    # presenter: transform (scale about bottom-centre)
    ps = keys(t, sc["ps"]); dx = sc.get("dx", 0)
    if isinstance(dx, list):
        dx = keys(t, dx)
    A = np.float32([[ps, 0, 540 + dx - 540 * ps], [0, ps, H - H * ps + 40 * (1 - ps)]])
    pimg = cv2.warpAffine(img, A, (W, H), flags=cv2.INTER_LINEAR)
    pa = cv2.warpAffine(a, A, (W, H), flags=cv2.INTER_LINEAR)
    exp_, gain, rimc, rims, wrap = LIGHT[sc["light"]]
    pimg = pimg * exp_ * np.array(gain, np.float32)
    inner = cv2.GaussianBlur(cv2.erode(pa, np.ones((9, 9), np.uint8)), (0, 0), 5)
    rim = np.clip(pa - inner, 0, 1)[..., None]
    bgb = soft(canvas, 12)
    pimg = pimg + (bgb - pimg) * rim * wrap + rim * rims * np.array(rimc, np.float32) * 0.6
    canvas = canvas * (1 - pa[..., None]) + pimg * pa[..., None]
    return canvas


def render_frame(t):
    sc = next(s for s in S if s["t0"] <= t < s["t1"] + 1e-9)
    lt = t - sc["t0"]
    k = sc["kind"]
    if k == "broll":
        canvas = zoom(clip_frame(sc["clip"], sc["ss"], lt), keys(t, sc["z"]), 540, 900)
    elif k == "pres":
        img, _ = master_frame(src_at(t))
        canvas = zoom(img, keys(t, sc["z"]), 540, 620)
    elif k == "cut":
        canvas = render_cut(sc, t)
    elif k == "studio":
        canvas = studio.frame(t, zoom=keys(t, sc["sz"]))
    else:  # end card with slow cinematic zoom-out
        canvas = studio.frame(t, zoom=1.08 - 0.06 * ease_out(lt / 5))
        blit(canvas, ENDC, 540, 960, 1.06 - 0.06 * ease_out(lt / 1.2), clamp(lt / 0.4))
    # camera punch on cuts
    for p in PUNCH:
        if 0 <= t - p < 0.22:
            canvas = zoom(canvas, 1 + 0.07 * (1 - ease_out((t - p) / 0.22)), 540, 900)
    for e in E:
        e.draw(canvas, t)
    draw_subs(canvas, t)
    for f in FLASH:
        if 0 <= t - f < 0.18:
            canvas += (0.55 * (1 - (t - f) / 0.18)) * np.array((1.0, 0.92, 0.75), np.float32)
    canvas = canvas * VIG
    g = cv2.resize(GRAIN[int(t * FPS) % 6], (W, H), interpolation=cv2.INTER_NEAREST)
    canvas += g[..., None]
    if t > TOTAL - 0.5:
        canvas *= clamp((TOTAL - t) / 0.5)
    return np.clip(canvas, 0, 1)


def main():
    global master
    master = Reader(MASTER, M0, MASTER_VF)
    if PREVIEW:
        ts = sorted(float(x) for x in PREVIEW.split(","))
        for t in ts:
            fr = render_frame(t)
            Image.fromarray((fr * 255).astype(np.uint8)).save(f"{WORK}/prev_{t:05.2f}.jpg", quality=88)
            print("preview", t, flush=True)
        return
    t_a, t_b = (0.0, TOTAL)
    if T_RANGE:
        t_a, t_b = map(float, T_RANGE.split(","))
    n0, n1 = int(round(t_a * FPS)), int(round(t_b * FPS))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                            "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            OUTV], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        t = n / FPS
        fr = render_frame(t)
        enc.stdin.write((fr * 255 + 0.5).astype(np.uint8).tobytes())
        if n % 60 == 0:
            print(f"{t:6.2f}/{TOTAL}", flush=True)
            for key in list(readers):              # free readers of finished scenes
                if not any(s.get("clip") == key[0] or (s.get("bg") and s["bg"][1:2] == (key[0],)) for s in S if s["t0"] <= t + 2 and s["t1"] >= t):
                    readers.pop(key).close()
    enc.stdin.close(); enc.wait()
    print("video ok", OUTV)


if __name__ == "__main__":
    main()
