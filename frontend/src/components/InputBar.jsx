// src/components/ChatList.jsx  
import React, { useState, useEffect, useCallback } from 'react';  
import { motion, AnimatePresence } from 'framer-motion';  
import apiClient from '../services/api';  
import { useWebSocket } from '../hooks/useWebSocket';  
import LoadingSpinner from './LoadingSpinner';  
import { formatDistanceToNow } from 'date-fns';  
import { ptBR } from 'date-fns/locale';  
import { UserCircleIcon } from '@heroicons/react/24/solid'; // Example icon

const logger = { info: console.log, error: console.error, warn: console.warn, debug: console.debug };

// Individual Chat Item Component  
function ChatListItem({ chat, isSelected, onSelect }) {  
  const {  
    id, // User WA ID serves as chat ID  
    contact_name,  
    last_message_preview,  
    last_message_ts,  
    unread_count,  
    mode,  
    status  
  } = chat;

  let timeAgo = '';  
  if (last_message_ts) {  
    try {  
      timeAgo = formatDistanceToNow(new Date(last_message_ts), { addSuffix: true, locale: ptBR });  
    } catch (e) {  
      logger.warn(`Could not format date for chat ${id}: ${last_message_ts}`, e);  
      timeAgo = 'data inválida';  
    }  
  }

  const itemVariants = {  
    hidden: { opacity: 0, y: 10 },  
    visible: { opacity: 1, y: 0 },  
    exit: { opacity: 0, x: -20 }  
  };

  return (  
    <motion.li  
      layout  
      variants={itemVariants}  
      initial="hidden"  
      animate="visible"  
      exit="exit"  
      onClick={() => onSelect(id)}  
      className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors duration-150 ease-out group ${  
        isSelected ? 'bg-fusion-purple/30' : 'hover:bg-fusion-medium/40'  
      }`}  
    >  
      {/* Avatar Placeholder */}  
      <div className="flex-shrink-0">  
        <UserCircleIcon className={`w-10 h-10 ${isSelected ? 'text-fusion-purple-light' : 'text-fusion-light'}`} />  
      </div>

      {/* Chat Info */}  
      <div className="flex-1 min-w-0">  
        <div className="flex justify-between items-center">  
          <span className={`text-sm font-semibold truncate ${isSelected ? 'text-fusion-text-primary' : 'text-fusion-text-secondary group-hover:text-fusion-text-primary'}`}>  
            {contact_name || id} {/* Show WA ID if name is missing */}  
          </span>  
          <span className={`text-[10px] flex-shrink-0 ml-2 ${isSelected ? 'text-fusion-text-secondary' : 'text-fusion-light'}`}>  
            {timeAgo}  
          </span>  
        </div>  
        <div className="flex justify-between items-center mt-1">  
          <p className={`text-xs truncate ${isSelected ? 'text-fusion-text-secondary' : 'text-fusion-light'}`}>  
            {last_message_preview || 'Nenhuma mensagem ainda.'}  
          </p>  
          {/* Unread Count Badge */}  
          {unread_count > 0 && (  
            <motion.span  
               initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2 }}  
               className="flex-shrink-0 ml-2 bg-fusion-purple text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full"  
             >  
              {unread_count > 9 ? '9+' : unread_count}  
            </motion.span>  
          )}  
           {/* Mode Indicator (Optional) */}  
           {/* <span className={`text-[9px] px-1 rounded ${mode === 'agent' ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'}`}>{mode}</span> */}  
        </div>  
      </div>  
    </motion.li>  
  );  
}

// Main Chat List Component  
function ChatList({ selectedChatId, onSelectChat }) {  
  const [chats, setChats] = useState([]);  
  const [isLoading, setIsLoading] = useState(false);  
  const [error, setError] = useState(null);  
  const { lastJsonMessage } = useWebSocket(); // To listen for updates

  // Fetch initial chat list  
  const fetchChats = useCallback(async () => {  
    setIsLoading(true);  
    setError(null);  
    logger.info("Fetching chat list...");  
    try {  
      // Assuming the API endpoint returns sorted chats (most recent first)  
      // And includes last_message_preview and unread_count  
      const response = await apiClient.get('/whatsapp/chats', { params: { limit: 50 } }); // Add params if needed  
      setChats(response.data || []);  
    } catch (err) {  
      logger.error("Error fetching chat list:", err);  
      setError("Falha ao carregar conversas.");  
      setChats([]);  
    } finally {  
      setIsLoading(false);  
    }  
  }, []);

  useEffect(() => {  
    fetchChats();  
  }, [fetchChats]);

  // Handle WebSocket updates  
  useEffect(() => {  
    if (!lastJsonMessage) return;

    const { type, payload } = lastJsonMessage;

    // --- Logic to update chat list based on WS message ---  
    // Example: New message received  
    if (type === 'new_whatsapp_message' && payload) {  
       logger.debug("WS: new_whatsapp_message received in ChatList", payload);  
       setChats(prevChats => {  
           const chatId = payload.chat_id;  
           const existingChatIndex = prevChats.findIndex(c => c.id === chatId);  
           let updatedChats = [...prevChats];

           // Create or update chat data based on message payload  
           const updatedChatData = {  
               id: chatId,  
               contact_id: chatId, // Assuming chat_id is user WA ID  
               contact_name: payload.metadata?.contact_name || prevChats.find(c=>c.id === chatId)?.contact_name || chatId,  
               last_message_preview: payload.content?.substring(0, 30) + (payload.content?.length > 30 ? '...' : ''),  
               last_message_ts: payload.timestamp,  
               // Increment unread count ONLY if message is from contact and chat is not selected  
               unread_count: (existingChatIndex !== -1 && prevChats[existingChatIndex].id !== selectedChatId && payload.sender_id === chatId)  
                                ? (prevChats[existingChatIndex].unread_count || 0) + 1  
                                : (existingChatIndex !== -1 ? prevChats[existingChatIndex].unread_count : (payload.sender_id === chatId ? 1 : 0)),  
               mode: prevChats.find(c=>c.id === chatId)?.mode || 'human', // Keep existing mode or default  
               status: 'open' // Assume new message opens the chat  
           };

           if (existingChatIndex !== -1) {  
               // Update existing chat  
               updatedChats[existingChatIndex] = { ...updatedChats[existingChatIndex], ...updatedChatData };  
           } else {  
               // Add new chat  
               updatedChats.push(updatedChatData);  
           }

           // Sort: Move updated/new chat to the top  
           return updatedChats.sort((a, b) => {  
               if (a.id === chatId) return -1; // Move current chat to top  
               if (b.id === chatId) return 1;  
               // Fallback sort by timestamp  
               return new Date(b.last_message_ts || 0) - new Date(a.last_message_ts || 0);  
           });  
       });  
    }  
     // Example: Chat mode update  
     else if (type === 'whatsapp_chat_mode_update' && payload) {  
        logger.debug("WS: whatsapp_chat_mode_update received in ChatList", payload);  
         setChats(prev => prev.map(chat =>  
             chat.id === payload.chat_id ? { ...chat, mode: payload.new_mode } : chat  
         ));  
     }  
     // Example: Message status update (might affect preview or unread count indirectly)  
     else if (type === 'whatsapp_message_status' && payload) {  
         // Maybe update preview if 'failed_send'? Or clear unread if 'read'?  
         // Requires more complex logic based on message ID mapping if needed here.  
         logger.debug("WS: whatsapp_message_status received in ChatList", payload);  
     }

  }, [lastJsonMessage, selectedChatId]);

   // Handle chat selection - Reset unread count locally  
   const handleSelect = useCallback((chatId) => {  
       if (chatId === selectedChatId) return; // Prevent re-selecting same chat  
       onSelectChat(chatId);  
       // Optimistically reset unread count in UI  
       setChats(prev => prev.map(chat =>  
           chat.id === chatId ? { ...chat, unread_count: 0 } : chat  
       ));  
       // TODO: Optionally call an API endpoint to mark messages as read in backend  
       // apiClient.post(`/whatsapp/chats/${chatId}/mark_read`).catch(...)  
   }, [onSelectChat, selectedChatId]);

  return (  
    // Use theme colors  
    <div className="w-80 h-full bg-fusion-dark flex flex-col border-r border-fusion-medium">  
      {/* Header (Optional) */}  
      <div className="p-4 border-b border-fusion-medium flex-shrink-0">  
        <h2 className="text-lg font-semibold text-fusion-text-primary">Conversas</h2>  
        {/* Add Search/Filter Input? */}  
      </div>

      {/* List Area (Scrollable) */}  
      <div className="flex-grow overflow-y-auto p-2 scrollbar"> {/* Added scrollbar class */}  
        {isLoading && (  
          <div className="p-4 text-center"><LoadingSpinner /></div>  
        )}  
        {!isLoading && error && (  
          <p className="p-4 text-center text-fusion-error text-sm">{error}</p>  
        )}  
        {!isLoading && !error && chats.length === 0 && (  
          <p className="p-4 text-center text-fusion-light text-sm italic">Nenhuma conversa encontrada.</p>  
        )}  
        {!isLoading && !error && chats.length > 0 && (  
          <ul className="space-y-1">  
            <AnimatePresence>  
              {chats.map(chat => (  
                <ChatListItem  
                  key={chat.id}  
                  chat={chat}  
                  isSelected={chat.id === selectedChatId}  
                  onSelect={handleSelect} // Use internal handler  
                />  
              ))}  
            </AnimatePresence>  
          </ul>  
        )}  
      </div>  
    </div>  
  );  
}

export default ChatList;

