# Evidence — T-9 (sebagian): storage persisten Docker + uji build

Tanggal: 8 September 2026

## Ringkasan

Bagian T-9 yang dikerjakan: storage persisten untuk deployment Docker. Autentikasi TIDAK
dikerjakan (ditunda sesuai arahan — sistem masih untuk 1 UMKM spesifik).

## Kondisi awal (dicek, bukan diasumsikan)

Tak ada `Dockerfile`, `docker-compose.yml`, `.dockerignore`, atau folder `docs/` di mana
pun di repo sebelum sesi ini — dicari menyeluruh dari root, nol hasil.

## File baru

- `app/Dockerfile` — base `python:3.14-slim` (cocok versi Python venv lokal yang sudah
  terbukti jalan dengan `requirements.txt` yang dipin, konsisten pola T-20), `libgomp1`
  untuk runtime XGBoost, `VOLUME ["/app/data"]`, `HEALTHCHECK` lewat endpoint bawaan
  Streamlit `/_stcore/health` (Python `urllib`, tanpa install `curl` tambahan).
- `app/.dockerignore` — kecualikan `venv/`, cache, DB dev lokal dari build context.
- `docker-compose.yml` (root) — volume bernama `upstock_data` di-mount ke `/app/data`,
  label Traefik dengan 3 PLACEHOLDER eksplisit (nama network, subdomain, cert resolver),
  TANPA `ports:` (Traefik menjangkau lewat network internal, bukan bind 80/443 langsung).
- `docs/deploy-docker.md` — panduan build/uji lokal, penjelasan perilaku volume Docker
  mewarisi isi image sekali di awal, dan bagian tegas "BELUM BISA DIJALANKAN" untuk
  bagian yang butuh konfirmasi Pak Ade.

## Uji build lokal

**Docker terdeteksi**: versi 29.7.2 (Docker Desktop, Windows, `desktop-linux` context).

**Command**: `docker build -t upstock:test .` (dari `app/`).

**Hasil: BUILD SUKSES.**
- Waktu: **2 menit 10 detik**.
- Ukuran image final: **2.35 GB**.
- Semua step selesai tanpa error: base image tertarik, `apt-get install libgomp1` sukses,
  `pip install -r requirements.txt` sukses (42 paket terinstall termasuk xgboost 3.2.0,
  scikit-learn 1.8.0, pandas 3.0.5 — semua wheel `cp314` cocok Python 3.14 di image),
  `COPY . .` sukses, image ter-export dan diberi tag `upstock:test`.

### Temuan tak terduga + perbaikan (investigasi & eksekusi terpisah, sesi sama)

`xgboost==3.2.0` menarik `nvidia-nccl-cu12` (342 MB terunduh) sebagai dependency transitif
— library NVIDIA Collective Communications (multi-GPU), sama sekali tak relevan untuk
inference CPU-only di VPS tanpa GPU. Ini penyumbang terbesar ukuran image 2.35 GB awal.

**Investigasi**: dicek metadata resmi PyPI (`requires_dist` xgboost 3.2.0) — konfirmasi
`nvidia-nccl-cu12; platform_system == "Linux"` adalah dependency WAJIB (bukan
`extras_require` opsional) untuk SEMUA platform Linux, bukan salah deteksi wheel. Tak ada
flag `pip install` yang bisa melewatkannya. Opsi ganti versi/variant xgboost DITOLAK
(berisiko terhadap kompatibilitas unpickling model `.joblib`, keputusan pin T-8 tetap
utuh, versi xgboost SAMA SEKALI tak diubah).

**Solusi aman yang diterapkan**: `app/Dockerfile` — `pip uninstall -y nvidia-nccl-cu12` di
`RUN` yang sama dengan `pip install`, setelah dicek `nvidia-nccl-cu12` cuma dipakai fitur
distributed multi-GPU training xgboost, TAK disentuh jalur inference CPU
(`model.predict()`) yang dipakai `core/forecasting.py`.

**Hasil build ulang**: SUKSES, 1 menit 57 detik. Ukuran image: **1.53 GB** (turun dari
2.35 GB, hemat ~820 MB).

**Smoke test load + predict model ASLI** (`docker run --rm upstock:test2 python -c "..."`,
load `models_trained/xgb_P001.joblib` sungguhan, BUKAN mock):
```
n_features_in_: 20   (cocok FEATURE_COLS di core/features.py)
predict(input=0 semua fitur):   [42.65163]
predict(input=5.0 semua fitur): [158.04242]
```
Keduanya angka finite, masuk akal (P001 punya `mu`=40, hasil di kisaran itu) — bukan NaN/
error/nol aneh. **Konfirmasi: xgboost tetap berfungsi normal tanpa `nvidia-nccl-cu12`,
tanpa mengubah versi xgboost sedikit pun.** `app/Dockerfile` diupdate permanen dengan
perbaikan ini.

**Tidak dijalankan** (sesuai batasan instruksi): `docker compose up`, atau deploy ke
server manapun. `docker run` HANYA dipakai untuk smoke test verifikasi di atas (perintah
inspeksi `ls`/`python -c`, bukan menjalankan aplikasi Streamlit penuh atau deploy).

## Yang MASIH BUTUH konfirmasi Pak Ade sebelum deploy sungguhan

1. Nama network Docker yang dipakai Traefik di server (placeholder saat ini: `traefik_net`,
   TEBAKAN, belum tentu benar).
2. Subdomain final untuk UPStock (placeholder: `SUBDOMAIN_PLACEHOLDER.dawala.xxx`).
3. Nama cert resolver Traefik (placeholder: `letsencrypt`, TEBAKAN umum).

Ketiganya ditandai eksplisit di `docker-compose.yml` (komentar `# PLACEHOLDER`) dan
`docs/deploy-docker.md`.

## Kesimpulan

Storage persisten (volume `upstock_data` → `/app/data`) siap secara konfigurasi, image
TERBUKTI bisa di-build sukses dari `requirements.txt` yang sudah dipin, dan sudah
dioptimalkan (1.53 GB, turun dari 2.35 GB awal) tanpa mengorbankan pin versi xgboost T-8 —
diverifikasi model asli tetap bisa di-load dan predict dengan hasil masuk akal. Belum bisa
dan belum dicoba deploy ke server sungguhan — menunggu instruksi terpisah DAN konfirmasi
Pak Ade soal detail Traefik.
