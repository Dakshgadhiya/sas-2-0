# Quick Deployment Setup Checklist

## ✅ Step 1: Set Render Environment Variables

1. Go to https://dashboard.render.com
2. Click your backend service: `sas-2-0-backend`
3. Go to **Settings** → **Environment**
4. Add these variables:

| Key | Value |
|-----|-------|
| `APP_SECRET_KEY` | `your-secret-key-here-change-me` |
| `JWT_SECRET` | `your-jwt-secret-here-change-me` |
| `FLASK_ENV` | `production` |
| `PYTHONUNBUFFERED` | `true` |

5. Click **Save Changes**
6. Service will auto-redeploy

## ✅ Step 2: Set Vercel Environment Variables

1. Go to https://vercel.com/dashboard
2. Click your frontend project
3. Go to **Settings** → **Environment Variables**
4. Add this variable:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://sas-2-0-tosl.onrender.com` |

5. Click **Save**
6. Go to **Deployments** → Click latest deploy → **Redeploy**

## ✅ Step 3: Test

After both deployments complete (2-5 minutes):

1. Open Vercel frontend URL
2. Login with:
   - Email: `shailesh@gmail.com`
   - Password: `12345678`
3. You should see lectures and attendance data

## ✅ Troubleshooting

**No data showing after login?**
- Wait 5 minutes for Render to fully deploy
- Check Render logs for errors: Dashboard → Service → Logs
- Manually trigger redeploy on Render

**Frontend shows "Cannot connect to backend"?**
- Verify `VITE_API_URL` is set correctly on Vercel
- Check that Render backend URL is accessible: https://sas-2-0-tosl.onrender.com/health
- Redeploy Vercel frontend

**Still stuck?**
- Run locally first: `python app.py` in backend terminal
- Verify data loads: Login and check attendance
- Then redeploy to production
