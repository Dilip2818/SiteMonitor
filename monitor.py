import requests
import time
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup

# ─────────────────────────────────────────
#  CONFIG — Fill these in before running
# ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8019517748:AAHtMBh7jeGco0_WQWgIxPqh76qYsiiuJbA")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "1894115469")

TARGET_URL    = "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-semi-final-2/ET00474271"
CHECK_EVERY   = 30          # seconds between each check
TRIGGER_TEXT  = "book now"  # text to look for (case-insensitive)
BLOCK_TEXT    = "coming soon"  # current text shown when NOT available

# ─────────────────────────────────────────
#  LOGGING SETUP
# ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log")
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
#  HEADERS — mimic a real browser
# ─────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://in.bookmyshow.com/",
}

# ─────────────────────────────────────────
#  TELEGRAM ALERT
# ─────────────────────────────────────────
def send_telegram_alert(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            log.info("✅ Telegram alert sent successfully!")
            return True
        else:
            log.error(f"Telegram error {r.status_code}: {r.text}")
            return False
    except Exception as e:
        log.error(f"Failed to send Telegram alert: {e}")
        return False

# ─────────────────────────────────────────
#  PAGE CHECK
# ─────────────────────────────────────────
def check_page() -> str | None:
    """
    Returns 'available' if Book Now is detected,
    'coming_soon' if still Coming Soon,
    or None on error.
    """
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(separator=" ").lower()

        if TRIGGER_TEXT in page_text:
            return "available"
        elif BLOCK_TEXT in page_text:
            return "coming_soon"
        else:
            # Neither found — log raw snippet for debugging
            log.warning("⚠️  Neither 'Book Now' nor 'Coming Soon' found on page.")
            log.debug(f"Page snippet: {page_text[:500]}")
            return "unknown"

    except requests.exceptions.RequestException as e:
        log.error(f"Request failed: {e}")
        return None

# ─────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────
def main():
    log.info("🚀 BMS Ticket Monitor Started")
    log.info(f"   URL        : {TARGET_URL}")
    log.info(f"   Check every: {CHECK_EVERY} seconds")
    log.info(f"   Watching for: '{TRIGGER_TEXT}'")
    log.info("─" * 50)

    # Send a startup confirmation to Telegram
    send_telegram_alert(
        "🟢 <b>BMS Monitor Started!</b>\n\n"
        f"Watching: ICC T20 World Cup 2026 Semi Final 2\n"
        f"Checking every <b>{CHECK_EVERY} seconds</b>\n\n"
        "I'll alert you the moment <b>Book Now</b> goes live! 🎟️"
    )

    alert_sent   = False
    check_count  = 0
    error_streak = 0

    while True:
        check_count += 1
        log.info(f"[Check #{check_count}] Fetching page...")

        status = check_page()

        if status == "available":
            log.info("🎉 BOOK NOW DETECTED!")
            if not alert_sent:
                send_telegram_alert(
                    "🚨🎟️ <b>TICKETS ARE LIVE!</b> 🎟️🚨\n\n"
                    "<b>ICC Men's T20 World Cup 2026</b>\n"
                    "Semi Final 2 — <b>Book Now is ACTIVE!</b>\n\n"
                    f"👉 <a href='{TARGET_URL}'>Click here to Book NOW</a>\n\n"
                    "⚡ Hurry before they sell out!"
                )
                alert_sent = True
                log.info("Alert sent. Continuing to monitor...")
            else:
                log.info("Alert already sent previously. Still live ✅")
            error_streak = 0

        elif status == "coming_soon":
            log.info("⏳ Still showing 'Coming Soon'. No change.")
            alert_sent   = False  # reset if page goes back (just in case)
            error_streak = 0

        elif status == "unknown":
            log.warning("Page loaded but status unclear. Will retry.")
            error_streak = 0

        else:  # None = error
            error_streak += 1
            log.error(f"⚠️  Error fetching page (streak: {error_streak})")
            if error_streak >= 5:
                send_telegram_alert(
                    "⚠️ <b>Monitor Warning</b>\n\n"
                    f"Failed to fetch the BMS page <b>{error_streak} times in a row</b>.\n"
                    "Please check if the monitor is still running correctly."
                )
                error_streak = 0  # reset after notifying

        time.sleep(CHECK_EVERY)


if __name__ == "__main__":
    main()
