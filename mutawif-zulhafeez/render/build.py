"""Render "Bersama Mutawif Ustaz Zulhafeez" (1080x1920, 30 fps) from edl.py.

Usage:
  SRC_DIR=... OUT_DIR=... python3 build.py audio            # -> $OUT_DIR/mix.wav
  SRC_DIR=... OUT_DIR=... python3 build.py video            # -> $OUT_DIR/<name>.mp4 (needs mix.wav)
  SRC_DIR=... OUT_DIR=... python3 build.py preview 1.0,25.3 # -> $OUT_DIR/preview_<t>.png
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "umrah-ramadan-2027", "render"))
from edl import *  # noqa

NAME = "DM_Mutawif_UstazZulhafeez_9x16"

# ================================================================== palette & fonts
GOLD = (240, 196, 92)
GOLD_L = (252, 226, 160)
NAVY = (12, 20, 48)
NAVY_L = (28, 40, 88)
PURPLE = (92, 28, 128)
DM_PURPLE = (140, 22, 150)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FD = "/usr/share/fonts/opentype/inter/"
FS = "/usr/share/fonts/truetype/crosextra/"
_fc = {}
def F(name, size):
    path = {"black": FD + "Inter-Black.otf", "xbold": FD + "Inter-ExtraBold.otf", "bold": FD + "Inter-Bold.otf",
            "semi": FD + "Inter-SemiBold.otf", "med": FD + "Inter-Medium.otf",
            "serif": FS + "Caladea-Bold.ttf", "serif_r": FS + "Caladea-Regular.ttf"}[name]
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

# ================================================================== easing / helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_back(x, s=1.7): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1

def set_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def scaled(im, s):
    if abs(s - 1) < 0.003: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)

def paste_c(base, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    if x >= W or y >= H or x + im.width <= 0 or y + im.height <= 0: return
    if x < 0 or y < 0 or x + im.width > W or y + im.height > H:   # clip to canvas
        l, t = max(0, -x), max(0, -y)
        im = im.crop((l, t, min(im.width, W - x), min(im.height, H - y))); x += l; y += t
    base.alpha_composite(im, (x, y))

def text_img(txt, font, fill=WHITE, glow=None, glow_r=16, shadow=True, tracking=0, stroke=0, stroke_fill=BLACK):
    pad = 40 + glow_r * 2
    widths = [font.getlength(c) + tracking for c in txt] if tracking else None
    tw = int(sum(widths) - tracking) if tracking else int(font.getlength(txt))
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    def draw_on(d, col, off=(0, 0), sw=stroke, sf=stroke_fill):
        x = pad + off[0]
        if tracking:
            for c, w_ in zip(txt, widths):
                d.text((x, pad + off[1]), c, font=font, fill=col, stroke_width=sw, stroke_fill=sf); x += w_
        else:
            d.text((x, pad + off[1]), txt, font=font, fill=col, stroke_width=sw, stroke_fill=sf)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw_on(ImageDraw.Draw(sh), (0, 0, 0, 180), (0, 6), sf=(0, 0, 0, 180))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw_on(ImageDraw.Draw(g), glow + (190,), sw=stroke + 3, sf=glow + (190,))
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(glow_r)))
    top = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw_on(ImageDraw.Draw(top), fill)
    im = Image.alpha_composite(im, top)
    return im.crop(im.getbbox())

def two_tone(parts, font, gap=None, glow=None):
    """parts: [(text, colour)] on one line."""
    ims = [text_img(t, font, c, glow=(glow if c != WHITE else None)) for t, c in parts]
    gap = gap if gap is not None else int(font.size * 0.12)
    w = sum(i.width for i in ims) + gap * (len(ims) - 1); h = max(i.height for i in ims)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); x = 0
    for i in ims: out.alpha_composite(i, (x, h - i.height)); x += i.width + gap
    return out

def stack(items, gap=10):
    w = max(i.width for i in items); h = sum(i.height for i in items) + gap * (len(items) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in items: out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    return out

def rounded_card(w, h, r, fill, alpha=200, border=None, bw=0, shadow=True):
    pad = 34 if shadow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), r, fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16)))
    c = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill + (alpha,),
                                        outline=(border + (255,)) if border else None, width=bw)
    return Image.alpha_composite(im, c)

def ornament(w=380, col=GOLD):
    im = Image.new("RGBA", (w, 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((0, 15, w / 2 - 22, 15), fill=col + (255,), width=3)
    d.line((w / 2 + 22, 15, w, 15), fill=col + (255,), width=3)
    d.polygon([(w / 2, 3), (w / 2 + 12, 15), (w / 2, 27), (w / 2 - 12, 15)], fill=col + (255,))
    return im

def glow_sprite(r, col, a=255):
    n = r * 2 + 1; y, x = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.sqrt(x * x + y * y) / r; al = np.clip(1 - d, 0, 1) ** 2.2 * a
    arr = np.zeros((n, n, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = al.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

# ================================================================== grading
VIGNETTE = None
def vignette():
    global VIGNETTE
    if VIGNETTE is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H / 2) / (H * 0.62)) ** 2)
        VIGNETTE = (1 - 0.42 * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None].astype(np.float32)
    return VIGNETTE

VGRADE = ("eq=contrast=1.07:saturation=1.10:gamma=0.97,"
          "colorbalance=rs=0.03:bs=-0.04:rm=0.04:gm=0.01:bm=-0.04:rh=0.05:bh=-0.06")

def grade_photo(im):
    a = np.asarray(im.convert("RGB"), np.float32) / 255.0
    a = (a - 0.5) * 1.07 + 0.5
    lum = a.mean(2, keepdims=True); a = lum + (a - lum) * 1.08
    a[..., 0] = a[..., 0] * 1.04 + 0.01; a[..., 2] = a[..., 2] * 0.94
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def load_photo(p, maxside=2400):
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im.thumbnail((maxside, maxside), Image.LANCZOS)
    return grade_photo(im)

def cover(im, w, h, cx=0.5, cy=0.5):
    s = max(w / im.width, h / im.height)
    r = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    x = int(clamp(cx * r.width - w / 2, 0, r.width - w)); y = int(clamp(cy * r.height - h / 2, 0, r.height - h))
    return r.crop((x, y, x + w, y + h))

def view(img, z, zmax, cx, cy, punch=0.0):
    """img is a (W*zmax x H*zmax) cover image; return the WxH view at zoom z centred on (cx, cy)."""
    z = z * (1 + punch)
    vw, vh = img.width / z, img.height / z
    x0 = clamp(cx * img.width - vw / 2, 0, img.width - vw); y0 = clamp(cy * img.height - vh / 2, 0, img.height - vh)
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + vw, y0 + vh))

# ================================================================== video segment reader
class VideoSeg:
    def __init__(self, t0, dur, src, ss, speed, z0, z1, cx, cy):
        self.t0, self.dur, self.src, self.ss, self.speed = t0, dur, src, ss, speed
        self.z0, self.z1, self.cx, self.cy = z0, z1, cx, cy
        self.zmax = max(z0, z1, 1.0)
        self.dw, self.dh = int(round(W * self.zmax / 2) * 2), int(round(H * self.zmax / 2) * 2)
        self.n = int(round(dur * FPS)); self.proc = None; self.i = 0; self.last = None
    def open(self):
        srcdur = self.dur * self.speed + 0.2
        vf = (f"setpts=(PTS-STARTPTS)/{self.speed},fps={FPS},"
              f"scale={self.dw}:{self.dh}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={self.dw}:{self.dh},{VGRADE}")
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(self.ss), "-t", str(srcdur), "-i", self.src,
                                      "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     stdout=subprocess.PIPE)
    def frame(self, t, punch=0.0):
        if self.proc is None: self.open()
        sz = self.dw * self.dh * 3
        buf = self.proc.stdout.read(sz)
        if len(buf) == sz: self.last = Image.frombuffer("RGB", (self.dw, self.dh), buf)
        p = clamp((t - self.t0) / self.dur)
        z = self.z0 + (self.z1 - self.z0) * ease_io(p)
        return view(self.last, z, self.zmax, self.cx, self.cy, punch)
    def close(self):
        if self.proc: self.proc.stdout.close(); self.proc.wait(); self.proc = None

# ================================================================== photo treatments
class KenBurns:
    def __init__(self, t0, dur, img, z0, z1, cx, cy):
        self.t0, self.dur, self.z0, self.z1, self.cx, self.cy = t0, dur, z0, z1, cx, cy
        self.zmax = max(z0, z1)
        self.img = cover(load_photo(img), int(W * self.zmax), int(H * self.zmax), cx, cy)
    def frame(self, t, punch=0.0):
        p = ease_io((t - self.t0) / self.dur)
        return view(self.img, self.z0 + (self.z1 - self.z0) * p, self.zmax, 0.5, 0.5, punch)

def blurred_bg(im, r=28, dark=0.55, tint=NAVY, tint_a=0.35, zoom=1.15):
    bg = cover(im, int(W * zoom), int(H * zoom)).filter(ImageFilter.GaussianBlur(r))
    a = np.asarray(bg, np.float32) * dark
    a = a * (1 - tint_a) + np.array(tint, np.float32) * tint_a
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def photo_card(im, w, r=34, border=5):
    """Rounded photo card with gold border + soft shadow."""
    h = int(im.height * w / im.width)
    ph_ = im.resize((w, h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    ph_.putalpha(mask)
    pad = 50
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 16, pad + w, pad + h + 16), r, fill=(0, 0, 0, 170))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(22)))
    gl = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(gl).rounded_rectangle((pad - 6, pad - 6, pad + w + 6, pad + h + 6), r + 6, outline=GOLD + (160,), width=8)
    out = Image.alpha_composite(out, gl.filter(ImageFilter.GaussianBlur(10)))
    out.alpha_composite(ph_, (pad, pad))
    ImageDraw.Draw(out).rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), r, outline=GOLD + (255,), width=border)
    return out

def light_sweep(card, p, width=0.22, strength=110):
    """Diagonal light streak travelling across an RGBA card, p in [0,1]."""
    if p <= 0 or p >= 1: return card
    w, h = card.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    pos = (x / w + y / h * 0.5) / 1.5
    c = -width + (1 + 2 * width) * p
    band = np.clip(1 - np.abs(pos - c) / width, 0, 1) ** 2 * strength
    a = np.asarray(card, np.float32).copy()
    al = a[..., 3:4] / 255.0
    a[..., :3] = np.clip(a[..., :3] + band[..., None] * al, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")

def rim_light(cut_im, col=GOLD, r=18, a=0.85):
    al = cut_im.getchannel("A").filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(r))
    g = Image.new("RGBA", cut_im.size, col + (0,)); g.putalpha(al.point(lambda v: int(v * a)))
    out = Image.new("RGBA", cut_im.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(cut_im)
    return out

class FloatFrame:                       # treatment B: floating photo frame
    def __init__(self, t0, dur, img):
        self.t0, self.dur = t0, dur
        im = load_photo(img)
        self.bg = blurred_bg(im, tint=PURPLE, tint_a=0.25)
        self.card = photo_card(cover(im, 860, 1150, 0.5, 0.42), 820)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur
        bg = view(self.bg, 1.15 - 0.08 * p, 1.15, 0.5, 0.5, punch)
        c = Image.new("RGBA", (W, H)); c.paste(bg)
        e = ease_out(p / 0.35)
        card = light_sweep(self.card, (p - 0.35) / 0.45)
        card = card.rotate(-4 * (1 - e) + 1.2 * math.sin(p * math.pi), Image.BILINEAR, expand=True)
        card = set_alpha(scaled(card, 0.82 + 0.18 * e + 0.03 * p), clamp(p / 0.15))
        paste_c(c, card, W / 2, 900 + 120 * (1 - e))
        return c.convert("RGB")

class Cutout:                           # treatment A: cinematic cut-out reveal with gold rim + parallax
    def __init__(self, t0, dur, bg, fg):
        self.t0, self.dur = t0, dur
        self.bg = blurred_bg(load_photo(bg), r=22, dark=0.5, tint=NAVY, tint_a=0.4, zoom=1.2)
        fgi = Image.open(fg).convert("RGBA"); bb = fgi.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
        fgi = fgi.crop(bb)
        rgb = grade_photo(fgi.convert("RGB")).convert("RGBA"); rgb.putalpha(fgi.getchannel("A")); fgi = rgb
        s = 1500 / fgi.height; fgi = fgi.resize((int(fgi.width * s), 1500), Image.LANCZOS)
        self.fg = rim_light(fgi)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur
        bg = view(self.bg, 1.2 - 0.12 * ease_io(p), 1.2, 0.5 - 0.04 * p, 0.5, punch)
        c = Image.new("RGBA", (W, H)); c.paste(bg)
        e = ease_out(p / 0.4)
        fg = set_alpha(scaled(light_sweep(self.fg, (p - 0.3) / 0.5, 0.18, 80), 0.9 + 0.1 * e + 0.04 * p), clamp(p / 0.12))
        paste_c(c, fg, W / 2 + 30 * p, H - fg.height / 2 - 130 + 140 * (1 - e))
        return c.convert("RGB")

class Split:                            # treatment C: dynamic split screen
    def __init__(self, t0, dur, top, bottom, top_c, bot_c):
        self.t0, self.dur = t0, dur
        hh = H // 2
        self.top = cover(load_photo(top), int(W * 1.15), int(hh * 1.15), *top_c)
        self.bot = cover(load_photo(bottom), int(W * 1.15), int(hh * 1.15), *bot_c)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur; e = ease_out(p / 0.3); hh = H // 2
        c = Image.new("RGB", (W, H), NAVY)
        ox = int((self.top.width - W) * (0.2 + 0.6 * p)); top = self.top.crop((ox, 20, ox + W, 20 + hh))
        ox2 = int((self.bot.width - W) * (0.8 - 0.6 * p)); bot = self.bot.crop((ox2, 30, ox2 + W, 30 + hh))
        c.paste(top, (int(-W * (1 - e)), 0)); c.paste(bot, (int(W * (1 - e)), hh))
        d = ImageDraw.Draw(c); lw = int(W * ease_out((p - 0.15) / 0.35))
        if lw > 0:
            d.rectangle((W / 2 - lw / 2, hh - 4, W / 2 + lw / 2, hh + 4), fill=GOLD)
        return c

class Gallery:                          # signature reveal: hero cut-out + floating memory cards
    def __init__(self, t0, dur, hero, cards):
        self.t0, self.dur = t0, dur
        y = np.linspace(0, 1, H)[:, None, None]
        grad = (np.array(NAVY) * (1 - y) + np.array(PURPLE) * y * 0.85 + np.array(NAVY) * y * 0.15)
        self.bg = Image.fromarray(np.broadcast_to(grad, (H, W, 3)).astype(np.uint8))
        h = Image.open(hero).convert("RGBA"); h = h.crop(h.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
        rgb = grade_photo(h.convert("RGB")).convert("RGBA"); rgb.putalpha(h.getchannel("A"))
        s = 1180 / rgb.height; self.hero = rim_light(rgb.resize((int(rgb.width * s), 1180), Image.LANCZOS), r=22)
        self.cards = [photo_card(cover(load_photo(p, 1400), 520, 700, 0.5, 0.4), 330, r=24, border=4) for p in cards]
        self.pos = [(205, 560, -9), (875, 520, 8), (190, 1080, 6), (890, 1050, -7)]
        self.halo = glow_sprite(520, GOLD, 120)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur; lt = t - self.t0
        c = Image.new("RGBA", (W, H)); c.paste(self.bg)
        paste_c(c, set_alpha(self.halo, 0.55 + 0.15 * math.sin(lt * 2)), W / 2, 820)
        for i, (card, (x, y, ang)) in enumerate(zip(self.cards, self.pos)):
            e = ease_out((lt - 0.25 - i * 0.22) / 0.6)
            if e <= 0: continue
            im = card.rotate(ang * (0.6 + 0.4 * e), Image.BILINEAR, expand=True)
            im = set_alpha(scaled(im, 0.7 + 0.3 * e), e)
            paste_c(c, im, x + (0 if x > W / 2 else 0), y + 14 * math.sin(lt * 1.3 + i) + 160 * (1 - e))
        e = ease_out(lt / 0.8)
        hero = set_alpha(scaled(self.hero, 0.94 + 0.06 * e + 0.02 * p), clamp(lt / 0.3))
        paste_c(c, hero, W / 2, H - hero.height / 2 - 250 + 120 * (1 - e))
        return c.convert("RGB")

class EndBg:
    def __init__(self, t0, dur, img):
        self.t0, self.dur = t0, dur
        self.bg = blurred_bg(load_photo(img), r=40, dark=0.35, tint=PURPLE, tint_a=0.45, zoom=1.1)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur
        return view(self.bg, 1.1 - 0.06 * p, 1.1, 0.5, 0.5, punch)

def make_segments():
    segs = [VideoSeg(*v) for v in VIDEO]
    kinds = {"kenburns": KenBurns, "frame": FloatFrame, "cutout": Cutout, "split": Split, "gallery": Gallery, "endbg": EndBg}
    for (t0, dur, kind, args) in PHOTOS:
        segs.append(kinds[kind](t0, dur, **args))
    segs.sort(key=lambda s: s.t0)
    return segs

# ================================================================== overlay elements
class El:
    """Timed RGBA element. anim: fade | up | pop | crash | left | right | down."""
    def __init__(self, t0, t1, img, cx, cy, anim="up", dur=0.45, out=0.3, drift=0.0):
        self.t0, self.t1, self.img, self.cx, self.cy = t0, t1, img, cx, cy
        self.anim, self.dur, self.out, self.drift = anim, dur, out, drift
    def draw(self, c, t):
        if not (self.t0 <= t < self.t1): return
        p = (t - self.t0) / self.dur
        a = clamp(p * (3 if self.anim == "crash" else 1)) * (clamp((self.t1 - t) / self.out) if self.out else 1)
        s, dx, dy = 1.0, 0, 0
        if self.anim == "up": dy = (1 - ease_out(p)) * 70
        elif self.anim == "down": dy = -(1 - ease_out(p)) * 70
        elif self.anim == "pop": s = 0.55 + 0.45 * ease_back(p)
        elif self.anim == "crash": s = 1 + 1.3 * (1 - ease_out(p))
        elif self.anim == "left": dx = -(1 - ease_out(p)) * 640
        elif self.anim == "right": dx = (1 - ease_out(p)) * 640
        s *= 1 + self.drift * (t - self.t0)
        paste_c(c, set_alpha(scaled(self.img, s), a), self.cx + dx, self.cy + dy)

class Fx:
    """Custom-drawn timed element: fn(canvas, local_t, alpha)."""
    def __init__(self, t0, t1, fn, out=0.3):
        self.t0, self.t1, self.fn, self.out = t0, t1, fn, out
    def draw(self, c, t):
        if not (self.t0 <= t < self.t1): return
        self.fn(c, t - self.t0, clamp((self.t1 - t) / self.out) if self.out else 1)

def lower_third(name, role, tag="MUTAWIF"):
    """Signature name reveal: gold line grows, name rises, role fades in."""
    nm = text_img(name, F("serif", 84), GOLD_L, glow=GOLD, glow_r=18, tracking=4)
    rl = text_img(role, F("semi", 34), WHITE)
    tg = text_img(tag, F("bold", 26), NAVY, shadow=False, tracking=6)
    tgb = rounded_card(tg.width + 36, tg.height + 18, 12, GOLD, 255, shadow=False); tgb.alpha_composite(tg, (18, 9))
    def fn(c, lt, a):
        x0, y0 = 90, 1210
        e1 = ease_out(lt / 0.5)
        paste_c(c, set_alpha(tgb, a * clamp(lt / 0.25)), x0 + tgb.width / 2, y0 - 70)
        d = ImageDraw.Draw(c); lw = int(860 * e1)
        if lw > 0:
            d.rectangle((x0, y0 + 112, x0 + lw, y0 + 117), fill=GOLD + (int(255 * a),))
            g = glow_sprite(40, GOLD_L, 230); paste_c(c, set_alpha(g, a), x0 + lw, y0 + 114)
        e2 = ease_out((lt - 0.15) / 0.5)
        if e2 > 0:
            im = set_alpha(nm, a * e2); c.alpha_composite(im, (x0 - 10, int(y0 - 10 + 40 * (1 - e2))))
        e3 = ease_out((lt - 0.45) / 0.5)
        if e3 > 0:
            c.alpha_composite(set_alpha(rl, a * e3), (x0, int(y0 + 140 + 20 * (1 - e3))))
    return fn

def location_pin(label, sub=None):
    t1 = text_img(label, F("bold", 34), WHITE, tracking=4)
    items = [t1] + ([text_img(sub, F("med", 26), GOLD_L)] if sub else [])
    body = Image.new("RGBA", (max(i.width for i in items), sum(i.height for i in items) + 4), (0, 0, 0, 0)); y = 0
    for i in items: body.alpha_composite(i, (0, y)); y += i.height + 4
    card = rounded_card(body.width + 110, body.height + 34, 22, NAVY, 190, border=GOLD, bw=2)
    pin = Image.new("RGBA", (40, 52), (0, 0, 0, 0)); d = ImageDraw.Draw(pin)
    d.ellipse((4, 2, 36, 34), fill=GOLD); d.polygon([(8, 26), (32, 26), (20, 50)], fill=GOLD); d.ellipse((13, 11, 27, 25), fill=NAVY)
    card.alpha_composite(pin, (34 + 22, 34 + (body.height + 34 - 52) // 2))
    card.alpha_composite(body, (34 + 82, 34 + 17))
    return card

def header_pill():
    """Persistent top pill (echoes the reference video's title pill)."""
    l1 = text_img("Darul Mubarak Travel & Tours", F("med", 30), (225, 225, 235), shadow=False)
    l2 = two_tone([("BERSAMA", WHITE), ("MUTAWIF", GOLD)], F("xbold", 48))
    body = stack([l1, l2], 2)
    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (92, 92), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 91, 91), fill=(255, 255, 255, 245), outline=GOLD + (255,), width=3)
    badge.alpha_composite(logo.resize((76, 76), Image.LANCZOS), (8, 7))
    w = badge.width + body.width + 70
    card = rounded_card(w, 128, 64, NAVY, 175, border=GOLD, bw=2)
    card.alpha_composite(badge, (34 + 16, 34 + 18)); card.alpha_composite(body, (34 + 12 + badge.width + 24, 34 + (128 - body.height) // 2))
    return card

def keyword(parts, size=118, sub=None):
    big = two_tone(parts, F("black", size), glow=GOLD)
    if big.width > 1000: big = scaled(big, 1000 / big.width)
    items = [big]
    if sub: items.append(text_img(sub, F("bold", 44), WHITE, tracking=2))
    return stack(items, 0)

def counter_fx(n_to, label, y):
    """Kinetic count-up: 1 -> n_to, then lands with a pop."""
    lab = text_img(label, F("black", 96), GOLD, glow=GOLD)
    def fn(c, lt, a):
        k = int(clamp(lt / 0.55) * (n_to - 1)) + 1
        s = 1.0 + 0.25 * (1 - ease_out((lt - 0.55) / 0.3)) if lt > 0.55 else 1.0
        num = text_img(str(k), F("black", 250), WHITE, glow=GOLD, glow_r=24)
        paste_c(c, set_alpha(scaled(num, s), a * clamp(lt / 0.1)), W / 2, y)
        paste_c(c, set_alpha(lab, a * clamp((lt - 0.4) / 0.2)), W / 2, y + 175)
    return fn

# ------------------------------------------------------------------ subtitles
KEYWORDS = {"QUBA", "PERTAMA", "BERJEMAAH", "19", "PINTU", "LELAKI", "MUSLIMAT", "BESAR", "ASSALAMUALAIKUM"}
def sub_chunks():
    """Group words of the Quba explanation into 2-4-word chunks on the output timeline."""
    words = [(T_QUBA + s, w) for s, w in QUBA_WORDS]
    ends = []
    for i, (t, w) in enumerate(words):
        nxt = words[i + 1][0] if i + 1 < len(words) else T_QUBA + QUBA_END
        ends.append(min(nxt, t + 0.9) if w not in QUBA_SENT_END else T_QUBA + QUBA_SENT_END[w])
    chunks, cur = [], []
    for i, (t, w) in enumerate(words):
        cur.append((t, ends[i], w))
        if len(cur) >= 4 or w[-1] in ".," or i + 1 == len(words) or words[i + 1][0] - ends[i] > 0.5:
            chunks.append(cur); cur = []
    return chunks

_sub = {}
def sub_img(ci, chunk, active):
    k = (ci, active)
    if k in _sub: return _sub[k]
    f = F("xbold", 62); sp = f.getlength(" ")
    toks = [w.upper() for (_, _, w) in chunk]
    tw = sum(f.getlength(x) for x in toks) + sp * (len(toks) - 1)
    im = Image.new("RGBA", (int(tw) + 80, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 40
    for j, tk in enumerate(toks):
        ww = f.getlength(tk); key = tk.strip(".,") in KEYWORDS
        if j == active:
            d.rounded_rectangle((x - 14, 18, x + ww + 14, 104), 16, fill=GOLD + (255,))
            d.text((x, 24), tk, font=f, fill=NAVY)
        else:
            d.text((x, 24), tk, font=f, fill=(GOLD_L if key else WHITE) + (255,), stroke_width=5, stroke_fill=(0, 0, 0, 255))
        x += ww + sp
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
    out = Image.alpha_composite(sh, im)
    if out.width > 1020: out = scaled(out, 1020 / out.width)
    _sub[k] = out
    return out

class Subs:
    def __init__(self, y=1470):
        self.chunks = sub_chunks(); self.y = y
    def draw(self, c, t):
        for ci, ch in enumerate(self.chunks):
            t0, t1 = ch[0][0] - 0.05, ch[-1][1] + 0.1
            if ci + 1 < len(self.chunks): t1 = min(t1, self.chunks[ci + 1][0][0] - 0.03)
            if t0 <= t < t1:
                act = max([j for j, (wt, _, _) in enumerate(ch) if wt <= t] or [0])
                im = sub_img(ci, ch, act)
                s = 0.92 + 0.08 * ease_back((t - t0) / 0.18)
                paste_c(c, scaled(im, s), W / 2, self.y)

# ------------------------------------------------------------------ particles
class Particles:
    def __init__(self, ranges, n=38, seed=7):
        rng = np.random.default_rng(seed)
        self.ranges = ranges
        self.p = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 14), rng.uniform(-70, -25),
                   rng.uniform(0, 6.28), rng.uniform(0.25, 0.8)) for _ in range(n)]
        self.spr = {r: glow_sprite(r, GOLD_L) for r in range(4, 15)}
    def draw(self, c, t):
        if not any(a <= t < b for a, b in self.ranges): return
        for (x, y, r, vy, ph_, a) in self.p:
            yy = (y + vy * t) % (H + 60) - 30; xx = x + 18 * math.sin(t * 0.7 + ph_)
            tw = 0.5 + 0.5 * math.sin(t * 2.2 + ph_)
            paste_c(c, set_alpha(self.spr[int(r)], a * tw), xx, yy)

# ------------------------------------------------------------------ build all overlays
def build_overlays():
    E = []
    def add(*a, **k): E.append(El(*a, **k))
    def fx(*a, **k): E.append(Fx(*a, **k))

    E.append(Particles([(0, T_JOURNEY), (T_PHOTOS, T_QUBA), (T_REVEAL, TOTAL)]))

    # ---- SCENE 1  HOOK: the salam, word-synced kinetic type
    words = [text_img(w.upper(), F("black", s), col, glow=GOLD if col == GOLD else None, tracking=2)
             for (w, s, col) in [("Assalamualaikum", 92, GOLD), ("warahmatullahi", 70, WHITE), ("wabarakatuh", 70, WHITE)]]
    for (st, _), im, y in zip(SALAM, words, (1240, 1350, 1440)):
        add(T_HOOK + st, T_TITLE + 0.05, im, W / 2, y, "pop", 0.32, 0.25)

    # ---- persistent header pill (reference-style)
    add(T_TITLE, T_CLOSE, header_pill(), W / 2, 215, "down", 0.5, 0.3)

    # ---- SCENE 1b  signature lower third (first reveal of the mutawif)
    fx(T_TITLE + 0.1, T_JOURNEY - 0.05, lower_third("USTAZ ZULHAFEEZ", "Mutawif  |  Darul Mubarak Travel & Tours"), out=0.35)

    # ---- SCENE 2  journey begins (airport, Malaysia)
    add(T_JOURNEY + 0.2, T_JOURNEY + 4.6, keyword([("PERJALANAN", WHITE)], 112), W / 2, 1300, "up", 0.4, 0.3)
    add(T_JOURNEY + 0.45, T_JOURNEY + 4.6, keyword([("BERMULA", GOLD)], 130), W / 2, 1430, "pop", 0.4, 0.3)
    add(T_JOURNEY + 5.1, T_PHOTOS - 0.05, stack([text_img("DARI TANAH AIR", F("black", 92), WHITE),
                                                  two_tone([("KE", WHITE), ("TANAH SUCI", GOLD)], F("black", 92), glow=GOLD)], 0),
        W / 2, 1360, "up", 0.45, 0.3)

    # ---- SCENE 3  photo montage (treatments: Ken Burns, floating frame, cut-out, split)
    add(T_PHOTOS + 0.15, T_PHOTOS + 2.35, location_pin("JABAL RAHMAH", "Arafah"), 300, 420, "left", 0.5, 0.3)
    add(T_PHOTOS + 0.3, T_QUBA - 0.05, stack([text_img("DI SETIAP LANGKAH", F("black", 86), WHITE),
                                               text_img("PERJALANAN", F("black", 104), GOLD, glow=GOLD)], 0),
        W / 2, 1585, "up", 0.45, 0.3)

    # ---- SCENE 4  tazkirah at Masjid Quba (his real voice)
    add(T_QUBA + 0.2, T_QUBA + 4.0, location_pin("MASJID QUBA", "Madinah"), 300, 420, "left", 0.5, 0.3)
    E.append(Subs(1500))
    q = lambda s: T_QUBA + s
    add(q(1.10), q(3.75), keyword([("MASJID", WHITE), ("PERTAMA", GOLD)], 116), W / 2, 1270, "crash", 0.35, 0.2)
    add(q(3.80), q(5.10), keyword([("SOLAT", WHITE), ("BERJEMAAH", GOLD)], 108), W / 2, 1270, "pop", 0.3, 0.2)
    fx(q(6.95), q(7.95), counter_fx(19, "PINTU", 1060), out=0.2)
    add(q(7.96), q(10.0), keyword([("2", GOLD), ("PINTU BESAR", WHITE)], 112, "JEMAAH LELAKI"), W / 2, 1250, "pop", 0.3, 0.2)
    add(q(10.04), q(13.2), keyword([("1", GOLD), ("PINTU BESAR", WHITE)], 112), W / 2, 1270, "pop", 0.3, 0.3)

    # ---- SCENE 5  signature reveal
    reveal = stack([text_img("BERSAMA MUTAWIF", F("bold", 50), WHITE, tracking=8),
                    text_img("USTAZ ZULHAFEEZ", F("serif", 104), GOLD_L, glow=GOLD, glow_r=22, tracking=3),
                    ornament(420)], 6)
    add(T_GALLERY + 0.9, T_CLOSE - 0.05, reveal, W / 2, 1560, "up", 0.6, 0.35)
    add(T_GALLERY + 1.5, T_CLOSE - 0.05, text_img("Mutawif  |  Darul Mubarak Travel & Tours", F("semi", 34), WHITE),
        W / 2, 1720, "fade", 0.5, 0.35)

    # ---- SCENE 6  closing line over Masjid Quba
    l1 = text_img("SETIAP PERJALANAN UMRAH", F("serif", 70), WHITE, tracking=3)
    l2 = text_img("MENINGGALKAN", F("serif", 70), WHITE, tracking=3)
    l3 = text_img("SERIBU KENANGAN", F("serif", 100), GOLD_L, glow=GOLD, glow_r=20, tracking=3)
    add(T_CLOSE + 0.3, T_END, l1, W / 2, 1160, "up", 0.6, 0.4)
    add(T_CLOSE + 0.9, T_END, l2, W / 2, 1260, "up", 0.6, 0.4)
    add(T_CLOSE + 1.5, T_END, l3, W / 2, 1385, "pop", 0.6, 0.4)
    add(T_CLOSE + 2.1, T_END, ornament(460), W / 2, 1490, "fade", 0.5, 0.4)

    # ---- SCENE 7  end card + CTA
    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 299, 299), fill=(255, 255, 255, 250), outline=GOLD + (255,), width=6)
    badge.alpha_composite(logo.resize((250, 250), Image.LANCZOS), (25, 22))
    halo = glow_sprite(260, GOLD, 150)
    add(T_END + 0.1, TOTAL, halo, W / 2, 470, "fade", 0.8, 0)
    add(T_END + 0.1, TOTAL, badge, W / 2, 470, "pop", 0.55, 0)
    add(T_END + 0.4, TOTAL, text_img("DARUL MUBARAK", F("serif", 92), WHITE, tracking=4), W / 2, 715, "up", 0.5, 0)
    add(T_END + 0.55, TOTAL, text_img("TRAVEL & TOURS", F("bold", 44), GOLD_L, tracking=12), W / 2, 800, "up", 0.5, 0)
    add(T_END + 0.7, TOTAL, text_img("Untuk Perkhidmatan Yang Lebih Meyakinkan", F("med", 32), (230, 225, 240)), W / 2, 865, "fade", 0.5, 0)
    add(T_END + 1.2, TOTAL, stack([text_img("NAK RASAI PENGALAMAN", F("black", 66), WHITE),
                                    text_img("UMRAH SEPERTI INI?", F("black", 76), GOLD, glow=GOLD)], 0),
        W / 2, 1080, "pop", 0.45, 0)
    btn_t = text_img("HUBUNGI KAMI", F("black", 56), NAVY, shadow=False, tracking=2)
    btn = rounded_card(btn_t.width + 120, btn_t.height + 50, 48, GOLD, 255)
    btn.alpha_composite(btn_t, (34 + 60, 34 + 25))
    def btn_fx(c, lt, a):
        s = 1 + 0.035 * math.sin(lt * 2 * math.pi * 0.9)
        e = ease_back(lt / 0.45)
        paste_c(c, set_alpha(scaled(btn, (0.6 + 0.4 * e) * s), clamp(lt / 0.2)), W / 2, 1290)
    fx(T_END + 1.7, TOTAL, btn_fx, out=0)
    add(T_END + 2.0, TOTAL, text_img("untuk maklumat pakej umrah", F("semi", 40), WHITE), W / 2, 1405, "fade", 0.5, 0)
    return E

# ================================================================== video render loop
def flash_amount(t):
    for c in CUTS:
        if 0 <= t - c < 0.2: return (1 - (t - c) / 0.2) ** 2
    return 0.0

def render(times=None):
    segs = make_segments()
    ovl = build_overlays()
    vig = vignette()
    nframes = int(round(TOTAL * FPS))
    frames = range(nframes) if times is None else [int(round(t * FPS)) for t in times]
    enc = None
    if times is None:
        os.makedirs(OUT, exist_ok=True)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{OUT}/mix.wav",
                                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-profile:v", "high", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart",
                                f"{OUT}/{NAME}.mp4"], stdin=subprocess.PIPE)
    active = None
    for fi in frames:
        t = fi / FPS
        seg = [s for s in segs if s.t0 <= t + 1e-6][-1]
        if seg is not active:
            if isinstance(active, VideoSeg): active.close()
            active = seg
        if times is not None and isinstance(seg, VideoSeg):     # preview: seek reader to the frame
            seg.close(); seg.ss_saved = seg.ss
            k = int(round((t - seg.t0) * FPS))
            for _ in range(k): seg.frame(seg.t0)
        fl = flash_amount(t)
        base = seg.frame(t, punch=0.05 * fl)
        a = np.asarray(base, np.float32) * vig
        if fl > 0: a = a + (np.array(GOLD_L, np.float32) - a) * (0.45 * fl)
        if t > TOTAL - 0.8: a *= clamp((TOTAL - t) / 0.8)
        if t < 0.25: a *= t / 0.25
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        for e in ovl: e.draw(c, t)
        rgb = c.convert("RGB")
        if enc: enc.stdin.write(rgb.tobytes())
        else: rgb.save(f"{OUT}/preview_{t:05.2f}.png"); print("preview", t)
        if times is None and fi % 150 == 0: print(f"frame {fi}/{nframes}", flush=True)
    if enc:
        enc.stdin.close(); enc.wait(); print("video ok:", f"{OUT}/{NAME}.mp4")

# ================================================================== audio
SR = 48000
def read_audio(src, ss, dur, af="anull"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", src, "-vn", "-af", af,
                          "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768

VOICE_AF = ("highpass=f=85,lowpass=f=11000,afftdn=nf=-24,equalizer=f=3000:t=q:w=1.2:g=2,"
            "acompressor=threshold=-22dB:ratio=3:attack=5:release=150")

def audio():
    from islamic_music import compose
    rng = np.random.default_rng(3)
    N = int(TOTAL * SR)
    def place(buf, clip, t, g):
        s = int(t * SR)
        if s >= N or s < 0: return
        c = clip[:N - s]; buf[s:s + len(c)] += c * g

    # voice: salam + Quba explanation, each loudness-matched
    voice = np.zeros(N)
    for (src, ss, dur, t) in [(ft("IMG_2031.MOV"), 0.0, SALAM_END, T_HOOK), (ft("IMG_2048.MOV"), 0.0, QUBA_END, T_QUBA)]:
        v = read_audio(src, ss, dur, VOICE_AF)
        v = v / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9) * 0.16
        fade = int(0.04 * SR); v[:fade] *= np.linspace(0, 1, fade); v[-fade * 3:] *= np.linspace(1, 0, fade * 3)
        place(voice, v, t, 1.0)

    amb = np.zeros(N)
    for (t, dur, src, ss) in AMBIENCE:
        a = read_audio(src, ss, dur, "highpass=f=120,lowpass=f=7000")
        f = int(0.15 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
        place(amb, a / (np.abs(a).max() + 1e-9), t, 0.10)

    music = compose(TOTAL, [(0.0, T_JOURNEY, "sparse"), (T_JOURNEY, T_QUBA, "full"), (T_QUBA, T_REVEAL, "calm"),
                            (T_REVEAL, T_CLOSE, "full"), (T_CLOSE, TOTAL, "end")])
    t = np.arange(N) / SR
    lvl = np.full(N, -12.0)
    lvl[(t >= T_JOURNEY) & (t < T_QUBA)] = -7.0
    lvl[(t >= T_REVEAL) & (t < T_CLOSE)] = -5.0                 # emotional lift
    lvl[t >= T_CLOSE] = -6.5
    win = int(0.05 * SR)
    ve = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
    act = np.convolve((ve > 0.015).astype(float), np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
    duck = -10.0 * np.clip(act * 1.6, 0, 1)
    gain = 10 ** ((lvl + duck) / 20)
    gain = np.convolve(gain, np.ones(int(0.2 * SR)) / int(0.2 * SR), "same")
    tail = t > TOTAL - 1.8; gain[tail] *= np.linspace(1, 0, tail.sum()) ** 2
    music = music * gain[:, None]

    # sound design
    def whoosh(d=0.6):
        n = int(d * SR); tt = np.linspace(0, 1, n); x = rng.standard_normal(n)
        b = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); b *= np.exp(-f / 2500)
        y = np.fft.irfft(b, n); return y / np.abs(y).max() * np.sin(np.pi * tt) ** 2
    def impact():
        n = int(1.8 * SR); tt = np.arange(n) / SR
        return np.sin(2 * np.pi * (40 + 80 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.6)
    def shimmer():
        n = int(1.4 * SR); tt = np.arange(n) / SR; o = np.zeros(n)
        for k, fq in enumerate([1568, 2093, 2637, 3136, 4186]):
            s = int(k * 0.07 * SR); o[s:] += np.sin(2 * np.pi * fq * tt[:n - s]) * np.exp(-tt[:n - s] * 4) * 0.2
        return o
    def riser(d=1.8):
        n = int(d * SR); tt = np.arange(n) / SR
        tone = np.sin(2 * np.pi * np.cumsum(220 * 6 ** (tt / d)) / SR) * 0.2
        return (tone + whoosh(d) * 0.8) * (tt / d) ** 2
    def tick():
        n = int(0.05 * SR); tt = np.arange(n) / SR
        return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 120)

    sfx = np.zeros(N)
    for c in CUTS: place(sfx, whoosh(), c - 0.3, 0.06)
    for tt_ in (T_TITLE, T_GALLERY, T_END): place(sfx, impact(), tt_, 0.22)
    for tt_ in (T_TITLE + 0.2, T_PHOTOS + 4.8, T_GALLERY + 0.3, T_GALLERY + 1.0, T_END + 0.2): place(sfx, shimmer(), tt_, 0.12)
    place(sfx, riser(), T_REVEAL - 1.8, 0.10); place(sfx, riser(), T_END - 1.8, 0.08)
    for k in range(19): place(sfx, tick(), T_QUBA + 6.95 + k * 0.55 / 18, 0.05)

    mono = voice + amb + sfx
    st = music * 0.55 + mono[:, None]
    st /= max(1.0, np.abs(st).max() / 0.95)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    os.makedirs(OUT, exist_ok=True)
    raw = f"{OUT}/mix_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-ar", str(SR), f"{OUT}/mix.wav"], check=True)
    print("audio ok")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    if cmd == "audio": audio()
    elif cmd == "video": render()
    elif cmd == "preview": render([float(x) for x in sys.argv[2].split(",")])
