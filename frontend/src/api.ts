// Tipos y llamadas a la API de MuscleSense Lab (backend/musclesense/api).

export type Num = number | null;

export interface ParamInfo {
  campo: string;
  por_defecto: number;
  supuesto: boolean;
  fuente?: string;
  descripcion?: string;
  rango?: [number, number];
  unidades?: string;
  verificado?: boolean;
  referencias?: string[];
}

export interface LedInfo {
  part: string;
  peak_nm: number;
  fwhm_nm: number;
  radiant_power_mW: number;
  [k: string]: unknown;
}

export interface Catalog {
  fisiologia: ParamInfo[];
  protocolo: Protocol;
  ajustes: Settings;
  sensor: {
    sds_mm: number;
    tia: { part: string; rf_ohm: number; cf_pF: number; en_nV_rtHz: number; in_fA_rtHz: number; cin_pF: number };
    adc: { part: string; bits: number; vref_V: number };
    leds: LedInfo[];
    ambient_photocurrent_nA: number;
  };
  perfiles: Record<string, ProfileData>;
  tejido: {
    skin_mm: number;
    att_mm: number;
    melanosome_epidermis: number;
    musculo_mm: number;
    rangos: Record<"att_mm" | "skin_mm" | "melanosome_epidermis", [number, number]>;
  };
}

export interface Protocol {
  baseline_s: number;
  exercise_s: number;
  intensity_pct_mvc: number;
  contraction: "isometric" | "dynamic" | "eccentric";
  duty_cycle: number;
  recovery_s: number;
  occlusion_test_s: number;
  sample_rate_hz: number;
}

export interface Settings {
  engine: "diffusion" | "montecarlo" | "mcx";
  n_photons: number;
  seed: number;
  noise: boolean;
  led_spectrum_points: number;
  assumed_dpf: number;
  use_led_spectrum_in_mbll: boolean;
  lowpass_hz: number;
}

export interface ProfileData {
  att_mm: number;
  skin_mm?: number;
  melanosome_epidermis?: number;
}

export interface Profile {
  nombre: string;
  datos: ProfileData;
  tipo: "predefinido" | "guardado";
}

export interface TissueForm {
  profile: string;
  att_mm: number;
  skin_mm: number;
  melanosome_epidermis: number;
}

export interface SensorForm {
  sds_mm: number;
  tia_rf_ohm: number;
  tia_cf_pF: number;
  adc_bits: number;
  led_power_mW: number[];
  ambient_photocurrent_nA: number;
}

export interface ScenarioForm {
  name: string;
  tissue: TissueForm;
  sensor: SensorForm;
  protocol: Protocol;
  settings: Settings;
  physiology: Record<string, number>; // solo los valores cambiados respecto al catálogo
}

export type Features = Record<string, Num>;

export interface RunSummary {
  longitudes_onda_nm: number[];
  snr_db: number[];
  saturado: boolean;
  fotocorriente_basal_nA: number[];
  trayectorias_parciales_mm: { piel: number[]; grasa: number[]; musculo: number[] };
  fraccion_trayectoria_musculo: number[];
  rasgos_estimados: Features;
  rasgos_verdaderos: Features;
  fuerza_en_marcas: Record<string, number>;
  marcas_s: Record<string, number>;
  tejido: Record<string, { grosor_mm: Num }>;
}

export type Conc = Record<"d_oxy" | "d_deoxy" | "d_total" | "d_diff", Num[]>;

export interface RunSeries {
  t_s: number[];
  fisiologia: Record<string, Num[]>;
  verdad_uM: Conc;
  estimado_uM: Conc;
  atenuacion: Record<string, Num[]>;
  fotocorriente_nA: Record<string, Num[]>;
}

export interface RunResponse {
  id: number | null;
  recalculadas: string[];
  huellas: Record<string, string>;
  segundos: number;
  resumen: RunSummary;
  series: RunSeries;
}

export interface HistoryItem {
  id: number;
  nombre: string | null;
  creado: string;
  recalculadas: string[];
  resumen: RunSummary;
  segundos: number;
}

export interface HistoryDetail extends HistoryItem {
  escenario: ScenarioRequest;
}

export interface ScenarioRequest {
  name?: string | null;
  physiology: Record<string, number>;
  protocol: Partial<Protocol>;
  tissue: { profile: string; att_mm?: number | null; skin_mm?: number | null; melanosome_epidermis?: number | null };
  sensor: Partial<SensorForm>;
  settings: Partial<Settings>;
  output_rate_hz?: number;
  save?: boolean;
}

export interface Level {
  nombre: string;
  descripcion: string;
  valores: Record<string, number>;
}

export interface GainRow {
  nivel: string;
  alcance: string;
  r2_nulo?: Num;
  r2_dosis?: Num;
  r2_nirs?: Num;
  r2_dosis_nirs?: Num;
  r2_dosis_oraculo?: Num;
  ganancia_nirs?: Num;
  ganancia_oraculo?: Num;
  perdida_instrumento?: Num;
}

export interface DissociationRow {
  nivel: string;
  marca: string;
  n: number;
  reox_frac_media: Num;
  fuerza_media: Num;
  fuerza_min: Num;
  reoxigenados: Num;
  recuperados: Num;
  reox_sin_fuerza: Num;
}

export interface StudyPoint {
  sujeto: string;
  nivel: string;
  marca: string;
  contraccion: string;
  fuerza: number;
  verdad_reox_frac: Num;
  nirs_reox_frac?: Num;
}

export interface StudyResult {
  sujetos: number;
  descartes: number;
  fallos: unknown[];
  niveles: Level[];
  ganancia: GainRow[];
  disociacion: DissociationRow[];
  puntos: StudyPoint[];
}

export interface Study {
  id: number;
  creado: string;
  estado: "en_cola" | "en_curso" | "terminado" | "error";
  progreso: number;
  parametros: { n_subjects: number; seed: number; levels: string[] | null; optics: boolean; models: string[] };
  resultado?: StudyResult | null;
  error?: string | null;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      /* respuesta sin JSON */
    }
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  catalog: () => call<Catalog>("/api/parametros"),
  profiles: () => call<Profile[]>("/api/perfiles"),
  saveProfile: (p: { name: string; att_mm: number; skin_mm?: number; melanosome_epidermis: number }) =>
    call("/api/perfiles", { method: "POST", body: JSON.stringify(p) }),
  run: (req: ScenarioRequest) => call<RunResponse>("/api/escenarios/ejecutar", { method: "POST", body: JSON.stringify(req) }),
  history: () => call<HistoryItem[]>("/api/historial?limit=100"),
  historyItem: (id: number) => call<HistoryDetail>(`/api/historial/${id}`),
  deleteRun: (id: number) => call<void>(`/api/historial/${id}`, { method: "DELETE" }),
  catalogComponents: () => call<ComponentCatalog>("/api/catalogo"),
  levels: () => call<Level[]>("/api/estudios/niveles"),
  studies: () => call<Study[]>("/api/estudios"),
  study: (id: number) => call<Study>(`/api/estudios/${id}`),
  startStudy: (p: { n_subjects: number; seed: number; levels: string[] | null; optics: boolean }) =>
    call<{ id: number }>("/api/estudios", { method: "POST", body: JSON.stringify({ ...p, models: ["ridge"] }) }),
};

export interface BomRow {
  concepto: string;
  id_componente: string;
  cantidad: number;
  precio_unitario_usd: number;
  subtotal_usd: number;
  precio_verificado: boolean;
}

export interface ComponentCatalog {
  bom_recomendada: BomRow[];
  bom_total_usd: number | { [k: string]: unknown };
  [k: string]: unknown;
}

/** Convierte el formulario en la petición que espera la API. */
export function toRequest(f: ScenarioForm, save: boolean): ScenarioRequest {
  return {
    name: f.name.trim() || null,
    physiology: f.physiology,
    protocol: f.protocol,
    tissue: {
      profile: f.tissue.profile,
      att_mm: f.tissue.att_mm,
      skin_mm: f.tissue.skin_mm,
      melanosome_epidermis: f.tissue.melanosome_epidermis,
    },
    sensor: f.sensor,
    settings: f.settings,
    output_rate_hz: 1,
    save,
  };
}

/** Formulario inicial con los valores por defecto del catálogo. */
export function defaultForm(c: Catalog): ScenarioForm {
  return {
    name: "",
    tissue: {
      profile: "referencia",
      att_mm: c.perfiles.referencia?.att_mm ?? c.tejido.att_mm,
      skin_mm: c.tejido.skin_mm,
      melanosome_epidermis: c.perfiles.referencia?.melanosome_epidermis ?? c.tejido.melanosome_epidermis,
    },
    sensor: {
      sds_mm: c.sensor.sds_mm,
      tia_rf_ohm: c.sensor.tia.rf_ohm,
      tia_cf_pF: c.sensor.tia.cf_pF,
      adc_bits: c.sensor.adc.bits,
      led_power_mW: c.sensor.leds.map((l) => l.radiant_power_mW),
      ambient_photocurrent_nA: c.sensor.ambient_photocurrent_nA,
    },
    protocol: { ...c.protocolo },
    settings: { ...c.ajustes },
    physiology: {},
  };
}

/** Formulario a partir de un escenario guardado en el historial. */
export function formFromRequest(c: Catalog, r: ScenarioRequest): ScenarioForm {
  const base = defaultForm(c);
  return {
    name: r.name ?? "",
    tissue: {
      profile: r.tissue?.profile ?? base.tissue.profile,
      att_mm: r.tissue?.att_mm ?? base.tissue.att_mm,
      skin_mm: r.tissue?.skin_mm ?? base.tissue.skin_mm,
      melanosome_epidermis: r.tissue?.melanosome_epidermis ?? base.tissue.melanosome_epidermis,
    },
    sensor: { ...base.sensor, ...stripNulls(r.sensor ?? {}) },
    protocol: { ...base.protocol, ...stripNulls(r.protocol ?? {}) },
    settings: { ...base.settings, ...stripNulls(r.settings ?? {}) },
    physiology: { ...(r.physiology ?? {}) },
  };
}

function stripNulls<T extends object>(o: T): Partial<T> {
  return Object.fromEntries(Object.entries(o).filter(([, v]) => v !== null && v !== undefined)) as Partial<T>;
}
