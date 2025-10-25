from sqlalchemy import Column,Integer,String,Float,ForeignKey,Text,JSON,DateTime,Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base 

# User table (for login / dashboard access)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(50), default="user") # "admin","seller","manufacturer", "viewer"

    is_active = Column(Boolean, default=True)

    # Optional later : user linked to brand/manufacturer 
    brand = Column(String(150), nullable=True)

# Platform(Myntra/Amazon/Flipkart/Meesho)
class Platform(Base):
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    url = Column(String(255), nullable=True)

    categories = relationship("Category", back_populates="platform")

# Category(e.g "Girls Kurta", "Mens Shirts")
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"))

    platform = relationship("Platform", back_populates="categories")
    products = relationship("Product", back_populates="category")

# Product Table 
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_link = Column(Text, nullable=False, unique=True)

    title = Column(Text, nullable=False)
    brand = Column(String(100))
    description = Column(Text)

    # Add Product Image URL here 
    image_url = Column(Text,nullable=True)

    rating = Column(Float)
    number_of_ratings = Column(Integer)

    display_price_value = Column(Float)
    mrp_value = Column(Float)
    discount_value = Column(Float)
    selling_price_value = Column(Float)

    product_detail_with_color = Column(Text)
    size_and_fit = Column(Text)
    material_and_care = Column(Text)
    specifications = Column(JSON)

    sentiment_overall = Column(String(50)) # "Positive" / "neutral" / "negative"

    category_id = Column(Integer, ForeignKey("categories.id"))
    platform_id = Column(Integer, ForeignKey("platforms.id"))

    category = relationship("Category", back_populates="products")
    platform = relationship("Platform")

    features = relationship("Feature", back_populates="product", cascade="all, delete-orphan")

    # Store Multiple product Images
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    # Store all reviews (deduplicated by review_uid)
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    # Historical trend snapshots
    snapshots = relationship("ProductSnapshot", back_populates="product", cascade="all, delete-orphan")

# Features tags(shape / sleeve / embroidery / etc.)
class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100)) 
    value =Column(Text)

    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="features")

# Reviews (store history **always** - deduplicated)
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    review_uid = Column(String(255), unique=True, index=True)

    reviewer = Column(String(150))
    rating = Column(Float)
    review_text = Column(Text)
    date = Column(String(50))

    summary = Column(Text)
    keywords = Column(JSON)
    overall_sentiment = Column(JSON)
    aspect_sentiments = Column(JSON)

    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="reviews")

# Snapshot Table (for lifecycle & time trends)
class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"           

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)

    avg_rating = Column(Float)
    review_count = Column(Integer)
    sentiment_overall = Column(String(50))

    product = relationship("Product", back_populates="snapshots")

# Product Images (secondary/multiple images)
class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True,index=True)
    image_url = Column(Text, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"))
    product = relationship("Product", back_populates="images")

