import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# =========================================================
# KONFIGURASI
# =========================================================

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "rahasia-faisal-123"
)

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL belum diset. Tambahkan DATABASE_URL di environment."
    )

# Supabase / PostgreSQL URL
# Pastikan menggunakan driver Psycopg 3
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================================================
# DATABASE
# =========================================================

db = SQLAlchemy(app)


# =========================================================
# LOGIN
# =========================================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# =========================================================
# MODEL USER
# =========================================================

class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    gaji = db.Column(
        db.Float,
        default=0
    )

    pengeluaran = db.relationship(
        "Pengeluaran",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    tabungan = db.relationship(
        "Tabungan",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================================================
# MODEL PENGELUARAN
# =========================================================

class Pengeluaran(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nama = db.Column(
        db.String(100),
        nullable=False
    )

    jumlah = db.Column(
        db.Float,
        nullable=False
    )

    tanggal = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        default="Belum Dibayar"
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================================================
# MODEL TABUNGAN
# =========================================================

class Tabungan(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    bulan = db.Column(
        db.String(20),
        nullable=False
    )

    jumlah = db.Column(
        db.Float,
        nullable=False
    )

    catatan = db.Column(
        db.String(255)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


# =========================================================
# LOGIN MANAGER
# =========================================================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(
        User,
        int(user_id)
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:
            flash(
                "Username dan password wajib diisi."
            )

            return redirect(
                url_for("register")
            )

        user_lama = User.query.filter_by(
            username=username
        ).first()

        if user_lama:
            flash(
                "Username sudah digunakan."
            )

            return redirect(
                url_for("register")
            )

        password_hash = generate_password_hash(
            password
        )

        user = User(
            username=username,
            password_hash=password_hash,
            gaji=0
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Registrasi berhasil. Silakan login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password_hash,
            password
        ):
            login_user(user)

            return redirect(
                url_for("index")
            )

        flash(
            "Username atau password salah."
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@login_required
def index():

    pengeluaran = Pengeluaran.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Pengeluaran.tanggal.desc()
    ).all()

    tabungan = Tabungan.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Tabungan.id.desc()
    ).all()

    gaji = current_user.gaji or 0

    total_dibayar = sum(
        item.jumlah
        for item in pengeluaran
        if item.status == "Sudah Dibayar"
    )

    total_belum_dibayar = sum(
        item.jumlah
        for item in pengeluaran
        if item.status != "Sudah Dibayar"
    )

    total_tabungan = sum(
        item.jumlah
        for item in tabungan
    )

    sisa_uang = (
        gaji
        - total_dibayar
        - total_tabungan
    )

    bulan_sekarang = datetime.now().strftime(
        "%B %Y"
    )

    return render_template(
        "index.html",
        username=current_user.username,
        gaji=gaji,
        pengeluaran=pengeluaran,
        tabungan=tabungan,
        total_dibayar=total_dibayar,
        total_belum_dibayar=total_belum_dibayar,
        total_tabungan=total_tabungan,
        sisa_uang=sisa_uang,
        bulan_sekarang=bulan_sekarang
    )


# =========================================================
# UPDATE GAJI
# =========================================================

@app.route("/set-gaji", methods=["POST"])
@login_required
def set_gaji():

    try:
        gaji = float(
            request.form.get(
                "gaji",
                0
            )
        )

        if gaji < 0:
            raise ValueError

        current_user.gaji = gaji

        db.session.commit()

        flash(
            "Gaji berhasil diperbarui."
        )

    except ValueError:
        flash(
            "Nominal gaji tidak valid."
        )

    return redirect(
        url_for("index")
    )


# =========================================================
# TAMBAH PENGELUARAN
# =========================================================

@app.route(
    "/tambah-pengeluaran",
    methods=["POST"]
)
@login_required
def tambah_pengeluaran():

    nama = request.form.get(
        "nama",
        ""
    ).strip()

    try:
        jumlah = float(
            request.form.get(
                "jumlah",
                0
            )
        )
    except ValueError:
        jumlah = 0

    if not nama or jumlah <= 0:

        flash(
            "Data pengeluaran tidak valid."
        )

        return redirect(
            url_for("index")
        )

    pengeluaran = Pengeluaran(
        nama=nama,
        jumlah=jumlah,
        status="Belum Dibayar",
        user_id=current_user.id
    )

    db.session.add(
        pengeluaran
    )

    db.session.commit()

    return redirect(
        url_for("index")
    )


# =========================================================
# TOGGLE STATUS PENGELUARAN
# =========================================================

@app.route(
    "/toggle-pengeluaran/<int:id>"
)
@login_required
def toggle_pengeluaran(id):

    pengeluaran = Pengeluaran.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if pengeluaran.status == "Sudah Dibayar":

        pengeluaran.status = "Belum Dibayar"

    else:

        pengeluaran.status = "Sudah Dibayar"

    db.session.commit()

    return redirect(
        url_for("index")
    )


# =========================================================
# HAPUS PENGELUARAN
# =========================================================

@app.route(
    "/hapus-pengeluaran/<int:id>"
)
@login_required
def hapus_pengeluaran(id):

    pengeluaran = Pengeluaran.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(
        pengeluaran
    )

    db.session.commit()

    return redirect(
        url_for("index")
    )


# =========================================================
# TAMBAH TABUNGAN
# =========================================================

@app.route(
    "/tambah-tabungan",
    methods=["POST"]
)
@login_required
def tambah_tabungan():

    bulan = request.form.get(
        "bulan",
        ""
    ).strip()

    catatan = request.form.get(
        "catatan",
        ""
    ).strip()

    try:
        jumlah = float(
            request.form.get(
                "jumlah",
                0
            )
        )
    except ValueError:
        jumlah = 0

    if not bulan:

        bulan = datetime.now().strftime(
            "%B %Y"
        )

    if jumlah <= 0:

        flash(
            "Nominal tabungan tidak valid."
        )

        return redirect(
            url_for("index")
        )

    tabungan = Tabungan(
        bulan=bulan,
        jumlah=jumlah,
        catatan=catatan,
        user_id=current_user.id
    )

    db.session.add(
        tabungan
    )

    db.session.commit()

    return redirect(
        url_for("index")
    )


# =========================================================
# HAPUS TABUNGAN
# =========================================================

@app.route(
    "/hapus-tabungan/<int:id>"
)
@login_required
def hapus_tabungan(id):

    tabungan = Tabungan.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(
        tabungan
    )

    db.session.commit()

    return redirect(
        url_for("index")
    )


# =========================================================
# JALANKAN APLIKASI
# =========================================================

if __name__ == "__main__":

    # Buat tabel hanya ketika menjalankan
    # aplikasi secara langsung dengan:
    # python app.py

    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )