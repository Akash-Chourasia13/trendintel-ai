# 📦 Standard libraries
import asyncio
import re, os, random, json
from urllib.parse import urlparse
from datetime import datetime
from typing import Optional

from transformers import pipeline

# 📦 Third-party libraries
from playwright.async_api import async_playwright  # Async Playwright for browser automation
from playwright_stealth import stealth_async       # Helps bypass bot detection
import pandas as pd     

from asyncio import Semaphore                           # For saving scraped data to Excel
from more_itertools import chunked  # pip install more-itertools



# 🌐 Proxy list - rotating proxies to reduce chance of IP bans
proxies = [
    {"server": "isp.decodo.com:10001", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"},
    {"server": "isp.decodo.com:10002", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"},
    {"server": "isp.decodo.com:10003", "username": "spavxwrl7o", "password": "d5_aqvaCG3eacVi1P8"}
]

# 🧠 Create a browser context with randomized settings to mimic real users
async def create_dynamic_context(browser):
    # user_agents = [
    #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    #     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    #     "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    #     "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
    # ]
    # locales = ["en-US", "en-GB", "hi-IN", "fr-FR"]
    # timezones = ["Asia/Kolkata", "America/New_York", "Europe/London", "Asia/Tokyo"]
    # viewports = [{"width": 1280, "height": 800}]

    # # 🎭 Create a new browser context with randomized settings
    # context = await browser.new_context(
    #     user_agent=random.choice(user_agents),
    #     locale=random.choice(locales),
    #     timezone_id=random.choice(timezones),
    #     viewport=random.choice(viewports)
    # )
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


    return context

# ✅ A safe wrapper around page.goto with retries and backoff
async def safe_goto(page, url, retries=3):
    for i in range(retries):
        try:
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f" Retry {i+1}/{retries} for {url} due to error: {e}")
            await asyncio.sleep(2 ** i)  # Wait 1, 2, 4... seconds
    return False

# 🧲 Core scraping function to collect product links from a category page
async def scrape_category(page, category_url):
    success = await safe_goto(page, category_url)

    if not success:
        print(f" Failed to load {category_url}")
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

    print(f"Found {len(product_links)} links on this page.")
    return product_links


def _clean_number(text: str) -> Optional[int]:
    """Return integer value found in text (first group of digits), or None."""
    if not text:
        return None
    m = re.search(r"(\d[\d,]*)", text.replace("\u00A0", " "))
    if not m:
        return None
    return int(m.group(1).replace(",", ""))

async def extract_reviews_details(review_link: str) -> dict:
    """Async helper to extract reviews details from the reviews page."""
    result = {}
    if not review_link:
        return result
    await asyncio.sleep(random.uniform(2, 4))
        
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)    
        page = None
        try:
            newContext = await create_dynamic_context(browser)
            page = await newContext.new_page()
        except Exception as e:
            print(f"❌ Error creating new page: {e}")
            return  # or continue to next iteration (if inside loop)

        if page:
            print(f"🔎 Scraping review details for {review_link}...")
            await safe_goto(page, review_link)
            await asyncio.sleep(random.uniform(2, 4))

        # wait for reviews container to load
        await page.wait_for_selector("div.detailed-reviews-userReviewsContainer",timeout = 20000)
        await asyncio.sleep(random.uniform(2, 4))

        reviews = []

        review_elements = await page.query_selector_all("div.user-review-userReviewWrapper")
        # 🔃 Scroll down to trigger lazy loading
        for _ in range(10):
            await page.mouse.wheel(0, random.randint(100, 300))
            await page.wait_for_timeout(random.randint(500, 1000))
        for review in review_elements:
            # Extract rating
            rating_el = await review.query_selector("span.user-review-starRating")
            rating = await rating_el.inner_text() if rating_el else None

            # Extract review text
            text_el = await review.query_selector("div.user-review-reviewTextWrapper")
            review_text = await text_el.inner_text() if text_el else None

            # Extract reviewer name & date
            footer_el = await review.query_selector("div.user-review-footer div.user-review-left")
            spans = await footer_el.query_selector_all("span") if footer_el else []
            name = await spans[0].inner_text() if len(spans) > 0 else None
            date = await spans[1].inner_text() if len(spans) > 1 else None

            reviews.append({
                "rating": rating,
                "review_text": review_text,
                "reviewer": name,
                "date": date
            })
            # Load sentiment model (lightweight version for speed)
            sentiment_analyzer = pipeline("sentiment-analysis")

            # def analyze_sentiment(review_text):
            sentiment = sentiment_analyzer(review_text[:512])[0]['label'].lower()  # truncate to 512 tokens
            reviews[-1]['sentiment'] = sentiment
        print(f"Extracted {len(reviews)} reviews.")
        print(f"Reviews details for {review_link}: {reviews}")

        # Store reviews in result
        result["reviews"] = reviews
        return result    


    

async def extract_price_details(page) -> dict:
    """Async helper to extract price details from the product page."""
    result = {
        "display_price": None,
        "display_price_value": None,
        "mrp": None,
        "mrp_value": None,
        "discount_text": None,
        "discount_value": None,
        "selling_price_text": None,
        "selling_price_value": None,
    }

    # Prominent display price
    await page.wait_for_selector("p.pdp-discount-container", timeout=20000)  # wait for title

    display_price = await page.text_content("span.pdp-price") or ""
    display_price = display_price.strip()
    if display_price:
        result["display_price"] = display_price
        result["display_price_value"] = _clean_number(display_price)

    # MRP - try a couple of selectors
    mrp_text = await page.text_content("span.pdp-mrp-verbiage-amt") or ""

    # if not mrp_text:
    #     mrp_text = await page.text_content("span.pdp-mrp s") or ""
    mrp_text = mrp_text.strip()
    if mrp_text:
        result["mrp"] = mrp_text
        result["mrp_value"] = _clean_number(mrp_text)

    # Discount
    discount = await page.text_content("span.pdp-discount") or ""
    discount = discount.strip()
    if discount:
        result["discount_text"] = discount
        result["discount_value"] = _clean_number(discount)

    # Selling Price from verbiage block as fallback
    try:
        verbiage = await page.text_content("div.pdp-mrp-verbiage") or ""
        if verbiage:
            for line in verbiage.splitlines():
                if "selling price" in line.lower():
                    selling_price_text = line.strip()
                    result["selling_price_text"] = selling_price_text
                    result["selling_price_value"] = _clean_number(selling_price_text)
                    break
    except Exception:
        pass

    # final fallback: selling_price = display_price
    if result["selling_price_value"] is None and result["display_price_value"] is not None:
        result["selling_price_value"] = result["display_price_value"]
        if not result["selling_price_text"]:
            result["selling_price_text"] = result["display_price"]

    # Features from the first product description ul li
    features = []
    li_texts = await page.locator("div.pdp-productDescriptorsContainer ul li").all_text_contents()
    for li in li_texts:
        text = li.strip()
        if not text:
            continue
        # split on first ":" to attempt key:value
        if ":" in text:
            k, v = text.split(":", 1)
            features.append({"key": k.strip(), "value": v.strip()})
        else:
            # fallback to generic feature key
            features.append({"key": "feature", "value": text})
    if features:
        result["features"] = features

    # Size & Fit
    size_and_fit = (await page.text_content("div.pdp-sizeFitDesc h4:has-text('Size & Fit') + p")) or ""
    size_and_fit = size_and_fit.strip()
    if size_and_fit:
        result["size_and_fit"] = size_and_fit

    # Material & Care
    material_and_care = (await page.text_content("div.pdp-sizeFitDesc h4:has-text('Material & Care') + p")) or ""
    material_and_care = material_and_care.strip()
    # Replace <br> produced newlines maybe — ensure normalized
    material_and_care = " ".join(material_and_care.split())
    if material_and_care:
        result["material_and_care"] = material_and_care

    # Specifications: pairs of .index-rowKey and .index-rowValue
    specs = []
    rows = await page.locator("div.index-tableContainer > div.index-row").all()
    # if direct children pattern doesn't match, try any .index-row under .index-tableContainer
    if not rows:
        rows = await page.locator(".index-tableContainer .index-row").all()
    for r in rows:
        key = (await r.locator(".index-rowKey").text_content()) or ""
        val = (await r.locator(".index-rowValue").text_content()) or ""
        key = key.strip()
        val = val.strip()
        if key or val:
            specs.append({"key": key, "value": val})
    if specs:
        result["specifications"] = specs        

    return result


# 👇 Accept playwright, not browser
async def scrape_product_details(context, link, proxy, semaphore):
    async with semaphore:
        await asyncio.sleep(random.uniform(1, 3))
        try:
            page = await context.new_page()
        except Exception as e:
            print(f"Error creating new page: {e}")    
        try:
            print(f" Scraping product details for {link['Product_Link']}...")
            # await page.goto(link['Product_Link'])
            await page.goto(link['Product_Link'], wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2, 4))

            try:
                await page.wait_for_selector("h1.pdp-title", timeout=15000)  # wait for title
                link['title'] = (await page.text_content("h1.pdp-title")) or ""
                # sometimes description uses a different selector; fallback used here
                link['description'] = (await page.text_content("h1.pdp-name")) or ""
            except Exception as e:
                print(f" Failed to get product details for {link['Product_Link']}: {e}")

            # Ratings (wrap in try to avoid exceptions if missing)
            try:
                link['rating'] = (await page.text_content("div.index-overallRating > div:nth-child(1)")) or ""
            except Exception:
                link['rating'] = ""

            try:
                link['numberOfRatings'] = (await page.text_content("div.index-ratingsCount")) or ""
            except Exception:
                link['numberOfRatings'] = ""
            # 🔃 Scroll down to trigger lazy loading
            # for _ in range(2):
            #     await page.mouse.wheel(0, random.randint(100, 300))
            #     await page.wait_for_timeout(random.randint(500, 1000))
            # get price details via the helper
            try:
                price_info = await extract_price_details(page)
                print(f" Price details for {link['Product_Link']}: {price_info}")
                # store both raw text and numeric values
                link['display_price'] = price_info.get("display_price")
                link['display_price_value'] = price_info.get("display_price_value")
                link['mrp'] = price_info.get("mrp")
                link['mrp_value'] = price_info.get("mrp_value")
                link['discount_text'] = price_info.get("discount_text")
                link['discount_value'] = price_info.get("discount_value")
                link['selling_price_text'] = price_info.get("selling_price_text")
                link['selling_price_value'] = price_info.get("selling_price_value")
                link['features'] = price_info.get("features", [])
                link['size_and_fit'] = price_info.get("size_and_fit")
                link['material_and_care'] = price_info.get("material_and_care")
                link['specifications'] = price_info.get("specifications", [])
                href = await page.get_attribute("div.detailed-reviews-flexReviews > a", "href") or ""
                review_link = 'https://www.myntra.com' + href if href else ""
                link['reviews_link'] = review_link
                reviews_details = await extract_reviews_details(review_link)
                await asyncio.sleep(random.uniform(5, 8))
                link['reviews'] = reviews_details.get("reviews", [])
                link['sentiment'] = reviews_details.get("sentiment", None)

                print(f" Reviews details for {link['Product_Link']}: {reviews_details}")
            except Exception as e:
                print(f" Failed to get price details for {link['Product_Link']}: {e}")
                # fallback: try a simple read so you have something
                try:
                    price = (await page.text_content("span.pdp-price")) or ""
                    link['display_price'] = price
                    link['display_price_value'] = _clean_number(price)
                except Exception:
                    pass


        except Exception as e:
            print(f"Error scraping {link['Product_Link']}: {e}")
        # finally:
        #     await context.close()
        #     # await browser.close()


# 🚀 Main function to manage the scraping process
async def run_myntra_scraper():
    print("1111111111111111111")
    category_urls = [
        # Add more categories here
        "https://www.myntra.com/men-kurtas",
        # "https://www.myntra.com/girl-dresses",
        # "https://www.myntra.com/girl-lehenga-choli",
        # "https://www.myntra.com/girl-kurta-sets",


    ]
    total_pages_to_scrape = 1

    # 🎬 Start Playwright session
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False
                    #                       ,args=[
                    #     "--no-sandbox",
                    #     "--disable-setuid-sandbox",
                    #     "--disable-dev-shm-usage",
                    #     "--disable-gpu",
                    #     "--single-process",
                    # ]
                    )  # Set to True for background scraping

        for category_url in category_urls:
            all_results = []
            for page_num in range(1, total_pages_to_scrape + 1):
                paginated_url = f"{category_url}?p={page_num}"
                print(f"Scraping: {paginated_url}")

                try:
                    # Rotate proxy for every request
                    context = await create_dynamic_context(browser)
                    
                    page = await context.new_page()
                    # Add headers to look less like a bot
                    await page.set_extra_http_headers({
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": "https://www.google.com/"
                    })
                    # await page.set_extra_http_headers({
                    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                    #     "Upgrade-Insecure-Requests": "1",
                    #     "Connection": "close",  # force HTTP/1.1
                    #     "Accept-Language": "en-US,en;q=0.9",
                    #     "Referer": "https://www.google.com/"
                    # })

                    await asyncio.sleep(random.uniform(3, 6))

                    # 🔍 Scrape this page
                    links = await scrape_category(page, paginated_url)
                    all_results.extend(links)

                    # Clean up
                    await page.close()
                    # await context.close()
                    await asyncio.sleep(random.uniform(1, 2))

                except Exception as e:
                    print(f"Error scraping {paginated_url}: {e}")
            # Now get all the required details by visiting each link
            all_results = all_results[:2]
            # Run up to 5 scrapers at a time in parallel
            # Limit parallelism (e.g., max 5 concurrent scrapers)
            semaphore = asyncio.Semaphore(2)
            batch_size = 2
            for batch in chunked(all_results, batch_size):
                print(f"Processing batch of {len(batch)} tasks...")
                try:
                    context = await create_dynamic_context(browser)
                except Exception as e:
                    print("eeeee",e)    
                
                tasks = [
                    scrape_product_details(context, link, random.choice(proxies), semaphore)
                    for link in batch
                ]
                await asyncio.gather(*tasks)
                print(f" Completed one batch of {len(batch)} tasks.")
                await context.close()
                await asyncio.sleep(random.uniform(5, 8))  # delay before next batch
            

            # 💾 Save the collected product links to Excel
            df = pd.DataFrame(all_results)

            # Ensure both columns are numeric (if needed)
            df["Ratings"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
            # Use regex to extract digits from the "Number Of Ratings" column
            def extract_number(x):
                if isinstance(x, str):
                    num_str = re.sub(r"[^\d]", "", x)
                    return int(num_str) if num_str else 0
                return 0

            df["Number Of Ratings"] = df["numberOfRatings"].apply(extract_number)
            df = df.sort_values(by=["Number Of Ratings","Ratings"], ascending=[False, False])
            # Save the sorted DataFrame back to Excel
            # df.to_excel("myntra_girl-dresses_links.xlsx", index=False)
            # return {"site": "myntra", "status": "success", "message": "Myntra scraper completed"}
        
            # Extract category name from URL
            category = urlparse(category_url).path.strip("/")

            # Get timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create folder path
            folder_path = os.path.join("scraped_data", category)
            os.makedirs(folder_path, exist_ok=True)

            # Define file name
            filename = f"{category}_{timestamp}.xlsx"
            file_path = os.path.join(folder_path, filename)

            # Save the DataFrame
            df.to_excel(file_path, index=False)
            print(f"Saved to: {file_path}")
        await context.close()
        await browser.close()    


            # df = pd.read_excel('./myntra_girl-dresses_links')
            # Sort in descending order: first by Ratings, then by Number Of Ratings
            # Read the Excel file (ensure the file extension is correct)
            # df = pd.read_excel('./myntra_girl-dresses_links.xlsx')

            # # Convert columns to numeric (handle any bad/missing data)
            # df["Ratings"] = pd.to_numeric(df["Ratings"], errors="coerce").fillna(0)
            # df["Number Of Ratings"] = pd.to_numeric(df["Number Of Ratings"], errors="coerce").fillna(0)

            # # Sort in descending order by number of ratings, then ratings
            # df = df.sort_values(by=["Number Of Ratings", "Ratings"], ascending=[False, False])
            # Save to Excel
            # df.to_excel("myntra_girl-dresses_links.xlsx", index=False)

# import sys
# # 🧵 Entry point of the script
if __name__ == "__main__":
#     print(" Scraper started running!")
#     try:
#         with open("myntra_log.txt", "w", encoding="utf-8") as f:
#             f.write("Scraper started running!\n")
#             f.write("⏳ Scraping logic running...\n")
#             # Place more scraping logic and logs here
#     except Exception as e:
#         # Open the file again to log the error
#         with open("myntra_log.txt", "a", encoding="utf-8") as f:
#             f.write(f"❌ Error: {str(e)}\n")
# hr@freestoneinfotech.com
# madhvi EY HR - connect next monday

    asyncio.run(run_myntra_scraper())  # 🔁 Run the async main function inside event loop
