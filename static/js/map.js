/* ATELIER · map.js
   Mapa cultural con Leaflet. Lo usan tres lugares:
   - /mapa (completo: filtros por categoría, mes y lista lateral)
   - Home (mapa pequeño)
   - Detalle de evento y de espacio (un solo punto)
   Los puntos vienen de /api/puntos (ver app.py). */
(() => {
  if (!window.L) return;
  const CENTER = [19.2528, -99.6053];             // Metepec, Estado de México
  const TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = t => String(t ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const svg = p => `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${p}</svg>`;
  const I = {
    cal: svg('<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M8 3v4M16 3v4M3.5 10h17"/>'),
    clock: svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    pin: svg('<path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>'),
    x: svg('<path d="M6 6l12 12M18 6 6 18"/>'),
  };

  $$('[data-map]').forEach(init);

  async function init(stage) {
    const canvas = $('.mapstage__canvas', stage), card = $('.mapcard', stage);
    const isPage = stage.hasAttribute('data-page');
    let points = [];
    try { points = await (await fetch(stage.dataset.endpoint)).json(); } catch { return; }

    const map = L.map(canvas, { center: CENTER, zoom: +stage.dataset.zoom || 15, scrollWheelZoom: stage.dataset.wheel !== 'off', zoomControl: true });
    L.tileLayer(TILES, { attribution: ATTR, maxZoom: 19, subdomains: 'abcd' }).addTo(map);
    const layer = L.layerGroup().addTo(map);
    setTimeout(() => map.invalidateSize(), 250);

    const state = { cat: 'todo', month: $('#map-months .is-on')?.dataset.month || 'todos', selected: null };
    const markers = new Map();

    const visible = p => {
      if (!isPage) return true;
      const catOk = state.cat === 'todo' ? true : state.cat === 'eventos' ? p.kind === 'event'
        : state.cat === 'espacios' ? p.kind === 'space' : (p.kind === 'event' && p.category === state.cat);
      const monthOk = state.month === 'todos' || p.kind === 'space' || p.month === state.month;
      return catOk && monthOk;
    };

    function icon(p) {
      return L.divIcon({ className: 'pinwrap', iconSize: [30, 30], iconAnchor: p.kind === 'event' ? [15, 36] : [15, 30],
        html: `<span class="pin pin--${p.kind}" style="--c:${p.color}"><i></i></span>` });
    }
    const pinEl = id => markers.get(id)?.getElement()?.querySelector('.pin');

    function showCard(p) {
      const meta = p.kind === 'event'
        ? `<span>${I.cal}${esc(p.date_label)}</span><span>${I.clock}${esc(p.time)} h</span><span>${I.pin}${esc(p.place)}</span>`
        : `<span>${I.pin}${esc(p.place)}, Metepec</span>`;
      card.innerHTML = `
        <div class="mapcard__img"><img src="${p.image}" alt=""></div>
        <div class="mapcard__body">
          <span class="chip" style="--c:${p.color}"><i class="chip__dot"></i>${esc(p.category_label)}</span>
          <h3 class="mapcard__title">${esc(p.name)}</h3>
          <div class="mapcard__meta">${meta}</div>
        </div>
        <div class="mapcard__cta"><a class="btn btn--sm" href="${p.url}">${p.kind === 'event' ? 'Ver evento' : 'Ver espacio'}</a></div>
        <button class="icon-btn mapcard__x" type="button" aria-label="Cerrar tarjeta">${I.x}</button>`;
      card.hidden = false;
      $('.mapcard__x', card).addEventListener('click', () => select(null));
    }

    function select(p, { pan = true } = {}) {
      if (state.selected) pinEl(state.selected.id)?.classList.remove('is-active');
      state.selected = p;
      $$('.mitem').forEach(el => el.classList.toggle('is-active', !!p && el.dataset.id === p.id));
      if (!p) { card.hidden = true; return; }
      pinEl(p.id)?.classList.add('is-active');
      showCard(p);
      if (pan) map.flyTo([p.lat, p.lng], Math.max(map.getZoom(), 15), { duration: .6 });
    }

    function render({ fit = true } = {}) {
      layer.clearLayers(); markers.clear();
      const vis = points.filter(visible);
      vis.forEach(p => {
        const m = L.marker([p.lat, p.lng], { icon: icon(p), title: p.name, keyboard: true, riseOnHover: true }).addTo(layer);
        m.on('click', () => select(p));
        markers.set(p.id, m);
      });
      if (fit && vis.length) {
        if (vis.length === 1) map.setView([vis[0].lat, vis[0].lng], +stage.dataset.zoom || 16);
        else map.fitBounds(L.latLngBounds(vis.map(p => [p.lat, p.lng])), { padding: [70, 70], maxZoom: 16 });
      }
      if (state.selected && !vis.includes(state.selected)) select(null);
      else if (state.selected) setTimeout(() => pinEl(state.selected.id)?.classList.add('is-active'), 0);
      if (isPage) renderList(vis);
    }

    function renderList(vis) {
      const list = $('#map-list'), count = $('#map-count');
      count.textContent = vis.length === 1 ? '1 punto en el mapa' : `${vis.length} puntos en el mapa`;
      list.innerHTML = vis.length ? vis.map(p => `
        <button class="mitem ${state.selected?.id === p.id ? 'is-active' : ''}" type="button" data-id="${p.id}" style="--c:${p.color}">
          <img src="${p.image}" alt="">
          <span><span class="mitem__name">${esc(p.name)}</span>
          <span class="mitem__sub"><i></i>${p.kind === 'event' ? esc(p.date_label) + ', ' + esc(p.time) + ' h' : esc(p.category_label)}</span></span>
        </button>`).join('') : '<p class="empty">No hay puntos con estos filtros. Prueba otro mes o categoría.</p>';
      $$('.mitem', list).forEach(el => el.addEventListener('click', () => {
        select(points.find(p => p.id === el.dataset.id));
        if (matchMedia('(max-width: 979px)').matches) stage.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }));
    }

    if (isPage) {
      const pick = (sel, attr, value, cb) => $$(sel).forEach(b => {
        const on = b.dataset[attr] === value; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on);
      });
      $$('#map-cats button').forEach(b => b.addEventListener('click', () => {
        state.cat = b.dataset.cat; pick('#map-cats button', 'cat', state.cat); render();
      }));
      $$('#map-months button').forEach(b => b.addEventListener('click', () => {
        state.month = b.dataset.month; pick('#map-months button', 'month', state.month); render();
      }));
    }

    // Enlace directo: /mapa?foco=event:slug
    const foco = new URLSearchParams(location.search).get('foco');
    const target = foco && points.find(p => p.id === foco);
    if (target && isPage && target.month) { state.month = target.month; $$('#map-months button').forEach(b => { const on = b.dataset.month === target.month; b.classList.toggle('is-on', on); b.setAttribute('aria-pressed', on); }); }
    render();
    if (target) setTimeout(() => select(target), 350);
    else if (stage.hasAttribute('data-open') && points[0]) setTimeout(() => select(points[0], { pan: false }), 350);
  }
})();
