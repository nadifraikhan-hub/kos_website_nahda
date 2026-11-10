from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)
app.secret_key = "ganti-dengan-kunci-rahasia-anda"
DB_PATH = Path(__file__).with_name("kos_nahda.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS penghuni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kamar TEXT NOT NULL UNIQUE,
            telepon TEXT DEFAULT '',
            mulai_tinggal TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Aktif'
        );
        CREATE TABLE IF NOT EXISTS pemasukan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            penghuni_id INTEGER,
            keterangan TEXT NOT NULL,
            jumlah INTEGER NOT NULL CHECK(jumlah >= 0),
            metode TEXT NOT NULL DEFAULT 'Tunai',
            status TEXT NOT NULL DEFAULT 'Lunas',
            FOREIGN KEY (penghuni_id) REFERENCES penghuni(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS pengeluaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL,
            kategori TEXT NOT NULL,
            keterangan TEXT NOT NULL,
            jumlah INTEGER NOT NULL CHECK(jumlah >= 0)
        );
        """)
        count = conn.execute("SELECT COUNT(*) FROM penghuni").fetchone()[0]
        if count == 0:
            conn.execute("INSERT INTO penghuni (nama,kamar,telepon,mulai_tinggal,status) VALUES (?,?,?,?,?)",
                         ("Contoh Penghuni", "A01", "-", date.today().isoformat(), "Aktif"))

@app.template_filter("rupiah")
def rupiah(value):
    try:
        return "Rp " + f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"

@app.context_processor
def inject_year():
    return {"tahun_ini": date.today().year, "hari_ini": date.today().isoformat()}

@app.route("/")
def dashboard():
    with db() as conn:
        total_masuk = conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pemasukan WHERE status='Lunas'").fetchone()[0]
        total_keluar = conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pengeluaran").fetchone()[0]
        penghuni_aktif = conn.execute("SELECT COUNT(*) FROM penghuni WHERE status='Aktif'").fetchone()[0]
        transaksi = conn.execute("""SELECT p.*, h.nama AS nama_penghuni, h.kamar
            FROM pemasukan p LEFT JOIN penghuni h ON h.id=p.penghuni_id
            ORDER BY p.tanggal DESC, p.id DESC LIMIT 6""").fetchall()
    return render_template("dashboard.html", total_masuk=total_masuk, total_keluar=total_keluar,
                           saldo=total_masuk-total_keluar, penghuni_aktif=penghuni_aktif, transaksi=transaksi)

@app.route("/pemasukan", methods=["GET", "POST"])
def pemasukan():
    with db() as conn:
        if request.method == "POST":
            tanggal = request.form.get("tanggal", "").strip()
            keterangan = request.form.get("keterangan", "").strip()
            jumlah = request.form.get("jumlah", "0").strip()
            metode = request.form.get("metode", "Tunai")
            status = request.form.get("status", "Lunas")
            penghuni_id = request.form.get("penghuni_id") or None
            try:
                jumlah = int(jumlah)
                if not tanggal or not keterangan or jumlah <= 0:
                    raise ValueError
                conn.execute("INSERT INTO pemasukan (tanggal,penghuni_id,keterangan,jumlah,metode,status) VALUES (?,?,?,?,?,?)",
                             (tanggal, penghuni_id, keterangan, jumlah, metode, status))
                flash("Data pemasukan berhasil ditambahkan.", "success")
            except (ValueError, TypeError):
                flash("Periksa kembali tanggal, keterangan, dan jumlah. Jumlah harus lebih dari nol.", "error")
            return redirect(url_for("pemasukan"))
        q = request.args.get("q", "").strip()
        sql = """SELECT p.*, h.nama AS nama_penghuni, h.kamar FROM pemasukan p
                 LEFT JOIN penghuni h ON h.id=p.penghuni_id"""
        params = []
        if q:
            sql += " WHERE p.keterangan LIKE ? OR h.nama LIKE ? OR p.status LIKE ?"
            params = [f"%{q}%"] * 3
        sql += " ORDER BY p.tanggal DESC, p.id DESC"
        rows = conn.execute(sql, params).fetchall()
        penghuni = conn.execute("SELECT id,nama,kamar FROM penghuni WHERE status='Aktif' ORDER BY nama").fetchall()
    return render_template("pemasukan.html", rows=rows, penghuni=penghuni, q=q)

@app.route("/pemasukan/<int:item_id>/edit", methods=["GET", "POST"])
def edit_pemasukan(item_id):
    with db() as conn:
        item = conn.execute("SELECT * FROM pemasukan WHERE id=?", (item_id,)).fetchone()
        if not item:
            flash("Data pemasukan tidak ditemukan.", "error")
            return redirect(url_for("pemasukan"))
        if request.method == "POST":
            try:
                tanggal = request.form.get("tanggal", "").strip()
                keterangan = request.form.get("keterangan", "").strip()
                jumlah = int(request.form.get("jumlah", "0"))
                if not tanggal or not keterangan or jumlah <= 0:
                    raise ValueError
                conn.execute("""UPDATE pemasukan SET tanggal=?, penghuni_id=?, keterangan=?, jumlah=?, metode=?, status=?
                    WHERE id=?""", (tanggal, request.form.get("penghuni_id") or None, keterangan, jumlah,
                                    request.form.get("metode","Tunai"), request.form.get("status","Lunas"), item_id))
                flash("Data pemasukan berhasil diperbarui.", "success")
                return redirect(url_for("pemasukan"))
            except (ValueError, TypeError):
                flash("Data tidak valid. Pastikan jumlah lebih dari nol.", "error")
                item = conn.execute("SELECT * FROM pemasukan WHERE id=?", (item_id,)).fetchone()
        penghuni = conn.execute("SELECT id,nama,kamar FROM penghuni ORDER BY nama").fetchall()
    return render_template("edit_pemasukan.html", item=item, penghuni=penghuni)

@app.route("/pemasukan/<int:item_id>/hapus", methods=["POST"])
def hapus_pemasukan(item_id):
    with db() as conn:
        conn.execute("DELETE FROM pemasukan WHERE id=?", (item_id,))
    flash("Data pemasukan berhasil dihapus.", "success")
    return redirect(url_for("pemasukan"))

@app.route("/penghuni", methods=["GET", "POST"])
def penghuni():
    with db() as conn:
        if request.method == "POST":
            nama=request.form.get("nama","").strip(); kamar=request.form.get("kamar","").strip()
            telepon=request.form.get("telepon","").strip(); mulai=request.form.get("mulai_tinggal","").strip()
            status=request.form.get("status","Aktif")
            try:
                if not nama or not kamar: raise ValueError
                conn.execute("INSERT INTO penghuni (nama,kamar,telepon,mulai_tinggal,status) VALUES (?,?,?,?,?)",
                             (nama,kamar,telepon,mulai,status))
                flash("Data penghuni berhasil ditambahkan.", "success")
            except sqlite3.IntegrityError:
                flash("Nomor kamar sudah terdaftar. Gunakan nomor kamar yang berbeda.", "error")
            except ValueError:
                flash("Nama dan nomor kamar wajib diisi.", "error")
            return redirect(url_for("penghuni"))
        rows=conn.execute("SELECT * FROM penghuni ORDER BY kamar").fetchall()
    return render_template("penghuni.html", rows=rows)

@app.route("/penghuni/<int:item_id>/edit", methods=["GET","POST"])
def edit_penghuni(item_id):
    with db() as conn:
        item=conn.execute("SELECT * FROM penghuni WHERE id=?",(item_id,)).fetchone()
        if not item:
            flash("Data penghuni tidak ditemukan.","error"); return redirect(url_for("penghuni"))
        if request.method=="POST":
            try:
                nama=request.form.get("nama","").strip(); kamar=request.form.get("kamar","").strip()
                if not nama or not kamar: raise ValueError
                conn.execute("UPDATE penghuni SET nama=?,kamar=?,telepon=?,mulai_tinggal=?,status=? WHERE id=?",
                             (nama,kamar,request.form.get("telepon","").strip(),request.form.get("mulai_tinggal","").strip(),
                              request.form.get("status","Aktif"),item_id))
                flash("Data penghuni berhasil diperbarui.","success"); return redirect(url_for("penghuni"))
            except sqlite3.IntegrityError:
                flash("Nomor kamar tersebut sudah dipakai penghuni lain.","error")
            except ValueError:
                flash("Nama dan nomor kamar wajib diisi.","error")
            item=conn.execute("SELECT * FROM penghuni WHERE id=?",(item_id,)).fetchone()
    return render_template("edit_penghuni.html", item=item)

@app.route("/penghuni/<int:item_id>/hapus", methods=["POST"])
def hapus_penghuni(item_id):
    with db() as conn:
        conn.execute("DELETE FROM penghuni WHERE id=?",(item_id,))
    flash("Data penghuni dihapus. Riwayat pemasukan tetap tersimpan tanpa nama penghuni.","success")
    return redirect(url_for("penghuni"))

@app.route("/pengeluaran", methods=["GET","POST"])
def pengeluaran():
    with db() as conn:
        if request.method=="POST":
            try:
                tanggal=request.form.get("tanggal","").strip()
                kategori=request.form.get("kategori","").strip()
                keterangan=request.form.get("keterangan","").strip()
                jumlah=int(request.form.get("jumlah","0"))
                if not tanggal or not kategori or not keterangan or jumlah<=0: raise ValueError
                conn.execute("INSERT INTO pengeluaran (tanggal,kategori,keterangan,jumlah) VALUES (?,?,?,?)",
                             (tanggal,kategori,keterangan,jumlah))
                flash("Pengeluaran berhasil dicatat.","success")
            except (ValueError,TypeError):
                flash("Lengkapi semua data dan pastikan jumlah lebih dari nol.","error")
            return redirect(url_for("pengeluaran"))
        rows=conn.execute("SELECT * FROM pengeluaran ORDER BY tanggal DESC,id DESC").fetchall()
    return render_template("pengeluaran.html", rows=rows)

@app.route("/pengeluaran/<int:item_id>/hapus", methods=["POST"])
def hapus_pengeluaran(item_id):
    with db() as conn: conn.execute("DELETE FROM pengeluaran WHERE id=?",(item_id,))
    flash("Data pengeluaran dihapus.","success"); return redirect(url_for("pengeluaran"))

@app.route("/laporan")
def laporan():
    awal=request.args.get("awal", date.today().replace(day=1).isoformat())
    akhir=request.args.get("akhir", date.today().isoformat())
    with db() as conn:
        masuk=conn.execute("""SELECT * FROM pemasukan WHERE tanggal BETWEEN ? AND ? ORDER BY tanggal DESC,id DESC""",(awal,akhir)).fetchall()
        keluar=conn.execute("""SELECT * FROM pengeluaran WHERE tanggal BETWEEN ? AND ? ORDER BY tanggal DESC,id DESC""",(awal,akhir)).fetchall()
        total_masuk=conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pemasukan WHERE status='Lunas' AND tanggal BETWEEN ? AND ?",(awal,akhir)).fetchone()[0]
        total_keluar=conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pengeluaran WHERE tanggal BETWEEN ? AND ?",(awal,akhir)).fetchone()[0]
    return render_template("laporan.html", awal=awal, akhir=akhir, masuk=masuk, keluar=keluar,
                           total_masuk=total_masuk,total_keluar=total_keluar, saldo=total_masuk-total_keluar)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
