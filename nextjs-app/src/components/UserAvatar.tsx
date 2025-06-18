'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface UserAvatarProps {
  onEditProfile: () => void
}

export default function UserAvatar({ onEditProfile }: UserAvatarProps) {
  const { user, profile, signOut } = useAuth()
  const [showDropdown, setShowDropdown] = useState(false)

  if (!user) return null

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const handleSignOut = async () => {
    await signOut()
    setShowDropdown(false)
  }

  const displayName = profile?.name || user.email?.split('@')[0] || 'User'
  const initials = profile?.name ? getInitials(profile.name) : displayName.slice(0, 2).toUpperCase()

  return (
    <div className="relative">
      {/* Avatar Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg px-3 py-2 transition-colors"
      >
        {/* Avatar Circle */}
        <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white font-mono text-sm font-bold">
          {initials}
        </div>
        
        {/* User Info */}
        <div className="text-left hidden sm:block">
          <div className="text-sm font-mono text-gray-200 truncate max-w-32">
            {displayName}
          </div>
          <div className="text-xs font-mono text-gray-400 truncate max-w-32">
            {profile?.title || 'Engineer'}
          </div>
        </div>
        
        {/* Dropdown Arrow */}
        <div className="text-gray-400">
          <svg className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Dropdown Menu */}
      {showDropdown && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setShowDropdown(false)}
          />
          
          {/* Menu */}
          <div className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-20">
            {/* User Info Header */}
            <div className="px-4 py-3 border-b border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white font-mono text-lg font-bold">
                  {initials}
                </div>
                <div>
                  <div className="text-sm font-mono text-gray-200 font-medium">
                    {displayName}
                  </div>
                  <div className="text-xs font-mono text-gray-400">
                    {user.email}
                  </div>
                  {profile?.title && (
                    <div className="text-xs font-mono text-blue-400">
                      {profile.title}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Profile Status */}
            {profile && (
              <div className="px-4 py-2 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-gray-400">Profile Status</span>
                  <span className={`text-xs font-mono px-2 py-1 rounded ${
                    profile.profile_completed 
                      ? 'bg-green-900 text-green-400 border border-green-800' 
                      : 'bg-yellow-900 text-yellow-400 border border-yellow-800'
                  }`}>
                    {profile.profile_completed ? 'Complete' : 'Incomplete'}
                  </span>
                </div>
              </div>
            )}

            {/* Menu Items */}
            <div className="py-2">
              <button
                onClick={() => {
                  onEditProfile()
                  setShowDropdown(false)
                }}
                className="w-full px-4 py-2 text-left text-sm font-mono text-gray-200 hover:bg-gray-700 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>Edit Profile</span>
              </button>
              
              <div className="border-t border-gray-700 my-2"></div>
              
              <button
                onClick={handleSignOut}
                className="w-full px-4 py-2 text-left text-sm font-mono text-red-400 hover:bg-gray-700 flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
} 