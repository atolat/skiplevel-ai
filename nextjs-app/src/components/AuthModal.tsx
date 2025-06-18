'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { signIn, signUp } = useAuth()

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const { error } = isLogin 
        ? await signIn(email, password)
        : await signUp(email, password)

      if (error) {
        setError(error.message)
      } else {
        if (!isLogin) {
          setError('Check your email for the confirmation link!')
        } else {
          onClose()
        }
      }
    } catch {
      setError('An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setError('')
    setEmail('')
    setPassword('')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 border border-gray-700 rounded-lg max-w-md w-full">
        {/* Terminal-style header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <div className="text-sm font-mono font-medium text-gray-200">
            emreq auth
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-lg"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {/* Terminal-style command */}
          <div className="mb-6">
            <div className="text-green-400 font-mono text-sm mb-2">
              $ emreq auth {isLogin ? 'login' : 'signup'}
            </div>
            <div className="text-gray-400 font-mono text-sm">
              {isLogin 
                ? 'Sign in to access personalized AI management'
                : 'Create account for personalized AI management'
              }
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-mono text-gray-300 mb-2">
                Email:
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                placeholder="your.email@company.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-mono text-gray-300 mb-2">
                Password:
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-gray-200 font-mono focus:outline-none focus:border-green-500"
                placeholder="••••••••"
                minLength={6}
                required
              />
            </div>

            {error && (
              <div className="text-red-400 font-mono text-sm bg-red-900/20 border border-red-800 rounded px-3 py-2">
                Error: {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 border border-green-600 disabled:border-gray-600 rounded px-4 py-2 font-mono text-sm transition-colors"
            >
              {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          {/* Toggle between login/signup */}
          <div className="mt-6 pt-4 border-t border-gray-700 text-center">
            <button
              onClick={toggleMode}
              className="text-blue-400 hover:text-blue-300 font-mono text-sm underline"
            >
              {isLogin 
                ? 'Need an account? Sign up' 
                : 'Already have an account? Sign in'
              }
            </button>
          </div>

          {/* Continue without auth */}
          <div className="mt-4 text-center">
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-400 font-mono text-xs underline"
            >
              Continue without signing in
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}