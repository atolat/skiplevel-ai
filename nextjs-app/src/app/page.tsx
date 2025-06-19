'use client'

import { useState, useEffect } from 'react'
import { useDirectChat } from '@/lib/useDirectChat'
import { useAuth } from '@/contexts/AuthContext'
import AuthModal from '@/components/AuthModal'
import ProfileModal from '@/components/ProfileModal'
import UserAvatar from '@/components/UserAvatar'
import ToolIndicator from '@/components/ToolIndicator'
import ConversationHistory from '@/components/ConversationHistory'
import ConversationControls from '@/components/ConversationControls'
// import { supabase } from '@/lib/supabase' // Removed unused import

// Typing indicator component
function TypingIndicator() {
  return (
    <div className="pl-4">
      <div className="flex items-center space-x-1 text-blue-400 font-mono">
        <span>Emreq is thinking</span>
        <div className="flex space-x-1">
          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
      
      {/* Tool execution indicator */}
      <div className="mt-2 flex items-center space-x-2 text-xs text-gray-400 font-mono">
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Tools may be executing...</span>
        </div>
        <div className="flex space-x-1">
          <span className="animate-pulse">🔧</span>
          <span className="animate-pulse" style={{ animationDelay: '200ms' }}>🧮</span>
          <span className="animate-pulse" style={{ animationDelay: '400ms' }}>🔍</span>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const { user, profile, loading: authLoading, signOut } = useAuth()
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const [mounted, setMounted] = useState(false)
  
  const { messages, input, handleInputChange, handleSubmit, isLoading, conversationId, startNewConversation } = useDirectChat()

  // Prevent hydration issues by only rendering after mount
  useEffect(() => {
    setMounted(true)
  }, [])

  // Debug logging
  useEffect(() => {
    if (mounted) {
      console.log('Messages updated:', messages)
      console.log('Is loading:', isLoading)
      console.log('User:', user)
      console.log('Profile:', profile)
    }
  }, [messages, isLoading, user, profile, mounted])

  // Show profile setup for new users
  useEffect(() => {
    if (mounted && user && !profile?.profile_completed && !authLoading) {
      // Don't auto-open - let users access via avatar
      // setShowProfileModal(true)
    }
  }, [user, profile, authLoading, mounted])

  const handleAuthClick = () => {
    if (user) {
      signOut()
    } else {
      setShowAuthModal(true)
    }
  }

  const handleEditProfile = () => {
    setShowProfileModal(true)
  }

  const handleShowHistory = () => {
    setShowHistoryModal(true)
  }

  const handleConversationEnded = () => {
    // Start a new conversation when the current one ends
    startNewConversation()
    console.log('Conversation ended - started new conversation')
  }

  // Show loading state until component is mounted and auth is loaded
  if (!mounted || authLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-green-400 font-mono">Loading...</div>
      </div>
    )
  }

  return (
    <div className="h-full p-6">
      <div className="bg-gray-800 border border-gray-700 rounded-lg h-full max-w-4xl mx-auto flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <div className="text-sm font-mono font-medium text-gray-200">
            Emreq AI Engineering Manager
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <ConversationControls 
                onHistoryClick={handleShowHistory}
                onConversationEnded={handleConversationEnded}
                conversationId={conversationId}
              />
            )}
            {user ? (
              <UserAvatar onEditProfile={handleEditProfile} />
            ) : (
              <button
                onClick={handleAuthClick}
                className="text-sm font-mono text-blue-400 hover:text-blue-300 underline"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
        
        <div className="flex-1 p-6 overflow-auto scrollbar-thin">
          <div className="space-y-4">
            {/* Welcome commands */}
            <div className="space-y-2">
              <div className="text-green-400 font-mono">$ emreq --version</div>
              <div className="text-gray-400 font-mono">Emreq AI Engineering Manager v1.0.0</div>
            </div>
            
            <div className="space-y-2">
              <div className="text-green-400 font-mono">$ emreq --help</div>
              <div className="text-gray-400 font-mono">
                Available commands:
                <br />
                &nbsp;&nbsp;chat     - Start conversation with your AI manager
                <br />
                &nbsp;&nbsp;profile  - Manage your engineering profile
                <br />
                &nbsp;&nbsp;schedule - Schedule 1:1 meetings
                <br />
                &nbsp;&nbsp;research - Get industry insights
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-green-400 font-mono">$ emreq chat</div>
              <div className="text-gray-200 font-mono whitespace-pre-line">
                Initializing AI Engineering Manager...
                <br />
                {user && profile?.profile_completed ? (
                  <>
                    ✓ Profile loaded ({profile.name})
                    <br />
                    ✓ Memory initialized
                    <br />
                    ✓ Tools ready
                  </>
                ) : user ? (
                  <>
                    ⚠ Profile incomplete
                    <br />
                    ✓ Memory initialized
                    <br />
                    ✓ Tools ready
                  </>
                ) : (
                  <>
                    ⚠ Anonymous mode (limited features)
                    <br />
                    ✓ Basic chat ready
                    <br />
                    ℹ Sign in for personalized experience
                  </>
                )}
                <br />
                <br />
                Ready to chat! Type your message below...
              </div>
            </div>

            {/* Standard useChat message rendering */}
            {messages.map((message) => (
              <div key={message.id} className="space-y-2">
                {message.role === 'user' ? (
                  <div className="flex items-start space-x-2">
                    <span className="text-green-400 font-mono">&gt;</span>
                    <div className="text-gray-200 font-mono">{message.content}</div>
                  </div>
                ) : (
                  <div className="pl-4">
                    <div className="text-blue-400 font-mono whitespace-pre-line">
                      {message.content}
                    </div>
                    <ToolIndicator 
                      tools_used={message.tools_used} 
                      tool_execution_info={message.tool_execution_info} 
                    />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="space-y-2">
                <TypingIndicator />
              </div>
            )}
          </div>
        </div>

        {/* Standard useChat form */}
        <div className="border-t border-gray-700 p-4">
          <form onSubmit={handleSubmit} className="flex items-center space-x-2">
            <span className="text-green-400 font-mono">&gt;</span>
            <input 
              value={input}
              onChange={handleInputChange}
              placeholder="Type your message..."
              className="bg-transparent border-none outline-none text-gray-200 font-mono placeholder:text-gray-500 flex-1"
              disabled={isLoading}
            />
            <button 
              type="submit"
              disabled={isLoading}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 border border-green-600 disabled:border-gray-600 rounded-md px-3 py-2 font-mono text-sm transition-colors"
            >
              {isLoading ? 'Thinking...' : 'Send'}
            </button>
          </form>
        </div>
      </div>

      {/* Modals - only render when mounted */}
      {mounted && (
        <>
          <AuthModal 
            isOpen={showAuthModal} 
            onClose={() => setShowAuthModal(false)} 
          />
          <ProfileModal 
            isOpen={showProfileModal} 
            onClose={() => setShowProfileModal(false)} 
          />
          <ConversationHistory
            isOpen={showHistoryModal}
            onClose={() => setShowHistoryModal(false)}
          />
        </>
      )}
    </div>
  )
}

