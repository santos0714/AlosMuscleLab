import { useCallback, useEffect, useMemo, useState } from "react";
import type { Data } from "plotly.js";
import { api, type Level, type Study } from "./api";
import { COLORS, CONTRACTION_LABEL, MARK_LABEL, fmt, levelLabel, pct } from "./charts";
import { Plot } from "./Plot";

const RECOVERY_MARKS = ["rec_0min", "rec_5min", "rec_15min", "rec_30min"];
const DEFAULT_LEVELS = ["ninguno", "dano_flujo_22pct", "lenta_mvo2_1", "combinado"];

// Color fijo por conjunto de predictores: sigue a la entidad aunque falte alguno
const SETS: [key: "r2_dosis" | "r2_nirs" | "r2_dosis_nirs" | "r2_dosis_oraculo", name: string, color: string][] = [
  ["r2_dosis", "Dosis", COLORS.s1],
  ["r2_nirs", "NIRS sola", COLORS.s2],
  ["r2_dosis_nirs", "Dosis + NIRS", COLORS.s3],
  ["r2_dosis_oraculo", "Dosis + sensor perfecto", COLORS.s4],
];

export function RecoveryView() {
  const [levels, setLevels] = useState<Level[]>([]);
  const [studies, setStudies] = useState<Study[]>([]);
  const [current, setCurrent] = useState<Study | null>(null);
  const [form, setForm] = useState({ n_subjects: 40, seed: 2026, optics: false, levels: DEFAULT_LEVELS });
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState("ninguno");
  const [mark, setMark] = useState("rec_5min");

  const refresh = useCallback(() => api.studies().then(setStudies).catch((e) => setError(String(e.message ?? e))), []);
  useEffect(() => {
    api.levels().then(setLevels).catch((e) => setError(String(e.message ?? e)));
    refresh();
  }, [refresh]);

  // Al entrar, abre el último estudio terminado
  useEffect(() => {
    if (current || !studies.length) return;
    const done = studies.find((s) => s.estado === "terminado");
    if (done) api.study(done.id).then(setCurrent).catch(() => undefined);
  }, [studies, current]);

  // Sondeo mientras el estudio corre
  useEffect(() => {
    if (!current || current.estado === "terminado" || current.estado === "error") return;
    const h = window.setInterval(async () => {
      try {
        const s = await api.study(current.id);
        setCurrent(s);
        if (s.estado === "terminado" || s.estado === "error") refresh();
      } catch (e) {
        setError(String((e as Error).message ?? e));
      }
    }, 1500);
    return () => window.clearInterval(h);
  }, [current, refresh]);

  useEffect(() => {
    const names = current?.resultado?.niveles.map((n) => n.nombre) ?? [];
    if (names.length && !names.includes(level)) setLevel(names[0]);
  }, [current, level]);

  const start = async () => {
    setError(null);
    try {
      const { id } = await api.startStudy({ ...form, levels: form.levels.length ? form.levels : null });
      setCurrent(await api.study(id));
      refresh();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  };

  const res = current?.resultado ?? null;
  const running = current && (current.estado === "en_cola" || current.estado === "en_curso");

  const dissociation = useMemo(() => {
    if (!res) return null;
    const rows = RECOVERY_MARKS.map((m) => res.disociacion.find((d) => d.nivel === level && d.marca === m));
    const xs = RECOVERY_MARKS.map((m) => MARK_LABEL[m]);
    const data: Data[] = [
      { type: "bar", name: "Reoxigenados (≥ 90 % de la caída)", x: xs, y: rows.map((r) => (r?.reoxigenados ?? 0) * 100), marker: { color: COLORS.s1, line: { color: "#fcfcfb", width: 2 } }, hovertemplate: "%{y:.0f} %<extra>Reoxigenados</extra>" },
      { type: "bar", name: "Fuerza recuperada (≥ 95 %)", x: xs, y: rows.map((r) => (r?.recuperados ?? 0) * 100), marker: { color: COLORS.s2, line: { color: "#fcfcfb", width: 2 } }, hovertemplate: "%{y:.0f} %<extra>Recuperados</extra>" },
    ];
    return { data, layout: { barmode: "group" as const, bargap: 0.3, bargroupgap: 0.08, yaxis: { title: { text: "Sujetos (%)" }, range: [0, 105] }, margin: { l: 56, r: 24, t: 40, b: 40 } } };
  }, [res, level]);

  const gain = useMemo(() => {
    if (!res) return null;
    const rows = RECOVERY_MARKS.map((m) => res.ganancia.find((g) => g.nivel === level && g.alcance === m));
    const xs = RECOVERY_MARKS.map((m) => MARK_LABEL[m]);
    const data: Data[] = SETS.filter(([k]) => rows.some((r) => r && r[k] !== undefined && r[k] !== null)).map(([k, n, c]) => ({
      type: "bar", name: n, x: xs, y: rows.map((r) => (r?.[k] ?? null)), marker: { color: c, line: { color: "#fcfcfb", width: 2 } },
      hovertemplate: `R² %{y:.3f}<extra>${n}</extra>`,
    }));
    return { data, layout: { barmode: "group" as const, bargap: 0.25, bargroupgap: 0.06, yaxis: { title: { text: "R² con validación cruzada" }, range: [-0.1, 1] }, margin: { l: 56, r: 24, t: 40, b: 40 } } };
  }, [res, level]);

  const scatter = useMemo(() => {
    if (!res) return null;
    const pts = res.puntos.filter((p) => p.nivel === level && p.marca === mark);
    const types: [string, string][] = [["isometric", COLORS.s1], ["dynamic", COLORS.s2], ["eccentric", COLORS.s3]];
    const data: Data[] = types.map(([c, col]) => {
      const sel = pts.filter((p) => p.contraccion === c);
      return {
        type: "scatter", mode: "markers", name: CONTRACTION_LABEL[c], x: sel.map((p) => (p.verdad_reox_frac ?? NaN) * 100), y: sel.map((p) => p.fuerza * 100),
        text: sel.map((p) => p.sujeto), marker: { color: col, size: 9, opacity: 0.85, line: { color: "#fcfcfb", width: 1.5 } },
        hovertemplate: "%{text}<br>Reoxigenación %{x:.0f} %<br>Fuerza %{y:.0f} %<extra></extra>",
      };
    });
    return {
      data,
      layout: {
        hovermode: "closest" as const,
        xaxis: { title: { text: "Caída de oxigenación ya recuperada (%)" } },
        yaxis: { title: { text: "Fuerza máxima (% de la previa)" } },
        shapes: [
          { type: "line" as const, xref: "x" as const, yref: "paper" as const, x0: 90, x1: 90, y0: 0, y1: 1, line: { color: "#b8c1ca", dash: "dot" as const, width: 1 } },
          { type: "line" as const, xref: "paper" as const, yref: "y" as const, x0: 0, x1: 1, y0: 95, y1: 95, line: { color: "#b8c1ca", dash: "dot" as const, width: 1 } },
        ],
        margin: { l: 56, r: 24, t: 40, b: 44 },
      },
    };
  }, [res, level, mark]);

  const disRow = res?.disociacion.find((d) => d.nivel === level && d.marca === mark);
  const levelInfo = res?.niveles.find((n) => n.nombre === level);

  return (
    <section className="view" aria-label="Recuperación">
      <p className="view-intro">
        Cohortes de sujetos virtuales con fisiología, grasa, piel y ejercicio distintos. La pregunta es si, en un momento dado de la
        recuperación, la NIRS predice la fuerza mejor que lo que ya se sabe: la dosis de ejercicio. Detalles en
        <code> docs/02_analisis_recuperacion.md</code>.
      </p>

      <fieldset className="group chart" style={{ padding: 16 }}>
        <legend className="group-title" style={{ padding: "0 4px" }}>Nuevo estudio</legend>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 24px", alignItems: "end" }}>
          <label className="field" style={{ gridTemplateColumns: "auto 90px", margin: 0 }}>
            <span>Sujetos</span>
            <input type="number" min={4} max={300} value={form.n_subjects} onChange={(e) => setForm({ ...form, n_subjects: Math.max(4, Math.min(300, Number(e.target.value) || 4)) })} />
          </label>
          <label className="field" style={{ gridTemplateColumns: "auto 90px", margin: 0 }}>
            <span>Semilla</span>
            <input type="number" value={form.seed} onChange={(e) => setForm({ ...form, seed: Number(e.target.value) || 0 })} />
          </label>
          <label className="check" style={{ margin: 0 }}>
            <input type="checkbox" checked={form.optics} onChange={(e) => setForm({ ...form, optics: e.target.checked })} />
            Simular también el sensor (unos 2 s por sujeto y nivel; sin él, solo fisiología)
          </label>
        </div>
        <div style={{ margin: "12px 0", display: "flex", flexWrap: "wrap", gap: "4px 18px" }} role="group" aria-label="Niveles de acoplamiento">
          {levels.map((l) => (
            <label className="check" key={l.nombre} title={l.descripcion} style={{ margin: 0 }}>
              <input type="checkbox" checked={form.levels.includes(l.nombre)} onChange={(e) => setForm({
                ...form, levels: e.target.checked ? [...form.levels, l.nombre] : form.levels.filter((x) => x !== l.nombre),
              })} />
              {levelLabel(l.nombre)}
            </label>
          ))}
        </div>
        <button type="button" className="btn btn-primary" onClick={start} disabled={!!running}>
          {running ? "Estudio en curso…" : "Iniciar estudio"}
        </button>
        {running && current && (
          <span style={{ marginLeft: 16 }}>
            <progress className="progress" value={current.progreso} max={1} aria-label="Progreso del estudio" /> {pct(current.progreso)}
          </span>
        )}
        {current?.estado === "error" && <p className="error">El estudio falló: {current.error}</p>}
        {error && <p className="error">{error}</p>}
      </fieldset>

      {studies.length > 0 && (
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <label htmlFor="estudio-sel">Estudio mostrado</label>
          <select id="estudio-sel" style={{ width: "auto" }} value={current?.id ?? ""} onChange={(e) => api.study(Number(e.target.value)).then(setCurrent)}>
            {studies.map((s) => (
              <option key={s.id} value={s.id}>
                {`#${s.id}: ${s.parametros.n_subjects} sujetos, ${s.parametros.optics ? "con sensor" : "solo fisiología"}, ${s.estado.replace("_", " ")}`}
              </option>
            ))}
          </select>
        </div>
      )}

      {!res && !running && <div className="empty">Inicia un estudio para ver la disociación entre reoxigenación y fuerza y cuánto aporta la NIRS.</div>}

      {res && (
        <>
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <label htmlFor="nivel-sel">Acoplamiento fatiga → hemodinámica</label>
            <select id="nivel-sel" style={{ width: "auto" }} value={level} onChange={(e) => setLevel(e.target.value)}>
              {res.niveles.map((n) => <option key={n.nombre} value={n.nombre}>{levelLabel(n.nombre)}</option>)}
            </select>
            <span className="muted">{levelInfo?.descripcion}</span>
          </div>
          <p className="muted" style={{ margin: 0 }}>
            {res.sujetos} sujetos aceptados, {res.descartes} descartados por incoherencia fisiológica{res.fallos.length ? `, ${res.fallos.length} fallos` : ""}.
          </p>
          <div className="grid-2">
            <div className="chart">
              <h3>Reoxigenación frente a recuperación</h3>
              <p className="caption">Cambios reales en el músculo. Casi todos reoxigenan en 5 min; la fuerza tarda mucho más.</p>
              {dissociation && <Plot data={dissociation.data} layout={dissociation.layout} label="Porcentaje de sujetos reoxigenados y con fuerza recuperada en cada marca" />}
            </div>
            <div className="chart">
              <h3>¿Cuánto explica cada conjunto de datos?</h3>
              <p className="caption">
                Un modelo ridge por marca. Sin el sensor simulado solo aparecen dosis y sensor perfecto.
                {res.sujetos < 80 && ` Con ${res.sujetos} sujetos los modelos con más variables sobreajustan; usa 100 o más para comparar.`}
              </p>
              {gain && <Plot data={gain.data} layout={gain.layout} label="R² de la predicción de la fuerza por conjunto de predictores y marca" />}
            </div>
          </div>
          <div className="chart">
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, alignItems: "baseline" }}>
              <h3>Cada sujeto en una marca</h3>
              <span role="group" aria-label="Marca mostrada" style={{ display: "flex", gap: 4 }}>
                {RECOVERY_MARKS.map((m) => (
                  <button key={m} type="button" className="btn btn-small" aria-pressed={mark === m} style={mark === m ? { background: "var(--ink)", color: "#fff" } : undefined} onClick={() => setMark(m)}>
                    {MARK_LABEL[m]}
                  </button>
                ))}
              </span>
            </div>
            <p className="caption">
              Arriba a la derecha de las líneas punteadas: reoxigenado y recuperado. {disRow && `En ${MARK_LABEL[mark]}, ${pct(disRow.reox_sin_fuerza)} de los sujetos están reoxigenados sin haber recuperado la fuerza (fuerza media ${fmt((disRow.fuerza_media ?? 0) * 100, 0, " %")}).`}
            </p>
            {scatter && <Plot data={scatter.data} layout={scatter.layout} label="Fracción reoxigenada frente a fuerza por sujeto y tipo de contracción" />}
          </div>
        </>
      )}
    </section>
  );
}
