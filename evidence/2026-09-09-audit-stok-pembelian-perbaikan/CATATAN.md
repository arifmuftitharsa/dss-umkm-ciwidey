# Evidence — Perbaikan 4 Temuan Audit Stok & Pembelian

Tanggal: 9 September 2026

## Ringkasan 4 perbaikan (`app/views/inventory.py`)

1. **Temuan 2 (PRIORITAS TERTINGGI)** — `BAHAN_BAKU` statis (`config.py`) diganti
   `store.get_bahan_dict()` dinamis untuk render nama kolom expander "Lihat perkiraan
   pemakaian bahan baku...". Pola identik T-4 asli (produk), kali ini bahan baku.
2. **Temuan 1** — `ui.format_angka()` diterapkan di kartu "Daftar Belanja" (detail
   stok) DAN kolom "Stok sekarang" tabel HTML.
3. **Temuan 3** — `st.column_config.NumberColumn(format="%.1f")` diterapkan ke semua
   kolom tabel expander, memaksa 1 desimal seragam (sebelumnya trailing zero hilang
   tak konsisten per-sel).
4. **Temuan 4** — Subtext diisi utk section "Kondisi Semua Bahan Baku" ("Semua bahan
   baku dan levelnya saat ini") dan "Posisi Stok terhadap Batas Aman" ("Perbandingan
   visual stok vs batas aman").

## Temuan 2 — bukti konkret SEBELUM vs SESUDAH (paling detail)

**SEBELUM** (mekanisme crash, dibuktikan lewat kode langsung):
```
$ python -c "
BAHAN_BAKU = {'M01': ..., 'M02': ...}  # config statis, cuma M01-M06 bawaan
columns = ['M01', 'M02', 'M07']  # M07 = bahan baru via dashboard
[BAHAN_BAKU[c]['nama'] for c in columns]
"
KeyError: 'M07'
```
Ini PERSIS baris kode lama `mat_show.columns = [BAHAN_BAKU[c]["nama"] for c in
mat_show.columns]` — akan crash total kalau ada bahan baku dengan kode di luar
config statis (realistis: `material_demand_7d()` sudah ambil bahan dari DATABASE
dinamis via `_sumber_data()`, jadi kolom BISA berisi kode baru kapan saja).

**SESUDAH** (dibuktikan lewat aplikasi sungguhan, BUKAN cuma baca kode):
Dibuat script test terpisah (`app/_test_bahan_baru_TEMP.py`, HANYA sementara, sudah
dihapus) yang **monkeypatch `store.get_bahan_dict()`/`get_bom_dict()` untuk
menyisipkan bahan palsu "M07" ("Kayu Manis Bubuk (TEST)")** di memori proses test —
TIDAK PERNAH menulis ke database production. Dijalankan sebagai server Streamlit
terpisah, expander dibuka.

Hasil: **TIDAK CRASH**. Bahan "Kayu Manis Bubuk (TEST)" muncul BENAR di:
- Tabel HTML "Kondisi Semua Bahan Baku" (baris baru, status "Aman")
- Bar chart "Posisi Stok terhadap Batas Aman" (label "Kayu Manis Bubuk (TEST)", 500)
- Kolom expander "Lihat perkiraan pemakaian..." — kolom "Kayu Manis Bubuk (TEST)"
  dengan nilai "0.0" (BOM coef 0 utk semua produk, sesuai simulasi) — nama kolom
  render BENAR, bukan KeyError.

Diuji juga di mobile (375px) — expander dibuka via `st.expander` summary click,
scroll horizontal tabel (`.dvn-scroller`) sampai kolom "Kayu Manis Bubuk (TEST)"
terlihat — tetap benar, tak crash.

Console browser menunjukkan error `ERR_CONNECTION_REFUSED`/"Is Streamlit still
running?" — dikonfirmasi ini SISA reconnect WebSocket dari sesi server SEBELUMNYA
yang dimatikan (bukan exception dari `render()` — konten tampil sempurna tanpa
traceback Python di layar).

## Verifikasi Temuan 1 (aplikasi real, bukan test)

Screenshot: kartu "Stok sekarang **42 kg**" (bukan "42.0 kg"), tabel "Stok sekarang"
kolom: 42, 120, 85, 30, 60, 500 — semua bulat tanpa `.0` tak perlu, konsisten dgn
kolom lain di tabel yang sama.

## Verifikasi Temuan 3 (terlihat sekaligus di screenshot test M07 di atas)

Tabel expander sekarang: "79.6", "39.0", "11.0", "5.3", "0.0" — SEMUA sel 1 desimal
seragam, tak ada lagi campuran "3" vs "5.28" dalam kolom yang sama.

## Verifikasi Temuan 4

Subtext "Semua bahan baku dan levelnya saat ini" dan "Perbandingan visual stok vs
batas aman" muncul persis di bawah judul section masing-masing.

## Cek regresi

Ringkasan Operasional: "Stok tinggal 42 kg" (di kartu "Yang Perlu Dilakukan") tetap
bulat, tak terpengaruh (pakai `ui.format_angka()` yang sama, sudah benar dari sesi
audit sebelumnya). Perkiraan Penjualan: tak ada elemen terkait, tak disentuh.
Manajemen & Pengaturan: data produk (P001-P003) DAN bahan baku (M01-M06) utuh persis
seperti sebelum simulasi — konfirmasi DB production tak tersentuh.

## Verifikasi tak ada sisa artefak simulasi

```
$ git status
modified:   app/views/inventory.py
Untracked: notes/  (selalu dikecualikan, tak berubah)
```
`app/_test_bahan_baru_TEMP.py` sudah dihapus, `.claude/launch.json` (gitignored)
dikembalikan ke isi semula.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Kartu, tabel (scroll horizontal), chart, subtext semua rapi. |
| Tablet (768×1024) | Tabel muat 1 baris tanpa scroll, semua rapi. |

## Kesimpulan

Keempat temuan diperbaiki dan diverifikasi dengan bukti konkret. Temuan 2 (paling
kritis) dibuktikan LENGKAP: mekanisme crash sebelum (KeyError nyata) DAN aplikasi
sungguhan sesudah (bahan baru tampil benar, tak crash, di desktop maupun mobile) —
bukan asumsi dari baca kode saja. Tak ada regresi, DB production terverifikasi utuh.
Server dimatikan bersih.
