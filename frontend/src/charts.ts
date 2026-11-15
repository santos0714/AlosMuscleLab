import type { Annotations, Data, Shape } from "plotly.js";
import type { Num, Protocol } from "./api";

export const COLORS = {
  oxi: "#e34948",
  desoxi: "#2a78d6",
  total: "#1baf7a",
  piel: "#e07a8f",
  grasa: "#b08d00",
  musculo: "#a12d3d",
  ink: "#17202b",
  s1: "#2a78d6",
  s2: "#eb6834",
  s3: "#1baf7a",
  s4: "#eda100",
};

export const MARK_LABEL: Record<string, string> = {
  basal: "Basal",
  rec_0min: "0 min",
  rec_5min: "5 min",
  rec_15min: "15 min",
  rec_30min: "30 min",
};

/** Rótulo de una marca sobre el eje de tiempo: minutos desde el final del ejercicio. */
export const MARK_AXIS_LABEL: Record<string, string> = {
  rec_5min: "+5 min",
  rec_15min: "+15 min",
  rec_30min: "+30 min",
};

export const STAGE_LABEL: Record<string, string> = {
  optics: "Óptica del tejido",
  transport: "Transporte de luz",
  physiology: "Fisiología",
  absorption: "Absorción",
  optical_signal: "Señal óptica",
  electronics: "Electrónica",
  processing: "Procesado",
  features: "Rasgos",
};
export const STAGES = Object.keys(STAGE_LABEL);

export const CONTRACTION_LABEL: Record<string, string> = {
  isometric: "Isométrica",
  dynamic: "Dinámica",
  eccentric: "Excéntrica",
};

/** Nombre legible de un nivel de acoplamiento del barrido. */
export function levelLabel(nombre: string): string {
  if (nombre === "ninguno") return "Sin acoplamiento";
  if (nombre === "combinado") return "Combinado";
  let m = nombre.match(/^dano_flujo_([\d.]+)pct$/);
  if (m) return `Daño → flujo (+${m[1]} % de SmO₂ en reposo)`;
  m = nombre.match(/^lenta_hiperemia_([\d.]+)$/);
  if (m) return `Fatiga lenta → hiperemia (${m[1]})`;
  m = nombre.match(/^lenta_mvo2_([\d.]+)$/);
  if (m) return `Fatiga lenta → consumo de O₂ (${m[1]})`;
  return nombre.replace(/_/g, " ");
}

export const minutes = (t: number[]) => t.map((s) => s / 60);

/** Línea de serie temporal. */
export function line(x: number[], y: Num[], name: string, color: string, opts: { dash?: "dash" | "dot"; width?: number; hover?: string; legendgroup?: string; showlegend?: boolean } = {}): Data {
  return {
    type: "scatter",
    mode: "lines",
    x,
    y: y as (number | null)[],
    name,
    line: { color, width: opts.width ?? 2, dash: opts.dash ?? "solid" },
    hovertemplate: opts.hover ?? `%{y:.2f}<extra>${name}</extra>`,
    legendgroup: opts.legendgroup,
    showlegend: opts.showlegend ?? true,
  };
}

/** Sombrea el ejercicio y marca las tomas de recuperación (eje x en minutos). */
export function protocolShapes(p: Protocol, marks: Record<string, number>, withLabels = true): { shapes: Partial<Shape>[]; annotations: Partial<Annotations>[] } {
  const t0 = p.baseline_s / 60;
  const t1 = (p.baseline_s + p.exercise_s) / 60;
  const shapes: Partial<Shape>[] = [
    { type: "rect", xref: "x", yref: "paper", x0: t0, x1: t1, y0: 0, y1: 1, fillcolor: "#17202b", opacity: 0.07, line: { width: 0 }, layer: "below" },
  ];
  const annotations: Partial<Annotations>[] = [];
  for (const [k, t] of Object.entries(marks)) {
    if (k === "basal" || k === "rec_0min") continue;
    shapes.push({ type: "line", xref: "x", yref: "paper", x0: t / 60, x1: t / 60, y0: 0, y1: 1, line: { color: "#b8c1ca", width: 1, dash: "dot" }, layer: "below" });
    if (withLabels) {
      annotations.push({ x: t / 60, y: 1, xref: "x", yref: "paper", xanchor: "left", yanchor: "top", xshift: 4, text: MARK_AXIS_LABEL[k] ?? k, showarrow: false, font: { size: 11, color: "#636c78" } });
    }
  }
  return { shapes, annotations };
}

/** Etiqueta directa al final de una serie (selectiva: solo para pocas series). */
export function endLabel(x: number[], y: Num[], text: string, color: string): Partial<Annotations> {
  let i = y.length - 1;
  while (i > 0 && (y[i] === null || y[i] === undefined)) i--;
  return {
    x: x[i],
    y: y[i] as number,
    text: `<b>${text}</b>`,
    showarrow: false,
    xanchor: "left",
    xshift: 6,
    font: { size: 12, color: "#17202b" },
    bgcolor: "rgba(252,252,251,0.85)",
    bordercolor: color,
    borderwidth: 0,
  };
}

export const fmt = (v: Num | undefined, digits = 2, suffix = "") =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : `${v.toLocaleString("es-MX", { maximumFractionDigits: digits, minimumFractionDigits: digits })}${suffix}`;

export const pct = (v: Num | undefined, digits = 0) => (v === null || v === undefined ? "—" : `${(v * 100).toLocaleString("es-MX", { maximumFractionDigits: digits, minimumFractionDigits: digits })} %`);
