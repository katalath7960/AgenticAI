# 📈 Stock Alert Agent

Real-time stock price monitoring agent that sends **free email alerts** (via Gmail SMTP) when prices rise above your threshold.

## How It Works

1. Fetches live prices from **Yahoo Finance** every 60 seconds
2. Compares current price to baseline for each tracked stock
3. Sends a **formatted HTML email via Gmail** (free, 500/day) when price rises ≥ your threshold %
4. Resets baseline after each alert so the next alert tracks from the new price

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```
> `smtplib` and `email` are Python built-ins — no extra install needed.

### 2. Configure Gmail (free, 2 minutes)
1. Go to **myaccount.google.com → Security → 2-Step Verification** and enable it
2. Then go to **Security → App Passwords**
3. Create an App Password for "Mail" — Google gives you a 16-character code
4. Fill in your `.env` and load it:

```bash
cp .env.example .env
export $(cat .env | xargs)
```

### 3. Add stocks to your watchlist
```bash
python agent.py add AAPL --threshold 1.5
python agent.py add TSLA --threshold 2.0
python agent.py add NVDA --threshold 1.0
```

### 4. Start the agent
```bash
python agent.py run --interval 60   # checks every 60s
python agent.py check               # run once now
streamlit run dashboard.py          # optional visual dashboard
```

---

## CLI Commands

| Command | Description |
|---|---|
| `python agent.py add AAPL --threshold 1.5` | Track AAPL, alert at +1.5% |
| `python agent.py remove AAPL` | Stop tracking AAPL |
| `python agent.py list` | Show all tracked stocks |
| `python agent.py check` | Run one price check now |
| `python agent.py run --interval 60` | Start continuous monitoring |

---

## Email Alert Example

```
Subject: 📈 Stock Alert: AAPL +1.52%

Previous price : $182.50
Current price  : $185.28
Change         : +1.52%
Threshold      : +1.5%
Time           : 2026-04-02 14:32:01
```

---

## Notes

- **Completely free** — Gmail SMTP is free (500 emails/day limit)
- **App Password** is a special 16-char code, not your regular Gmail password
- **ALERT_EMAIL** can be any address — your Gmail, work email, or a Slack email integration
- **Market hours**: Yahoo Finance returns the last known price outside market hours
