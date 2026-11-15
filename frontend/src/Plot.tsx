import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { Config, Data, Layout } from "plotly.js";

const INK = "#17202b";
const INK2 = "#4a5462";
const GRID = "#e4e8ec";
const AXIS = "#b8c1ca";
const SURFACE = "#fcfcfb";

export const baseAxis = {
  gridcolor: GRID,
  linecolor: AXIS,
  zeroline: false,
  ticks: "outside" as const,
  tickcolor: AXIS,
  ticklen: 4,
  automargin: true,
  title: { font: { size: 12, color: INK2 } },
};

const BASE_LAYOUT: Partial<Layout> = {
  font: { family: '"Public Sans Variable", "Public Sans", system-ui, sans-serif', size: 12, color: INK2 },
  paper_bgcolor: SURFACE,
  plot_bgcolor: SURFACE,
  margin: { l: 56, r: 24, t: 28, b: 44 },
  hovermode: "x unified",
  hoverlabel: { bgcolor: "#ffffff", bordercolor: AXIS, font: { color: INK, size: 12 } },
  legend: { orientation: "h", x: 0, y: 1.02, yanchor: "bottom", font: { size: 12, color: INK } },
  showlegend: true,
};

const CONFIG: Partial<Config> = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["select2d", "lasso2d", "autoScale2d", "toggleSpikelines"],
  toImageButtonOptions: { format: "png", scale: 2 },
  locale: "es",
};

interface Props {
  data: Data[];
  layout?: Partial<Layout>;
  tall?: boolean;
  label: string; // descripción accesible del gráfico
}

export function Plot({ data, layout, tall, label }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const lay: Partial<Layout> = {
      ...BASE_LAYOUT,
      ...layout,
      xaxis: { ...baseAxis, ...(layout?.xaxis ?? {}) },
      yaxis: { ...baseAxis, ...(layout?.yaxis ?? {}) },
    };
    void Plotly.react(el, data, lay, CONFIG);
  }, [data, layout]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      if (el.offsetParent !== null) void Plotly.Plots.resize(el);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      Plotly.purge(el);
    };
  }, []);

  return <div ref={ref} className={tall ? "plot tall" : "plot"} role="img" aria-label={label} />;
}
