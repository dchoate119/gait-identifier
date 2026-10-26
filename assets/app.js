// Gait Logger page, two tabs:
//   Record:   label + Start/Stop, live status, 5 s plot, recordings list
//   Evaluate: live prediction cards for model 1 and model 2, 5 s plot
// Python sends "samples" ([t_ms, ax, ay, az, gx, gy, gz] rows), "status",
// "recordings" and "prediction" {model, gait, peak, probs}; this page sends
// "start" {label} and "stop".

const WINDOW = 250;   // samples on the plot (5 s at 50 Hz)
const CLASSES = ['still', 'bike', 'walk', 'run'];

const ui = new WebUI();
const $ = id => document.getElementById(id);

let label = 'walk';
let recording = false;
let showGyro = false;
let buffer = [];

// --- connection ---
ui.on_connect(() => setConn(true));
ui.on_disconnect(() => setConn(false));

function setConn(on) {
  $('conn').textContent = on ? 'connected' : 'disconnected';
  $('conn').className = 'pill ' + (on ? 'on' : 'off');
}

// --- tabs ---
// One plot card, moved into the active tab's slot
document.querySelectorAll('.tabs button').forEach(b => {
  b.addEventListener('click', () => showTab(b.dataset.tab));
});

function showTab(name) {
  document.querySelectorAll('.tabs button').forEach(b => b.classList.toggle('selected', b.dataset.tab === name));
  document.querySelectorAll('.tab').forEach(t => (t.hidden = t.id !== `tab-${name}`));
  $(`tab-${name}`).querySelector('.plot-slot').appendChild($('plot-card'));
  try { localStorage.setItem('tab', name); } catch {}
  draw();
}

// --- controls ---
document.querySelectorAll('#labels button').forEach(b => {
  b.addEventListener('click', () => {
    if (recording) return;
    label = b.dataset.label;
    document.querySelectorAll('#labels button').forEach(o => o.classList.toggle('selected', o === b));
  });
});

$('record').addEventListener('click', () => {
  if (recording) ui.send_message('stop');
  else ui.send_message('start', { label });
});

$('show-accel').addEventListener('click', () => setView(false));
$('show-gyro').addEventListener('click', () => setView(true));

function setView(gyro) {
  showGyro = gyro;
  $('show-accel').classList.toggle('selected', !gyro);
  $('show-gyro').classList.toggle('selected', gyro);
  draw();
}

// --- messages from the board ---
ui.on_message('status', s => {
  recording = s.recording;
  $('rec-badge').hidden = !recording;
  $('record').textContent = recording ? 'Stop' : 'Start';
  $('record').classList.toggle('recording', recording);
  document.querySelectorAll('#labels button').forEach(b => (b.disabled = recording));
  $('file').textContent = s.file || '–';
  $('elapsed').textContent = `${s.elapsed.toFixed(1)} s`;
  $('rows').textContent = s.rows;
  $('hz').textContent = s.hz ? `${s.hz} Hz` : '– Hz';
  $('gap').textContent = s.max_gap ? `${s.max_gap} ms` : '– ms';
  $('dropped').textContent = s.dropped;
});

ui.on_message('prediction', p => {
  const card = $(`model-${p.model}`);
  if (!card) return;
  card.querySelector('.gait').textContent = p.gait;
  card.querySelector('.detail').textContent = p.peak != null ? `peak ${p.peak.toFixed(2)} g` : '';
  card.querySelector('.probs').innerHTML = CLASSES.map(c => {
    const pct = Math.round((p.probs[c] ?? 0) * 100);
    return `<div class="prob"><span>${c}</span><div class="bar"><div class="fill" style="width:${pct}%"></div></div><span class="pct">${pct}%</span></div>`;
  }).join('');
});

ui.on_message('samples', m => {
  buffer = buffer.concat(m.samples).slice(-WINDOW);
  draw();
});

ui.on_message('recordings', m => {
  const list = $('recordings');
  list.innerHTML = '';
  if (!m.files.length) {
    list.innerHTML = '<li class="empty">None yet</li>';
    return;
  }
  for (const f of m.files) {
    const li = document.createElement('li');
    li.innerHTML = `<span>${f.file}</span><span>${f.kb} KB</span>`;
    list.appendChild(li);
  }
});

// --- plot ---
const canvas = $('plot');
const ctx = canvas.getContext('2d');

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w * dpr) { canvas.width = w * dpr; canvas.height = h * dpr; }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const css = getComputedStyle(document.documentElement);
  const cols = showGyro ? [4, 5, 6] : [1, 2, 3];
  const colors = ['--x', '--y', '--z'].map(c => css.getPropertyValue(c));

  // Symmetric y range that grows to fit the data, with a minimum
  let max = showGyro ? 100 : 2;
  for (const s of buffer) for (const c of cols) max = Math.max(max, Math.abs(s[c]));
  const y = v => h / 2 - (v / max) * (h / 2 - 4);
  const x = i => (i / (WINDOW - 1)) * w;

  // zero line and range labels
  ctx.strokeStyle = css.getPropertyValue('--border');
  ctx.beginPath(); ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2); ctx.stroke();
  ctx.fillStyle = css.getPropertyValue('--muted');
  ctx.font = '11px system-ui';
  ctx.fillText(`+${max.toFixed(showGyro ? 0 : 1)}`, 4, 12);
  ctx.fillText(`-${max.toFixed(showGyro ? 0 : 1)}`, 4, h - 4);

  const offset = WINDOW - buffer.length;   // newest sample on the right edge
  cols.forEach((c, k) => {
    ctx.strokeStyle = colors[k];
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    buffer.forEach((s, i) => {
      const px = x(i + offset), py = y(s[c]);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
  });
}

window.addEventListener('resize', draw);

// Reopen the last tab
let savedTab = 'record';
try { savedTab = localStorage.getItem('tab') || 'record'; } catch {}
showTab(savedTab === 'evaluate' ? 'evaluate' : 'record');
