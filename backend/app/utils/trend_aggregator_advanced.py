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
risk_phrases = ['tight','small','loose','color','fade','poor','defect','damage','itchy']
def compute_risk_score(reviews):
    score = 0
    for r in reviews:
        text = str(r.get('review_text','')).lower()
        if any(p in text for p in risk_phrases):
            score += 1
    return score   

df['risk_score'] = df['reviews'].apply(compute_risk_score) 
risk_map = df[['title','rating','risk_score']].sort_values(by='risk_score',ascending = False).head(10)

# opportunity score
def compute_opportunity(row):
    pos_count, neg_count = 0, 0
    for r in row['reviews']:
        for a, items in r.get('aspect_sentiments', {}).items():
            for item in items:
                if item['label'] == 'positive': pos_count += 1
                elif item['label'] == 'negative': neg_count += 1
    return round(((pos_count - neg_count)*(len(row['reviews'])+1)) / (row['risk_score']), 2)     

df['opportunity_score'] = df.apply(compute_opportunity, axis=1)
top_opportunities = df[['title','rating','opportunity_score']].sort_values(by='opportunity_score',ascending=False).head(10)

# Competitive gap mapping
brand_aspect_perf = defaultdict(lambda: defaultdict(list))
for _, row in df.iterrows():
    brand = row['title'].split()[0]
    for review in row['reviews']:
        for aspect,items in review.get('aspect_sentimets', {}).items():
            for item in items:
                brand_aspect_perf[brand][aspect].append(item['label'])

brand_summary = {
    b: {a: round((labels.count('positive') / len(labels))*100,2) if len(labels) else 0
        for a,labels in asp.items()}
        for b, asp in brand_perf.items()
}

# compute category averages
aspect_avgs = defaultdict(list)
for b, asp in brand_summary.items():
    for a, score in asp.items():
        aspect_avgs[a].append(score)
aspect_avg = {a: round(np.mean(v),2) for a,v in aspect_avgs.items() if v}

brand_gap = {}
for b, asp in brand_summary.items():
    brand_gap[b] = {a: round(score - aspect_avg[a],2) for a,score in asp.items() if a in aspect_avg}


# Lifecycle / Drop-Off analysis
def parse_date_safe(date_str):
    """Convert Date dtring like '18 Oct 2025' safely to datetime"""
    try:
        return datetime.strptime(date_str, "%d %b %Y")
    except:
        return None

def compute_lifecycle_metrics(reviews):
    """Given list of reviews (each with date + sentiment), compute lifecycle dropoff metrics."""
    if not reviews:
        return {"initial_sentiment":None, "current_sentiment":None, "dropoff_pct":None, "stability_index":None, "stage":"unknown"}

    # sort reviews by date 
    dated_reviews = []
    for r in reviews:
        dt = parse_date_safe(r.get('date'))
        if dt:
            score = 1 if r.get('overall_sentiment', {}).get('label') == 'positive' else -1
            dated_reviews.append((dt,score))
    if len(dated_reviews) < 4:
        return {"initial_sentiment":None, "current_sentiment":None, "dropoff_pct":None, "stability_index":None, "stage":"unknown"}
    dated_reviews.sort(key=lambda x: x[0])

    # split into initial and recent phases 
    n = len(dated_reviews)
    split = max(1,n//3)
    initial = [s for _, s in dated_reviews[:split]]
    current = [s for _, s in dated_reviews[-split:]]

    initial_sent = np.mean(initial)
    current_sent = np.mean(current)
    dropoff = round(((initial_sent - current_sent) / abs(initial_sent)) * 100, 2) if initial_sent else 0

    # compute stability (month-to-month variance)   
    df_temp = pd.DataFrame(dated_reviews, columns=["date","score"])
    df_temp["month"] = df_temp["date"].dt.to_period("M")
    month_avg = df_temp.groupby("month")["score"].mean()
    stability_index = round(np.std(month_avg),3) if len(month_avg) > 1 else 0

    # classify lifecycle stage 
    if dropoff > 30:
        stage = " Declining Trend"
    elif dropoff < -10:
        stage = "Improving Trend"
    else:
        stage = "Stable Performer"

    return {
        "initial_sentiment": round(initial_sent,2),
        "current_sentiment": round(current_sent,2),
        "dropoff_pct": dropoff,
        "stability_index": stability_index,
        "stage": stage
    }                

# Apply for all products
lifecycle_data = []
for _, row in df.iterrows():
    lifecycle = compute_lifecycle_metrics(row['reviews'])
    lifecycle["title"] = row["title"]
    lifecycle_data.append(lifecycle)

lifecycle_df = pd.DataFrame(lifecycle_data)
top_declining = lifecycle_df.sort_values(by="dropoff_pct", ascending=False).head(5).to_dict(orient="records")
top_stable = lifecycle_df[lifecycle_df["stage"]=="Stable Performer"].head(5).to_dict(orient="records")
top_improving = lifecycle_df[lifecycle_df["stage"]=="Improving Trend"].head(5).to_dict(orient="records")


# Final Trend Summary 
advanced_trend_summary = {
    "category": "Girls Kurta Sets",
    "total_products": len(df),
    "avg_rating": round(df["rating"].mean(), 2),
    "material_occasion_matrix": material_occasion.to_dict(),
    "feature_impact": feature_sentiment,
    "combo_performance": combo_perf.to_dict(orient='records'),
    "volume_flags": volume_flags,
    "keyword_growth": keyword_growth,
    "aspect_growth": aspect_growth,
    "return_risk_top": risk_map.to_dict(orient='records'),
    "top_opportunities": top_opportunities.to_dict(orient='records'),
    "brand_summary": brand_summary,
    "brand_gap_analysis": brand_gap,
    "lifecycle_analysis": {
        "top_declining": top_declining,
        "top_stable": top_stable,
        "top_improving": top_improving
    }
}

# with open("outputs/trends/girls-kurta-sets_trend_summary_advanced.json","w",encoding="utf-8") as f:
#     json.dump(advanced_trend_summary, f, indent=2, ensure_ascii=False)

# print("✅ Advanced trend insights saved successfully!")