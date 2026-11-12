"""Step 3: motion graphics, kinetic typography and word-by-word subtitles composited over base.mp4,
muxed with mix.wav -> final mp4.

Usage: SRC_DIR=... OUT_DIR=... TX_JSON=... python3 build_overlay.py [--preview T1,T2,...]
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from timeline import W, H, FPS, SRC, OUT, TOTAL, INTER, END

# ---------------------------------------------------------------- style
GOLD = (242, 193, 78)
GOLD_L = (250, 222, 150)
EMERALD = (11, 93, 59)
EMERALD_D = (6, 52, 34)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
WA_GREEN = (37, 211, 102)

FD = "/usr/share/fonts/opentype/inter/"
FS = "/usr/share/fonts/truetype/crosextra/"
_fc = {}
def F(name, size):
    path = {"black": FD + "Inter-Black.otf", "xbold": FD + "Inter-ExtraBold.otf", "bold": FD + "Inter-Bold.otf",
            "semi": FD + "Inter-SemiBold.otf", "med": FD + "Inter-Medium.otf",
            "serif": FS + "Caladea-Bold.ttf", "serif_i": FS + "Caladea-BoldItalic.ttf", "serif_r": FS + "Caladea-Italic.ttf",
            "sym": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"}[name]
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

# ---------------------------------------------------------------- drawing helpers
def text_img(txt, font, fill=WHITE, stroke=0, stroke_fill=BLACK, glow=None, glow_r=14, shadow=True, tracking=0):
    """Render text to a tight RGBA image (with optional glow + drop shadow)."""
    pad = 40 + glow_r * 2
    if tracking:
        widths = [font.getlength(c) + tracking for c in txt]
        tw = int(sum(widths) - tracking)
    else:
        tw = int(font.getlength(txt))
    asc, desc = font.getmetrics()
    th = asc + desc
    im = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    def draw_on(d, col, sw=stroke, sf=stroke_fill, off=(0, 0)):
        x = pad + off[0]
        if tracking:
            for c, w_ in zip(txt, widths):
                d.text((x, pad + off[1]), c, font=font, fill=col, stroke_width=sw, stroke_fill=sf)
                x += w_
        else:
            d.text((x, pad + off[1]), txt, font=font, fill=col, stroke_width=sw, stroke_fill=sf)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw_on(ImageDraw.Draw(sh), (0, 0, 0, 170), sw=stroke, sf=(0, 0, 0, 170), off=(0, 5))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(7)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw_on(ImageDraw.Draw(g), glow + (200,), sw=stroke + 4, sf=glow + (200,))
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(glow_r)))
    top = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw_on(ImageDraw.Draw(top), fill)
    im = Image.alpha_composite(im, top)
    return im.crop(im.getbbox())

def rounded(w, h, r, fill, border=None, bw=0, alpha=235, shadow=True):
    pad = 30 if shadow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 8, pad + w, pad + h + 8), r, fill=(0, 0, 0, 140))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
    card = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill + (alpha,),
                                           outline=(border + (255,)) if border else None, width=bw)
    return Image.alpha_composite(im, card)

def paste_c(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def stack(items, gap=10, align="center"):
    """Vertically stack RGBA images."""
    w = max(i.width for i in items); h = sum(i.height for i in items) + gap * (len(items) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in items:
        x = (w - i.width) // 2 if align == "center" else 0
        out.alpha_composite(i, (x, y)); y += i.height + gap
    return out

def ornament(w=420):
    im = Image.new("RGBA", (w, 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((0, 15, w / 2 - 22, 15), fill=GOLD + (255,), width=3)
    d.line((w / 2 + 22, 15, w, 15), fill=GOLD + (255,), width=3)
    d.polygon([(w / 2, 3), (w / 2 + 12, 15), (w / 2, 27), (w / 2 - 12, 15)], fill=GOLD + (255,))
    return im

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x, s=1.7):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

class El:
    """Timed overlay element. anim: fade | up | pop | crash | left | right."""
    def __init__(self, t0, t1, img, cx, cy, anim="up", dur=0.45, out=0.3, pulse=0.0, drift=0.0):
        self.t0, self.t1, self.img, self.cx, self.cy = t0, t1, img, cx, cy
        self.anim, self.dur, self.out, self.pulse, self.drift = anim, dur, out, pulse, drift
        self.np = None
    def draw(self, canvas, t):
        if not (self.t0 <= t < self.t1): return
        p = (t - self.t0) / self.dur
        a = clamp(p) if self.anim != "crash" else clamp(p * 3)
        a *= clamp((self.t1 - t) / self.out) if self.out else 1
        s, dx, dy = 1.0, 0, 0
        if self.anim == "up": dy = (1 - ease_out(p)) * 60
        elif self.anim == "pop": s = 0.6 + 0.4 * ease_back(p)
        elif self.anim == "crash": s = 1 + 1.4 * (1 - ease_out(p))
        elif self.anim == "left": dx = -(1 - ease_out(p)) * 700
        elif self.anim == "right": dx = (1 - ease_out(p)) * 700
        if self.pulse: s *= 1 + self.pulse * (0.5 + 0.5 * math.sin((t - self.t0) * 2 * math.pi * 1.2))
        if self.drift: s *= 1 + self.drift * (t - self.t0)
        im = self.img
        if abs(s - 1) > 0.002:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
        if a < 0.999:
            al = im.getchannel("A").point(lambda v: int(v * a))
            im = im.copy(); im.putalpha(al)
        paste_c(canvas, im, self.cx + dx, self.cy + dy)

# ---------------------------------------------------------------- subtitles
FIX = {"buat": "Mubarak", "ramadhan": "Ramadan", "terawih": "tarawih", "mekah": "Makkah", "beg-peg": "beg-beg",
       "telekom": "telekung", "jum'ah": "jemaah", "wanita": "wanita", "zam-zam": "Zamzam", "nabawi": "Nabawi",
       "insyaallah": "InsyaAllah"}
DROP = {"lima", "pun"}
KEY = {"UMRAH", "RAMADAN", "PAKEJ", "MAKKAH", "MADINAH", "100", "TERAWAL", "PERCUMA", "ZAMZAM", "IHRAM",
       "TELEKUNG", "BEG-BEG", "ISTIMEWA", "DAFTAR", "SEGERA", "2026", "DARUL", "MUBARAK", "TARAWIH", "NABAWI",
       "HARAM", "MASJIDIL", "ALLAH", "SWT", "SUCI", "TANAH", "500", "ML"}

def load_words(path):
    toks = []
    for s in json.load(open(path)):
        for (a, b, w) in s["w"]:
            w = w.strip()
            if toks and (w.startswith("-") or w.startswith("'")):
                toks[-1][2] += w; toks[-1][1] = b
            else:
                toks.append([a, b, w])
    out = []
    for a, b, w in toks:
        if a >= 93.3: continue                       # whisper hallucination at the end
        T = a - 1.9 if a < 32.3 else (a + 11.0 if a >= 37.3 else None)
        if T is None or T < 0: continue
        core = w.strip(".,!?").lower(); punct = w[len(w.rstrip(".,!?")):]
        if core in DROP: continue
        if core in FIX: w = FIX[core] + punct
        out.append([T, b - a, w])
    # pair fixes
    for i in range(len(out) - 1):
        a, b = out[i][2].lower(), out[i + 1][2].lower().strip(".,")
        if a == "masjid" and b == "haram": out[i][2] = "Masjidil"; out[i + 1][2] = "Haram"
        if a == "masjid" and b == "nabawi": out[i][2] = "Masjid"
        if a == "tanah" and b == "haram": out[i][2] = "Tanah"; out[i + 1][2] = "Haram"
        if out[i][2] == "500": out[i][2] = "500"
        if out[i][2] == "ml": out[i][2] = "ml"
    return out

def chunk_words(words, maxw=4, gap=0.45):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end = (len(cur) >= maxw or w[2][-1] in ".,!?" or nxt is None or nxt[0] - (w[0] + w[1]) > gap
               or (nxt is not None and nxt[0] - w[0] > 3))
        if end:
            chunks.append(cur); cur = []
    res = []
    for i, c in enumerate(chunks):
        t0 = c[0][0] - 0.05
        t1 = c[-1][0] + c[-1][1] + 0.35
        if i + 1 < len(chunks): t1 = min(t1, chunks[i + 1][0][0] - 0.05)
        res.append((t0, t1, c))
    return res

_subcache = {}
def sub_img(ci, chunk, active):
    k = (ci, active)
    if k in _subcache: return _subcache[k]
    f = F("xbold", 66)
    sp = f.getlength(" ")
    items = []
    for j, (_, _, w) in enumerate(chunk):
        up = w.upper()
        key = up.strip(".,!?") in KEY
        col = GOLD if key else WHITE
        items.append((up, col, j == active))
    # layout into lines (max width 940)
    lines, cur, cw = [], [], 0
    for it in items:
        ww = f.getlength(it[0])
        if cur and cw + sp + ww > 940:
            lines.append(cur); cur, cw = [], 0
        cur.append(it); cw += (sp if cw else 0) + ww
    lines.append(cur)
    lh = 86
    im = Image.new("RGBA", (1040, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, line in enumerate(lines):
        tw = sum(f.getlength(x[0]) for x in line) + sp * (len(line) - 1)
        x = (1040 - tw) / 2; y = 20 + li * lh
        for (txt, col, act) in line:
            ww = f.getlength(txt)
            if act:
                d.rounded_rectangle((x - 12, y - 4, x + ww + 12, y + 78), 14, fill=EMERALD + (235,), outline=GOLD + (255,), width=3)
                d.text((x, y), txt, font=f, fill=GOLD_L, stroke_width=0)
            else:
                d.text((x, y), txt, font=f, fill=col, stroke_width=7, stroke_fill=BLACK)
            x += ww + sp
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.6)))
    out = Image.alpha_composite(sh, im)
    _subcache[k] = out
    return out

# ---------------------------------------------------------------- build elements
def build():
    E = []
    def add(*a, **k): E.append(El(*a, **k))

    # Logo bug (top-left) for most of the video
    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 149, 149), fill=(255, 255, 255, 235), outline=GOLD + (255,), width=4)
    badge.alpha_composite(logo.resize((120, 120), Image.LANCZOS), (15, 12))
    add(3.0, END[0], badge, 120, 150, anim="fade", dur=0.5, out=0.3)

    # ---- SCENE 1 HOOK
    add(0.25, 2.95, text_img("UMRAH RAMADAN 2027", F("bold", 40), GOLD_L, tracking=8), 540, 620, "fade", 0.5, 0.25)
    add(0.15, 2.95, text_img("RAMADAN KALI INI…", F("black", 90), WHITE, 0, glow=GOLD, glow_r=18), 540, 760, "pop", 0.35, 0.25)
    add(1.05, 2.95, text_img("DI TANAH SUCI?", F("black", 118), GOLD, 0, glow=(255, 170, 40), glow_r=22), 540, 910, "crash", 0.35, 0.25)

    # ---- Lower third (company)
    lt = rounded(760, 150, 22, EMERALD_D, GOLD, 3, 225)
    lt.alpha_composite(Image.new("RGBA", (12, 120), GOLD + (255,)), (50, 45))
    lt.alpha_composite(text_img("DARUL MUBARAK TRAVEL & TOURS", F("xbold", 40), WHITE, shadow=False), (82, 55))
    lt.alpha_composite(text_img("Pakej Umrah Ramadan 2027", F("serif_i", 40), GOLD_L, shadow=False), (82, 108))
    add(3.3, 6.8, lt, 470, 1260, "left", 0.5, 0.3)

    # ---- SCENE 2 serif labels
    def label(l1, l2):
        return stack([ornament(), text_img(l1, F("serif", 92), GOLD, glow=(0, 0, 0), glow_r=10),
                      text_img(l2, F("serif", 72), WHITE, glow=(0, 0, 0), glow_r=10), ornament()], gap=8)
    add(7.3, 11.15, label("RAMADAN", "PENUH KEBERKATAN"), 540, 560, "up", 0.6, 0.35, drift=0.006)
    add(14.5, 19.85, label("IBADAH DI", "TANAH SUCI"), 540, 560, "up", 0.6, 0.35, drift=0.006)
    add(26.2, 30.15, label("KENANGAN", "YANG DIRINDUI"), 540, 560, "up", 0.6, 0.35, drift=0.006)

    # ---- INTERLUDE a: title + both real posters
    i0 = INTER[0]
    add(i0 + 0.1, i0 + 2.95, text_img("PAKEJ UMRAH", F("black", 92), WHITE), 540, 300, "up", 0.45, 0.25)
    add(i0 + 0.3, i0 + 2.95, text_img("RAMADAN 2027", F("black", 116), GOLD, glow=(255, 170, 40), glow_r=16), 540, 420, "pop", 0.4, 0.25)
    for k, (pf, cy) in enumerate([("p1.jpg", 820), ("p2.jpg", 1300)]):
        p = Image.open(f"{SRC}/{pf}").convert("RGBA").resize((960, 480), Image.LANCZOS)
        fr = rounded(972, 492, 16, WHITE, GOLD, 4, 255)
        fr.alpha_composite(p, (36, 36))
        add(i0 + 0.5 + k * 0.35, i0 + 2.95, fr, 540, cy, "right" if k else "left", 0.5, 0.25, drift=0.012)

    # ---- INTERLUDE b: price crash zoom
    p0 = 33.3
    add(p0 + 0.05, p0 + 3.45, text_img("HARGA SERENDAH", F("bold", 56), WHITE, tracking=6), 540, 690, "fade", 0.3, 0.25)
    add(p0 + 0.0, p0 + 3.45, text_img("RM 7,230", F("black", 210), GOLD, glow=(255, 175, 40), glow_r=28), 540, 880, "crash", 0.3, 0.25, pulse=0.015)
    add(p0 + 0.4, p0 + 3.45, text_img("SEORANG • BILIK BEREMPAT", F("xbold", 48), WHITE), 540, 1050, "up", 0.4, 0.25)
    add(p0 + 0.7, p0 + 3.45, text_img("Pakej Super Jimat Iktikaf Ramadan", F("serif_i", 50), GOLD_L), 540, 1135, "up", 0.4, 0.25)

    # ---- INTERLUDE c: price table (both posters)
    t0 = 36.8; t1 = 43.25
    add(t0 + 0.0, t1, text_img("6 PILIHAN TARIKH 2027", F("black", 70), GOLD, glow=(0, 0, 0), glow_r=8), 540, 330, "pop", 0.4, 0.3)
    rows = [("Sambut Ramadan", "1 – 12 FEB", "7,550", "7,230"),
            ("Awal Ramadan", "11 – 22 FEB", "7,650", "7,330"),
            ("Pertengahan Ramadan", "18 FEB – 1 MAC", "8,150", "7,830"),
            ("Akhir Ramadan", "25 FEB – 8 MAC", "9,850", "8,730"),
            ("Akhir Ramadan Sambut Syawal", "4 – 15 MAC", "8,950", "7,830"),
            ("Sebulan Ramadan", "8 FEB – 11 MAC", "13,950", "11,630")]
    hdr = rounded(1000, 96, 20, EMERALD_D, GOLD, 3, 240)
    hdr.alpha_composite(text_img("PAKEJ & TARIKH", F("xbold", 32), GOLD_L, shadow=False), (60, 60))
    c2 = text_img("SUPER JIMAT", F("xbold", 32), GOLD_L, shadow=False); hdr.alpha_composite(c2, (30 + 655 - c2.width // 2, 60))
    c3 = text_img("IKTIKAF", F("xbold", 32), GOLD_L, shadow=False); hdr.alpha_composite(c3, (30 + 880 - c3.width // 2, 60))
    add(t0 + 0.2, t1, hdr, 540, 450, "fade", 0.3, 0.3)
    for r, (nm, dt, pa, pb) in enumerate(rows):
        card = rounded(1000, 132, 18, (8, 70, 44) if r % 2 == 0 else EMERALD_D, None, 0, 228)
        card.alpha_composite(text_img(nm, F("bold", 38 if len(nm) < 22 else 30), WHITE, shadow=False), (60, 48))
        card.alpha_composite(text_img(dt, F("semi", 34), GOLD_L, shadow=False), (60, 98))
        for cx, pr, col in ((655, pa, WHITE), (880, pb, GOLD)):
            im = stack([text_img("RM", F("bold", 26), col, shadow=False), text_img(pr, F("black", 48), col, shadow=False)], gap=2)
            card.alpha_composite(im, (30 + cx - im.width // 2, 30 + (132 - im.height) // 2))
        add(t0 + 0.45 + r * 0.22, t1, card, 540, 575 + r * 140, "right", 0.45, 0.3)
    add(t0 + 1.9, t1, text_img("*Harga seorang, bilik berempat (rujuk poster rasmi)", F("med", 30), WHITE), 540, 1440, "fade", 0.4, 0.3)

    # ---- INTERLUDE d: hotel + flight
    h0 = 43.3; h1 = INTER[1] - 0.05
    def info_card(title, lines, h):
        c = rounded(960, h, 24, EMERALD_D, GOLD, 3, 232)
        c.alpha_composite(text_img(title, F("black", 46), GOLD, shadow=False), (64, 52))
        y = 118
        for (txt, fnt, col) in lines:
            im = text_img(txt, fnt, col, shadow=False); c.alpha_composite(im, (64, y)); y += im.height + 16
        return c
    add(h0 + 0.0, h1, info_card("HOTEL MAKKAH", [
        ("Super Jimat: Wahat Al Dhiyafah @ setaraf", F("bold", 38), WHITE),
        ("Iktikaf: Hotel Oriens Shisha @ setaraf", F("bold", 38), WHITE),
        ("200 meter++", F("semi", 34), GOLD_L)], 330), 540, 600, "left", 0.5, 0.3)
    add(h0 + 0.5, h1, info_card("HOTEL MADINAH", [
        ("Rua Al Dhiyafah @ setaraf", F("bold", 40), WHITE),
        ("250 meter++", F("semi", 34), GOLD_L)], 260), 540, 925, "right", 0.5, 0.3)
    add(h0 + 1.0, h1, info_card("✈ PENERBANGAN".replace("✈ ", ""), [
        ("Emirates Airlines @ Qatar Airways", F("bold", 40), WHITE)], 200), 540, 1185, "left", 0.5, 0.3)

    # ---- PROMO
    pr = rounded(780, 130, 65, GOLD, (255, 240, 200), 4, 255)
    paste_c(pr, text_img("PROMOSI ISTIMEWA", F("black", 66), BLACK, shadow=False), pr.width / 2, pr.height / 2)
    add(48.9, 52.15, pr, 540, 380, "pop", 0.4, 0.25)
    add(52.25, 57.85, text_img("100 ORANG", F("black", 168), GOLD, glow=(255, 170, 40), glow_r=24), 540, 640, "crash", 0.3, 0.3)
    add(52.45, 57.85, text_img("TERAWAL!", F("black", 140), WHITE, glow=(0, 0, 0), glow_r=10), 540, 810, "pop", 0.4, 0.3)
    add(52.9, 57.85, text_img("yang mendaftar pakej Ramadan", F("serif_i", 54), GOLD_L, glow=(0, 0, 0), glow_r=8), 540, 930, "up", 0.4, 0.3)

    hh = rounded(560, 90, 45, EMERALD_D, GOLD, 3, 240)
    paste_c(hh, text_img("HADIAH ISTIMEWA", F("black", 44), GOLD, shadow=False), hh.width / 2, hh.height / 2)
    add(58.2, 74.9, hh, 540, 860, "pop", 0.4, 0.3)
    def chip(n, txt, big=False):
        w = 900; h = 104 if not big else 128
        c = rounded(w, h, 26, EMERALD_D if not big else (120, 85, 10), GOLD, 3, 235)
        d = ImageDraw.Draw(c); r = h // 2 - 12
        d.ellipse((30 + 22, 30 + h / 2 - r, 30 + 22 + 2 * r, 30 + h / 2 + r), fill=GOLD + (255,))
        paste_c(c, text_img(str(n), F("black", 40), BLACK, shadow=False), 30 + 22 + r, 30 + h / 2)
        im = text_img(txt, F("black" if big else "xbold", 48 if big else 42), GOLD_L if big else WHITE, shadow=False)
        c.alpha_composite(im, (30 + 50 + 2 * r, int(30 + h / 2 - im.height / 2)))
        return c
    add(59.4, 74.9, chip(1, "BEG ISTIMEWA"), 540, 975, "left", 0.4, 0.3)
    add(62.5, 74.9, chip(2, "KAIN IHRAM"), 540, 1090, "right", 0.4, 0.3)
    add(63.8, 74.9, chip(3, "MINI TELEKUNG (JEMAAH WANITA)"), 540, 1205, "left", 0.4, 0.3)
    add(68.8, 74.9, chip(4, "AIR ZAMZAM 500 ML PERCUMA", big=True), 540, 1335, "pop", 0.45, 0.3)
    # Real product photos (optional): SRC/gifts/ihram.jpg, SRC/gifts/telekung.jpg
    for k, (fn, cap, t_in, cx) in enumerate([("ihram", "KAIN IHRAM", 62.5, 290), ("telekung", "MINI TELEKUNG", 63.8, 790)]):
        path = next((f"{SRC}/gifts/{fn}.{e}" for e in ("jpg", "jpeg", "png") if os.path.exists(f"{SRC}/gifts/{fn}.{e}")), None)
        if not path: continue
        ph = Image.open(path).convert("RGBA")
        pw, phh = 420, 520
        s = max(pw / ph.width, phh / ph.height)
        ph = ph.resize((int(ph.width * s) + 1, int(ph.height * s) + 1), Image.LANCZOS)
        ph = ph.crop(((ph.width - pw) // 2, 0, (ph.width - pw) // 2 + pw, phh))
        fr = rounded(pw + 24, phh + 90, 18, WHITE, GOLD, 4, 255)
        fr.alpha_composite(ph, (42, 42))
        paste_c(fr, text_img(cap, F("black", 38), EMERALD_D, shadow=False), fr.width / 2, 42 + phh + 40)
        add(t_in, 74.9, fr, cx, 470, "pop", 0.45, 0.3)

    vc = rounded(900, 220, 28, EMERALD_D, GOLD, 3, 235)
    paste_c(vc, text_img("PROMOSI DIBUKA SEKARANG", F("xbold", 46), WHITE, shadow=False), vc.width / 2, 30 + 62)
    paste_c(vc, text_img("SEHINGGA AKHIR TAHUN 2026", F("black", 56), GOLD, shadow=False), vc.width / 2, 30 + 138)
    add(75.3, 80.65, vc, 540, 400, "pop", 0.45, 0.3)
    add(75.8, 80.65, text_img("*Tertakluk kepada terma & syarat", F("med", 30), WHITE), 540, 560, "fade", 0.4, 0.3)

    add(80.9, 88.75, text_img("REBUT SEGERA!", F("black", 118), GOLD, glow=(255, 170, 40), glow_r=22), 540, 680, "crash", 0.3, 0.3, pulse=0.012)
    add(81.3, 88.75, text_img("Peluang yang jarang-jarang dibuka", F("serif_i", 56), WHITE, glow=(0, 0, 0), glow_r=10), 540, 820, "up", 0.45, 0.3)

    # ---- CLOSING (serif, elegant)
    add(89.2, 98.7, text_img("Ramadan ini,", F("serif_i", 84), WHITE, glow=(0, 0, 0), glow_r=12), 540, 560, "up", 0.9, 0.6)
    add(90.1, 98.7, text_img("CIPTA KENANGAN IBADAH", F("serif", 72), GOLD, glow=(0, 0, 0), glow_r=12), 540, 680, "up", 0.9, 0.6)
    add(91.0, 98.7, text_img("DI TANAH SUCI.", F("serif", 110), GOLD, glow=(255, 170, 40), glow_r=20), 540, 810, "up", 0.9, 0.6)
    add(91.6, 98.7, ornament(520), 540, 905, "fade", 0.9, 0.6)

    # ---- CTA over presenter
    jp = rounded(860, 130, 65, GOLD, (255, 240, 200), 4, 255)
    paste_c(jp, text_img("JOM UMRAH RAMADAN!", F("black", 64), BLACK, shadow=False), jp.width / 2, jp.height / 2)
    add(99.0, END[0], jp, 540, 360, "pop", 0.45, 0.2)
    wa = rounded(820, 120, 60, WA_GREEN, WHITE, 3, 255)
    paste_c(wa, text_img("DAFTAR SEKARANG  ›", F("black", 56), WHITE, shadow=False), wa.width / 2, wa.height / 2)
    add(100.6, END[0], wa, 540, 1190, "pop", 0.45, 0.2, pulse=0.03)
    add(100.9, END[0], text_img("WhatsApp 016-524 7001  |  016-524 3001", F("xbold", 42), WHITE, stroke=5), 540, 1310, "up", 0.4, 0.2)

    # ---- END CARD
    e0 = END[0]; e1 = TOTAL
    lb = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(lb).ellipse((0, 0, 299, 299), fill=(255, 255, 255, 255), outline=GOLD + (255,), width=6)
    lb.alpha_composite(logo.resize((250, 250), Image.LANCZOS), (25, 22))
    add(e0 + 0.05, e1, lb, 540, 340, "pop", 0.5, 0)
    add(e0 + 0.3, e1, text_img("JOM UMRAH RAMADAN!", F("black", 76), GOLD, glow=(255, 170, 40), glow_r=16), 540, 590, "up", 0.45, 0)
    add(e0 + 0.5, e1, text_img("TEMPAH TEMPAT ANDA SEKARANG!", F("xbold", 52), WHITE), 540, 690, "up", 0.45, 0)
    pc = rounded(760, 96, 48, EMERALD_D, GOLD, 3, 240)
    paste_c(pc, text_img("DARI RM 7,230 • BILIK BEREMPAT", F("xbold", 42), GOLD_L, shadow=False), pc.width / 2, pc.height / 2)
    add(e0 + 0.7, e1, pc, 540, 800, "pop", 0.45, 0)
    wb = rounded(900, 120, 60, WA_GREEN, WHITE, 3, 255)
    paste_c(wb, text_img("KLIK WHATSAPP UNTUK PENDAFTARAN", F("black", 40), WHITE, shadow=False), wb.width / 2, wb.height / 2)
    add(e0 + 0.9, e1, wb, 540, 945, "pop", 0.45, 0, pulse=0.025)
    add(e0 + 1.1, e1, text_img("016-524 7001", F("black", 96), WHITE, glow=(0, 0, 0), glow_r=8), 540, 1090, "up", 0.45, 0)
    add(e0 + 1.25, e1, text_img("016-524 3001", F("black", 96), WHITE, glow=(0, 0, 0), glow_r=8), 540, 1200, "up", 0.45, 0)
    add(e0 + 1.4, e1, text_img("www.darulmubarak.com", F("bold", 44), GOLD_L), 540, 1310, "up", 0.45, 0)
    add(e0 + 1.6, e1, text_img("DARUL MUBARAK TRAVEL AND TOURS", F("bold", 30), WHITE), 540, 1400, "fade", 0.5, 0)
    add(e0 + 1.6, e1, text_img("NO SYARIKAT 2005011025978 (708111-W)", F("med", 26), WHITE), 540, 1445, "fade", 0.5, 0)
    add(e0 + 1.6, e1, text_img("NO SIRI KELULUSAN MOTAC IU00569 | KPL/LN: 4398", F("med", 26), WHITE), 540, 1485, "fade", 0.5, 0)
    return E

# ---------------------------------------------------------------- render
def main():
    tx = os.environ.get("TX_JSON", f"{OUT}/tx.json")
    words = load_words(tx)
    chunks = chunk_words(words)
    E = build()
    no_sub = [(INTER[0], INTER[1]), (END[0], TOTAL)]

    def render_overlay(t, frame_img):
        canvas = frame_img
        for e in E:
            e.draw(canvas, t)
        if not any(a <= t < b for a, b in no_sub):
            for ci, (c0, c1, ch) in enumerate(chunks):
                if c0 <= t < c1:
                    act = max([j for j, w in enumerate(ch) if w[0] <= t] or [0])
                    im = sub_img(ci, ch, act)
                    p = clamp((t - c0) / 0.12)
                    if p < 1:
                        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * p)))
                    paste_c(canvas, im, 540, 1530)
                    break
        return canvas

    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        for t in ts:
            fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f"{OUT}/base.mp4", "-frames:v", "1",
                                 "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True, check=True).stdout
            im = Image.frombytes("RGBA", (W, H), fr)
            render_overlay(t, im).convert("RGB").resize((540, 960)).save(f"{OUT}/prev_{t:06.2f}.jpg", quality=85)
        return

    final = os.environ.get("FINAL", f"{OUT}/DM_UmrahRamadan2027_9x16.mp4")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{OUT}/base.mp4", "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", f"{OUT}/mix.wav",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "9M", "-bufsize", "18M",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "256k",
                            "-movflags", "+faststart", "-shortest", final], stdin=subprocess.PIPE)
    n = int(round(TOTAL * FPS)); fsz = W * H * 4
    for i in range(n):
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz: break
        im = Image.frombytes("RGBA", (W, H), buf)
        enc.stdin.write(render_overlay(i / FPS, im).tobytes())
        if i % 300 == 0: print(f"frame {i}/{n}", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("done", final)

if __name__ == "__main__":
    main()
