import { geometry, thresholdMask } from './science.mjs';

const $ = (id) => document.getElementById(id);
const error = (message) => { $('load-error').hidden = false; $('load-error').textContent = message; };
const fixed = (value, digits = 3) => Number(value).toFixed(digits);
let synthetic;
let selected;
let earthDisplayPromise;
const systemTheme = matchMedia('(prefers-color-scheme: dark)');
document.querySelectorAll('figure:not(.hero-image) img').forEach((figure) => {
  const link = document.createElement('a');
  link.className = 'figure-link';
  link.href = figure.src;
  link.setAttribute('aria-label', `Open full-size figure: ${figure.alt}`);
  const media = figure.parentElement.tagName === 'PICTURE' ? figure.parentElement : figure;
  media.before(link); link.append(media);
});

function setFigure(id, path, alt) {
  const figure = $(id);
  figure.src = path; figure.alt = alt;
  figure.closest('a').href = path;
  figure.closest('a').setAttribute('aria-label', `Open full-size figure: ${alt}`);
}
try { const saved = localStorage.getItem('sar-theme'); if (saved) document.documentElement.dataset.theme = saved; } catch { /* Storage is optional. */ }
$('theme').addEventListener('click', () => {
  const current = document.documentElement.dataset.theme || (systemTheme.matches ? 'dark' : 'light');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('sar-theme', next); } catch { /* Continue without persistence. */ }
  if (selected) drawProfile(selected);
});
systemTheme.addEventListener('change', () => { if (selected) drawProfile(selected); });

function updateGeometry() {
  const angle = Number($('angle').value);
  const result = geometry(angle);
  const targetX = 140 + 250 * Math.tan(angle * Math.PI / 180);
  $('angle-value').textContent = `${angle}°`;
  $('ground-width').replaceChildren(document.createTextNode(`${fixed(result.groundWidthM, 2)} `));
  const units = document.createElement('small'); units.textContent = 'm'; $('ground-width').append(units);
  $('slant-line').setAttribute('d', `M140 65L${targetX} 315`);
  $('ground-target').setAttribute('cx', targetX);
  $('slant-label').textContent = `R = ${fixed(result.slantM / 1000, 2)} km`;
  $('slant-label').setAttribute('x', 150 + (targetX - 140) / 2);
  $('ground-label').textContent = `Ground range = ${fixed(result.groundM / 1000, 2)} km`;
}
$('angle').addEventListener('input', updateGeometry); updateGeometry();

const captions = {
  scene: ['Synthetic point and extended-scene scatterer coordinates in metres.', 'Synthetic scene: three isolated scatterers and a patch with seeded random phases. Amplitude is arbitrary, not calibrated reflectivity.'],
  raw: ['Power of simulated complex radar echoes by pulse and fast-time sample.', 'Full synthetic scene raw echoes: delayed 40 MHz chirps sampled at 160 MHz. Color shows complex magnitude squared; phase is preserved in the numerical record.'],
  compressed: ['Synthetic range-compressed point-target power by pulse and sample.', 'Full synthetic scene after linear convolution with the reversed conjugate transmit chirp. Normalized by chirp energy; no circular wraparound.'],
  extended: ['Focused synthetic point targets and an extended scatterer patch.', 'Extended scene after exact-delay backprojection. The scene, raw and compressed views share this input. The quality lab separately isolates one target for uncontaminated impulse metrics.'],
};
document.querySelectorAll('[data-stage]').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('[data-stage]').forEach((other) => other.setAttribute('aria-pressed', String(other === button)));
  const key = button.dataset.stage;
  setFigure('stage-image', `assets/${key}.png`, captions[key][0]);
  $('stage-caption').textContent = captions[key][1];
}));

async function getJSON(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status}).`);
  return response.json();
}

function drawProfile(item) {
  const canvas = $('profile'), ctx = canvas.getContext('2d');
  canvas.width = Math.round(canvas.getBoundingClientRect().width);
  canvas.height = canvas.width < 500 ? 230 : 300;
  const css = getComputedStyle(document.documentElement);
  const w = canvas.width, h = canvas.height, left = 66, right = 20, top = 20, bottom = 48;
  const xmin = -2, xmax = 2, ymin = -45, ymax = 0;
  const sx = (x) => left + (x - xmin) / (xmax - xmin) * (w - left - right);
  const sy = (y) => top + (ymax - y) / (ymax - ymin) * (h - top - bottom);
  ctx.fillStyle = css.getPropertyValue('--bg'); ctx.fillRect(0, 0, w, h);
  ctx.font = canvas.width < 500 ? '11px monospace' : '14px monospace'; ctx.fillStyle = css.getPropertyValue('--muted');
  ctx.strokeStyle = css.getPropertyValue('--line'); ctx.lineWidth = 1;
  for (let db = -40; db <= 0; db += 10) { ctx.beginPath(); ctx.moveTo(left, sy(db)); ctx.lineTo(w - right, sy(db)); ctx.stroke(); ctx.fillText(String(db), 23, sy(db) + 5); }
  for (let x = -2; x <= 2; x++) ctx.fillText(String(x), sx(x) - 6, h - 27);
  ctx.fillText('Along-track x [m]', w / 2 - 74, h - 7);
  ctx.save(); ctx.translate(15, h / 2 + 48); ctx.rotate(-Math.PI / 2); ctx.fillText('Relative power [dB]', 0, 0); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.rect(left, top, w - left - right, h - top - bottom); ctx.clip();
  for (const [data, color] of [[synthetic.cases[0], css.getPropertyValue('--muted')], [item, css.getPropertyValue('--accent')]]) {
    ctx.strokeStyle = color; ctx.lineWidth = data === item ? 2.5 : 1.4; ctx.beginPath();
    data.profile_x_m.forEach((x, i) => { const y = data.azimuth_profile_db[i]; if (i === 0) ctx.moveTo(sx(x), sy(y)); else ctx.lineTo(sx(x), sy(y)); });
    ctx.stroke();
  }
  ctx.restore();
}

function updateCase() {
  selected = synthetic.cases.find((item) => item.id === $('experiment').value);
  const { metrics, gate, performance } = selected.manifest;
  const failed = Object.entries(gate.checks).filter(([, passed]) => !passed).map(([key]) => key.replaceAll('_', ' '));
  $('gate-status').textContent = gate.passed ? 'Accepted by the educational quality gates' : `Flagged: ${failed.join(', ')}`;
  const values = [
    ['Azimuth width', `${fixed(metrics.azimuth.width_m)} m`],
    ['Ground-range width', `${fixed(metrics.ground_range.width_m)} m`],
    ['Localization error', `${fixed(metrics.localization_m, 2)} m`],
    ['Azimuth PSLR', `${fixed(metrics.azimuth.pslr_db, 2)} dB`],
    ['Azimuth ISLR', `${fixed(metrics.azimuth.islr_db, 2)} dB`],
    ['Peak power', fixed(metrics.peak_power, 4)],
  ];
  $('quality-metrics').replaceChildren(...values.map(([name, value]) => {
    const row = document.createElement('div'), term = document.createElement('dt'), definition = document.createElement('dd');
    term.textContent = name; definition.textContent = value; row.append(term, definition); return row;
  }));
  setFigure('quality-image', `assets/${selected.id}.png`, `${selected.label}: generated synthetic focused point-target response with metre axes and peak-normalized dB scale.`);
  $('quality-caption').textContent = `${selected.label}. Peak normalization is per image; peak power above uses the common matched-filter normalization.`;
  $('performance').textContent = `Recorded compression + focusing: ${fixed(performance.compression_and_focus_s, 3)} s. Sampled peak RSS: ${fixed(performance.sampled_peak_rss_mib, 1)} MiB; increment above starting RSS: ${fixed(performance.incremental_peak_rss_mib, 1)} MiB. ${performance.os}, ${performance.hardware}, Python ${performance.python}, NumPy ${performance.numpy}. Measurements vary with machine and cache state.`;
  drawProfile(selected);
}
$('experiment').addEventListener('change', updateCase);
$('corrupt').addEventListener('click', () => {
  if (!synthetic) return;
  $('corrupt-output').hidden = false;
  $('corrupt-output').textContent = JSON.stringify(synthetic.corrupted_input, null, 2);
  $('corrupt').textContent = 'Recorded rejection shown';
});

$('earth-method').addEventListener('change', () => {
  const method = $('earth-method').value;
  for (const period of ['before', 'after']) {
    setFigure(`earth-${period}`, `assets/earth-${period}${method === 'backscatter' ? '' : `-${method}`}.png`, `${period === 'before' ? 'December 2019' : 'July 2020'}: ${method === 'backscatter' ? 'VV gamma-zero intensity in dB' : `${method} candidate-water classification; not confirmed flooding`}, with kilometre axes.`);
  }
});

async function updateLiveThreshold() {
  const threshold = Number($('threshold').value);
  $('threshold-value').textContent = `${threshold} dB`;
  $('live-result').textContent = 'Loading display grid…';
  try {
    earthDisplayPromise ||= getJSON('assets/earth-display.json');
    const display = await earthDisplayPromise;
    // A later control event owns the latest rendering.
    if (threshold !== Number($('threshold').value)) return;
    const fractions = [];
    for (const [index, period] of ['before', 'after'].entries()) {
      const result = thresholdMask(display.db[index], display.valid, threshold);
      fractions.push(result.fraction);
      const ctx = $(`live-${period}`).getContext('2d');
      const image = ctx.createImageData(256, 256);
      result.mask.forEach((row, y) => row.forEach((classification, x) => {
        const offset = (y * 256 + x) * 4;
        const gray = Math.max(30, Math.min(235, (display.db[index][y][x] + 30) / 30 * 235));
        const rgb = classification === 1 ? [110, 162, 117] : classification === -1 ? [50, 50, 50] : [gray, gray, gray];
        image.data.set([...rgb, 255], offset);
      }));
      ctx.putImageData(image, 0, 0);
    }
    $('live-result').textContent = `Live 40 m display grid: December ${(fractions[0] * 100).toFixed(1)}%, July ${(fractions[1] * 100).toFixed(1)}% candidate water. Change ${((fractions[1] - fractions[0]) * 100).toFixed(1)} percentage points. Green = below threshold; gray = other pixels. North up, 10.24 km square.`;
  } catch (reason) { $('live-result').textContent = String(reason); earthDisplayPromise = undefined; }
}
$('threshold').addEventListener('input', updateLiveThreshold);

// Defer experiment records until the laboratory is near the viewport.
// Initial rendering only needs static imagery and the live geometry formula.
await new Promise((resolve) => {
  const observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) { observer.disconnect(); resolve(); }
  }, { rootMargin: '300px' });
  observer.observe($('quality'));
});

try {
  [synthetic] = await Promise.all([getJSON('assets/synthetic.json')]);
  $('experiment').replaceChildren(...synthetic.cases.map((item) => { const option = document.createElement('option'); option.value = item.id; option.textContent = item.label; return option; }));
  $('experiment').disabled = false; updateCase();
  const earth = await getJSON('assets/earth.json');
  const table = document.createElement('table');
  table.innerHTML = '<caption>Measured candidate-water area on the 10 m common grid. No reference-label accuracy is implied.</caption><thead><tr><th scope="col">Method</th><th scope="col">Dec km²</th><th scope="col">Jul km²</th><th scope="col">Change, pp</th></tr></thead>';
  const body = document.createElement('tbody');
  for (const [key, method] of Object.entries(earth.methods)) {
    const row = document.createElement('tr');
    for (const value of [key === 'fixed' ? 'Fixed −17 dB' : 'Otsu per date', ...method.candidate_area_km2.map((area) => fixed(area, 2)), fixed(method.change_fraction * 100, 2)]) {
      const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
    }
    body.append(row);
  }
  table.append(body); $('earth-results').replaceChildren(table);
  const note = document.createElement('p');
  note.className = 'artifact-mode';
  note.textContent = `Otsu threshold changes from ${fixed(earth.methods.otsu.threshold_db[0], 2)} to ${fixed(earth.methods.otsu.threshold_db[1], 2)} dB. Its class-balance adaptation confounds a temporal extent comparison. Spatial block sensitivity is documented in the report.`;
  $('earth-results').append(note);
} catch (reason) { error(`${String(reason)} Figures and source documentation remain available. Reload to retry numerical artifacts.`); }
