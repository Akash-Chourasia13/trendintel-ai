import asyncio
import pandas as pd
from app.utils.myntra_scraper import run_myntra_scraper
from scripts.load_to_db import push_to_api

async def main():
    print(" Starting Myntra scrape...")
    df = await run_myntra_scraper()

    print(f" scraped {len(df)} products")
    print("Sending to DB via API ingest...")

    push_to_api(df)

    print("Done. Data inserted to DB successfully.")

if __name__ == "__main__":
    asyncio.run(main())    