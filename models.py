# models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# ================= USER MODEL =================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    date_of_birth = Column(String(20), nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), default="public")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete")
    reviews = relationship("Review", back_populates="reviewer", cascade="all, delete")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


# ================= POST MODEL =================
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Foreign key linking to user
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships
    author = relationship("User", back_populates="posts")
    reviews = relationship("Review", back_populates="post", cascade="all, delete")

    def __repr__(self):
        return f"<Post(title='{self.title}', author='{self.author_name}')>"


# ================= REVIEW MODEL =================
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String(100), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)   # positive, negative, neutral
    sentiment_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review(post_id={self.post_id}, sentiment='{self.sentiment}')>"
