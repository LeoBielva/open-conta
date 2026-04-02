import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/axios'

const TIPOS = [
  { value: '', label: 'Todos' },
  { value: 'faltante', label: 'Pagos Faltantes' },
  { value: 'de_mas', label: 'Pagos de Mas' },
  { value: 'completo', label: 'Pagos Completos' },
]

const CANALES = [
  { value: '', label: 'Todos' },
  { value: 'aliados', label: 'Aliados' },
  { value: 'oxxo', label: 'Oxxo' },
  { value: 'paynet', label: 'Paynet' },
]

export default function Resultados() {
  const [searchParams] = useSearchParams()
  const periodoParam = searchParams.get('periodo') || ''

  const [periodos, setPeriodos] = useState([])
  const [periodo, setPeriodo] = useState(periodoParam)
  const [tipo, setTipo] = useState('')
  const [canal, setCanal] = useState('')
  const [resultados, setResultados] = useState([])
  const [resumen, setResumen] = useState([])
  const [loading, setLoading] = useState(false)

  // Load periodos on mount
  useEffect(() => {
    api.get('/periodos/').then(res => setPeriodos(res.data)).catch(console.error)
  }, [])

  // Load results when filters change
  useEffect(() => {
    if (!periodo) return

    setLoading(true)

    const params = new URLSearchParams({ periodo })
    if (tipo) params.set('tipo', tipo)
    if (canal) params.set('canal', canal)

    Promise.all([
      api.get(`/reconciliacion/resultados/?${params}`),
      api.get(`/reconciliacion/resumen/?periodo=${periodo}`),
    ])
      .then(([resRes, sumRes]) => {
        setResultados(resRes.data)
        setResumen(sumRes.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [periodo, tipo, canal])

  return (
    <div className="resultados-page">
      <h2>Resultados de Reconciliacion</h2>

      <div className="filters">
        <div className="form-group">
          <label>Periodo</label>
          <select value={periodo} onChange={e => setPeriodo(e.target.value)}>
            <option value="">Seleccionar...</option>
            {periodos.map(p => (
              <option key={p.id} value={p.id}>{p.mes_display} {p.anio}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Tipo</label>
          <select value={tipo} onChange={e => setTipo(e.target.value)}>
            {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Canal</label>
          <select value={canal} onChange={e => setCanal(e.target.value)}>
            {CANALES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
      </div>

      {/* Resumen */}
      {resumen.length > 0 && (
        <div className="resumen-section">
          <h3>Resumen</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Canal</th>
                <th>Conteo</th>
                <th>Total Interes</th>
                <th>Total Impuesto</th>
              </tr>
            </thead>
            <tbody>
              {resumen.map((r, i) => (
                <tr key={i}>
                  <td>{r.tipo}</td>
                  <td>{r.canal}</td>
                  <td>{Number(r.conteo).toLocaleString()}</td>
                  <td>${Number(r.total_interes).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                  <td>${Number(r.total_impuesto).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detalle */}
      {loading ? (
        <div className="loading">Cargando resultados...</div>
      ) : resultados.length > 0 ? (
        <div className="detalle-section">
          <h3>Detalle ({resultados.length.toLocaleString()} registros)</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Contrato</th>
                <th>Tipo</th>
                <th>Canal</th>
                <th>Interes</th>
                <th>Impuesto</th>
              </tr>
            </thead>
            <tbody>
              {resultados.slice(0, 500).map(r => (
                <tr key={r.id}>
                  <td>{r.numero_contrato}</td>
                  <td>{r.tipo_display}</td>
                  <td>{r.canal}</td>
                  <td>${Number(r.interes).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                  <td>${Number(r.impuesto).toLocaleString('es-MX', { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {resultados.length > 500 && (
            <p className="truncation-notice">
              Mostrando 500 de {resultados.length.toLocaleString()} registros.
            </p>
          )}
        </div>
      ) : periodo ? (
        <p>No hay resultados para los filtros seleccionados.</p>
      ) : null}
    </div>
  )
}
