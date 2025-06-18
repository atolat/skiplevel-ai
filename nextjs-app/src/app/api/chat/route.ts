import { NextRequest } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { cookies } from 'next/headers';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

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
      .eq('user_id', user.id)
      .single();

    if (profileError) {
      console.error('Profile fetch error:', profileError);
      return new Response('Profile not found', { status: 404 });
    }

    // Get request body
    const body = await request.json();
    const { messages } = body;

    // Construct the URL for the Python function
    const protocol = request.headers.get('x-forwarded-proto') || 'https';
    const host = request.headers.get('host');
    const pythonFunctionUrl = `${protocol}://${host}/api/emreq`;

    // Prepare headers for the Python function call
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Debug: Check if bypass secret is available
    const bypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;
    console.log('Bypass secret available:', !!bypassSecret);
    console.log('Bypass secret length:', bypassSecret?.length || 0);
    
    // Add bypass header with the generated secret
    if (bypassSecret) {
      headers['x-vercel-protection-bypass'] = bypassSecret;
      console.log('Added bypass header');
    } else {
      console.log('No bypass secret found in environment');
    }

    console.log('Request headers:', Object.keys(headers));
    console.log('Calling URL:', pythonFunctionUrl);

    // Call the Python function
    const response = await fetch(pythonFunctionUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        messages,
        user_context: {
          name: profile.name,
          role: profile.role,
          experience_level: profile.experience_level,
          specialization: profile.specialization,
          years_of_experience: profile.years_of_experience,
          technical_skills: profile.technical_skills,
          current_challenges: profile.current_challenges,
          career_goals: profile.career_goals,
          communication_style: profile.communication_style,
          preferred_feedback_style: profile.preferred_feedback_style,
        }
      }),
    });

    console.log('Python function response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python function error:', errorText);
      throw new Error(`Python function returned ${response.status}: ${response.statusText}`);
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
      },
    });

  } catch (error) {
    console.error('Chat API error:', error);
    return new Response('Internal server error', { status: 500 });
  }
}

export async function GET() {
  return new Response('Chat API is running - Standard Vercel AI SDK streaming!', { status: 200 })
} 