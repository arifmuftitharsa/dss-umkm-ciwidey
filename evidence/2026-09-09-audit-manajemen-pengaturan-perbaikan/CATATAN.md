# Evidence — Perbaikan 2 Temuan Audit Manajemen & Pengaturan (halaman 4/4, TERAKHIR)

Tanggal: 9 September 2026

## Ringkasan 2 perbaikan

1. **Temuan 1** — ISO mentah (`strftime("%Y-%m-%d")`) diganti `ui.tanggal_id()` di
   DUA lokasi: [`data/weather.py`](../../app/data/weather.py) (tabel referensi hari
   libur, Tab 5) dan [`data/record_sales.py`](../../app/data/record_sales.py)
   `last_records()` (tabel "Riwayat penjualan", Tab 4). `manual_records()` (dropdown
   koreksi/hapus, alur T-1 sensitif) sengaja TIDAK disentuh — di luar cakupan.
2. **Temuan 2 (PRIORITAS)** — guard `if not prod_map:` ditambahkan di
   [`views/pengaturan.py`](../../app/views/pengaturan.py) Tab 4, SEBELUM semua
   pemakaian `pid_sel`. Pola crash sama seperti T-4 asli, audit#2 (halaman 1), dan
   audit#2 (halaman 3) — kali ini produk kosong di halaman Manajemen itu sendiri.

## Temuan 2 — bukti konkret SEBELUM vs SESUDAH

**Analisis titik crash** — semua fungsi pemakai `pid_sel` ditelusuri
(`sudah_tercatat_hari_ini` → `next_valid_date` → `last_date_of`, `manual_records`,
`last_records`, dan akses langsung `prod_map[pid_sel]['nama']`). Titik crash paling
pasti: `prod_map[pid_sel]['nama']` — dict-lookup langsung tanpa validasi, dengan
`pid_sel=None` (hasil `st.selectbox("Produk", [])` saat `prod_map={}`).

**SEBELUM** (mekanisme crash, dibuktikan lewat reproduksi langsung):
```
$ python -c "
prod_map = {}  # simulasi semua produk dihapus
pid_sel = None  # st.selectbox('Produk', []) kembalikan None
print(prod_map[pid_sel]['nama'])
"
KeyError: None
```
Persis dugaan analisis — `KeyError: None` di titik akses dict tanpa guard.

**SESUDAH** (dibuktikan lewat aplikasi sungguhan, BUKAN cuma baca kode):
Dibuat script test terpisah (`app/_test_produk_kosong_TEMP.py`, HANYA sementara,
sudah dihapus) yang **monkeypatch `store.get_produk_dict()` → `{}`** di memori
proses test — TIDAK PERNAH menulis/menghapus data production. Dijalankan sebagai
server Streamlit terpisah (port 8502, entri `.claude/launch.json` sementara, sudah
dikembalikan).

Hasil: **TIDAK CRASH**. Tab "Catat Penjualan" menampilkan:
- Judul "Catat Penjualan Harian" + subteks tetap normal
- Pesan `ui.action("Belum ada produk terdaftar", "Tambahkan produk dulu di tab
  Produk supaya penjualan bisa dicatat.", "info")` — styling konsisten dgn guard
  produk kosong `overview.py` (border-left biru info)
- Tidak ada traceback Python di layar, console browser 0 error

Diuji juga di mobile (375px, `get_page_text` + `read_console_messages` karena
Browser pane sedang hidden di sisi user — tetap valid, bukti dari DOM/console
sungguhan bukan asumsi): teks sama persis muncul, 0 error console.

**Tab 5 (Window Libur) tetap render normal** meski guard baru ada di Tab 4 (produk
kosong) — dicek langsung di server test yang sama, tabel window libur & referensi
tampil sempurna. Ini membuktikan guard TIDAK pakai `return` yang akan membatalkan
render tab-tab setelahnya dalam fungsi `render()` yang sama — sesuai analisis
struktur Streamlit `st.tabs()` (semua tab body jalan dalam satu run function).

## Verifikasi Temuan 1 (aplikasi real, bukan test, server production port 8501)

- Tab 4, tabel "Riwayat penjualan": kolom Tanggal tampil "Rabu, 31 Des",
  "Selasa, 30 Des", dst — Bahasa Indonesia, bukan ISO `2025-12-31`.
- Tab 5, tabel "Daftar hari libur & window efektif": baris "Rabu, 01 Jan",
  "Senin, 27 Jan", dst — konsisten format sama.

## Verifikasi kasus NORMAL Tab 4 (produk ada) — tak ada regresi

Server production (port 8501, data asli, 3 produk P001-P003): Tab 4 dibuka,
dropdown Produk terisi normal ("Selai Stroberi" dst), kartu info "Sistem masih
memakai data latihan" + checkbox + tombol "Mulai Pakai Data Real Hari Ini" tampil
persis seperti sebelum perbaikan (alur T-1 belum diaktifkan di data ini — belum
diklik apa pun, sesuai protokol data-safety). Tabel Riwayat penjualan tampil normal
dengan format tanggal baru. Tidak ada perubahan perilaku pada alur yang sudah benar.

## Protokol keamanan data — Tab 4 (Catat Penjualan)

Checkbox konfirmasi TIDAK PERNAH dicentang, tombol aktivasi/submit TIDAK PERNAH
diklik selama observasi maupun pengujian.

```
$ git status --porcelain -- app/data/historis_penjualan.csv
(kosong)
$ git diff app/data/historis_penjualan.csv
(kosong)
```
Sebelum DAN sesudah seluruh pengujian (termasuk sesi test produk kosong terpisah)
— nol perubahan data production.

## Cek regresi halaman lain

Ringkasan Operasional: grafik perkiraan penjualan, kartu rekomendasi tampil normal,
tak ada elemen yang menyentuh `weather.py`/`record_sales.py`/`pengaturan.py` secara
langsung selain lewat data yang sudah diverifikasi utuh.

## Verifikasi tak ada sisa artefak simulasi

```
$ git status --porcelain
 M app/data/record_sales.py
 M app/data/weather.py
 M app/views/pengaturan.py
?? notes/
$ ls app/_test_produk_kosong_TEMP.py
ls: cannot access 'app/_test_produk_kosong_TEMP.py': No such file or directory
```
`.claude/launch.json` (gitignored) dikembalikan ke entri tunggal semula.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Desktop (1280px) | Tab 4 & 5 production normal, format tanggal Indonesia konsisten. |
| Mobile (375px) | Guard produk kosong tampil rapi via DOM/console check, 0 error. |

## Kesimpulan

Kedua temuan diperbaiki dan diverifikasi dengan bukti konkret. Temuan 2 dibuktikan
LENGKAP: mekanisme crash sebelum (`KeyError: None` nyata via reproduksi langsung)
DAN aplikasi sungguhan sesudah (pesan ramah tampil, tak crash, Tab 5 tak terdampak,
di desktop maupun mobile) — bukan asumsi dari baca kode saja. Tak ada regresi pada
kasus normal maupun halaman lain. DB/CSV production terverifikasi utuh. Server
dimatikan bersih, semua jejak test dihapus.

**Ini penutup audit menyeluruh 4 halaman aplikasi** (Ringkasan Operasional,
Perkiraan Penjualan, Stok & Pembelian, Manajemen & Pengaturan) — total 14 temuan
ditemukan & diperbaiki sepanjang seluruh audit.
