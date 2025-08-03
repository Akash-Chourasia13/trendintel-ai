# import threading
# import subprocess
# import sys
# import os

# def run_scraper_subprocess(script_path, log_path):
#     with open(log_path, "w") as log_file:
#         subprocess.Popen(
#             [sys.executable, script_path],
#             stdout=log_file,
#             stderr=log_file,
#             cwd=os.path.dirname(script_path),
#             creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
#         )

# async def trigger_scraper(site_name: str):
#     print("Triggering...")
#     if site_name.lower() == "myntra":
#         try:
#             script_path = os.path.abspath("app/utils/myntra_scraper.py")
#             log_path = os.path.abspath("app/utils/scraper.log")
            
#             print(f"Script path: {script_path}")
#             print(f"Log path: {log_path}")

#             # Check if script exists
#             if not os.path.exists(script_path):
#                 return {"status": "error", "message": "Script not found."}

#             # Run subprocess in a separate thread to avoid blocking event loop
#             thread = threading.Thread(target=run_scraper_subprocess, args=(script_path, log_path))
#             thread.start()

#             return {"status": "success", "message": "Scraper triggered in background."}

#         except Exception as e:
#             return {"status": "error", "message": str(e)}

#     return {"status": "error", "message": "Invalid site name."}



# utils/scraper_trigger.py

from app.utils.myntra_scraper import run_myntra_scraper
# In future you can import more like: from utils.amazon_scraper import run_amazon_scraper

async def trigger_scraper(site_name: str):
    if site_name.lower() == "myntra":
        result = await run_myntra_scraper()
        return result
    # elif site_name.lower() == "amazon":
    #     return run_amazon_scraper()
    else:
        return {"status": "error", "message": f"No scraper found for site: {site_name}"}
