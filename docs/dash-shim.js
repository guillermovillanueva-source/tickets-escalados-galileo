// Versión mínima de la API "dash" del dashboard original, para correr la misma
// página como sitio estático: lee data.json, calcula y redibuja con los filtros.
(function () {
  const sources = {};          // id -> {status, data}
  const calcs = [];            // [{id, inputs, fn}]
  const calcOut = {};          // id -> {status, data}
  const draws = [];            // [{name, fn}]
  const onDataFns = [];
  let defaults = {};
  let params = {};

  function compute() {
    for (const c of calcs) {
      const ins = c.inputs.map((i) => api.data(i));
      const bad = ins.find((d) => d.status !== 'ok');
      if (bad) { calcOut[c.id] = { status: bad.status, data: null }; continue; }
      try {
        calcOut[c.id] = { status: 'ok', data: c.fn(...ins.map((d) => d.data)) };
      } catch (e) {
        console.error('Cálculo', c.id, e);
        calcOut[c.id] = { status: 'error', data: null, message: String(e) };
      }
    }
  }

  function render() {
    compute();
    for (const f of onDataFns) { try { f(); } catch (e) { console.error(e); } }
    for (const d of draws) {
      for (const el of document.querySelectorAll(`[data-draw="${d.name}"]`)) {
        try { d.fn(el); } catch (e) { console.error('Dibujo', d.name, e); }
      }
    }
  }

  let timer = null;
  function schedule() { clearTimeout(timer); timer = setTimeout(render, 0); }

  const api = {
    colors: ['var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)'],
    data(id) {
      if (id in calcOut) return calcOut[id];
      return sources[id] || { status: 'loading', data: [] };
    },
    calc(id, { inputs, fn }) { calcs.push({ id, inputs, fn }); },
    loader() {},
    draw(name, fn) { draws.push({ name, fn: typeof fn === 'function' ? fn : (el) => fn.update && fn.update(el) }); },
    onData(fn) { onDataFns.push(fn); },
    params() { return { ...params }; },
    setParams(o) { params = { ...params, ...o }; for (const k in params) if (params[k] == null) params[k] = ''; schedule(); },
    resetParams() { params = { ...defaults }; schedule(); },
    setLink() {}, refresh() {},
    _setDefaults(d) { defaults = { ...d }; params = { ...d }; },
    _setSource(id, v) { sources[id] = v; },
    _render: schedule,
  };
  window.dash = api;

  document.addEventListener('DOMContentLoaded', () => {
    render();
    fetch('data.json', { cache: 'no-store' })
      .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then((j) => {
        api._setSource('tickets', { status: 'ok', data: j.tickets || [] });
        api._setSource('canal', { status: 'ok', data: j.canal || [] });
        for (const el of document.querySelectorAll('[data-generado]')) el.textContent = j.generado || '—';
        render();
      })
      .catch((e) => {
        console.error(e);
        api._setSource('tickets', { status: 'error', data: [] });
        api._setSource('canal', { status: 'error', data: [] });
        for (const el of document.querySelectorAll('[data-generado]')) el.textContent = 'todavía no hay datos (corre la Action "Actualizar datos")';
        render();
      });
    let w = window.innerWidth;
    window.addEventListener('resize', () => { if (window.innerWidth !== w) { w = window.innerWidth; schedule(); } });
  });
})();
