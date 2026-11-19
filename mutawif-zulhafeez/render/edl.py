"""Edit decision list for "Bersama Mutawif Ustaz Zulhafeez" (9:16, 1080x1920, 30 fps).

All times are output-timeline seconds unless noted. Source files live in $SRC_DIR:
  footage/IMG_2031.MOV  Ustaz at Masjid Quba (night), says the salam      (3.0 s)
  footage/IMG_2032.MOV  Ustaz at Masjid Quba (night), close              (0.6 s)
  footage/IMG_2048.MOV  Ustaz explains Masjid Quba to camera             (14.6 s)
  footage/991cf9ec.mp4, 89b65111.mp4, e6576e55.mp4, 8d2a9015.mp4, f48bade2.mp4
                        jemaah + petugas at a Malaysian airport (no usable speech)
  ustaz/*.jpg           12 real photos of Ustaz Zulhafeez (Drive "Gambar Mutawif")
  cut/*.png             MODNet cut-outs of some of those photos (make_cutouts.py)
  logo.png              Darul Mubarak logo (Drive)
"""
import os

W, H, FPS = 1080, 1920, 30
SRC = os.environ.get("SRC_DIR", "./src")
OUT = os.environ.get("OUT_DIR", "./out")

def ft(name): return f"{SRC}/footage/{name}"
def ph(name): return f"{SRC}/ustaz/{name}"
def cut(name): return f"{SRC}/cut/{name}"

# ------------------------------------------------------------------ real speech (verified by Whisper large-v3)
# IMG_2031: salam.   IMG_2048: Masjid Quba explanation.  Times are SOURCE-clip seconds.
SALAM = [(0.00, "Assalamualaikum"), (0.86, "warahmatullahi"), (1.52, "wabarakatuh")]
SALAM_END = 1.78
QUBA_WORDS = [
    (0.00, "Masjid"), (0.50, "Quba"), (0.78, "merupakan"), (1.16, "masjid"), (1.50, "pertama"), (1.82, "yang"),
    (2.54, "melaksanakan"), (3.84, "solat"), (4.38, "secara"), (4.64, "berjemaah."),
    (5.14, "Yang"), (5.66, "kedua,"), (5.98, "Masjid"), (6.16, "Quba"), (6.46, "mempunyai"), (7.08, "19"), (7.30, "pintu."),
    (7.96, "Dua"), (8.56, "pintu"), (8.94, "besar"), (9.10, "untuk"), (9.34, "jemaah"), (9.68, "lelaki"),
    (9.94, "dan"), (10.04, "satu"), (10.26, "pintu"), (10.70, "besar"), (10.90, "untuk"), (11.14, "muslimat"), (12.88, "pula."),
]
QUBA_END = 13.35
# sentence ends (source s) used to close subtitle chunks
QUBA_SENT_END = {"berjemaah.": 5.04, "pintu.": 7.92, "pula.": 13.30}

# ------------------------------------------------------------------ scene boundaries (output s)
T_HOOK = 0.0          # salam
T_TITLE = 2.1         # title / lower-third reveal
T_JOURNEY = 4.9       # airport: perjalanan bermula
T_PHOTOS = 14.3       # photo montage
T_QUBA = 23.9         # tazkirah at Masjid Quba
T_REVEAL = 37.4       # signature mutawif reveal
T_GALLERY = 39.8
T_CLOSE = 45.8        # "setiap perjalanan umrah..."
T_END = 50.6          # brand end card
TOTAL = 56.0

# video segments: (t_out, dur_out, src, src_start, speed, z0, z1, cx, cy)
VIDEO = [
    (0.0, 2.1, ft("IMG_2031.MOV"), 0.00, 1.0, 1.55, 1.38, 0.50, 0.40),     # salam (hook)
    (2.1, 2.8, ft("IMG_2032.MOV"), 0.00, 0.2, 1.00, 1.14, 0.62, 0.46),     # slow-mo close, name reveal
    (4.9, 2.9, ft("991cf9ec.mp4"), 0.30, 1.0, 1.05, 1.16, 0.50, 0.42),
    (7.8, 2.2, ft("89b65111.mp4"), 0.00, 1.0, 1.14, 1.02, 0.45, 0.45),
    (10.0, 2.4, ft("e6576e55.mp4"), 0.00, 1.0, 1.00, 1.10, 0.50, 0.55),
    (12.4, 1.9, ft("8d2a9015.mp4"), 0.20, 1.0, 1.10, 1.20, 0.42, 0.40),
    # 14.3 - 23.9 photo segments (see PHOTOS)
    (23.9, 5.2, ft("IMG_2048.MOV"), 0.00, 1.0, 1.05, 1.12, 0.57, 0.42),   # Quba part 1
    (29.1, 2.8, ft("IMG_2048.MOV"), 5.20, 1.0, 1.28, 1.34, 0.57, 0.40),   # punch-in: "yang kedua ... 19 pintu"
    (31.9, 5.5, ft("IMG_2048.MOV"), 8.00, 1.0, 1.08, 1.14, 0.57, 0.42),   # "dua pintu besar ..."
    (37.4, 2.4, ft("IMG_2048.MOV"), 13.35, 0.52, 1.10, 1.22, 0.55, 0.45), # walks away, slow-mo
    # 39.8 - 45.8 gallery (photo)
    (45.8, 4.8, ft("IMG_2031.MOV"), 0.00, 0.33, 1.22, 1.00, 0.50, 0.38),  # Quba wide, slow zoom-out
    # 50.6 - 56.0 end card (photo-based bg)
]

# photo segments: (t_out, dur_out, kind, args)
PHOTOS = [
    (14.3, 2.4, "kenburns", dict(img=ph("IMG_9497.jpg"), z0=1.00, z1=1.14, cx=0.45, cy=0.55)),
    (16.7, 2.4, "frame", dict(img=ph("IMG_9407.jpg"))),
    (19.1, 2.4, "cutout", dict(bg=ph("IMG_2177.jpg"), fg=cut("IMG_2177.png"))),
    (21.5, 2.4, "split", dict(top=ph("F0F0E1AF.jpg"), bottom=ph("IMG_3195.jpg"), top_c=(0.45, 0.42), bot_c=(0.30, 0.55))),
    (39.8, 6.0, "gallery", dict(hero=cut("IMG_9620.png"),
                                cards=[ph("IMG_7005.jpg"), ph("IMG_2178.jpg"), ph("AF02554A.jpg"), ph("d2c10b8f.jpg")])),
    (50.6, 5.4, "endbg", dict(img=ph("IMG_2177.jpg"))),
]

# hard cuts that get a light flash + zoom punch + whoosh
CUTS = [2.1, 4.9, 7.8, 10.0, 12.4, 14.3, 16.7, 19.1, 21.5, 23.9, 29.1, 31.9, 37.4, 39.8, 45.8, 50.6]

# airport ambience under music (output t, dur, src, src_start)
AMBIENCE = [(4.9, 2.9, ft("991cf9ec.mp4"), 0.30), (7.8, 2.2, ft("89b65111.mp4"), 0.0),
            (10.0, 2.4, ft("e6576e55.mp4"), 0.0), (12.4, 1.9, ft("8d2a9015.mp4"), 0.20)]
