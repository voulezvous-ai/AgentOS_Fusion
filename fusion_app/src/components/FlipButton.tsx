import React from 'react'
import { useFusionStore } from '@/store/useFusionStore'

export const FlipButton = () => {
  const flipView = useFusionStore((state) => state.flipView)

  return (
    <button
      onClick={flipView}
      className="fixed bottom-4 right-4 p-3 bg-gray-800 rounded-full shadow-lg hover:bg-gray-700 text-white"
      title="Alternate views"
    >
      Flip View
    </button>
  )
}