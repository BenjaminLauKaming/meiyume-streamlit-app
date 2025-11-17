# Deployment Guide for Meiyume AI Assistant

## Option 1: Streamlit Cloud (Recommended - Easiest & Free)

Streamlit Cloud is the official hosting platform for Streamlit apps and is the easiest option.

### Prerequisites
1. GitHub account
2. Your code pushed to a GitHub repository

### Steps:

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/meiyume-ai-assistant.git
   git push -u origin main
   ```

2. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io/
   - Sign in with your GitHub account

3. **Deploy your app:**
   - Click "New app"
   - Select your repository
   - Set Main file path: `main.py`
   - Set Python version: 3.9 or 3.10
   - Add your secrets (environment variables):
     - `DATABASE_URL`: Your Supabase database URL
     - `DJANGO_API_URL`: Your Django backend URL (if using ngrok, update this)
     - Any other environment variables from your `.env` file

4. **Click "Deploy"**

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

---

## Option 2: Railway (Alternative - Also Free Tier)

Railway supports Python apps and is good for full-stack deployments.

### Steps:

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Create railway.json:**
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "streamlit run main.py --server.port $PORT --server.address 0.0.0.0",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

3. **Deploy:**
   ```bash
   railway login
   railway init
   railway up
   ```

4. **Set environment variables in Railway dashboard**

---

## Option 3: Render (Alternative - Free Tier Available)

### Steps:

1. **Create render.yaml:**
   ```yaml
   services:
     - type: web
       name: meiyume-ai-assistant
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run main.py --server.port $PORT --server.address 0.0.0.0
       envVars:
         - key: DATABASE_URL
           sync: false
         - key: DJANGO_API_URL
           sync: false
   ```

2. **Connect your GitHub repo to Render**
3. **Set environment variables in Render dashboard**

---

## Environment Variables Needed

Make sure to set these in your hosting platform:

- `DATABASE_URL`: Your Supabase PostgreSQL connection string
- `DJANGO_API_URL`: Your Django backend URL (e.g., `https://daf20c2517fd.ngrok-free.app`)
- Any other variables from your `.env` file

---

## Important Notes:

1. **Vercel is NOT recommended** for Streamlit apps because:
   - Vercel is designed for serverless functions and static sites
   - Streamlit needs a persistent Python server process
   - WebSocket support is limited

2. **For production**, consider:
   - Using a custom domain
   - Setting up proper authentication
   - Monitoring and logging
   - Database connection pooling

3. **If you must use Vercel**, you'd need to:
   - Convert your Streamlit app to a REST API
   - Build a separate frontend (React/Next.js)
   - This is a major refactor and not recommended

---

## Quick Start with Streamlit Cloud:

1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Connect repository
4. Set main file: `main.py`
5. Add secrets (environment variables)
6. Deploy!

Your app will be live in ~2 minutes! 🚀

