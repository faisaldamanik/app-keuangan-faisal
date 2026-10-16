(() => {
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const idr = n => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 })
                     .format(n).replace(/\u00a0/g, ' ');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const icons = () => window.lucide && lucide.createIcons();
  icons();

  /* ---- Animasi masuk saat scroll ---- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { threshold: .08 });
  $$('.reveal').forEach((el, i) => { el.style.setProperty('--d', (i % 6) * 70 + 'ms'); io.observe(el); });

  /* ---- Hitung naik untuk angka uang ---- */
  $$('[data-count]').forEach(el => {
    const to = parseFloat(el.dataset.count) || 0;
    if (reduce) { el.textContent = idr(to); return; }
    const t0 = performance.now(), dur = 1100;
    const tick = t => {
      const p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 4);
      el.textContent = idr(to * e);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  /* ---- Donut alokasi gaji ---- */
  $$('.ring').forEach(r => {
    const g = +r.dataset.gaji || 0, b = +r.dataset.bayar || 0, u = +r.dataset.belum || 0;
    const C = 2 * Math.PI * 56;
    const pb = g > 0 ? Math.min(b / g, 1) : 0;
    const pu = g > 0 ? Math.min(u / g, 1 - pb) : 0;
    const set = (el, len, off) => { el.style.strokeDasharray = `${len} ${C}`; el.style.strokeDashoffset = -off; };
    setTimeout(() => {
      set($('.seg-bayar', r), pb * C, 0);
      set($('.seg-belum', r), pu * C, pb * C);
    }, 150);
    const pct = Math.round((pb + pu) * 100);
    const out = $('.ring-pct', r), t0 = performance.now();
    const tick = t => {
      const p = reduce ? 1 : Math.min((t - t0) / 1200, 1);
      out.textContent = Math.round(pct * (1 - Math.pow(1 - p, 3))) + '%';
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    const lb = $('#lg-bayar'), lu = $('#lg-belum');
    if (lb) lb.textContent = Math.round(pb * 100) + '%';
    if (lu) lu.textContent = Math.round(pu * 100) + '%';
  });

  /* ---- Efek miring 3D + sorotan ---- */
  if (!reduce && matchMedia('(hover:hover)').matches) {
    $$('.tilt').forEach(el => {
      el.addEventListener('pointermove', e => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        el.style.transform = `perspective(700px) rotateX(${-y * 8}deg) rotateY(${x * 8}deg) translateY(-3px)`;
        el.style.setProperty('--mx', (x + .5) * 100 + '%');
        el.style.setProperty('--my', (y + .5) * 100 + '%');
      });
      el.addEventListener('pointerleave', () => { el.style.transform = ''; });
    });
  }

  /* ---- Ripple pada tombol ---- */
  document.addEventListener('pointerdown', e => {
    const b = e.target.closest('.btn'); if (!b) return;
    const r = b.getBoundingClientRect(), s = Math.max(r.width, r.height) / 2;
    const sp = document.createElement('span');
    sp.className = 'ripple';
    sp.style.cssText = `width:${s}px;height:${s}px;left:${e.clientX - r.left - s / 2}px;top:${e.clientY - r.top - s / 2}px`;
    b.appendChild(sp); setTimeout(() => sp.remove(), 650);
  });

  /* ---- Toast (menggantikan flash message biasa) ---- */
  const stack = document.createElement('div');
  stack.className = 'toasts'; document.body.append(stack);
  function toast(msg, cat) {
    const t = document.createElement('div');
    t.className = 'toast ' + cat;
    t.innerHTML = `<i data-lucide="${cat === 'danger' ? 'circle-alert' : 'circle-check'}"></i><span></span><div class="bar"></div>`;
    $('span', t).textContent = msg;
    stack.append(t); icons();
    const kill = () => { t.classList.add('out'); setTimeout(() => t.remove(), 400); };
    setTimeout(kill, 4200); t.onclick = kill;
  }
  $$('.flash-data').forEach(f => toast(f.dataset.msg, f.dataset.cat === 'danger' ? 'danger' : 'ok'));

  /* ---- Modal konfirmasi (menggantikan confirm() bawaan browser) ---- */
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `<div class="modal-box glass glow" role="dialog" aria-modal="true">
    <div class="modal-ico"><i data-lucide="triangle-alert"></i></div>
    <h3>Yakin?</h3><p></p>
    <div class="modal-act"><button class="btn btn-ghost" data-no type="button">Batal</button>
    <a class="btn btn-danger" data-yes>Ya, lanjut</a></div></div>`;
  document.body.append(modal); icons();
  const closeModal = () => modal.classList.remove('open');
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-confirm]');
    if (a) {
      e.preventDefault();
      $('p', modal).textContent = a.dataset.confirm;
      $('[data-yes]', modal).href = a.href;
      modal.classList.add('open'); $('[data-no]', modal).focus();
    } else if (e.target.closest('[data-no]') || e.target === modal) closeModal();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

  /* ---- Cari & filter pengeluaran ---- */
  const list = $('#expList');
  if (list) {
    let f = 'all', q = '';
    const items = $$('.item', list), none = $('#noMatch');
    const apply = () => {
      let n = 0;
      items.forEach(i => {
        const ok = (f === 'all' || i.dataset.status === f) && i.dataset.name.includes(q);
        i.hidden = !ok; if (ok) n++;
      });
      if (none) none.hidden = n > 0;
    };
    $$('.chip').forEach(c => c.onclick = () => {
      $$('.chip').forEach(x => x.classList.remove('on'));
      c.classList.add('on'); f = c.dataset.f; apply();
    });
    const s = $('#search');
    if (s) s.addEventListener('input', e => { q = e.target.value.trim().toLowerCase(); apply(); });
  }

  /* ---- Tab mobile ---- */
  $$('.tab').forEach(t => t.onclick = () => {
    $$('.tab').forEach(x => x.classList.toggle('on', x === t));
    $$('.panel').forEach(p => p.classList.toggle('show', p.dataset.panel === t.dataset.tab));
  });

  /* ---- Pratinjau nominal rupiah saat mengetik ---- */
  $$('[data-money]').forEach(i => {
    const h = i.closest('.fld')?.querySelector('.hint'); if (!h) return;
    const up = () => { h.textContent = i.value ? idr(+i.value) : ''; };
    i.addEventListener('input', up); up();
  });

  /* ---- Tampilkan / sembunyikan password ---- */
  $$('[data-eye]').forEach(b => b.onclick = () => {
    const i = $('#' + b.dataset.eye), show = i.type === 'password';
    i.type = show ? 'text' : 'password';
    b.classList.toggle('shown', show);
    b.setAttribute('aria-label', show ? 'Sembunyikan password' : 'Tampilkan password');
  });

  /* ---- Indikator kekuatan password ---- */
  const pw = $('#password[data-meter]');
  if (pw) {
    const bar = $('.meter i'), lab = $('.meter-l');
    const names = ['', 'Lemah', 'Cukup', 'Kuat', 'Sangat kuat'];
    const cols = ['', '#fb7185', '#fbbf24', '#34d399', '#22d3ee'];
    pw.addEventListener('input', () => {
      const v = pw.value;
      let s = v ? (v.length >= 6) + (v.length >= 10) + (/[A-Z]/.test(v) && /[a-z]/.test(v)) + (/\d|[^\w]/.test(v)) : 0;
      bar.style.width = s * 25 + '%'; bar.style.background = cols[s] || 'transparent';
      lab.textContent = names[s];
    });
  }

  /* ---- Tombol loading saat submit ---- */
  $$('form').forEach(f => f.addEventListener('submit', () => {
    const b = $('button[type=submit]', f); if (b) b.classList.add('loading');
  }));
})();