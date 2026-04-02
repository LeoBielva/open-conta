import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Resultados from './pages/Resultados'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/upload"
              element={
                <ProtectedRoute requireAdmin>
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route path="/resultados" element={<Resultados />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
