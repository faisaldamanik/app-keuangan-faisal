from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Data Keuangan
data_keuangan = {
    'gaji': 0,
    'pengeluaran': [],
    'tabungan': []
}

next_id = 1
next_tabungan_id = 1


@app.route('/')
def index():
    total_gaji = data_keuangan['gaji']

    # Pengeluaran
    total_terbayar = sum(
        p['jumlah']
        for p in data_keuangan['pengeluaran']
        if p['status'] == 'lunas'
    )

    total_pending = sum(
        p['jumlah']
        for p in data_keuangan['pengeluaran']
        if p['status'] == 'pending'
    )

    total_pengeluaran = total_terbayar + total_pending

    # Tabungan
    total_tabungan = sum(
        t['jumlah']
        for t in data_keuangan['tabungan']
    )

    # Sisa saldo setelah pengeluaran yang sudah dibayar
    # dan uang yang sudah dimasukkan ke tabungan
    sisa_saldo = total_gaji - total_terbayar - total_tabungan

    # Bulan sekarang
    bulan_sekarang = datetime.now().strftime('%Y-%m')

    # Tabungan bulan sekarang
    tabungan_bulan_ini = sum(
        t['jumlah']
        for t in data_keuangan['tabungan']
        if t['bulan'] == bulan_sekarang
    )

    return render_template(
        'index.html',
        gaji=total_gaji,
        pengeluaran=data_keuangan['pengeluaran'],
        tabungan=data_keuangan['tabungan'],
        total_terbayar=total_terbayar,
        total_pending=total_pending,
        total_pengeluaran=total_pengeluaran,
        total_tabungan=total_tabungan,
        tabungan_bulan_ini=tabungan_bulan_ini,
        sisa_saldo=sisa_saldo,
        bulan_sekarang=bulan_sekarang
    )


@app.route('/update-gaji', methods=['POST'])
def update_gaji():
    try:
        gaji_baru = float(request.form.get('gaji', 0))
    except ValueError:
        gaji_baru = 0

    data_keuangan['gaji'] = gaji_baru

    return redirect(url_for('index'))


# =========================
# PENGELUARAN
# =========================

@app.route('/tambah-pengeluaran', methods=['POST'])
def tambah_pengeluaran():
    global next_id

    nama = request.form.get('nama')
    tanggal = request.form.get('tanggal')
    status = request.form.get('status', 'pending')

    try:
        jumlah = float(request.form.get('jumlah', 0))
    except ValueError:
        jumlah = 0

    data_keuangan['pengeluaran'].append({
        'id': next_id,
        'nama': nama,
        'jumlah': jumlah,
        'tanggal': tanggal,
        'status': status
    })

    next_id += 1

    return redirect(url_for('index'))


@app.route('/toggle-status/<int:item_id>', methods=['POST'])
def toggle_status(item_id):
    for item in data_keuangan['pengeluaran']:
        if item['id'] == item_id:
            if item['status'] == 'pending':
                item['status'] = 'lunas'
            else:
                item['status'] = 'pending'
            break

    return redirect(url_for('index'))


@app.route('/hapus-pengeluaran/<int:item_id>', methods=['POST'])
def hapus_pengeluaran(item_id):
    data_keuangan['pengeluaran'] = [
        p for p in data_keuangan['pengeluaran']
        if p['id'] != item_id
    ]

    return redirect(url_for('index'))


# =========================
# TABUNGAN
# =========================

@app.route('/tambah-tabungan', methods=['POST'])
def tambah_tabungan():
    global next_tabungan_id

    bulan = request.form.get('bulan')
    catatan = request.form.get('catatan', '').strip()

    try:
        jumlah = float(request.form.get('jumlah', 0))
    except ValueError:
        jumlah = 0

    # Jangan simpan nominal 0 atau negatif
    if jumlah <= 0:
        return redirect(url_for('index'))

    data_keuangan['tabungan'].append({
        'id': next_tabungan_id,
        'bulan': bulan,
        'jumlah': jumlah,
        'catatan': catatan
    })

    next_tabungan_id += 1

    return redirect(url_for('index'))


@app.route('/hapus-tabungan/<int:tabungan_id>', methods=['POST'])
def hapus_tabungan(tabungan_id):
    data_keuangan['tabungan'] = [
        t for t in data_keuangan['tabungan']
        if t['id'] != tabungan_id
    ]

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
