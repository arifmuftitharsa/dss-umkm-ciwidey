# Deploy UPStock via Docker (VPS + Traefik)

Bagian dari T-9 (storage persisten deployment). Autentikasi BELUM dikerjakan (ditunda --
sistem masih untuk 1 UMKM spesifik, belum multi-tenant).

## File terkait

- `app/Dockerfile` -- image aplikasi.
- `app/.dockerignore` -- kecualikan `venv/`, cache, DB dev lokal dari build context.
- `docker-compose.yml` (root repo) -- definisi service, volume persisten, label Traefik.

## Kenapa `data/` jadi volume persisten

`data/store.py` (`DB_PATH`) dan `data/record_sales.py` (`_CSV_PATH`) sama-sama resolve ke
`app/data/`. Tanpa volume, isi folder ini (riwayat penjualan asli yang sudah dicatat
pengguna, database SQLite) IKUT HILANG tiap image di-rebuild/container diganti -- balik ke
data seed sintetis, bukan data operasional sungguhan.

Volume Docker bernama (`upstock_data`) yang MASIH KOSONG otomatis mewarisi isi direktori
image (`app/data/` versi seed, termasuk `cuaca_bandung_aktual.csv` referensi statis) SEKALI
saat pertama kali dibuat -- perilaku bawaan Docker, bukan skrip khusus. Setelah itu, isi
volume jadi sumber kebenaran, TIDAK ditimpa lagi oleh isi image walau `docker compose up
--build` dijalankan ulang.

## Build image (aman dilakukan kapan saja, tak menyentuh server)

```bash
docker compose build
```

## Uji jalan LOKAL (tanpa Traefik, untuk verifikasi sebelum deploy sungguhan)

Override sementara supaya bisa diakses langsung dari browser lokal (Traefik belum ada di
lingkungan dev):

```bash
docker compose run --rm -p 8501:8501 upstock
```

Buka `http://localhost:8501` -- verifikasi aplikasi jalan normal DAN cek data yang dicatat
lewat form Catat Penjualan tetap ada setelah container dihentikan lalu dijalankan ulang
(bukti volume persisten bekerja).

## BELUM BISA DIJALANKAN sampai Pak Ade konfirmasi

`docker-compose.yml` punya 3 nilai PLACEHOLDER yang harus diganti nilai sungguhan SEBELUM
`docker compose up -d` dijalankan di server:

1. **`traefik_net`** (nama network Docker yang dipakai Traefik di server) -- placeholder
   ini TEBAKAN UMUM, belum tentu nama sungguhan. Cek dengan `docker network ls` di server,
   atau tanya langsung ke Pak Ade.
2. **`SUBDOMAIN_PLACEHOLDER.dawala.xxx`** -- subdomain final untuk UPStock, belum
   dikonfirmasi.
3. **`letsencrypt`** (nama cert resolver Traefik) -- juga tebakan umum, tergantung
   konfigurasi Traefik yang sudah ada di server (lihat `traefik.yml`/`static config`
   Traefik di server, biasanya di bawah `certificatesResolvers`).

Begitu ketiganya dikonfirmasi, cukup ganti 3 baris di `docker-compose.yml` -- tidak perlu
tulis ulang konfigurasi dari nol.

## Yang TIDAK termasuk scope ini

- Autentikasi (ditunda, lihat brief T-9).
- Backup otomatis volume `upstock_data` -- belum dirancang, perlu didiskusikan terpisah
  (mis. cron `docker run --rm -v upstock_data:/data -v $(pwd)/backup:/backup ...`).
- CI/CD build otomatis (prinsip #2 CLAUDE.md) -- Dockerfile ini dirancang bisa dipakai
  GitHub Actions nanti, tapi belum ada workflow-nya.
