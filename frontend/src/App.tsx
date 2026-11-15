import { useCallback, useEffect, useRef, useState } from "react";
import { api, defaultForm, formFromRequest, toRequest, type Catalog, type Profile, type Protocol, type RunResponse, type ScenarioForm, type ScenarioRequest } from "./api";
import { STAGES, STAGE_LABEL } from "./charts";
import { HistoryView } from "./HistoryView";
import { RecoveryView } from "./RecoveryView";
import { ScenarioPanel } from "./ScenarioPanel";
import { TissueSection } from "./TissueSection";
import { LightView, PhysiologyView, SensorView, SignalView } from "./views";

const TABS = [
  { id: "senal", label: "Señal" },
  { id: "fisiologia", label: "Fisiología" },
  { id: "luz", label: "Luz y tejido" },
  { id: "sensor", label: "Sensor" },
  { id: "recuperacion", label: "Recuperación" },
  { id: "historial", label: "Historial" },
] as const;
type TabId = (typeof TABS)[number]["id"];

interface Ran {
  result: RunResponse;
  form: ScenarioForm; // formulario con el que se calculó
}

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [form, setForm] = useState<ScenarioForm | null>(null);
  const [ran, setRan] = useState<Ran | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("senal");
  const [historyKey, setHistoryKey] = useState(0);
  const first = useRef(true);

  const run = useCallback(async (f: ScenarioForm, save: boolean) => {
    setRunning(true);
    setError(null);
    try {
      const result = await api.run(toRequest(f, save));
      setRan({ result, form: f });
      if (save) setHistoryKey((k) => k + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }, []);

  useEffect(() => {
    Promise.all([api.catalog(), api.profiles()])
      .then(([c, p]) => {
        setCatalog(c);
        setProfiles(p);
        const f = defaultForm(c);
        setForm(f);
        if (first.current) {
          first.current = false;
          void run(f, false); // primer cálculo sin guardarlo en el historial
        }
      })
      .catch((e) => setError(`No se pudo conectar con la API: ${e.message}. ¿Está corriendo uvicorn?`));
  }, [run]);

  const loadFromHistory = (req: ScenarioRequest) => {
    if (!catalog) return;
    const f = formFromRequest(catalog, req);
    setForm(f);
    setTab("senal");
    void run(f, false);
  };

  if (!catalog || !form) {
    return (
      <main className="main">
        <h1>MuscleSense Lab</h1>
        {error ? <p className="error">{error}</p> : <p className="muted">Cargando parámetros…</p>}
      </main>
    );
  }

  const dirty = !!ran && JSON.stringify(ran.form) !== JSON.stringify(form);
  const recomputed = new Set(ran?.result.recalculadas ?? []);
  const protocolOfRun: Protocol = ran?.form.protocol ?? form.protocol;
  const viewProps = ran ? { result: ran.result, protocol: protocolOfRun, assumedDpf: ran.form.settings.assumed_dpf } : null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>MuscleSense Lab</h1>
          <p>Sensor NIRS de onda continua sobre el bíceps braquial</p>
        </div>
        <div className="run">
          <span className={`status${dirty ? " dirty" : ""}`} role="status">
            {running ? "Calculando la cadena…" : dirty ? "Hay cambios sin simular" : ran ? "Resultados al día" : ""}
          </span>
          <button type="button" className="btn btn-primary" disabled={running} onClick={() => run(form, true)}>
            {running ? "Simulando…" : "Simular"}
          </button>
        </div>
        <div className="chain-row">
          <ol className="chain" aria-label="Etapas de la cadena de simulación">
            {STAGES.map((s) => (
              <li key={s}>
                <span className={`stage${recomputed.has(s) ? " on" : ""}`} title={recomputed.has(s) ? "Recalculada en la última simulación" : "Reutilizada de la caché"}>
                  {STAGE_LABEL[s]}
                </span>
              </li>
            ))}
          </ol>
          <div className="chain-caption">
            {!ran
              ? "Aún no hay simulación."
              : ran.result.recalculadas.length === 0
                ? "Nada cambió: todas las etapas se reutilizaron de la caché."
                : `Oscuras: recalculadas en la última simulación (${ran.result.recalculadas.length} de 8, ${ran.result.segundos.toFixed(1)} s). Claras: reutilizadas.`}
          </div>
        </div>
        {error && <p className="error" style={{ flexBasis: "100%", margin: 0 }}>{error}</p>}
      </header>

      <ScenarioPanel catalog={catalog} profiles={profiles} form={form} onChange={setForm} />

      <main className="main">
        <TissueSection skinMm={form.tissue.skin_mm} attMm={form.tissue.att_mm} sdsMm={form.sensor.sds_mm} summary={ran?.result.resumen ?? null} stale={dirty} />

        <div className="tabs" role="tablist" aria-label="Vistas">
          {TABS.map((t) => (
            <button key={t.id} type="button" role="tab" id={`tab-${t.id}`} aria-controls={`panel-${t.id}`} aria-selected={tab === t.id} className="tab" onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>

        <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
          {tab === "recuperacion" ? (
            <RecoveryView />
          ) : tab === "historial" ? (
            <HistoryView refreshKey={historyKey} onLoad={loadFromHistory} />
          ) : !viewProps ? (
            <div className="empty">{running ? "Simulando el escenario de referencia…" : "Pulsa Simular para calcular el escenario."}</div>
          ) : tab === "senal" ? (
            <SignalView {...viewProps} />
          ) : tab === "fisiologia" ? (
            <PhysiologyView {...viewProps} />
          ) : tab === "luz" ? (
            <LightView {...viewProps} sdsMm={ran!.form.sensor.sds_mm} />
          ) : (
            <SensorView {...viewProps} catalog={catalog} />
          )}
        </div>
      </main>
    </div>
  );
}
