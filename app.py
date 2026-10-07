import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rahasia-faisal-123')

# Konfigurasi Database Supabase (Ganti URL dibawah dengan milikmu dari Supabase)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxx.supabase.co:5432/postgres')

# Supabase PostgreSQL fix URI scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# =========================
# TABEL DATABASE
# =========================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    gaji = db.Column(db.Float, default=0.0)

    pengeluaran = db.relationship('Pengeluaran', backref='user', lazy=True, cascade="all, delete-orphan")
    tabungan = db.relationship('Tabungan', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Pengeluaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Tabungan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bulan = db.Column(db.String(20), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    catatan = db.Column(db.String(200), default='')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Inisialisasi Tabel di Supabase
with app.app_context():
    db.create_all()


# =========================
# AUTENTIKASI (LOGIN & REGISTER)
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan! Pilih username lain.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Akun berhasil dibuat! Silakan login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Username atau password salah!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# =========================
# DASHBOARD UTAMA
# =========================

@app.route('/')
@login_required
def index():
    total_gaji = current_user.gaji

    # Ambil pengeluaran milik user yang sedang login saja
    user_pengeluaran = Pengeluaran.query.filter_by(user_id=current_user.id).all()
    
    total_terbayar = sum(p.jumlah for p in user_pengeluaran if p.status == 'lunas')
    total_pending = sum(p.jumlah for p in user_pengeluaran if p.status == 'pending')
    total_pengeluaran = total_terbayar + total_pending

    # Ambil tabungan milik user yang sedang login saja
    user_tabungan = Tabungan.query.filter_by(user_id=current_user.id).all()
    total_tabungan = sum(t.jumlah for t in user_tabungan)

    sisa_saldo = total_gaji - total_terbayar - total_tabungan
    bulan_sekarang = datetime.now().strftime('%Y-%m')

    tabungan_bulan_ini = sum(
        t.jumlah for t in user_tabungan if t.bulan == bulan_sekarang
    )

    return render_template(
        'index.html',
        gaji=total_gaji,
        pengeluaran=user_pengeluaran,
        tabungan=user_tabungan,
        total_terbayar=total_terbayar,
        total_pending=total_pending,
        total_pengeluaran=total_pengeluaran,
        total_tabungan=total_tabungan,
        tabungan_bulan_ini=tabungan_bulan_ini,
        sisa_saldo=sisa_saldo,
        bulan_sekarang=bulan_sekarang,
        username=current_user.username
    )


@app.route('/update-gaji', methods=['POST'])
@login_required
def update_gaji():
    try:
        gaji_baru = float(request.form.get('gaji', 0))
    except ValueError:
        gaji_baru = 0

    current_user.gaji = gaji_baru
    db.session.commit()

    return redirect(url_for('index'))


# =========================
# PENGELUARAN
# =========================

@app.route('/tambah-pengeluaran', methods=['POST'])
@login_required
def tambah_pengeluaran():
    nama = request.form.get('nama')
    tanggal = request.form.get('tanggal')
    status = request.form.get('status', 'pending')

    try:
        jumlah = float(request.form.get('jumlah', 0))
    except ValueError:
        jumlah = 0

    baru = Pengeluaran(
        nama=nama,
        jumlah=jumlah,
        tanggal=tanggal,
        status=status,
        user_id=current_user.id
    )
    db.session.add(baru)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/toggle-status/<int:item_id>', methods=['POST'])
@login_required
def toggle_status(item_id):
    item = Pengeluaran.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        item.status = 'lunas' if item.status == 'pending' else 'pending'
        db.session.commit()

    return redirect(url_for('index'))


@app.route('/hapus-pengeluaran/<int:item_id>', methods=['POST'])
@login_required
def hapus_pengeluaran(item_id):
    item = Pengeluaran.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('index'))


# =========================
# TABUNGAN
# =========================

@app.route('/tambah-tabungan', methods=['POST'])
@login_required
def tambah_tabungan():
    bulan = request.form.get('bulan')
    catatan = request.form.get('catatan', '').strip()

    try:
        jumlah = float(request.form.get('jumlah', 0))
    except ValueError:
        jumlah = 0

    if jumlah <= 0:
        return redirect(url_for('index'))

    baru = Tabungan(
        bulan=bulan,
        jumlah=jumlah,
        catatan=catatan,
        user_id=current_user.id
    )
    db.session.add(baru)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/hapus-tabungan/<int:tabungan_id>', methods=['POST'])
@login_required
def hapus_tabungan(tabungan_id):
    item = Tabungan.query.filter_by(id=tabungan_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)