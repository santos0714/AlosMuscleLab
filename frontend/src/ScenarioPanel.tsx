import { useId } from "react";
import type { Catalog, ParamInfo, Profile, ScenarioForm } from "./api";

interface Props {
  catalog: Catalog;
  profiles: Profile[];
  form: ScenarioForm;
  onChange: (f: ScenarioForm) => void;
}

interface NumProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  slider?: boolean;
  hint?: string;
  changed?: boolean;
}

function NumField({ label, value, onChange, unit, min, max, step = 0.1, slider, hint, changed }: NumProps) {
  const id = useId();
  const set = (raw: string) => {
    const v = Number(raw);
    if (raw !== "" && Number.isFinite(v)) onChange(v);
  };
  return (
    <div className={`field${changed ? " changed" : ""}`}>
      <label htmlFor={id}>
        {label} {unit && <span className="unit">({unit})</span>}
      </label>
      <input id={id} type="number" value={value} min={min} max={max} step={step} onChange={(e) => set(e.target.value)} />
      {slider && min !== undefined && max !== undefined && (
        <input type="range" aria-label={`${label}, deslizador`} value={value} min={min} max={max} step={step} onChange={(e) => set(e.target.value)} />
      )}
      {hint && <span className="hint">{hint}</span>}
    </div>
  );
}

const PARAM_NAMES: Record<string, string> = {
  hb_blood_g_dl: "Hemoglobina en sangre",
  blood_volume_fraction: "Fracción de sangre en el músculo",
  myoglobin_mM: "Mioglobina",
  smbo2_rest: "Saturación de mioglobina en reposo",
  mvo2_rest_uM_s: "Consumo de O₂ en reposo",
  mvo2_max_factor: "Consumo máximo / reposo",
  flow_rest_ml_min_100ml: "Flujo en reposo",
  flow_peak_ml_min_100ml: "Flujo tras el ejercicio",
  occlusion_full_pct_mvc: "Oclusión completa",
  occlusion_onset_pct_mvc: "Inicio de oclusión",
  tau_pcr_s: "Constante de recuperación de PCr",
  tau_ph_s: "Constante de recuperación del pH",
  tau_force_fast_s: "Recuperación rápida de la fuerza",
  tau_force_slow_s: "Recuperación lenta de la fuerza",
  force_slow_fraction: "Fracción lenta de la fatiga",
  force_drop_reference: "Caída de fuerza de referencia",
  force_drop_eccentric: "Caída de fuerza tras excéntrico",
  volume_hyperemia_gain: "Sobreimpulso de volumen",
  coupling_damage_flow: "Acoplamiento daño → flujo",
  coupling_slow_hyperemia: "Acoplamiento fatiga lenta → hiperemia",
  coupling_slow_mvo2: "Acoplamiento fatiga lenta → consumo",
};

function ParamField({ p, value, onChange }: { p: ParamInfo; value: number; onChange: (v: number | null) => void }) {
  const id = useId();
  const changed = value !== p.por_defecto;
  const nombre = PARAM_NAMES[p.campo] ?? p.descripcion ?? p.campo;
  const step = Math.abs(p.por_defecto) >= 10 ? 1 : Math.abs(p.por_defecto) >= 1 ? 0.1 : 0.005;
  return (
    <div className={`field param${changed ? " changed" : ""}`}>
      <label htmlFor={id} title={p.descripcion ?? p.campo}>
        {nombre} {p.unidades && <span className="unit">({p.unidades})</span>}
      </label>
      <input id={id} type="number" step={step} value={value} onChange={(e) => {
        const v = Number(e.target.value);
        if (e.target.value !== "" && Number.isFinite(v)) onChange(v === p.por_defecto ? null : v);
      }} />
      <span className="hint">
        {p.supuesto ? <span className="badge assumed">supuesto</span> : p.rango ? `Publicado: ${p.rango[0]} a ${p.rango[1]}` : ""}
        {!p.supuesto && p.verificado === false && <> <span className="badge">sin verificar</span></>}
        {changed && <> <button type="button" className="btn btn-small" onClick={() => onChange(null)}>Restablecer</button></>}
      </span>
    </div>
  );
}

export function ScenarioPanel({ catalog, profiles, form, onChange }: Props) {
  const t = form.tissue, s = form.sensor, p = form.protocol, st = form.settings;
  const rangos = catalog.tejido.rangos;
  const set = <K extends keyof ScenarioForm>(k: K, v: ScenarioForm[K]) => onChange({ ...form, [k]: v });
  const nameId = useId(), profId = useId(), contrId = useId(), engId = useId();

  const chooseProfile = (nombre: string) => {
    const pr = profiles.find((x) => x.nombre === nombre);
    if (!pr) return;
    set("tissue", {
      profile: nombre,
      att_mm: pr.datos.att_mm,
      skin_mm: pr.datos.skin_mm ?? catalog.tejido.skin_mm,
      melanosome_epidermis: pr.datos.melanosome_epidermis ?? catalog.tejido.melanosome_epidermis,
    });
  };

  const physChanged = Object.keys(form.physiology).length;

  return (
    <form className="panel" aria-label="Parámetros del escenario" onSubmit={(e) => e.preventDefault()}>
      <fieldset className="group">
        <legend>Escenario</legend>
        <div className="field">
          <label htmlFor={nameId}>Nombre para el historial</label>
          <span />
          <input id={nameId} type="text" style={{ gridColumn: "1 / -1" }} placeholder="Sin nombre" value={form.name}
                 onChange={(e) => set("name", e.target.value)} maxLength={120} />
        </div>
      </fieldset>

      <fieldset className="group">
        <legend>Tejido</legend>
        <div className="field">
          <label htmlFor={profId}>Perfil de sujeto</label>
          <span />
          <select id={profId} style={{ gridColumn: "1 / -1" }} value={t.profile} onChange={(e) => chooseProfile(e.target.value)}>
            {profiles.map((pr) => (
              <option key={pr.nombre} value={pr.nombre}>{pr.nombre.replace(/_/g, " ")}{pr.tipo === "guardado" ? " (guardado)" : ""}</option>
            ))}
          </select>
        </div>
        <NumField label="Grasa subcutánea" unit="mm" value={t.att_mm} min={0.5} max={15} step={0.1} slider
                  hint={`Publicado en bíceps: ${rangos.att_mm[0]} a ${rangos.att_mm[1]} mm`}
                  onChange={(v) => set("tissue", { ...t, att_mm: v })} />
        <NumField label="Piel" unit="mm" value={t.skin_mm} min={0.5} max={5} step={0.1}
                  hint={`Publicado: ${rangos.skin_mm[0]} a ${rangos.skin_mm[1]} mm`}
                  onChange={(v) => set("tissue", { ...t, skin_mm: v })} />
        <NumField label="Melanina en la epidermis" unit="fracción" value={t.melanosome_epidermis} min={0} max={0.6} step={0.01} slider
                  hint="0.02 piel clara, 0.3 piel oscura"
                  onChange={(v) => set("tissue", { ...t, melanosome_epidermis: v })} />
      </fieldset>

      <fieldset className="group">
        <legend>Sensor</legend>
        <NumField label="Distancia emisor-detector" unit="mm" value={s.sds_mm} min={10} max={50} step={1} slider
                  onChange={(v) => set("sensor", { ...s, sds_mm: v })} />
        <div className="field">
          <span id="led-l" style={{ gridColumn: "1 / -1", fontSize: "0.875rem", color: "var(--ink-2)" }}>Potencia de los LED (mW)</span>
          <div className="trio" role="group" aria-labelledby="led-l" style={{ gridColumn: "1 / -1" }}>
            {s.led_power_mW.map((v, i) => (
              <label key={i}>
                <span>{catalog.sensor.leds[i]?.peak_nm ?? ""} nm</span>
                <input type="number" min={0.1} step={0.5} value={v} onChange={(e) => {
                  const n = Number(e.target.value);
                  if (Number.isFinite(n) && n > 0) set("sensor", { ...s, led_power_mW: s.led_power_mW.map((x, j) => (j === i ? n : x)) });
                }} />
              </label>
            ))}
          </div>
        </div>
        <NumField label="Ganancia del amplificador" unit="MΩ" value={s.tia_rf_ohm / 1e6} min={0.01} step={0.1}
                  hint={`${catalog.sensor.tia.part}`} onChange={(v) => set("sensor", { ...s, tia_rf_ohm: v * 1e6 })} />
        <NumField label="Capacitor de realimentación" unit="pF" value={s.tia_cf_pF} min={0.1} step={0.5}
                  onChange={(v) => set("sensor", { ...s, tia_cf_pF: v })} />
        <NumField label="Resolución del ADC" unit="bits" value={s.adc_bits} min={8} max={32} step={1}
                  hint={catalog.sensor.adc.part} onChange={(v) => set("sensor", { ...s, adc_bits: Math.round(v) })} />
        <NumField label="Luz ambiental" unit="nA" value={s.ambient_photocurrent_nA} min={0} step={0.1}
                  onChange={(v) => set("sensor", { ...s, ambient_photocurrent_nA: v })} />
      </fieldset>

      <fieldset className="group">
        <legend>Ejercicio</legend>
        <div className="field">
          <label htmlFor={contrId}>Tipo de contracción</label>
          <span />
          <select id={contrId} style={{ gridColumn: "1 / -1" }} value={p.contraction}
                  onChange={(e) => set("protocol", { ...p, contraction: e.target.value as typeof p.contraction })}>
            <option value="isometric">Isométrica</option>
            <option value="dynamic">Dinámica</option>
            <option value="eccentric">Excéntrica</option>
          </select>
        </div>
        <NumField label="Intensidad" unit="% MVC" value={p.intensity_pct_mvc} min={5} max={100} step={1} slider
                  onChange={(v) => set("protocol", { ...p, intensity_pct_mvc: v })} />
        <NumField label="Duración del ejercicio" unit="s" value={p.exercise_s} min={5} max={3000} step={5}
                  onChange={(v) => set("protocol", { ...p, exercise_s: v })} />
        <NumField label="Ciclo de trabajo" unit="fracción" value={p.duty_cycle} min={0.05} max={1} step={0.05}
                  hint="Fracción del tiempo en contracción (dinámico y excéntrico)"
                  onChange={(v) => set("protocol", { ...p, duty_cycle: v })} />
        <NumField label="Reposo inicial" unit="s" value={p.baseline_s} min={30} max={600} step={10}
                  onChange={(v) => set("protocol", { ...p, baseline_s: v })} />
        <NumField label="Recuperación registrada" unit="s" value={p.recovery_s} min={60} max={4000} step={60}
                  hint="Las marcas llegan hasta 30 min (1800 s)"
                  onChange={(v) => set("protocol", { ...p, recovery_s: v })} />
      </fieldset>

      <fieldset className="group">
        <legend>Cálculo</legend>
        <div className="field">
          <label htmlFor={engId}>Motor de transporte</label>
          <span />
          <select id={engId} style={{ gridColumn: "1 / -1" }} value={st.engine}
                  onChange={(e) => set("settings", { ...st, engine: e.target.value as typeof st.engine })}>
            <option value="diffusion">Difusión de N capas (segundos)</option>
            <option value="montecarlo">Monte Carlo propio (lento)</option>
            <option value="mcx">MCX-CL (requiere OpenCL)</option>
          </select>
        </div>
        {st.engine !== "diffusion" && (
          <NumField label="Fotones por longitud de onda" value={st.n_photons} min={10000} max={2000000} step={10000}
                    onChange={(v) => set("settings", { ...st, n_photons: Math.round(v) })} />
        )}
        <NumField label="DPF supuesto en Beer-Lambert" value={st.assumed_dpf} min={1} max={10} step={0.01}
                  hint="4.16: valor publicado para antebrazo" onChange={(v) => set("settings", { ...st, assumed_dpf: v })} />
        <label className="check">
          <input type="checkbox" checked={st.noise} onChange={(e) => set("settings", { ...st, noise: e.target.checked })} />
          Ruido del sensor
        </label>
        <NumField label="Semilla del ruido" value={st.seed} min={0} step={1} onChange={(v) => set("settings", { ...st, seed: Math.round(v) })} />
      </fieldset>

      <details className="group">
        <summary>Fisiología del sujeto{physChanged ? ` (${physChanged} cambiados)` : ""}</summary>
        <p className="muted" style={{ fontSize: "0.82rem" }}>
          Los marcados como supuesto no vienen de una medida: están calibrados para reproducir resultados publicados.
        </p>
        {catalog.fisiologia.map((pi) => (
          <ParamField key={pi.campo} p={pi} value={form.physiology[pi.campo] ?? pi.por_defecto}
                      onChange={(v) => {
                        const next = { ...form.physiology };
                        if (v === null) delete next[pi.campo];
                        else next[pi.campo] = v;
                        set("physiology", next);
                      }} />
        ))}
      </details>
    </form>
  );
}
