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
