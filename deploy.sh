#!/bin/bash

# Emreq AI Engineering Manager - Railway Deployment Script

echo "🚀 Emreq AI Engineering Manager - Railway Deployment"
echo "=================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

# Check for required environment variables in .env
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one with your environment variables."
    echo "📋 Required variables:"
    echo "   - OPENAI_API_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - SUPABASE_SERVICE_ROLE_KEY"
    exit 1
fi

echo "✅ Environment file found"

# Initialize Railway project if not already done
if [ ! -f railway.json ]; then
    echo "🚂 Initializing Railway project..."
    railway init
fi

echo "📤 Deploying to Railway..."

# Deploy the project
railway up

echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Check your Railway dashboard for the deployment URL"
echo "2. Set the FRONTEND_URL environment variable in Railway dashboard"
echo "3. Deploy your Next.js frontend to Vercel"
echo "4. Update NEXT_PUBLIC_API_URL in your frontend deployment"
echo ""
echo "🔗 Your backend will be available at: https://your-service.railway.app"
echo "🏥 Health check: https://your-service.railway.app/health"
echo ""
echo "Happy deploying! 🚀" 