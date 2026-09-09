# Evidence — Perhalus Kotak Peringatan Cuaca Halaman Perkiraan Penjualan

Tanggal: 9 September 2026

## Perubahan

[`views/forecasting.py`](../../app/views/forecasting.py) — kotak peringatan yang
muncul saat horizon > `MAX_FORECAST_DAYS` (16 hari, jadi hanya tampil untuk pilihan
30 hari) diganti dari `st.warning()` (kuning mencolok) jadi `ui.action(..., "info")`
(border-kiri navy) — pendekatan sama seperti perbaikan kotak Catat Penjualan
sebelumnya (commit `0da1e43`). Kalimat pertama teks asli jadi judul card (verbatim,
titik dibuang krn jadi baris judul terpisah), sisa kalimat jadi detail (persis kata
demi kata, tak diringkas/diubah). Kondisi `if horizon > MAX_FORECAST_DAYS:` tak
disentuh sama sekali.

## Pengujian

**1-2. Horizon 30 hari, gaya visual + teks lengkap** (desktop 1280px, produk
Selai Stroberi): kotak peringatan tampil dengan border-kiri navy (komponen
`ui.action` yang sama dipakai di seluruh app), bukan lagi kuning `st.warning`.
Teks diverifikasi via DOM (`get_page_text`) persis sama:
> Prakiraan cuaca hanya tersedia sampai hari ke-16
> Hari ke-17 sampai ke-30 memakai rata-rata curah hujan bulanan Ciwidey, sehingga
> cocok untuk perencanaan kasar, bukan keputusan harian.

Tidak ada kata yang hilang, diringkas, atau diparafrase dari teks asli.

**3. Horizon 7 & 14 hari — peringatan TIDAK muncul**: dicek `get_page_text` untuk
kedua pilihan, teks "Prakiraan cuaca hanya tersedia..." tidak ada di DOM sama
sekali pada horizon 7 hari (baseline default halaman) maupun 14 hari — kondisi
`horizon > MAX_FORECAST_DAYS` (16) tetap berfungsi sama persis seperti sebelum
perbaikan.

**4. Cek regresi halaman lain**: Ringkasan Operasional, Stok & Pembelian, Manajemen
& Pengaturan (Tab Produk) dibuka via `get_page_text` — semua elemen tampil normal,
tak ada yang menyentuh `forecasting.py` selain sudah diverifikasi di atas.

**5. Uji responsif** — horizon 30 hari dipilih via `form_input`/klik opsi filtered
listbox (native click sempat gagal krn Browser pane sedang hidden di sisi user;
`javascript_tool` dipakai untuk klik elemen listbox DOM langsung — tetap interaksi
UI sungguhan, bukan bypass logika app):

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Kotak navy tampil, teks lengkap sama persis, tak crash. |
| Tablet (768×1024) | Sama seperti mobile — kotak tampil rapi, teks utuh. |

Console browser menunjukkan banyak error `ERR_CONNECTION_REFUSED`/
"Is Streamlit still running?" — dikonfirmasi ini SISA reconnect WebSocket dari
server test sesi SEBELUMNYA (port 8502, sudah dimatikan bersih di akhir sesi lalu),
bukan exception dari `render()` halaman ini — konten tampil sempurna tanpa
traceback Python di layar pada seluruh pengujian di atas.

**6. Server dimatikan bersih** setelah pengujian selesai.

## Verifikasi tak ada sisa artefak & data production utuh

```
$ git status --porcelain
 M app/views/forecasting.py
?? notes/
$ git diff app/data/historis_penjualan.csv
(kosong)
```
Tidak ada script test sementara dibuat untuk perbaikan ini (perubahan murni visual,
tak perlu monkeypatch DB) — cukup diuji langsung lewat server production.

## Kesimpulan

Kotak peringatan cuaca berhasil diperhalus secara visual (kuning → navy `ui.action`
info) tanpa mengubah SATU KATA PUN dari isi teks maupun kapan kondisinya muncul.
Tak ada regresi pada horizon lain, halaman lain, maupun tampilan mobile/tablet.
Data production tak tersentuh, server dimatikan bersih.
