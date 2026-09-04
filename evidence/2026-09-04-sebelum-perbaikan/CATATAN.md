# Bukti "Sebelum Perbaikan" — Pengujian Aplikasi DSS UMKM

**Tanggal pengujian:** 4 September 2026
**Commit yang diuji:** `8ddd1c0` (Perbaiki T-8: lengkapi app/requirements.txt)
**Status:** SEBELUM T-1 dan T-2 disentuh sama sekali — baseline pembanding untuk laporan.
**Metode:** `streamlit run app.py` di venv baru, diakses lewat Browser pane (Claude Code), dibaca
via accessibility-tree (`read_page`/`get_page_text`) dan screenshot inline — bukan file PNG
tersimpan (lihat catatan keterbatasan di bagian akhir).

---

## Ringkasan Delapan Prinsip (per instruksi CLAUDE.md, sebelum eksekusi)

| Prinsip | Relevan? | Catatan |
|---|---|---|
| C4 Model | Tidak | Tak ada dokumentasi arsitektur ditulis di langkah ini |
| CI/CD | Tidak | Capture manual, bukan pipeline rilis |
| Testing berbasis risiko | **Ya** | Fokus pengujian tepat di T-1 (`record_sales.py`) dan T-2 (`forecasting.py`) — dua modul risiko tertinggi |
| Audit keamanan | Tidak | Belum ada deploy/tag rilis |
| docs/ vs notes/ | **Ya, perlu keputusan** | Lihat bagian penutup — bukti ini snapshot historis, tak murni cocok kategori `docs/` (stabil) atau `notes/` (kerja berjalan) |
| Fail-fast | **Ya** | Diterapkan: begitu instalasi/start gagal, berhenti & laporkan — dan begitu efek samping tak sengaja terjadi (lihat Temuan T-1), langsung dihentikan, dilaporkan, direvert sebelum lanjut |
| Dependency hygiene | Tidak | Tak ada dependency baru ditambah di langkah ini |
| Version control rapi | **Ya** | Tak commit dulu — folder ini menunggu keputusan sebelum masuk git |

---

## Langkah 1 — Instalasi

venv baru dibuat di `app/venv/`. Install dari `requirements.txt` commit `8ddd1c0` — **sukses,
exit code 0, tanpa konflik**.

**Temuan tambahan (bukan bagian instruksi, tapi wajib dilaporkan):** dua paket di-pin persis
(`xgboost==3.2.0`, `scikit-learn==1.8.0`) sesuai keputusan sebelumnya, resolve tepat sesuai pin.
Tapi paket lain yang cuma diberi floor longgar (`pandas>=2.0`, `numpy>=1.24`, `streamlit>=1.30`,
`plotly>=5.18`, `holidays>=0.101`) resolve ke versi jauh lebih baru dari yang didokumentasikan
Tabel 3.9 skripsi:

| Paket | Requirements.txt | Versi training (Tabel 3.9) | Versi ter-install |
|---|---|---|---|
| pandas | `>=2.0` | 2.3.3 | **3.0.5** (lompatan mayor) |
| numpy | `>=1.24` | 2.4.0 | 2.5.2 |
| streamlit | `>=1.30` | 1.30 | 1.63.0 |
| plotly | `>=5.18` | 6.8.0 | 7.0.0 |
| holidays | `>=0.101` | 0.101 | 0.103 |

Tak ada error yang muncul akibat ini di pengujian sesi ini, tapi `pandas 3.0` adalah lompatan
versi mayor dari versi training (2.3.3) — pola risiko sama seperti alasan yang dipakai untuk
pin `xgboost`/`scikit-learn`, belum diuji cross-version secara eksplisit di sini. Dicatat sebagai
temuan terpisah, bukan diputuskan sendiri untuk diubah.

## Langkah 2 — Menjalankan Aplikasi

`streamlit run app.py` **berhasil start tanpa error**. Log terminal lengkap (tak dipotong):

```
Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
2026-09-04 20:25:15.638 Uvicorn server started on :::8501
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.1.100:8501
External URL: http://140.213.190.29:8501
```

Tak ada traceback, tak ada import error. Ini mengonfirmasi perbaikan T-8 (requirements.txt)
sudah cukup untuk start — belum tentu cukup untuk semua alur (belum diuji retraining/`model/`).

## Langkah 3 — Empat Halaman

### 3.1 Ringkasan Operasional

Render sukses. Isi: kartu "Akurasi Perkiraan 92%", "Perkiraan Penjualan 1.704 unit",
"Bahan Perlu Dibeli 1", "Hari Libur Nasional: Ada". Grafik forecast Jus Stroberi Segar dengan
sumbu tanggal **Okt 2025 – Jan 2026**. Bagian "Kondisi Stok Bahan Baku" — 6 bahan, status
sesuai warna (Stroberi Segar merah/kritis, lainnya hijau/aman).

**🔴 Pelanggaran ditemukan:** kartu **"AKURASI PERKIRAAN: 92%"** tampil mencolok di halaman
paling depan yang dilihat pengguna. Ini melanggar langsung CLAUDE.md aturan #4 ("Jangan sebut
angka akurasi model ke pelaku UMKM di lapangan"). Bukan T-1/T-2 — temuan terpisah, sengaja tak
disentuh sesuai instruksi tugas ini (hanya capture, bukan perbaiki).

**Konfirmasi visual T-1:** grafik forecast berlabuh di Jan 2026, bukan sekitar tanggal
pengujian sebenarnya (4 Sept 2026) — bukti langsung bahwa forecast dihitung dari akhir data
historis (31 Des 2025), bukan dari kalender hari ini.

**Stabilitas lintas reload:** angka "Perkiraan Penjualan: 1.704" pada kartu ringkasan ini
**identik di tiga kali pemuatan halaman berturut-turut** (dikonfirmasi via `read_page`,
bukan tebakan visual). Berbeda dengan temuan T-2 di halaman Perkiraan Penjualan (lihat 3.2) —
kemungkinan karena kartu ini menjumlah/membulatkan lintas 3 produk sehingga variasi kecil per
produk saling menutupi, atau memakai jalur kode berbeda. Tidak diselidiki lebih lanjut karena
di luar cakupan tugas ini.

### 3.2 Perkiraan Penjualan

Render sukses. Kontrol: pilih produk (dropdown), horizon (dropdown 7/14/30).

**🔴 Pelanggaran ditemukan:** kartu **"AKURASI MODEL: 92.1%"** dengan keterangan "hasil uji
backtest H+7" — instance kedua pelanggaran akurasi, lebih eksplisit dari yang di halaman
Ringkasan Operasional.

**T-2 dikonfirmasi dengan bukti bersih (metode konsisten kedua sisi — dibaca via `read_page`,
bukan screenshot):**

| Percobaan | Produk | Horizon | Total 7 Hari | Rata-rata/Hari | Akurasi Model (label) |
|---|---|---|---|---|---|
| Reload #2 | P001 Selai Stroberi | 7 hari | **502 jar** | 71 jar | 92.1% |
| Reload #3 | P001 Selai Stroberi | 7 hari | **498 jar** | 71 jar | 92.1% |

Produk, tanggal, horizon sama persis — total forecast berubah (502 → 498). Ini bukti langsung
noise acak `core/forecasting.py` (T-2). Label "Akurasi Model 92.1%" **tidak ikut berubah** —
konsisten dengan T-3 (angka itu konstanta `mape_ref`, bukan dihitung ulang dari data).

Catatan metodologi: percobaan pertama (sebelum reload #2) sempat dibaca lewat screenshot visual
dan menunjukkan kejanggalan transkripsi (superscript render kecil rawan salah baca angka
mirip, mis. "83" terbaca "93"). Data itu **dibuang, tidak dipakai sebagai bukti** — hanya
perbandingan reload #2 vs #3 (keduanya dibaca via accessibility tree, metode identik dan
dapat dipercaya) yang dijadikan bukti resmi T-2 di atas.

### 3.3 Stok & Pembelian

Render sukses, **tanpa error, tanpa peringatan aneh**. Tak ada angka MAPE/akurasi ditampilkan
di halaman ini — sesuai desain yang benar (metrik teknis disembunyikan dari halaman
operasional, per catatan brief Bagian 3.3). Tabel "Kondisi Semua Bahan Baku" konsisten:
Stroberi Segar berstatus "Segera beli" (satu-satunya yang di bawah ROP), lima bahan lain
"Aman". Angka EOQ Stroberi (138 kg) konsisten dengan rekomendasi "beli ± 137 kg" di kartu
atasnya (selisih 1 kg = pembulatan tampilan, bukan bug).

Catatan: halaman ini menampilkan **status stok titik-waktu sekarang**, bukan simulasi
stockout 165 hari seperti Tabel 4.22 skripsi — jadi tampilan normal di sini tidak
bertentangan dengan temuan T-3/T-12 soal stockout 78% pada simulasi; keduanya mengukur hal
berbeda.

### 3.4 Manajemen & Pengaturan (5 tab)

Lima tab terkonfirmasi persis sesuai brief: Produk, Bahan Baku & Stok, Resep (BOM),
Catat Penjualan, Window Libur.

**Tab Produk:** menampilkan data dari `config.py`/database — harga P001 Rp15.000,
P002 Rp22.200, P003 Rp12.000. Ini **angka `config.py`, bukan angka skripsi**
(Rp35.000/85.000/15.000) — konfirmasi visual langsung dari T-11, terlihat di UI sungguhan
bukan cuma di kode.

**Tab Catat Penjualan — pengujian T-1, lihat detail penuh di bagian berikut.**

## Langkah 4 — Pengujian T-1 (Catat Penjualan)

Field "Tanggal penjualan" **tidak berupa date-picker bebas** — muncul pra-isi dengan
keterangan eksplisit: *"Mencatat untuk 2026-01-01 (hari berikutnya setelah data terakhir).
Pencatatan berurutan menjaga perkiraan tetap valid."*

**Percobaan mengisi `2026-09-04` (hari pengujian sebenarnya) lewat injeksi nilai form
langsung** — hasil: **nilai yang kuisi tidak tersimpan**. Widget kemungkinan besar dibangun
dengan rentang `min=max=tanggal_valid_berikutnya`, sehingga secara struktural tak
memungkinkan memasukkan tanggal di luar itu lewat alur pemakaian normal.

**Efek samping tak terduga (dilaporkan apa adanya, bukan disembunyikan):** karena field tetap
membawa nilai default `2026-01-01` saat tombol "Catat Penjualan" diklik, klik itu **berhasil
mencatat penjualan sungguhan**: baris baru `2026-01-01,P001,Selai Stroberi,0,0,1,H,0.0` masuk
ke `historis_penjualan.csv` (qty 0 karena field "Jumlah terjual" tak sempat diisi).

**Tindakan perbaikan segera (fail-fast, sesuai CLAUDE.md prinsip #6):**
1. Terdeteksi lewat `git status`/`git diff` pada repo kerja.
2. Direvert lewat `git checkout -- app/data/historis_penjualan.csv` — bersih, terverifikasi
   `git diff` kosong setelahnya.
3. Proses Streamlit lama dimatikan paksa (PID di-`taskkill`) karena cache in-memory
   (`core.forecasting._HIST`) sudah kadung memuat baris yang sudah dihapus dari disk — restart
   diperlukan agar proses baru membaca ulang file yang sudah bersih.
4. Streamlit dijalankan ulang, log terkonfirmasi bersih tanpa error.

**Kesimpulan pengujian T-1:** dikonfirmasi — kode `record_sales.py` yang mengunci tanggal
persis seperti dijelaskan brief. Tapi **UI normal tidak pernah menampilkan pesan errornya**
secara visual, karena widget tanggal sendiri sudah membatasi rentang sebelum submit sempat
terjadi — pengguna asli yang membuka aplikasi apa adanya tidak akan pernah melihat tanggal lain
sebagai pilihan, apalagi pesan gagal. Ini nuansa yang perlu masuk laporan: **T-1 bukan cuma
"pesan error yang membingungkan" — lebih parah, penggunanya bahkan tidak diberi jalan sama
sekali untuk mencoba tanggal lain.** Dan karena periode Jan 2026 sudah lewat dari kalender
sungguhan (sekarang Sept 2026), setiap kali dijalankan aplikasi akan terus menawarkan tanggal
"berikutnya setelah data terakhir" yang sama-sama sudah basi — pengguna terjebak permanen di
titik itu sampai kode diperbaiki (bukan cuma satu kali gagal, tapi seterusnya).

## Langkah 5 — Pengujian T-2 (Noise Acak)

Sudah dijabarkan di 3.2 — **dikonfirmasi dengan bukti bersih**: 502 jar → 498 jar untuk
produk/tanggal/horizon yang identik lintas dua reload berbeda, dibaca dengan metode konsisten
(accessibility tree). Label akurasi statis (92.1%, tak berubah) — sejalan dengan T-3.

## Langkah 6-7 — Bukti dan Keterbatasan

**Keterbatasan penting: tak ada file screenshot PNG tersimpan di folder ini.** Browser pane
yang dipakai untuk pengujian adalah preview sandbox internal Claude Code, bukan jendela OS
nyata — tak ada mekanisme dari sisi Claude untuk menuliskan hasil render itu jadi berkas
`.png` ke disk. Semua screenshot di atas ditampilkan inline di percakapan (bisa dilihat di
transkrip sesi), tapi tidak otomatis tersimpan sebagai file.

**Kalau butuh file PNG fisik untuk laporan, screenshot manual berikut yang disarankan** (bisa
dilakukan sendiri sambil `streamlit run app.py` aktif di `http://localhost:8501`, viewport
lebar ≥1440px agar layout tak terpotong):

1. `01-ringkasan-operasional.png` — halaman Ringkasan Operasional, termasuk kartu
   "Akurasi Perkiraan 92%" dan grafik forecast.
2. `02-perkiraan-penjualan-run-a.png` dan `02-perkiraan-penjualan-run-b.png` — halaman
   Perkiraan Penjualan untuk P001/7 hari, di-screenshot, lalu **reload halaman (F5)** dan
   screenshot lagi — untuk mereplikasi bukti T-2 (502 vs 498 jar) secara visual.
3. `03-stok-pembelian.png` — halaman Stok & Pembelian lengkap (kartu ringkasan + tabel
   kondisi bahan baku + grafik posisi stok).
4. `04-manajemen-tab-produk.png` — tab Produk di halaman Manajemen (bukti T-11).
5. `05-manajemen-tab-catat-penjualan.png` — tab Catat Penjualan, **sebelum klik apa pun**,
   memperlihatkan field tanggal terkunci dan keterangan "Mencatat untuk 2026-01-01 (hari
   berikutnya setelah data terakhir)" — ini bukti visual T-1 yang paling penting.

**Peringatan kalau screenshot manual dilakukan:** JANGAN klik tombol "Catat Penjualan" di
tab Catat Penjualan tanpa mengisi Jumlah Terjual dengan sengaja — klik itu akan menulis
baris baru sungguhan ke `historis_penjualan.csv` seperti yang terjadi di pengujian ini.

---

## Keputusan yang Perlu Diambil (bukan diputuskan sendiri di sini)

1. **Struktur folder:** `docs/bukti-sebelum-perbaikan/` cocok masuk kategori evidence/audit-trail
   — bukan `docs/` murni (dokumentasi stabil) atau `notes/` murni (catatan kerja berjalan). Perlu
   diputuskan: biarkan di sini, pindah ke folder `evidence/` terpisah, atau masuk `notes/` dengan
   sub-kategori snapshot?
2. **Commit atau tidak:** folder ini belum di-`git add`. Kalau di-commit, isinya jadi bagian
   riwayat repo publik (termasuk temuan pelanggaran akurasi yang belum diperbaiki) — pertimbangkan
   apakah itu diinginkan sebelum T-1/T-2 benar-benar diperbaiki, atau simpan lokal dulu sampai
   perbaikan selesai lalu commit sepasang (sebelum+sesudah) sekaligus.
3. **Temuan baru di luar cakupan tugas ini** yang perlu ditambahkan ke daftar T-1..T-18 di brief:
   - Kartu akurasi tampil di 2 halaman (Ringkasan Operasional, Perkiraan Penjualan) — pelanggaran
     aturan #4 CLAUDE.md, belum ada nomor T- untuk ini secara eksplisit.
   - `pandas>=2.0` resolve ke `3.0.5` (lompatan mayor), belum diuji kompatibilitasnya.
   - T-1 lebih parah dari deskripsi awal: pengguna tak pernah melihat pesan error sama sekali,
     karena widget membatasi pilihan sebelum submit.
