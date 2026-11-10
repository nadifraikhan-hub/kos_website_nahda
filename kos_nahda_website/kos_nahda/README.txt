KOS NAHDA - Aplikasi Pencatatan Keuangan Kos

FITUR (5 halaman utama)
1. Dashboard: ringkasan pemasukan lunas, pengeluaran, saldo, penghuni aktif, transaksi terbaru.
2. Pemasukan: tambah, cari, ubah, dan hapus transaksi pemasukan (CRUD).
3. Penghuni: tambah, ubah, dan hapus data penghuni serta nomor kamar.
4. Pengeluaran: catat biaya operasional dan hapus data pengeluaran.
5. Laporan: filter periode tanggal, rekap pemasukan/pengeluaran/saldo, dan cetak dari browser.

CARA MENJALANKAN DI WINDOWS
1. Ekstrak folder/ZIP ini.
2. Install Python 3 dari https://www.python.org/downloads/ (centang "Add Python to PATH").
3. Buka Command Prompt di folder proyek.
4. Jalankan:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
5. Buka browser ke http://127.0.0.1:5000

DATABASE
- Data otomatis disimpan dalam file kos_nahda.db di folder proyek.
- Jangan hapus file tersebut jika ingin mempertahankan data.
- Untuk cadangan, hentikan aplikasi lalu salin file kos_nahda.db ke tempat aman.

CATATAN
- Ini aplikasi lokal untuk tugas/praktik. Jangan dibuka ke internet tanpa menambahkan autentikasi,
  perlindungan keamanan, dan konfigurasi server yang sesuai.
- Data contoh penghuni "Contoh Penghuni" dibuat otomatis saat database pertama kali dibuat.
