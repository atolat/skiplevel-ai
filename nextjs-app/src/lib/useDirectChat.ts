import { useState, useCallback } from 'react'
import { chatWithRailwayBackend, UserContext } from './api'
import { useAuth } from '@/contexts/AuthContext'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt?: Date
  tools_used?: string[]
  tool_execution_info?: Array<{
    name: string
    args: Record<string, unknown>
    id: string
  }>
}

export interface UseDirectChatReturn {
  messages: Message[]
  input: string
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void
  isLoading: boolean
  error: string | null
  conversationId: string | null
  startNewConversation: () => void
}

export function useDirectChat(): UseDirectChatReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const { user, profile } = useAuth()

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }, [])

  const handleSubmit = useCallback(async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      createdAt: new Date()
    }

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      // Prepare user context
      const userContext: UserContext = {
        user_id: user?.id || 'anonymous',
        email: user?.email || 'anonymous@example.com',
        profile: profile ? {
          name: profile.name,
          title: profile.title,
          role: profile.title,
          experience_level: profile.level,
          specialization: profile.specialization,
          years_of_experience: profile.years_experience,
          technical_skills: profile.tech_skills,
          current_challenges: profile.biggest_challenges,
          career_goals: profile.career_goals,
          communication_style: profile.communication_style,
          preferred_feedback_style: profile.feedback_frequency,
          profile_completed: profile.profile_completed || false
        } : null
      }

      // Call Railway backend directly with conversation ID
      const apiResponse = await chatWithRailwayBackend(userMessage.content, userContext, conversationId || undefined)
      
      // If this is the first message, we might get a new conversation ID back
      if (!conversationId && apiResponse.conversation_id) {
        setConversationId(apiResponse.conversation_id)
      }

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: apiResponse.response,
        createdAt: new Date(),
        tools_used: apiResponse.tools_used,
        tool_execution_info: apiResponse.tool_execution_info
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        createdAt: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, user, profile, conversationId])

  const startNewConversation = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setError(null)
  }, [])

  return {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    conversationId,
    startNewConversation
  }
} 