# Render & Vercel Deployment Setup Guide for SAS 2.0

## Step 1: Set Environment Variables on Render

Go to https://dashboard.render.com/ → Your Backend Service → Environment

Add these variables:
```
APP_SECRET_KEY = sas_super_secret_key_2026
JWT_SECRET = sas_jwt_secret_2026
FLASK_ENV = production
DATABASE_URL = sqlite:////var/data/app.db
PYTHONUNBUFFERED = true
```

## Step 2: Set Environment Variables on Vercel

Go to https://vercel.com/dashboard → Your Frontend Project → Settings → Environment Variables

Add this variable:
```
VITE_API_URL = https://sas-2-0-i41p.onrender.com/
```

## Step 3: Push to GitHub

After setting variables, push any changes:
```bash
git add .
git commit -m "Add render.yaml and deployment configs"
git push origin main
```

## Step 4: Trigger Redeploy

- **Render**: Dashboard → Services → Redeploy
- **Vercel**: Dashboard → Deployments → Redeploy latest

## Step 5: Seed Database with Initial Data

Option A: Run locally, then push to Render
```bash
python regenerate_attendance.py
git add backend/app.db
git commit -m "Add populated database"
git push origin main
# Then redeploy on Render
```

Option B: Set up automatic seeding on first startup (recommended)
- We can modify app.py to auto-seed if database is empty

## Testing

After deployment:

1. Test backend health:
   ```
   https://sas-2-0-tosl.onrender.com/health
   ```

2. Test login (via frontend at Vercel URL):
   - Email: `shailesh@gmail.com`
   - Password: `12345678`

3. Check if lectures/attendance appear
