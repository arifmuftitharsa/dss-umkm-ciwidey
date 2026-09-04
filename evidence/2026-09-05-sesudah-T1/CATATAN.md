# Bukti "Sesudah Perbaikan T-1" — Titik Reset Operasional

**Tanggal pengujian:** 5 September 2026
**Commit sebelum perubahan:** `6a05219` (T-7b: penyelarasan tanggal cuaca)
**Berkas diubah:** `app/data/store.py`, `app/data/record_sales.py`, `app/core/forecasting.py`,
`app/views/pengaturan.py`
**Status:** SESUDAH T-1 diperbaiki (Opsi B: reset baseline ke tanggal mulai pemakaian nyata).
**Ini pekerjaan terbesar sejauh ini** — pengujian dua tahap: smoke test Python langsung, lalu
pengujian UI penuh via browser (yang menemukan satu bug baru, diperbaiki di tengah jalan).

---

## Ringkasan Delapan Prinsip

| Prinsip | Relevan? | Catatan |
|---|---|---|
| C4 Model | Sebagian | Keputusan ini level arsitektur (Container: titik reset lintas 4 file) — didiskusikan sebagai rencana tertulis sebelum kode, tapi tak ada diagram formal ditulis di sesi ini |
| CI/CD | Tidak | Pengujian manual, bukan pipeline otomatis |
| Testing berbasis risiko | **Ya** | T-1 menyentuh persis rantai risiko tertinggi (`record_sales.py`→CSV→`forecasting.py` lag/rolling) — pengujian UI penuh (bukan cuma smoke test) dilakukan karena skala risikonya |
| Audit keamanan | Tidak | Belum ada deploy/tag rilis |
| docs/ vs notes/ | **Ya** | Evidence ini masuk `evidence/`, konsisten pola sebelumnya |
| Fail-fast | **Ya** | Form terkunci total sebelum reset diaktifkan (bukan diam-diam menerima input tanpa dasar); pesan jelas di tiap kondisi (terkunci, sudah tercatat hari ini, jeda tanggal) |
| Dependency hygiene | **Ya** | `_reset_cache()` duplikat dihapus, diganti pemanggilan fungsi yang sudah ada (DRY) |
| Version control rapi | **Ya** | Satu commit logis mencakup 4 file + evidence, pesan menjelaskan opsi yang dipilih dan hasil verifikasi |

---

## Keputusan Desain (ringkasan — detail lengkap di diskusi sebelum eksekusi)

**Opsi B dipilih**: reset baseline ke tanggal mulai pemakaian nyata, BUKAN Opsi A (isi otomatis
gap 247 hari dengan nilai model — ditolak karena risiko autoregressive drift dan CSV
tercampur data karangan) dan BUKAN "Opsi C naif" (longgarkan validasi tanpa reset — ditolak
eksplisit karena `lag_7`/`lag_14` akan diam-diam menunjuk ke data sintetis lama tanpa error).

**Titik reset disimpan di SQLite** (tabel baru `pengaturan_sistem`, key-value), konsisten pola
tabel lain di `store.py`. Diaktifkan lewat aksi eksplisit dua langkah (checkbox konfirmasi +
tombol) — bukan otomatis, sesuai fail-fast: pengguna sadar betul kapan garis batas antara data
training sintetis dan data operasional asli dilewati.

**`core/forecasting.py` direvisi dari rencana awal** — awalnya diperkirakan "tak berubah",
ternyata perlu filter riwayat ke pasca-reset supaya `series_hist` yang dikirim ke
`build_feature_row()` (fitur lag/rolling posisional) tak lagi bercampur data sintetis lama.
Revisi ini dilaporkan ke pengguna sebelum eksekusi, sesuai instruksi "jangan diam-diam ubah
rencana".

Fungsi dev-only `store.reset_tanggal_mulai_operasional()` ditambahkan supaya pengujian T-1
bisa diulang dari kondisi awal tanpa hapus database manual. **Sengaja tak ada tombol UI untuk
ini** — lihat verifikasi negatif di bawah.

---

## Tahap 1 — Smoke Test Python (sebelum UI)

Dijalankan langsung lewat interpreter, di luar browser, untuk verifikasi logika inti sebelum
uji UI:

| Skenario | Hasil |
|---|---|
| State awal | `mulai_operasional=None`, `next_valid_date('P001')=None` |
| Forecast sebelum reset (regresi check) | Total 486 jar — **identik evidence T-7b**, tak ada regresi |
| `record_one()` sebelum reset | Ditolak: "Data real belum diaktifkan. Tekan tombol..." |
| Reset diaktifkan (`2026-09-05`) | `next_valid_date('P001')` = `2026-09-05` (cold start) |
| Forecast cold-start (0 catatan real) | `[40,40,40,40,40,40,40]` — base demand P001, **tak crash** (edge case yang ditemukan saat desain, sudah ditangani) |
| `record_one()` tanggal salah (`2026-09-10`) | Ditolak: "Ada jeda 6 hari... tanggal yang harus dicatat berikutnya: 2026-09-05" — **mengarah ke titik reset, bukan tanggal sintetis lama** |
| `record_one()` tanggal benar (`2026-09-05`, qty 55) | Sukses, `next_valid_date` maju ke `2026-09-06` |
| Forecast setelah 1 catatan real | `[59,41,41,41,41,43,71]` — pola berubah total dari cold-start flat, bukti lag pakai data real (55), bukan data sintetis Desember 2025 |
| `store.reset_tanggal_mulai_operasional()` (dev-only) | Bekerja, kembali ke `None` |

Efek samping smoke test (baris CSV test, state DB) **dibersihkan** sebelum lanjut ke pengujian
UI, supaya kondisi awal UI-testing bersih.

---

## Tahap 2 — Pengujian UI Penuh (Browser)

### Langkah 2 — Verifikasi visual + fungsional kondisi terkunci

Warning kuning tampil ("Sistem masih memakai data latihan..."), checkbox belum tercentang,
tombol "🚀 Mulai Pakai Data Real Hari Ini" tampak pudar (disabled).

**Verifikasi fungsional (bukan cuma visual):** tombol diklik SEBELUM checkbox dicentang —
state database diperiksa langsung sesudahnya, **tetap `None`** — konfirmasi `disabled=not
konfirmasi` benar bekerja, bukan cuma tampilan.

### Langkah 3 — Aktivasi

Checkbox dicentang (via klik koordinat visual — `form_input` injeksi DOM langsung terbukti
**tidak** sinkron ke state React Streamlit, pola yang sama persis ditemukan di sesi T-1
4 September; klik koordinat asli yang berhasil). Tombol berubah dari abu-abu jadi **hijau
solid** begitu checkbox aktif — kontras visual jelas. Diklik, form biasa muncul dengan tanggal
default **`2026/09/05`** (hari ini sungguhan) — bukan lagi terkunci Januari 2026.

### Langkah 4-5 — Submit data uji + verifikasi tersimpan

Diisi qty **1** (jelas data uji, bukan angka realistis, sesuai instruksi). Submit pertama kali
memicu **bug baru** (lihat bagian terpisah di bawah) — setelah diperbaiki dan server di-restart,
data submit pertama terverifikasi benar tersimpan di CSV:

```
2026-09-05,P001,Selai Stroberi,1,1,0,---,0.0
```

Tanggal `2026-09-05` — **bukti langsung bug `nxt`/`tgl` yang diperbaiki di kode benar bekerja
di UI sungguhan**, bukan cuma smoke test.

### Bug Baru Ditemukan Di Tengah Pengujian — `StreamlitInvalidMinMaxError`

Setelah submit pertama sukses dan halaman rerun, muncul crash:

```
streamlit.errors.StreamlitInvalidMinMaxError: The min_value, set to 2026-09-06,
cannot be greater than the max_value, set to 2026-09-05.
```

**Akar masalah:** begitu 1 entri tercatat untuk hari ini, `next_valid_date()` otomatis maju ke
besok (`2026-09-06`) — tapi `max_value` widget dihitung dari jam sistem sungguhan yang **masih
hari ini** (`2026-09-05`, waktu asli belum lewat tengah malam). `min_value` (besok) > `max_value`
(hari ini) — Streamlit menolak konfigurasi widget itu sendiri.

**Analisis multi-produk (diminta eksplisit sebelum perbaikan):** dikonfirmasi lewat pengujian
langsung bahwa `next_valid_date()` **per produk**, bukan global:

```
P001 (sudah dicatat hari ini): next_valid_date = 2026-09-06
P002 (belum dicatat):          next_valid_date = 2026-09-05
P003 (belum dicatat):          next_valid_date = 2026-09-05
```

Mencatat P001 **tidak** mengunci P002/P003 — desain sudah benar sejak awal, bukan bug
tambahan. Bug crash murni soal produk yang sedang dipilih di dropdown, bukan kondisi global.

**Perbaikan:** fungsi baru `record_sales.sudah_tercatat_hari_ini(product_id) -> bool` (publik,
pure function, ditaruh di `record_sales.py` — dipertimbangkan SOLID: dipanggil lintas modul
dari `views/`, jadi lebih tepat sebagai fungsi domain yang testable terpisah dari Streamlit,
bukan inline di view). `views/pengaturan.py` dicabangkan: kalau `True`, tampilkan pesan sukses
+ ringkasan catatan terakhir, TIDAK mencoba render `date_input` sama sekali.

**Verifikasi ulang setelah perbaikan (memerlukan restart proses penuh — Streamlit tak
me-reimport modul Python yang sudah di-cache meski file di disk berubah, pelajaran yang sama
dari sesi-sesi sebelumnya):**

- P001: pesan hijau *"✓ Sudah tercatat untuk hari ini: Selai Stroberi, 1 unit (2026-09-05).
  Kembali lagi besok untuk mencatat penjualan berikutnya."* — tak crash.
- P002 (dipilih via dropdown): form biasa tetap terbuka, tanggal `2026/09/05` — **konfirmasi
  visual langsung isolasi per-produk**, bukan cuma dari analisis kode.

### Langkah 6 — Forecast mencerminkan data baru

Halaman Ringkasan Operasional: "Perkiraan Penjualan" berubah dari **1.637** (sebelum reset)
menjadi **1.011** lalu **346 jar** (di halaman Perkiraan Penjualan, P001 spesifik) — jauh
berbeda dari baseline 486 jar era T-7b.

**Temuan tak terduga yang menguatkan (bukan direncanakan, ditemukan saat verifikasi):** sumbu
tanggal grafik forecast sekarang **`Sep 5 – Sep 12 2026`** — tanggal kalender sungguhan,
BUKAN lagi `Oct 2025 – Jan 2026` seperti di seluruh evidence sebelumnya (T-2, T-7b). Ini bukti
visual bahwa T-1 dan T-7b sekarang bekerja **bersama secara otomatis**: begitu `last_date`
jadi tanggal real (bukan Desember 2025), `weather.future_exogenous()` menghitung
`offset_days` positif kecil (besok), otomatis memicu cabang **live-API** T-7b (bukan cabang
klimatologi masa lalu) — persis desain Open/Closed yang direncanakan sebelum T-1 dikerjakan:
T-7b tak perlu disentuh ulang sama sekali.

### Langkah 7 — Verifikasi Negatif: fungsi dev-only tak bocor ke UI

Pencarian teks "reset"/"kembalikan" di halaman UI: nihil. Diperkuat dengan **analisis statis
kode** (lebih pasti daripada scan visual, yang bisa terlewat elemen tersembunyi/expander):

```
grep -rn "reset_tanggal_mulai_operasional" — hanya 2 kemunculan:
  data/store.py:216  (definisi fungsi)
  data/store.py:225  (contoh perintah di DOCSTRING, bukan pemanggilan)
```

**Nol pemanggilan dari `views/` atau file manapun lain.** Tak ada jalur dari UI menuju fungsi
ini sama sekali.

### Langkah 8-9 — Pembersihan

Server dimatikan bersih (`taskkill /F`) dua kali (sekali sebelum perbaikan bug crash untuk
restart memuat kode baru, sekali di akhir pengujian). Efek samping dibersihkan:
- `historis_penjualan.csv`: baris `2026-09-05,P001,...,1,...` di-revert via `git checkout --`.
- Tabel `pengaturan_sistem`: dikosongkan via `store.reset_tanggal_mulai_operasional()`
  (fungsi dev-only yang baru saja diverifikasi tak bocor ke UI produksi).

Kondisi akhir: identik kondisi sebelum pengujian dimulai — sistem siap didemokan dari titik
"belum pernah dipakai" yang sesungguhnya, bukan "sudah pernah dites developer".

---

## Kesimpulan

**T-1 selesai, diverifikasi lewat dua lapis pengujian** (smoke test logika inti + UI penuh
via browser sungguhan) — bukan cuma baca kode. Satu bug tak terduga ditemukan **di tengah
pengujian UI** (min>max pada widget tanggal), dianalisis akar masalahnya (termasuk verifikasi
eksplisit bahwa ini bukan soal multi-produk yang lebih besar), diperbaiki, dan **diuji ulang
dari nol** — bukan diasumsikan benar setelah ditambal.

**Blocker demo mutlak** yang tercatat sejak 4 September (pengguna tak pernah bisa mencatat
penjualan sama sekali) **sekarang selesai**: form terbuka dengan tanggal kalender sungguhan,
per produk independen, dengan pengaman eksplisit di setiap transisi (checkbox konfirmasi,
pesan jelas saat terkunci/sudah tercatat/jeda tanggal) — tak ada jalur diam-diam.

**Yang belum diuji, perlu diketahui untuk pekerjaan berikutnya:** pengujian ini hanya
mencakup skenario satu hari pemakaian (hari ini). Belum diuji: mencatat berturut-turut
beberapa hari nyata (butuh menunggu hari kalender berganti sungguhan, tak bisa disimulasikan
dalam satu sesi), dan belum diuji interaksi titik reset dengan tab "Koreksi catatan manual"
/`update_qty`/`delete_last` (fungsi-fungsi itu masih pakai `BASE_END` lama, bukan
`mulai_operasional` baru — dicatat sebagai observasi di sesi analisis awal, sengaja tak
disentuh karena di luar scope yang disetujui, tapi perlu diperiksa lagi begitu ada beberapa
hari data real terkumpul).
