import React, { useState, useEffect } from 'react'
import { FusionShell } from './components/FusionShell'
import { Login } from './components/Login'
import { logger } from './utils/logger'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(true)

  useEffect(() => {
    const token = localStorage.getItem('authToken')
    if (token) {
      logger.log('[App] Token de autenticação encontrado.')
      setIsAuthenticated(true)
    } else {
      logger.log('[App] Nenhum token encontrado.')
    }
    setIsLoadingAuth(false)
  }, [])

  const handleLoginSuccess = () => {
    logger.log('[App] Login realizado com sucesso.')
    setIsAuthenticated(true)
  }

  if (isLoadingAuth)
    return <div className="flex items-center justify-center h-screen bg-gray-900 text-white">Carregando...</div>

  return (
    <div>
      {isAuthenticated ? <FusionShell /> : <Login onLoginSuccess={handleLoginSuccess} />}
    </div>
  )
}

export default App