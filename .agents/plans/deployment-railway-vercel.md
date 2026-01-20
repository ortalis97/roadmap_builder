# Deployment Plan: Railway + Vercel

> **Status**: Plan ready for implementation
> **Delete after**: Deployment complete and verified

## Overview

Deploy the Learning Roadmap App using:
- **Frontend**: Vercel (free tier)
- **Backend**: Railway (free $5 credit/month)
- **Database**: MongoDB Atlas (already configured, M0 free tier)
- **Auth**: Firebase (already configured, free tier)

---

## Prerequisites

Before starting deployment:

- [ ] GitHub repository with latest code pushed
- [ ] MongoDB Atlas cluster running (M0 free tier)
- [ ] Firebase project configured with Google OAuth
- [ ] Gemini API key available
- [ ] Accounts created: [Railway](https://railway.app), [Vercel](https://vercel.com)

---

## Phase 1: Pre-Deployment Preparation

### 1.1 Commit or Stash Current Work

```bash
# Check current status
git status

# Either commit the markdown rendering work
git add -A && git commit -m "feat: Add markdown rendering for session content"

# Or stash it for later
git stash save "markdown rendering WIP"
```

### 1.2 Review Environment Variables

Ensure no hardcoded values. Check these files:
- `server/app/config.py` - Uses Pydantic BaseSettings (good)
- `client/src/services/api.ts` - Uses `import.meta.env.VITE_API_URL` (good)

### 1.3 Create Backend Deployment Files

**Option A: Procfile (simpler)**

Create `server/Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Option B: railway.json (more control)**

Create `server/railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 1.4 Verify Python Version

Create/update `server/runtime.txt`:
```
python-3.11.7
```

Or add to `server/pyproject.toml`:
```toml
[tool.poetry]
python = "^3.11"
```

---

## Phase 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select the `roadmap_builder` repository

### 2.2 Configure Service

1. Railway will detect the repo - click on the created service
2. Go to **Settings** tab
3. Set **Root Directory**: `server`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2.3 Set Environment Variables

Go to **Variables** tab and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `MONGODB_URI` | `mongodb+srv://...` | Your Atlas connection string |
| `GEMINI_API_KEY` | `AIza...` | Your Gemini API key |
| `ENVIRONMENT` | `production` | |
| `CORS_ORIGINS` | `https://your-app.vercel.app` | Update after Vercel deploy |
| `PORT` | `8000` | Railway provides this automatically |

**For Firebase Service Account** (choose one method):

**Method A: JSON as environment variable**
```
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```
Then update `server/app/middleware/auth.py` to parse JSON from env var.

**Method B: Base64 encoded**
```bash
# Encode locally
base64 -i firebase-service-account.json
```
Set as `FIREBASE_CREDENTIALS_BASE64` and decode in code.

### 2.4 Deploy

1. Railway auto-deploys on push to main branch
2. Click **"Deploy"** to trigger manual deploy
3. Watch logs for successful startup
4. Note the public URL: `https://roadmap-api-production-xxxx.up.railway.app`

### 2.5 Verify Backend

```bash
# Health check
curl https://your-railway-url.up.railway.app/health

# Expected: {"status":"healthy","environment":"production"}
```

---

## Phase 3: Deploy Frontend to Vercel

### 3.1 Connect Repository

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Select the `roadmap_builder` repo

### 3.2 Configure Build Settings

| Setting | Value |
|---------|-------|
| **Framework Preset** | Vite |
| **Root Directory** | `client` |
| **Build Command** | `bun run build` |
| **Output Directory** | `dist` |
| **Install Command** | `bun install` |

### 3.3 Set Environment Variables

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-railway-url.up.railway.app/api/v1` |
| `VITE_FIREBASE_API_KEY` | Your Firebase API key |
| `VITE_FIREBASE_AUTH_DOMAIN` | `your-project.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | `your-project-id` |

### 3.4 Deploy

1. Click **"Deploy"**
2. Wait for build to complete
3. Note your Vercel URL: `https://your-app.vercel.app`

---

## Phase 4: Connect the Pieces

### 4.1 Update Railway CORS

Go back to Railway and update the `CORS_ORIGINS` variable:
```
https://your-app.vercel.app
```

Redeploy Railway service for changes to take effect.

### 4.2 Update Firebase Authorized Domains

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to **Authentication** → **Settings** → **Authorized domains**
4. Add your Vercel domain: `your-app.vercel.app`

### 4.3 Test Full Flow

1. Open your Vercel URL in browser
2. Click "Sign in with Google"
3. Verify login succeeds
4. Create a new roadmap
5. Verify SSE progress streaming works
6. Open a session and test AI chat

---

## Phase 5: Polish (Optional)

### 5.1 Custom Domain

**Vercel:**
1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS at your registrar

**Railway:**
1. Go to Service Settings → Networking
2. Add custom domain
3. Configure DNS CNAME record

### 5.2 Railway Credit Monitoring

Monitor usage in Railway dashboard:
- Check **Usage** tab for credit consumption
- Set up email alerts if available
- Consider upgrading to Hobby plan ($5/month) for predictable billing

### 5.3 Fallback to Render (If Needed)

If Railway credits run out mid-month:

1. Create account at [Render](https://render.com)
2. Create new Web Service from GitHub
3. Same configuration as Railway
4. Update Vercel `VITE_API_URL` to Render URL
5. Update Firebase authorized domains

---

## Environment Variables Summary

### Backend (Railway)

```env
# Database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/roadmap_builder

# Firebase (see method options above)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# AI
GEMINI_API_KEY=AIza...

# Server
ENVIRONMENT=production
CORS_ORIGINS=https://your-app.vercel.app
```

### Frontend (Vercel)

```env
VITE_API_URL=https://your-railway-url.up.railway.app/api/v1
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
```

---

## Troubleshooting

### Backend won't start

1. Check Railway logs for error messages
2. Verify all environment variables are set
3. Ensure `requirements.txt` is complete
4. Check Python version compatibility

### CORS errors

1. Verify `CORS_ORIGINS` includes exact Vercel URL (with https://)
2. Check no trailing slash in CORS_ORIGINS
3. Redeploy Railway after changing CORS

### Firebase auth fails

1. Check Vercel domain is in Firebase authorized domains
2. Verify Firebase env vars are correct
3. Check browser console for specific error

### SSE streaming issues

1. Railway should handle SSE fine
2. Check response headers include `text/event-stream`
3. Verify no proxy/CDN is buffering the response

---

## Verification Checklist

- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Google OAuth login works
- [ ] Dashboard shows (empty or with roadmaps)
- [ ] Create roadmap flow works with SSE progress
- [ ] Session view loads content
- [ ] AI chat responds correctly
- [ ] Notes save successfully
- [ ] Session status updates persist

---

## Cost Summary

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| Railway | $0 (with $5 credit) | May run out if 24/7 |
| Vercel | $0 | Generous free tier |
| MongoDB Atlas | $0 | M0 free tier |
| Firebase Auth | $0 | Free tier |
| Gemini API | $0 | Free tier limits |
| **Total** | **$0/month** | |

---

## Post-Deployment

After successful deployment:

1. Delete this plan file
2. Update README.md with production URLs
3. Remove any development-only configurations
4. Consider setting up monitoring/alerting
