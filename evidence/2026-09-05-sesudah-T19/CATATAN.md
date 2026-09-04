# Bukti "Sesudah Perbaikan T-19" — Kartu Akurasi Dihapus dari UI

**Tanggal pengujian:** 5 September 2026
**Commit sebelum perubahan:** `a6cdeb1` (T-1: titik reset operasional)
**Berkas diubah:** `app/views/overview.py`, `app/views/forecasting.py`
**Status:** perbaikan kecil — evidence ini ringkas sesuai instruksi, tak sebesar T-1.

---

## Ringkasan Delapan Prinsip

| Prinsip | Relevan? | Catatan |
|---|---|---|
| C4 Model, CI/CD, audit keamanan, fail-fast, dependency hygiene* | Tidak/sebagian | Perbaikan murni UI-facing, bukan arsitektur/pipeline/rilis/error-handling. *Dependency hygiene tetap diterapkan pada eksekusi (hapus dead code `_akurasi_backtest`, `_AKURASI_PATH`, import `json`/`Path`/`MODEL` yang jadi tak terpakai) |
| Testing berbasis risiko | Sebagian | Bukan modul risiko backend tinggi, tapi tetap diuji visual sesuai instruksi karena menyentuh apa yang dilihat pengguna |
| docs/ vs notes/ | **Ya** | Evidence ini masuk `evidence/`, pola konsisten |
| Version control rapi | **Ya** | Commit tunggal, pesan jelas |

---

## Investigasi (sebelum eksekusi)

Grep menyeluruh `views/`, `components/` untuk "akurasi/accuracy/mape/backtest" — ditemukan
lebih dari 2 tempat awal, tapi setelah ditelusuri: `views/research.py` dan fungsi MAPE-chart
terkait di `components/charts.py` **tak pernah diimpor `app.py` sama sekali** (kode mati,
tak cuma tak dirouting) — di luar scope karena tak pernah tampil ke pengguna manapun.
**Hanya 2 tempat nyata** yang perlu diperbaiki, persis sesuai brief, tak ada yang terlewat.

**Temuan penguat rekomendasi (Opsi A dipilih):** kedua file docstring-nya sendiri sudah
eksplisit menyatakan niat "tanpa istilah teknis" — `overview.py`: *"Ditujukan untuk pemilik
UMKM: bahasa sehari-hari, tanpa rumus dan istilah teknis (MAPE, EOQ, sigma)."*;
`forecasting.py`: *"Pemilihan model dan metrik teknis sengaja tidak ditampilkan di sini."*
Kartu akurasi **bertentangan langsung** dengan niat tertulis di file yang sama — bukti kuat
ini penyimpangan dari desain asli, bukan keputusan desain baru.

---

## Verifikasi UI

**Ringkasan Operasional:** kartu "Akurasi Perkiraan 92%" hilang. 3 kolom tersisa tertata
rapi tanpa kolom kosong: **Perkiraan Penjualan** (1.637), **Bahan Perlu Dibeli** (1),
**Hari Libur Nasional** (Ada).

**Perkiraan Penjualan:** kartu "Akurasi Model 92.1%" hilang. 2 kolom tersisa tertata rapi
proporsional: **Total Perkiraan 7 Hari** (486 jar), **Rata-rata per Hari** (69 jar).

Kedua halaman: tak ada error, tak ada traceback, layout tak rusak.

**Konsistensi docstring:** kedua file sekarang **benar-benar cocok** dengan niat yang
tertulis di komentar pembuka masing-masing — janji "tanpa istilah teknis" akhirnya
terpenuhi sepenuhnya, bukan cuma tertulis tapi tak dijalankan.

---

## Kesimpulan

T-19 selesai. Perubahan murni penghapusan (tak ada penambahan elemen baru), diverifikasi
visual di browser sungguhan pada kedua halaman yang terdampak. Dead code terkait
(`_akurasi_backtest`, `_AKURASI_PATH`, import `json`/`Path` di `forecasting.py`, import
`MODEL`/`MODEL_TERBAIK` tak terpakai di `overview.py`) dibersihkan sekalian — diverifikasi
dulu lewat grep tak ada pemanggil lain sebelum dihapus, konsisten pola kehati-hatian sesi
sebelumnya.
