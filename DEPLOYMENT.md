# Deployment Guide

## 🚀 Deploy to Vercel

### 1. Deploy the Application

```bash
bun x vercel --prod
```

Follow the prompts:
- **Link to existing project?** No
- **Project name:** voroojak
- **Directory:** ./ (press Enter)
- **Override settings?** No

### 2. Set Environment Variables

After deployment, set your environment variables in Vercel:

```bash
# Using Vercel CLI
bun x vercel env add TELEGRAM_TOKEN
bun x vercel env add OPENAI_API_KEY
bun x vercel env add SUPABASE_URL
bun x vercel env add SUPABASE_KEY
bun x vercel env add WEBHOOK_URL
```

Or via Vercel Dashboard:
1. Go to your project settings
2. Navigate to "Environment Variables"
3. Add each variable from your `.env` file

### 3. Redeploy with Environment Variables

```bash
bun x vercel --prod
```

### 4. Set Telegram Webhook

After deployment, you'll get a URL like `https://voroojak.vercel.app`

Set the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook?url=https://your-app.vercel.app/api/webhook"
```

**Expected response:**
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### 5. Test Your Bot

1. Open Telegram
2. Find your bot (e.g., @voroojak_bot)
3. Send `/start`
4. You should get a welcome message!

---

## 🔍 Verify Webhook

Check webhook status:

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getWebhookInfo"
```

---

## 🛠️ Troubleshooting

### Bot doesn't respond
- Check Vercel function logs: `bun x vercel logs`
- Verify webhook is set: `getWebhookInfo`
- Ensure environment variables are set in Vercel

### "Unauthorized" message
- Verify your Telegram ID is in `allowed_users` table
- Check `is_active = true` in Supabase

### OpenAI errors
- Verify `OPENAI_API_KEY` is correct
- Check you have API credits
- Ensure model names are correct (e.g., `gpt-5-mini`)

---

## 📊 Monitor Usage

- **Vercel Dashboard:** Check function invocations
- **Supabase Dashboard:** Monitor database usage
- **OpenAI Dashboard:** Track API usage and costs
