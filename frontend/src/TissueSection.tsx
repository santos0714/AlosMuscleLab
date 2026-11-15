import { COLORS, pct } from "./charts";
import type { RunSummary } from "./api";

interface Props {
  skinMm: number;
  attMm: number;
  sdsMm: number;
  summary: RunSummary | null; // último cálculo (porcentajes de recorrido)
  stale: boolean; // el formulario cambió desde ese cálculo
}

const W = 960; // ancho del dibujo en unidades SVG
const MARGIN_MM = 9; // margen lateral a cada lado del par emisor-detector
const MUSCLE_SHOWN_MM = 10;
const TOP = 46; // espacio para emisor, detector y cota

/**
 * Corte del brazo a escala real (misma escala en horizontal y vertical): piel, grasa subcutánea
 * y músculo, con el emisor y el detector a la distancia elegida. La "banana" de fotones es
 * ilustrativa; los porcentajes de recorrido por capa son los que calculó la simulación.
 */
export function TissueSection({ skinMm, attMm, sdsMm, summary, stale }: Props) {
  const widthMm = sdsMm + 2 * MARGIN_MM;
  const k = W / widthMm; // px por mm
  const depthMm = skinMm + attMm + MUSCLE_SHOWN_MM;
  const H = TOP + depthMm * k + 8;
  const y = (mm: number) => TOP + mm * k;
  const xe = MARGIN_MM * k;
  const xd = (MARGIN_MM + sdsMm) * k;
  const xm = (xe + xd) / 2;

  // Banana ilustrativa: curvas de Bézier cuadráticas (la profundidad máxima es la mitad del control)
  const band = (dIn: number, dOut: number) => {
    const cOut = y(2 * dOut);
    const cIn = y(2 * dIn);
    return `M ${xe} ${TOP} Q ${xm} ${cOut} ${xd} ${TOP} Q ${xm} ${cIn} ${xe} ${TOP} Z`;
  };
  const deep = Math.min(0.42 * sdsMm, depthMm - 0.5);

  // Porcentaje del recorrido medio por capa, a la longitud de onda central del sensor
  const idx = summary ? Math.floor(summary.longitudes_onda_nm.length / 2) : -1;
  const frac = (capa: "piel" | "grasa" | "musculo") => {
    if (!summary) return null;
    const t = summary.trayectorias_parciales_mm;
    const tot = t.piel[idx] + t.grasa[idx] + t.musculo[idx];
    return tot > 0 ? t[capa][idx] / tot : null;
  };
  const lam = summary ? summary.longitudes_onda_nm[idx] : null;

  const layers = [
    { key: "piel" as const, name: "Piel", top: 0, h: skinMm, color: COLORS.piel },
    { key: "grasa" as const, name: "Grasa subcutánea", top: skinMm, h: attMm, color: COLORS.grasa },
    { key: "musculo" as const, name: "Bíceps braquial", top: skinMm + attMm, h: MUSCLE_SHOWN_MM, color: COLORS.musculo },
  ];

  return (
    <figure className="section-figure" aria-labelledby="corte-titulo">
      <div className="section-head">
        <h2 id="corte-titulo">Corte del brazo bajo el sensor</h2>
        <p>
          {summary
            ? `Recorrido medio de la luz por capa a ${lam} nm${stale ? ", del último cálculo" : ""}. La forma de la trayectoria es ilustrativa.`
            : "Calculando el recorrido de la luz…"}
        </p>
      </div>
      <svg className="tissue-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Piel de ${skinMm} mm, grasa de ${attMm} mm y músculo; emisor y detector separados ${sdsMm} mm`}>
        <defs>
          <linearGradient id="fade" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#fcfcfb" stopOpacity="0" />
            <stop offset="1" stopColor="#fcfcfb" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        {layers.map((l) => (
          <rect key={l.key} x={0} y={y(l.top)} width={W} height={l.h * k} fill={l.color} opacity={l.key === "musculo" ? 0.85 : 0.75} />
        ))}
        {/* el músculo continúa hacia abajo */}
        <rect x={0} y={y(depthMm - 4)} width={W} height={4 * k + 8} fill="url(#fade)" />
        {/* separaciones de 2 px entre capas */}
        {layers.slice(1).map((l) => (
          <line key={l.key} x1={0} x2={W} y1={y(l.top)} y2={y(l.top)} stroke="#fcfcfb" strokeWidth={2} />
        ))}

        <path className="banana" d={band(0.1 * sdsMm, deep)} fill="#fcfcfb" opacity={0.35} />
        <path className="banana" d={band(0.18 * sdsMm, 0.3 * sdsMm)} fill="#fcfcfb" opacity={0.45} />

        {/* emisor y detector */}
        <g>
          <rect x={xe - 14} y={TOP - 18} width={28} height={14} rx={3} fill={COLORS.ink} />
          <text x={xe} y={TOP - 24} textAnchor="middle" fontSize={12} fontWeight={600}>LED 760, 810 y 850 nm</text>
          <rect x={xd - 14} y={TOP - 18} width={28} height={14} rx={3} fill="#fcfcfb" stroke={COLORS.ink} strokeWidth={2} />
          <text x={xd} y={TOP - 24} textAnchor="middle" fontSize={12} fontWeight={600}>Fotodiodo</text>
          <line x1={xe + 18} x2={xd - 18} y1={TOP - 11} y2={TOP - 11} stroke={COLORS.ink} strokeWidth={1} markerStart="" />
          <text x={xm} y={TOP - 15} textAnchor="middle" fontSize={12}>{`${sdsMm} mm`}</text>
        </g>

        {/* rótulos de capa con su porcentaje de recorrido */}
        {layers.map((l) => {
          const f = frac(l.key);
          const cy = y(l.top + Math.min(l.h, 6) / 2);
          const grosor = l.key === "musculo" ? "" : `${l.h.toLocaleString("es-MX", { maximumFractionDigits: 1 })} mm`;
          const texto = [grosor, f !== null ? `${pct(f)} del recorrido` : null].filter(Boolean).join(", ");
          return (
            <g key={l.key}>
              <text x={12} y={cy + 4} className={`layer-label${l.key === "musculo" ? " on-dark" : ""}`}>{l.name}</text>
              <text x={W - 12} y={cy + 4} textAnchor="end" className={`layer-value${l.key === "musculo" ? " on-dark" : ""}`}>{texto}</text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
