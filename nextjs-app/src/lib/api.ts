// API configuration for different environments

export const API_CONFIG = {
  // Use Railway backend URL in production, localhost in development
  baseURL: process.env.NODE_ENV === 'production' 
    ? process.env.NEXT_PUBLIC_API_URL || 'https://your-service.railway.app'
    : 'http://localhost:8001',
    
  endpoints: {
    health: '/health',
    chat: '/api/chat',
    chatStream: '/api/chat/stream',
    agents: '/agents'
  }
}

export const getApiUrl = (endpoint: keyof typeof API_CONFIG.endpoints): string => {
  return `${API_CONFIG.baseURL}${API_CONFIG.endpoints[endpoint]}`
}

// Helper function to check if API is available
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl('health'))
    return response.ok
  } catch (error) {
    console.error('API health check failed:', error)
    return false
  }
} 