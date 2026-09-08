# Evidence — Label Sumbu-X "Tanggal", Rangeslider, Investigasi Kotak Putih

Tanggal: 8 September 2026

## Ringkasan 3 perbaikan (components/charts.py, forecast_chart())

1. **xaxis_title="Tanggal"** — sebelumnya cuma yaxis_title ("Unit (jar)"/dst) ada, sumbu-x
   tanggal tak berlabel. Ditambah lewat `fig.update_xaxes(..., title="Tanggal")`.
2. **inventory_bar()** — dicek, TIDAK perlu tambahan: sudah punya
   `xaxis_title="Jumlah (satuan masing-masing)"`, sumbu-y kategori nama bahan baku
   self-explanatory (tak butuh label).
3. **Rangeslider** — `rangeslider=dict(visible=True, thickness=.08)` di xaxis
   forecast_chart(). Height dinaikkan 380→460 supaya area plot utama tak tergencet
   rangeslider. `thickness=.08` (bukan default .15) supaya jejak vertikal tambahan
   seminim mungkin, terutama relevan di mobile.

## Investigasi kotak putih kursor

Render ulang chart, screenshot BERSIH tanpa mouse di atas area grafik (Ringkasan
Operasional, area sekitar 16/11) — TIDAK ADA kotak putih apa pun terlihat, chart bersih.

**Kesimpulan: BUKAN bug rendering Plotly/CSS.** Artefak di screenshot Arif sebelumnya
adalah kursor mouse atau elemen tool screenshot, tak terkait kode aplikasi sama sekali.

## Verifikasi DOM langsung

```js
forecast_chart: xaxis.title.text = "Tanggal", height = 460
rangeslider = {visible: true, thickness: 0.08, ...}
fixedrangeX = false   (drag-select zoom tetap aktif)
fixedrangeY = true    (skala unit tetap terkunci)
```

## Uji fungsi — drag-select zoom vs rangeslider (Perkiraan Penjualan)

- Drag-select pada area plot utama: tick sumbu-x berubah dari ~2 mingguan (05/10, 19/10,
  ...) jadi harian (05/10, 12/10, 19/10, ... 23/11) — zoom bekerja normal, TIDAK terganggu
  rangeslider baru.
- Drag pada rangeslider: `xaxis.range` berubah (dari full range jadi range yang
  dipersempit sesuai posisi drag) — dikonfirmasi via `gd.layout.xaxis.range` sebelum/
  sesudah drag, nilainya berbeda. Rangeslider dan drag-select zoom berdampingan, tidak
  saling mengganggu.

## Uji responsif

| Ukuran | Hasil |
|---|---|
| Mobile (375×812) | Label "Tanggal" muncul jelas. Rangeslider tipis, proporsional — tinggi chart 460px dari 812px viewport (56,7%), naik dari sebelumnya (~46,8%) karena rangeslider, tapi visual TIDAK mendominasi layar, konten "Yang Perlu Dilakukan" & "Kondisi Stok" tetap terlihat wajar saat scroll. Tak ada overlap/layout rusak. |
| Tablet (768×1024) | Label + rangeslider rapi, proporsional, tak ada masalah. |

## Cek regresi

- **Stok & Pembelian**: normal, `inventory_bar()` (tak diubah) tampil sama seperti
  sebelumnya — bar warna, marker ROP/EOQ, margin, semua utuh.
- **Manajemen & Pengaturan**: normal — halaman ini tak memakai `charts.py` sama sekali,
  tak ada dampak. Tab Catat Penjualan TIDAK dibuka sesi ini (tak relevan dgn perubahan
  chart), jadi tak ada risiko terhadap data historis_penjualan.csv.

## Kesimpulan

Ketiga perbaikan (label sumbu-x, rangeslider, investigasi kotak putih) selesai dan
diverifikasi via DOM + uji fungsi nyata (drag-select zoom, drag rangeslider), bukan cuma
visual. Kotak putih dikonfirmasi BUKAN bug — artefak kursor/tool screenshot. Responsif
mobile & tablet wajar, tak ada regresi di halaman lain. Server dimatikan bersih.
