"""
views/pengaturan.py - Halaman Manajemen & Pengaturan.

Tempat pemilik UMKM mengelola data master sendiri lewat browser, tanpa
menyentuh kode: produk, bahan baku & stok, resep (BOM), pencatatan penjualan
harian, dan panjang window tiap hari libur.

Semua perubahan tersimpan di database lokal (data/store.py) dan langsung
dipakai modul forecasting dan inventori.
"""
import streamlit as st
import pandas as pd

from components import ui
from data import store


def render():
    st.markdown("## Manajemen & Pengaturan")
    st.markdown('<div class="section-sub">Kelola produk, stok bahan baku, dan '
                'resep (BOM) Anda. Perubahan tersimpan otomatis.</div>',
                unsafe_allow_html=True)

    store.init_db()  # pastikan tabel ada (idempotent)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📦 Produk", "🧺 Bahan Baku & Stok", "📋 Resep (BOM)",
         "🧾 Catat Penjualan", "📅 Window Libur"])

    # --- TAB 1: PRODUK
    with tab1:
        ui.section("Daftar Produk",
                   "Tambah baris baru untuk produk baru. 'mu' = perkiraan "
                   "rata-rata terjual per hari (jadi acuan awal sistem).")
        prod = store.get_produk()
        edited = st.data_editor(
            prod, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("Kode", help="mis. P004"),
                "nama": st.column_config.TextColumn("Nama Produk"),
                "satuan": st.column_config.TextColumn("Satuan"),
                "mu": st.column_config.NumberColumn("Rata-rata/hari", min_value=0),
                "harga": st.column_config.NumberColumn("Harga (Rp)", min_value=0,
                                                       format="Rp %d"),
            }, key="ed_produk",
        )
        if st.button("💾 Simpan Produk", type="primary"):
            store.save_produk(edited.dropna(subset=["id"]))
            st.success("Data produk tersimpan.")
            st.rerun()

    # --- TAB 2: BAHAN BAKU & STOK
    with tab2:
        ui.section("Bahan Baku & Stok Saat Ini",
                   "Perbarui kolom 'Stok' setiap kali Anda belanja atau memakai "
                   "bahan. Lead time & biaya dipakai untuk hitung EOQ/ROP.")
        bahan = store.get_bahan()
        edited_b = st.data_editor(
            bahan, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "id": st.column_config.TextColumn("Kode", help="mis. M07"),
                "nama": st.column_config.TextColumn("Nama Bahan"),
                "satuan": st.column_config.TextColumn("Satuan"),
                "stok": st.column_config.NumberColumn("Stok Saat Ini", min_value=0),
                "lead_time": st.column_config.NumberColumn("Lead Time (hari)",
                                                           min_value=0, step=1),
                "ordering_cost": st.column_config.NumberColumn("Biaya Pesan (Rp)",
                                                               min_value=0),
                "holding_cost": st.column_config.NumberColumn("Biaya Simpan/hari (Rp)",
                                                              min_value=0),
            }, key="ed_bahan",
        )
        if st.button("💾 Simpan Bahan Baku", type="primary"):
            store.save_bahan(edited_b.dropna(subset=["id"]))
            st.success("Data bahan baku & stok tersimpan.")
            st.rerun()

    # --- TAB 3: BOM
    with tab3:
        ui.section("Resep / Bill of Materials",
                   "Isi berapa banyak tiap bahan baku dipakai untuk membuat "
                   "1 unit produk. Kosongkan (0) bila bahan tidak dipakai.")
        mat = store.get_bom_matrix()
        # ganti header kode bahan -> nama agar mudah dibaca pemilik
        nama_bahan = store.get_bahan().set_index("id")["nama"].to_dict()
        mat_show = mat.rename(columns=nama_bahan)
        edited_m = st.data_editor(mat_show, use_container_width=True, key="ed_bom")
        if st.button("💾 Simpan Resep", type="primary"):
            # kembalikan nama kolom -> kode
            inv = {v: k for k, v in nama_bahan.items()}
            edited_m.columns = [inv.get(c, c) for c in edited_m.columns]
            store.save_bom_matrix(edited_m)
            st.success("Resep (BOM) tersimpan.")
            st.rerun()

    # --- TAB 4: CATAT PENJUALAN
    with tab4:
        ui.section("Catat Penjualan Harian",
                   "Laporkan penjualan aktual. Data masuk ke riwayat sehingga "
                   "perkiraan berikutnya makin akurat. Hari libur & cuaca diisi "
                   "otomatis.")
        from data import record_sales

        prod_map = store.get_produk_dict()
        mulai_operasional = store.get_tanggal_mulai_operasional()
        hari_ini = pd.Timestamp.now().normalize()

        if mulai_operasional is None:
            # Titik reset (T-1) belum diaktifkan -- form pencatatan terkunci.
            # Data yang ada masih 100% data latihan sintetis (2023-2025).
            pid_sel = st.selectbox("Produk", list(prod_map.keys()),
                                   format_func=lambda k: prod_map[k]["nama"],
                                   key="rec_pid")
            st.warning(
                "Sistem masih memakai data latihan (bukan catatan penjualan "
                "asli). Aktifkan data real dulu sebelum mulai mencatat "
                "penjualan sungguhan -- data latihan lama tidak lagi dipakai "
                "untuk menghitung tren setelah ini."
            )
            konfirmasi = st.checkbox(
                f"Saya paham — mulai catat data asli mulai hari ini "
                f"({hari_ini.date()}), data latihan lama tidak lagi dipakai "
                f"untuk hitung tren.",
                key="konfirmasi_reset_operasional",
            )
            if st.button("🚀 Mulai Pakai Data Real Hari Ini", type="primary",
                        disabled=not konfirmasi):
                store.set_tanggal_mulai_operasional(hari_ini)
                try:
                    import core.forecasting as fc
                    fc._HIST = None
                except Exception:
                    pass
                st.rerun()
        else:
            cc1, cc2, cc3 = st.columns([2, 1, 1])
            with cc1:
                pid_sel = st.selectbox("Produk", list(prod_map.keys()),
                                       format_func=lambda k: prod_map[k]["nama"],
                                       key="rec_pid")

            if record_sales.sudah_tercatat_hari_ini(pid_sel):
                # Tanggal valid berikutnya untuk produk ini sudah lewat hari
                # sungguhan sekarang -- jangan render date_input (min_value
                # > max_value akan ditolak Streamlit). Per produk: produk
                # lain di dropdown mungkin belum tercatat, tetap bisa dipilih.
                terbaru = record_sales.last_records(pid_sel, n=1)
                if not terbaru.empty:
                    b = terbaru.iloc[0]
                    st.success(
                        f"✓ Sudah tercatat untuk hari ini: {prod_map[pid_sel]['nama']}, "
                        f"{int(b['Terjual'])} unit ({b['Tanggal']}). Kembali lagi besok "
                        f"untuk mencatat penjualan berikutnya.")
                else:
                    st.success("✓ Sudah tercatat untuk hari ini. Kembali lagi besok "
                              "untuk mencatat penjualan berikutnya.")
            else:
                nxt = record_sales.next_valid_date(pid_sel)
                with cc2:
                    tgl = st.date_input("Tanggal penjualan",
                                        value=nxt, min_value=nxt, max_value=hari_ini)
                with cc3:
                    qty = st.number_input("Jumlah terjual", min_value=0, step=1)

                st.caption(f"📅 Tanggal valid berikutnya: **{nxt.date()}** — pencatatan "
                           f"berurutan menjaga perkiraan tetap valid.")

                if st.button("🧾 Catat Penjualan", type="primary"):
                    ok, msg = record_sales.record_one(
                        pid_sel, prod_map[pid_sel]["nama"], tgl, qty)
                    (st.success if ok else st.warning)(msg)
                    if ok:
                        st.rerun()

        # --- Koreksi / hapus catatan manual
        manual = record_sales.manual_records(pid_sel)
        if not manual.empty:
            st.markdown("**Koreksi catatan manual** (data dasar tidak bisa diubah):")
            cole1, cole2, cole3 = st.columns([1.4, 1, 1])
            with cole1:
                tgl_edit = st.selectbox("Tanggal", manual["Tanggal"].tolist()[::-1],
                                        key="edit_tgl")
            with cole2:
                cur_val = int(manual[manual.Tanggal == tgl_edit]["Terjual"].iloc[0])
                qty_edit = st.number_input("Jumlah baru", min_value=0, step=1,
                                           value=cur_val, key="edit_qty")
            with cole3:
                st.write("")
                st.write("")
                if st.button("✏️ Perbarui"):
                    ok, m = record_sales.update_qty(pid_sel, tgl_edit, qty_edit)
                    (st.success if ok else st.warning)(m)
                    st.rerun()
            if st.button("🗑️ Hapus catatan terakhir"):
                ok, m = record_sales.delete_last(pid_sel)
                (st.success if ok else st.warning)(m)
                st.rerun()

        # --- Riwayat lengkap (scrollable)
        st.markdown("**Riwayat penjualan (terbaru di atas):**")
        full = record_sales.last_records(pid_sel, n=10000).iloc[::-1]
        st.dataframe(full, use_container_width=True, hide_index=True, height=320)
        st.caption("ℹ️ Mencatat penjualan memperkaya riwayat (lag/rolling) sehingga "
                   "perkiraan berikutnya lebih relevan. Bobot model diperbarui via "
                   "pelatihan ulang berkala (pengembangan lanjutan).")

    # --- TAB 5: WINDOW LIBUR
    with tab5:
        ui.section("Pengaturan Window Hari Libur",
                   "Atur berapa hari sebelum (H-) dan sesudah (H+) tiap hari "
                   "libur nasional memengaruhi penjualan. Lebaran biasanya lebih "
                   "panjang. Perubahan langsung memengaruhi perkiraan penjualan.")
        from data import weather

        wdf = store.get_window_df()
        edited_w = st.data_editor(
            wdf, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "jenis": st.column_config.TextColumn(
                    "Jenis Libur (kata kunci)",
                    help="mis. 'idul fitri', 'natal'. '(default)' = semua libur lain"),
                "h_minus": st.column_config.NumberColumn(
                    "Hari sebelum (H-)", min_value=0, max_value=7, step=1),
                "h_plus": st.column_config.NumberColumn(
                    "Hari sesudah (H+)", min_value=0, max_value=7, step=1),
            }, key="ed_window",
        )
        if st.button("💾 Simpan Window Libur", type="primary"):
            store.save_window_df(edited_w.dropna(subset=["jenis"]))
            st.success("Pengaturan window tersimpan. Perkiraan memakai window baru.")
            st.rerun()

        st.markdown("**Daftar hari libur & window efektif (2025–2026):**")
        st.caption("Window dihitung otomatis dari pengaturan di atas.")
        st.dataframe(weather.list_holidays_with_window([2025, 2026]),
                     use_container_width=True, hide_index=True, height=300)

    st.divider()
    st.caption("ℹ️ Data tersimpan di database lokal (data/dss_umkm.db). "
               "Pada deployment, diganti PostgreSQL tanpa ubah kode (Sec. 3.7.1).")
