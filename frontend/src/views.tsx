import { useEffect, useMemo, useState } from "react";
import type { Data } from "plotly.js";
import { api, type ComponentCatalog, type Catalog, type Protocol, type RunResponse } from "./api";
import { COLORS, endLabel, fmt, line, minutes, pct, protocolShapes } from "./charts";
import { Plot } from "./Plot";

interface ViewProps {
  result: RunResponse;
  protocol: Protocol; // protocolo con el que se calculó el resultado
  assumedDpf: number;
}

const MARKS = ["rec_0min", "rec_5min", "rec_15min", "rec_30min"];

/** Fracción de la caída de (O2 − desoxi) del ejercicio ya recuperada en una marca. */
function reoxFraction(f: Record<string, number | null>, mark: string) {
  const caida = f.caida_diff_uM;
  const v = f[`${mark}_d_diff_uM`];
  return caida !== null && caida < 0 && v !== null && v !== undefined ? 1 - v / caida : null;
}

/* ------------------------------------------------------------------ señal y procesado */
export function SignalView({ result, protocol, assumedDpf }: ViewProps) {
  const { series: s, resumen: r } = result;
  const x = useMemo(() => minutes(s.t_s), [s.t_s]);
  const ph = useMemo(() => protocolShapes(protocol, r.marcas_s), [protocol, r.marcas_s]);

  const conc = useMemo(() => {
    const data: Data[] = [
      line(x, s.estimado_uM.d_oxy, "Oxi, sensor", COLORS.oxi, { hover: "%{y:.1f} µM<extra>Oxi, sensor</extra>" }),
      line(x, s.estimado_uM.d_deoxy, "Desoxi, sensor", COLORS.desoxi, { hover: "%{y:.1f} µM<extra>Desoxi, sensor</extra>" }),
      line(x, s.verdad_uM.d_oxy, "Oxi, real en el músculo", COLORS.oxi, { dash: "dash", width: 1.5, hover: "%{y:.1f} µM<extra>Oxi, real</extra>" }),
      line(x, s.verdad_uM.d_deoxy, "Desoxi, real en el músculo", COLORS.desoxi, { dash: "dash", width: 1.5, hover: "%{y:.1f} µM<extra>Desoxi, real</extra>" }),
    ];
    return {
      data,
      layout: {
        xaxis: { title: { text: "Tiempo (min)" } },
        yaxis: { title: { text: "Cambio respecto al reposo (µM)" } },
        shapes: ph.shapes,
        annotations: ph.annotations,
        margin: { l: 60, r: 24, t: 36, b: 44 },
      },
    };
  }, [x, s, ph]);

  const atten = useMemo(() => {
    const keys = Object.keys(s.atenuacion);
    const cols = [COLORS.s1, COLORS.s2, COLORS.s3];
    const data = keys.map((k, i) => line(x, s.atenuacion[k], `${k} nm`, cols[i], { hover: `%{y:.4f}<extra>${k} nm</extra>` }));
    return {
      data,
      layout: {
        xaxis: { title: { text: "Tiempo (min)" } },
        yaxis: { title: { text: "Cambio de atenuación (ln)" } },
        shapes: ph.shapes,
        margin: { l: 64, r: 24, t: 32, b: 44 },
      },
    };
  }, [x, s.atenuacion, ph]);

  const e = r.rasgos_estimados, v = r.rasgos_verdaderos;
  const rows: [string, string, number | null, number | null, number][] = [
    ["Caída de (oxi − desoxi) en el ejercicio", "µM", e.caida_diff_uM, v.caida_diff_uM, 1],
    ["Pico de desoxi", "µM", e.pico_deoxy_uM, v.pico_deoxy_uM, 1],
    ["Tiempo medio de reoxigenación", "s", e.t_medio_reox_s, v.t_medio_reox_s, 1],
    ["Pico de la hiperemia (hemoglobina total)", "µM", e.hiperemia_pico_total_uM, v.hiperemia_pico_total_uM, 1],
    ["Tiempo al pico de la hiperemia", "s", e.hiperemia_t_pico_s, v.hiperemia_t_pico_s, 0],
  ];

  return (
    <section className="view" aria-label="Señal y procesado">
      <p className="view-intro">
        Lo que estima el sensor con Beer-Lambert modificada (DPF supuesto {fmt(assumedDpf, 2)}) frente al cambio real de
        hemoglobina y mioglobina en el músculo. La diferencia viene de la grasa y la piel, que también recorre la luz, y del DPF.
      </p>
      <div className="chart">
        <h3>Cambios de concentración</h3>
        <p className="caption">Continua: estimado por el sensor. Discontinua: real en el músculo. La franja gris es el ejercicio; las líneas punteadas, las marcas de recuperación.</p>
        <Plot data={conc.data} layout={conc.layout} tall label="Cambios de oxi y desoxihemoglobina estimados y reales durante el protocolo" />
      </div>
      <div className="grid-2">
        <div className="table-wrap">
          <table>
            <caption className="muted" style={{ textAlign: "left", padding: "10px 12px 4px", fontWeight: 600, color: "var(--ink)" }}>Rasgos de la sesión</caption>
            <thead><tr><th>Rasgo</th><th>Sensor</th><th>Real</th><th>Sensor / real</th></tr></thead>
            <tbody>
              {rows.map(([n, u, a, b, d]) => (
                <tr key={n}>
                  <td>{n}</td>
                  <td>{fmt(a, d, ` ${u}`)}</td>
                  <td>{fmt(b, d, ` ${u}`)}</td>
                  <td>{a !== null && b !== null && b !== 0 ? fmt(a / b, 2) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="chart">
          <h3>Atenuación medida</h3>
          <p className="caption">Cambio de −ln(I/I₀) en cada longitud de onda, ya filtrado.</p>
          <Plot data={atten.data} layout={atten.layout} label="Cambio de atenuación en 760, 810 y 850 nm" />
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ fisiología */
export function PhysiologyView({ result, protocol }: ViewProps) {
  const { series: s, resumen: r } = result;
  const f = s.fisiologia;
  const x = useMemo(() => minutes(s.t_s), [s.t_s]);
  const ph = useMemo(() => protocolShapes(protocol, r.marcas_s), [protocol, r.marcas_s]);
  const toPct = (a: (number | null)[]) => a.map((v) => (v === null ? null : 100 * v));

  const sat = useMemo(() => ({
    data: [
      line(x, toPct(f.smo2), "Hemoglobina (SmO₂)", COLORS.oxi, { hover: "%{y:.1f} %<extra>SmO₂</extra>" }),
      line(x, toPct(f.smbo2), "Mioglobina", COLORS.s4, { hover: "%{y:.1f} %<extra>Mioglobina</extra>" }),
    ],
    layout: { xaxis: { title: { text: "Tiempo (min)" } }, yaxis: { title: { text: "Saturación (%)" } }, shapes: ph.shapes, annotations: ph.annotations, margin: { l: 56, r: 24, t: 36, b: 44 } },
  }), [x, f, ph]);

  const hemo = useMemo(() => ({
    data: [
      line(x, f.flujo_rel, "Flujo", COLORS.s1, { hover: "%{y:.2f}×<extra>Flujo</extra>" }),
      line(x, f.volumen_sangre_rel, "Volumen de sangre", COLORS.s2, { hover: "%{y:.2f}×<extra>Volumen</extra>" }),
      line(x, f.consumo_o2_rel, "Consumo de O₂", COLORS.s3, { hover: "%{y:.2f}×<extra>Consumo de O₂</extra>" }),
    ],
    layout: { xaxis: { title: { text: "Tiempo (min)" } }, yaxis: { title: { text: "Veces el valor de reposo" }, type: "log" as const, tickvals: [0.1, 0.2, 0.5, 1, 2, 5, 10, 20], ticktext: ["0.1", "0.2", "0.5", "1", "2", "5", "10", "20"] }, shapes: ph.shapes, margin: { l: 56, r: 24, t: 32, b: 44 } },
  }), [x, f, ph]);

  const force = useMemo(() => {
    const marks = Object.entries(r.fuerza_en_marcas);
    return {
      data: [
        line(x, toPct(f.fuerza), "Capacidad de fuerza", COLORS.ink, { hover: "%{y:.1f} %<extra>Fuerza</extra>" }),
        {
          type: "scatter" as const, mode: "markers" as const, name: "Marcas", showlegend: false,
          x: marks.map(([k]) => r.marcas_s[k] / 60), y: marks.map(([, v]) => 100 * v),
          marker: { size: 9, color: COLORS.ink, line: { color: "#fcfcfb", width: 2 } }, hoverinfo: "skip" as const,
        },
      ] as Data[],
      layout: {
        showlegend: false,
        xaxis: { title: { text: "Tiempo (min)" } },
        yaxis: { title: { text: "Fuerza máxima (% de la previa)" } },
        shapes: ph.shapes,
        margin: { l: 56, r: 24, t: 32, b: 44 },
        annotations: marks.filter(([k]) => k !== "basal").map(([k, v]) => ({
          x: r.marcas_s[k] / 60, y: 100 * v, text: `${(100 * v).toFixed(0)} %`, showarrow: false, xanchor: "left" as const, yanchor: "top" as const, xshift: 4, yshift: -4, font: { size: 11, color: "#17202b" },
        })),
      },
    };
  }, [x, f, r, ph]);

  const reox5 = reoxFraction(r.rasgos_verdaderos, "rec_5min");
  const f5 = r.fuerza_en_marcas.rec_5min;

  return (
    <section className="view" aria-label="Fisiología">
      <p className="callout">
        {reox5 !== null && reox5 >= 0.995
          ? "A los 5 minutos de recuperación el músculo ya recuperó toda su caída de oxigenación"
          : `A los 5 minutos de recuperación el músculo ya recuperó el ${pct(reox5)} de su caída de oxigenación`}
        , pero la fuerza máxima está en el {pct(f5)} de la previa. Reoxigenarse no es recuperarse.
      </p>
      <div className="grid-2">
        <div className="chart">
          <h3>Saturación de oxígeno en el músculo</h3>
          <p className="caption">La franja gris es el ejercicio.</p>
          <Plot data={sat.data} layout={sat.layout} label="Saturación de hemoglobina y mioglobina en el músculo" />
        </div>
        <div className="chart">
          <h3>Capacidad de fuerza</h3>
          <p className="caption">Valores en las marcas de recuperación (+0, +5, +15 y +30 min).</p>
          <Plot data={force.data} layout={force.layout} label="Capacidad de fuerza máxima durante el protocolo" />
        </div>
      </div>
      <div className="chart">
        <h3>Flujo, volumen de sangre y consumo de oxígeno</h3>
        <p className="caption">Relativos al reposo, en escala logarítmica.</p>
        <Plot data={hemo.data} layout={hemo.layout} label="Flujo, volumen de sangre y consumo de oxígeno relativos al reposo" />
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ luz y tejido */
export function LightView({ result, assumedDpf, sdsMm }: ViewProps & { sdsMm: number }) {
  const r = result.resumen;
  const lams = r.longitudes_onda_nm.map((l) => `${l} nm`);
  const t = r.trayectorias_parciales_mm;
  const layers: ["piel" | "grasa" | "musculo", string, string][] = [
    ["piel", "Piel", COLORS.piel],
    ["grasa", "Grasa", COLORS.grasa],
    ["musculo", "Músculo", COLORS.musculo],
  ];
  const data: Data[] = layers.map(([k, n, c]) => ({
    type: "bar", orientation: "h", name: n, y: lams, x: t[k], marker: { color: c, line: { color: "#fcfcfb", width: 2 } },
    hovertemplate: `%{x:.1f} mm<extra>${n}</extra>`,
  }));
  const totals = r.longitudes_onda_nm.map((_, i) => t.piel[i] + t.grasa[i] + t.musculo[i]);
  const layout = {
    barmode: "stack" as const, hovermode: "y unified" as const, legend: { orientation: "h" as const, x: 0, y: 1.02, yanchor: "bottom" as const, traceorder: "normal" as const },
    xaxis: { title: { text: "Recorrido medio de los fotones detectados (mm)" } },
    yaxis: { autorange: "reversed" as const },
    margin: { l: 64, r: 24, t: 32, b: 44 },
  };
  const dpfEff = totals.map((tt) => tt / sdsMm);
  const ratio = (r.rasgos_estimados.pico_deoxy_uM ?? NaN) / (r.rasgos_verdaderos.pico_deoxy_uM ?? NaN);

  return (
    <section className="view" aria-label="Luz y tejido">
      <p className="view-intro">
        La luz que llega al detector recorre las tres capas. Solo la parte que pasa por el músculo lleva la señal
        fisiológica; la grasa diluye el cambio y Beer-Lambert con un DPF fijo no lo corrige.
      </p>
      <div className="figures">
        {r.longitudes_onda_nm.map((l, i) => (
          <div className="figure" key={l}>
            <strong>{pct(r.fraccion_trayectoria_musculo[i])}</strong>
            <span>del recorrido en el músculo a {l} nm</span>
          </div>
        ))}
        <div className="figure">
          <strong>{fmt(dpfEff[1] ?? dpfEff[0], 2)}</strong>
          <span>DPF efectivo a {r.longitudes_onda_nm[1] ?? r.longitudes_onda_nm[0]} nm (supuesto: {fmt(assumedDpf, 2)})</span>
        </div>
        <div className="figure">
          <strong>{fmt(ratio, 2)}</strong>
          <span>pico de desoxi estimado / real</span>
        </div>
      </div>
      <div className="chart">
        <h3>Recorrido de la luz por capa</h3>
        <Plot data={data} layout={layout} label="Trayectoria parcial media por capa en cada longitud de onda" />
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Longitud de onda</th><th>Piel (mm)</th><th>Grasa (mm)</th><th>Músculo (mm)</th><th>Total (mm)</th><th>DPF efectivo</th></tr></thead>
          <tbody>
            {r.longitudes_onda_nm.map((l, i) => (
              <tr key={l}><td>{l} nm</td><td>{fmt(t.piel[i], 1)}</td><td>{fmt(t.grasa[i], 1)}</td><td>{fmt(t.musculo[i], 1)}</td><td>{fmt(totals[i], 1)}</td><td>{fmt(dpfEff[i], 2)}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ sensor */
export function SensorView({ result, protocol, catalog }: ViewProps & { catalog: Catalog }) {
  const r = result.resumen, s = result.series;
  const x = useMemo(() => minutes(s.t_s), [s.t_s]);
  const ph = useMemo(() => protocolShapes(protocol, r.marcas_s, false), [protocol, r.marcas_s]);
  const [bom, setBom] = useState<ComponentCatalog | null>(null);
  useEffect(() => { api.catalogComponents().then(setBom).catch(() => setBom(null)); }, []);

  const keys = Object.keys(s.fotocorriente_nA);
  const cols = [COLORS.s1, COLORS.s2, COLORS.s3];
  const current = {
    data: keys.map((k, i) => line(x, s.fotocorriente_nA[k], `${k} nm`, cols[i], { hover: `%{y:.3f} nA<extra>${k} nm</extra>` })),
    layout: {
      xaxis: { title: { text: "Tiempo (min)" } }, yaxis: { title: { text: "Fotocorriente (nA)" } }, shapes: ph.shapes,
      margin: { l: 60, r: 64, t: 32, b: 44 },
      annotations: keys.map((k, i) => endLabel(x, s.fotocorriente_nA[k], `${k} nm`, cols[i])),
    },
  };
  const total = bom && typeof bom.bom_total_usd === "number" ? bom.bom_total_usd : bom?.bom_recomendada.reduce((a, b) => a + b.subtotal_usd, 0);

  return (
    <section className="view" aria-label="Sensor">
      <div className="figures">
        {r.longitudes_onda_nm.map((l, i) => (
          <div className="figure" key={l}>
            <strong>{fmt(r.snr_db[i], 0, " dB")}</strong>
            <span>SNR a {l} nm, {fmt(r.fotocorriente_basal_nA[i], 2, " nA")} en reposo</span>
          </div>
        ))}
        <div className="figure">
          <strong>{r.saturado ? "Saturado" : "Sin saturar"}</strong>
          <span>{r.saturado ? "El ADC recorta: baja la ganancia o la potencia" : "El ADC no recorta en ningún momento"}</span>
        </div>
      </div>
      <div className="chart">
        <h3>Fotocorriente en el detector</h3>
        <p className="caption">{catalog.sensor.tia.part}, ADC {catalog.sensor.adc.part}. La sombra marca el ejercicio.</p>
        <Plot data={current.data} layout={current.layout} label="Fotocorriente en cada longitud de onda" />
      </div>
      <div className="table-wrap">
        <table>
          <caption style={{ textAlign: "left", padding: "10px 12px 4px", fontWeight: 600 }}>Lista de materiales recomendada</caption>
          <thead><tr><th>Concepto</th><th>Componente</th><th>Cantidad</th><th>Precio unitario</th><th>Subtotal</th><th>Precio</th></tr></thead>
          <tbody>
            {bom?.bom_recomendada.map((b) => (
              <tr key={b.id_componente + b.concepto}>
                <td>{b.concepto}</td><td style={{ textAlign: "left" }}>{b.id_componente}</td><td>{b.cantidad}</td>
                <td>{fmt(b.precio_unitario_usd, 2, " USD")}</td><td>{fmt(b.subtotal_usd, 2, " USD")}</td>
                <td className={b.precio_verificado ? "flag-ok" : "flag-no"}>{b.precio_verificado ? "verificado" : "estimado"}</td>
              </tr>
            ))}
            {bom && (
              <tr><td><strong>Total</strong></td><td /><td /><td /><td><strong>{fmt(total ?? null, 2, " USD")}</strong></td><td /></tr>
            )}
          </tbody>
        </table>
        {!bom && <p className="muted" style={{ padding: 12 }}>Cargando el catálogo de componentes…</p>}
      </div>
    </section>
  );
}

export { MARKS };
