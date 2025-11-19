# playwright_login.py
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = str(Path.cwd() / "pw_profile")  # same dir used by scraper

def run_login(url="https://www.amazon.in/"):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            slow_mo=50,              # slows actions so you can see them
            args=["--start-maximized"]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 1366, "height": 768})
        print("🔑 Browser opened. Please log in to Amazon in the opened window.")
        print("After logging in, navigate to any product review page (or click See all reviews).")
        input("When you're done logging in, press Enter here to close the browser and save session...")
        print("Saving session and closing browser...")
        browser.close()
        print("✅ Done. Persistent profile saved to:", PROFILE_DIR)

if __name__ == "__main__":
    run_login()
