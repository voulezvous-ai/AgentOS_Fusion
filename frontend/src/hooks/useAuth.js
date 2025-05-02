// src/components/ProtectedRoute.jsx  
import React from 'react';  
import { Navigate, useLocation } from 'react-router-dom';  
import { useAuth } from '../hooks/useAuth';  
import LoadingSpinner from './LoadingSpinner'; // Opcional: para mostrar loading

/**  
 * Componente HOC (Higher-Order Component) ou Wrapper para proteger rotas.  
 * Verifica se o usuário está autenticado usando o useAuth hook.  
 * Redireciona para /login se não autenticado.  
 * Mostra um loading enquanto o estado de autenticação inicial está sendo verificado.  
 */  
const ProtectedRoute = ({ children }) => {  
  const { isAuthenticated, loading } = useAuth();  
  const location = useLocation(); // Para guardar a página que o usuário tentou acessar

  // Mostrar loading enquanto o AuthContext verifica o token inicial  
  if (loading) {  
    return (  
      <div className="flex items-center justify-center h-screen w-screen bg-fusion-deep">  
        <LoadingSpinner />  
        <span className='ml-2 text-fusion-light'>Verificando autenticação...</span>  
      </div>  
    );  
  }

  // Se não estiver autenticado (e o loading terminou), redirecionar para login  
  if (!isAuthenticated) {  
    console.log('ProtectedRoute: User not authenticated, redirecting to login.');  
    // Guardar a rota atual para redirecionar de volta após login  
    return <Navigate to="/login" state={{ from: location }} replace />;  
    // 'replace' evita que a rota protegida entre no histórico de navegação  
  }

  // Se autenticado, renderizar o componente filho (a página protegida)  
  return children;  
};

export default ProtectedRoute;  
