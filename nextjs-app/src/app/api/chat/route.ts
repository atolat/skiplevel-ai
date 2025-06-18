import { supabase } from '@/lib/supabase'
import { cookies } from 'next/headers'

export async function POST(req: Request) {
  const { messages } = await req.json()
  
  console.log('API route called with message:', messages[messages.length - 1].content)
  
  // Get auth from cookies
  let userContext = null
  
  try {
    const cookieStore = await cookies()
    const accessToken = cookieStore.get('sb-access-token')?.value
    const refreshToken = cookieStore.get('sb-refresh-token')?.value
    
    console.log('Access token exists:', !!accessToken)
    console.log('Refresh token exists:', !!refreshToken)
    
    if (accessToken) {
      // Set the session for this request
      await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken || ''
      })
      
      // Get the user
      const { data: { user }, error } = await supabase.auth.getUser()
      
      console.log('User validation result:', !!user, 'Error:', !!error)
      
      if (user && !error) {
        // Get user profile with authenticated session
        const { data: profile, error: profileError } = await supabase
          .from('employee_profiles')
          .select('*')
          .eq('id', user.id)
          .single()
          
        console.log('Profile query result:', !!profile, 'Profile error:', !!profileError)
        if (profileError) {
          console.error('Profile error details:', profileError)
        }
        
        userContext = {
          user_id: user.id,
          email: user.email,
          profile: profile
        }
        
        console.log('Authenticated user:', user.email, 'Profile:', profile?.name)
        console.log('Profile completed?', profile?.profile_completed)
        console.log('Full profile data:', JSON.stringify(profile, null, 2))
      }
    }
  } catch (error) {
    console.error('Error getting auth from cookies:', error)
  }
  
  console.log('Final user context being sent:', userContext ? 'Present' : 'None')
  if (userContext?.profile) {
    console.log('Profile data keys:', Object.keys(userContext.profile))
  }
  
  // Call FastAPI backend
  const apiUrl = process.env.NODE_ENV === 'production'
    ? process.env.NEXT_PUBLIC_API_URL || 'https://your-service.railway.app'
    : 'http://localhost:8001'
    
  const response = await fetch(`${apiUrl}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: messages[messages.length - 1].content,
      user_id: userContext?.user_id || 'anonymous',
      agent_name: 'engineering_manager_emreq',
      user_context: userContext
    })
  })
  
  console.log('FastAPI response status:', response.status)
  
  if (!response.body) {
    console.error('No response body from FastAPI')
    return new Response('No response from agent', { status: 500 })
  }

  // Create a readable stream that converts FastAPI chunks to Data Stream Protocol
  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value)
          console.log('Processing chunk:', chunk)
          
          // Send the chunk as-is in Data Stream Protocol format
          // Don't re-split - FastAPI is already sending perfect word chunks
          if (chunk.trim()) {
            const dataStreamChunk = `0:${JSON.stringify(chunk)}\n`
            controller.enqueue(new TextEncoder().encode(dataStreamChunk))
            console.log('Sending data stream chunk:', dataStreamChunk.trim())
          }
        }
        
        // Send finish message part (required by protocol)
        const finishChunk = `d:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20}}\n`
        controller.enqueue(new TextEncoder().encode(finishChunk))
        console.log('Sending finish chunk:', finishChunk.trim())
        
      } catch (error) {
        console.error('Stream error:', error)
        controller.error(error)
      } finally {
        controller.close()
      }
    }
  })

  // Return with proper Data Stream Protocol headers
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'x-vercel-ai-data-stream': 'v1',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}

export async function GET() {
  return new Response('Chat API is running - Standard Vercel AI SDK streaming!', { status: 200 })
} 