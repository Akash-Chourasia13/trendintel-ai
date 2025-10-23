import pandas as pd
from ast import literal_eval
from collections import defaultdict,Counter
import numpy as np
import json
import re
from datetime import datetime

# Load Data
df = pd.read_csv(r"D:\trendIntel\trendintel-ai\backend\scraped_data\girl-kurta-sets\girl-kurta-sets_2025-10-18_19-59-39.csv")
df["reviews"] = df["reviews"].apply(lambda x: literal_eval(x) if isinstance(x,str) else [])

# Helper Functions
def extract_materials(text):
    materials = ['cotton','silk','polyster','rayon','georgette','linen','blend']
    found = [m for m in materials if m.lower() in str(text).lower()]
    return found[0] if found else None

def extract_colors(text):
    colors = ['red','pink','yellow','blue','green','black','white','purple','orange','gold','silver','beige','maroon']
    found = [c for c in colors if c.lower() in str(text).lower()]
    return found[0] if found else None

def identify_occasion(description):
    desc = str(description).lower()
    festive_keywords = ["festival","festive","wedding","party","ceremony","ethnic","event","function","celebration","occasion","sangeet","navratri","diwali","gatta patti","gota patti","embroidery","embroidered","thread work","sequin","sequinned","brocade","zari","mirror work","anarkali","lehenga","sharara","patiala","angrakha","dupatta","chanderi","banarasi","silk","foiled","art silk","peplum","floral printed"]
    
    casual_keywords = ["casual","daily","regular","everyday","simple","plain","printed","cotton","straight","round neck","shirt collar","comfortable","soft fabric","machine wash","lightweight","easy wear"]

    formal_keywords = [
        "formal","office","corporate","school","uniform","presentation"
    ]
         
    # scoring logic
    score = {"festive":0,"casual":0,"formal":0}
    for word in festive_keywords:
        if word in desc:
            score["festive"] += 1
    for word in casual_keywords:
        if word in desc:
            score["casual"] += 1
    for word in formal_keywords:
        if word in desc:
            score["formal"] += 1
    # pick max score   
    max_cat = max(score,key=score.get)   
    if score[max_cat] == 0:
        return "unknown"
    return max_cat                      
    
# Basic Preprocessing
df['material_type'] = df['material_and_care'].apply(extract_materials)
df['color_type'] = df['productDetailWithColor'].apply(extract_colors)
df['occasion'] = df['description'].apply(identify_occasion)    
df['num_reviews'] = df['reviews'].apply(len)

# material * sentiment * occasion - unstack() “pivots” the inner index (in this case occasion) into columns.
material_occasion = df.groupby(['material_type','occasion'])['rating'].mean().unstack().fillna(0)

# feature/design element impact
def extract_features(features_text):
    try:
        features = literal_eval(features_text)
        return [f['value'].lower() for f in features if 'value' in f]
    except:
        return []

df['feature_list'] = df['features'].apply(extract_features)
df['rating'] = pd.to_numeric(df['rating'],errors='coerce')
feature_sentiment = defaultdict(lambda: {'count':0,'avg_rating':0})
for _,row in df.iterrows():
    rating = row['rating']
    if pd.isna(rating):
        continue
    for f in row['feature_list']:
        feature_sentiment[f]['count'] += 1
        feature_sentiment[f]['avg_rating'] += rating
for f,data in feature_sentiment.items():
    if data['count']>0:
        data['avg_rating'] = round(data['avg_rating']/data['count'],2)     

# print(feature_sentiment)    

# color + material + price combo performance
bins = [0,500,1000,1500,2000,5000]
df['price_bin'] = pd.cut(df['display_price_value'],bins)

combo_perf = (
    df.groupby(['color_type','material_type','price_bin'])['rating'].mean().reset_index().dropna().sort_values(by='rating',ascending=False)
)

# review volume vs sentiment vs rating
volume_flags = {
    "high_volume_low_rating": df[(df['num_reviews']>100) & (df['rating']<3.5)][['title','rating','num_reviews']].to_dict(orient='records'),
    "low_volume_high_rating":df[(df['num_reviews']<10) & (df['rating']>4.5)][['title','rating','num_reviews']].to_dict(orient='records')
}

# time-trend of keywords & aspects
kw_months = defaultdict(lambda:Counter())
aspect_months = defaultdict(lambda:Counter())

for _,row in df.iterrows():
    for r in row['reviews']:
        date_str = r.get('date')
        if not date_str: continue
        try:
            date_obj = datetime.strptime(date_str,"%d %b %Y")
            month_key = date_obj.strptime("%Y-%m")
        except:
            continue

        for kw in r.get('keywords',[]):
            kw_months[month_key].update([kw])   

        for aspect, items in r.get('aspect_sentiments',{}).items():
            for item in items:
                aspect_months[month_key].update([f"{aspect}_{item['label']}"])         

# trend growth (last 2 months)
def calc_growth(counter_dict):
    sorted_months = sorted(counter_dict.keys())
    if len(sorted_months) < 2: return {}
    last, prev = sorted_months[-1],sorted_months[-2]
    last_counts, prev_counts = counter_dict[last], counter_dict[prev]
    growth = {k: last_counts[k] - prev_counts.get(k,0) for k in last_counts}
    return dict(sorted(growth.items(),key=lambda x: -x[1])[:10])

keyword_growth = calc_growth(kw_months)
aspect_growth = calc_growth(aspect_months)                

# Return/Complaint risk signal 
