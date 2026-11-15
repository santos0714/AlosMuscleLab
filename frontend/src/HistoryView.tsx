import { useEffect, useState } from "react";
import { api, type HistoryItem, type ScenarioRequest } from "./api";
import { fmt, pct } from "./charts";

interface Props {
  refreshKey: number;
  onLoad: (req: ScenarioRequest) => void;
}

export function HistoryView({ refreshKey, onLoad }: Props) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.history().then(setItems).catch((e) => setError(String(e.message ?? e)));
  useEffect(() => { load(); }, [refreshKey]);

  const open = async (id: number) => {
    try {
      onLoad((await api.historyItem(id)).escenario);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  };
  const remove = async (id: number) => {
    try {
      await api.deleteRun(id);
      load();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!items) return <p className="muted">Cargando el historial…</p>;
  if (!items.length) return <div className="empty">Aún no hay simulaciones guardadas. Pulsa Simular y aparecerán aquí.</div>;

  return (
    <section className="view" aria-label="Historial">
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>#</th><th>Nombre</th><th>Fecha</th><th>Etapas recalculadas</th><th>Tiempo</th><th>SNR mínima</th><th>Músculo a 810 nm</th><th>Fuerza a 30 min</th><th /></tr>
          </thead>
          <tbody>
            {items.map((h) => {
              const r = h.resumen;
              return (
                <tr key={h.id}>
                  <td>{h.id}</td>
                  <td>{h.nombre ?? <span className="muted">sin nombre</span>}</td>
                  <td>{new Date(h.creado).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" })}</td>
                  <td>{h.recalculadas.length} de 8</td>
                  <td>{fmt(h.segundos, 1, " s")}</td>
                  <td>{fmt(Math.min(...r.snr_db), 0, " dB")}</td>
                  <td>{pct(r.fraccion_trayectoria_musculo[1])}</td>
                  <td>{pct(r.fuerza_en_marcas.rec_30min)}</td>
                  <td style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                    <button type="button" className="btn btn-small" onClick={() => open(h.id)}>Cargar</button>
                    <button type="button" className="btn btn-small" onClick={() => remove(h.id)} aria-label={`Borrar la simulación ${h.id}`}>Borrar</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
