// src/routes/CommsPage.jsx  
import React, { useState, useCallback } from 'react';  
import ChatList from '../components/ChatList';  
import MessageView from '../components/MessageView';  
import InputBar from '../components/InputBar';  
import apiClient from '../services/api'; // To send messages  
import { useAuth } from '../hooks/useAuth'; // To get user info if needed  
import { useWebSocket } from '../hooks/useWebSocket'; // To monitor connection

const logger = { info: console.log, error: console.error, warn: console.warn, debug: console.debug };

function CommsPage() {  
  const [selectedChatId, setSelectedChatId] = useState(null); // User's WA ID is the Chat ID  
  const [draft, setDraft] = useState('');  
  const [isSending, setIsSending] = useState(false);  
  const [sendError, setSendError] = useState(null);  
  const { user } = useAuth(); // Needed for audit/logging, maybe sender info?  
  const { isConnected: isWsConnected } = useWebSocket(); // Get WS connection status

  const handleSelectChat = useCallback((chatId) => {  
    logger.info(`Chat selected: ${chatId}`);  
    setSelectedChatId(chatId);  
    setDraft(''); // Clear draft when changing chat  
    setSendError(null); // Clear previous send errors  
  }, []);

  const handleSendMessage = useCallback(async () => {  
    if (!selectedChatId || !draft.trim() || isSending) {  
      logger.warn("Send message condition not met.", { selectedChatId, draft, isSending });  
      return;  
    }

    logger.info(`Sending message to chat: ${selectedChatId}`);  
    setIsSending(true);  
    setSendError(null);

    const payload = {  
        recipient_wa_id: selectedChatId,  
        content: draft,  
    };

    try {  
      // Call the backend API to send/queue the message  
      const response = await apiClient.post('/whatsapp/send', payload);  
      logger.debug("Send message API response:", response.data);

      if (response.data?.status === 'queued') {  
          logger.info(`Message ${response.data.internal_message_id} queued successfully.`);  
          setDraft(''); // Clear input on successful queueing  
          // The message will appear in MessageView via WebSocket update or next fetch  
      } else {  
          throw new Error(response.data?.details || 'Falha ao enfileirar mensagem.');  
      }  
    } catch (error) {  
      logger.error("Error sending message via API:", error);  
      setSendError(error.message || "Erro ao enviar mensagem.");  
      // Keep draft in input bar on error for retry?  
    } finally {  
      setIsSending(false);  
    }  
  }, [selectedChatId, draft, isSending]);

  return (  
    // Main layout for the Comms Page  
    <div className="flex h-full w-full bg-fusion-deep"> {/* Ensure full height */}

      {/* Chat List Panel */}  
      <ChatList  
        selectedChatId={selectedChatId}  
        onSelectChat={handleSelectChat}  
      />

      {/* Main Chat Area (Message View + Input) */}  
      <div className="flex flex-col flex-1 h-full overflow-hidden"> {/* Prevent chat area from overflowing */}

        {/* Message View Area (Scrollable) */}  
        <MessageView chatId={selectedChatId} />

        {/* Input Bar Area */}  
        <div className="flex-shrink-0 border-t border-fusion-medium">  
          {selectedChatId ? (  
            <>  
             {/* Display Send Error */}  
             {sendError && (  
                 <div className="px-4 py-1 bg-red-800/50 text-center text-xs text-red-200">  
                     Erro ao enviar: {sendError}  
                 </div>  
             )}  
             <InputBar  
                draft={draft}  
                setDraft={setDraft}  
                sendAction={handleSendMessage}  
                placeholder="Digite sua mensagem..."  
                disabled={isSending || !isWsConnected} // Disable if sending or WS offline  
              />  
             </>  
          ) : (  
              <div className="p-4 text-center text-sm text-fusion-light h-[76px] flex items-center justify-center bg-fusion-dark"> {/* Match InputBar height approx */}  
                 Selecione uma conversa para começar a conversar.  
              </div>  
          )}  
        </div>  
      </div>  
    </div>  
  );  
}

export default CommsPage;  
