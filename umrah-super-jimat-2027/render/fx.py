"""Graphics toolkit: 3D extruded metallic typography, virtual Islamic studio, overlays, compositing helpers."""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
GOLD = (242, 193, 78)
GOLD_L = (255, 232, 160)
EMERALD = (11, 93, 59)
EMERALD_D = (4, 38, 26)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
WA_GREEN = (37, 211, 102)
FD = "/usr/share/fonts/opentype/inter/"
SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"


def F(name, size):
    if name == "serif":
        return ImageFont.truetype(SERIF, size)
    return ImageFont.truetype(FD + name + ".otf", size)


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_back(x, s=1.6):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1


def to_np(im):
    """PIL RGBA -> premultiplied float32 (h,w,4)"""
    a = np.asarray(im.convert("RGBA"), np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


# ----------------------------------------------------------------------------------------- 3D typography
def text3d(txt, size, depth=22, font="InterDisplay-Black", tracking=4, face="gold"):
    """Extruded metallic title. Returns (premult RGBA float, face-mask float) – no glow/shadow (added at draw)."""
    f = F(font, size)
    # glyph mask with tracking
    widths = [f.getlength(c) for c in txt]
    tw = int(sum(widths) + tracking * (len(txt) - 1))
    asc, desc = f.getmetrics()
    pad = 30
    cw, ch = tw + 2 * pad + depth, asc + desc + 2 * pad + depth
    M = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(M)
    x = pad
    for c, w in zip(txt, widths):
        d.text((x, pad), c, font=f, fill=255)
        x += w + tracking
    m = np.asarray(M, np.float32) / 255
    out = np.zeros((ch, cw, 4), np.float32)
    # extrusion: stacked offsets down-right, dark bronze at the back -> warm gold near the face
    for k in range(depth, 0, -1):
        sh = np.zeros_like(m)
        dx, dy = int(round(k * 0.35)), k
        sh[dy:, dx:] = m[:ch - dy, :cw - dx]
        u = k / depth
        col = np.array([95 + 90 * (1 - u), 58 + 60 * (1 - u), 12 + 20 * (1 - u)], np.float32) / 255
        if k % 4 == 0:
            col *= 0.86                                      # subtle ridges on the side walls
        a = sh
        out[..., :3] = out[..., :3] * (1 - a[..., None]) + col * a[..., None]
        out[..., 3] = out[..., 3] * (1 - a) + a
    # face: vertical metallic gradient + brushed bands
    yy = np.linspace(0, 1, ch, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, cw, dtype=np.float32)[None, :]
    if face == "gold":
        top, mid, bot = np.array(GOLD_L) / 255, np.array((236, 182, 66)) / 255, np.array((160, 104, 22)) / 255
    else:  # white-silver
        top, mid, bot = np.array((255, 255, 255)) / 255, np.array((228, 232, 236)) / 255, np.array((150, 156, 165)) / 255
    t = np.clip((yy - pad / ch) / ((asc + desc) / ch), 0, 1)[..., None]
    g = np.where(t < 0.5, top + (mid - top) * (t / 0.5), mid + (bot - mid) * ((t - 0.5) / 0.5))
    g = g * (0.94 + 0.06 * np.sin(xx * 90 + yy * 7)[..., None])
    g = np.broadcast_to(g, (ch, cw, 3))
    # bevel: light on top edges, shade on bottom edges
    up = np.zeros_like(m); up[3:] = m[:-3]
    dn = np.zeros_like(m); dn[:-3] = m[3:]
    hi = np.clip(m - up, 0, 1); lo = np.clip(m - dn, 0, 1)
    hi = cv2.GaussianBlur(hi, (0, 0), 1.0); lo = cv2.GaussianBlur(lo, (0, 0), 1.2)
    fc = np.clip(g + hi[..., None] * 0.55 - lo[..., None] * 0.35, 0, 1)
    out[..., :3] = out[..., :3] * (1 - m[..., None]) + fc * m[..., None]
    out[..., 3] = np.maximum(out[..., 3], m)
    # thin dark outline for separation
    o = cv2.dilate(m, np.ones((3, 3), np.uint8))
    ring = np.clip(o - out[..., 3], 0, 1)
    out[..., 3] = np.maximum(out[..., 3], ring * 0.9)
    out[..., :3] *= out[..., 3:4]  # premultiply (ring colour = black)
    return out, m


class Title3D:
    """A 3D title living BEHIND the presenter. Enters by flying from depth (scale + Y-rotation), then drifts."""
    def __init__(self, txt, t0, t1, cy, size=200, cx=540, face="gold", fit=980):
        img, face_m = text3d(txt, size, face=face)
        h, w = img.shape[:2]
        if w > fit + 60:                                     # auto-fit width
            s = (fit + 60) / w
            img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
            face_m = cv2.resize(face_m, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        self.img, self.face = img, face_m
        a = img[..., 3]
        glow = cv2.GaussianBlur(a, (0, 0), 22)
        self.glow = glow
        self.t0, self.t1, self.cx, self.cy = t0, t1, cx, cy

    def draw(self, canvas, t, cam=1.0):
        if t < self.t0 or t > self.t1:
            return
        p = (t - self.t0) / 0.65
        a_in = clamp((t - self.t0) / 0.22) * clamp((self.t1 - t) / 0.25)
        s = (0.55 + 0.45 * ease_back(p, 1.3)) * (1 + 0.035 * (t - self.t0)) * cam
        rot = (1 - ease_out(p)) * 28                         # degrees around Y axis while entering
        img = self.img.copy()
        h, w = img.shape[:2]
        # metallic light sweep across the face (first 1.4 s)
        q = (t - self.t0 - 0.35) / 1.0
        if 0 <= q <= 1:
            xs = np.arange(w, dtype=np.float32)[None, :]
            ys = np.arange(h, dtype=np.float32)[:, None]
            band = np.exp(-((xs + ys * 0.45 - (q * (w + h)) + h * 0.3) / 38) ** 2)
            img[..., :3] += (band * self.face * 0.75)[..., None] * img[..., 3:4]
        # perspective (Y rotation) homography
        f = 1400.0
        th = math.radians(rot)
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        pts = []
        for (x, y) in src:
            X, Y = (x - w / 2), (y - h / 2)
            Xr, Zr = X * math.cos(th), X * math.sin(th)
            k = f / (f + Zr)
            pts.append([self.cx + Xr * k * s, self.cy + Y * k * s])
        Hm = cv2.getPerspectiveTransform(src, np.float32(pts))
        # glow + soft shadow behind the letters
        sh = cv2.warpPerspective(self.glow, Hm, (W, H))
        Hs = Hm.copy(); Hs[0, 2] += 14; Hs[1, 2] += 26
        shadow = cv2.warpPerspective(cv2.GaussianBlur(self.img[..., 3], (0, 0), 9), Hs, (W, H))
        canvas *= (1 - shadow * 0.55 * a_in)[..., None]
        canvas += (sh * 0.45 * a_in)[..., None] * (np.array(GOLD, np.float32) / 255)
        layer = cv2.warpPerspective(img, Hm, (W, H), flags=cv2.INTER_LINEAR)
        layer *= a_in
        canvas *= (1 - layer[..., 3:4])
        canvas += layer[..., :3]


# ----------------------------------------------------------------------------------------- virtual studio
def eight_star(d, cx, cy, r, col, w=2):
    for rot in (0, 45):
        pts = []
        for k in range(4):
            ang = math.radians(rot + 90 * k + 45)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        d.line(pts + [pts[0]], fill=col, width=w)


def make_studio(seed=3):
    """Premium emerald + gold Islamic virtual set (static plate, 1.12x oversize for camera moves)."""
    SW, SH = int(W * 1.12), int(H * 1.12)
    yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
    yn, xn = yy / SH, xx / SW
    base = np.zeros((SH, SW, 3), np.float32)
    top, mid, bot = np.array((3, 28, 20)), np.array((9, 78, 52)), np.array((2, 18, 13))
    t = yn[..., None]
    base = np.where(t < 0.45, top + (mid - top) * (t / 0.45), mid + (bot - mid) * ((t - 0.45) / 0.55)) / 255
    # radial key glow behind the presenter
    r = np.sqrt(((xn - 0.5) * 1.3) ** 2 + ((yn - 0.36) * 0.9) ** 2)
    base += (np.exp(-(r / 0.28) ** 2) * 0.32)[..., None] * np.array((0.25, 0.75, 0.5))
    img = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # geometric star lattice on the back wall
    step = 150
    for gy in range(-step, int(SH * 0.72), step):
        for gx in range(-step, SW + step, step):
            ox = step / 2 if (gy // step) % 2 else 0
            eight_star(d, gx + ox, gy, 52, (242, 193, 78, 34), 2)
            d.ellipse((gx + ox - 4, gy - 4, gx + ox + 4, gy + 4), fill=(242, 193, 78, 40))
    # pointed Islamic arch (gold) framing the presenter
    cx, ay, aw = SW / 2, SH * 0.20, SW * 0.36
    for k, (wd, al) in enumerate([(14, 40), (6, 150), (3, 230)]):
        arch = []
        for i in range(0, 91):
            u = i / 90
            ang = math.pi * (1 - u)
            x = cx + aw * math.cos(ang)
            yv = ay + aw * 0.95 - aw * 1.25 * math.sin(ang) ** 0.75
            arch.append((x, yv))
        arch = [(cx - aw, SH * 0.72)] + arch + [(cx + aw, SH * 0.72)]
        d.line(arch, fill=(242, 193, 78, al), width=wd, joint="curve")
    # floor (glossy) with perspective lines
    fy = int(SH * 0.72)
    d.rectangle((0, fy, SW, SH), fill=(2, 14, 10, 150))
    for i in range(-12, 13):
        d.line((SW / 2 + i * 40, fy, SW / 2 + i * 260, SH), fill=(242, 193, 78, 26), width=2)
    for j in range(1, 8):
        yv = fy + (SH - fy) * (j / 8) ** 1.7
        d.line((0, yv, SW, yv), fill=(242, 193, 78, 18), width=2)
    d.line((0, fy, SW, fy), fill=(242, 193, 78, 120), width=3)
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.alpha_composite(img, lay)
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    # spotlights from top corners (additive warm)
    for sx in (0.12, 0.88):
        dxn = xn - sx
        ang = np.abs(dxn - (0.5 - sx) * yn) / (0.05 + 0.22 * yn)
        cone = np.exp(-ang ** 2) * np.clip(1.15 - yn, 0, 1) * 0.16
        a += cone[..., None] * np.array((1.0, 0.85, 0.55))
    # depth-of-field: the set sits behind the presenter
    a = cv2.GaussianBlur(a, (0, 0), 2.2)
    return np.clip(a, 0, 1).astype(np.float32)


class StudioAnim:
    """Animated light streaks + floating gold particles over the studio plate."""
    def __init__(self, seed=5):
        rng = np.random.default_rng(seed)
        self.p = rng.random((70, 4)).astype(np.float32)   # x, y, size, speed
        self.plate = make_studio()

    def frame(self, t, zoom=1.0, cx=0.5, cy=0.4):
        SH, SW = self.plate.shape[:2]
        s = zoom / 1.12
        M = np.float32([[1 / s, 0, 0], [0, 1 / s, 0]])
        # map output pixel -> plate: x_p = (x - W*cx)/s + SW*cx ; use affine on plate
        A = np.float32([[s, 0, W * cx - SW * cx * s], [0, s, H * cy - SH * cy * s]])
        img = cv2.warpAffine(self.plate, A, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # streaks
        yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
        for k, (sp, off) in enumerate([(160, 0), (110, 700), (210, 1500)]):
            pos = (t * sp + off) % (W + H + 600) - 300
            band = np.exp(-((xx * 0.6 + yy * 0.8 - pos) / 6) ** 2) * (0.10 if k != 1 else 0.07)
            img += band[..., None] * np.array((1.0, 0.8, 0.45), np.float32)
        # particles
        lay = np.zeros((H // 4, W // 4), np.float32)
        for (x, y, sz, spd) in self.p:
            py = ((y - t * (0.02 + 0.04 * spd)) % 1.0) * (H // 4)
            px = (x + 0.01 * math.sin(t * 0.7 + y * 9)) * (W // 4)
            cv2.circle(lay, (int(px), int(py)), int(1 + sz * 3), float(0.25 + 0.5 * sz), -1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (0, 0), 1.6)
        lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR)
        img += lay[..., None] * np.array((1.0, 0.82, 0.45), np.float32) * 0.6
        return img


# ----------------------------------------------------------------------------------------- 2D overlays
def text_img(txt, font, fill=WHITE, stroke=0, stroke_fill=BLACK, glow=None, glow_r=14, shadow=True, grad=None):
    bbox = font.getbbox(txt, stroke_width=stroke)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 40
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    org = (pad - bbox[0], pad - bbox[1])
    if shadow:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(s).text((org[0] + 4, org[1] + 6), txt, font=font, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, s.filter(ImageFilter.GaussianBlur(6)))
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text(org, txt, font=font, fill=glow + (200,), stroke_width=stroke + 4)
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(glow_r)))
    t = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(t).text(org, txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if grad:
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).text(org, txt, font=font, fill=255)
        gy = np.linspace(0, 1, im.size[1])[:, None, None]
        c = np.array(grad[0]) * (1 - gy) + np.array(grad[1]) * gy
        gi = Image.fromarray(np.broadcast_to(c, (im.size[1], im.size[0], 3)).astype(np.uint8)).convert("RGBA")
        gi.putalpha(m)
        t = Image.alpha_composite(t, gi)
    return Image.alpha_composite(im, t)


def rounded(w, h, r, fill, border=None, bw=0, shadow=True):
    pad = 30
    im = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if shadow:
        s = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(s).rounded_rectangle((pad + 4, pad + 10, pad + w + 4, pad + h + 10), r, fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, s.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), r, fill=fill, outline=border, width=bw)
    return im


def stack(items, gap=8):
    w = max(i.size[0] for i in items); h = sum(i.size[1] for i in items) + gap * (len(items) - 1)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in items:
        im.alpha_composite(i, ((w - i.size[0]) // 2, y)); y += i.size[1] + gap
    return im


def paste_c(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.size[0] / 2), int(cy - im.size[1] / 2)))
    return base


def photo_card(path, w, h, border=GOLD, r=28, focus=(0.5, 0.5)):
    im = Image.open(path).convert("RGB")
    sc = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * sc + 1), int(im.height * sc + 1)), Image.LANCZOS)
    x0 = int((im.width - w) * focus[0]); y0 = int((im.height - h) * focus[1])
    im = im.crop((x0, y0, x0 + w, y0 + h))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), r, fill=255)
    card = rounded(w + 12, h + 12, r + 6, border)
    ph = Image.new("RGBA", (w, h)); ph.paste(im, (0, 0)); ph.putalpha(m)
    card.alpha_composite(ph, (36, 36))
    return card


class El:
    """Foreground overlay element with entrance/exit animation."""
    def __init__(self, t0, t1, img, cx, cy, anim="pop", dur=0.4, out=0.25, pulse=0.0, drift=0.0, bumps=()):
        self.t0, self.t1, self.cx, self.cy = t0, t1, cx, cy
        self.img = to_np(img) if isinstance(img, Image.Image) else img
        self.anim, self.dur, self.out, self.pulse, self.drift, self.bumps = anim, dur, out, pulse, drift, bumps

    def draw(self, canvas, t):
        if t < self.t0 or t > self.t1:
            return
        p = (t - self.t0) / self.dur
        a = clamp((self.t1 - t) / self.out) if self.out else 1.0
        s, dx, dy = 1.0, 0.0, 0.0
        if self.anim == "pop":
            s = 0.3 + 0.7 * ease_back(p); a *= clamp(p * 3)
        elif self.anim == "stamp":
            s = 1 + 1.4 * (1 - ease_out(p)); a *= clamp(p * 4)
        elif self.anim == "up":
            dy = 80 * (1 - ease_out(p)); a *= clamp(p * 1.5)
        elif self.anim == "left":
            dx = -700 * (1 - ease_out(p)); a *= clamp(p * 2)
        elif self.anim == "right":
            dx = 700 * (1 - ease_out(p)); a *= clamp(p * 2)
        elif self.anim == "fade":
            a *= clamp(p)
        elif self.anim == "zoomin":
            s = 0.85 + 0.15 * ease_out(p); a *= clamp(p)
        if self.pulse and p > 1:
            s *= 1 + self.pulse * (0.5 + 0.5 * math.sin((t - self.t0) * 6.0))
        for b in self.bumps:
            if 0 <= t - b < 0.35:
                s *= 1 + 0.08 * math.sin(math.pi * (t - b) / 0.35)
        s *= 1 + self.drift * (t - self.t0)
        if a <= 0.003:
            return
        blit(canvas, self.img, self.cx + dx, self.cy + dy, s, a)


def blit(canvas, img, cx, cy, s=1.0, a=1.0):
    h, w = img.shape[:2]
    if abs(s - 1) > 1e-3:
        nw, nh = max(1, int(w * s)), max(1, int(h * s))
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        h, w = nh, nw
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    sub = img[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * a
    reg = canvas[Y0:Y1, X0:X1]
    reg *= (1 - sub[..., 3:4])
    reg += sub[..., :3]
