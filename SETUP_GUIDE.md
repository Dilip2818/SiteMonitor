# 🎟️ BMS Ticket Monitor — Setup Guide

Monitor BookMyShow for ICC T20 World Cup 2026 Semi Final 2 ticket availability.
Gets a Telegram alert the moment **Book Now** goes live!

---

## 📁 Files Included

| File | Purpose |
|------|---------|
| `monitor.py` | Main monitoring script |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | For cloud deployment |
| `.env.example` | Template for your credentials |

---

## 🤖 Step 1 — Create Your Telegram Bot (2 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `BMS Alert Bot`)
4. Give it a username (e.g. `bms_alert_12345_bot`)
5. BotFather will give you a **Bot Token** — looks like:
   ```
   7412345678:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Now open your new bot and press **START**
7. To get your **Chat ID**, open this URL in your browser (replace YOUR_TOKEN):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
   Look for `"id"` inside `"chat"` — that's your Chat ID (e.g. `987654321`)

---

## ☁️ Step 2 — Deploy to Railway (FREE, Runs 24/7)

Railway is free and keeps your monitor running even when your PC/phone is off.

### 2a. Prepare a GitHub Repo
1. Go to [github.com](https://github.com) → Create a new repository (e.g. `bms-monitor`)
2. Upload all 4 files: `monitor.py`, `requirements.txt`, `Dockerfile`, `.env.example`

### 2b. Deploy on Railway
1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `bms-monitor` repo
4. Railway auto-detects the Dockerfile ✅

### 2c. Add Your Credentials
1. In Railway, go to your project → **Variables** tab
2. Add these two variables:
   ```
   TELEGRAM_BOT_TOKEN = 7412345678:AAFxxxxxxxxxx   ← your bot token
   TELEGRAM_CHAT_ID   = 987654321                  ← your chat id
   ```
3. Railway will restart the app automatically

### 2d. Verify It's Running
- Go to the **Logs** tab in Railway
- You should see: `🚀 BMS Monitor Started`
- You'll also get a **Telegram message** confirming it started!

---

## 💻 Alternative: Run Locally (PC must stay on)

If you prefer running it on your own machine:

```bash
# Install dependencies
pip install -r requirements.txt

# Set your credentials (Windows)
set TELEGRAM_BOT_TOKEN=your_token_here
set TELEGRAM_CHAT_ID=your_chat_id_here

# Set your credentials (Mac/Linux)
export TELEGRAM_BOT_TOKEN=your_token_here
export TELEGRAM_CHAT_ID=your_chat_id_here

# Run the monitor
python monitor.py
```

---

## 📱 What You'll Receive on Telegram

**When monitor starts:**
```
🟢 BMS Monitor Started!

Watching: ICC T20 World Cup 2026 Semi Final 2
Checking every 30 seconds

I'll alert you the moment Book Now goes live! 🎟️
```

**When tickets go live:**
```
🚨🎟️ TICKETS ARE LIVE! 🎟️🚨

ICC Men's T20 World Cup 2026
Semi Final 2 — Book Now is ACTIVE!

👉 [Click here to Book NOW]

⚡ Hurry before they sell out!
```

**If something goes wrong (5 failed checks in a row):**
```
⚠️ Monitor Warning

Failed to fetch the BMS page 5 times in a row.
Please check if the monitor is still running correctly.
```

---

## ⚠️ Important Notes

- **BookMyShow may use JavaScript** to load the button dynamically.
  If the monitor shows "unknown" status repeatedly, let me know — I can upgrade
  it to use Playwright (a browser-based scraper) for 100% accuracy.
- **Railway free tier** gives you 500 hours/month — enough for ~20 days continuous.
  For longer monitoring, consider a $5/month plan or use **Render.com** (also free).
- The monitor automatically **resets** the alert flag if the page goes back to
  "Coming Soon" (in case of a false trigger or rollback).

---

## 🆘 Need Help?

If the monitor shows "unknown" or doesn't detect the button correctly,
share the issue and I'll upgrade it with a full browser-based scraper!
