from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="user_data",
        headless=False,
        locale="en-US"
    )
    page = browser.new_page()
    page.goto("https://www.amazon.in/dp/B0CHWV2WYK")
    input("Press Enter after you see the page...")
    browser.close()
