import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { user, isAdmin, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/">Open Conta</Link>
        </div>
        <div className="navbar-links">
          <Link to="/">Dashboard</Link>
          {isAdmin && <Link to="/upload">Subir Archivos</Link>}
          <Link to="/resultados">Resultados</Link>
        </div>
        <div className="navbar-user">
          <span>{user?.email}</span>
          <span className="role-badge">{isAdmin ? 'Admin' : 'Usuario'}</span>
          <button onClick={handleSignOut}>Salir</button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
