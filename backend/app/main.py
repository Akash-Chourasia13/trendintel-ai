from fastapi import FastAPI
from app.api import routes,scraper_routes,ingest
from playwright.async_api import async_playwright  # Async Playwright for browser automation

from fastapi.middleware.cors import CORSMiddleware

# main.py

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())



app = FastAPI(title = "TrendIntel AI")
# @app.get("/test-browser")
# async def test_browser():
#     print("Trying to launch browser...")
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         print("✅ Playwright browser launched")
#         await browser.close()
#     return {"message": "Playwright works!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(scraper_routes.router)
app.include_router(ingest.router)