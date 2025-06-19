'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface ConversationControlsProps {
  onHistoryClick: () => void
  onConversationEnded?: () => void
  conversationId?: string | null
}

export default function ConversationControls({ onHistoryClick, onConversationEnded, conversationId }: ConversationControlsProps) {
  const { user } = useAuth()
  const [isEnding, setIsEnding] = useState(false)
  const [showEndDialog, setShowEndDialog] = useState(false)

  const handleEndConversation = async () => {
    if (!user) return

    setIsEnding(true)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      const url = conversationId 
        ? `${apiUrl}/api/conversations/complete?user_id=${user.id}&conversation_id=${conversationId}`
        : `${apiUrl}/api/conversations/complete?user_id=${user.id}`
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (response.ok) {
        console.log('Conversation ended successfully')
        onConversationEnded?.()
        setShowEndDialog(false)
      } else {
        console.error('Failed to end conversation')
      }
    } catch (error) {
      console.error('Error ending conversation:', error)
    } finally {
      setIsEnding(false)
    }
  }

  if (!user) return null

  return (
    <>
      {/* Control buttons */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onHistoryClick}
          className="flex items-center space-x-1 bg-gray-700 hover:bg-gray-600 text-gray-300 hover:text-white border border-gray-600 rounded-md px-2 py-1 font-mono text-xs transition-colors"
          title="View conversation history"
        >
          <span>📋</span>
          <span>History</span>
        </button>
        
        <button
          onClick={() => setShowEndDialog(true)}
          className="flex items-center space-x-1 bg-gray-700 hover:bg-red-700 text-gray-300 hover:text-white border border-gray-600 hover:border-red-600 rounded-md px-2 py-1 font-mono text-xs transition-colors"
          title="End current conversation"
        >
          <span>🏁</span>
          <span>End</span>
        </button>
      </div>

      {/* End conversation confirmation dialog */}
      {showEndDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 border border-gray-700 rounded-lg w-full max-w-md">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
              <div className="flex space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="text-sm font-mono font-medium text-gray-200">
                End Conversation
              </div>
              <button
                onClick={() => setShowEndDialog(false)}
                className="text-gray-400 hover:text-gray-200 text-xl font-mono"
                disabled={isEnding}
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="space-y-4">
                <div className="text-green-400 font-mono">$ emreq conversation --end</div>
                <div className="text-gray-300 font-mono text-sm">
                  Are you sure you want to end this conversation?
                </div>
                <div className="text-gray-400 font-mono text-sm bg-gray-900 p-3 rounded border border-gray-700">
                  ⚠️ This will:
                  <br />
                  • Save the conversation to your history
                  <br />
                  • Generate a summary of the discussion
                  <br />
                  • Clear the current chat session
                  <br />
                  • Start fresh for your next conversation
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-700 p-4 flex justify-end space-x-3">
              <button
                onClick={() => setShowEndDialog(false)}
                disabled={isEnding}
                className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 text-gray-200 border border-gray-600 rounded-md px-4 py-2 font-mono text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEndConversation}
                disabled={isEnding}
                className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white border border-red-600 rounded-md px-4 py-2 font-mono text-sm transition-colors flex items-center space-x-2"
              >
                {isEnding ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>Ending...</span>
                  </>
                ) : (
                  <>
                    <span>🏁</span>
                    <span>End Conversation</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
} 