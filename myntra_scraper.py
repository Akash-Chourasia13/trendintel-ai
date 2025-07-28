# 📦 Standard libraries
import asyncio
import re, os, random, json

# 📦 Third-party libraries
from playwright.async_api import async_playwright  # Async Playwright for browser automation
from playwright_stealth import stealth_async       # Helps bypass bot detection
import pandas as pd                                # For saving scraped data to Excel

# 🌐 Proxy list - rotating proxies to reduce chance of IP bans
proxies = [
    {"server": "isp.decodo.com:10001", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"},
    {"server": "isp.decodo.com:10002", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"},
    {"server": "isp.decodo.com:10003", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"}
]

# 🧠 Create a browser context with randomized settings to mimic real users
async def create_dynamic_context(browser):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    ]
    locales = ["en-US", "en-GB", "hi-IN", "fr-FR"]
    timezones = ["Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Tokyo"]
    viewports = [{"width": 1280, "height": 800}]

    # 🎭 Create a new browser context with randomized settings
    context = await browser.new_context(
        user_agent=random.choice(user_agents),
        locale=random.choice(locales),
        timezone_id=random.choice(timezones),
        viewport=random.choice(viewports)
    )
    return context

# ✅ A safe wrapper around page.goto with retries and backoff
async def safe_goto(page, url, retries=3):
    for i in range(retries):
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"⚠️ Retry {i+1}/{retries} for {url} due to error: {e}")
            await asyncio.sleep(2 ** i)  # Wait 1, 2, 4... seconds
    return False

# 🧲 Core scraping function to collect product links from a category page
async def scrape_category(page, category_url):
    success = await safe_goto(page, category_url)
    if not success:
        print(f"❌ Failed to load {category_url}")
        return []

    # Random wait to mimic human behavior
    await asyncio.sleep(random.uniform(5, 10))

    # Wait for product container to load
    await page.wait_for_selector('ul.results-base > li', timeout=10000)

    # 🔃 Scroll down to trigger lazy loading
    for _ in range(10):
        await page.mouse.wheel(0, random.randint(100, 300))
        await page.wait_for_timeout(random.randint(500, 1000))

    await asyncio.sleep(random.uniform(3, 6))

    # Extract all product links
    li_elements = await page.query_selector_all("ul.results-base > li.product-base")
    product_links = []
    for li in li_elements:
        a_tag = await li.query_selector("a")
        href = await a_tag.get_attribute("href") if a_tag else None
        if href:
            product_links.append({'Product_Link': f"https://www.myntra.com/{href}"})

    print(f"🧭 Found {len(product_links)} links on this page.")
    return product_links

# 🚀 Main function to manage the scraping process
async def main():
    category_urls = [
        # Add more categories here
        "https://www.myntra.com/bra"
    ]
    total_pages_to_scrape = 2
    all_results = []

    # 🎬 Start Playwright session
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for background scraping

        for category_url in category_urls:
            for page_num in range(1, total_pages_to_scrape + 1):
                paginated_url = f"{category_url}?p={page_num}"
                print(f"📄 Scraping: {paginated_url}")

                try:
                    # Rotate proxy for every request
                    proxy = random.choice(proxies)

                    # 🧱 Create a new context for each page (mimics new user session)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        locale="en-US",
                        timezone_id="Asia/Kolkata",
                        viewport={"width": 1280, "height": 800},
                        proxy={
                            "server": f"http://{proxy['server']}",
                            "username": proxy["username"],
                            "password": proxy["password"]
                        }
                    )

                    page = await context.new_page()

                    # Add headers to look less like a bot
                    await page.set_extra_http_headers({
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.google.com/"
                    })

                    await asyncio.sleep(random.uniform(3, 6))

                    # 🔍 Scrape this page
                    links = await scrape_category(page, paginated_url)
                    all_results.extend(links)

                    # Clean up
                    await page.close()
                    await context.close()
                    await asyncio.sleep(random.uniform(1, 2))

                except Exception as e:
                    print(f"❌ Error scraping {paginated_url}: {e}")

        await browser.close()

    # 💾 Save the collected product links to Excel
    df = pd.DataFrame(all_results, columns=["Product_Link"])
    df.to_excel("myntra_bra_links.xlsx", index=False)
    print("✅ Saved to myntra_bra_links.xlsx")

# 🧵 Entry point of the script
if __name__ == "__main__":
    asyncio.run(main())  # 🔁 Run the async main function inside event loop
