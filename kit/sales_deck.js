/* WF Sales Deck System — deck runtime
   Keyboard: ←/→ ↑/↓ space | Home/End | F fullscreen
   Builds side progress dots from .slide sections; adds slide counter.
   FX: currency-matrix rain canvases  <canvas class="fx-matrix" data-color="pink|lavender">
*/
(function () {
  /* ?only=<id or 1-based index> renders a single slide full-viewport
     (faithful capture for verification / per-slide PDF export) */
  const only = new URLSearchParams(location.search).get('only');
  if (only) {
    document.querySelectorAll('.slide').forEach((s, i) => {
      if (s.id !== only && String(i + 1) !== only) s.remove();
    });
  }

  const slides = Array.from(document.querySelectorAll('.slide'));
  if (!slides.length) return;

  /* --- progress dots --- */
  const nav = document.createElement('nav');
  nav.className = 'deck-nav';
  slides.forEach((s, i) => {
    if (!s.id) s.id = 's' + (i + 1);
    const a = document.createElement('a');
    a.href = '#' + s.id;
    nav.appendChild(a);
  });
  document.body.appendChild(nav);
  const dots = Array.from(nav.children);

  /* --- counter --- */
  const counter = document.createElement('div');
  counter.className = 'slide-count';
  document.body.appendChild(counter);

  let cur = 0;
  function setActive(i) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    dots.forEach((d, j) => d.classList.toggle('on', j === cur));
    counter.textContent = (cur + 1) + ' / ' + slides.length;
    const light = slides[cur].dataset.mode === 'light';
    nav.classList.toggle('nav-dark', light);
    counter.style.color = light ? 'rgba(19,0,45,.45)' : 'rgba(255,255,255,.5)';
  }
  function go(i) {
    setActive(i);
    slides[cur].scrollIntoView({ behavior: 'smooth' });
  }

  /* --- observe scroll position --- */
  const io = new IntersectionObserver(
    (es) => es.forEach((e) => { if (e.isIntersecting) setActive(slides.indexOf(e.target)); }),
    { threshold: 0.55 }
  );
  slides.forEach((s) => io.observe(s));

  /* --- keys --- */
  addEventListener('keydown', (e) => {
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(cur + 1); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); go(cur - 1); }
    else if (e.key === 'Home') go(0);
    else if (e.key === 'End') go(slides.length - 1);
    else if (e.key.toLowerCase() === 'f') {
      document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
    }
  });
  setActive(0);

  /* --- currency matrix rain --- */
  document.querySelectorAll('canvas.fx-matrix').forEach((cv) => {
    const ctx = cv.getContext('2d');
    const glyphs = '01¥£$€¢₩3581'.split('');
    const tint = cv.dataset.color === 'lavender' ? '221,192,255' : '255,110,142';
    let cols = [], W, H, size;
    function resize() {
      W = cv.width = cv.offsetWidth * devicePixelRatio;
      H = cv.height = cv.offsetHeight * devicePixelRatio;
      size = Math.max(14, W / 46);
      cols = Array.from({ length: Math.floor(W / size) }, () => Math.random() * H);
    }
    resize(); addEventListener('resize', resize);
    (function tick() {
      ctx.clearRect(0, 0, W, H);
      ctx.font = size * 0.72 + 'px Poppins, monospace';
      cols.forEach((y, i) => {
        for (let t = 0; t < 14; t++) {
          const a = Math.max(0, 0.34 - t * 0.026);
          ctx.fillStyle = 'rgba(' + tint + ',' + a + ')';
          ctx.fillText(glyphs[(i * 7 + t * 3 + ((y / size) | 0)) % glyphs.length], i * size, y - t * size);
        }
        cols[i] = y > H + 14 * size ? 0 : y + size * 0.16;
      });
      requestAnimationFrame(tick);
    })();
  });
})();
