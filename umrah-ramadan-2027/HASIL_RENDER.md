# HASIL RENDER – Video Umrah Ramadan 2027

| Versi | Fail | Beza |
|---|---|---|
| v1 | `output/DM_UmrahRamadan2027_9x16.mp4` | Hook "RAMADAN KALI INI… DI TANAH SUCI?"; gambar ihram & telekung muncul kecil bersama senarai hadiah |
| v2 | `output/DM_UmrahRamadan2027_9x16_v2.mp4` | Hook "BAYANGKAN… RAMADAN DI TANAH SUCI!"; B-roll berbeza; setiap hadiah (ihram, telekung, Zamzam) dipaparkan skrin penuh tepat ketika disebut |

**Audio (kemas kini):** muzik instrumental gaya Islamik yang dijana sendiri (`render/islamic_music.py`, bebas hak cipta):
melodi oud maqam Hijaz + dengung + rentak daf (bahagian pakej & promosi) + gema. Kesan bunyi (impact, whoosh, riser, sparkle) direndahkan ~50%.
Muzik ±17 dB di bawah suara; naik semasa selitan pakej dan kad akhir. Boleh diganti dengan nasyid berlesen di CapCut jika mahu.
Gambar hadiah daripada folder Drive "Hadiah Percuma" (tiada gambar beg – beg dipaparkan sebagai teks sahaja).

---


**Fail:** `output/DM_UmrahRamadan2027_9x16.mp4`
**Spesifikasi:** 1080×1920 (9:16) • 30 fps • H.264 + AAC 256k • 109.6 saat • kenyaringan -14 LUFS (sesuai TikTok/Reels)

## Struktur video sebenar

| Masa | Babak | Visual | Teks / grafik |
|---|---|---|---|
| 0:00–0:03 | Hook | Kaabah malam (IMG_7400, 4K), crash zoom | "RAMADAN KALI INI… DI TANAH SUCI?" |
| 0:03–0:30 | Emosi | Penyampai ↔ Kaabah (IMG_6432, 6415, 7399) | Lower third syarikat, "RAMADAN PENUH KEBERKATAN", "IBADAH DI TANAH SUCI", "KENANGAN YANG DIRINDUI" |
| 0:30–0:48 | Pakej (selitan muzik, tanpa suara) | Kedua-dua poster sebenar → harga crash zoom → jadual 6 tarikh → hotel & penerbangan | "HARGA SERENDAH RM 7,230", jadual Super Jimat vs Iktikaf |
| 0:48–1:15 | Promosi (suara penyampai) | Penyampai, jemaah DM (IMG_5503, 6637) | "PROMOSI ISTIMEWA", "100 ORANG TERAWAL!", hadiah 1–4 |
| 1:15–1:29 | Tempoh & desakan | Penyampai, jemaah solat (IMG_7516) | "SEHINGGA AKHIR TAHUN 2026", "REBUT SEGERA!" |
| 1:29–1:39 | Penutup emosi | Kaabah malam, slow zoom-out | "Ramadan ini, CIPTA KENANGAN IBADAH DI TANAH SUCI." |
| 1:39–1:50 | CTA + kad akhir | Penyampai → kad akhir | "JOM UMRAH RAMADAN!", butang WhatsApp, 016-524 7001 / 016-524 3001, laman web, no. syarikat & MOTAC |

Subtitle Bahasa Malaysia word-by-word dijana daripada transkrip suara asal (`render/transkrip_master.json`),
dengan pembetulan ejaan (cth. "Darul Mubarak", "Masjidil Haram", "telekung", "Zamzam").

## Suntingan Master Video
- Dikekalkan: 0:01.9–0:32.2 dan 0:37.3–1:33.8 (maksud asal tidak diubah).
- Dibuang: 0:32.8–0:37.3 ("Bayangkan tuan-tuan, perasaan ini…") – ulangan; ruang diganti dengan selitan pakej.
- Akhir rakaman: tiada ucapan "terima kasih kerana menonton" – itu kesilapan transkrip automatik, bukan suara sebenar.

## PEMBETULAN PENTING kepada pelan asal
1. **Ada DUA poster / dua pakej** (pelan awal hanya membaca satu):
   | Pakej | Tarikh 2027 | Super Jimat Ramadan | Super Jimat **Iktikaf** Ramadan |
   |---|---|---|---|
   | Sambut Ramadan | 1–12 Feb | RM 7,550 | RM 7,230 |
   | Awal Ramadan | 11–22 Feb | RM 7,650 | RM 7,330 |
   | Pertengahan Ramadan | 18 Feb–1 Mac | RM 8,150 | RM 7,830 |
   | Akhir Ramadan | 25 Feb–8 Mac | RM 9,850 | RM 8,730 |
   | Akhir Ramadan Sambut Syawal | 4–15 Mac | RM 8,950 | RM 7,830 |
   | Sebulan Ramadan | 8 Feb–11 Mac | RM 13,950 | RM 11,630 |
   Hotel Makkah: Super Jimat = Wahat Al Dhiyafah @ setaraf; Iktikaf = Hotel Oriens Shisha @ setaraf (kedua-dua "200 Meter++").
   Hotel Madinah (kedua-dua): Rua Al Dhiyafah @ setaraf (250 Meter++). Penerbangan: Emirates Airlines @ Qatar Airways.
2. **Promosi DISAHKAN oleh penyampai sendiri** dalam Master Video: 100 orang terawal yang mendaftar pakej Ramadan,
   beg istimewa, kain ihram, mini telekung (jemaah wanita), air Zamzam 500 ml percuma; dibuka sekarang sehingga akhir tahun 2026.

## Perlu disahkan sebelum dimuat naik
- [ ] **No. syarikat**: poster tertulis "2005011025978 (708111-W)" (13 digit). Nombor SSM format baharu biasanya 12 digit, jadi mungkin ada salah taip pada poster. Teks itu disalin tepat seperti poster. Sila sahkan.
- [ ] Ejaan hotel "Hotel Oriens Shisha" (dibaca dari poster resolusi rendah).
- [ ] Harga Iktikaf "RM 7,830" muncul dua kali (Pertengahan & Sambut Syawal). Begitulah yang tertera pada poster.
- [ ] "Bilik berempat, harga seorang": kenyataan "harga seorang" adalah andaian biasa industri. Buang jika tidak tepat.
- [ ] Gambar beg istimewa tiada – hantar jika mahu dimasukkan.

## Gambar hadiah (kain ihram & mini telekung)
Skrip sudah ada slot untuk gambar produk sebenar (muncul pada 1:02 dan 1:04 bersama senarai hadiah).
Muat naik ke folder Google Drive dengan nama `ihram.jpg` dan `telekung.jpg` (atau ke `gifts/` dalam folder sumber),
kemudian render semula. Gambar dalam chat tidak boleh dicapai oleh skrip.

## Cara render semula
```bash
export SRC_DIR=/path/to/src OUT_DIR=/path/to/out   # src: master.mov, p1.jpg, p2.jpg, logo.png, broll/, gifts/
VARIANT=v2 python3 render/build_base.py      # potong, reframe 9:16, zoom, colour grade
python3 render/build_audio.py     # suara dibersihkan + muzik + SFX + ducking
cp render/transkrip_master.json $OUT_DIR/tx.json
python3 render/build_overlay.py   # grafik, tipografi, subtitle → mp4 akhir
```
Keperluan: ffmpeg, Python 3 + Pillow + numpy, fon Inter & Caladea.

## Prompt Higgsfield
Tiada klip AI digunakan. Semua visual ialah B-roll sebenar syarikat. Jika mahu klip Masjid Nabawi (tiada dalam B-roll),
guna prompt HF-02 dalam `PELAN_PRODUKSI_VIDEO.md` §5 dan ganti segmen 0:14–0:20 atau 1:29–1:39.
