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

// Direct Railway backend chat function
export const chatWithRailwayBackend = async (
  message: string,
  userContext: any
): Promise<string> => {
  try {
    console.log('Calling Railway backend directly:', getApiUrl('chat'))
    console.log('Message:', message)
    console.log('User context:', userContext)

    const response = await fetch(getApiUrl('chat'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        user_id: userContext?.user_id || 'anonymous',
        agent_name: 'engineering_manager_emreq',
        user_context: userContext
      }),
    })

    console.log('Railway backend response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Railway backend error:', errorText)
      throw new Error(`Railway backend returned ${response.status}: ${response.statusText}`)
    }

    const railwayResponse = await response.json()
    console.log('Railway response:', railwayResponse)
    
    return railwayResponse.response
  } catch (error) {
    console.error('Error calling Railway backend:', error)
    throw error
  }
} 