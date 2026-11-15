# Kamus Mandarin Offline

Kamus Indonesia–Mandarin (aksara sederhana) offline untuk Android — WebView + data
inline, tanpa internet, tanpa iklan, tanpa akun.

- **Paket:** `id.kamusmandarin.offline` — **v1.0.0** (versionCode 1)
- **APK:** `apk/dist/KamusMandarin-Offline-v1.0.0.apk` (12 MB)
- **Entri:** 121.718 (dari 124.769 baris sumber, digabung per hanzi + bacaan)

## Cara mencari

Satu kotak cari, tiga arah — ketik apa saja:

| Ketik | Contoh | Hasil |
|---|---|---|
| Bahasa Indonesia | `belajar`, `terima kasih`, `air` | 学习, 谢谢, 水 |
| Hanzi sederhana | `学习`, `谢谢`, `中国` | arti Indonesia + pinyin |
| Pinyin tanpa nada | `xuexi`, `ni hao` | 学习, 你好 |
| Pinyin bernada | `xuéxí` | 学习 |
| Pinyin bernomor | `xue2xi2` | 学习 |

Mode filter: Semua / 🇮🇩 Indonesia / 🀄 Hanzi / 🔤 Pinyin. Pinyin diwarnai
per nada (1 merah, 2 hijau, 3 biru, 4 ungu, netral abu-abu). Badge **HSK 1–6**
menandai kosakata ujian HSK (paling umum, didahulukan di hasil cari).

Fitur: ⭐ favorit, 🕘 riwayat (50 terakhir), 🎲 kata acak, 📚 jelajahi HSK 1,
📋 salin, kata gaul → kata baku (`mau`→ingin, `nggak`→tidak, `gue`→saya,
`makasih`→terima kasih).

## Sumber data & lisensi

- **Kamus:** `data/CC-CPLUSDICT_id.u8` — CC-CPLUSDICT Indonesia
  (R8VEN-LLC/CC-CPLUSDICT), turunan CC-CEDICT, lisensi **CC BY-SA 4.0**.
  Atribusi: CEDICT © 1997, 1998 Paul Andrew Denisowski; CC-CEDICT (komunitas).
- **Penanda HSK:** daftar kosakata HSK 3.0, drkameleon/complete-hsk-vocabulary
  (`data/hsk20_*.json` → `data/hsk_map.json`).
- **Jujur soal kualitas:** arti Indonesia adalah **terjemahan mesin** dari
  definisi Inggris CC-CEDICT — bukan dibaca manusia satu per satu. Sebagian
  kecil entri masih mengandung bahasa Inggris, dan beberapa arti bisa kurang
  pas (mis. `mau` tidak ada sebagai arti — pakai `ingin`). Jangan pakai kamus
  ini sendirian untuk urusan hukum/medis.

## Struktur

```
index.html                  UI + logika cari (single file)
data/
  CC-CPLUSDICT_id.u8        sumber kamus (10 MB, CC BY-SA 4.0)
  hsk20_*.json, hsk_map.json  daftar HSK 3.0 (level 1-6)
  kamus_data.js             data ringkas hasil build (12 MB, JANGAN edit manual)
tools/
  build_data.py             .u8 -> kamus_data.js (pinyin bernada, gabung duplikat, tag HSK)
  test_search.js            20 kasus uji peringkat (harus 20/20)
  test_app.js               smoke test index.html (DOM palsu)
apk/
  app/                      AndroidManifest, MainActivity.java (WebView), res, assets
  scripts/01_build_apk.sh   build manual aapt2 (VM, tanpa Gradle)
  scripts/make_icon.py      ikon (merah + 汉 putih)
  keystore.jks              signing key — LOKAL SAJA, jangan masuk GitHub
```

## Build

```bash
$ python3 tools/build_data.py   # bangun ulang kamus_data.js dari .u8
$ node tools/test_search.js     # 20/20 kasus peringkat harus lolos
$ bash apk/scripts/01_build_apk.sh
# -> apk/dist/KamusMandarin-Offline-v1.0.0.apk (BUILD_OK + badging)
```

Build memakai JDK 17 (`~/workspace/jdk/`) + Android SDK build-tools 34.0.0
(`~/workspace/android-sdk/`), pola manual aapt2 yang sama dengan
Basa Jawa / Katolik Digital (Gradle daemon rusak di sandbox ini).

## Versi

Semver 3 digit (MAJOR.MINOR.PATCH, seperti News Offline): PATCH untuk
perbaikan data/UI kecil, MINOR untuk fitur baru. versionCode/Name hardcoded
di `apk/app/AndroidManifest.xml` (sumber kebenaran tunggal).
