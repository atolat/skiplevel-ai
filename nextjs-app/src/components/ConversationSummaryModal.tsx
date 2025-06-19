'use client'

import { useEffect } from 'react'
import { X } from 'lucide-react'
import MarkdownRenderer from './MarkdownRenderer'

interface ConversationSummaryModalProps {
  isOpen: boolean
  onClose: () => void
  conversation: {
    id: string
    title: string
    summary: string
    status: 'active' | 'completed'
    created_at: string
    completed_at?: string
  }
}

export default function ConversationSummaryModal({
  isOpen,
  onClose,
  conversation
}: ConversationSummaryModalProps) {
  // Handle ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEsc)
      return () => document.removeEventListener('keydown', handleEsc)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.abs(now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' })
    } else {
      return date.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="text-green-400 font-mono text-sm">$</div>
            <h2 className="text-white font-mono text-lg">
              {conversation.title}
            </h2>
            <span className={`px-2 py-1 rounded text-xs font-mono ${
              conversation.status === 'active' 
                ? 'bg-green-900/30 text-green-400 border border-green-700' 
                : 'bg-gray-800/50 text-gray-400 border border-gray-600'
            }`}>
              {conversation.status}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1"
          >
            <X size={20} />
          </button>
        </div>

        {/* Metadata */}
        <div className="px-4 py-3 bg-gray-800/30 border-b border-gray-700">
          <div className="flex items-center space-x-6 text-sm font-mono text-gray-400">
            <div>
              <span className="text-blue-400">Created:</span> {formatDate(conversation.created_at)}
            </div>
            {conversation.completed_at && (
              <div>
                <span className="text-yellow-400">Completed:</span> {formatDate(conversation.completed_at)}
              </div>
            )}
            <div>
              <span className="text-purple-400">ID:</span> {conversation.id.slice(0, 8)}...
            </div>
          </div>
        </div>

        {/* Summary Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="mb-4">
            <h3 className="text-green-400 font-mono text-sm mb-2 flex items-center">
              <span className="text-green-400 mr-2">📋</span>
              CONVERSATION SUMMARY
            </h3>
          </div>
          
          <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-4">
            <MarkdownRenderer 
              content={conversation.summary} 
              className="text-sm"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-800/30 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <div className="text-xs font-mono text-gray-500">
              Press ESC to close
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-mono text-sm rounded border border-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
} 