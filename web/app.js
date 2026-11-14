const $ = (id) => document.getElementById(id);
const ns = "http://www.w3.org/2000/svg";
const C = {
  cyan: "#7FDBFF",
  yellow: "#F2C14E",
  red: "#FF8A7A",
  dim: "#8FB4C9",
  green: "#9BE7C4",
};
let data = null,
  method = "detrended",
  trial = 0,
  meta = null,
  busy = false;
function node(tag, attrs = {}, text) {
  const e = document.createElementNS(ns, tag);
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  if (text !== undefined) e.textContent = text;
  return e;
}
function plot(id, xmin, xmax, ymin, ymax, xlabel, ylabel) {
  const e = $(id);
  e.replaceChildren();
  const wide = id === "timeline",
    w = wide ? 1100 : 540,
    h = wide ? 290 : 310;
  const left = 68,
    right = 20,
    top = 30,
    bottom = 48;
  const x = (v) => left + ((v - xmin) / (xmax - xmin)) * (w - left - right),
    y = (v) => h - bottom - ((v - ymin) / (ymax - ymin)) * (h - top - bottom);
  for (let i = 0; i <= 4; i++) {
    let a = ymin + ((ymax - ymin) * i) / 4,
      b = xmin + ((xmax - xmin) * i) / 4;
    e.append(
      node("line", {
        x1: left,
        x2: w - right,
        y1: y(a),
        y2: y(a),
        stroke: C.cyan,
        opacity: 0.14,
      }),
    );
    e.append(
      node(
        "text",
        { x: left - 10, y: y(a) + 4, "text-anchor": "end" },
        Math.round(a).toLocaleString(),
      ),
    );
    e.append(
      node(
        "text",
        { x: x(b), y: h - 24, "text-anchor": "middle" },
        b.toFixed(1),
      ),
    );
  }
  e.append(node("text", { x: left, y: 16 }, ylabel));
  e.append(
    node("text", { x: w - right, y: h - 4, "text-anchor": "end" }, xlabel),
  );
  return { e, x, y, w, h, left, right, top, bottom };
}
function line(p, xs, ys, color, width = 1.5, extra = {}) {
  p.e.append(
    node("path", {
      d: xs
        .map(
          (v, i) =>
            (i ? "L" : "M") + p.x(v).toFixed(2) + "," + p.y(ys[i]).toFixed(2),
        )
        .join(" "),
      fill: "none",
      stroke: color,
      "stroke-width": width,
      ...extra,
    }),
  );
}
function dots(p, xs, ys, color, r = 1.6, opacity = 0.65) {
  xs.forEach((v, i) =>
    p.e.append(
      node("circle", { cx: p.x(v), cy: p.y(ys[i]), r, fill: color, opacity }),
    ),
  );
}
function bounds(values) {
  let lo = Math.min(...values),
    hi = Math.max(...values);
  const pad = Math.max((hi - lo) * 0.12, 100);
  return [lo - pad, hi + pad];
}
function ppm(y) {
  return y.map((v) => (v - 1) * 1e6);
}
function render() {
  if (!data) return;
  const fit = data.methods[method],
    raw = ppm(data.flux),
    clean = ppm(fit.flux),
    pvalue = fit.periods[trial],
    reveal = $("reveal").checked;
  const [lo, hi] = bounds(raw);
  let p = plot(
    "timeline",
    0,
    27,
    lo,
    hi,
    "Elapsed days",
    "Relative flux · ppm",
  );
  if (reveal) {
    data.transit.forEach((v, i) => {
      if (v < 0)
        p.e.append(
          node("line", {
            x1: p.x(data.time[i]),
            x2: p.x(data.time[i]),
            y1: p.top,
            y2: p.h - p.bottom,
            stroke: C.yellow,
            opacity: 0.1,
          }),
        );
    });
  }
  dots(p, data.time, raw, C.cyan);
  if (method === "detrended") line(p, data.time, ppm(fit.trend), C.yellow);
  $("trend-key").hidden = method !== "detrended";
  $("truth-key").hidden = !reveal;
  $("best-period").textContent = fit.period_days.toFixed(3) + " days";
  $("score").textContent =
    fit.score.toFixed(2) + " / " + fit.threshold.toFixed(2);
  $("decision").textContent = fit.alarm
    ? "Candidate flagged"
    : "Below threshold";
  $("decision").style.color = fit.alarm ? C.yellow : C.dim;
  $("record").textContent = "Seed " + data.truth.seed;
  $("method-note").textContent =
    method === "raw"
      ? "No stellar-trend removal"
      : fit.window_days.toFixed(1) + " day time-window median";
  p = plot(
    "periodogram",
    1.4,
    5.6,
    0,
    Math.max(...fit.scores, fit.threshold) * 1.15,
    "Trial period · days",
    "Box-search score",
  );
  line(p, fit.periods, fit.scores, C.cyan, 1.6, {
    class: "draw",
    pathLength: 1,
  });
  line(p, [1.4, 5.6], [fit.threshold, fit.threshold], C.yellow, 1, {
    "stroke-dasharray": "5 5",
  });
  line(
    p,
    [pvalue, pvalue],
    [0, Math.max(...fit.scores, fit.threshold) * 1.15],
    C.dim,
    1,
  );
  p.e.append(
    node("circle", {
      cx: p.x(pvalue),
      cy: p.y(fit.scores[trial]),
      r: 4,
      fill: C.yellow,
    }),
  );
  const phase = data.time
    .map((t) => ((t - fit.epoch_days) / pvalue + 0.5) % 1)
    .map((v) => ((v + 1) % 1) - 0.5);
  const [clo, chi] = bounds(clean);
  p = plot("fold", -0.5, 0.5, clo, chi, "Phase · cycles", "Search input · ppm");
  dots(p, phase, clean, C.dim, 1.4, 0.45);
  const bx = [],
    by = [];
  for (let i = 0; i < 64; i++) {
    const points = clean.filter(
      (_, j) => phase[j] >= i / 64 - 0.5 && phase[j] < (i + 1) / 64 - 0.5,
    );
    if (points.length) {
      bx.push((i + 0.5) / 64 - 0.5);
      by.push(points.reduce((a, b) => a + b, 0) / points.length);
    }
  }
  dots(p, bx, by, C.cyan, 3, 1);
  if (Math.abs(pvalue - fit.period_days) < 1e-8) {
    const half = fit.duration_days / fit.period_days / 2,
      out = (fit.baseline_flux - 1) * 1e6;
    line(
      p,
      [-0.5, -half, -half, half, half, 0.5],
      [out, out, out - fit.depth_ppm, out - fit.depth_ppm, out, out],
      C.red,
      2,
    );
  }
  $("fold-label").textContent = pvalue.toFixed(3) + " d";
  $("trial-output").textContent = pvalue.toFixed(3) + " days";
  $("truth").hidden = !reveal;
  $("truth").textContent =
    `EVALUATOR ONLY — injected period ${data.truth.period_days.toFixed(4)} days; depth ${data.truth.depth_ppm} ppm; duration ${(data.truth.duty_fraction * data.truth.period_days * 24).toFixed(2)} hours. ${data.truth.depth_ppm === 0 ? "This is a no-transit control. The stored period has no physical signal." : Math.abs(fit.period_days / data.truth.period_days - 1) <= 0.02 ? "The strongest trial matches the injected period within 2%." : "The strongest trial misses the injected fundamental period."}`;
}
function choose(name) {
  method = name;
  for (const m of ["raw", "detrended"])
    $(m).setAttribute("aria-pressed", String(m === name));
  best();
}
function best() {
  if (!data) return;
  trial = data.methods[method].scores.indexOf(
    Math.max(...data.methods[method].scores),
  );
  $("trial").value = trial;
  render();
}
async function run(event) {
  event?.preventDefault();
  if (busy) return;
  busy = true;
  $("run").disabled = true;
  $("export").disabled = true;
  $("error").hidden = true;
  $("status").textContent =
    "Generating observations and searching both methods…";
  $("experiment").setAttribute("aria-busy", "true");
  try {
    const r = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        seed: Number($("seed").value),
        family: $("family").value,
        depth_ppm: Number($("depth").value),
      }),
    });
    const value = await r.json();
    if (!r.ok) throw Error(value.error || "Simulation failed");
    data = value;
    $("experiment").hidden = false;
    $("status").textContent =
      `Completed: ${data.time.length} observations · ${data.truth.family} · seed ${data.truth.seed} · ${data.truth.depth_ppm} ppm injection`;
    best();
    $("export").disabled = false;
  } catch (e) {
    $("error").textContent = e.message;
    $("error").hidden = false;
    $("status").textContent =
      "Run failed. Any plots shown belong to the previous completed record.";
  } finally {
    busy = false;
    $("run").disabled = false;
    $("experiment").setAttribute("aria-busy", "false");
  }
}
$("controls").addEventListener("submit", run);
$("raw").addEventListener("click", () => choose("raw"));
$("detrended").addEventListener("click", () => choose("detrended"));
$("reveal").addEventListener("change", render);
$("trial").addEventListener("input", (e) => {
  trial = Number(e.target.value);
  render();
});
$("best").addEventListener("click", best);
$("export").addEventListener("click", () => {
  if (!data || busy || $("export").disabled) return;
  const a = document.createElement("a"),
    url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
    );
  a.href = url;
  a.download = `transitweave-${data.truth.seed}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
try {
  const response = await fetch("/api/meta");
  if (!response.ok) throw Error("Unable to load benchmark configuration");
  meta = await response.json();
  for (const row of meta.summary) {
    const tr = document.createElement("tr");
    for (const text of [
      row.family,
      row.method,
      `${row.recovered} / ${row.signals} (${((100 * row.recovered) / row.signals).toFixed(1)}%)`,
      `${row.false_alarms} / ${row.nulls} (${((100 * row.false_alarms) / row.nulls).toFixed(1)}%)`,
    ]) {
      const td = document.createElement("td");
      td.textContent = text;
      tr.append(td);
    }
    $("benchmark").append(tr);
  }
  $("protocol").textContent =
    `Window selected on validation scenarios: ${meta.config.selected_window_days} days. Calibration uses 120 independent no-transit scenarios per method; the 95th-percentile threshold is fixed before the held-out test. Recovery requires a score above threshold AND a fundamental period within 2%. These counts describe this synthetic generator only.`;
  await run();
} catch (e) {
  $("error").hidden = false;
  $("error").textContent = e.message;
  $("status").textContent = "Could not start the experiment.";
}
