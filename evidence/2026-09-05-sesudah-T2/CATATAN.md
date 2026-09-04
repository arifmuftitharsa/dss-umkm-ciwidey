# Bukti "Sesudah Perbaikan T-2" — Penghapusan Noise Acak di Forecasting

**Tanggal pengujian:** 5 September 2026
**Commit sebelum perubahan:** `638ae7a` (Rapikan struktur evidence, T-19/T-20, revisi T-1)
**Berkas diubah:** `app/core/forecasting.py`
**Status:** SESUDAH T-2 diperbaiki — pembanding langsung terhadap
`evidence/2026-09-04-sebelum-perbaikan/CATATAN.md`.

---

## Ringkasan Delapan Prinsip (sebelum eksekusi langkah ini)

| Prinsip | Relevan? | Catatan |
|---|---|---|
| C4 Model | Tidak | Tak ada dokumentasi arsitektur ditulis di langkah ini |
| CI/CD | Tidak | Pengujian manual pembanding, bukan pipeline otomatis |
| Testing berbasis risiko | **Ya** | Tepat menguji ulang modul risiko tertinggi (`core/forecasting.py`) setelah diedit |
| Audit keamanan | Tidak | Belum ada deploy/tag rilis |
| docs/ vs notes/ | **Ya** | Bukti masuk `evidence/` (snapshot immutable), bukan `docs/` atau `notes/` — pola sudah ditetapkan sesi sebelumnya |
| Fail-fast | **Ya** | Diterapkan langsung — dua skenario hasil (identik/tidak identik) disiapkan sebelum eksekusi, supaya hasil apa pun ditangani jujur tanpa menyesuaikan cerita sesudahnya |
| Dependency hygiene | **Ya** | `noise_rng` dan `mu` yang jadi tak terpakai di cabang `else` sekalian dihapus, bukan ditinggal sebagai dead code |
| Version control rapi | **Ya** | Diff minimal (−6 baris, tanpa penambahan), commit tunggal kode+bukti, pesan jujur soal temuan |

---

## Temuan Kunci — WAJIB Dibaca Sebelum Angka di Bawah

**Penghapusan noise di baris 90-100 BUKAN penyebab variasi 502 vs 498 yang tercatat di evidence
4 September.** Ini bukan interpretasi — dibuktikan langsung lewat eksperimen terkontrol sebelum
kode diubah sama sekali:

```python
# noise_rng = np.random.default_rng(42 + sum(ord(c) for c in product_id))
```

Seed ini **konstan per product_id** (`"P001"` selalu menghasilkan seed `267`), bukan diacak
ulang tiap panggilan. RNG baru dengan seed sama, dipanggil `.normal()` sejumlah hari horizon
(selalu 7 kali untuk horizon 7 hari) yang sama pula — menghasilkan **urutan angka noise yang
identik setiap kali fungsi dipanggil**, untuk produk yang sama.

**Bukti langsung (dijalankan 5 September, SEBELUM baris noise dihapus):**

```python
_, fut1, _ = forecast_future(None, 'P001', horizon=7)
_, fut2, _ = forecast_future(None, 'P001', horizon=7)
# Run 1 yhat: [124, 82, 96, 69, 50, 40, 37]  Total: 498
# Run 2 yhat: [124, 82, 96, 69, 50, 40, 37]  Total: 498
# IDENTIK
```

Dua panggilan berturut, kode ASLI (noise masih ada), hasil **identik sempurna** — bukan cuma
totalnya, tiap angka harian sama persis. Ini mengonfirmasi noise memang deterministik seperti
dugaan analisis matematis, dan **bukan sumber variasi yang terekam di UI 4 September**.

**Kesimpulan yang jujur:** variasi 502 vs 498 pada evidence 4 September kemungkinan besar
disebabkan **T-7b** (bug penyelarasan tanggal cuaca) — `weather.future_exogenous()` meminta
cuaca mulai `last_date+1` (2026-01-01), tapi Open-Meteo Forecast API selalu membalas untuk
rentang hari dari **hari ini sungguhan** (server API), lalu nilainya ditempelkan seolah untuk
tanggal Januari 2026. Model cuaca live bisa saja ter-refresh dalam rentang menit antar reload,
menghasilkan `rainfall_mm` berbeda → fitur berbeda → prediksi rekursif berbeda — meskipun
noise-nya sendiri (kalau masih ada) akan tetap sama persis.

**Baris noise tetap harus dihapus** — bukan karena ia terbukti jadi penyebab 502/498, tapi
karena ia tetap merupakan cacat independen: menambahkan simpangan acak buatan tanpa nilai
informasi ke angka yang dipakai pemilik UMKM untuk memutuskan belanja bahan baku. Tujuan T-2
(hilangkan noise buatan dari prediksi) **tercapai**, terlepas dari apakah ia satu-satunya
penyebab yang terekam kemarin.

---

## Hasil Pengujian Reload (Skenario A — hasil sesuai ekspektasi)

Setelah kode diubah, `streamlit run app.py` dijalankan dari venv T-8, dibuka di Browser pane,
halaman Perkiraan Penjualan, produk P001 Selai Stroberi (default), horizon 7 hari — kondisi
identik dengan pengujian 4 September.

| | Total 7 Hari | Rata-rata/Hari | Akurasi Model (label statis) |
|---|---|---|---|
| Run A | **486 jar** | 69 jar | 92.1% |
| Run B (reload penuh) | **486 jar** | 69 jar | 92.1% |

**IDENTIK.** Dibaca via accessibility tree (`read_page`), metode konsisten kedua run — bukan
tebakan visual.

### Perbandingan eksplisit dengan baseline 4 September

| | Sebelum (4 Sept, kode lama) | Sesudah (5 Sept, kode baru) |
|---|---|---|
| Reload #1 | 502 jar | 486 jar |
| Reload #2 | 498 jar | 486 jar |
| **Beda antar-reload?** | **Ya (502 ≠ 498)** | **Tidak (486 = 486)** |

Catatan: totalnya sendiri (502/498 → 486) tidak bisa dibandingkan apel-ke-apel — beda hari
pengujian (4 vs 5 September) berarti input cuaca dan histori berbeda secara wajar. Yang
dibandingkan di sini murni **konsistensi antar-reload pada hari yang sama**, dan itu yang
menjadi bukti T-2 selesai.

---

## Status Server

Streamlit dijalankan di venv (`app/venv/`), port 8501, log start bersih tanpa error (sama
seperti pengujian T-8 sebelumnya). Proses **dimatikan bersih** (`taskkill /F`) setelah
pengujian selesai — pelajaran dari sesi 4 September (T-1) di mana proses yang masih jalan
sempat mengunci file `.txt` saat `mv`.

---

## Rekomendasi Prioritas T-7b

**T-7b sebaiknya naik prioritas, dikerjakan segera setelah T-2 ini** — bukan menunggu giliran
sesuai urutan brief semula (yang menempatkannya sebagai "kecil, ikut selesai bareng T-1").
Alasan:

1. **Dampaknya lebih besar dari deskripsi awal.** Brief semula menyebutnya sebagai "prediksi
   tertempel di tanggal salah" — kedengarannya kosmetik. Tapi hasil investigasi hari ini
   menunjukkan ia kemungkinan **penyebab nyata inkonsistensi forecast antar-waktu** yang
   sebelumnya salah diatribusikan ke T-2. Pengguna yang membuka aplikasi dua kali di hari
   yang sama bisa mendapat rekomendasi belanja berbeda tanpa penjelasan — ini merusak
   kepercayaan terhadap sistem sama seperti T-2, bahkan berpotensi lebih membingungkan karena
   tak ada cara mudah menjelaskan ke pengguna awam kenapa angkanya berubah.
2. **Berkaitan langsung dengan T-1.** Begitu T-1 diperbaiki (forecast berbasis tanggal
   sungguhan, bukan terkunci Jan 2026), bug penyelarasan tanggal cuaca ini otomatis jadi
   relevan setiap hari penggunaan normal — bukan cuma saat pengujian.
3. **Belum ada bukti pasti** — analisis di atas kuat tapi berbasis penalaran, bukan pengukuran
   langsung `rainfall_mm` yang berbeda antar-reload (skenario B di instruksi tugas ini tidak
   dieksekusi karena hasil ternyata skenario A). Kalau T-7b dikerjakan, langkah pertamanya
   sebaiknya justru mengonfirmasi ini secara langsung — log/print `rainfall_mm` di beberapa
   reload berturut pada hari yang sama, baru kemudian perbaiki penyelarasan tanggalnya.

Keputusan akhir tetap di tangan Arif — ini rekomendasi berbasis temuan sesi ini, bukan
keputusan final.
