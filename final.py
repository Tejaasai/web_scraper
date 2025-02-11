import os
import time
import random
import hashlib
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from wordcloud import WordCloud
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------- Authentication System ----------------------
def authenticate_user(username, password):
    """Secure authentication system with hashed passwords"""
    authorized_users = {
        "admin": hashlib.sha256(os.getenv("ADMIN_PW", "admin@123").encode()).hexdigest(),
        "user": hashlib.sha256(os.getenv("USER_PW", "user@123").encode()).hexdigest()
    }
    return authorized_users.get(username) == hashlib.sha256(password.encode()).hexdigest()

# Passwords Are Never Stored in Plain Text: Even if someone hacks the system, they can’t see the original passwords—only the scrambled hashes

# When you enter your password, it gets converted into a scrambled format (called a "hash"). 
# This process is one-way — you can’t convert it back into the original password.
# For example:
# Password: admin@123
# Scrambled Code (Hash): ef92b778bafe771e89245b89ecbc3457b63e4e3

def login_form():
    """Display login form and handle authentication"""
    with st.form("Login"):
        st.subheader("🔒 Administrator Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    """Clear session state for logout"""
    st.session_state.clear()

# ---------------------- Enhanced Scraping Function ----------------------
def get_headers():
    """Generate random headers for each request"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]

    # Pretends to be different browsers (random user agents) 
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'en-US,en;q=0.9',
        #en-US: "I prefer U.S. English."
        #en;q=0.9: "If U.S. English isn’t available, I can also accept other types of English."
        'Referer': 'https://www.google.com/',
        #By setting the Referer as https://www.google.com/, you’re pretending to tell the website: "Hey, I clicked this link from Google search."
        'Accept-Encoding': 'gzip, deflate, br'
        #gzip, deflate, and br are types of compression formats.
        #You’re telling the website: "I can handle these formats, so send me the compressed version if you have it."
    }

def scrape_flipkart(urls, num_pages):
    """Robust scraping function with anti-blocking measures"""
    all_data = {
        'Name': [],
        'Price': [],
        'Rating': [],
        'Discount': []
    }

    for base_url in urls:
        parsed_url = urlparse(base_url)
        
        for page in range(1, num_pages + 1):
            try:
                # Add human-like delay
                time.sleep(random.uniform(2.5, 6.5))

                # Build URL with pagination
                query = f"{parsed_url.query}&page={page}" if parsed_url.query else f"page={page}"
                url = urlunparse(parsed_url._replace(query=query))

                # Make request through proxy
                api_key = os.getenv("SCRAPER_API_KEY")
                scraperapi_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"
                response = requests.get(scraperapi_url, headers=get_headers(), timeout=20)
                #It uses a pool of thousands of IP addresses from different regions, so websites can’t tell it’s scraping. 
                # Every request looks like it’s coming from a new visitor.

                # Check for blocking
                if response.status_code in [403, 429, 503]:
                    st.error("Access denied. Try reducing request frequency.")
                    break

                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

                # Updated 2024 CSS selectors
                main_container = soup.find('div', class_=['DOjaWF gdgoEp'])
                products = main_container.find_all('div', class_=['tUxRFH','slAVV4','_1sdMkc LFEi7Z']) if main_container else []  # Product container
                
                for product in products:
                    # Product Name
                    name = product.find(['a', 'div'], class_=['KzDlHZ', 'wjcEIp', 'WKTcLC', 'WKTcLC BwBZTg'])
                    all_data['Name'].append(name.text.strip() if name else "N/A")

                    # Price
                    price = product.find('div', class_=['Nx9bqj','Nx9bqj _4b5DiR'])
                    all_data['Price'].append(price.text.replace('₹', '').replace(',', '') if price else "0")

                    # Rating
                    rating = product.find('div', class_='XQDdHH')
                    all_data['Rating'].append(rating.text.strip() if rating else "0")

                    # Discount
                    discount = product.find('div',class_='UkUFwK')
                    all_data['Discount'].append(discount.text.split('%')[0] if discount else "0")

            except Exception as e:
                st.error(f"Error on page {page}: {str(e)}")
                continue

    return pd.DataFrame(all_data)

# ---------------------- Main Application ----------------------
def main():
    st.set_page_config(
        page_title="Flipkart Scraper Pro",
        page_icon="📈",
        layout="wide"
    )

    if not st.session_state.get('authenticated'):
        login_form()
        return

    # Sidebar Controls
    st.sidebar.button("🚪 Logout", on_click=logout)
    st.sidebar.header("Configuration ⚙️")
    
    # URL Input
    urls = st.sidebar.text_area(
        "🔍 Enter Flipkart Search URLs (one per line):",
        height=100,
        help="Example: https://www.flipkart.com/search?q=smartphones"
    ).splitlines()

    # Scraping Limits
    num_pages = st.sidebar.slider(
        "📄 Pages per URL (Max 3)", 
        min_value=1, 
        max_value=3, 
        value=1
    )

    # Main Interface of scraper which is displayed as top header of page
    st.markdown(f"""
    <div style='background:#f8f9fa;padding:20px;border-radius:10px;margin-bottom:20px'>
        <h1 style='color:#2874f0;text-align:center'>
            🛍️ Flipkart Smart Scraper
        </h1>
        <p style='text-align:center'>Logged in as: {st.session_state.username}</p>
    </div>
    """, unsafe_allow_html=True)

    # Scraping Trigger
    if st.sidebar.button("🚀 Start Scraping", type="primary"):
        if not any(urls):
            st.warning("Please enter valid URLs")
            return

        with st.spinner("🕸️ Scanning Flipkart for products..."):
            try:
                df = scrape_flipkart(
                    urls=[u.strip() for u in urls if u.strip()],
                    num_pages=num_pages
                )
                
                # Data Processing
                numeric_cols = ['Price', 'Rating', 'Discount']
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                df = df.reset_index(drop=True)
                
                st.session_state.df = df
                st.success(f"✅ Collected {len(df)} valid products")

            except Exception as e:
                st.error(f"Scraping failed: {str(e)}")

    # Data Display Section
    if 'df' in st.session_state:
        df = st.session_state.df

        # Key Metrics
        st.subheader("📊 Business Insights")
        cols = st.columns(5)
        metrics = [
            ("Total Products", len(df), ""),
            ("Avg Price", f"₹{df.Price.mean():.2f}", "#2874f0"),
            ("Avg Rating", f"{df.Rating.mean():.1f}/5", "orange"),
            ("Avg Discount", f"{df.Discount.mean():.1f}%", "green"),
            ("Missing Data", df.isna().sum().sum(), "red")
        ]
        
        for col, (title, value, color) in zip(cols, metrics):
            col.markdown(f"""
            <div style='padding:15px;background:{color + "10" if color else "#fff"};
                        border-radius:10px;border:1px solid {color + "30" if color else "#eee"}'>
                <h4 style='color:{color or "#333"};margin:0'>{title}</h4>
                <h2 style='color:{color or "#2874f0"};margin:0'>{value}</h2>
            </div>
            """, unsafe_allow_html=True)

        # Data Preview
        st.subheader("🔍 Raw Data Preview")
        st.dataframe(df, use_container_width=True)

        # Export
        st.subheader("📥 Export Results")
        csv = df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="flipkart_data.csv",
            mime="text/csv"
        )

        # Analytics Dashboard
        st.header("📈 Advanced Analytics")
        tabs = st.tabs(["Price Trends", "Rating Analysis", "Product Insights","Text Analytics"])
        #Price Distribution Analysis
        with tabs[0]:
            st.subheader("💰 Price Distribution Analysis")
            col1, col2 = st.columns(2)
            with col1:
                fig = plt.figure()
                sns.histplot(df['Price'].dropna(), bins=20, kde=True, color='skyblue')
                plt.xlabel("Price (₹)")
                st.pyplot(fig)
            with col2:
                fig = plt.figure()
                sns.boxplot(x=df['Price'].dropna(), color='lightgreen')
                plt.xlabel("Price (₹)")
                st.pyplot(fig)

            st.subheader("🎯 Discount Analysis")
            col3, col4 = st.columns(2)
            with col3:
                fig = plt.figure()
                sns.histplot(df['Discount'].dropna(), bins=20, kde=True, color='purple')
                plt.xlabel("Discount (%)")
                st.pyplot(fig)
            with col4:
                fig = plt.figure()
                sns.scatterplot(x=df['Discount'], y=df['Price'], alpha=0.6, color='green')
                plt.xlabel("Discount (%)")
                plt.ylabel("Price (₹)")
                st.pyplot(fig)
        #Rating Distribution
        
        with tabs[1]:
            st.subheader("⭐ Rating Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Rating Distribution**")
                fig, ax = plt.subplots()
                sns.countplot(x=df.Rating.round(1), ax=ax)
                st.pyplot(fig)
            
            with col2:
                st.write("**Price vs Rating**")
                fig, ax = plt.subplots()
                sns.scatterplot(x=df.Rating, y=df.Price, ax=ax)
                st.pyplot(fig)
        #Product Leaderboards
        with tabs[2]:
            st.subheader("🏆 Product Leaderboards")
            st.write("**Highest Prices**")
            st.dataframe(df.nlargest(10, 'Price')[['Name', 'Price']].style.format({'Price': '₹{:.2f}'}), height=400)
            
            st.write("**Top Ratings**")
            st.dataframe(df.nlargest(10, 'Rating')[['Name', 'Rating']], height=400)
            
            st.write("**Biggest Discounts**")
            st.dataframe(df.nlargest(10, 'Discount')[['Name', 'Discount']].style.format({'Discount': '{:.1f}%'}), height=400)
        #Product Name Analytics
        with tabs[3]:
            st.subheader("📝 Product Name Analytics")
            if not df['Name'].empty:
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(df['Name'].dropna()))
                fig = plt.figure()
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                st.pyplot(fig)
            else:
                st.warning("No product names available for text analysis")

if __name__ == "__main__":
    main()
