from playwright.sync_api import sync_playwright
import time

def get_flipkart_title(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)
        title_el = page.query_selector("span.B_NuCI")
        title = title_el.inner_text().strip() if title_el else "Flipkart Product"
        browser.close()
        return title

def scrape_flipkart(url: str, max_scrolls=3):
    reviews = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)

        for _ in range(max_scrolls):
            page.mouse.wheel(0, 2000)
            time.sleep(2)

        review_divs = page.query_selector_all("._27M-vq")
        for div in review_divs:
            text = div.query_selector("div.t-ZTKy")
            rating = div.query_selector("._3LWZlK")
            date = div.query_selector("._2sc7ZR._2V5EHH")
            reviews.append({
                "rating": rating.inner_text() if rating else None,
                "date": date.inner_text() if date else None,
                "text": text.inner_text() if text else "",
            })
        browser.close()
    return reviews
