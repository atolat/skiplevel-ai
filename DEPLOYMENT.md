# Emreq Deployment Guide

This guide covers the easiest ways to deploy your Emreq AI Engineering Manager system to production.

## 🚀 Quick Deployment Options (Ranked by Ease)

### 1. Railway (Recommended - Easiest) ⭐

**Why Railway?**
- Zero configuration deployment
- Automatic HTTPS
- Built-in environment variables management
- Free tier available
- Perfect for Python/Chainlit apps

**Steps:**
1. **Connect Repository**
   ```bash
   # Push your code to GitHub if not already there
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect it's a Python app

3. **Set Environment Variables**
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   ```

4. **Deploy** 
   - Railway automatically builds and deploys
   - Get your URL: `https://your-app-name.railway.app`

**Cost:** Free tier includes 500 hours/month, $5/month for unlimited

---

### 2. Render (Very Easy)

**Why Render?**
- Simple deployment process
- Free tier available
- Automatic SSL
- Good for Python apps

**Steps:**
1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Connect your GitHub account
   - Select your repository

2. **Configure Service**
   ```yaml
   # Service Type: Web Service
   # Build Command: pip install -r requirements.txt
   # Start Command: python -m chainlit run app.py --host 0.0.0.0 --port $PORT
   ```

3. **Set Environment Variables** (same as Railway)

4. **Deploy** - Render handles the rest

**Cost:** Free tier available, paid plans start at $7/month

---

### 3. Heroku (Easy)

**Steps:**
1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Login
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-emreq-app
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set SUPABASE_URL=your_url
   heroku config:set SUPABASE_ANON_KEY=your_key
   heroku config:set SUPABASE_SERVICE_ROLE_KEY=your_key
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

**Cost:** $7/month minimum (no free tier as of 2022)

---

### 4. Vercel (Easy - Serverless)

**Why Vercel?**
- Serverless deployment
- Automatic scaling
- Great for Next.js/Python
- Free tier

**Steps:**
1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Create vercel.json**
   ```json
   {
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

**Note:** May require modifications for Chainlit WebSocket support

---

## 🔧 Pre-Deployment Checklist

### Required Environment Variables
```bash
# Essential - Your app won't work without these
OPENAI_API_KEY=sk-...                    # OpenAI API key
SUPABASE_URL=https://...supabase.co      # Your Supabase project URL
SUPABASE_ANON_KEY=eyJ...                 # Supabase anonymous key
SUPABASE_SERVICE_ROLE_KEY=eyJ...         # Supabase service role key

# Optional - For enhanced features
SMTP_USERNAME=your-email@gmail.com       # For calendar invites
SMTP_PASSWORD=your-app-password          # Gmail app password
SENDER_NAME=Emreq                        # Email sender name
```

### Files Created for Deployment
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Process definition for Heroku-style platforms
- ✅ `railway.json` - Railway-specific configuration
- ✅ `DEPLOYMENT.md` - This guide

### Testing Before Deployment
```bash
# Test locally first
python -m chainlit run app.py --host 0.0.0.0 --port 8000

# Verify these work:
# 1. Chat interface loads
# 2. Personalized welcome (if profile exists)
# 3. Tool usage (calculator, web search)
# 4. Memory system (remembers conversation)
```

---

## 🎯 Recommended Deployment: Railway

**For your use case, Railway is the best choice because:**

1. **Zero Configuration** - Works out of the box with your current setup
2. **Environment Variables** - Easy management through web interface
3. **Automatic HTTPS** - Secure by default
4. **WebSocket Support** - Perfect for Chainlit's real-time features
5. **Cost Effective** - Free tier covers development, low cost for production

### Quick Railway Deployment

```bash
# 1. Ensure your code is in GitHub
git add .
git commit -m "Ready for Railway deployment"
git push origin main

# 2. Go to railway.app and click "Deploy from GitHub repo"
# 3. Select your repository
# 4. Add environment variables in Railway dashboard
# 5. Deploy automatically happens!
```

Your app will be live at: `https://your-app-name.railway.app`

---

## 🔍 Monitoring and Maintenance

### Health Checks
Your app includes basic health monitoring:
- Chainlit provides built-in health endpoints
- Monitor logs through your platform's dashboard
- Set up alerts for downtime

### Scaling Considerations
- **Railway/Render**: Automatic scaling based on traffic
- **Heroku**: Manual dyno scaling required
- **Vercel**: Serverless auto-scaling

### Database Management
- Your Supabase database is already cloud-hosted
- No additional database deployment needed
- Monitor usage through Supabase dashboard

---

## 🚨 Troubleshooting Common Issues

### "Module not found" errors
```bash
# Ensure requirements.txt includes all dependencies
pip freeze > requirements.txt
```

### Environment variables not loading
```bash
# Check platform-specific environment variable syntax
# Most platforms use the same format as shown above
```

### WebSocket connection issues
```bash
# Ensure your platform supports WebSocket connections
# Railway, Render, and Heroku all support WebSockets
```

### Supabase connection errors
```bash
# Verify all Supabase environment variables are set correctly
# Check that SUPABASE_SERVICE_ROLE_KEY is set (not just ANON_KEY)
```

---

## 💡 Next Steps After Deployment

1. **Custom Domain** - Add your own domain through your platform
2. **Monitoring** - Set up uptime monitoring (UptimeRobot is free)
3. **Analytics** - Monitor usage patterns and performance
4. **Backups** - Your Supabase data is automatically backed up
5. **SSL Certificate** - Automatically provided by all recommended platforms

---

**Ready to deploy?** Start with Railway for the easiest experience! 🚀 