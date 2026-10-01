/* ATELIER · app.js
   Comportamiento general: guardados, modal de colaboración, búsqueda, filtros,
   compartir, lightbox y avisos. Sin dependencias. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const A = window.ATELIER || {};
  const norm = t => (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const esc = t => String(t ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ICON = {
    close: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    check: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    star: '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="m12 3.5 2.6 5.3 5.9.8-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.8z"/></svg>',
  };

  /* ---------- Aviso (toast) ---------- */
  let toastTimer;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.classList.add('is-on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('is-on'), 2600);
  }
  window.Atelier = { toast };

  /* ---------- Barra demo y cabecera ---------- */
  const demo = $('#demobar');
  if (demo && !sessionStorage.getItem('atelier.demo.off')) demo.hidden = false;
  $('[data-dismiss-demo]')?.addEventListener('click', () => { demo.hidden = true; sessionStorage.setItem('atelier.demo.off', '1'); });
  const topbar = $('.topbar');
  const onScroll = () => topbar.classList.toggle('is-scrolled', window.scrollY > 8);
  onScroll(); addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Diálogos ---------- */
  $$('dialog').forEach(d => {
    d.addEventListener('click', e => { if (e.target === d) d.close(); });   // clic en el fondo
  });
  document.addEventListener('click', e => { if (e.target.closest('[data-close]')) e.target.closest('dialog').close(); });

  /* ---------- Guardar eventos (localStorage) ---------- */
  const KEY = 'atelier.saved';
  const getSaved = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };
  const setSaved = list => { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch {} };

  function syncSaved() {
    const list = getSaved();
    $$('.js-save').forEach(b => {
      const on = list.includes(b.dataset.slug);
      b.setAttribute('aria-pressed', on);
      const lbl = $('[data-label]', b);
      if (lbl) lbl.textContent = on ? 'Evento guardado' : 'Guardar evento';
    });
    const badge = $('[data-saved-count]');
    badge.textContent = list.length;
    badge.hidden = !list.length;
  }

  function toggleSave(btn) {
    const slug = btn.dataset.slug;
    let list = getSaved();
    const was = list.includes(slug);
    list = was ? list.filter(s => s !== slug) : [...list, slug];
    setSaved(list);
    syncSaved();
    btn.classList.remove('is-pop'); void btn.offsetWidth; btn.classList.add('is-pop');
    toast(was ? 'Evento quitado de guardados' : 'Evento guardado');
  }

  async function openSaved() {
    const box = $('#saved-list');
    const list = getSaved();
    $('#dlg-saved').showModal();
    if (!list.length) { box.innerHTML = '<p class="saved-empty">Todavía no guardas eventos. Toca el marcador en cualquier evento para verlo aquí.</p>'; return; }
    box.innerHTML = '<p class="saved-empty">Cargando…</p>';
    try {
      const items = await (await fetch('/api/eventos?slugs=' + list.join(','))).json();
      box.innerHTML = items.map(e => `
        <div class="saved">
          <a href="${e.url}"><img src="${e.image}" alt=""></a>
          <a href="${e.url}"><span class="saved__t">${esc(e.title)}</span><span class="saved__m">${esc(e.date)}, ${esc(e.time)} h, ${esc(e.place)}</span></a>
          <button class="icon-btn js-save" type="button" data-slug="${e.slug}" data-remove aria-label="Quitar de guardados">${ICON.close}</button>
        </div>`).join('') || '<p class="saved-empty">No encontramos tus eventos guardados.</p>';
    } catch { box.innerHTML = '<p class="saved-empty">No pudimos cargar tus guardados. Intenta de nuevo.</p>'; }
  }

  /* ---------- Modal de colaboración ---------- */
  const options = (arr, first) => (first ? `<option value="">${first}</option>` : '') + arr.map(o => `<option>${esc(o)}</option>`).join('');
  const artistOpts = sel => '<option value="">Aún no lo sé</option>' + (A.artists || []).map(a => `<option value="${esc(a.name)}" ${a.slug === sel ? 'selected' : ''}>${esc(a.name)}</option>`).join('');
  const spaceOpts = sel => '<option value="">Otro / aún no registrado</option>' + (A.spaces || []).map(s => `<option value="${esc(s.name)}" ${s.slug === sel ? 'selected' : ''}>${esc(s.name)}</option>`).join('');
  const field = (id, label, control) => `<div class="field" data-field="${id}"><label for="f-${id}">${label}</label>${control}<span class="field__msg" hidden></span></div>`;

  function collabForm(mode, ctx) {
    const artist = (A.artists || []).find(a => a.slug === ctx.artist);
    const space = (A.spaces || []).find(s => s.slug === ctx.space);
    const cfg = {
      join: {
        title: 'Quiero formar parte', intro: 'Cuéntanos quién eres y qué haces. Atelier revisa cada perfil y te escribe.',
        fields: field('nombre', 'Tu nombre o nombre artístico', '<input id="f-nombre" name="nombre" autocomplete="name" required>') +
          field('contacto', 'Correo o Instagram', '<input id="f-contacto" name="contacto" required>') +
          field('rol', 'Disciplina', `<select id="f-rol" name="rol">${options(A.disciplines || [])}</select>`) +
          field('mensaje', 'Cuéntanos de tu trabajo', '<textarea id="f-mensaje" name="mensaje" placeholder="Qué haces, qué buscas y dónde te gustaría presentarte"></textarea>'),
        send: 'Enviar mi perfil', ok: 'Recibimos tu perfil. Atelier lo revisará y te escribirá.', destino: '',
      },
      collab: {
        title: artist ? `Quiero colaborar con ${artist.name}` : 'Quiero colaborar', intro: 'Cuéntanos qué tienes en mente. Atelier acerca tu propuesta al artista.',
        fields: field('nombre', 'Tu nombre o el de tu espacio', '<input id="f-nombre" name="nombre" autocomplete="name" required>') +
          field('contacto', 'Correo o teléfono', '<input id="f-contacto" name="contacto" required>') +
          field('rol', 'Tipo de colaboración', `<select id="f-rol" name="rol">${options(A.collabTypes || [])}</select>`) +
          field('mensaje', 'Tu idea', '<textarea id="f-mensaje" name="mensaje" placeholder="Qué te gustaría crear y cuándo"></textarea>'),
        send: 'Enviar propuesta', ok: 'Propuesta enviada. Atelier la compartirá con el artista.', destino: artist ? artist.name : '',
      },
      propose: {
        title: 'Proponer una colaboración', intro: 'Un espacio puede impulsar talento. Cuéntanos qué tienes y qué te gustaría crear.',
        fields: field('nombre', 'Tu nombre', '<input id="f-nombre" name="nombre" autocomplete="name" required>') +
          field('contacto', 'Correo o teléfono', '<input id="f-contacto" name="contacto" required>') +
          field('rol', 'Soy', `<select id="f-rol" name="rol">${options(['Dueño o encargado de un espacio', 'Artista', 'Otro'])}</select>`) +
          field('espacio', 'Espacio', `<select id="f-espacio" name="espacio">${spaceOpts(ctx.space)}</select>`) +
          field('artista', 'Artista de interés', `<select id="f-artista" name="artista">${artistOpts(ctx.artist)}</select>`) +
          field('mensaje', 'Tu idea', '<textarea id="f-mensaje" name="mensaje" placeholder="Exposición, concierto, mural, taller u otra idea"></textarea>'),
        send: 'Enviar propuesta', ok: 'Propuesta enviada. Atelier te escribirá para dar el siguiente paso.', destino: space ? space.name : '',
      },
    }[mode];
    return cfg;
  }

  function openCollab(mode, ctx = {}) {
    const cfg = collabForm(mode, ctx);
    const panel = $('#collab-panel');
    panel.innerHTML = `
      <div class="sheet__head"><h2 class="sheet__title" id="collab-title">${esc(cfg.title)}</h2>
        <button type="button" class="icon-btn" data-close aria-label="Cerrar">${ICON.close}</button></div>
      <p class="sheet__intro">${esc(cfg.intro)}</p>
      <form novalidate>${cfg.fields}
        <p class="form-error" hidden></p>
        <div class="form-actions"><button class="btn" type="submit">${cfg.send}</button>
        <button class="btn btn--ghost" type="button" data-close>Cancelar</button></div></form>`;
    const form = $('form', panel);
    form.addEventListener('submit', async e => {
      e.preventDefault();
      let ok = true;
      ['nombre', 'contacto'].forEach(id => {
        const wrap = $(`[data-field="${id}"]`, form), input = $('input', wrap), msg = $('.field__msg', wrap);
        const bad = input.value.trim().length < (id === 'nombre' ? 2 : 3);
        wrap.classList.toggle('field--error', bad);
        msg.hidden = !bad; msg.textContent = bad ? (id === 'nombre' ? 'Escribe tu nombre.' : 'Déjanos un correo, teléfono o Instagram.') : '';
        if (bad) ok = false;
      });
      if (!ok) return;
      const d = Object.fromEntries(new FormData(form));
      const destino = [d.espacio || cfg.destino, d.artista].filter(Boolean).join(' con ');
      const btn = $('button[type=submit]', form); btn.disabled = true;
      try {
        const r = await fetch('/api/solicitudes', { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ modo: mode, nombre: d.nombre, contacto: d.contacto, rol: d.rol, destino, mensaje: d.mensaje }) });
        if (!r.ok) throw new Error();
        panel.innerHTML = `<div class="done"><span class="done__ic">${ICON.check}</span>
          <h2 class="sheet__title">¡Listo!</h2><p class="sheet__intro">${esc(cfg.ok)}</p>
          <button class="btn" type="button" data-close>Cerrar</button></div>`;
      } catch {
        const err = $('.form-error', form); err.hidden = false; err.textContent = 'No pudimos enviar el formulario. Revisa tu conexión e intenta de nuevo.'; btn.disabled = false;
      }
    });
    $('#dlg-collab').showModal();
    $('input', form).focus();
  }

  /* ---------- Opinión / comentarios (botón flotante) ---------- */
  function feedbackForm() {
    const stars = Array.from({ length: 5 }, (_, i) => i + 1)
      .map(n => `<button type="button" class="star js-star" data-n="${n}" aria-label="${n} de 5 estrellas">${ICON.star}</button>`).join('');
    return `
      <div class="sheet__head"><h2 class="sheet__title">Danos tu opinión</h2>
        <button type="button" class="icon-btn" data-close aria-label="Cerrar">${ICON.close}</button></div>
      <p class="sheet__intro">Nos ayuda a mejorar Atelier. Cuéntanos qué tal te fue navegando el sitio.</p>
      <form novalidate>
        <div class="starpicker" role="radiogroup" aria-label="Calificación">${stars}</div>
        <p class="field__msg" data-star-msg hidden>Elige una calificación.</p>
        ${field('mensaje', 'Tu comentario', '<textarea id="f-mensaje" name="mensaje" placeholder="Qué te gustó o qué mejorarías"></textarea>')}
        ${field('nombre', 'Tu nombre (opcional)', '<input id="f-nombre" name="nombre" autocomplete="name">')}
        <p class="form-error" hidden></p>
        <div class="form-actions"><button class="btn" type="submit">Enviar comentario</button>
        <button class="btn btn--ghost" type="button" data-close>Cancelar</button></div>
      </form>`;
  }

  function openFeedback() {
    const panel = $('#feedback-panel');
    panel.innerHTML = feedbackForm();
    let rating = 0;
    const picker = $('.starpicker', panel);
    const paint = n => $$('.js-star', picker).forEach(b => b.classList.toggle('is-on', +b.dataset.n <= n));
    picker.addEventListener('click', e => {
      const b = e.target.closest('.js-star'); if (!b) return;
      rating = +b.dataset.n; paint(rating); $('[data-star-msg]', panel).hidden = true;
    });
    const form = $('form', panel);
    form.addEventListener('submit', async e => {
      e.preventDefault();
      let ok = true;
      if (!rating) { $('[data-star-msg]', panel).hidden = false; ok = false; }
      const wrap = $('[data-field="mensaje"]', form), ta = $('textarea', wrap), msg = $('.field__msg', wrap);
      const bad = ta.value.trim().length < 3;
      wrap.classList.toggle('field--error', bad);
      msg.hidden = !bad; msg.textContent = bad ? 'Cuéntanos un poco más.' : '';
      if (bad) ok = false;
      if (!ok) return;
      const d = Object.fromEntries(new FormData(form));
      const btn = $('button[type=submit]', form); btn.disabled = true;
      try {
        const r = await fetch('/api/comentarios', { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ calificacion: rating, mensaje: d.mensaje, nombre: d.nombre, pagina: location.pathname }) });
        if (!r.ok) throw new Error();
        panel.innerHTML = `<div class="done"><span class="done__ic">${ICON.check}</span>
          <h2 class="sheet__title">¡Gracias!</h2><p class="sheet__intro">Tu opinión nos ayuda a mejorar Atelier.</p>
          <button class="btn" type="button" data-close>Cerrar</button></div>`;
      } catch {
        const err = $('.form-error', form); err.hidden = false; err.textContent = 'No pudimos enviar tu comentario. Revisa tu conexión e intenta de nuevo.'; btn.disabled = false;
      }
    });
    $('#dlg-feedback').showModal();
  }

  /* ---------- Búsqueda en vivo ---------- */
  let searchTimer;
  const sInput = $('#search-input'), sBox = $('#search-results');
  const group = (title, items) => items.length ? `<h5>${title}</h5>` + items.map(i =>
    `<a class="res" href="${i.url}"><img src="${i.image}" alt=""><div><b>${esc(i.name)}</b><span>${esc(i.sub)}</span></div></a>`).join('') : '';
  sInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = sInput.value.trim();
    if (q.length < 2) { sBox.innerHTML = ''; return; }
    searchTimer = setTimeout(async () => {
      try {
        const r = await (await fetch('/api/buscar?q=' + encodeURIComponent(q))).json();
        const html = group('Eventos', r.events) + group('Artistas', r.artists) + group('Espacios', r.spaces);
        sBox.innerHTML = html || `<p class="results__none">No encontramos nada para “${esc(q)}”.</p>`;
      } catch { sBox.innerHTML = '<p class="results__none">La búsqueda no está disponible ahora.</p>'; }
    }, 180);
  });

  /* ---------- Filtros de listas (eventos, artistas, espacios) ---------- */
  $$('.js-filterable').forEach(box => {
    const chips = $$('.chip--btn', box), input = $('.js-filter-q', box), items = $$('.js-item', box), empty = $('.empty', box);
    let cat = 'todo';
    const apply = () => {
      const q = norm(input?.value.trim());
      let n = 0;
      items.forEach(it => {
        const show = (cat === 'todo' || it.dataset.cat === cat) && (!q || it.dataset.search.includes(q));
        it.hidden = !show; if (show) n++;
      });
      empty.hidden = n > 0; empty.textContent = box.dataset.empty || '';
    };
    const pick = value => {
      cat = value;
      chips.forEach(c => { const on = c.dataset.value === value; c.classList.toggle('is-on', on); c.setAttribute('aria-pressed', on); });
      apply();
    };
    chips.forEach(c => c.addEventListener('click', () => pick(c.dataset.value)));
    input?.addEventListener('input', apply);
    const pre = new URLSearchParams(location.search).get('cat');
    if (pre && chips.some(c => c.dataset.value === pre)) pick(pre);
  });

  /* ---------- Clics delegados ---------- */
  document.addEventListener('click', async e => {
    const t = e.target;
    const save = t.closest('.js-save');
    if (save) {
      e.preventDefault();
      toggleSave(save);
      if (save.hasAttribute('data-remove')) { save.closest('.saved').remove(); if (!$('.saved')) openSaved(); }
      return;
    }
    const collab = t.closest('.js-collab');
    if (collab) { openCollab(collab.dataset.mode, { artist: collab.dataset.artist, space: collab.dataset.space }); return; }
    if (t.closest('.js-open-search')) { $('#dlg-search').showModal(); sInput.focus(); return; }
    if (t.closest('.js-open-saved')) { openSaved(); return; }
    if (t.closest('.js-open-feedback')) { openFeedback(); return; }
    const share = t.closest('.js-share');
    if (share) {
      const data = { title: share.dataset.title, text: share.dataset.text, url: location.href };
      try {
        if (navigator.share) await navigator.share(data);
        else { await navigator.clipboard.writeText(location.href); toast('Enlace copiado'); }
      } catch { /* el usuario canceló */ }
      return;
    }
    const zoom = t.closest('.js-zoom');
    if (zoom) { $('#zoom-img').src = zoom.dataset.src; $('#zoom-img').alt = zoom.dataset.title; $('#zoom-cap').textContent = zoom.dataset.title; $('#dlg-zoom').showModal(); }
  });

  syncSaved();
})();
