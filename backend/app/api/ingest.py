from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import session
from sqlalchemy import select
from app.db.database import get_db
from app.schemas.schemas import IngestBatchIn, IngestResult
from app.models import models as m 
from app.utils.ids import review_uid_from

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

@router.post("/batch", response_model=IngestResult)
def ingest_batch(payload: IngestBatchIn, db: session = Depends(get_db)):
    products_upserted = 0
    reviews_inserted = 0
    snapshots_added = 0

    for p in payload.items:
        #Platform
        platform = db.execute(select(m.Platform).where(m.Platform.name == p.platform_name)).scalar_one_or_none()
        if not platform:
            platform = m.Platform(name=p.platform_name)
            db.add(platform)
            db.flush()

        # Category
        category = db.execute(
            select(m.Category).where(m.Category.name == p.category_name, m.Category.platform_id == platform.id)
        ).scalar_one_or_none()    
        if not category:
            category = m.Category(name=p.category_name, platform_id=platform.id)
            db.add(category)
            db.flush()

        # Product (upsert by product_link)
        product = db.execute(select(m.Product).where(m.Product.product_link == str(p.product_link))).scalar_one_or_none() 
        if not product:
            product = m.Product(
                product_link=str(p.product_link),
                title=p.title,
                brand=p.brand,
                description=p.description,
                image_url=str(p.image_url) if p.image_url else None,
                rating=p.rating,
                number_of_ratings=p.number_of_ratings,
                display_price_value=p.display_price_value,
                mrp_value=p.mrp_value,
                discount_value=p.discount_value,
                selling_price_value=p.selling_price_value,
                product_detail_with_color=p.product_detail_with_color,
                size_and_fit=p.size_and_fit,
                material_and_care=p.material_and_care,
                specifications=p.specifications,
                sentiment_overall=p.sentiment_overall,
                category_id=category.id,
                platform_id=platform.id,
            )   
            db.add(product)
            db.flush()
            products_upserted += 1
        else:
            # update latest fields
            product.title = p.title
            product.brand = p.brand
            product.description = p.description
            product.image_url = str(p.image_url) if p.image_url else product.image_url
            product.rating = p.rating
            product.number_of_ratings = p.number_of_ratings
            product.display_price_value = p.display_price_value
            product.mrp_value = p.mrp_value
            product.discount_value = p.discount_value
            product.selling_price_value = p.selling_price_value
            product.product_detail_with_color = p.product_detail_with_color
            product.size_and_fit = p.size_and_fit
            product.material_and_care = p.material_and_care
            product.specifications = p.specifications
            product.sentiment_overall = p.sentiment_overall
            # category/platform unchanged

        # Features: Simple re-sync (optional: smarter diff)
        if p.features:
            #wipe & add for simplicity (safe because features are small) 
            db.query(m.Feature).filter(m.Feature.product_id == product.id).delete()
            for f in p.features:
                db.add(m.Feature(key=f.key, value=f.value, product_id=product.id))

        # Images: upsert by URL
        if p.images:
            existing = {img.image_url for img in product.images}
            for im in p.images:
                url = str(im.image_url)
                if url not in existing:
                    db.add(m.ProductImage(image_url=url, product_id=product.id))

        # reviews: insert only new (by review_uid)
        if p.reviews:
            existing_uids = set(
                r[0] for r in db.query(m.Review.review_uid).filter(m.Review.product_id == product.id).all()
            )
            for r in p.reviews:
                uid = r.review_uid or review_uid_from(r.review_text or "",r.reviewer or "", r.date or "")
                if uid in existing_uids:
                    continue
                db.add(m.Review(
                    review_uid=uid,
                    reviewer=r.reviewer,
                    rating=r.rating,
                    review_text=r.review_text,
                    date=r.date,
                    summary=r.summary,
                    keywords=r.keywords,
                    overall_sentiment=r.overall_sentiment,
                    aspect_sentiments=r.aspect_sentiments,
                    product_id=product.id 
                ))                               
                reviews_inserted += 1

            # Snapshot: take a point-in-time record(optional toggle) 
            db.add(m.ProductSnapshot(product_id=product.id,
            avg_rating=product.rating,
            review_count=product.number_of_ratings,
            sentiment_overall=product.sentiment_overall
            ))
            snapshots_added += 1

    db.commit()
    return IngestResult(
        products_upserted=products_upserted,
        reviews_inserted=reviews_inserted,
        snapshots_added=snapshots_added 
    )        

