"""Shared edit decision list for the Umrah Ramadan 2027 promo (9:16, 30 fps).

All times in seconds. T = output timeline time, m = Master Video time.
Section A: T = m - 1.9   (master 1.9 -> 32.2)
Interlude: T 30.3 -> 48.3 (package info, no voice)
Section B: T = m + 11.0  (master 37.3 -> 93.6)
End card : T 104.6 -> 109.6
"""
import os

W, H, FPS = 1080, 1920, 30
SRC = os.environ.get("SRC_DIR", "./src")          # holds master.mov, p1.jpg, p2.jpg, logo.png, broll/
OUT = os.environ.get("OUT_DIR", "./out")
MASTER = f"{SRC}/master.mov"

def br(name):
    return f"{SRC}/broll/{name}"

A_OFF = -1.9
B_OFF = 11.0
INTER = (30.3, 48.3)
END = (104.6, 109.6)
TOTAL = 109.6

# Voice pieces: (master_start, master_end, T_start)
VOICE = [(1.9, 32.2, 0.0), (37.3, 93.8, 48.3)]

# Base video segments: (source, src_start, duration, zoom_from, zoom_to, style)
# style: "master" | "broll" | "bg" (blurred + darkened background for cards)
SEGMENTS = [
    # --- Section A: hook + emotional build-up ---
    (br("IMG_7400.MOV"), 0.0, 3.0, 1.40, 1.06, "hook"),     # T0.0  Kaabah malam (hook)
    (MASTER,             4.9, 4.0, 1.00, 1.05, "master"),   # T3.0
    (br("IMG_6432.MOV"), 0.5, 4.4, 1.00, 1.12, "broll"),    # T7.0  Kaabah + menara jam
    (MASTER,            13.3, 2.8, 1.10, 1.14, "master"),   # T11.4 punch-in
    (br("IMG_6415.MOV"), 4.0, 5.9, 1.00, 1.10, "broll"),    # T14.2 tawaf siang (dolly-in)
    (MASTER,            22.0, 5.8, 1.00, 1.05, "master"),   # T20.1
    (br("IMG_7399.mov"), 5.0, 4.4, 1.12, 1.00, "broll"),    # T25.9 Kaabah malam
    # --- Interlude: package ---
    (br("IMG_6437.MOV"), 10.0, 3.0, 1.00, 1.08, "dim"),     # T30.3 title + poster
    (br("IMG_7400.MOV"), 15.0, 3.5, 1.25, 1.05, "bg"),      # T33.3 price crash zoom
    (br("IMG_6432.MOV"), 1.0, 6.5, 1.00, 1.06, "bg"),       # T36.8 price table
    (br("33ee.MP4"),     2.0, 5.0, 1.00, 1.06, "bg"),       # T43.3 hotel + flight
    # --- Section B: promo + closing + CTA ---
    (MASTER,            37.3, 3.9, 1.00, 1.05, "master"),   # T48.3
    (br("IMG_5503.MOV"), 0.0, 5.7, 1.00, 1.10, "broll"),    # T52.2 jemaah DM
    (MASTER,            46.9, 7.5, 1.10, 1.14, "master"),   # T57.9 gifts
    (br("IMG_6637.MOV"), 0.0, 9.6, 1.00, 1.08, "broll"),    # T65.4 jemaah DM dalam masjid
    (MASTER,            64.0, 5.7, 1.00, 1.05, "master"),   # T75.0
    (br("IMG_7516.MOV"), 0.0, 8.1, 1.00, 1.10, "broll"),    # T80.7 jemaah solat
    (br("IMG_7400.MOV"), 8.0, 10.0, 1.20, 1.00, "broll"),   # T88.8 closing slow zoom-out
    (MASTER,            87.8, 5.8, 1.05, 1.12, "master"),   # T98.8 CTA
    (br("IMG_7400.MOV"), 18.0, 5.0, 1.00, 1.08, "bg"),      # T104.6 end card
]

def seg_starts():
    t, out = 0.0, []
    for s in SEGMENTS:
        out.append(round(t, 3))
        t += s[2]
    return out

SPARKLES = [59.4, 62.5, 63.8, 68.8]
HOOK = ("RAMADAN KALI INI…", "DI TANAH SUCI?")

# ---------------------------------------------------------------- Variant v2 (same style, gift-focused)
VARIANT = os.environ.get("VARIANT", "v1")
if VARIANT == "v2":
    def gift(n):
        return f"{SRC}/gifts/{n}.jpg"
    HOOK = ("BAYANGKAN…", "RAMADAN DI TANAH SUCI!")
    SPARKLES = [59.4, 62.5, 64.0, 68.8]
    SEGMENTS = [
        (br("IMG_7399.mov"), 0.0, 3.0, 1.40, 1.06, "hook"),     # T0.0  Kaabah malam
        (MASTER,             4.9, 4.0, 1.00, 1.05, "master"),   # T3.0
        (br("IMG_6437.MOV"), 0.0, 4.4, 1.00, 1.10, "broll"),    # T7.0  halaman Masjidil Haram
        (MASTER,            13.3, 2.8, 1.10, 1.14, "master"),   # T11.4
        (br("IMG_6415.MOV"), 12.0, 5.9, 1.00, 1.10, "broll"),   # T14.2 tawaf
        (MASTER,            22.0, 5.8, 1.00, 1.05, "master"),   # T20.1
        (br("IMG_7400.MOV"), 0.0, 4.4, 1.12, 1.00, "broll"),    # T25.9 Kaabah malam 4K
        (br("IMG_6432.MOV"), 3.0, 3.0, 1.00, 1.08, "dim"),      # T30.3 title + posters
        (br("IMG_7399.mov"), 3.0, 3.5, 1.25, 1.05, "bg"),       # T33.3 price
        (br("IMG_6437.MOV"), 20.0, 6.5, 1.00, 1.06, "bg"),      # T36.8 table
        (br("IMG_5542.MOV"), 30.0, 5.0, 1.00, 1.06, "bg"),      # T43.3 hotel + flight
        (MASTER,            37.3, 3.9, 1.00, 1.05, "master"),   # T48.3
        (br("IMG_5542.MOV"), 10.0, 5.7, 1.00, 1.10, "broll"),   # T52.2 jemaah DM (ziarah)
        (MASTER,            46.9, 4.6, 1.10, 1.14, "master"),   # T57.9 beg
        (gift("ihram"),      0.0, 1.5, 1.00, 1.05, "bg"),       # T62.5 kain ihram
        (gift("telekung"),   0.0, 2.0, 1.00, 1.05, "bg"),       # T64.0 mini telekung
        (br("IMG_6636.MOV"), 0.0, 2.8, 1.00, 1.08, "broll"),    # T66.0 jemaah DM dalam masjid
        (gift("zamzam"),     0.0, 6.2, 1.00, 1.06, "bg"),       # T68.8 air Zamzam
        (MASTER,            64.0, 5.7, 1.00, 1.05, "master"),   # T75.0
        (br("IMG_7522.MOV"), 0.0, 8.1, 1.00, 1.10, "broll"),    # T80.7 jemaah
        (br("IMG_7400.MOV"), 8.0, 10.0, 1.20, 1.00, "broll"),   # T88.8 closing
        (MASTER,            87.8, 5.8, 1.05, 1.12, "master"),   # T98.8 CTA
        (br("IMG_7400.MOV"), 18.0, 5.0, 1.00, 1.08, "bg"),      # T104.6 end card
    ]
