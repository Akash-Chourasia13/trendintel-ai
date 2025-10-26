import pandas as pd
import requests 
from ast import literal_eval

API = "http://localhost:8000/api/ingest/batch"

def df_to_payload(df, platform="Myntra", category="Girls Kurta Sets"):
    items = []

    for _, row in df.iterrows():

        # Convert JSON-like strings to Python lists/dicts
        reviews = literal_eval(row.get("reviews") or "[]")
        features = literal_eval(row.get("fetaures") or "[]")
        # specs = literal_eval(row.get("specifications") or "{}")
        raw_specs = row.get("specifications")

        if isinstance(raw_specs, str):
            raw_specs = literal_eval(raw_specs)

        # convert list -> dict
        if isinstance(raw_specs, list):
            specs = {x["key"]: x["value"] for x in raw_specs if isinstance(x, dict)}
        else:
            specs = raw_specs or {}



        items.append({
            "product_link": row["Product_Link"],
            "title": row["title"],
            "brand": row["title"].split(",")[0],
            "description": row["description"],
            "image_url": None, # fill later when we scrape images

            "rating": float(str(row["rating"]).split()[0]) if row.get("rating") else None,
            "number_of_ratings": int(str(row["numberOfRatings"]).split()[0]) if row.get("numberOfRatings") else None,

            "display_price_value": row.get("display_price_value"),
            "mrp_value": row.get("mrp_value"),
            "discount_value": row.get("discount_value"),
            "selling_price_value": row.get("selling_price_value"),

            "product_detail_with_color": row.get("prodcutDetailWithColor"),
            "size_and_fit": row.get("size_and_fit"),
            "material_and_care": row.get("material_and_care"),
            "specifications": specs,
            "sentiment_overall": row.get("sentiment"),

            "platform_name": platform,
            "category_name": category,
            "features": features,
            "images": [],
            "reviews": reviews,
        })
    return {"items":items}

def push_to_api(df):
    payload = df_to_payload(df)
    response = requests.post(API, json=payload)

    print("Status", response.status_code)
    try:
        print(response.json()) 
    except:
        print(response.text)

# if __name__ == "__main__":
#     df = load_df("")                   
