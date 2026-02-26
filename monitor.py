import asyncio
import logging
import os
import random
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8019517748:AAHtMBh7jeGco0_WQWgIxPqh76qYsiiuJbA")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "1894115469")

TARGET_URL   = "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-semi-final-2/ET00474271"
CHECK_EVERY  = 30   # seconds
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
#  BROWSER CHECK — acts like a real human
# ─────────────────────────────────────────
async def check_with_browser():
    async with async_playwright() as p:
        # Launch real Chromium browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",  # hide bot flag
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True,
            # Spoof real browser properties
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            }
        )

        # Hide automation flags
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        try:
            log.info("Opening BookMyShow page in headless browser...")

            # Go to page and wait for content to fully load
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)

            # Wait a bit for JS to render the button
            await asyncio.sleep(random.uniform(3, 5))

            # Try to wait for the key button to appear
            try:
                await page.wait_for_selector("button, a", timeout=8000)
            except:
                pass

            # Get full page text
            page_text = await page.inner_text("body")
            page_text_lower = page_text.lower()

            log.info(f"Page loaded. Scanning for keywords...")

            # Check for Book Now button specifically
            book_now_btn = None
            try:
                book_now_btn = await page.query_selector("text=Book Now")
            except:
                pass

            if book_now_btn or TRIGGER_TEXT in page_text_lower:
                log.info("🎉 'Book Now' DETECTED!")
                await browser.close()
                return "available"

            elif BLOCK_TEXT in page_text_lower:
                log.info("⏳ Still showing 'Coming Soon'")
                await browser.close()
                return "coming_soon"

            else:
                # Log a snippet to help debug
                snippet = page_text[:300].replace('\n', ' ')
                log.warning(f"Page loaded but status unclear. Snippet: {snippet}")
                await browser.close()
                return "unknown"

        except Exception as e:
            log.error(f"Browser error: {e}")
            await browser.close()
            return None

# ─────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────
async def main():
    log.info("🚀 BMS Ticket Monitor v3 (Browser Mode) Started")
    log.info(f"   URL        : {TARGET_URL}")
    log.info(f"   Check every: {CHECK_EVERY} seconds")
    log.info(f"   Method     : Playwright Headless Browser")
    log.info("─" * 55)

    send_telegram(
        "🟢 <b>BMS Monitor v3 Started!</b>\n\n"
        "🏏 <b>ICC T20 World Cup 2026 — Semi Final 2</b>\n"
        f"Checking every <b>{CHECK_EVERY} seconds</b>\n"
        "Using <b>Real Browser</b> — bot protection bypassed! 💪\n\n"
        "I'll alert you the moment <b>Book Now</b> goes live! 🎟️"
    )

    alert_sent   = False
    check_count  = 0
    error_streak = 0

    while True:
        check_count += 1
        log.info(f"[Check #{check_count}] Launching browser check...")

        status = await check_with_browser()

        if status == "available":
            log.info("🎉 TICKETS ARE LIVE!")
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
            log.info("⏳ Still 'Coming Soon'. Waiting...")
            alert_sent = False
            error_streak = 0

        elif status == "unknown":
            log.warning("⚠️ Page loaded but couldn't detect status clearly.")
            error_streak = 0

        else:  # None = total failure
            error_streak += 1
            log.error(f"❌ Browser check failed (streak: {error_streak})")

            if error_streak >= 5:
                send_telegram(
                    "⚠️ <b>Monitor Warning</b>\n\n"
                    f"Browser failed to load page <b>{error_streak} times</b>.\n"
                    "Possible network issue on server.\n"
                    "Still retrying automatically... 🔄"
                )
                error_streak = 0

        # Wait before next check (slightly random to avoid patterns)
        sleep_time = CHECK_EVERY + random.uniform(-3, 3)
        log.info(f"Waiting {sleep_time:.0f} seconds before next check...")
        await asyncio.sleep(max(20, sleep_time))


if __name__ == "__main__":
    asyncio.run(main())
