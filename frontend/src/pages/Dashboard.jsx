import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../contexts/AuthContext'

export default function Dashboard() {
  const { isAdmin } = useAuth()
  const [periodos, setPeriodos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/periodos/')
      .then(res => setPeriodos(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Cargando periodos...</div>

  return (
    <div className="dashboard">
      <h2>Periodos de Reconciliacion</h2>

      {periodos.length === 0 ? (
        <p>No hay periodos registrados. {isAdmin && 'Sube archivos para comenzar.'}</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Periodo</th>
              <th>Creado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {periodos.map(p => (
              <tr key={p.id}>
                <td>{p.mes_display} {p.anio}</td>
                <td>{new Date(p.created_at).toLocaleDateString('es-MX')}</td>
                <td>
                  <Link to={`/resultados?periodo=${p.id}`}>Ver Resultados</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {isAdmin && (
        <div className="dashboard-actions">
          <Link to="/upload" className="btn-primary">Subir Archivos</Link>
        </div>
      )}
    </div>
  )
}
