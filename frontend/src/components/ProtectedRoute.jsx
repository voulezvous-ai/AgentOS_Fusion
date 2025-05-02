// src/routes/LoginPage.jsx  
import React, { useState, useEffect } from 'react';  
import { useLocation, useNavigate } from 'react-router-dom';  
import { useAuth } from '../hooks/useAuth'; // Usar nosso hook  
import { motion } from 'framer-motion';  
import LoadingSpinner from '../components/LoadingSpinner'; // Importar spinner

function LoginPage() {  
  const [email, setEmail] = useState(''); // Usar 'email' como username  
  const [password, setPassword] = useState('');  
  const { login, loading, error, isAuthenticated } = useAuth();  
  const navigate = useNavigate();  
  const location = useLocation();

  // Redirecionar se já estiver autenticado  
  useEffect(() => {  
    if (isAuthenticated) {  
      const from = location.state?.from?.pathname || '/comms'; // Redireciona para onde veio ou /comms  
      console.log(`LoginPage: Already authenticated, redirecting to ${from}`);  
      navigate(from, { replace: true });  
    }  
  }, [isAuthenticated, navigate, location.state]);

  const handleSubmit = async (e) => {  
    e.preventDefault();  
    if (!email || !password) {  
      // Poderia usar o setError do AuthContext, mas é mais local  
      alert("Por favor, preencha o email e a senha.");  
      return;  
    }  
    try {  
       await login(email, password);  
       // Navegação é feita dentro do 'login' do AuthContext em caso de sucesso  
    } catch (loginError) {  
       // O erro já é tratado e logado no AuthContext  
       // O estado 'error' do AuthContext será atualizado e podemos exibi-lo  
       console.error("Login attempt failed in component:", loginError);  
       // Poderíamos ter um estado local de erro também, mas usar o global é mais simples aqui  
    }  
  };

  return (  
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-fusion-deep via-gray-900 to-fusion-dark p-4">  
      <motion.div  
        initial={{ opacity: 0, y: -20 }}  
        animate={{ opacity: 1, y: 0 }}  
        transition={{ duration: 0.5 }}  
        className="w-full max-w-md p-8 space-y-6 bg-fusion-dark rounded-xl shadow-2xl border border-fusion-medium/30"  
      >  
        {/* Placeholder for Logo */}  
        <div className="text-center">  
            {/* <img src="/path/to/your/logo.svg" alt="Logo" className="w-24 h-24 mx-auto mb-4"/> */}  
             <h1 className="text-3xl font-bold text-center text-fusion-purple mb-6">  
                Fusion Login  
             </h1>  
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">  
          {/* Email Input */}  
          <div>  
            <label  
              htmlFor="email"  
              className="block text-sm font-medium text-fusion-text-secondary mb-1"  
            >  
              Email (Usuário)  
            </label>  
            <input  
              id="email"  
              name="email"  
              type="email"  
              autoComplete="email"  
              required  
              value={email}  
              onChange={(e) => setEmail(e.target.value)}  
              disabled={loading}  
              className="appearance-none block w-full px-4 py-2.5 border border-fusion-medium bg-fusion-deep rounded-md shadow-sm placeholder-fusion-light focus:outline-none focus:ring-2 focus:ring-fusion-purple focus:border-transparent text-sm text-fusion-text-primary disabled:opacity-50"  
              placeholder="seu@email.com"  
            />  
          </div>

          {/* Password Input */}  
          <div>  
            <label  
              htmlFor="password"  
              className="block text-sm font-medium text-fusion-text-secondary mb-1"  
            >  
              Senha  
            </label>  
            <input  
              id="password"  
              name="password"  
              type="password"  
              autoComplete="current-password"  
              required  
              value={password}  
              onChange={(e) => setPassword(e.target.value)}  
              disabled={loading}  
              className="appearance-none block w-full px-4 py-2.5 border border-fusion-medium bg-fusion-deep rounded-md shadow-sm placeholder-fusion-light focus:outline-none focus:ring-2 focus:ring-fusion-purple focus:border-transparent text-sm text-fusion-text-primary disabled:opacity-50"  
              placeholder="Sua senha"  
            />  
          </div>

          {/* Error Display */}  
          {error && !loading && (  
             <motion.div  
                 initial={{ opacity: 0 }} animate={{ opacity: 1 }}  
                 className="p-3 rounded-md bg-red-800/50 border border-fusion-error text-center text-sm text-red-200"  
              >  
               {error}  
             </motion.div>  
           )}

          {/* Submit Button */}  
          <div>  
            <button  
              type="submit"  
              disabled={loading}  
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-fusion-purple hover:bg-fusion-purple-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-fusion-dark focus:ring-fusion-purple disabled:opacity-60 disabled:cursor-not-allowed transition duration-150 ease-in-out"  
            >  
              {loading ? (  
                <>  
                  <LoadingSpinner className="w-5 h-5 mr-2"/>  
                  Entrando...  
                </>  
              ) : (  
                'Entrar'  
              )}  
            </button>  
          </div>  
        </form>  
         {/* Opcional: Links esqueci senha / registro */}  
         {/* <div className="text-center text-sm mt-6">  
             <a href="#" className="font-medium text-fusion-purple-light hover:text-fusion-purple">  
                 Esqueceu sua senha?  
             </a>  
         </div> */}  
      </motion.div>  
    </div>  
  );  
}

export default LoginPage;  
