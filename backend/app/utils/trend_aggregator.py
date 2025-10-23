import pandas as pd
from ast import literal_eval
from collections import defaultdict,Counter
import re 
import json
import os

# Load Data
df = pd.read_csv(r'D:\trendIntel\trendintel-ai\backend\scraped_data\girl-kurta-sets\girl-kurta-sets_2025-10-18_19-59-39.csv')
# Normalize Nested Json columns
df['reviews'] = df['reviews'].apply(lambda x: literal_eval(x) if isinstance(x,str) else [])

# Compute Aspect-level stats
aspect_counts = defaultdict(lambda:{'positive':0,'negative':0,'neutral':0,'total':0,'avg_conf':0})
for _,row in df.iterrows():
    for review in row['reviews']:
        aspects = review.get('aspect_sentiments',{})
        for aspect,items in aspects.items():
            for item in items:
                label = item['label'].lower()
                conf = item['confidence']
                aspect_counts[aspect]['total'] += 1
                aspect_counts[aspect]['avg_conf'] += conf
                if 'pos' in label: aspect_counts[aspect]['positive'] += 1
                if 'neg' in label: aspect_counts[aspect]['negative'] += 1
                else: aspect_counts[aspect]['neutral'] += 1

for aspect,d in aspect_counts.items():
    if d['total']:
        d['avg_conf'] /= d['total']

# Material Trend
def extract_materials(text):
    materials = ['cotton','silk','polyester','rayon','georgette','linen']
    found = [m for m in materials if m.lower() in str(text).lower()]
    return found[0] if found else None

df['material_type'] = df['material_and_care'].apply(extract_materials)

material_sentiments = df.groupby('material_type')['rating'].mean().sort_values(ascending=False)
print("=============================")
# print(material_sentiments)

# Keywords Trend
kw_counter = Counter()
for _,row in df.iterrows():
    for r in row['reviews']:
        kw_counter.update(r.get('keywords',[]))
top_keywords = kw_counter.most_common(20)
# print(top_keywords)      

# Price Sentiments Curve
bins = [0,500,1000,1500,2000,5000]
df['price_bin'] = pd.cut(df['display_price_value'],bins)
price_sentiment = df.groupby('price_bin')['rating'].mean().sort_values(ascending=False)
# print(price_sentiment)

# Complaint Mining - Collect all negative aspect contexts - cluster by aspect word
complaints = defaultdict(list)
for _,row in df.iterrows():
    for review in row['reviews']:
        for aspect,items in review.get('aspect_sentiments',{}).items():
            for item in items:
                if item['label'] == 'negative':
                    complaints[aspect].append(item['context'])
# print(complaints)                     

# Brand Benchmarking
brand_aspect = defaultdict(lambda:defaultdict(list))
for _,row in df.iterrows():
    brand = row['title']
    for review in row['reviews']:
        for aspect,items in review.get('aspect_sentiments',{}).items():
            for item in items:
                brand_aspect[brand][aspect].append(item['label'])
brand_summary = {b:{a:round((labels.count('positive')/len(labels))*100,2) if labels else None for a,labels in asp.items()} for b,asp in brand_aspect.items()}    
# print(brand_summary)            

trend_summary = {
    "category": "Girls Kurta Sets",
    "total_products": len(df),
    "avg_rating": round(df["rating"].mean(), 2),
    "top_materials": material_sentiments.to_dict(),
    "aspect_summary": aspect_counts,
    "top_keywords": top_keywords,
    "price_sentiment_curve": price_sentiment.to_dict(),
    "complaints": complaints,
    "brand_summary": brand_summary
}
# print(trend_summary)
des = df["description"]
# Make sure directory exists
os.makedirs("outputs/trends", exist_ok=True)
des.to_csv("outputs/trends/girls-kurta-sets_trend_description.csv", index=False, encoding="utf-8")

# with open("outputs/trends/girls-kurta-sets_trend_summary.json","w",encoding="utf-8") as f:
#     json.dump(trend_summary,f,indent=2,ensure_ascii=False)



