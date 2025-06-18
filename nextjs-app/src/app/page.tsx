'use client'

import { useChat } from 'ai/react'
import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import AuthModal from '@/components/AuthModal'
import ProfileModal from '@/components/ProfileModal'
import UserAvatar from '@/components/UserAvatar'
// import { supabase } from '@/lib/supabase' // Removed unused import

// Typing indicator component
function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1 text-blue-400 font-mono pl-4">
      <span>Emreq is thinking</span>
      <div className="flex space-x-1">
        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  )
}

export default function Home() {
  const { user, profile, loading: authLoading, signOut } = useAuth()
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat'
  })

  // Debug logging
  useEffect(() => {
    console.log('Messages updated:', messages)
    console.log('Is loading:', isLoading)
    console.log('User:', user)
    console.log('Profile:', profile)
  }, [messages, isLoading, user, profile])

  // Show profile setup for new users
  useEffect(() => {
    if (user && !profile?.profile_completed && !authLoading) {
      // Don't auto-open - let users access via avatar
      // setShowProfileModal(true)
    }
  }, [user, profile, authLoading])

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

  if (authLoading) {
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
          <div className="flex items-center space-x-2">
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
                  <div className="text-blue-400 font-mono whitespace-pre-line pl-4">
                    {message.content}
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

      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />

      {/* Profile Modal */}
      <ProfileModal 
        isOpen={showProfileModal} 
        onClose={() => setShowProfileModal(false)}
        isNewProfile={!profile?.profile_completed}
      />
    </div>
  )
}

