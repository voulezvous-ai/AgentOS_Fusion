import React from 'react'
import { useActiveView } from '@/store/useFusionStore'
import { WhatsAppView } from './WhatsAppView'
import { ChatGPTView } from './ChatGPTView'
import { FlipButton } from './FlipButton'

export const FusionShell = () => {
  const activeView = useActiveView()

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      {activeView === 'whatsapp' ? <WhatsAppView /> : <ChatGPTView />}
      <FlipButton />
    </div>
  )
}