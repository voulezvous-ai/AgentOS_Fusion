import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { shallow } from 'zustand/shallow'
import { logger } from '@/utils/logger'
import apiClient from '@/lib/apiClient'

type ViewMode = 'whatsapp' | 'chatgpt'
type WebsocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

interface FusionState {
  activeView: ViewMode
  setActiveView: (view: ViewMode) => void
  flipView: () => void
}

export const useFusionStore = create<FusionState>()(
  devtools(
    persist(
      (set) => ({
        activeView: 'whatsapp',
        setActiveView: (view) => set({ activeView: view }),
        flipView: () =>
          set((state) => ({ activeView: state.activeView === 'whatsapp' ? 'chatgpt' : 'whatsapp' }))
      }),
      {
        name: 'fusion-app-store'
      }
    )
  )
)

export const useActiveView = () => useFusionStore((state) => state.activeView, shallow)