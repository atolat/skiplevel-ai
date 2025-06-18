# Railway Deployment Guide

This guide will help you deploy the Emreq AI Engineering Manager to Railway.

## Architecture

The deployment includes:
- **FastAPI Backend**: Serves the AI agent API with streaming responses
- **Authentication**: Supabase integration for user management
- **Profile System**: Complete user profile management with personalization
- **AI Agent**: Emreq engineering manager with memory and tools

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Supabase Project**: Your Supabase database with employee_profiles table
3. **OpenAI API Key**: For the AI agent (GPT-4)

## Deployment Steps

### 1. Connect to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (from your repo root)
railway init
```

### 2. Set Environment Variables

In your Railway dashboard, add these environment variables:

#### Required Variables:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Frontend URL (for CORS - set after frontend deployment)
FRONTEND_URL=https://your-nextjs-app.vercel.app
```

#### Optional Variables:
```bash
# For additional API providers (if using)
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
```

### 3. Deploy Backend

```bash
# Deploy the FastAPI backend
railway up
```

The backend will be available at: `https://your-service.railway.app`

### 4. Deploy Frontend (Vercel Recommended)

For the Next.js frontend, we recommend deploying to Vercel:

```bash
cd nextjs-app

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
# SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

### 5. Update CORS Settings

After deploying the frontend, update the `FRONTEND_URL` environment variable in Railway with your Vercel URL.

## API Endpoints

Once deployed, your Railway backend will provide:

- `GET /health` - Health check
- `POST /api/chat` - Non-streaming chat
- `POST /api/chat/stream` - Streaming chat (recommended)
- `GET /agents` - List available agents

## Frontend Integration

Update your Next.js app's API calls to use the Railway backend:

```typescript
// In your API routes or client code
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-service.railway.app'
  : 'http://localhost:8001'
```

## Testing the Deployment

1. **Health Check**: Visit `https://your-service.railway.app/health`
2. **Frontend**: Test the complete flow with authentication and profile
3. **Personalization**: Verify that Emreq uses your profile data

## Monitoring

Railway provides built-in monitoring:
- **Logs**: View real-time application logs
- **Metrics**: Monitor CPU, memory, and network usage
- **Deployments**: Track deployment history

## Troubleshooting

### Common Issues:

1. **CORS Errors**: Ensure `FRONTEND_URL` is set correctly
2. **Supabase Connection**: Verify all Supabase environment variables
3. **OpenAI Errors**: Check API key and quota
4. **Profile Loading**: Ensure RLS policies allow profile access

### Debug Commands:

```bash
# View logs
railway logs

# Connect to shell
railway shell

# Check environment variables
railway variables
```

## Production Considerations

1. **Security**: All API keys are properly configured as environment variables
2. **CORS**: Restricted to your frontend domain
3. **Health Checks**: Enabled for Railway monitoring
4. **Auto-scaling**: Railway handles scaling automatically
5. **SSL**: HTTPS enabled by default

## Cost Optimization

- Railway charges based on usage
- The FastAPI backend is lightweight and efficient
- Consider using Railway's sleep mode for development environments

## Next Steps

After deployment:
1. Test all functionality with real users
2. Monitor performance and logs
3. Set up custom domain if needed
4. Configure backup strategies for your Supabase data

Your Emreq AI Engineering Manager is now live and ready to help teams worldwide! 🚀 