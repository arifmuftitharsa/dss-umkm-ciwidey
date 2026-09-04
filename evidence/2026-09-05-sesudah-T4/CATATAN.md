# Evidence — sesudah perbaikan T-4 (cold start produk baru pasti gagal)

Tanggal pengujian: 5 September 2026

## Ringkasan temuan & perbaikan

T-4 di brief menyebut 3 titik kegagalan resmi. Selama pengerjaan, ditemukan 2 masalah
tambahan yang tidak disebut di brief (dilaporkan ke Arif sebelum dieksekusi, sesuai aturan
standing). Total 5 file kode diubah.

### 1. Tiga titik kegagalan resmi (dari brief)

| # | Lokasi | Masalah | Perbaikan |
|---|--------|---------|-----------|
| 1 | `core/forecasting.py` | `PRODUK[product_id]["mu"]` dari `config.py` statis → `KeyError` untuk produk yang tidak ada di config | Ganti ke `store.get_produk_dict()[product_id]["mu"]`, dengan `ValueError` jelas kalau produk benar-benar tidak ada di database |
| 2 | `core/inventory.py` | `for pid in PRODUK:` baca config, bukan database → produk baru tidak pernah ikut dihitung kebutuhan bahan baku | Ganti ke `for pid in store.get_produk_dict():` |
| 3 | Fallback saat model `None` pakai `np.full(HORIZON, mu)` — `HORIZON` konstanta global, bukan parameter `horizon` yang diminta | Panjang array forecast selalu 7 walau horizon diminta 14/30 hari | Ganti ke `np.full(horizon, mu, dtype=float)` |

### 2. Perluasan scope yang dilaporkan & disetujui sebelum dieksekusi

`config.PRODUK` ternyata dipakai juga di `views/forecasting.py` (dropdown pilih produk) dan
`views/overview.py` (5 titik loop) — tidak disebut di brief. Kalau hanya `core/` yang
diperbaiki, produk baru tetap tidak bisa dipilih/tidak muncul di UI walau perhitungan
backend-nya sudah benar. Diputuskan bersama Arif: satu fungsi sumber tunggal
`store.get_produk_dict()` dipakai di semua 4 file pemanggil (DRY, SRP — `store.py` jadi
satu-satunya tempat yang tahu cara membaca daftar produk).

`data/store.py` — `get_produk_dict()` diperkuat jadi 2 tingkat:
- **DB kosong / belum pernah di-seed**: dianggap kondisi transien normal, BUKAN kegagalan.
  Ditangani dengan memanggil `init_db()` dulu (sudah idempotent & self-healing dari desain
  lama) — tabel dibuat & di-seed otomatis dari `config.PRODUK` kalau memang belum ada.
- **Error sungguhan** (file database korup, permission error, dsb): baru di sini fallback ke
  `config.PRODUK` statis dipakai, DAN dicatat lewat `logger.warning()` dengan detail
  exception — supaya developer tahu kalau ini terjadi saat testing/deployment, konsisten
  dengan pola logging T-7b (`weather.py`). Tidak perlu tampil ke UI (beda pertimbangan dari
  `used_climatology` T-7b) karena ini murni masalah infrastruktur, bukan sesuatu yang bisa
  ditindaklanjuti pemilik UMKM dari dashboard.

Dict hasil query yang SUKSES tapi kosong (misal pemilik sengaja hapus semua produk) tetap
dikembalikan apa adanya — bukan dianggap kegagalan, supaya tidak diam-diam memunculkan
kembali produk default yang sudah sengaja dihapus.

### 3. Bug tak terduga #1 — `NaT` untuk produk tanpa riwayat sama sekali

Ditemukan lewat smoke test Python (sebelum UI testing), sebelum ada persetujuan terpisah —
konsekuensi langsung dari rencana yang sudah disetujui, jadi diperbaiki dalam giliran yang
sama tanpa siklus approval baru.

Produk yang baru ditambah lewat dashboard dan belum pernah dicatat penjualannya sama sekali
(nol baris di `historis_penjualan.csv`) membuat `last_date = s["date"].max()` menghasilkan
`NaT`. `weather.future_exogenous(NaT, ...)` lalu crash:
`ValueError: Neither start nor end can be NaT`.

Ini BEDA dari kasus cold-start reset operasional T-1 (yang selalu punya
`tanggal_mulai_operasional` sebagai titik acuan valid). Diperbaiki dengan cabang eksplisit:
kalau riwayat kosong sama sekali, `last_date` dipatok ke hari ini dikurangi 1 hari — forecast
produk baru paling masuk akal mulai dari hari ini sungguhan.

### 4. Bug tak terduga #2 — chart crash untuk produk tanpa riwayat

Ditemukan HANYA lewat pengujian UI browser langsung (memilih produk baru P004 di dropdown
Perkiraan Penjualan) — smoke test Python tidak menangkap ini karena `forecast_future()`
sendiri sudah benar (KPI card sempat tervalidasi benar: 175 botol / 25 botol per hari), tapi
`components/charts.py` crash saat menggambar chart:

```
IndexError: single positional indexer is out-of-bounds
```

Penyebab: kode "jembatan" garis penghubung riwayat→perkiraan mengasumsikan
`history.date.iloc[-1]` selalu ada. Untuk produk baru, `history` kosong (memang belum pernah
terjual — ini kebenaran, bukan kekurangan data yang perlu ditambal angka karangan). Diperbaiki
dengan guard `if not history.empty:` di sekitar trace jembatan itu.

### 5. Perbaikan tambahan dalam scope T-4 (instruksi terpisah dari Arif)

`views/overview.py` — `pid_utama = "P003"` hardcode di section "Produk dengan penjualan
tertinggi". Dicek dulu maksud aslinya: teks UI eksplisit bilang "produk dengan penjualan
tertinggi", dan P003 memang kebetulan `mu` tertinggi di `config.py` lama (80 vs 40 vs 15) —
jadi hardcode ini BUKAN pilihan sembarang, tapi statis (tidak ikut berubah kalau produk
ditambah/dihapus). Diganti jadi dinamis: `max(produk, key=lambda pid: produk[pid]["mu"])` —
mempertahankan maksud bisnis aslinya (produk ber-volume tertinggi), bukan sekadar menghindari
crash.

## Perubahan file

| File | Perubahan |
|------|-----------|
| `app/data/store.py` | `get_produk_dict()` diperkuat 2 tingkat (self-healing vs error sungguhan + logging), tambah `import logging` |
| `app/core/forecasting.py` | `mu`/daftar produk dari `store.get_produk_dict()`, `ValueError` untuk produk tak dikenal, fix `NaT` (riwayat kosong), fix `horizon` vs `HORIZON` |
| `app/core/inventory.py` | Loop bahan baku pakai `store.get_produk_dict()`, bukan `config.PRODUK` |
| `app/views/forecasting.py` | Dropdown produk & label pakai `store.get_produk_dict()` |
| `app/views/overview.py` | Semua loop & `pid_utama` pakai `store.get_produk_dict()`, hardcode `"P003"` dihapus |
| `app/components/charts.py` | Guard `if not history.empty:` di trace jembatan (bug tak terduga #2) |

## Pengujian

### A. Smoke test Python (sebelum UI testing)
- Tambah produk uji `P004` (Sirup Stroberi, mu=25, satuan botol) langsung ke DB.
- `forecast_future(df, "P004")` dijalankan — awalnya crash `NaT` (temuan #3 di atas),
  setelah fix berhasil, hasil `yhat` flat 25.0 sesuai `mu` (produk baru tanpa model .joblib,
  tanpa riwayat → base demand datar dari input mu, sesuai desain existing "model belum
  tersedia").
- `pid_utama` di `overview.py`: dites hapus `P003` dari dict sementara (test env, dikembalikan
  segera setelah), `pid_utama` otomatis pindah ke produk mu tertinggi berikutnya tanpa crash.
  Dikembalikan setelah verifikasi.

### B. Pengujian UI browser end-to-end (Streamlit dijalankan penuh, bukan cuma smoke test)

1. Jalankan `streamlit run app.py` dari venv.
2. Tambah produk baru "Sirup Stroberi" (kode P004, satuan botol, mu=25, harga=30000) lewat
   tab Produk di halaman Manajemen & Pengaturan, pakai `st.data_editor` (double-click → ketik
   → **Enter** per sel — Tab tidak commit nilai dengan andal di widget canvas ini, temuan
   teknis tersendiri, bukan bug aplikasi).
3. **Ringkasan Operasional**: total "Perkiraan Penjualan" naik dari 1.637 → **1.812** — delta
   persis +175, sama persis dengan total forecast P004 (25 botol/hari × 7 hari = 175) yang
   divalidasi independen di halaman Perkiraan Penjualan. Ini bukti pendukung kuat perhitungan
   `core/inventory.py`/`views/overview.py` bekerja benar, bukan cuma "tidak crash".
4. **Perkiraan Penjualan**: dropdown "Pilih produk" menampilkan 4 opsi termasuk "Sirup
   Stroberi" (produk baru) — konfirmasi `views/forecasting.py` fix berhasil.
5. Pilih "Sirup Stroberi" di dropdown: KPI card tampil "175 botol" total / "25 botol"
   rata-rata per hari, dan **grafik berhasil dirender** tanpa crash — garis perkiraan flat di
   angka 25, konsisten dengan smoke test Python di atas. Ini mengonfirmasi bug tak terduga #2
   (`charts.py` IndexError) sudah teratasi.
6. Produk lama (Selai Stroberi, 486 jar) tetap tampil normal tanpa regresi.
7. Server Streamlit dimatikan bersih (`taskkill /F /PID <pid>`).
8. Produk uji P004 dihapus dari database (`store.save_produk()` dengan P004 difilter keluar),
   dikonfirmasi `get_produk_dict()` kembali hanya `['P001', 'P002', 'P003']`.

## Yang SUDAH diverifikasi

- Ketiga titik kegagalan resmi di brief: tidak lagi crash, dan perhitungan produk baru ikut
  masuk ke Ringkasan Operasional (dibuktikan lewat delta angka yang cocok, bukan cuma
  "tidak error").
- Produk baru muncul di dropdown Perkiraan Penjualan dan bisa di-forecast tanpa crash.
- Chart untuk produk tanpa riwayat sama sekali berhasil dirender (bug tak terduga #2 teratasi).
- `pid_utama` dinamis tidak crash saat produk dengan mu tertinggi dihapus, berpindah ke
  produk berikutnya dengan benar.
- Tidak ada regresi terlihat pada 3 produk lama (P001–P003) di kedua halaman yang diuji.

## Yang TIDAK/BELUM diverifikasi (batasan pengujian ini, disebutkan apa adanya)

- Horizon 14/30 hari untuk produk baru (tanpa model) tidak diuji langsung di UI kali ini —
  perbaikan `horizon` vs `HORIZON` (titik kegagalan resmi #3) hanya diverifikasi lewat
  pembacaan kode dan logika, belum lewat klik horizon 14/30 hari di dropdown untuk produk
  baru secara spesifik. Perilaku untuk produk LAMA (P001–P003) di horizon 14/30 tidak berubah
  oleh perbaikan ini (variabel `horizon` sudah dipakai benar di jalur model-tersedia
  sebelumnya) sehingga risiko regresi di sana rendah, tapi jalur "model None" untuk produk
  baru di horizon 14/30 secara spesifik belum diklik manual.
- Halaman Manajemen & Pengaturan (tab Bahan Baku/BOM) tidak diuji ulang di sesi ini — di luar
  scope T-4 (T-4 fokus ke daftar produk, bukan bahan baku/BOM yang sudah lebih dulu baca dari
  DB dengan benar sebelum sesi ini).
- Skenario "database benar-benar korup/permission error" (jalur fallback + `logger.warning`
  di `get_produk_dict()`) tidak disimulasikan — perilakunya diverifikasi lewat pembacaan kode,
  bukan lewat pemicuan error sungguhan.
- Halaman Stok & Pembelian tidak diperiksa ulang screenshot-nya di sesi ini (perubahan
  `core/inventory.py` memengaruhi halaman ini secara tidak langsung lewat
  `material_demand_7d()`, tapi angka totalnya sudah tervalidasi lewat delta di Ringkasan
  Operasional sebagai bukti tidak langsung).

## Kesimpulan

T-4 (3 titik kegagalan resmi) dan 2 bug tak terduga yang ditemukan selama pengujian, plus
hardcode `pid_utama` di luar 3 titik resmi (instruksi terpisah, sekelas bug: asumsi statis
soal produk yang seharusnya dinamis dari database), sudah diperbaiki dan diverifikasi lewat
kombinasi smoke test Python + pengujian UI browser end-to-end. Batasan pengujian tercantum di
atas apa adanya.
