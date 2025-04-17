import React, { useState } from 'react'
import apiClient from '@/lib/apiClient'
import { logger } from '@/utils/logger'

interface LoginProps {
  onLoginSuccess: () => void
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState(import.meta.env.VITE_TEST_USERNAME || '')
  const [password, setPassword] = useState(import.meta.env.VITE_TEST_PASSWORD || '')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)
    logger.log(`[Login] Tentando login para ${username}`)
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)
      const response = await apiClient.post('/auth/login', formData, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
      const token = response.data?.access_token
      if (token) {
        logger.success("[Login] Login realizado com sucesso.")
        localStorage.setItem('authToken', token)
        onLoginSuccess()
      } else {
        throw new Error("Token de acesso não encontrado.")
      }
    } catch (err: any) {
      logger.error("[Login] Falha no login:", err)
      setError(err?.detail || err?.message || "Falha no login. Verifique as credenciais.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gray-900">
      <form onSubmit={handleLogin} className="p-8 bg-gray-800 rounded-lg shadow-xl w-full max-w-sm">
        <h2 className="text-2xl font-bold mb-6 text-center text-white">FusionApp Login</h2>
        {error && <p className="mb-4 text-center text-red-400 bg-red-900/50 p-2 rounded">{error}</p>}
        <div className="mb-4">
          <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
        <div className="mb-6">
          <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-2 bg-sky-600 text-white rounded-md hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-wait"
        >
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  )
}