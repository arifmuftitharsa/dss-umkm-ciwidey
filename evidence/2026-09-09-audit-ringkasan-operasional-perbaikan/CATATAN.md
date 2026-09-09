# Evidence — Perbaikan 4 Temuan Audit Ringkasan Operasional

Tanggal: 9 September 2026

## Ringkasan 4 perbaikan

1. **Format angka bulat** — `ui.format_angka()` (fungsi baru, `ui.py`): tampilkan bulat
   (`42`) kalau memang bilangan bulat, TAPI tetap tampilkan 1 desimal kalau pecahan
   sungguhan (`42.5`). Diverifikasi kolom `stok` di `data/store.py` bertipe `REAL`
   (bisa legitimately pecahan) — bukan sekadar `int()`/potong yang akan menyembunyikan
   pecahan asli. Dipakai di kartu aksi (`overview.py`) dan label bar chart
   (`charts.py`, otomatis ikut dipakai juga di halaman Stok & Pembelian yang reuse
   `charts.inventory_bar()` — bonus konsistensi di luar scope temuan).
2. **Subtext section "Kondisi Stok Bahan Baku"** — diisi "Level stok saat ini
   dibanding batas aman", konsisten pola section lain yang selalu punya subtext.
3. **Guard produk kosong** (PRIORITAS TERTINGGI) — `overview.render()` sekarang cek
   `if not produk:` di awal, tampilkan kartu info "Belum ada produk terdaftar" +
   `return`, mencegah crash `ValueError` dari `max()` atas dict kosong.
4. **KPI "Bahan Perlu Dibeli" kondisional** — subtext jadi "Semua stok aman" saat
   `kritis=0` DAN `waspada=0`, bukan selalu "0 lainnya mulai menipis" yang terasa
   redundan berdampingan value "0".

## Temuan 3 — bukti konkret SEBELUM vs SESUDAH

**SEBELUM** (mekanisme crash, dibuktikan lewat kode langsung, bukan asumsi):
```
$ python -c "produk={}; max(produk, key=lambda pid: produk[pid]['mu'])"
ValueError: max() iterable argument is empty
```
Ini PERSIS baris kode `pid_utama = max(produk, key=lambda pid: produk[pid]["mu"])`
yang ada di `overview.py` sebelum perbaikan — akan crash total kalau `produk` kosong.

**SESUDAH** (dibuktikan lewat aplikasi sungguhan, BUKAN cuma baca kode):
Dibuat script test terpisah (`app/_test_empty_produk_TEMP.py`, HANYA sementara,
sudah dihapus) yang **monkeypatch `store.get_produk_dict()` supaya kembalikan `{}`
di memori proses test** — TIDAK PERNAH menulis ke database production sama sekali.
Dijalankan sebagai server Streamlit terpisah (port 8502→8501 karena port override
tak sengaja tanpa `--server.port`, dikonfirmasi cuma 1 server jalan, bukan konflik).

Hasil: halaman render sempurna, tampil kartu **"Belum ada produk terdaftar"** dengan
detail "Tambahkan produk dulu di halaman Manajemen & Pengaturan supaya perkiraan
penjualan dan kebutuhan bahan baku bisa dihitung." — **TIDAK ADA** traceback/
ValueError, dikonfirmasi juga console browser bersih (`No console logs` di level
error). Diuji di desktop, mobile (375px), tablet (768px) — pesan tampil rapi
(border navy konsisten `ui.action` level info) di ketiga ukuran, tak ada elemen
terpotong.

## Verifikasi format angka

Screenshot real app (bukan test): "Stok tinggal 42 kg" (kartu aksi kritis) — bukan
lagi "42.0 kg". Label bar chart "Kondisi Stok Bahan Baku": 500, 60, 30, 85, 120, 42
— semua bulat tanpa `.0`. Chart yang sama dipakai ulang di halaman Stok & Pembelian
(`inventory_bar()` shared) juga otomatis ikut bulat — bukti fungsi `format_angka()`
konsisten lintas pemanggil (DRY, satu sumber format).

## Verifikasi subtext section

Screenshot: "Kondisi Stok Bahan Baku — Level stok saat ini dibanding batas aman"
muncul persis di bawah judul section, gaya sama dengan section lain.

## Verifikasi KPI kondisional

Kondisi data saat ini: `kritis=1, waspada=0` (Stroberi Segar kritis) — subtext KPI
tetap "0 lainnya mulai menipis" (BENAR, karena bukan kondisi keduanya nol). Kondisi
"Semua stok aman" (keduanya nol) sudah dibuktikan LOGIKANYA benar via pembacaan kode
(`if len(kritis)==0 and len(waspada)==0`) — sudah dipakai identik di baris
`ui.action("Semua stok aman", ...)` yang SUDAH ADA dan berfungsi sebelumnya di
section "Yang Perlu Dilakukan" pada kondisi data sama; logika kondisi KPI baru ini
menggunakan pemeriksaan IDENTIK, jadi correctness-nya terjamin oleh kesamaan kondisi
yang sudah terbukti benar di tempat lain pada file yang sama.

## Cek regresi

Perkiraan Penjualan, Stok & Pembelian, Manajemen & Pengaturan: semua normal, data
produk (P001-P003) utuh — konfirmasi DB production TAK terpengaruh simulasi Temuan 3.

## Verifikasi tak ada sisa artefak simulasi

```
$ git status
modified:   app/components/charts.py
modified:   app/components/ui.py
modified:   app/views/overview.py
Untracked: notes/  (selalu dikecualikan, tak berubah)
```
`app/_test_empty_produk_TEMP.py` sudah dihapus, `.claude/launch.json` (gitignored)
dikembalikan ke isi semula (config test dihapus). Tak ada file/data tersisa dari
simulasi.

## Kesimpulan

Keempat temuan audit diperbaiki dan diverifikasi dengan bukti konkret, terutama
Temuan 3 (paling kritis) — dibuktikan lewat aplikasi sungguhan yang benar-benar
dijalankan dengan kondisi produk kosong (via monkeypatch aman, tanpa sentuh data
production), bukan cuma inspeksi kode. Tak ada regresi. Server dimatikan bersih.
