# Bukti "Sesudah Perbaikan T-7b" — Penyelarasan Tanggal Cuaca + Fail-Fast

**Tanggal pengujian:** 5 September 2026
**Commit sebelum perubahan:** `e903dd0` (T-2: hapus noise acak)
**Berkas diubah:** `app/data/weather.py`, `app/core/forecasting.py`, `app/data/record_sales.py`
**Status:** SESUDAH T-7b diperbaiki — pembanding terhadap dua evidence sebelumnya (4 Sept
sebelum apa pun diperbaiki, 5 Sept sesudah T-2 saja).

---

## Ringkasan Delapan Prinsip

| Prinsip | Relevan? | Catatan |
|---|---|---|
| C4 Model | Tidak | Tak ada dokumentasi arsitektur di langkah ini |
| CI/CD | Tidak | Pengujian manual pembanding |
| Testing berbasis risiko | **Ya** | `weather.py` langsung memberi makan `core/forecasting.py`, rantai risiko tertinggi |
| Audit keamanan | Tidak | Belum ada deploy/tag rilis |
| docs/ vs notes/ | **Ya** | Evidence lagi masuk `evidence/`, pola konsisten dari sesi-sesi sebelumnya |
| Fail-fast | **Ya, inti tugas ini** | `except Exception: pass` diganti exception spesifik + logger, fallback klimatologi kini punya jejak yang bisa diperiksa (bukan senyap) |
| Dependency hygiene | **Ya** | `import requests` dipindah ke level modul (sebelumnya di dalam try, rawan `NameError` di klausa except-nya sendiri kalau import gagal); `logging` dipakai (stdlib, tanpa dependency baru) |
| Version control rapi | **Ya** | Satu commit logis mencakup dua bug (mismatch tanggal + except senyap) + flag status + evidence |

---

## Keputusan Scope — Opsi 2 (Flag Disiapkan, UI Belum Disentuh)

Sebelum eksekusi, dibahas dulu: log `logger.info`/`logger.warning` HANYA muncul di terminal
server (developer-only) — dikonfirmasi tak ada jembatan otomatis dari modul `logging` Python
ke UI Streamlit. Pemilik UMKM yang buka aplikasi lewat browser tidak akan pernah melihatnya.

Tiga opsi dipertimbangkan: (1) biarkan cuma log developer, (2) tambah flag status dari
`fetch_rainfall_forecast()`/`future_exogenous()` tapi jangan sentuh `views/`, (3) sekalian
tampilkan catatan di UI. **Opsi 2 dipilih** — alasan: prinsip #2 CLAUDE.md eksplisit "jangan
poles UI sebelum T-1/T-2 beres", dan proyek sudah punya slot khusus (T-19) buat perubahan UI
yang dikumpulkan untuk Minggu 3, bukan dicicil. Flag `used_climatology` (nama dipilih
konsisten dengan istilah "klimatologi" yang sudah dipakai di kode, bukan istilah baru)
sekarang tersedia dari `fetch_rainfall_forecast()` (via `RainfallForecast` NamedTuple) dan
diteruskan `future_exogenous()` — kedua pemanggil (`core/forecasting.py`,
`data/record_sales.py`) sudah disesuaikan menampung nilainya, **belum dipakai untuk logic
atau ditampilkan apa pun** — disiapkan murni untuk Minggu 3/T-19 nanti tanpa perlu bongkar
ulang `weather.py`.

---

## Verifikasi Flag `used_climatology`

Dijalankan independen (Python langsung, di luar UI) sebelum Run A:

```
INFO data.weather: fetch_rainfall_forecast: start_date 2026-01-01 ada di masa lalu relatif
hari ini (2026-09-05) -- Open-Meteo Forecast API tak bisa menjawab tanggal itu ...
used_climatology (independen, sebelum Run A): True
```

**Sesuai ekspektasi.** T-1 belum diperbaiki, `last_date` masih terkunci 2025-12-31, sehingga
`start_date` (2026-01-01) tetap di masa lalu relatif hari sungguhan (5 Sept 2026) — flag
`True` benar mendeteksi kondisi ini persis seperti dirancang.

---

## Hasil Pengujian Reload — P001 Selai Stroberi, Horizon 7 Hari

| Run | Kapan | Total 7 Hari |
|---|---|---|
| Run A | Awal pengujian | **486 jar** |
| Run B | Reload segera (replikasi kondisi T-2 kemarin) | **486 jar** |
| Run C | Reload setelah jeda ±6 menit sungguhan | **486 jar** |

**Ketiganya identik**, termasuk setelah jeda 6 menit — jeda yang sengaja dipakai untuk
memberi kesempatan cuaca live API benar-benar berbeda (bukan cuma kebetulan window pengujian
terlalu singkat, seperti catatan di evidence T-2 kemarin).

---

## Perbandingan Terhadap Semua Evidence Sebelumnya

| Tanggal | Kondisi kode | Reload #1 | Reload #2 | Reload #3 (+jeda) | Konsisten? |
|---|---|---|---|---|---|
| 4 Sept | Sebelum T-2 & T-7b | 502 jar | 498 jar | *(tak diuji)* | **Tidak** |
| 5 Sept (pagi) | Sesudah T-2 saja | 486 jar | 486 jar | *(tak diuji)* | Ya, tapi ditandai *kemungkinan kebetulan* — window uji singkat |
| 5 Sept (sekarang) | Sesudah T-2 + T-7b | 486 jar | 486 jar | 486 jar | **Ya, dengan jeda 6 menit sungguhan** |

---

## Kesimpulan — Jujur, Termasuk Batasan Pengujian Ini

**T-7b terbukti sebagian, bukan sepenuhnya, dan itu perlu dijelaskan dengan tepat — bukan
dipoles.**

Yang **benar-benar teruji dan terbukti** hari ini:
1. Cabang "`start_date` di masa lalu relatif hari sungguhan" (kondisi yang selalu aktif
   sekarang, karena T-1 belum selesai) sekarang **konsisten dan deterministik** — 3 reload,
   termasuk berjeda 6 menit, semua 486 jar. Sebelumnya (4 Sept) cabang setara ini
   menghasilkan hasil salah/tak konsisten karena tertimpa data API yang salah tanggal.
2. Flag `used_climatology` terverifikasi mendeteksi kondisi ini dengan benar (`True`).
3. `except Exception: pass` sudah diganti exception spesifik + logger — kegagalan (kalaupun
   terjadi) sekarang punya jejak, bukan senyap.

Yang **BELUM teruji** oleh pengujian hari ini, dan perlu disadari sebagai batasan:

**Cabang "`start_date` hari ini atau ke depan" (jalur API live dengan realignment offset)
tidak ikut tereksekusi dalam pengujian Run A/B/C di atas**, karena T-1 belum diperbaiki —
`last_date` masih terkunci di masa lalu, sehingga setiap panggilan `forecast_future()` selalu
jatuh ke cabang klimatologi (deterministik, memang seharusnya selalu sama). Kebenaran logika
offset/realignment untuk cabang API live sudah diverifikasi terpisah lewat smoke test Python
manual (lihat percakapan pengembangan, bukan bagian evidence UI ini) yang menunjukkan hasil
API tergeser dengan benar sesuai offset — tapi **belum diverifikasi lewat pengujian reload
berulang di UI sungguhan**, karena kondisi itu baru akan aktif setelah T-1 selesai.

**Implikasi untuk pengujian masa depan:** setelah T-1 diperbaiki, "identik di setiap reload"
BUKAN lagi kriteria kebenaran yang tepat untuk diuji ulang — begitu `start_date` jadi hari
sungguhan, nilai cuaca live SEHARUSNYA berbeda dari hari ke hari (itu perilaku benar, bukan
bug). Kriteria yang tepat saat itu: forecast harus **konsisten dalam jendela waktu pendek di
hari yang sama** (mis. beberapa reload dalam hitungan menit), tapi boleh berbeda secara wajar
antar-hari kalender yang berbeda. Pengujian evidence ini perlu diulang lagi setelah T-1
selesai, dengan kriteria yang disesuaikan itu — dicatat di sini supaya tidak lupa/salah
asumsi nanti.

**Ringkasan satu kalimat:** T-7b memperbaiki bug yang benar-benar ada (mismatch tanggal +
kegagalan senyap), gejalanya (inkonsistensi reload) sekarang terbukti hilang untuk kondisi
yang bisa diuji hari ini, tapi klaim "T-7b sepenuhnya benar untuk semua kondisi" masih
menunggu verifikasi lanjutan setelah T-1 selesai.
