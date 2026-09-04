# Evidence — sesudah perbaikan T-20 (floor version pandas/numpy)

Tanggal: 5 September 2026

## Keputusan

`app/requirements.txt`: `pandas>=2.0` → `pandas==3.0.5`, `numpy>=1.24` → `numpy==2.5.2`
(exact-pin, sama pola dengan `xgboost`/`scikit-learn` di T-8).

## Alasan singkat

Floor longgar sudah resolve ke lompatan mayor (pandas 2.x→3.0.5) di venv ini — bukan lagi
risiko hipotetis. Audit kode (`core/forecasting.py`, `core/inventory.py`, `core/features.py`,
seluruh `data/`) tak menemukan pemakaian API yang dihapus/berubah di pandas 3.0 (tak ada
`DataFrame.append()`, `applymap`, `np.float_`, dst — grep menyeluruh nol hasil). Disiplin
`.copy()` eksplisit yang sudah ada di banyak file jadi mitigasi alami risiko terbesar pandas
3.0 (copy-on-write chained assignment).

Dipilih pin ke versi TERINSTALL SEKARANG (3.0.5 / 2.5.2, sudah lolos testing nyata T-1/T-4/
T-7b/T-10), BUKAN versi training skripsi (2.3.3/2.4.0 — tak pernah dijalankan di repo ini
sama sekali, downgrade ke situ = ganti risiko terbukti-aman dengan risiko tak-teruji). Bukan
juga floor longgar terus-menerus (redeploy masa depan bisa resolve ke versi lebih baru yang
belum diaudit).

## Verifikasi

1. `pip show pandas numpy` di venv: `3.0.5` / `2.5.2` — persis cocok pin baru, reinstall tak
   perlu dilakukan.
2. Smoke test import: `core.forecasting`, `core.inventory`, `core.features`, `data.store`,
   `data.record_sales`, `data.weather` — semua OK.
3. Satu panggilan `forecast_future(df, "P001")` — berhasil, total 486 jar/7 hari (cocok
   baseline sesi-sesi sebelumnya). Warning yang muncul (`sklearn ... does not have valid
   feature names`) sudah dikenal dari sesi-sesi sebelumnya, tak terkait pandas/numpy, bukan
   regresi baru dari perubahan ini.

## Kesimpulan

Tidak ada regresi dari perubahan `requirements.txt` ini sendiri (perubahan versi pin,
bukan logika aplikasi — tak perlu pengujian UI penuh).
