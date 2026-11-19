"""Edit decision list: TESTIMONI JEMAAH – Umrah bersama Mutawif Ustaz Zulhafeez (9:16, 1080x1920, 30 fps).

Sources ($SRC_DIR):
  testi/M1.MOV  Jemaah 1 (white serban, airport lounge)        37.4 s
  testi/M2.MOV  Jemaah 2 (kopiah, DM lanyard, seated)          67.9 s
  testi/M3.mov  Jemaah 3 (white jubah, purple DM sash)         73.0 s
  footage/*     Ustaz Zulhafeez at Masjid Quba + airport B-roll
  ustaz/*.jpg, cut/*.png, logo.png

Every spoken word below is the jemaah's own (Whisper large-v3, transcribed twice, ms + id models).
Only pauses/hesitations are removed between pieces; no sentence is re-ordered inside a piece.
"""
M1, M2, M3 = "testi/M1.MOV", "testi/M2.MOV", "testi/M3.mov"

# (id, source, src_in, src_out, zoom_from, zoom_to, cx, cy)
PIECES = [
    ("P1",  M3, 67.05, 72.60, 1.00, 1.08, 0.50, 0.30),   # HOOK: mutawif Zulhafeez memang A lah terbaik
    ("P2a", M1, 5.70, 13.60, 1.00, 1.07, 0.50, 0.30),    # peluang kedua ... saya akan minta
    ("P2b", M1, 14.95, 17.80, 1.18, 1.23, 0.50, 0.28),   # dari Darul Mubarak mutawif yang sama
    ("P5a", M2, 0.00, 6.05, 1.00, 1.06, 0.50, 0.28),     # mutawif sempoi, boleh mengopi sekali
    ("P5b", M2, 6.70, 10.45, 1.16, 1.20, 0.50, 0.26),    # banyak belajar daripada mutawif
    ("P6a", M3, 2.55, 11.25, 1.00, 1.08, 0.50, 0.30),    # bersama Ustaz Zulhafeez
    ("P6b", M3, 11.80, 13.85, 1.18, 1.22, 0.50, 0.28),   # komitmen yang terbaik, steady
    ("P7a", M3, 19.90, 25.30, 1.04, 1.10, 0.50, 0.30),   # jemaah hilang di Masjid Quba
    ("P7b", M3, 26.75, 35.30, 1.00, 1.08, 0.50, 0.30),   # ... alhamdulillah mutawif kita boleh cari
    ("P8a", M2, 28.65, 31.75, 1.00, 1.05, 0.50, 0.28),   # first time nak datang tempat yang Allah...
    ("P8b", M2, 32.75, 46.45, 1.05, 1.16, 0.50, 0.27),   # paling suci ... berkat mutawif ... berjalan lancar
    ("P9",  M2, 60.05, 66.75, 1.12, 1.22, 0.50, 0.27),   # 100 peratus, terbaik ada Darul Mubarak
]

# Words per piece: (src_time, text). Spelling normalised (Mutawih->mutawif, Kuba->Quba, Zul Hafiz->Zulhafeez).
WORDS = {
    "P1": [(67.14, "Mutawif"), (68.24, "Zulhafeez"), (68.88, "memang"), (69.62, "A"), (69.92, "lah"), (70.14, "terbaik."),
           (70.70, "Sempoi,"), (71.54, "padu,"), (72.16, "bahang.")],
    "P2a": [(5.84, "Kalau"), (6.56, "saya"), (7.22, "insyaAllah"), (8.42, "diberi"), (9.46, "peluang"), (9.80, "kedua"),
            (10.16, "untuk"), (10.46, "ke"), (10.96, "Tanah"), (11.44, "Suci,"), (11.96, "saya"), (12.54, "akan"), (13.18, "minta")],
    "P2b": [(15.04, "dari"), (15.90, "Darul"), (16.44, "Mubarak"), (16.78, "mutawif"), (17.28, "yang"), (17.42, "sama.")],
    "P5a": [(0.00, "Darul"), (0.30, "Mubarak,"), (0.66, "dari"), (0.76, "segi"), (1.18, "mutawif"), (1.48, "sendiri,"),
            (1.84, "mutawif"), (2.56, "pun"), (2.70, "memang"), (2.90, "sempoi"), (3.46, "lah."), (3.76, "Boleh"), (4.32, "buat"),
            (4.42, "bincang,"), (4.76, "boleh"), (4.88, "mengopi"), (5.30, "sekali,"), (5.60, "alhamdulillah.")],
    "P5b": [(6.78, "Kita"), (7.34, "boleh"), (7.90, "banyak"), (8.24, "belajar"), (8.56, "daripada"), (9.00, "mutawif"), (9.98, "sendiri.")],
    "P6a": [(2.64, "Daripada"), (3.24, "segi"), (3.54, "mutawif,"), (4.12, "mutawif"), (4.70, "yang"), (5.20, "kali"), (5.76, "ini"),
            (6.02, "yang"), (6.22, "saya"), (6.40, "pergi"), (6.70, "ni"), (6.94, "bersama"), (8.22, "Ustaz"), (9.42, "Zulhafeez,"),
            (9.94, "kita"), (10.20, "memang"), (10.92, "dia")],
    "P6b": [(11.84, "membagi"), (12.34, "komitmen"), (12.74, "yang"), (12.92, "terbaik"), (13.24, "lah,"), (13.42, "steady.")],
    "P7a": [(19.94, "Satu"), (20.14, "benda"), (20.42, "tu"), (20.58, "yang"), (20.70, "saya"), (20.84, "tengok"), (21.16, "tu,"),
            (21.34, "jemaah"), (22.40, "hilang."), (22.86, "Jemaah"), (23.58, "hilang"), (23.98, "di"), (24.10, "Masjid"), (24.78, "Quba.")],
    "P7b": [(26.88, "Tapi"), (27.40, "jemaah"), (27.92, "itu"), (28.00, "membagikan…"), (28.58, "satu"), (29.46, "benda"), (29.72, "yang"),
            (29.88, "tak"), (30.10, "masuk"), (30.28, "akal."), (30.54, "Macam"), (31.40, "nak"), (31.66, "cari"), (32.08, "dia,"),
            (32.18, "dia"), (32.34, "ada"), (32.68, "kat"), (32.82, "mana"), (32.98, "ni."), (33.16, "Tapi"), (33.48, "alhamdulillah,"),
            (34.26, "mutawif"), (34.56, "kita"), (34.70, "boleh"), (34.88, "cari.")],
    "P8a": [(28.70, "Kita"), (29.30, "first"), (29.78, "time"), (30.04, "ni"), (30.22, "nak"), (30.40, "datang"), (30.76, "tempat"),
            (31.10, "yang"), (31.32, "Allah…")],
    "P8b": [(32.84, "memang"), (33.36, "paling"), (33.54, "suci"), (33.98, "dalam"), (34.14, "dunia"), (34.56, "ni"), (34.68, "kan."),
            (35.42, "Kita"), (35.72, "takut,"), (36.28, "kita"), (36.56, "tahu"), (36.90, "diri"), (37.10, "kita"), (37.24, "macam"),
            (37.48, "mana,"), (37.70, "tapi"), (38.00, "dengan"), (38.58, "apa,"), (39.96, "berkat"), (40.78, "mutawif"),
            (41.50, "sendiri,"), (41.80, "menunjuk"), (43.12, "ajar,"), (43.46, "memang"), (43.98, "alhamdulillah,"), (44.88, "kat"),
            (45.46, "sini"), (45.68, "berjalan"), (46.04, "lancar.")],
    "P9": [(60.18, "Rate"), (60.80, "bagi"), (61.22, "itu"), (61.28, "memang,"), (61.98, "kalau"), (62.44, "100"), (63.34, "itu"),
           (63.62, "memang"), (63.86, "100"), (64.32, "peratus"), (64.70, "lah,"), (64.86, "sebab"), (65.44, "terbaik"),
           (65.70, "ada"), (65.84, "Darul"), (66.02, "Mubarak.")],
}

# Mentions of the mutawif in the kept audio (piece, src_time, word) -> each one drives a photo treatment
MENTIONS = [("P1", 67.14, "Mutawif"), ("P1", 68.24, "Zulhafeez"), ("P2b", 16.78, "mutawif"),
            ("P5a", 1.18, "mutawif"), ("P5a", 1.84, "mutawif"), ("P5b", 9.00, "mutawif"),
            ("P6a", 3.54, "mutawif"), ("P6a", 4.12, "mutawif"), ("P6a", 8.22, "Ustaz Zulhafeez"),
            ("P7b", 34.26, "mutawif"), ("P8b", 40.78, "mutawif")]

END_DUR = (4.0, 4.0, 5.0)   # gallery reveal, closing line over Masjid Quba, brand + CTA
