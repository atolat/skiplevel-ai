// API configuration for different environments

export const API_CONFIG = {
  // Use Railway backend URL for both development and production
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://web-development-c0b4.up.railway.app',
    
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