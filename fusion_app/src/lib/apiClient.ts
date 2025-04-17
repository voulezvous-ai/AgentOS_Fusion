import axios from 'axios'
import { logger } from '@/utils/logger'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor de Requisição: Adiciona token JWT, se disponível.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      logger.debug('[API Client] Token adicionado à requisição.')
    } else {
      logger.debug('[API Client] Nenhum token encontrado.')
    }
    return config
  },
  (error) => {
    logger.error('[API Client] Erro na requisição:', error)
    return Promise.reject(error)
  }
)

// Interceptor de Resposta: Trata erros e autenticação.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    logger.error('[API Client] Erro na resposta:', error.response || error.message)
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        logger.warn('[API Client] 401 Unauthorized. Token inválido ou expirado.')
        localStorage.removeItem('authToken')
      }
      return Promise.reject({ status, detail: data?.detail || 'Erro na API', raw: error.response })
    } else if (error.request) {
      return Promise.reject({ status: null, detail: 'Erro de rede ou sem resposta do servidor', raw: error })
    } else {
      return Promise.reject({ status: null, detail: `Erro de configuração: ${error.message}`, raw: error })
    }
  }
)

export default apiClient