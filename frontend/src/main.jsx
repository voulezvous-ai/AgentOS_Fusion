// src/App.jsx  
import React from 'react';  
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';  
import { AuthProvider } from './context/AuthContext';  
import { WebSocketProvider } from './context/WebSocketContext'; // Importar WS Provider

// Layout, Páginas e Proteção  
import FusionShell from './components/FusionShell';  
import LoginPage from './routes/LoginPage';  
import CommsPage from './routes/CommsPage';  
import AdvisorPage from './routes/AdvisorPage';  
import ProtectedRoute from './components/ProtectedRoute';

// Logger para debug  
const logger = { debug: console.debug, info: console.info };

function App() {  
  logger.debug("App component rendering...");

  return (  
    <AuthProvider>  
      {/* WebSocketProvider precisa estar DENTRO do AuthProvider para acessar o token/user */}  
      <WebSocketProvider>  
        <BrowserRouter>  
          <Routes>  
            {/* Rota de Login (Pública) */}  
            <Route path="/login" element={<LoginPage />} />

            {/* Rotas Protegidas dentro do Shell */}  
            <Route  
              path="/"  
              element={  
                <ProtectedRoute>  
                  <FusionShell>  
                    {/* O Outlet implícito renderizará as rotas aninhadas */}  
                    {/* Vamos definir as rotas aninhadas diretamente */}  
                  </FusionShell>  
                </ProtectedRoute>  
              }  
            >  
                {/* Rota Index - Redirecionar para /comms por padrão */}  
                {/* Usar Navigate como elemento filho de Route com index */}  
                <Route index element={<Navigate to="/comms" replace />} />

                {/* Rota Comms */}  
                <Route path="/comms" element={<CommsPage />} />  
                {/* Opcional: Rota para chat específico */}  
                {/* <Route path="/comms/:chatId" element={<CommsPage />} /> */}

                {/* Rota Advisor */}  
                <Route path="/advisor" element={<AdvisorPage />} />  
                 {/* Opcional: Rota para conversa Advisor específica */}  
                 {/* <Route path="/advisor/:conversationId" element={<AdvisorPage />} /> */}

                 {/* Adicionar outras rotas protegidas aqui (ex: /settings, /orders) */}  
                 {/* Exemplo: <Route path="/settings" element={<SettingsPage />} /> */}

            </Route>

            {/* Rota Catch-all (404) - Opcional */}  
            <Route path="*" element={<Navigate to="/" replace />} />  
             {/* Ou renderizar um componente 404: */}  
             {/* <Route path="*" element={<NotFoundPage />} /> */}

          </Routes>  
        </BrowserRouter>  
      </WebSocketProvider>  
    </AuthProvider>  
  );  
}

export default App;  
