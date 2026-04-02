import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'

const MESES = [
  { value: 1, label: 'Enero' },
  { value: 2, label: 'Febrero' },
  { value: 3, label: 'Marzo' },
  { value: 4, label: 'Abril' },
  { value: 5, label: 'Mayo' },
  { value: 6, label: 'Junio' },
  { value: 7, label: 'Julio' },
  { value: 8, label: 'Agosto' },
  { value: 9, label: 'Septiembre' },
  { value: 10, label: 'Octubre' },
  { value: 11, label: 'Noviembre' },
  { value: 12, label: 'Diciembre' },
]

export default function Upload() {
  const [mes, setMes] = useState(1)
  const [anio, setAnio] = useState(new Date().getFullYear())
  const [archivoCuotas, setArchivoCuotas] = useState(null)
  const [archivoSat, setArchivoSat] = useState(null)
  const [loading, setLoading] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResultado(null)
    setLoading(true)

    try {
      // 1. Crear o encontrar el periodo
      let periodoId
      try {
        const res = await api.post('/periodos/', { mes, anio })
        periodoId = res.data.id
      } catch (err) {
        // Si ya existe, buscar el periodo
        if (err.response?.status === 400) {
          const listRes = await api.get('/periodos/')
          const found = listRes.data.find(p => p.mes === mes && p.anio === anio)
          if (found) {
            periodoId = found.id
          } else {
            throw new Error('No se pudo crear ni encontrar el periodo.')
          }
        } else {
          throw err
        }
      }

      // 2. Subir archivos y ejecutar reconciliacion
      const formData = new FormData()
      formData.append('periodo_id', periodoId)
      formData.append('archivo_cuotas', archivoCuotas)
      formData.append('archivo_sat', archivoSat)

      const res = await api.post('/reconciliacion/upload/', formData)
      setResultado(res.data)
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Error al procesar.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="upload-page">
      <h2>Subir Archivos de Reconciliacion</h2>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="mes">Mes</label>
            <select id="mes" value={mes} onChange={e => setMes(Number(e.target.value))}>
              {MESES.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="anio">Ano</label>
            <input
              id="anio"
              type="number"
              value={anio}
              onChange={e => setAnio(Number(e.target.value))}
              min={2020}
              max={2030}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="cuotas">Archivo CUOTAS_MEXICO (.xlsx)</label>
          <input
            id="cuotas"
            type="file"
            accept=".xlsx"
            onChange={e => setArchivoCuotas(e.target.files[0])}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="sat">Archivo Base SAT Mexico (.xlsx)</label>
          <input
            id="sat"
            type="file"
            accept=".xlsx"
            onChange={e => setArchivoSat(e.target.files[0])}
            required
          />
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" disabled={loading}>
          {loading ? 'Procesando...' : 'Subir y Reconciliar'}
        </button>
      </form>

      {resultado && (
        <div className="resultado-summary">
          <h3>Reconciliacion completada: {resultado.periodo}</h3>
          <p>Filas CUOTAS: {resultado.filas_cuotas?.toLocaleString()}</p>
          <p>Filas SAT: {resultado.filas_sat?.toLocaleString()}</p>

          <h4>Resumen por canal</h4>
          <table className="data-table">
            <thead>
              <tr>
                <th>Canal</th>
                <th>Faltantes</th>
                <th>De Mas</th>
                <th>Completos</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(resultado.resumen || {}).map(([canal, data]) => (
                <tr key={canal}>
                  <td>{canal}</td>
                  <td>{data.faltantes?.toLocaleString()}</td>
                  <td>{data.de_mas?.toLocaleString()}</td>
                  <td>{data.completos?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={() => navigate(`/resultados?periodo=${resultado.periodo_id}`)}>
            Ver Resultados Detallados
          </button>
        </div>
      )}
    </div>
  )
}
