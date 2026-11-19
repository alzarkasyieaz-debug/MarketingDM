# Bersama Mutawif Ustaz Zulhafeez – Pelan Suntingan & Hasil Render

**Fail video:** `output/DM_Mutawif_UstazZulhafeez_9x16.mp4`
**Spesifikasi:** 1080×1920 (9:16) • 30 fps • H.264 + AAC 256k • 56.0 saat • kenyaringan -14 LUFS (TikTok/Reels/FB Reels)

---

## 1. Analisis bahan sumber (Google Drive)

| Folder | Fail | Kandungan sebenar |
|---|---|---|
| Footage Mutawif | `IMG_2048.MOV` (14.6 s, 4K) | **Ustaz Zulhafeez bercakap ke kamera di Masjid Quba (malam)** – satu-satunya ucapan panjang |
| | `IMG_2031.MOV` (3.0 s) | Ustaz di Masjid Quba, memberi salam |
| | `IMG_2032.MOV` (0.6 s) | Ustaz, syot dekat, Masjid Quba |
| | `991cf9ec`, `89b65111`, `e6576e55`, `8d2a9015`, `f48bade2` (.mp4, 2–4 s) | Petugas berbaju merah & jemaah di lapangan terbang Malaysia (papan tanda "KELUAR/EXIT"). Audio hanya bunyi latar – **tiada ucapan** |
| Gambar Mutawif | 12 gambar | Gambar sebenar Ustaz Zulhafeez (Jabal Rahmah, Madinah, Makkah, hotel, kereta api, vest DM "USTAZ HAFEEZ") |
| Refrence Video | `Refrence 1.mp4` (46 s) | Gaya: pil tajuk berkaca di atas, kapsyen dua warna, kad terapung, CTA berlatar kabur. Muzik **tidak** digunakan |
| (lain) | Logo DM, "Footer DM.png" | Logo & tagline "Untuk Perkhidmatan Yang Lebih Meyakinkan" |

> **PENTING:** Tiada video testimoni jemaah dalam folder ini. Semua footage ialah rakaman **mutawif sendiri**.
> Oleh itu video ini dibina sebagai *"Bersama Mutawif Ustaz Zulhafeez"* menggunakan suara sebenar Ustaz.
> **Tiada kata-kata jemaah direka.** Frasa contoh dalam brief (cth. "TERIMA KASIH USTAZ!", "LAYANAN SANGAT BAIK!") **tidak digunakan** kerana tiada sesiapa menyebutnya.
> Peraturan "gambar Ustaz muncul apabila jemaah sebut 'Ustaz'" tidak dapat dicetuskan (tiada sebutan oleh jemaah) –
> sebaliknya gambar Ustaz dipaparkan dengan 5 teknik berbeza di babak-babak utama (lihat §3).
> Apabila video testimoni jemaah ada, letakkan dalam folder dan render semula – struktur sedia untuk itu.

## 2. Transkrip sebenar (Whisper large-v3, disemak 2 kali)

**IMG_2031** (0.00–1.78): *"Assalamualaikum warahmatullahi wabarakatuh."*

**IMG_2048:**
| Masa sumber | Ucapan |
|---|---|
| 0.00–5.04 | "Masjid Quba merupakan masjid pertama yang melaksanakan solat **secara berjemaah**." |
| 5.14–7.92 | "Yang kedua, Masjid Quba mempunyai **19 pintu**." |
| 7.96–13.30 | "Dua pintu besar untuk jemaah lelaki dan satu pintu besar untuk **muslimat** pula." |

Klip lapangan terbang: Whisper "mendengar" frasa seperti *"Terima kasih kerana menonton"* – ini **halusinasi** atas bunyi bising, bukan ucapan sebenar. Tidak digunakan.

### Sebutan "Ustaz / Mutawif / Ustaz Zulhafeez"
Tiada dalam mana-mana audio (Ustaz sendiri yang bercakap). Paparan nama/gambar diletakkan pada babak di bawah.

## 3. Senarai keputusan suntingan (EDL) – timecode output

| Masa | Babak | Visual (lapisan dasar) | Gambar Ustaz / grafik | Teks besar | Bunyi |
|---|---|---|---|---|---|
| 0:00.0–0:02.1 | **Hook** | IMG_2031 0–2.1 s, zoom 1.55→1.38 ke Ustaz | – | "ASSALAMUALAIKUM / WARAHMATULLAHI / WABARAKATUH" muncul serentak setiap perkataan | Suara salam asal, muzik lembut |
| 0:02.1–0:04.9 | Pengenalan | IMG_2032 slow-mo 0.2×, push-in 1.0→1.14 | **Lower-third tandatangan**: tag "MUTAWIF", "USTAZ ZULHAFEEZ" (serif emas bercahaya, garis emas memanjang), "Mutawif \| Darul Mubarak Travel & Tours". Pil atas "Darul Mubarak Travel & Tours – BERSAMA MUTAWIF" + logo (kekal hingga 0:45.8) | – | Impact + shimmer |
| 0:04.9–0:14.3 | Perjalanan bermula | 4 klip lapangan terbang (2.9/2.2/2.4/1.9 s), zoom bergilir | – | "PERJALANAN **BERMULA**" → "DARI TANAH AIR KE **TANAH SUCI**" | Ambien lapangan terbang -20 dB, muzik naik + daf |
| 0:14.3–0:16.7 | Montaj foto | IMG_9497 Ken Burns 1.0→1.14 | Pin lokasi "JABAL RAHMAH – Arafah" | "DI SETIAP LANGKAH **PERJALANAN**" (kekal 0:14.3–0:23.9) | Whoosh |
| 0:16.7–0:19.1 | | Latar IMG_9407 kabur | **B. Bingkai foto terapung** (bingkai emas, condong → lurus, sinar cahaya melintas) | | Whoosh |
| 0:19.1–0:21.5 | | Latar IMG_2177 kabur, parallax | **A. Cut-out sinematik** (MODNet) dengan cahaya rim emas, naik + skala | | Shimmer |
| 0:21.5–0:23.9 | | **C. Skrin terbelah**: atas F0F0E1AF (vest DM), bawah IMG_3195 (bersama jemaah), garis emas di tengah, pan bertentangan | | | Whoosh |
| 0:23.9–0:29.1 | **Tazkirah Masjid Quba** | IMG_2048 0–5.2 s, zoom 1.05→1.12 | Pin "MASJID QUBA – Madinah" | "MASJID **PERTAMA**" (0:25.0) → "SOLAT **BERJEMAAH**" (0:27.7) | Suara Ustaz; muzik turun (ducking -10 dB) |
| 0:29.1–0:31.9 | | IMG_2048 5.2–8.0 s, **punch-in** 1.28 | – | Kaunter "1 → **19**" + "PINTU" (0:30.85), di langit atas kepala Ustaz (tidak menutup wajah) | Bunyi tik ×19 |
| 0:31.9–0:37.4 | | IMG_2048 8.0–13.5 s | – | "**2** PINTU BESAR / JEMAAH LELAKI" (0:31.86) → "**1** PINTU BESAR" (0:33.94) | |
| *(sepanjang 0:23.9–0:37.3)* | | | | Subtitle perkataan-demi-perkataan (Inter ExtraBold 62, perkataan aktif dalam pil emas, kata kunci emas), y≈1500 | |
| 0:37.4–0:39.8 | Peralihan emosi | IMG_2048 13.35–14.6 s slow-mo 0.52× (Ustaz berpaling & berjalan) | – | – | Riser, muzik membina |
| 0:39.8–0:45.8 | **Pendedahan tandatangan** | Latar gradien navy→ungu, partikel emas | **D. Galeri kenangan**: cut-out IMG_9620 di tengah dengan halo emas + 4 kad foto terapung (IMG_7005, IMG_2178, AF02554A, d2c10b8f) masuk berperingkat | "BERSAMA MUTAWIF / **USTAZ ZULHAFEEZ**" + "Mutawif \| Darul Mubarak Travel & Tours" | Impact + shimmer, muzik puncak |
| 0:45.8–0:50.6 | Penutup | IMG_2031 slow-mo 0.33×, zoom-out 1.22→1.0 (Masjid Quba malam) | – | "SETIAP PERJALANAN UMRAH / MENINGGALKAN / **SERIBU KENANGAN**" + ornamen | Muzik tenang |
| 0:50.6–0:56.0 | **CTA** | IMG_2177 sangat kabur, tona ungu | Logo DM dalam lencana bulat | "DARUL MUBARAK / TRAVEL & TOURS", tagline, "NAK RASAI PENGALAMAN **UMRAH SEPERTI INI?**", butang "HUBUNGI KAMI" berdenyut, "untuk maklumat pakej umrah" | Impact, fade-out 0.8 s |

**Peralihan:** setiap potongan (16 kesemuanya) = kilatan emas lembut 0.2 s + zoom punch 5% + whoosh perlahan.
**Gred warna:** kontras +7%, tepu +10%, highlight/midtone hangat ke emas, bayang kurang biru, vignette lembut. Kulit kekal semula jadi.
**Partikel:** debu emas terapung pada babak hook, montaj foto dan pendedahan/penutup sahaja (tidak semasa Ustaz bercakap).

## 4. Audio
- Suara Ustaz: high-pass 85 Hz, pengurangan bunyi (afftdn), EQ kejelasan +2 dB @3 kHz, kompresor ringan; disamakan kenyaringan.
- Muzik: instrumental gaya maqam Hijaz (oud + dengung + daf) dijana sendiri (`../umrah-ramadan-2027/render/islamic_music.py`) – **bebas hak cipta**. Struktur: lembut → membina (perjalanan) → tenang (tazkirah) → puncak (pendedahan) → damai (penutup).
- Ducking automatik -10 dB ketika suara.
- Muzik video rujukan tidak digunakan.

## 5. Tipografi
Poppins/Cinzel tidak dapat dimuat turun dalam persekitaran render (GitHub disekat), jadi digunakan:
- **Inter** Black/ExtraBold (kata kunci & subtitle – geometri hampir sama dengan Poppins)
- **Caladea** Bold (nama & tajuk elegan – menggantikan Cinzel/Trajan)

Untuk CapCut: guna Poppins Bold (kata kunci), Poppins Medium (subtitle), Cinzel (nama) mengikut jadual di atas.

## 6. PERLU DISAHKAN sebelum muat naik
- [ ] **"…satu pintu besar untuk *muslimat* pula"** – perkataan terakhir kurang jelas dalam rakaman (Whisper dengar "masjid"). Fakta umum: Masjid Quba ada 3 pintu utama (2 lelaki, 1 wanita), jadi "muslimat" paling munasabah. Sila dengar & sahkan.
- [ ] **"solat *secara* berjemaah"** – Whisper dengar "sejarah (ber)jemaah"; "secara berjemaah" ialah bacaan yang bermakna. Sila sahkan.
- [ ] Lelaki berbaju merah di lapangan terbang **tidak dilabel** sebagai Ustaz Zulhafeez (identiti tidak disahkan). Klip ini hanya digunakan sebagai suasana "perjalanan bermula".
- [ ] Label "JABAL RAHMAH – Arafah" pada IMG_9497 (berdasarkan bukit & tiang putih dalam gambar).
- [ ] Gambar IMG_3195 menunjukkan Ustaz bersama seorang jemaah – pastikan jemaah itu tidak keberatan wajahnya dipaparkan.
- [ ] **Tiada no. telefon / pautan** dalam CTA kerana tidak dibekalkan untuk video ini. Beritahu nombor/pautan untuk dimasukkan.

## 7. Cara render semula
```bash
export SRC_DIR=/path/to/src OUT_DIR=/path/to/out
# src/: footage/*.MOV|mp4, ustaz/*.jpg (IMG_3195.heic -> .jpg), cut/*.png, logo.png
python3 render/make_cutouts.py modnet.onnx $SRC_DIR/cut $SRC_DIR/ustaz/IMG_2177.jpg $SRC_DIR/ustaz/IMG_9620.jpg
python3 render/build.py audio
python3 render/build.py video
python3 render/build.py preview 1.0,25.5    # bingkai PNG untuk semakan
```
Keperluan: ffmpeg, Python 3 + Pillow + numpy (+ onnxruntime untuk cut-out), fon Inter & Caladea.
Semua masa, klip dan teks dalam `render/edl.py` & `render/build.py` (`build_overlays`).
