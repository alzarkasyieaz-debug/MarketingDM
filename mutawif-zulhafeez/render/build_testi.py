"""Render TESTIMONI JEMAAH – Umrah bersama Mutawif Ustaz Zulhafeez (1080x1920, 30 fps).

Usage:
  SRC_DIR=... OUT_DIR=... python3 build_testi.py audio
  SRC_DIR=... OUT_DIR=... python3 build_testi.py video
  SRC_DIR=... OUT_DIR=... python3 build_testi.py preview 1.0,12.5
  SRC_DIR=... OUT_DIR=... python3 build_testi.py report      # prints output timecodes of pieces & mentions
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as B
from build import (W, H, FPS, SRC, OUT, F, GOLD, GOLD_L, NAVY, PURPLE, WHITE, clamp, ease_out, ease_io, ease_back,
                   set_alpha, scaled, paste_c, text_img, two_tone, stack, rounded_card, ornament, glow_sprite,
                   load_photo, cover, view, blurred_bg, photo_card, light_sweep, rim_light, grade_photo,
                   El, Fx, VideoSeg, KenBurns, Gallery, EndBg, location_pin, Particles, VGRADE)
from edl_testi import PIECES, WORDS, MENTIONS, END_DUR

NAME = "DM_Testimoni_Jemaah_UstazZulhafeez_9x16"
def S(p): return f"{SRC}/{p}"
def ft(n): return f"{SRC}/footage/{n}"
def ph(n): return f"{SRC}/ustaz/{n}"
def ct(n): return f"{SRC}/cut/{n}"

# ================================================================== timeline
T_OF = {}; t = 0.0
for (pid, src, a, b, *_r) in PIECES:
    T_OF[pid] = (t, a, b); t += b - a
T_VOICE_END = t
T_END1 = T_VOICE_END; T_END2 = T_END1 + END_DUR[0]; T_END3 = T_END2 + END_DUR[1]
TOTAL = round(T_END3 + END_DUR[2], 2)

def at(pid, src_t):
    t0, a, _ = T_OF[pid]; return t0 + (src_t - a)

# ================================================================== segments
class SyncSeg(VideoSeg):
    """VideoSeg that stays frame-locked to the timeline even when it is not displayed (cutaways)."""
    def frame(self, t, punch=0.0):
        if self.proc is None: self.open()
        target = int(round((t - self.t0) * FPS)); sz = self.dw * self.dh * 3
        while self.i <= target:
            buf = self.proc.stdout.read(sz)
            if len(buf) == sz: self.last = Image.frombuffer("RGB", (self.dw, self.dh), buf)
            self.i += 1
        p = clamp((t - self.t0) / self.dur)
        return view(self.last, self.z0 + (self.z1 - self.z0) * ease_io(p), self.zmax, self.cx, self.cy, punch)

class SplitLive:
    """Treatment C: speaker (live) on top half, Ustaz photo on bottom half, gold divider."""
    def __init__(self, t0, dur, speaker, photo, pc=(0.5, 0.45)):
        self.t0, self.dur, self.sp = t0, dur, speaker
        self.ph = cover(load_photo(photo), int(W * 1.15), int(H / 2 * 1.15), *pc)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur; e = ease_out(p / 0.25); hh = H // 2
        full = self.sp.frame(t)
        top = full.crop((0, int(H * 0.08), W, int(H * 0.08) + hh))
        c = full.copy()
        k = ease_out(p / 0.2)                             # speaker slides up into the top half
        c.paste(top, (0, int((1 - k) * H * 0.08)))
        ox = int((self.ph.width - W) * (0.25 + 0.5 * p))
        bot = self.ph.crop((ox, 20, ox + W, 20 + hh))
        c.paste(bot, (0, hh + int(hh * (1 - e))))
        d = ImageDraw.Draw(c); lw = int(W * ease_out((p - 0.1) / 0.3))
        if lw > 0: d.rectangle((W / 2 - lw / 2, hh - 4, W / 2 + lw / 2, hh + 4), fill=GOLD)
        return c

class Memory:
    """Treatment D: B-roll of Masjid Quba with Ustaz's photo blended in as a soft memory layer."""
    def __init__(self, t0, dur, video, cut_png, side=0.70):
        self.t0, self.dur, self.v = t0, dur, video
        fg = Image.open(cut_png).convert("RGBA"); fg = fg.crop(fg.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
        rgb = grade_photo(fg.convert("RGB")).convert("RGBA"); rgb.putalpha(fg.getchannel("A"))
        s = 1250 / rgb.height; self.fg = rim_light(rgb.resize((int(rgb.width * s), 1250), Image.LANCZOS), r=26, a=0.7)
        self.side = side; self.halo = glow_sprite(420, GOLD_L, 110)
    def frame(self, t, punch=0.0):
        p = (t - self.t0) / self.dur
        bg = self.v.frame(t, punch)
        a = np.asarray(bg, np.float32) * 0.8
        c = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
        paste_c(c, set_alpha(self.halo, 0.6), W * self.side, 900)
        e = ease_out(p / 0.45)
        paste_c(c, set_alpha(scaled(self.fg, 0.95 + 0.07 * p), 0.82 * e), W * self.side + 40 * (1 - p), H - 625 + 60 * (1 - e))
        return c.convert("RGB")

SPEAKERS = {}
def make_segments():
    segs = []
    for (pid, src, a, b, z0, z1, cx, cy) in PIECES:
        s = SyncSeg(T_OF[pid][0], b - a, S(src), a, 1.0, z0, z1, cx, cy); s.kind = "speaker"; s.pid = pid
        SPEAKERS[pid] = s; segs.append(s)
    cuts = []   # cutaways replace the base layer; speaker audio continues underneath
    def cut(seg, kind="cut"): seg.kind = kind; cuts.append(seg)
    # P2a "peluang kedua untuk ke Tanah Suci" -> Ustaz at Jabal Rahmah (Ken Burns)
    cut(KenBurns(at("P2a", 10.40), 2.0, ph("IMG_9497.jpg"), 1.00, 1.12, 0.45, 0.50))
    # P5a "mutawif ... mutawif pun memang sempoi" -> split screen
    cut(SplitLive(at("P5a", 1.10), 3.1, SPEAKERS["P5a"], ph("IMG_3195.jpg"), (0.30, 0.55)))
    # P5b "belajar daripada mutawif sendiri" -> REAL footage of Ustaz teaching at Masjid Quba
    cut(SyncSeg(at("P5b", 8.95), at("P5b", 10.45) - at("P5b", 8.95), ft("IMG_2048.MOV"), 0.6, 1.0, 1.06, 1.14, 0.57, 0.42))
    # P6a first "mutawif" -> Ustaz with jemaah (vest DM) Ken Burns
    cut(KenBurns(at("P6a", 3.50), 2.2, ph("F0F0E1AF.jpg"), 1.12, 1.00, 0.45, 0.40))
    # P7a "jemaah hilang di Masjid Quba" -> Quba at night, slow-mo
    cut(SyncSeg(at("P7a", 22.80), at("P7a", 25.30) - at("P7a", 22.80), ft("IMG_2048.MOV"), 13.35, 0.5, 1.10, 1.22, 0.55, 0.45))
    # P7b "alhamdulillah mutawif kita boleh cari" -> memory overlay over Quba
    mv = SyncSeg(at("P7b", 33.30), at("P7b", 35.30) - at("P7b", 33.30), ft("IMG_2031.MOV"), 0.0, 0.5, 1.25, 1.12, 0.5, 0.38)
    cut(Memory(mv.t0, mv.dur, mv, ct("IMG_2177.png")))
    # P8b "kat sini berjalan lancar" -> jemaah journey B-roll
    cut(SyncSeg(at("P8b", 44.70), at("P8b", 46.45) - at("P8b", 44.70), ft("89b65111.mp4"), 0.0, 1.0, 1.10, 1.02, 0.45, 0.45))
    # ending
    g = Gallery(T_END1, END_DUR[0], ct("IMG_9620.png"), [ph("IMG_7005.jpg"), ph("IMG_2178.jpg"), ph("AF02554A.jpg"), ph("d2c10b8f.jpg")])
    g.kind = "end"; segs.append(g)
    q = SyncSeg(T_END2, END_DUR[1], ft("IMG_2031.MOV"), 0.0, 0.38, 1.22, 1.00, 0.5, 0.38); q.kind = "end"; segs.append(q)
    e = EndBg(T_END3, END_DUR[2], ph("IMG_2177.jpg")); e.kind = "end"; segs.append(e)
    return segs, cuts

def cut_times(segs, cuts):
    ts = sorted({round(s.t0, 3) for s in segs + cuts} | {round(s.t0 + s.dur, 3) for s in cuts})
    return [x for x in ts if 0.1 < x < TOTAL - 0.1]

# ================================================================== overlays
def header():
    l1 = text_img("TESTIMONI JEMAAH", F("bold", 28), GOLD_L, shadow=False, tracking=5)
    l2 = two_tone([("UMRAH BERSAMA", WHITE), ("MUTAWIF", GOLD)], F("xbold", 42))
    body = stack([l1, l2], 4)
    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 95, 95), fill=(255, 255, 255, 245), outline=GOLD + (255,), width=3)
    badge.alpha_composite(logo.resize((80, 80), Image.LANCZOS), (8, 7))
    w = badge.width + body.width + 76
    card = rounded_card(w, 130, 65, NAVY, 180, border=GOLD, bw=2)
    card.alpha_composite(badge, (34 + 16, 34 + 17)); card.alpha_composite(body, (34 + 16 + badge.width + 26, 34 + (130 - body.height) // 2))
    return card

def kw(parts, size=112, sub=None, maxw=1000):
    big = two_tone(parts, F("black", size), glow=GOLD)
    if big.width > maxw: big = scaled(big, maxw / big.width)
    items = [big] + ([text_img(sub, F("bold", 42), WHITE, tracking=2)] if sub else [])
    return stack(items, 0)

def name_tag(name="USTAZ ZULHAFEEZ", role="Mutawif  |  Darul Mubarak Travel & Tours"):
    nm = text_img(name, F("serif", 68), GOLD_L, glow=GOLD, glow_r=16, tracking=3)
    rl = text_img(role, F("semi", 28), WHITE)
    return stack([nm, ornament(360), rl], 4)

def cutout_reveal(png, x, h=1000, flip=False):
    """Treatment A: cut-out of Ustaz rises beside the speaker with gold rim light + light sweep."""
    fg = Image.open(png).convert("RGBA"); fg = fg.crop(fg.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
    rgb = grade_photo(fg.convert("RGB")).convert("RGBA"); rgb.putalpha(fg.getchannel("A"))
    if flip: rgb = rgb.transpose(Image.FLIP_LEFT_RIGHT)
    s = h / rgb.height; im = rim_light(rgb.resize((int(rgb.width * s), h), Image.LANCZOS), r=20)
    halo = glow_sprite(360, GOLD, 120)
    def fn(c, lt, a):
        e = ease_out(lt / 0.55)
        paste_c(c, set_alpha(halo, a * e * 0.8), x, H - h * 0.62)
        fr = set_alpha(scaled(light_sweep(im, (lt - 0.35) / 0.6, 0.18, 90), 0.9 + 0.1 * e + 0.015 * lt), a * clamp(lt / 0.18))
        paste_c(c, fr, x + 12 * math.sin(lt * 1.1), H - fr.height / 2 + 180 * (1 - e) - 60)
    return fn

def floating_card(photo, x, y, w=400, ang=-6, label=None):
    """Treatment B: framed photo floats in on the keyword, with light sweep."""
    card = photo_card(cover(load_photo(photo, 1600), 600, 760, 0.5, 0.38), w, r=26, border=5)
    lab = text_img(label, F("bold", 34), WHITE, tracking=3) if label else None
    def fn(c, lt, a):
        e = ease_back(lt / 0.5)
        im = light_sweep(card, (lt - 0.4) / 0.6, 0.2, 100)
        im = im.rotate(ang * (1.6 - 0.6 * clamp(e)) + 1.5 * math.sin(lt * 1.4), Image.BILINEAR, expand=True)
        im = set_alpha(scaled(im, 0.55 + 0.45 * clamp(e)), a * clamp(lt / 0.15))
        paste_c(c, im, x, y + 10 * math.sin(lt * 1.2) + 90 * (1 - ease_out(lt / 0.5)))
        if lab and lt > 0.35: paste_c(c, set_alpha(lab, a * clamp((lt - 0.35) / 0.25)), x, y + im.height / 2 - 10)
    return fn

def memory_cards(photos, y=1180):
    """Variation for repeated mention: three small memory cards fan out."""
    cards = [photo_card(cover(load_photo(p, 1400), 500, 640, 0.5, 0.38), 250, r=20, border=4) for p in photos]
    pos = [(250, -10), (540, 8), (830, -6)]
    def fn(c, lt, a):
        for i, (cd, (x, ang)) in enumerate(zip(cards, pos)):
            e = ease_out((lt - i * 0.12) / 0.5)
            if e <= 0: continue
            im = set_alpha(scaled(cd.rotate(ang * e, Image.BILINEAR, expand=True), 0.6 + 0.4 * e), a * e)
            paste_c(c, im, W / 2 + (x - W / 2) * e, y + 12 * math.sin(lt * 1.3 + i) + 120 * (1 - e))
    return fn

def counter(n_to, suffix, y, size=230):
    lab = text_img(suffix, F("black", 120), GOLD, glow=GOLD)
    def fn(c, lt, a):
        k = int(round(clamp(lt / 0.7) ** 0.6 * n_to))
        s = 1.0 + 0.22 * (1 - ease_out((lt - 0.7) / 0.3)) if lt > 0.7 else 1.0
        num = text_img(str(k), F("black", size), WHITE, glow=GOLD, glow_r=26)
        row = Image.new("RGBA", (num.width + lab.width + 10, max(num.height, lab.height)), (0, 0, 0, 0))
        row.alpha_composite(num, (0, 0)); row.alpha_composite(lab, (num.width + 10, row.height - lab.height - 20))
        paste_c(c, set_alpha(scaled(row, s), a * clamp(lt / 0.1)), W / 2, y)
    return fn

# ------------------------------------------------------------------ subtitles
KEY = {"MUTAWIF", "USTAZ", "ZULHAFEEZ", "TERBAIK", "TERBAIK.", "SEMPOI", "SEMPOI,", "PADU,", "BAHANG.", "SAMA.", "PELUANG", "KEDUA",
       "TANAH", "SUCI,", "SUCI", "BELAJAR", "MENGOPI", "KOMITMEN", "STEADY.", "HILANG.", "HILANG", "QUBA.", "CARI.",
       "ALHAMDULILLAH,", "ALHAMDULILLAH.", "BERKAT", "LANCAR.", "100", "PERATUS", "DARUL", "MUBARAK.", "MUBARAK", "MUBARAK,"}
def chunks():
    out = []
    for (pid, *_r) in PIECES:
        ws = WORDS[pid]; _, a, b = T_OF[pid]
        cur = []
        for i, (st, w) in enumerate(ws):
            t0 = at(pid, st); nxt = at(pid, ws[i + 1][0]) if i + 1 < len(ws) else at(pid, b)
            cur.append((t0, min(nxt, t0 + 0.9), w))
            if len(cur) >= 4 or w[-1] in ".,…?" or i + 1 == len(ws) or nxt - t0 > 1.2:
                out.append(cur); cur = []
    return out

_sc = {}
def sub_img(ci, ch, act):
    k = (ci, act)
    if k in _sc: return _sc[k]
    f = F("xbold", 60); sp = f.getlength(" ")
    toks = [w.upper() for (_, _, w) in ch]
    tw = sum(f.getlength(x) for x in toks) + sp * (len(toks) - 1)
    im = Image.new("RGBA", (int(tw) + 80, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 40
    for j, tk in enumerate(toks):
        ww = f.getlength(tk)
        if j == act:
            d.rounded_rectangle((x - 13, 18, x + ww + 13, 102), 16, fill=GOLD + (255,)); d.text((x, 24), tk, font=f, fill=NAVY)
        else:
            col = GOLD_L if tk in KEY or tk.strip(".,…") in KEY else WHITE
            d.text((x, 24), tk, font=f, fill=col + (255,), stroke_width=5, stroke_fill=(0, 0, 0, 255))
        x += ww + sp
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.55)))
    out = Image.alpha_composite(sh, im)
    if out.width > 1020: out = scaled(out, 1020 / out.width)
    _sc[k] = out; return out

class Subs:
    def __init__(self, y=1530):
        self.ch = chunks(); self.y = y
    def draw(self, c, t):
        for ci, ch in enumerate(self.ch):
            t0, t1 = ch[0][0] - 0.05, ch[-1][1] + 0.15
            if ci + 1 < len(self.ch): t1 = min(t1, self.ch[ci + 1][0][0] - 0.03)
            if t0 <= t < t1:
                act = max([j for j, (wt, _, _) in enumerate(ch) if wt <= t] or [0])
                paste_c(c, scaled(sub_img(ci, ch, act), 0.92 + 0.08 * ease_back((t - t0) / 0.18)), W / 2, self.y); return

# ------------------------------------------------------------------ overlay list
def overlays():
    E = []
    def add(*a, **k): E.append(El(*a, **k))
    def fx(*a, **k): E.append(Fx(*a, **k))
    KY = 1250                       # keyword line (below faces, above subtitles)
    K3 = 1350                       # jemaah M3 sits lower in frame: keep text below his chin

    E.append(Particles([(0, at("P2a", 5.7)), (T_END1, TOTAL)], n=30))

    # ---------------- HOOK (P1): "Mutawif Zulhafeez memang A lah terbaik. Sempoi, padu, bahang."
    fx(at("P1", 68.20), at("P1", 72.60), cutout_reveal(ct("IMG_9620.png"), 820, 980), out=0.3)          # A: cut-out on "Zulhafeez"
    add(at("P1", 68.30), at("P1", 69.55), name_tag(), 330, 1340, "left", 0.45, 0.2)
    add(at("P1", 69.60), at("P1", 70.65), kw([("A LAH", GOLD), ("TERBAIK!", WHITE)], 120), W / 2, K3, "crash", 0.3, 0.15)
    for st, wd, x in [(70.70, "SEMPOI.", 200), (71.54, "PADU.", 520), (72.16, "BAHANG!", 835)]:
        add(at("P1", st), at("P1", 72.60), text_img(wd, F("black", 68), GOLD if wd == "PADU." else WHITE, glow=GOLD), x, K3, "pop", 0.25, 0.15)

    add(0.15, T_END1, header(), W / 2, 215, "down", 0.5, 0.3)
    add(at("P2a", 5.9), at("P2a", 9.3), location_pin("JEMAAH UMRAH", "Darul Mubarak Travel & Tours"), 330, 430, "left", 0.5, 0.3)

    # ---------------- P2: peluang kedua ... mutawif yang sama
    add(at("P2a", 9.46), at("P2a", 10.40), kw([("PELUANG", WHITE), ("KEDUA", GOLD)], 116), W / 2, KY, "pop", 0.3, 0.15)
    add(at("P2a", 10.45), at("P2a", 12.30), kw([("KE", WHITE), ("TANAH SUCI", GOLD)], 116), W / 2, KY, "up", 0.35, 0.2)
    fx(at("P2b", 16.70), at("P5a", 0.9), floating_card(ph("IMG_9620.jpg"), 215, 1190, 320, -7, "USTAZ ZULHAFEEZ"), out=0.3)  # B
    add(at("P2b", 16.78), at("P2b", 17.80), kw([("MUTAWIF", GOLD), ("YANG SAMA", WHITE)], 80), 610, 1395, "crash", 0.3, 0.15)

    # ---------------- P5: sempoi, mengopi, belajar  (C split screen is a cutaway at 1.1 s)
    add(at("P5a", 2.70), at("P5a", 3.70), kw([("MUTAWIF", WHITE), ("SEMPOI!", GOLD)], 112), W / 2, 1360, "pop", 0.3, 0.15)
    add(at("P5a", 4.76), at("P5a", 6.05), kw([("BOLEH", WHITE), ("MENGOPI", GOLD)], 112, "SEKALI"), W / 2, KY, "pop", 0.3, 0.15)
    add(at("P5b", 7.90), at("P5b", 8.95), kw([("BANYAK", WHITE), ("BELAJAR", GOLD)], 112), W / 2, KY, "crash", 0.3, 0.15)
    add(at("P5b", 9.00), at("P5b", 10.45), kw([("DARIPADA", WHITE), ("MUTAWIF", GOLD)], 104), W / 2, KY, "up", 0.3, 0.2)
    add(at("P5b", 9.05), at("P5b", 10.45), location_pin("USTAZ ZULHAFEEZ", "Masjid Quba, Madinah"), 360, 430, "left", 0.45, 0.2)

    # ---------------- P6: bersama Ustaz Zulhafeez ... komitmen terbaik, steady
    add(at("P6a", 3.60), at("P6a", 5.65), kw([("MUTAWIF", GOLD)], 120), W / 2, KY, "pop", 0.3, 0.2)
    fx(at("P6a", 8.18), at("P6b", 13.85), cutout_reveal(ct("IMG_2177.png"), 800, 1020), out=0.3)          # A again (different photo)
    add(at("P6a", 8.22), at("P6a", 11.25), name_tag(), 330, 1350, "left", 0.45, 0.25)
    add(at("P6b", 12.34), at("P6b", 13.40), kw([("KOMITMEN", WHITE), ("TERBAIK", GOLD)], 108), W / 2, K3, "crash", 0.3, 0.15)
    add(at("P6b", 13.42), at("P6b", 13.85), kw([("STEADY!", GOLD)], 130), W / 2, K3, "pop", 0.2, 0.1)

    # ---------------- P7: jemaah hilang ... mutawif kita boleh cari
    add(at("P7a", 21.30), at("P7a", 22.80), kw([("JEMAAH", WHITE), ("HILANG!", GOLD)], 120), W / 2, K3, "crash", 0.3, 0.15)
    add(at("P7a", 22.90), at("P7a", 25.30), location_pin("MASJID QUBA", "Madinah"), 300, 430, "left", 0.45, 0.25)
    add(at("P7b", 29.85), at("P7b", 30.55), kw([("TAK MASUK", WHITE), ("AKAL", GOLD)], 116), W / 2, K3, "pop", 0.25, 0.15)
    add(at("P7b", 33.40), at("P7b", 34.20), kw([("ALHAMDULILLAH", GOLD)], 116), W / 2, KY - 80, "pop", 0.3, 0.15)
    add(at("P7b", 34.25), at("P7b", 35.30), kw([("MUTAWIF KITA", WHITE)], 96, None), W / 2, KY - 140, "up", 0.25, 0.15)
    add(at("P7b", 34.70), at("P7b", 35.30), kw([("BOLEH", WHITE), ("CARI!", GOLD)], 116), W / 2, KY - 20, "pop", 0.25, 0.15)

    # ---------------- P8: first time ... paling suci ... berkat mutawif ... berjalan lancar (emotional climax)
    add(at("P8a", 29.30), at("P8a", 31.75), kw([("FIRST TIME", GOLD)], 116), W / 2, KY, "up", 0.4, 0.2)
    add(at("P8b", 33.30), at("P8b", 35.40), kw([("PALING", WHITE), ("SUCI", GOLD)], 120, "DALAM DUNIA"), W / 2, KY, "pop", 0.35, 0.25)
    add(at("P8b", 35.70), at("P8b", 37.60), kw([("TAKUT", GOLD)], 120), W / 2, KY, "up", 0.35, 0.2)
    fx(at("P8b", 40.70), at("P8b", 44.70), memory_cards([ph("IMG_2178.jpg"), ph("IMG_9497.jpg"), ph("IMG_7005.jpg")], 1060), out=0.3)
    add(at("P8b", 39.96), at("P8b", 43.00), kw([("BERKAT", WHITE), ("MUTAWIF", GOLD)], 112), W / 2, 1400, "crash", 0.35, 0.2)
    add(at("P8b", 43.98), at("P8b", 44.70), kw([("ALHAMDULILLAH", GOLD)], 110), W / 2, KY, "pop", 0.25, 0.15)
    add(at("P8b", 45.68), at("P8b", 46.45), kw([("BERJALAN", WHITE), ("LANCAR", GOLD)], 112), W / 2, KY, "pop", 0.25, 0.15)

    # ---------------- P9: 100 peratus ... terbaik ada Darul Mubarak
    fx(at("P9", 63.80), at("P9", 65.40), counter(100, "%", 1180), out=0.2)
    add(at("P9", 65.44), at("P9", 66.75), kw([("TERBAIK", GOLD)], 116, "DARUL MUBARAK"), W / 2, KY, "crash", 0.3, 0.2)

    E.append(Subs(1530))

    # ---------------- ENDING
    rev = stack([text_img("BERSAMA MUTAWIF", F("bold", 50), WHITE, tracking=8),
                 text_img("USTAZ ZULHAFEEZ", F("serif", 104), GOLD_L, glow=GOLD, glow_r=22, tracking=3), ornament(420)], 6)
    add(T_END1 + 0.6, T_END2, rev, W / 2, 1560, "up", 0.6, 0.35)
    add(T_END1 + 1.1, T_END2, text_img("Mutawif  |  Darul Mubarak Travel & Tours", F("semi", 34), WHITE), W / 2, 1720, "fade", 0.5, 0.35)
    add(T_END2 + 0.2, T_END3, text_img("SETIAP PERJALANAN UMRAH", F("serif", 70), WHITE, tracking=3), W / 2, 1160, "up", 0.5, 0.35)
    add(T_END2 + 0.7, T_END3, text_img("MENINGGALKAN", F("serif", 70), WHITE, tracking=3), W / 2, 1260, "up", 0.5, 0.35)
    add(T_END2 + 1.2, T_END3, text_img("SERIBU KENANGAN", F("serif", 100), GOLD_L, glow=GOLD, glow_r=20, tracking=3), W / 2, 1385, "pop", 0.5, 0.35)
    add(T_END2 + 1.7, T_END3, ornament(460), W / 2, 1490, "fade", 0.4, 0.35)

    logo = Image.open(f"{SRC}/logo.png").convert("RGBA")
    badge = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((0, 0, 299, 299), fill=(255, 255, 255, 250), outline=GOLD + (255,), width=6)
    badge.alpha_composite(logo.resize((250, 250), Image.LANCZOS), (25, 22))
    e0 = T_END3
    add(e0 + 0.05, TOTAL, glow_sprite(260, GOLD, 150), W / 2, 470, "fade", 0.7, 0)
    add(e0 + 0.05, TOTAL, badge, W / 2, 470, "pop", 0.5, 0)
    add(e0 + 0.3, TOTAL, text_img("DARUL MUBARAK", F("serif", 92), WHITE, tracking=4), W / 2, 715, "up", 0.45, 0)
    add(e0 + 0.45, TOTAL, text_img("TRAVEL & TOURS", F("bold", 44), GOLD_L, tracking=12), W / 2, 800, "up", 0.45, 0)
    add(e0 + 0.6, TOTAL, text_img("Untuk Perkhidmatan Yang Lebih Meyakinkan", F("med", 32), (230, 225, 240)), W / 2, 865, "fade", 0.45, 0)
    add(e0 + 1.0, TOTAL, stack([text_img("NAK RASAI PENGALAMAN", F("black", 66), WHITE),
                                 text_img("UMRAH SEPERTI INI?", F("black", 76), GOLD, glow=GOLD)], 0), W / 2, 1080, "pop", 0.45, 0)
    bt = text_img("HUBUNGI KAMI", F("black", 56), NAVY, shadow=False, tracking=2)
    btn = rounded_card(bt.width + 120, bt.height + 50, 48, GOLD, 255); btn.alpha_composite(bt, (34 + 60, 34 + 25))
    def btn_fx(c, lt, a):
        paste_c(c, set_alpha(scaled(btn, (0.6 + 0.4 * ease_back(lt / 0.45)) * (1 + 0.035 * math.sin(lt * 5.6))), clamp(lt / 0.2)), W / 2, 1290)
    fx(e0 + 1.4, TOTAL, btn_fx, out=0)
    add(e0 + 1.7, TOTAL, text_img("untuk maklumat pakej umrah", F("semi", 40), WHITE), W / 2, 1405, "fade", 0.45, 0)
    return E

# ================================================================== render
def render(times=None):
    segs, cuts = make_segments(); ovl = overlays(); vig = B.vignette()
    CUTS = cut_times(segs, cuts)
    def flash(t):
        for c in CUTS:
            if 0 <= t - c < 0.18: return (1 - (t - c) / 0.18) ** 2
        return 0.0
    n = int(round(TOTAL * FPS)); frames = range(n) if times is None else [int(round(x * FPS)) for x in times]
    enc = None
    if times is None:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                "-i", "-", "-i", f"{OUT}/mix_testi.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "256k", "-shortest",
                                "-movflags", "+faststart", f"{OUT}/{NAME}.mp4"], stdin=subprocess.PIPE)
    for fi in frames:
        t = fi / FPS
        base_seg = [s for s in segs if s.t0 <= t + 1e-6][-1]
        cut_seg = next((c for c in cuts if c.t0 <= t < c.t0 + c.dur), None)
        # keep speaker readers advancing so they stay in sync under cutaways
        if getattr(base_seg, "kind", "") == "speaker" and cut_seg is not None and not isinstance(cut_seg, SplitLive):
            base_seg.frame(t)
        seg = cut_seg or base_seg
        for s in segs + cuts:                      # close finished readers
            if isinstance(s, VideoSeg) and s.proc and t > s.t0 + s.dur + 0.1: s.close()
        fl = flash(t)
        base = seg.frame(t, punch=0.04 * fl) if not isinstance(seg, SplitLive) else seg.frame(t)
        a = np.asarray(base, np.float32) * vig
        if fl > 0: a = a + (np.array(GOLD_L, np.float32) - a) * (0.35 * fl)
        if t > TOTAL - 0.8: a *= clamp((TOTAL - t) / 0.8)
        if t < 0.2: a *= t / 0.2
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
        for e in ovl: e.draw(c, t)
        rgb = c.convert("RGB")
        if enc: enc.stdin.write(rgb.tobytes())
        else: rgb.save(f"{OUT}/tprev_{t:06.2f}.png"); print("preview", round(t, 2), flush=True)
        if enc and fi % 300 == 0: print(f"frame {fi}/{n}", flush=True)
    if enc: enc.stdin.close(); enc.wait(); print("video ok", f"{OUT}/{NAME}.mp4")

# ================================================================== audio
SR = 48000
def audio():
    from islamic_music import compose
    rng = np.random.default_rng(5); N = int(TOTAL * SR)
    def place(buf, clip, t, g):
        s = int(t * SR)
        if 0 <= s < N: c = clip[:N - s]; buf[s:s + len(c)] += c * g
    voice = np.zeros(N)
    gains = {}
    for src in {p[1] for p in PIECES}:            # per-speaker loudness match on the whole clip
        v = B.read_audio(S(src), 0, 999, B.VOICE_AF); gains[src] = 0.15 / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9)
    for (pid, src, a, b, *_r) in PIECES:
        v = B.read_audio(S(src), a, b - a, B.VOICE_AF) * gains[src]
        f = int(0.03 * SR); v[:f] *= np.linspace(0, 1, f); v[-f:] *= np.linspace(1, 0, f)
        place(voice, v, T_OF[pid][0], 1.0)
    music = compose(TOTAL, [(0.0, at("P5a", 0), "sparse"), (at("P5a", 0), at("P8a", 28.65), "full"),
                            (at("P8a", 28.65), at("P9", 60.05), "calm"), (at("P9", 60.05), T_END3, "full"), (T_END3, TOTAL, "end")])
    t = np.arange(N) / SR
    lvl = np.full(N, -13.0); lvl[t >= T_END1] = -5.5
    win = int(0.05 * SR); ve = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
    act = np.convolve((ve > 0.015).astype(float), np.ones(int(0.35 * SR)) / int(0.35 * SR), "same")
    gain = 10 ** ((lvl - 9.0 * np.clip(act * 1.6, 0, 1)) / 20)
    gain = np.convolve(gain, np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    tail = t > TOTAL - 1.8; gain[tail] *= np.linspace(1, 0, tail.sum()) ** 2
    music = music * gain[:, None]

    def whoosh(d=0.6):
        n = int(d * SR); x = rng.standard_normal(n); b_ = np.fft.rfft(x); b_ *= np.exp(-np.fft.rfftfreq(n, 1 / SR) / 2500)
        y = np.fft.irfft(b_, n); return y / np.abs(y).max() * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    def impact():
        n = int(1.8 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * (40 + 80 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.6)
    def shimmer():
        n = int(1.4 * SR); tt = np.arange(n) / SR; o = np.zeros(n)
        for k, fq in enumerate([1568, 2093, 2637, 3136, 4186]):
            s = int(k * 0.07 * SR); o[s:] += np.sin(2 * np.pi * fq * tt[:n - s]) * np.exp(-tt[:n - s] * 4) * 0.2
        return o
    def tick():
        n = int(0.05 * SR); tt = np.arange(n) / SR; return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 120)
    def riser(d=1.6):
        n = int(d * SR); tt = np.arange(n) / SR
        return (np.sin(2 * np.pi * np.cumsum(220 * 6 ** (tt / d)) / SR) * 0.2 + whoosh(d) * 0.8) * (tt / d) ** 2
    sfx = np.zeros(N)
    segs, cuts = make_segments()
    for c in cut_times(segs, cuts): place(sfx, whoosh(), c - 0.3, 0.05)
    for (pid, st, _) in MENTIONS: place(sfx, shimmer(), at(pid, st) - 0.05, 0.08)       # photo-reveal sound on every mention
    for x in (at("P1", 68.20), at("P6a", 8.18), T_END1, T_END3): place(sfx, impact(), x, 0.18)
    for k in range(25): place(sfx, tick(), at("P9", 63.80) + k * 0.7 / 24, 0.04)
    place(sfx, impact(), at("P9", 64.50), 0.15)
    place(sfx, riser(), T_END1 - 1.6, 0.07)
    st = music * 0.55 + (voice + sfx)[:, None]
    st /= max(1.0, np.abs(st).max() / 0.95)
    raw = f"{OUT}/mix_testi_raw.wav"
    with wave.open(raw, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR),
                    f"{OUT}/mix_testi.wav"], check=True)
    print("audio ok")

def report():
    def tc(x): return f"{int(x // 60)}:{x % 60:05.2f}"
    print("TOTAL", TOTAL)
    for (pid, src, a, b, *_r) in PIECES: print(f"{pid:4s} {tc(T_OF[pid][0])}-{tc(T_OF[pid][0] + b - a)}  {src} {a:.2f}-{b:.2f}")
    for (pid, st, w) in MENTIONS: print("mention", tc(at(pid, st)), w)
    print("end", tc(T_END1), tc(T_END2), tc(T_END3))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    {"audio": audio, "video": render, "report": report}.get(cmd, lambda: render([float(x) for x in sys.argv[2].split(",")]))()
