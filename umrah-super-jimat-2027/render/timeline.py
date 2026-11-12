"""Shared edit decision list for the Umrah Super Jimat promo (all times in seconds).

VOICE: (master_in, master_out, timeline_in). Removed from the Master Video:
  0.00-1.85  pre-roll silence
  4.05-9.20  "Sempena promosi ... " (company name unclear in recording -> cut, the promo name is said again at 36.4)
  41.0-41.9  long pause between "Disember" and "2026"
  66.75-end  tail
"""
import os

FPS = 30
W, H = 1080, 1920
SRC = os.environ.get("SRC_DIR", "/home/user/src2")
WORK = os.environ.get("WORK", "/home/user/work")
MASTER = f"{SRC}/master.mov"
BR = f"{WORK}/br"

HOOK = 1.5
VOICE = [(1.85, 4.05, HOOK), (9.20, 41.00, 3.70), (41.90, 66.75, 35.50)]
END0 = 60.35
TOTAL = 65.35


def o(src):
    """master time -> timeline time"""
    for a, b, t0 in VOICE:
        if a - 1e-6 <= src <= b + 1e-6:
            return t0 + src - a
    raise ValueError(src)


def src_at(t):
    """timeline time -> master time (or None)"""
    for a, b, t0 in VOICE:
        if t0 <= t < t0 + (b - a):
            return a + t - t0
    return None


# Subtitle words (master time, text). Corrected by hand from the Whisper large-v3 transcript
# ("tonton" -> "tuan-tuan", "Darul Barat" -> "Darul Mubarak", "perempuan" -> "puan-puan", "Telekong" -> "telekung").
WORDS = [
    (2.00, "Assalamualaikum"), (2.85, "warahmatullahi"), (3.45, "wabarakatuh."),
    (9.30, "Kita"), (9.52, "buka"), (10.00, "peluang"), (10.44, "terbaik"), (10.94, "pada"), (11.16, "mereka"),
    (11.46, "yang"), (11.88, "ingin"), (12.18, "mendaftar"), (12.80, "pakej"), (13.12, "Umrah"), (13.62, "Super"),
    (13.88, "Jimat"), (14.90, "Januari"), (16.02, "2027"), (16.64, "ini."),
    (17.12, "Kita"), (17.80, "bagi"), (18.40, "peluang"), (19.00, "bagi"), (19.34, "mereka"), (19.60, "mendaftar"),
    (20.20, "pakej"), (20.64, "ini,"),
    (20.80, "kita"), (21.24, "akan"), (21.54, "berikan"), (21.96, "backpack"), (22.32, "istimewa."),
    (23.20, "Kita"), (23.76, "akan"), (24.22, "berikan"), (24.74, "kain"), (25.18, "telekung"), (25.78, "atau"),
    (26.06, "ihram."),
    (26.70, "Dan"), (27.24, "juga"), (27.62, "kita"), (28.02, "akan"), (28.40, "berikan"), (28.84, "500ml"),
    (29.90, "air"), (30.38, "Zamzam"), (30.92, "secara"), (31.36, "percuma."),
    (31.82, "Tuan-tuan"), (32.22, "daftar"), (32.76, "sahaja"), (33.02, "kepada"), (33.16, "kami,"),
    (33.50, "tuan-tuan"), (34.10, "akan"), (34.24, "terima"), (34.80, "kesemua"), (35.36, "item-item"),
    (36.20, "ini"), (36.42, "sempena"), (37.38, "promosi"), (38.16, "Year"), (38.48, "End"), (38.70, "Sale"),
    (38.98, "yang"), (39.22, "akan"), (39.46, "berakhir"), (40.06, "pada"), (40.44, "Disember"),
    (42.06, "2026"), (42.82, "ini."),
    (43.24, "Jadi"), (43.96, "rebut"), (44.34, "peluang"), (44.60, "segera"), (45.02, "sementara"), (45.62, "masih"),
    (45.92, "lagi"), (46.26, "ada"), (46.50, "stok,"), (46.82, "sementara"), (47.38, "masih"), (47.66, "lagi"),
    (47.88, "ada"), (48.00, "peluang"), (48.32, "untuk"), (48.82, "tuan-tuan"), (49.20, "merasai"),
    (49.86, "sendiri"), (50.40, "pengalaman"), (51.12, "umrah"), (51.60, "Super"), (51.85, "Jimat"),
    (52.20, "bersama"), (53.10, "dengan"), (53.42, "Darul"), (53.84, "Mubarak"), (54.12, "Travel"), (54.48, "&"),
    (54.78, "Tours."),
    (55.18, "InsyaAllah,"), (55.74, "segala-galanya"), (57.02, "kami"), (57.26, "usahakan"), (57.94, "untuk"),
    (58.58, "merealisasikan"), (59.76, "impian"), (60.28, "tuan-tuan"), (60.64, "dan"), (60.72, "puan-puan"),
    (61.04, "menjadi"), (61.68, "tetamu-tetamu"), (63.12, "Allah"), (63.34, "subhanahu"), (64.52, "wa"),
    (64.66, "ta'ala."), (65.14, "Daftar"), (66.14, "segera!"),
]
KEY = {"UMRAH", "SUPER", "JIMAT", "JANUARI", "2027", "BACKPACK", "ISTIMEWA", "TELEKUNG", "IHRAM", "500ML", "ZAMZAM",
       "PERCUMA", "YEAR", "END", "SALE", "DISEMBER", "2026", "REBUT", "SEGERA", "STOK", "DARUL", "MUBARAK",
       "ALLAH", "DAFTAR", "TERBAIK", "KESEMUA"}


def subtitle_chunks(maxw=3, gap=0.5):
    words = [(o(s), w) for s, w in WORDS]
    chunks, cur = [], []
    for i, (t, w) in enumerate(words):
        if cur and (len(cur) >= maxw or t - cur[-1][0] > 1.0 or cur[-1][1][-1] in ".,!"):
            chunks.append(cur); cur = []
        cur.append((t, w))
    if cur: chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        t0 = c[0][0]
        nxt = chunks[i + 1][0][0] if i + 1 < len(chunks) else c[-1][0] + 1.0
        t1 = min(nxt, c[-1][0] + 1.1)
        out.append((t0, t1, c))
    return out
