FROM python:3.14-slim

# libgomp1 -- runtime dependency XGBoost (OpenMP). Fail-fast: tanpa ini
# forecast_future() crash saat load model .joblib, BUKAN saat startup --
# container terlihat "jalan" tapi request pertama gagal, membingungkan.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# nvidia-nccl-cu12 (~342MB) -- dependency WAJIB paket xgboost==3.2.0 di semua
# platform Linux (requires_dist PyPI, bukan extras_require -- dicek, bukan
# ditebak), tapi cuma dipakai fitur distributed multi-GPU training, TIDAK
# disentuh jalur inference CPU (model.predict()) yang dipakai
# core/forecasting.py. Dihapus di RUN yang sama supaya tak nyangkut di layer
# image. TIDAK mengubah versi xgboost sedikit pun (pin T-8 tetap utuh).
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y --no-input nvidia-nccl-cu12

COPY . .

# data/ = mount point volume persisten (lihat docker-compose.yml). Isi awal
# (seed CSV, cuaca_bandung_aktual.csv) ikut ter-COPY ke image; volume Docker
# bernama yang masih kosong otomatis mewarisi isi ini SEKALI saat pertama
# dibuat (perilaku bawaan Docker), lalu persisten lintas redeploy setelahnya.
VOLUME ["/app/data"]

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
