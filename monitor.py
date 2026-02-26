import requests
import time
import logging
import os
import random
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8019517748:AAHtMBh7jeGco0_WQWgIxPqh76qYsiiuJbA")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "1894115469")

TARGET_URL   = "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-semi-final-2/ET00474271"
API_URL      = "https://in.bookmyshow.com/api/explore/v1/events/ET00474271"  # BMS internal API fallback
CHECK_EVERY  = 30       # seconds
TRIGGER_TEXT = "book now"
BLOCK_TEXT   = "coming soon"

# ─────────────────────────────────────────
#  LOGGING
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
#  ROTATE USER AGENTS — looks like real browsers
# ─────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    }

def get_api_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
        "Origin": "https://in.bookmyshow.com",
        "Referer": TARGET_URL,
        "x-bms-id": "IN",
        "x-region-code": "NATIONAL",
        "x-region-slug": "national",
    }

# ─────────────────────────────────────────
#  SESSION — reuse cookies like a real browser
# ─────────────────────────────────────────
session = requests.Session()
session_initialized = False

def init_session():
    """Visit homepage first to get cookies — mimics real browser behavior"""
    global session_initialized
    try:
        log.info("Initializing session (visiting homepage for cookies)...")
        session.get(
            "https://in.bookmyshow.com/",
            headers=get_headers(),
            timeout=15
        )
        time.sleep(random.uniform(2, 4))  # human-like delay
        session_initialized = True
        log.info("Session initialized with cookies ✅")
    except Exception as e:
        log.warning(f"Session init failed (will try without cookies): {e}")

# ─────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────
def send_telegram(message: str) -> bool:
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
            log.info("✅ Telegram alert sent!")
            return True
        else:
            log.error(f"Telegram error {r.status_code}: {r.text}")
            return False
    except Exception as e:
        log.error(f"Telegram failed: {e}")
        return False

# ─────────────────────────────────────────
#  METHOD 1 — Scrape HTML page
# ─────────────────────────────────────────
def check_html_page():
    try:
        if not session_initialized:
            init_session()

        # Random delay between checks to avoid rate limiting
        time.sleep(random.uniform(1.5, 3.5))

        response = session.get(
            TARGET_URL,
            headers=get_headers(),
            timeout=20,
            allow_redirects=True
        )

        log.info(f"HTTP Status: {response.status_code}")

        if response.status_code == 403:
            log.warning("403 Forbidden — site is blocking us. Trying API method...")
            return None  # trigger fallback

        if response.status_code == 200:
            page_text = response.text.lower()

            if TRIGGER_TEXT in page_text:
                return "available"
            elif BLOCK_TEXT in page_text:
                return "coming_soon"
            else:
                log.warning("Page loaded but neither keyword found — might be JS-rendered")
                return "unknown"

        return None

    except requests.exceptions.ConnectionError:
        log.error("Connection error — network issue or site blocked")
        return None
    except requests.exceptions.Timeout:
        log.error("Request timed out")
        return None
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        return None

# ─────────────────────────────────────────
#  METHOD 2 — Try BMS internal API
# ─────────────────────────────────────────
def check_api():
    try:
        log.info("Trying BMS API endpoint...")
        r = requests.get(
            API_URL,
            headers=get_api_headers(),
            timeout=15
        )
        log.info(f"API Status: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            text = str(data).lower()
            if "book now" in text or "booknow" in text or "available" in text:
                return "available"
            elif "coming soon" in text or "comingsoon" in text:
                return "coming_soon"
            else:
                log.info(f"API response snippet: {str(data)[:300]}")
                return "unknown"
        return None
    except Exception as e:
        log.error(f"API check failed: {e}")
        return None

# ─────────────────────────────────────────
#  METHOD 3 — Mobile API endpoint
# ─────────────────────────────────────────
def check_mobile_api():
    try:
        mobile_url = f"https://in.bookmyshow.com/api/mobile/v1/events/ET00474271"
        headers = get_api_headers()
        headers["User-Agent"] = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"

        r = requests.get(mobile_url, headers=headers, timeout=15)
        log.info(f"Mobile API Status: {r.status_code}")

        if r.status_code == 200:
            text = r.text.lower()
            if "book now" in text or "booknow" in text:
                return "available"
            elif "coming soon" in text:
                return "coming_soon"
        return None
    except Exception as e:
        log.error(f"Mobile API check failed: {e}")
        return None

# ─────────────────────────────────────────
#  MASTER CHECK — tries all methods
# ─────────────────────────────────────────
def check_ticket_status():
    # Try HTML scraping first
    result = check_html_page()
    if result and result != "unknown":
        return result, "HTML"

    # Fallback to BMS API
    result = check_api()
    if result and result != "unknown":
        return result, "API"

    # Fallback to Mobile API
    result = check_mobile_api()
    if result and result != "unknown":
        return result, "Mobile API"

    # If all methods got "unknown", return it
    if result == "unknown":
        return "unknown", "all methods"

    return None, "all methods failed"

# ─────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────
def main():
    log.info("🚀 BMS Ticket Monitor v2 Started")
    log.info(f"   URL        : {TARGET_URL}")
    log.info(f"   Check every: {CHECK_EVERY} seconds")
    log.info("─" * 50)

    send_telegram(
        "🟢 <b>BMS Monitor v2 Started!</b>\n\n"
        "🏏 <b>ICC T20 World Cup 2026 — Semi Final 2</b>\n"
        f"Checking every <b>{CHECK_EVERY} seconds</b>\n"
        "Using <b>3 detection methods</b> for maximum reliability\n\n"
        "I'll alert you the moment <b>Book Now</b> goes live! 🎟️"
    )

    # Initialize session with homepage cookies
    init_session()

    alert_sent   = False
    check_count  = 0
    error_streak = 0

    while True:
        check_count += 1
        log.info(f"[Check #{check_count}] Checking ticket status...")

        status, method = check_ticket_status()

        if status == "available":
            log.info(f"🎉 BOOK NOW DETECTED via {method}!")
            if not alert_sent:
                send_telegram(
                    "🚨🎟️ <b>TICKETS ARE LIVE!</b> 🎟️🚨\n\n"
                    "<b>ICC Men's T20 World Cup 2026</b>\n"
                    "Semi Final 2 — <b>Book Now is ACTIVE!</b>\n\n"
                    f"👉 <a href='{TARGET_URL}'>Click here to Book NOW</a>\n\n"
                    "⚡ Hurry before they sell out!"
                )
                alert_sent = True
            error_streak = 0

        elif status == "coming_soon":
            log.info(f"⏳ Still 'Coming Soon' (checked via {method})")
            alert_sent = False
            error_streak = 0

        elif status == "unknown":
            log.warning(f"⚠️ Page loaded but status unclear (via {method})")
            error_streak = 0

        else:
            error_streak += 1
            log.error(f"❌ All fetch methods failed (streak: {error_streak})")

            if error_streak >= 10:
                send_telegram(
                    "⚠️ <b>Monitor Warning</b>\n\n"
                    f"Could not reach BookMyShow after <b>{error_streak} attempts</b>.\n"
                    "This may be a temporary network block.\n"
                    "The monitor will keep retrying automatically. 🔄"
                )
                error_streak = 0  # reset after notifying

        # Random sleep to avoid looking like a bot
        sleep_time = CHECK_EVERY + random.uniform(-5, 5)
        time.sleep(max(20, sleep_time))


if __name__ == "__main__":
    main()
