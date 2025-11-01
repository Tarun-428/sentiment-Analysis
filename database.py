import os
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Optional
import pandas as pd
from text_analyzer import analyze
import hashlib
from datetime import datetime

# Database connection
DATABASE_URL = 'postgresql+psycopg2://postgres:tarun@localhost:5432/sentiment_db'
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

engine = create_engine(DATABASE_URL)

def create_post(title: str, content: str, author_name: str) -> Optional[int]:
    """Create a new post and return the post ID"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO posts (title, content, author_name) 
                    VALUES (:title, :content, :author_name) 
                    RETURNING id
                """),
                {"title": title, "content": content, "author_name": author_name}
            )
            conn.commit()
            row = result.fetchone()
            return row[0] if row else None
    except SQLAlchemyError as e:
        print(f"Error creating post: {e}")
        return None

def get_all_posts() -> List[Dict]:
    """Get all posts with their basic info"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, title, content, author_name, created_at,
                       (SELECT COUNT(*) FROM reviews WHERE post_id = posts.id) as review_count
                FROM posts 
                ORDER BY created_at DESC
            """))
            posts = []
            for row in result:
                posts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'author_name': row[3],
                    'created_at': row[4],
                    'review_count': row[5]
                })
            return posts
    except SQLAlchemyError as e:
        print(f"Error getting posts: {e}")
        return []

def get_post_by_id(post_id: int) -> Optional[Dict]:
    """Get a specific post by ID"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, content, author_name, created_at FROM posts WHERE id = :post_id"),
                {"post_id": post_id}
            )
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'author_name': row[3],
                    'created_at': row[4]
                }
            return None
    except SQLAlchemyError as e:
        print(f"Error getting post: {e}")
        return None

def create_review(post_id: int, reviewer_name: str, review_text: str) -> bool:
    """Create a review for a post with sentiment analysis"""
    try:
        # Analyze sentiment of the review
        sentiment_result = analyze(review_text)
        
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO reviews (post_id, reviewer_name, review_text, sentiment, sentiment_score) 
                    VALUES (:post_id, :reviewer_name, :review_text, :sentiment, :sentiment_score)
                """),
                {
                    "post_id": post_id, 
                    "reviewer_name": reviewer_name, 
                    "review_text": review_text,
                    "sentiment": sentiment_result['sentiment'],
                    "sentiment_score": sentiment_result['compound_score']
                }
            )
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print(f"Error creating review: {e}")
        return False

def get_reviews_by_post(post_id: int, sentiment_filter: Optional[str] = None) -> List[Dict]:
    """Get all reviews for a specific post, optionally filtered by sentiment"""
    try:
        with engine.connect() as conn:
            if sentiment_filter:
                result = conn.execute(
                    text("""
                        SELECT id, reviewer_name, review_text, sentiment, sentiment_score, created_at
                        FROM reviews 
                        WHERE post_id = :post_id AND sentiment = :sentiment
                        ORDER BY created_at DESC
                    """),
                    {"post_id": post_id, "sentiment": sentiment_filter}
                )
            else:
                result = conn.execute(
                    text("""
                        SELECT id, reviewer_name, review_text, sentiment, sentiment_score, created_at
                        FROM reviews 
                        WHERE post_id = :post_id 
                        ORDER BY created_at DESC
                    """),
                    {"post_id": post_id}
                )
            
            reviews = []
            for row in result:
                reviews.append({
                    'id': row[0],
                    'reviewer_name': row[1],
                    'review_text': row[2],
                    'sentiment': row[3],
                    'sentiment_score': row[4],
                    'created_at': row[5]
                })
            return reviews
    except SQLAlchemyError as e:
        print(f"Error getting reviews: {e}")
        return []

def get_post_analytics(post_id: int) -> Dict:
    """Get analytics for a specific post"""
    try:
        with engine.connect() as conn:
            # Get sentiment counts
            result = conn.execute(
                text("""
                    SELECT sentiment, COUNT(*) as count
                    FROM reviews 
                    WHERE post_id = :post_id 
                    GROUP BY sentiment
                """),
                {"post_id": post_id}
            )
            
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            for row in result:
                sentiment_counts[row[0]] = row[1]
            
            # Get total review count
            total_reviews = sum(sentiment_counts.values())
            
            # Get average sentiment score
            avg_result = conn.execute(
                text("""
                    SELECT AVG(sentiment_score) as avg_score
                    FROM reviews 
                    WHERE post_id = :post_id
                """),
                {"post_id": post_id}
            )
            avg_row = avg_result.fetchone()
            avg_score = avg_row[0] if avg_row and avg_row[0] is not None else 0
            
            return {
                'total_reviews': total_reviews,
                'positive_count': sentiment_counts['positive'],
                'negative_count': sentiment_counts['negative'],
                'neutral_count': sentiment_counts['neutral'],
                'average_sentiment_score': float(avg_score)
            }
    except SQLAlchemyError as e:
        print(f"Error getting analytics: {e}")
        return {
            'total_reviews': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'average_sentiment_score': 0.0
        }

def get_posts_by_author(author_name: str) -> List[Dict]:
    """Get all posts by a specific author"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, title, content, created_at,
                           (SELECT COUNT(*) FROM reviews WHERE post_id = posts.id) as review_count
                    FROM posts 
                    WHERE author_name = :author_name
                    ORDER BY created_at DESC
                """),
                {"author_name": author_name}
            )
            
            posts = []
            for row in result:
                posts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'created_at': row[3],
                    'review_count': row[4]
                
                })
            return posts
    except SQLAlchemyError as e:
        print(f"Error getting posts by author: {e}")
        return author_name

# ========== USER AUTHENTICATION FUNCTIONS ==========

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, email: str, date_of_birth: str, password: str, role: str) -> bool:
    """Create a new user account"""
    try:
        hashed_password = hash_password(password)
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, email, date_of_birth, password_hash, role) 
                    VALUES (:username, :email, :date_of_birth, :password_hash, :role)
                """),
                {
                    "username": username,
                    "email": email, 
                    "date_of_birth": date_of_birth,
                    "password_hash": hashed_password,
                    "role": role
                }
            )
            conn.commit()
            return True
    except SQLAlchemyError as e:
        print(f"Error creating user: {e}")
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user login and return user info if successful"""
    try:
        hashed_password = hash_password(password)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, email, date_of_birth, role, created_at
                    FROM users 
                    WHERE username = :username AND password_hash = :password_hash
                """),
                {"username": username, "password_hash": hashed_password}
            )
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'date_of_birth': row[3],
                    'role': row[4],
                    'created_at': row[5]
                }
            return None
    except SQLAlchemyError as e:
        print(f"Error authenticating user: {e}")
        return None

def check_username_exists(username: str) -> bool:
    """Check if username already exists"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM users WHERE username = :username"),
                {"username": username}
            )
            count = result.fetchone()[0]
            return count > 0
    except SQLAlchemyError as e:
        print(f"Error checking username: {e}")
        return False

def check_email_exists(email: str) -> bool:
    """Check if email already exists"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM users WHERE email = :email"),
                {"email": email}
            )
            count = result.fetchone()[0]
            return count > 0
    except SQLAlchemyError as e:
        print(f"Error checking email: {e}")
        return False

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user information by ID"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, email, date_of_birth, role, created_at
                    FROM users 
                    WHERE id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'date_of_birth': row[3],
                    'role': row[4],
                    'created_at': row[5]
                }
            return None
    except SQLAlchemyError as e:
        print(f"Error getting user: {e}")
        return None

def get_role_based_summary(role: str, content: str) -> str:
    """Generate role-based summary based on user's role"""
    role_prompts = {
        'student': "As a student, focus on learning opportunities, key concepts to understand, and how this relates to academic studies",
        'professional': "From a professional perspective, emphasize practical applications, industry relevance, and career implications",
        'entrepreneur': "From an entrepreneurial viewpoint, highlight business opportunities, market potential, and innovation aspects",
        'legal expert': "From a legal perspective, focus on compliance, regulations, legal implications, and risk assessment",
        'public': "For general public interest, emphasize societal impact, accessibility, and common concerns",
        'social activist': "From a social activism perspective, focus on social justice, community impact, and advocacy opportunities"
    }
    
    prompt = role_prompts.get(role, "Provide a general summary")
    
    # For now, we'll use the existing extractive summarizer with role context
    # In a real application, you might want to use a more sophisticated approach
    # from text_analyzer import TextAnalyzer
    analyzer = analyze(content)
    from text_analyzer import extractive_summarizer
    summary = extractive_summarizer.summarize(content, max_length=60)
    
    # Add role-specific context to the summary
    role_context = f"[{role.title()} Perspective] {summary}"
    return role_context