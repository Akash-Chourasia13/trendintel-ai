# app/api/scraper_routes.py

from fastapi import APIRouter, Body
from app.utils.scraper_trigger import trigger_scraper

router = APIRouter()

@router.post("/run-scraper")
async def run_scraper(site_name: str = Body(..., embed=True)):
    print("hgjj")
    result = await trigger_scraper(site_name)
    return result
