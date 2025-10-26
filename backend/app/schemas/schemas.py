from typing import List,Optional,Dict,Any 
from pydantic import BaseModel, HttpUrl, Field

# Features
class FeatureIn(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None

# Image
class ProductImageIn(BaseModel):
    image_url: HttpUrl
    
# Review 
class ReviewIn(BaseModel):
    reviewer: Optional[str] = None
    rating: Optional[float] = None 
    review_text: Optional[str] = None
    date: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    overall_sentiment: Optional[Dict[str,Any]] = None
    aspect_sentiments: Optional[Dict[str, Any]] = None
    # Optinal product-side UID if available; we'll compute fallback if not provided
    review_uid: Optional[str] = None

# Product ingest (one product with nested data)
class ProductIn(BaseModel):
    product_link: HttpUrl
    title:str
    brand: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None

    rating: Optional[float] = None
    number_of_ratings: Optional[int] = None

    display_price_value: Optional[float] = None
    mrp_value: Optional[float] = None
    discount_value: Optional[float] = None
    selling_price_value: Optional[float] = None

    product_detail_with_color: Optional[str] = None
    size_and_fit: Optional[str] = None
    material_and_care: Optional[str] = None
    specifications: Optional[Dict[str,Any]] = None

    sentiment_overall: Optional[str] = None

    platform_name:str
    category_name:str

    features: Optional[List[FeatureIn]] = None
    images: Optional[List[ProductImageIn]] = None
    reviews: Optional[List[ReviewIn]] = None

class IngestBatchIn(BaseModel):
    items: List[ProductIn]

# Simple responses
class IngestResult(BaseModel):
    products_upserted: int
    reviews_inserted: int
    snapshots_added: int
