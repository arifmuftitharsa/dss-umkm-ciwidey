# Evidence — sesudah perbaikan T-10 (angka evaluasi palsu di kode)

Tanggal pengujian: 5 September 2026

## Ringkasan

Kode mati (tidak pernah dipanggil, tidak pernah tampil ke pengguna) yang berisi angka
evaluasi hardcoded/palsu, bertentangan dengan hasil nyata skripsi (T-14, T-18) — dihapus
sepenuhnya sebelum deploy karena repo publik & jadi Lampiran B skripsi.

Verifikasi ulang sebelum hapus (grep menyeluruh `app/`): dikonfirmasi ketiga lokasi memang
tidak dipanggil dari mana pun, termasuk dari perubahan T-4 kemarin yang menyentuh file yang
sama (`core/forecasting.py`, `core/inventory.py`) — T-4 tidak menyerempet fungsi-fungsi ini.

## Yang dihapus

| Lokasi | Isi |
|--------|-----|
| `app/core/forecasting.py` | `_EVAL_RESULTS` (dict hardcoded MAE/RMSE/MAPE per produk), `evaluate_models()`, `ablation_study()` — plus 2 baris docstring modul yang merujuk keduanya |
| `app/core/inventory.py` | `simulasi_skenario()` (stockout rate 18,5% vs 4,2% hardcoded, bertentangan dengan Tabel 4.22 skripsi yang hasil sebenarnya justru sebaliknya) |
| `app/views/research.py` | File dihapus sepenuhnya (bukan cuma sebagian) — satu-satunya pemanggil 3 fungsi di atas, dan tidak pernah di-routing dari `app.py` (dikonfirmasi ulang: `app.py` hanya import `overview, forecasting, inventory, pengaturan`) |

Analisis sebelum eksekusi (dilaporkan & disetujui terpisah): `views/research.py` punya 4 tab
— Tab 1 & 2 langsung bergantung ke angka palsu di atas (kalau fungsi dihapus tapi file
dipertahankan, import pecah); Tab 3 & 4 tidak pakai angka palsu, tapi tetap dead code (tidak
pernah di-routing). Diputuskan hapus file sepenuhnya, bukan hapus sebagian — konten RQ-mapping
yang berguna untuk referensi tetap ada di git history kalau diperlukan nanti, dan tempat yang
lebih tepat untuk dokumentasi semacam itu adalah `docs/` resmi (Minggu 4), bukan halaman
Streamlit mati.

## Pengujian

1. Sintaks: `ast.parse()` pada `core/forecasting.py` dan `core/inventory.py` — OK.
2. Grep ulang pasca-hapus: tidak ada sisa rujukan ke `_EVAL_RESULTS`, `evaluate_models`,
   `ablation_study`, `simulasi_skenario`, atau `views.research` di `app/`.
3. Smoke test import: `core.forecasting.forecast_future`, `core.inventory.material_demand_7d`,
   `core.inventory.inventory_table`, dan keempat halaman hidup (`overview`, `forecasting`,
   `inventory`, `pengaturan`) — semua berhasil di-import tanpa error.
4. Pengujian UI end-to-end (`streamlit run app.py`, headless, browser):
   - **Ringkasan Operasional**: 1.637 unit (baseline tidak berubah), 1 bahan perlu dibeli,
     grafik & rekomendasi tampil normal.
   - **Perkiraan Penjualan**: Selai Stroberi 486 jar (baseline tidak berubah), grafik render
     normal.
   - **Stok & Pembelian**: 6 bahan dipantau, tabel EOQ/ROP/kondisi tampil normal.
   - **Manajemen & Pengaturan**: tab Produk (3 produk P001–P003, sesuai state setelah
     cleanup T-4 kemarin) dan tab Catat Penjualan (riwayat penjualan, dropdown produk)
     tampil normal.
   - Tidak ada error/traceback di halaman mana pun selama pengujian.
5. Server dimatikan bersih (`taskkill /F`) setelah pengujian selesai.

## Kesimpulan

Tidak ada regresi terdeteksi pada fungsi yang masih dipakai. Ketiga lokasi kode mati beserta
angka evaluasi palsunya (kontradiktif dengan hasil skripsi asli) sudah bersih dari repo.
