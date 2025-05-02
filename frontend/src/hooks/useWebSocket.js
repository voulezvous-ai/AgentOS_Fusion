// src/components/InputBar.jsx  
import React, { useCallback, useRef, useEffect } from 'react';  
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'; // Usar ícone solid  
import { motion } from 'framer-motion';

/**  
 * Barra de input reutilizável com textarea auto-ajustável e botão de envio.  
 * @param {string} draft - O valor atual do input (controlado pelo componente pai).  
 * @param {function} setDraft - Função para atualizar o valor do input no pai.  
 * @param {function} sendAction - Função a ser chamada ao enviar (clique ou Enter).  
 * @param {string} placeholder - Placeholder para o textarea.  
 * @param {boolean} disabled - Desabilita input e botão.  
 */  
function InputBar({ draft, setDraft, sendAction, placeholder = "Digite sua mensagem...", disabled = false }) {  
  const textareaRef = useRef(null);

  // Auto-ajuste da altura do textarea  
  useEffect(() => {  
    const textarea = textareaRef.current;  
    if (textarea) {  
      textarea.style.height = 'auto'; // Resetar altura  
      const scrollHeight = textarea.scrollHeight;  
      // Definir altura máxima (ex: 5 linhas) - ajuste conforme necessário  
      const maxHeight = 120; // Aproximadamente 5 linhas com line-height padrão  
      textarea.style.height = `${Math.min(scrollHeight, maxHeight)}px`;  
      // Habilitar scroll vertical se conteúdo exceder maxHeight  
      textarea.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';  
    }  
  }, [draft]); // Reajustar quando o texto mudar

  // Handler para mudança no input  
  const handleChange = (event) => {  
    setDraft(event.target.value);  
  };

  // Handler para pressionar tecla (Enter para enviar, Shift+Enter para nova linha)  
  const handleKeyDown = useCallback((event) => {  
    // Verificar se Enter foi pressionado sem Shift e se não está desabilitado  
    if (event.key === 'Enter' && !event.shiftKey && !disabled && draft.trim()) {  
      event.preventDefault(); // Impedir nova linha padrão do Enter  
      sendAction();  
    }  
  }, [sendAction, disabled, draft]);

  // Handler para clique no botão  
  const handleSendClick = useCallback(() => {  
    if (!disabled && draft.trim()) {  
      sendAction();  
    }  
  }, [sendAction, disabled, draft]);

  const isSendDisabled = disabled || !draft.trim();

  return (  
    // Usar cores do tema  
    <div className="flex items-end p-3 md:p-4 bg-fusion-dark border-t border-fusion-medium space-x-3">  
      <textarea  
        ref={textareaRef}  
        value={draft}  
        onChange={handleChange}  
        onKeyDown={handleKeyDown}  
        placeholder={placeholder}  
        disabled={disabled}  
        rows="1" // Iniciar com 1 linha  
        className="flex-1 resize-none bg-fusion-medium/40 rounded-lg p-3 text-sm text-fusion-text-primary placeholder-fusion-light focus:outline-none focus:ring-2 focus:ring-fusion-purple border border-transparent focus:border-transparent transition duration-150 ease-in-out scrollbar disabled:opacity-60 disabled:cursor-not-allowed" // Adicionar scrollbar class  
        style={{ minHeight: '44px', maxHeight: '120px' }} // Definir min/max height inline  
      />  
      <motion.button  
        onClick={handleSendClick}  
        disabled={isSendDisabled}  
        className={`p-2 rounded-full transition-colors duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-fusion-dark ${  
          isSendDisabled  
            ? 'bg-fusion-medium text-fusion-light cursor-not-allowed'  
            : 'bg-fusion-purple hover:bg-fusion-purple-hover text-white' // Use theme colors  
        }`}  
        whileHover={!isSendDisabled ? { scale: 1.1 } : {}}  
        whileTap={!isSendDisabled ? { scale: 0.9 } : {}}  
        title="Enviar Mensagem (Enter)"  
      >  
        <PaperAirplaneIcon className="w-5 h-5 transform rotate-0" /> {/* Ajustar rotação se necessário */}  
      </motion.button>  
    </div>  
  );  
}

export default InputBar;  
