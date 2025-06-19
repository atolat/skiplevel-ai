'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import ConversationSummaryModal from './ConversationSummaryModal'

interface ConversationSession {
  id: string
  title: string
  summary: string
  created_at: string
  completed_at?: string
  status: 'active' | 'completed'
}

interface ConversationHistoryProps {
  isOpen: boolean
  onClose: () => void
  onConversationSelect?: (conversationId: string) => void
}

export default function ConversationHistory({ isOpen, onClose, onConversationSelect }: ConversationHistoryProps) {
  const { user } = useAuth()
  const [sessions, setSessions] = useState<ConversationSession[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedConversation, setSelectedConversation] = useState<ConversationSession | null>(null)
  const [summaryModalOpen, setSummaryModalOpen] = useState(false)

  const fetchConversationHistory = useCallback(async () => {
    if (!user) return

    setLoading(true)
    setError(null)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'
      const response = await fetch(`${apiUrl}/api/conversations/history?user_id=${user.id}&limit=10`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch conversation history')
      }

      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (err) {
      console.error('Error fetching conversation history:', err)
      setError(err instanceof Error ? err.message : 'Failed to load conversation history')
    } finally {
      setLoading(false)
    }
  }, [user])

  const handleConversationClick = (session: ConversationSession) => {
    if (session.status === 'active' && onConversationSelect) {
      // For active conversations, allow resuming
      onConversationSelect(session.id)
      onClose()
    } else {
      // For completed conversations, show rich summary modal
      setSelectedConversation(session)
      setSummaryModalOpen(true)
    }
  }

  useEffect(() => {
    if (isOpen && user) {
      fetchConversationHistory()
    }
  }, [isOpen, user, fetchConversationHistory])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 24) {
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      })
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString('en-US', { 
        weekday: 'short',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 border border-gray-700 rounded-lg w-full max-w-4xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <div className="text-sm font-mono font-medium text-gray-200">
            Conversation History
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-xl font-mono"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="space-y-4">
            {/* Terminal-style header */}
            <div className="space-y-2">
              <div className="text-green-400 font-mono">$ emreq history --list</div>
              <div className="text-gray-400 font-mono">
                Loading conversation history for {user?.email}...
              </div>
            </div>

            {loading && (
              <div className="flex items-center space-x-2 text-blue-400 font-mono">
                <div className="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                <span>Fetching conversations...</span>
              </div>
            )}

            {error && (
              <div className="text-red-400 font-mono">
                ❌ Error: {error}
              </div>
            )}

            {!loading && !error && sessions.length === 0 && (
              <div className="text-gray-400 font-mono">
                📝 No conversation history found
                <br />
                Start chatting with Emreq to build your conversation history!
              </div>
            )}

            {!loading && sessions.length > 0 && (
              <div className="space-y-4">
                <div className="text-gray-300 font-mono">
                  Found {sessions.length} conversation{sessions.length !== 1 ? 's' : ''}:
                </div>
                
                {sessions.map((session, index) => (
                  <div 
                    key={session.id} 
                    className="border border-gray-600 rounded-lg p-4 bg-gray-900 hover:bg-gray-800 cursor-pointer transition-colors"
                    onClick={() => handleConversationClick(session)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-green-400 font-mono">#{index + 1}</span>
                        <span className="text-gray-300 font-mono text-sm hover:text-white">
                          {session.title}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs font-mono ${
                          session.status === 'active' 
                            ? 'bg-green-900 text-green-300 border border-green-700' 
                            : 'bg-gray-700 text-gray-300 border border-gray-600'
                        }`}>
                          {session.status}
                        </span>
                      </div>
                      <div className="text-gray-400 font-mono text-sm">
                        {formatDate(session.created_at)}
                      </div>
                    </div>
                    
                    {session.summary && (
                      <div className="text-gray-300 font-mono text-sm bg-gray-800 p-3 rounded border border-gray-700">
                        <div className="text-blue-400 mb-1">Summary:</div>
                        <div className="whitespace-pre-wrap">{session.summary}</div>
                      </div>
                    )}
                    
                    {session.completed_at && (
                      <div className="text-gray-500 font-mono text-xs mt-2">
                        Completed: {formatDate(session.completed_at)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 p-4">
          <div className="flex justify-between items-center">
            <div className="text-gray-400 font-mono text-sm">
              💡 Tip: Use &quot;End Conversation&quot; to save your current chat to history
            </div>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 text-gray-200 border border-gray-600 rounded-md px-4 py-2 font-mono text-sm transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Rich Summary Modal */}
      {selectedConversation && (
        <ConversationSummaryModal
          isOpen={summaryModalOpen}
          onClose={() => {
            setSummaryModalOpen(false)
            setSelectedConversation(null)
          }}
          conversation={selectedConversation}
        />
      )}
    </div>
  )
} 