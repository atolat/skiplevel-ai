import { NextRequest } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

// Railway backend URL
const RAILWAY_API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://web-development-c0b4.up.railway.app';

export async function POST(request: NextRequest) {
  try {
    // Get cookies
    const cookieStore = await cookies();
    const accessToken = cookieStore.get('sb-access-token')?.value;
    const refreshToken = cookieStore.get('sb-refresh-token')?.value;

    if (!accessToken || !refreshToken) {
      return new Response('Authentication required', { status: 401 });
    }

    // Set session in Supabase client
    const { data: { user }, error: authError } = await supabase.auth.setSession({
      access_token: accessToken,
      refresh_token: refreshToken
    });

    if (authError || !user) {
      return new Response('Invalid session', { status: 401 });
    }

    // Get user profile
    const { data: profile, error: profileError } = await supabase
      .from('employee_profiles')
      .select('*')
      .eq('id', user.id)
      .single();

    if (profileError) {
      console.error('Profile fetch error:', profileError);
      return new Response('Profile not found', { status: 404 });
    }

    // Get request body
    const body = await request.json();
    const { messages } = body;

    // Extract the latest message
    const latestMessage = messages[messages.length - 1]?.content || '';

    console.log('Calling Railway backend:', `${RAILWAY_API_URL}/api/chat`);
    console.log('Message:', latestMessage);
    console.log('User:', user.email);
    console.log('Profile:', profile.name);

    // Call the Railway backend
    const response = await fetch(`${RAILWAY_API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: latestMessage,
        user_id: user.id,
        agent_name: 'engineering_manager_emreq',
        user_context: {
          email: user.email,
          profile: {
            name: profile.name,
            title: profile.role,
            role: profile.role,
            experience_level: profile.experience_level,
            specialization: profile.specialization,
            years_of_experience: profile.years_of_experience,
            technical_skills: profile.technical_skills,
            current_challenges: profile.current_challenges,
            career_goals: profile.career_goals,
            communication_style: profile.communication_style,
            preferred_feedback_style: profile.preferred_feedback_style,
            profile_completed: true
          }
        }
      }),
    });

    console.log('Railway backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Railway backend error:', errorText);
      throw new Error(`Railway backend returned ${response.status}: ${response.statusText}`);
    }

    // Get the response from Railway backend
    const railwayResponse = await response.json();
    console.log('Railway response:', railwayResponse);

    // Convert the response to Data Stream Protocol format for useChat
    const stream = new ReadableStream({
      start(controller) {
        try {
          // Send the response as a single chunk
          const dataStreamChunk = `0:${JSON.stringify(railwayResponse.response)}\n`;
          controller.enqueue(new TextEncoder().encode(dataStreamChunk));
          
          // Send completion message
          const finishChunk = `d:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20}}\n`;
          controller.enqueue(new TextEncoder().encode(finishChunk));
          
          controller.close();
        } catch (error) {
          console.error('Stream error:', error);
          controller.error(error);
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'x-vercel-ai-data-stream': 'v1',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return new Response('Internal server error', { status: 500 });
  }
}

export async function GET() {
  return new Response('Chat API is running - Connected to Railway backend!', { status: 200 })
} 