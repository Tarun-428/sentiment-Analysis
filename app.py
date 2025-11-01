import streamlit as st
import pandas as pd
from text_analyzer import (
    clean_text, tokenize, analyze, extractive_summarizer, 
    wcg, get_abstractive_summarizer
)
from database import (
    create_post, get_all_posts, get_post_by_id, create_review,
    get_reviews_by_post, get_post_analytics, get_posts_by_author,
    create_user, authenticate_user, check_username_exists, check_email_exists,
    get_role_based_summary
)
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Text Analysis Tool",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'

# Authentication flow
if not st.session_state.authenticated:
    st.title("🔐 Welcome to Text Analysis & Community Platform")
    st.markdown("Please sign up or log in to access the platform")
    
    # Authentication tabs
    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with auth_tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            
            if st.form_submit_button("🚀 Login"):
                if login_username and login_password:
                    user_info = authenticate_user(login_username, login_password)
                    if user_info:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.success(f"✅ Welcome back, {user_info['username']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please fill in all fields")
    
    with auth_tab2:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            signup_username = st.text_input("Username", placeholder="Choose a unique username")
            signup_email = st.text_input("Email", placeholder="your.email@example.com")
            signup_dob = st.date_input("Date of Birth", 
                                     min_value=datetime(1900, 1, 1),
                                     max_value=datetime(2010, 12, 31))
            signup_password = st.text_input("Password", type="password", 
                                          placeholder="Choose a strong password")
            signup_role = st.selectbox("Your Role", 
                                     ["student", "professional", "entrepreneur", 
                                      "legal expert", "public", "social activist"],
                                     help="Select your primary role - this will customize content for you")
            
            if st.form_submit_button("🎉 Create Account"):
                if signup_username and signup_email and signup_password and signup_role:
                    # Check if username or email already exists
                    if check_username_exists(signup_username):
                        st.error("❌ Username already exists. Please choose a different one.")
                    elif check_email_exists(signup_email):
                        st.error("❌ Email already registered. Please use a different email or login.")
                    else:
                        # Create the user
                        if create_user(signup_username, signup_email, str(signup_dob), 
                                     signup_password, signup_role):
                            st.success("✅ Account created successfully! Please login with your credentials.")
                            st.info("👈 Switch to the Login tab to access your account")
                        else:
                            st.error("❌ Failed to create account. Please try again.")
                else:
                    st.warning("⚠️ Please fill in all fields")
    
    # Stop here if not authenticated
    st.stop()

# If authenticated, show the main app
user_info = st.session_state.user_info

# Main title with user greeting
st.title("📝 Comprehensive Text Analysis & Community Platform")
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"Welcome back, **{user_info['username']}** ({user_info['role'].title()})!")
with col2:
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# Sidebar navigation
st.sidebar.header("🧭 Navigation")
app_mode = st.sidebar.radio(
    "Choose Mode:",
    ["Text Analysis", "Community Posts", "My Analytics"],
    help="Select what you want to do"
)

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")
if st.sidebar.button("🔄 Reset to Default"):
    st.session_state.clear()
    st.rerun()

# ========== TEXT ANALYSIS MODE ==========
if app_mode == "Text Analysis":
    # Text input section
    st.header("📄 Text Input")
    input_method = st.radio("Choose input method:", ["Type/Paste Text", "Upload File"])

    text_input = ""
    if input_method == "Type/Paste Text":
        text_input = st.text_area(
            "Enter your text here:",
            height=200,
            placeholder="Paste your text here for analysis..."
        )
        
        if st.button("📤 Send for Analysis"):
            st.session_state['submitted_text'] = text_input
            
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload a text file", type=['txt'])
        if uploaded_file is not None:
            text_input = str(uploaded_file.read(), "utf-8")
            st.text_area("Uploaded text:", value=text_input, height=200, disabled=True)

    # Only proceed if there's text input
    if text_input and text_input.strip():
        
        # Display original text info
        st.subheader("📊 Text Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Characters", len(text_input))
        with col2:
            st.metric("Words", len(text_input.split()))
        with col3:
            st.metric("Sentences", len(text_input.split('.')))
        with col4:
            st.metric("Paragraphs", len(text_input.split('\n\n')))

        # Text cleaning section
        st.subheader("🧹 Text Preprocessing")
        with st.expander("View cleaned text and tokens"):
            cleaned = clean_text(text_input)
            tokens = tokenize(text_input)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Cleaned Text:**")
                st.text_area("", value=cleaned, height=100, disabled=True)
            with col2:
                st.write("**Tokens:**")
                st.write(tokens[:50])  # Show first 50 tokens
                if len(tokens) > 50:
                    st.write(f"... and {len(tokens) - 50} more tokens")

        # Sentiment Analysis
        st.subheader("😊 Sentiment Analysis")
        sentiment_result = analyze(text_input)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            # Display sentiment with color coding
            sentiment = sentiment_result['sentiment']
            if sentiment == 'positive':
                st.success(f"**Sentiment: {sentiment.upper()}**")
            elif sentiment == 'negative':
                st.error(f"**Sentiment: {sentiment.upper()}**")
            else:
                st.info(f"**Sentiment: {sentiment.upper()}**")
            
            st.metric("Compound Score", f"{sentiment_result['compound_score']:.3f}")
        
        with col2:
            # Sentiment scores breakdown
            sentiment_df = pd.DataFrame({
                'Aspect': ['Positive', 'Negative', 'Neutral'],
                'Score': [sentiment_result['positive'], sentiment_result['negative'], sentiment_result['neutral']]
            })
            st.bar_chart(sentiment_df.set_index('Aspect'))

        # Summarization section
        st.subheader("📝 Text Summarization")
        
                # --- Summarization Type Option ---
        st.markdown("**Choose summary type:**")
        summary_type = st.radio(
            "Summary Type",
            ["Small", "Long", "Document"],
            horizontal=True,
            help="Small: ~1-2 sentences, Long: ~1 paragraph, Document: detailed summary"
        )

        # Set summary lengths based on type
        if summary_type == "Small":
            extractive_length = 60
            abstractive_min_length = 15
            abstractive_max_length = 40
        elif summary_type == "Long":
            extractive_length = 120
            abstractive_min_length = 30
            abstractive_max_length = 80
        else:  # Document
            extractive_length = 250
            abstractive_min_length = 60
            abstractive_max_length = 150
        
        # Sidebar controls for summarization
        st.sidebar.subheader("Summarization Settings")
        extractive_length = st.sidebar.slider("Extractive Summary Max Length (words)", 50, 300, 120)
        abstractive_min_length = st.sidebar.slider("Abstractive Summary Min Length", 10, 50, 20)
        abstractive_max_length = st.sidebar.slider("Abstractive Summary Max Length", 30, 150, 60)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🎯 Extractive Summary**")
            with st.spinner("Generating extractive summary..."):
                extractive_summary = extractive_summarizer.summarize(text_input, max_length=extractive_length)
            if extractive_summary:
                st.text_area("", value=extractive_summary, height=150, disabled=True)
            else:
                st.warning("Unable to generate extractive summary")
    
        with col2:
            st.write("**🤖 Abstractive Summary**")
            try:
                from text_analyzer import TRANSFORMERS_AVAILABLE
                if TRANSFORMERS_AVAILABLE:
                    if st.button("Generate Abstractive Summary", help="Click to generate AI-powered abstractive summary"):
                        with st.spinner("Loading AI model and generating summary..."):
                            try:
                                abstractive_summarizer = get_abstractive_summarizer()
                                summary_result = abstractive_summarizer(
                                    text_input, 
                                    max_length=abstractive_max_length, 
                                    min_length=abstractive_min_length, 
                                    do_sample=False
                                )
                                abstractive_summary = summary_result[0]['summary_text']
                                st.text_area("", value=abstractive_summary, height=150, disabled=True)
                            except Exception as e:
                                st.error(f"Error generating abstractive summary: {str(e)}")
                else:
                    st.warning("🔧 Abstractive summarization requires the 'transformers' package to be installed. The feature is currently unavailable, but extractive summarization is working.")
            except ImportError:
                st.warning("🔧 Abstractive summarization feature is currently unavailable.")

        # Role-based summary section
        st.subheader(f"🎯 {user_info['role'].title()} Perspective Summary")
        with st.spinner(f"Generating summary for {user_info['role']}..."):
            role_summary = get_role_based_summary(user_info['role'], text_input)
        
        st.info(role_summary)
        
        # Explanation of role-based analysis
        with st.expander(f"Why {user_info['role'].title()} perspective?"):
            role_explanations = {
                'student': "As a student, this analysis focuses on learning opportunities, key concepts to understand, and how this content relates to your academic studies.",
                'professional': "From a professional perspective, this analysis emphasizes practical applications, industry relevance, and career implications of the content.",
                'entrepreneur': "From an entrepreneurial viewpoint, this analysis highlights business opportunities, market potential, and innovation aspects within the content.",
                'legal expert': "From a legal perspective, this analysis focuses on compliance, regulations, legal implications, and risk assessment related to the content.",
                'public': "For general public interest, this analysis emphasizes societal impact, accessibility, and common concerns that affect everyone.",
                'social activist': "From a social activism perspective, this analysis focuses on social justice, community impact, and advocacy opportunities within the content."
            }
            st.write(role_explanations.get(user_info['role'], "This provides a customized analysis based on your selected role."))

        # Word Cloud section
        st.subheader("☁️ Word Cloud")
        
        # Sidebar controls for word cloud
        st.sidebar.subheader("Word Cloud Settings")
        wc_width = st.sidebar.slider("Width", 400, 1200, 800)
        wc_height = st.sidebar.slider("Height", 200, 800, 400)
        wc_max_words = st.sidebar.slider("Max Words", 50, 500, 200)
        wc_colormap = st.sidebar.selectbox(
            "Color Scheme",
            ['viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Blues', 'Reds', 'Greens']
        )
        
        if st.button("Generate Word Cloud"):
            with st.spinner("Generating word cloud..."):
                cleaned_for_wc = clean_text(text_input)
                if cleaned_for_wc:
                    wc_image = wcg.generate_image(
                        cleaned_for_wc,
                        width=wc_width,
                        height=wc_height,
                        max_words=wc_max_words,
                        colormap=wc_colormap
                    )
                    
                    if wc_image:
                        st.image(wc_image, caption="Generated Word Cloud")
                        
                        # Download button for word cloud
                        buf = BytesIO()
                        wc_image.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        
                        st.download_button(
                            label="📥 Download Word Cloud",
                            data=byte_im,
                            file_name="wordcloud.png",
                            mime="image/png"
                        )
                    else:
                        st.error("Unable to generate word cloud")
                else:
                    st.warning("No text available for word cloud generation after cleaning")

        # Word Frequency Analysis
        st.subheader("📈 Word Frequency Analysis")
        with st.expander("View top words"):
            cleaned_for_freq = clean_text(text_input)
            if cleaned_for_freq:
                frequencies = wcg.frequencies(cleaned_for_freq)
                if frequencies:
                    # Display top 20 words
                    freq_data = frequencies[:20]
                    freq_df = pd.DataFrame(data=freq_data, columns=['Word', 'Frequency'])
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.dataframe(freq_df, height=400)
                    with col2:
                        st.bar_chart(freq_df.set_index('Word'))
                else:
                    st.warning("No word frequencies to display")
            else:
                st.warning("No text available for frequency analysis after cleaning")

    else:
        # Welcome message when no text is provided
        st.info("👆 Please enter some text above to begin analysis")
        
        # Feature overview
        st.subheader("🚀 Features")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**😊 Sentiment Analysis**")
            st.write("- VADER sentiment scoring")
            st.write("- Positive/Negative/Neutral classification")
            st.write("- Visual sentiment indicators")
        
        with col2:
            st.write("**📝 Text Summarization**")
            st.write("- Extractive summarization")
            st.write("- AI-powered abstractive summarization")
            st.write("- Customizable summary length")
        
        with col3:
            st.write("**☁️ Word Cloud & Analysis**")
            st.write("- Interactive word cloud generation")
            st.write("- Word frequency analysis")
            st.write("- Customizable visualization options")

# ========== COMMUNITY POSTS MODE ==========
elif app_mode == "Community Posts":
    st.header("🌐 Community Posts")
    
    # Tabs for different actions
    tab1, tab2, tab3 = st.tabs(["📝 Create Post", "👀 View Posts", "💬 Review Posts"])
    
    with tab1:
        st.subheader("Create a New Post")
        st.info(f"📝 Posting as: **{user_info['username']}** ({user_info['role'].title()})")
        with st.form("create_post_form"):
            post_title = st.text_input("Title", placeholder="Enter a catchy title for your post")
            post_content = st.text_area(
                "Content", 
                height=300,
                placeholder="Write your post content here. This could be anything you want the community to review..."
            )
            
            if st.form_submit_button("📤 Post"):
                if post_title and post_content:
                    post_id = create_post(post_title, post_content, user_info['username'])
                    if post_id:
                        st.success(f"✅ Post created successfully! Post ID: {post_id}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create post. Please try again.")
                else:
                    st.warning("⚠️ Please fill in all fields")
    
    with tab2:
        st.subheader("All Community Posts")
        posts = get_all_posts()
        
        if posts:
            for post in posts:
                with st.expander(f"📄 {post['title']} by {post['author_name']} - {post['review_count']} reviews"):
                    st.write("**Content:**")
                    st.write(post['content'])
                    st.write(f"**Posted:** {post['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Quick analytics
                    if post['review_count'] > 0:
                        analytics = get_post_analytics(post['id'])
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Reviews", analytics['total_reviews'])
                        with col2:
                            st.metric("Positive", analytics['positive_count'])
                        with col3:
                            st.metric("Negative", analytics['negative_count'])
                        with col4:
                            st.metric("Neutral", analytics['neutral_count'])
        else:
            st.info("📭 No posts yet. Be the first to create one!")
    
    with tab3:
        st.subheader("Review Posts")
        posts = get_all_posts()
        
        if posts:
            post_options = {f"{post['title']} by {post['author_name']}": post['id'] for post in posts}
            selected_post_title = st.selectbox("Select a post to review:", list(post_options.keys()))
            
            if selected_post_title:
                selected_post_id = post_options[selected_post_title]
                selected_post = get_post_by_id(selected_post_id)
                
                if selected_post:
                    # Display the post
                    st.write("**Post Content:**")
                    st.info(selected_post['content'])
                    
                    # Review form
                    st.write("**Write Your Review:**")
                    st.info(f"📝 Reviewing as: **{user_info['username']}** ({user_info['role'].title()})")
                    with st.form("review_form"):
                        review_text = st.text_area(
                            "Review", 
                            height=150,
                            placeholder="Share your thoughts about this post..."
                        )
                        
                        if st.form_submit_button("📤 Submit Review"):
                            if review_text:
                                if create_review(selected_post_id, user_info['username'], review_text):
                                    st.success("✅ Review submitted successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to submit review. Please try again.")
                            else:
                                st.warning("⚠️ Please fill in your review")
                    
                    # Show existing reviews
                    st.write("**Existing Reviews:**")
                    reviews = get_reviews_by_post(selected_post_id)
                    
                    if reviews:
                        for review in reviews:
                            sentiment_color = "🟢" if review['sentiment'] == 'positive' else "🔴" if review['sentiment'] == 'negative' else "🟡"
                            with st.expander(f"{sentiment_color} Review by {review['reviewer_name']} - {review['sentiment'].upper()}"):
                                st.write(review['review_text'])
                                st.write(f"**Sentiment Score:** {review['sentiment_score']:.3f}")
                                st.write(f"**Posted:** {review['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.info("📝 No reviews yet. Be the first to review this post!")
        else:
            st.info("📭 No posts available to review yet.")

# ========== MY ANALYTICS MODE ==========
elif app_mode == "My Analytics":
    st.header("📊 My Analytics Dashboard")
    st.info(f"📊 Showing analytics for: **{user_info['username']}** ({user_info['role'].title()})")
    
    user_posts = get_posts_by_author(user_info['username'])
    
    if user_posts:
        st.subheader(f"📝 Your Posts ({len(user_posts)} total)")
        
        # Overall statistics
        total_reviews = sum(post['review_count'] for post in user_posts)
        st.metric("Total Reviews Received", total_reviews)
        
        # Individual post analytics
        for post in user_posts:
            with st.expander(f"📄 {post['title']} - {post['review_count']} reviews"):
                    st.write("**Content Preview:**")
                    preview = post['content'][:200] + "..." if len(post['content']) > 200 else post['content']
                    st.write(preview)
                    
                    if post['review_count'] > 0:
                        # Get detailed analytics
                        analytics = get_post_analytics(post['id'])
                        
                        # Display metrics
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total Reviews", analytics['total_reviews'])
                        with col2:
                            st.metric("Positive", analytics['positive_count'], 
                                    f"{(analytics['positive_count']/analytics['total_reviews']*100):.1f}%")
                        with col3:
                            st.metric("Negative", analytics['negative_count'], 
                                    f"{(analytics['negative_count']/analytics['total_reviews']*100):.1f}%")
                        with col4:
                            st.metric("Neutral", analytics['neutral_count'], 
                                    f"{(analytics['neutral_count']/analytics['total_reviews']*100):.1f}%")
                        with col5:
                            st.metric("Avg Score", f"{analytics['average_sentiment_score']:.3f}")
                        
                        # Sentiment breakdown chart
                        sentiment_data = pd.DataFrame({
                            'Sentiment': ['Positive', 'Negative', 'Neutral'],
                            'Count': [analytics['positive_count'], analytics['negative_count'], analytics['neutral_count']]
                        })
                        st.bar_chart(sentiment_data.set_index('Sentiment'))
                        
                        # View reviews by sentiment
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button(f"View Positive ({analytics['positive_count']})", key=f"pos_{post['id']}"):
                                positive_reviews = get_reviews_by_post(post['id'], 'positive')
                                if positive_reviews:
                                    st.write("**Positive Reviews:**")
                                    for review in positive_reviews:
                                        with st.container():
                                            st.success(f"**{review['reviewer_name']}**: {review['review_text']}")
                                            st.write(f"Score: {review['sentiment_score']:.3f}")
                        
                        with col2:
                            if st.button(f"View Negative ({analytics['negative_count']})", key=f"neg_{post['id']}"):
                                negative_reviews = get_reviews_by_post(post['id'], 'negative')
                                if negative_reviews:
                                    st.write("**Negative Reviews:**")
                                    for review in negative_reviews:
                                        with st.container():
                                            st.error(f"**{review['reviewer_name']}**: {review['review_text']}")
                                            st.write(f"Score: {review['sentiment_score']:.3f}")
                        
                        with col3:
                            if st.button(f"View Neutral ({analytics['neutral_count']})", key=f"neu_{post['id']}"):
                                neutral_reviews = get_reviews_by_post(post['id'], 'neutral')
                                if neutral_reviews:
                                    st.write("**Neutral Reviews:**")
                                    for review in neutral_reviews:
                                        with st.container():
                                            st.info(f"**{review['reviewer_name']}**: {review['review_text']}")
                                            st.write(f"Score: {review['sentiment_score']:.3f}")
                        
                        # Overall summary using text analysis
                        if st.button("📋 Generate Overall Summary", key=f"summary_{post['id']}"):
                            all_reviews = get_reviews_by_post(post['id'])
                            review_texts = [review['review_text'] for review in all_reviews]
                            combined_text = " ".join(review_texts)
                            
                            if combined_text:
                                st.write("**Overall Review Summary:**")
                                summary = extractive_summarizer.summarize(combined_text, max_length=100)
                                st.info(summary)
                    else:
                        st.info("No reviews yet for this post.")
        # else:
        #     st.info(f"No posts found for User. Create some posts first!")
    else:
        st.info(f"No posts found for user {user_info['username']}. Create some posts first!")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit • Powered by NLTK, Transformers, WordCloud, and PostgreSQL")
