/* Small, self-contained teaching models. Research fitting and MPFR exports live
 * in C++; the browser exposes their ideas without a plotting dependency. */
(() => {
  'use strict';
  const BLUE = '#3e6a89', ORANGE = '#b86632', RULE = '#d8d4ca';
  const svgNS = 'http://www.w3.org/2000/svg';
  const scientific = value => value === 0 ? '0' : value.toExponential(2);
  const get = id => document.getElementById(id);
  function node(tag, attrs = {}, content) {
    const result = document.createElementNS(svgNS, tag);
    Object.entries(attrs).forEach(([key, value]) => result.setAttribute(key, value));
    if (content !== undefined) result.textContent = content;
    return result;
  }
  // ViewBox coordinates let the plot resize without a bitmap or a canvas ratio.
  function chart(svg, {xmin = 0, xmax = 1, ymin, ymax, title, xlabel, series, shade, marker}) {
    svg.replaceChildren();
    svg.append(node('title', {}, title));
    const H = Number(svg.getAttribute('viewBox').split(' ')[3]);
    const left = 70, right = 658, top = 28, bottom = H - 42;
    if (ymin === ymax) { ymin -= 1; ymax += 1; }
    const X = x => left + (x - xmin) / (xmax - xmin) * (right - left);
    const Y = y => bottom - (y - ymin) / (ymax - ymin) * (bottom - top);
    const label = (x, y, text, anchor = 'start', size = 11) => svg.append(node('text', {
      x, y, fill: '#62686b', 'font-size': size, 'font-family': 'system-ui, sans-serif', 'text-anchor': anchor
    }, text));
    if (shade) svg.append(node('rect', {x: X(shade[0]), y: top, width: Math.max(2, X(shade[1])-X(shade[0])), height: bottom-top, fill: '#e1e9ed'}));
    for (let i = 0; i <= 4; ++i) {
      const y = ymin + (ymax - ymin) * i / 4;
      svg.append(node('path', {d: `M${left},${Y(y)}H${right}`, stroke: RULE, fill: 'none'}));
      label(left - 8, Y(y) + 4, Math.abs(y) >= 1000 || (Math.abs(y) < .001 && y !== 0) ? y.toExponential(1) : Number(y.toPrecision(3)).toString(), 'end');
      const x = xmin + (xmax-xmin)*i/4;
      label(X(x), bottom+20, Number(x.toPrecision(4)).toString(), 'middle');
    }
    series.forEach(line => svg.append(node('path', {d: line.points.map(([x,y],i) => `${i ? 'L' : 'M'}${X(x).toFixed(2)},${Y(y).toFixed(2)}`).join(' '), stroke: line.color, 'stroke-width': 1.8, 'stroke-dasharray': line.dash || '', fill: 'none', 'stroke-linejoin': 'round'})));
    if (marker !== undefined) svg.append(node('path', {d: `M${X(marker)},${top}V${bottom}`, stroke: '#8d765d', 'stroke-dasharray': '3 4', fill: 'none'}));
    label(left, 16, title, 'start', 12);
    label((left+right)/2, H-4, xlabel, 'middle');
  }
  function metric(value, name) { return `<div><strong>${value}</strong><span>${name}</span></div>`; }
  const {midpointQuadratic} = globalThis.SfuMath;
  function reduction() {
    const root = get('reduction-widget');
    if (!root) return;
    const bounds = [2, 1, .5, .25];
    const labels = ['[−2, 2]', '[−1, 1]', '[−½, ½]', '[−¼, ¼]'];
    const button = get('reduction-play'), status = get('reduction-step');
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const hold = 1500, transition = 1000;
    const duration = (bounds.length - 1) * (hold + transition);
    let frame = null, elapsed = 0, lastDraw = -Infinity, announced = -1;
    function draw(bound, step) {
      const exact = [], estimate = [];
      for (let i = 0; i <= 256; ++i) {
        const x = -bound + 2 * bound * i / 256;
        exact.push([x, 2**x]);
        // The expansion point stays at zero; only the visible interval changes.
        estimate.push([x, midpointQuadratic(-bound, 2 * bound, x)]);
      }
      const minimum = Math.min(...exact.map(p => p[1]), ...estimate.map(p => p[1]));
      const maximum = Math.max(...exact.map(p => p[1]), ...estimate.map(p => p[1]));
      const padding = (maximum - minimum) * .08;
      chart(get('reduction-curve'), {
        xmin: -bound, xmax: bound, ymin: minimum - padding, ymax: maximum + padding,
        title: 'Same quadratic · both axes rescale', xlabel: 'x', marker: 0,
        series: [{points: exact, color: BLUE}, {points: estimate, color: ORANGE, dash: '5 3'}]
      });
      // Announce settled views, rather than every intermediate animation frame.
      if (step !== announced) {
        status.textContent = `${step + 1} of 4 · ${labels[step]}`;
        get('reduction-curve').setAttribute('aria-label', `Exponential and a fixed quadratic on ${labels[step]}`);
        announced = step;
      }
    }
    function stop() {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
      button.textContent = motion.matches ? (elapsed >= duration ? 'Restart' : 'Next interval') :
        (elapsed >= duration ? 'Replay' : 'Play');
    }
    button.addEventListener('click', () => {
      if (frame !== null) { stop(); return; }
      if (motion.matches) {
        const step = elapsed >= duration ? 0 : Math.min(3, Math.floor(elapsed / (hold + transition)) + 1);
        elapsed = step * (hold + transition);
        draw(bounds[step], step); stop(); return;
      }
      if (elapsed >= duration) elapsed = 0;
      const start = performance.now() - elapsed;
      button.textContent = 'Pause';
      function tick(now) {
        elapsed = Math.min(duration, now - start);
        const step = Math.min(3, Math.floor(elapsed / (hold + transition)));
        const progress = Math.max(0, (elapsed - step * (hold + transition) - hold) / transition);
        // Equal steps in log scale make each halving feel like the same zoom.
        const eased = progress * progress * (3 - 2 * progress);
        const bound = bounds[step] * 2**(-eased);
        if (now - lastDraw >= 40 || elapsed >= duration) {
          draw(bound, step); lastDraw = now;
        }
        if (elapsed >= duration) { stop(); return; }
        frame = requestAnimationFrame(tick);
      }
      frame = requestAnimationFrame(tick);
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    motion.addEventListener('change', () => {
      stop();
      const step = Math.min(3, Math.floor(elapsed / (hold + transition)));
      elapsed = step * (hold + transition); draw(bounds[step], step); stop();
    });
    draw(bounds[0], 0); stop();
  }
  // Initialize after the document has parsed its content controls.
  function start() { reduction(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();
