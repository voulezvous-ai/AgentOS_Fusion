// src/components/AdvisorHistorySidebar.jsx  
import React, { useState, useEffect, useCallback, forwardRef, useImperativeHandle } from 'react'; // Added forwardRef, useImperativeHandle  
import { motion, AnimatePresence } from 'framer-motion';  
import apiClient from '../services/api';  
// import { useAuth } from '../context/AuthContext'; // Auth likely handled by interceptor  
import LoadingSpinner from './LoadingSpinner';  
import { formatDistanceToNow } from 'date-fns';  
import { ptBR } from 'date-fns/locale';  
import { PlusIcon, TrashIcon, ChatBubbleLeftEllipsisIcon, ArrowPathIcon } from '@heroicons/react/24/outline'; // Added ArrowPathIcon

const logger = { info: console.log, error: console.error, warn: console.warn, debug: console.debug };

function ConversationItem({ conversation, isSelected, onSelect, onDelete }) {  
    const updatedAt = conversation.updated_at ? new Date(conversation.updated_at) : new Date();  
    let timeAgo = 'data inválida';  
    try {  
        timeAgo = formatDistanceToNow(updatedAt, { addSuffix: true, locale: ptBR });  
    } catch (e) {  
        logger.warn(`Could not format date for conversation ${conversation.id}: ${conversation.updated_at}`, e);  
    }

     const handleDeleteClick = (e) => {  
        e.stopPropagation();  
        if (window.confirm(`Tem certeza que deseja deletar a conversa "${conversation.title || 'sem título'}"?`)) {  
             onDelete(conversation.id);  
        }  
    };

    return (  
        <motion.div  
            layout  
            initial={{ opacity: 0, y: 5 }}  
            animate={{ opacity: 1, y: 0 }}  
            exit={{ opacity: 0, transition: { duration: 0.1 } }}  
            transition={{ duration: 0.2, type: "spring", stiffness: 100 }}  
            onClick={() => onSelect(conversation.id)}  
            className={`flex items-center justify-between p-2.5 rounded-md cursor-pointer transition-colors duration-150 group ${  
                isSelected ? 'bg-fusion-purple/60' : 'hover:bg-fusion-medium/50'  
            }`}  
        >  
            <div className="flex items-center space-x-2 overflow-hidden flex-1 min-w-0"> {/* Added flex-1 min-w-0 */}  
                 <ChatBubbleLeftEllipsisIcon className="w-4 h-4 text-fusion-light flex-shrink-0" />  
                 <span className={`text-sm truncate ${isSelected ? 'text-fusion-text-primary font-semibold' : 'text-fusion-text-secondary'}`}>  
                     {conversation.title || "Conversa sem título"}  
                 </span>  
            </div>  
            <div className="flex items-center space-x-1 flex-shrink-0 pl-2">  
                {/* Show time always, hide delete button initially */}  
                <span className={`text-[10px] transition-opacity duration-150 ${isSelected ? 'text-fusion-text-secondary' : 'text-fusion-light group-hover:opacity-0'}`}>  
                    {timeAgo}  
                </span>  
                <button  
                     onClick={handleDeleteClick}  
                     title="Deletar conversa"  
                     className={`p-1 rounded text-fusion-light hover:text-fusion-error opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity ${isSelected ? 'opacity-100' : ''}`}  
                 >  
                    <TrashIcon className="w-4 h-4" />  
                </button>  
            </div>  
        </motion.div>  
    );  
}

// Use forwardRef to allow parent (AdvisorPage) to call refreshHistory  
const AdvisorHistorySidebar = forwardRef(({ currentConversationId, onSelectConversation, onNewConversation, isLoading }, ref) => {  
    // const { token } = useAuth(); // Handled by interceptor  
    const [conversations, setConversations] = useState([]);  
    const [loadingHistory, setLoadingHistory] = useState(false);  
    const [error, setError] = useState(null);

    const fetchHistory = useCallback(async () => {  
        setLoadingHistory(true);  
        setError(null);  
        try {  
            const response = await apiClient.get('/advisor/conversations', { params: { limit: 100 } });  
            const sortedConversations = (response.data || []).sort((a, b) =>  
                new Date(b.updated_at) - new Date(a.updated_at)  
            );  
            setConversations(sortedConversations);  
        } catch (err) {  
            logger.error("Erro ao buscar histórico do Advisor:", err);  
            setError("Falha ao carregar histórico.");  
            setConversations([]);  
        } finally {  
            setLoadingHistory(false);  
        }  
    }, []);

    useEffect(() => {  
        fetchHistory();  
    }, [fetchHistory]);

    const handleDelete = async (conversationId) => {  
        if (isLoading || loadingHistory) return;  
        const conversationTitle = conversations.find(c => c.id === conversationId)?.title || 'esta conversa';  
        // Use custom confirm or library later  
        if (!window.confirm(`Tem certeza que deseja deletar "${conversationTitle}"?`)) {  
            return;  
        }

        logger.info(`Deletando conversa ${conversationId}`);  
        try {  
            await apiClient.delete(`/advisor/conversations/${conversationId}`);  
            // Optimistic UI update  
            setConversations(prev => prev.filter(c => c.id !== conversationId));  
            if (currentConversationId === conversationId) {  
                onNewConversation();  
            }  
            // Optional: show success toast/message  
        } catch (err) {  
            logger.error(`Erro ao deletar conversa ${conversationId}:`, err);  
            setError("Falha ao deletar conversa.");  
            // Revert optimistic update? Or just show error and let user refresh.  
            // fetchHistory(); // Refetch to get consistent state on error  
            setTimeout(() => setError(null), 3000);  
        }  
    };

    // Expose the fetchHistory function to the parent component using useImperativeHandle  
    useImperativeHandle(ref, () => ({  
        refreshHistory: () => {  
            logger.debug("Refreshing Advisor history list via ref...");  
            fetchHistory();  
        }  
    }));

    return (  
        // Use theme colors  
        <div className="w-64 bg-fusion-dark h-full flex flex-col border-r border-fusion-medium">  
             {/* New Conversation Button */}  
             <div className="p-3 border-b border-fusion-medium">  
                 <button  
                    onClick={onNewConversation}  
                    className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-md text-sm font-medium bg-fusion-purple hover:bg-fusion-purple-hover text-white transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-fusion-purple-light focus:ring-offset-2 focus:ring-offset-fusion-dark disabled:opacity-60 disabled:cursor-not-allowed"  
                    disabled={isLoading || loadingHistory}  
                 >  
                     <PlusIcon className="w-5 h-5"/>  
                     <span>Nova Conversa</span>  
                 </button>  
             </div>

             {/* Conversation List */}  
             <div className="flex-grow overflow-y-auto p-2 space-y-1 scrollbar"> {/* Added scrollbar class */}  
                 {loadingHistory && (  
                    <div className="p-4 text-center">  
                         <LoadingSpinner />  
                    </div>  
                  )}  
                 {!loadingHistory && error && (  
                     <p className="p-4 text-center text-fusion-error text-xs">{error}</p>  
                  )}  
                 {!loadingHistory && !error && conversations.length === 0 && (  
                     <p className="p-4 text-center text-fusion-light text-sm italic">Nenhuma conversa ainda.</p>  
                 )}  
                 <AnimatePresence>  
                     {!loadingHistory && !error && conversations.map(conv => (  
                         <ConversationItem  
                             key={conv.id}  
                             conversation={conv}  
                             isSelected={conv.id === currentConversationId}  
                             onSelect={onSelectConversation}  
                             onDelete={handleDelete}  
                         />  
                     ))}  
                 </AnimatePresence>  
             </div>  
             {/* Refresh Button Footer */}  
             <div className="p-2 border-t border-fusion-medium text-center">  
                 <button  
                    onClick={fetchHistory}  
                    className="text-xs text-fusion-light hover:text-fusion-text-primary disabled:opacity-50 disabled:cursor-wait flex items-center justify-center w-full py-1"  
                    disabled={loadingHistory}  
                    title="Atualizar lista"  
                 >  
                     <ArrowPathIcon className={`w-3.5 h-3.5 mr-1 ${loadingHistory ? 'animate-spin' : ''}`}/>  
                     {loadingHistory ? 'Carregando...' : 'Atualizar Histórico'}  
                 </button>  
             </div>  
        </div>  
    );  
});

// Set display name for debugging  
AdvisorHistorySidebar.displayName = 'AdvisorHistorySidebar';

export default AdvisorHistorySidebar;

