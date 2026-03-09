# ==========================================
# ACCESSORIZE WITH YVON - PRODUCTION E-COMMERCE
# ==========================================

import streamlit as st
import gspread
import pandas as pd
import os
import json
import random
import requests
import smtplib
import threading
import time
import hashlib
import secrets
from datetime import datetime
from functools import lru_cache
from oauth2client.service_account import ServiceAccountCredentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cloudinary
import cloudinary.uploader

# Must be first Streamlit command
st.set_page_config(
    page_title="Accessorize with Yvon | Elegant Jewelry",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Hide all Streamlit default UI elements
HIDE_STREAMLIT_STYLE = """
<style>
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
.stDeployButton {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
.stSpinner > div > div {border-top-color: #d97706 !important;}
</style>
"""
st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# ==========================================
# CONFIGURATION
# ==========================================

# Load secrets safely with fallbacks
def get_secret(key_path, default=None):
    """Safely get nested secrets"""
    try:
        keys = key_path.split('.')
        value = st.secrets
        for k in keys:
            value = value[k]
        return value
    except Exception:
        return default

# Store Identity
STORE_NAME = "Accessorize with Yvon & Knottycrafts Shop"
STORE_TAGLINE = "Curated jewelry, beauty & handmade treasures"
LOGO_TEXT = "AYK"
LOGO_SHAPE = "circle"

# Colors
BACKGROUND_COLOR = "#fef3f2"
CARD_BACKGROUND = "#ffffff"
SURFACE_COLOR = "#fff5f5"
PRIMARY_COLOR = "#d97706"
PRIMARY_LIGHT = "#f59e0b"
PRIMARY_DARK = "#b45309"
ACCENT_COLOR = "#ec4899"
TEXT_PRIMARY = "#78350f"
TEXT_SECONDARY = "#92400e"
TEXT_MUTED = "#a16207"
PRICE_COLOR = "#dc2626"
SUCCESS_COLOR = "#10b981"
ERROR_COLOR = "#ef4444"
BORDER_COLOR = "#fed7aa"
SHADOW_COLOR = "rgba(217, 119, 6, 0.15)"

# Functional
CURRENCY_SYMBOL = "GHS"
REFERENCE_PREFIX = "AYK"
REFERENCE_LENGTH = 4
MIN_ORDER_QUANTITY = 1
MAX_ORDER_QUANTITY = 50
MAX_PRODUCT_IMAGES = 3
CACHE_TTL_PRODUCTS = 300
CACHE_TTL_ORDERS = 120

# Sheets
SHEET_NAME = "accessorize_with_yvon"
PRODUCTS_WORKSHEET = "products"
ORDERS_WORKSHEET = "orders"

# Status
STATUS_IN_STOCK = "In Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"
STATUS_PENDING = "Pending"
STATUS_APPROVED = "Approved"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"

# Text
TEXT_ADD_TO_CART = "Order Now"
TEXT_PLACE_ORDER = "Place Order"
TEXT_OUT_OF_STOCK = "Sold Out"
TEXT_ADMIN_LOGIN = "Admin Login"
TEXT_FEATURED_PRODUCTS = "Our Collection"
TEXT_CHECKOUT = "Complete Your Order"
TEXT_ADMIN_DASHBOARD = "Admin Dashboard"

# Social
FOOTER_LINKS = [
    {"icon": "📞", "text": "0545651573", "url": "tel:0545651573"},
    {"icon": "📱", "text": "0507262613", "url": "tel:0507262613"},
    {"icon": "👻", "text": "@yvonisdark", "url": "https://snapchat.com/add/yvonisdark"},
    {"icon": "🎵", "text": "@knottycrafts", "url": "https://www.tiktok.com/@knottycrafts"},
]

COPYRIGHT_TEXT = f"© 2026 {STORE_NAME} • All Rights Reserved"

TELEGRAM_TEMPLATE = """
🛍️ <b>NEW ORDER - {STORE_NAME}</b>

📦 <b>Product:</b> {product_name}
🎯 <b>Variant:</b> {variant}
👤 <b>Customer:</b> {customer_name}
📱 <b>Phone:</b> {phone}
📍 <b>Location:</b> {location}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Total:</b> {currency} {total}
🔖 <b>Reference:</b> {reference}
⏰ <b>Time:</b> {timestamp}
"""

# ==========================================
# SECURITY & SESSION MANAGEMENT
# ==========================================

def generate_csrf_token():
    """Generate secure CSRF token"""
    if 'csrf_token' not in st.session_state:
        st.session_state.csrf_token = secrets.token_urlsafe(32)
    return st.session_state.csrf_token

def verify_csrf_token(token):
    """Verify CSRF token"""
    return token == st.session_state.get('csrf_token')

def hash_password(password, salt=None):
    """Secure password hashing"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + pwdhash.hex()

def verify_password(stored_password, provided_password):
    """Verify password against hash"""
    salt = stored_password[:32]
    return hash_password(provided_password, salt) == stored_password

# Initialize session state securely
def init_session():
    """Initialize all session state variables"""
    defaults = {
        'admin_logged': False,
        'admin_user': None,
        'login_attempts': 0,
        'last_attempt': 0,
        'selected_product': None,
        'carousel_indices': {},
        'active_category': 'All',
        'admin_page': 'dashboard',
        'csrf_token': secrets.token_urlsafe(32),
        'cart': [],
        'viewed_products': set()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# Rate limiting
def check_rate_limit():
    """Prevent brute force attacks"""
    now = time.time()
    if st.session_state.login_attempts >= 5:
        if now - st.session_state.last_attempt < 300:  # 5 min lockout
            remaining = int(300 - (now - st.session_state.last_attempt))
            st.error(f"⏱️ Too many attempts. Try again in {remaining} seconds.")
            return False
        else:
            st.session_state.login_attempts = 0
    return True

# ==========================================
# CLOUDINARY CONFIG
# ==========================================

try:
    cloudinary.config(
        cloud_name=get_secret("cloudinary.cloud_name"),
        api_key=get_secret("cloudinary.api_key"),
        api_secret=get_secret("cloudinary.api_secret"),
        secure=True
    )
except Exception as e:
    st.error("⚠️ Cloudinary configuration failed")

# ==========================================
# OPTIMIZED GOOGLE SHEETS CONNECTION
# ==========================================

@st.cache_resource(ttl=3600, show_spinner=False)
def get_sheets_client():
    """Get cached Google Sheets client"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = get_secret("gcp_service_account")
        if not creds_dict:
            raise ValueError("GCP credentials not found")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Sheets connection failed: {str(e)}")
        return None

@st.cache_data(ttl=CACHE_TTL_PRODUCTS, show_spinner=False)
def load_products():
    """Load products with aggressive caching"""
    try:
        client = get_sheets_client()
        if not client:
            return pd.DataFrame()
        sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
        records = sheet.get_all_records()
        for i, r in enumerate(records, start=2):
            r["_row"] = i
        return pd.DataFrame(records)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL_ORDERS, show_spinner=False)
def load_orders():
    """Load orders with caching"""
    try:
        client = get_sheets_client()
        if not client:
            return pd.DataFrame()
        sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
        records = sheet.get_all_records()
        for i, r in enumerate(records, start=2):
            r["_row"] = i
        return pd.DataFrame(records)
    except:
        return pd.DataFrame()

# ==========================================
# CORE FUNCTIONS
# ==========================================

def generate_reference(product_name, location):
    """Generate unique order reference"""
    product_code = product_name[:3].upper() if len(product_name) >= 3 else product_name.upper()
    location_code = location[:3].upper() if len(location) >= 3 else location.upper()
    random_num = random.randint(10 ** (REFERENCE_LENGTH - 1), (10 ** REFERENCE_LENGTH) - 1)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{random_num}"

def upload_to_cloudinary(file, filename):
    """Upload image to Cloudinary"""
    try:
        file.seek(0)
        clean_filename = ''.join(c for c in filename.replace(' ', '_') if c.isalnum() or c in '_-')
        public_id = f"ayv/{clean_filename}_{int(time.time())}"
        result = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True, resource_type="image")
        return result.get('secure_url')
    except Exception as e:
        raise RuntimeError(f"Upload failed: {e}")

def delete_from_cloudinary(image_url):
    """Delete image from Cloudinary"""
    try:
        if 'cloudinary.com' in image_url:
            parts = image_url.split('/')
            upload_idx = parts.index('upload')
            public_id = '/'.join(parts[upload_idx + 2:]).rsplit('.', 1)[0]
            cloudinary.uploader.destroy(public_id)
            return True
    except:
        return False

def send_notifications_async(product_name, variant, customer_name, phone, location, qty, total, reference, timestamp):
    """Send notifications in background thread"""
    def _send():
        # Telegram
        try:
            token = get_secret("telegram.bot_token")
            chat_id = get_secret("telegram.chat_id")
            if token and chat_id:
                msg = TELEGRAM_TEMPLATE.format(
                    STORE_NAME=STORE_NAME, product_name=product_name, variant=variant,
                    customer_name=customer_name, phone=phone, location=location,
                    quantity=qty, currency=CURRENCY_SYMBOL, total=total,
                    reference=reference, timestamp=timestamp
                )
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                    timeout=5
                )
        except:
            pass
        
        # Email
        try:
            admin_email = get_secret("email.admin_email")
            password = get_secret("email.app_password")
            if admin_email and password:
                msg = MIMEMultipart('alternative')
                msg['From'] = admin_email
                msg['To'] = admin_email
                msg['Subject'] = f"New Order: {reference}"
                html = f"""
                <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
                <div style='background:linear-gradient(135deg,{PRIMARY_COLOR},{PRIMARY_LIGHT});color:white;padding:30px;text-align:center;border-radius:15px 15px 0 0;'>
                    <h1>🛍️ New Order!</h1>
                </div>
                <div style='background:#fff5f5;padding:30px;border:1px solid {BORDER_COLOR};'>
                    <p><strong>Product:</strong> {product_name}</p>
                    <p><strong>Customer:</strong> {customer_name}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Total:</strong> {CURRENCY_SYMBOL}{total}</p>
                    <p><strong>Reference:</strong> {reference}</p>
                </div>
                </body></html>
                """
                msg.attach(MIMEText(html, 'html'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(admin_email, password)
                server.send_message(msg)
                server.quit()
        except:
            pass
    
    threading.Thread(target=_send, daemon=True).start()

# ==========================================
# PROFESSIONAL CSS
# ==========================================

_logo_radius = "50%" if LOGO_SHAPE == "circle" else "16px"

ALL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

#MainMenu, footer, header, .stDeployButton, [data-testid="stToolbar"] {{ 
    display: none !important; visibility: hidden !important; 
}}

.stAppViewBlockContainer, .block-container {{ 
    padding: 0 !important; max-width: 100% !important; 
}}

body, .stApp {{ 
    background: {BACKGROUND_COLOR} !important; 
    font-family: 'Inter', sans-serif; 
    overflow-x: hidden;
    color: {TEXT_PRIMARY};
}}

/* Background Elements */
.gold-particles {{
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: 0; overflow: hidden;
}}

.gold-particle {{
    position: absolute; width: 6px; height: 6px;
    background: radial-gradient(circle, {PRIMARY_LIGHT}, {PRIMARY_COLOR});
    border-radius: 50%; animation: floatParticle linear infinite; opacity: 0;
}}

.gold-particle:nth-child(1) {{ left: 10%; animation-duration: 8s; animation-delay: 0s; }}
.gold-particle:nth-child(2) {{ left: 20%; animation-duration: 12s; animation-delay: 2s; }}
.gold-particle:nth-child(3) {{ left: 30%; animation-duration: 9s; animation-delay: 4s; }}
.gold-particle:nth-child(4) {{ left: 40%; animation-duration: 15s; animation-delay: 1s; }}
.gold-particle:nth-child(5) {{ left: 50%; animation-duration: 10s; animation-delay: 3s; }}
.gold-particle:nth-child(6) {{ left: 60%; animation-duration: 13s; animation-delay: 5s; }}
.gold-particle:nth-child(7) {{ left: 70%; animation-duration: 11s; animation-delay: 0.5s; }}
.gold-particle:nth-child(8) {{ left: 80%; animation-duration: 14s; animation-delay: 2.5s; }}
.gold-particle:nth-child(9) {{ left: 90%; animation-duration: 8s; animation-delay: 1.5s; }}
.gold-particle:nth-child(10) {{ left: 25%; animation-duration: 16s; animation-delay: 3.5s; }}

@keyframes floatParticle {{
    0% {{ transform: translateY(100vh) rotate(0deg); opacity: 0; }}
    10% {{ opacity: 0.8; }} 90% {{ opacity: 0.6; }}
    100% {{ transform: translateY(-100px) rotate(720deg); opacity: 0; }}
}}

.pink-orb {{
    position: fixed; border-radius: 50%; filter: blur(80px);
    pointer-events: none; z-index: 0; animation: orbPulse 6s ease-in-out infinite;
}}

.pink-orb:nth-child(1) {{ width: 400px; height: 400px; background: radial-gradient(circle, rgba(236,72,153,0.15), transparent); top: -100px; right: -100px; }}
.pink-orb:nth-child(2) {{ width: 300px; height: 300px; background: radial-gradient(circle, rgba(217,119,6,0.1), transparent); bottom: 200px; left: -80px; animation-delay: 3s; }}
.pink-orb:nth-child(3) {{ width: 250px; height: 250px; background: radial-gradient(circle, rgba(245,158,11,0.1), transparent); top: 50%; left: 50%; animation-delay: 1.5s; }}

@keyframes orbPulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.8; }}
    50% {{ transform: scale(1.2); opacity: 1; }}
}}

/* Hero */
.hero-section {{
    position: relative;
    background: linear-gradient(135deg, {PRIMARY_DARK} 0%, {PRIMARY_COLOR} 40%, {ACCENT_COLOR} 100%);
    padding: 3rem 1.5rem 4rem; text-align: center; overflow: hidden; z-index: 1;
}}

.hero-shimmer {{
    position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    animation: heroShimmer 4s ease-in-out infinite;
}}

@keyframes heroShimmer {{ 0% {{ left: -100%; }} 100% {{ left: 200%; }} }}

.hero-content {{
    position: relative; z-index: 2; display: flex; flex-direction: column;
    align-items: center; gap: 1.5rem;
}}

@media (min-width: 768px) {{
    .hero-content {{ flex-direction: row; justify-content: center; gap: 2.5rem; }}
    .hero-section {{ padding: 4rem 3rem 5rem; }}
}}

.hero-logo {{
    width: 90px; height: 90px; background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px); border-radius: {_logo_radius};
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; font-weight: 700; color: white;
    border: 3px solid rgba(255,255,255,0.4);
    box-shadow: 0 10px 40px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.3);
    animation: logoFloat 4s ease-in-out infinite; flex-shrink: 0;
    font-family: 'Playfair Display', serif;
}}

@media (min-width: 768px) {{ .hero-logo {{ width: 110px; height: 110px; font-size: 2.5rem; }} }}

@keyframes logoFloat {{
    0%, 100% {{ transform: translateY(0) rotate(-2deg); }}
    50% {{ transform: translateY(-10px) rotate(2deg); }}
}}

.hero-text {{ color: white; text-align: center; }}
@media (min-width: 768px) {{ .hero-text {{ text-align: left; }} }}

.hero-title {{
    font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem;
    font-family: 'Playfair Display', serif;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2); line-height: 1.2;
}}

@media (min-width: 768px) {{ .hero-title {{ font-size: 2.8rem; }} }}

.hero-tagline {{ font-size: 1rem; opacity: 0.9; margin-bottom: 1rem; font-weight: 500; }}
@media (min-width: 768px) {{ .hero-tagline {{ font-size: 1.2rem; }} }}

.hero-badge {{
    display: inline-block; background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.4);
    padding: 0.5rem 1.5rem; border-radius: 50px; font-size: 0.9rem;
    font-weight: 600; letter-spacing: 1px;
    animation: badgePulse 2s ease-in-out infinite;
}}

@keyframes badgePulse {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(255,255,255,0.3); }}
    50% {{ box-shadow: 0 0 0 8px rgba(255,255,255,0); }}
}}

/* Main Content */
.main-content {{ max-width: 1400px; margin: 0 auto; padding: 0 1rem; position: relative; z-index: 1; }}
@media (min-width: 768px) {{ .main-content {{ padding: 0 2rem; }} }}

/* Section Title */
.section-title {{
    font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 600;
    color: {TEXT_PRIMARY}; text-align: center; margin: 3rem 0 2rem 0;
    position: relative; letter-spacing: -0.5px;
}}

.section-title::after {{
    content: ''; display: block; width: 60px; height: 3px;
    background: linear-gradient(90deg, {PRIMARY_COLOR}, {PRIMARY_LIGHT});
    margin: 1rem auto 0; border-radius: 2px;
}}

@media (min-width: 768px) {{ .section-title {{ font-size: 2.5rem; margin: 4rem 0 3rem 0; }} }}

/* Product Grid */
.product-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; padding: 0 0 3rem 0;
}}

@media (min-width: 640px) {{ .product-grid {{ gap: 2rem; }} }}
@media (min-width: 768px) {{ .product-grid {{ grid-template-columns: repeat(3, 1fr); gap: 2.5rem; }} }}
@media (min-width: 1200px) {{ .product-grid {{ grid-template-columns: repeat(4, 1fr); gap: 3rem; }} }}

/* Product Card */
.product-card {{
    background: {CARD_BACKGROUND}; border-radius: 20px; overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04); transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
    border: 1px solid {BORDER_COLOR}; position: relative;
    display: flex; flex-direction: column; height: 100%;
    animation: fadeInUp 0.6s ease forwards; opacity: 0;
}}

@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.product-card:hover {{
    transform: translateY(-8px); box-shadow: 0 20px 40px rgba(217, 119, 6, 0.12);
    border-color: rgba(217, 119, 6, 0.3);
}}

.product-image-wrapper {{
    position: relative; width: 100%; aspect-ratio: 1 / 1;
    background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
    overflow: hidden; border-bottom: 1px solid {BORDER_COLOR};
}}

.product-image-container {{
    width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
    padding: 1.5rem; transition: transform 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}}

.product-card:hover .product-image-container {{ transform: scale(1.05); }}

.product-image {{
    max-width: 100%; max-height: 100%; width: auto; height: auto;
    object-fit: contain; border-radius: 12px;
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.08));
    transition: all 0.5s ease;
}}

.product-card:hover .product-image {{
    filter: drop-shadow(0 12px 24px rgba(0,0,0,0.12));
}}

.stock-badge {{
    position: absolute; top: 12px; left: 12px;
    padding: 0.4rem 0.9rem; border-radius: 20px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; z-index: 10; backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
}}

.badge-in-stock {{ background: rgba(16, 185, 129, 0.9); color: white; }}
.badge-out-stock {{ background: rgba(239, 68, 68, 0.9); color: white; }}

.carousel-dots {{
    position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
    display: flex; gap: 6px; z-index: 10; background: rgba(255,255,255,0.9);
    padding: 6px 10px; border-radius: 20px; backdrop-filter: blur(4px);
    border: 1px solid rgba(0,0,0,0.05);
}}

.carousel-dot {{
    width: 6px; height: 6px; border-radius: 50%;
    background: rgba(0,0,0,0.2); border: none;
    transition: all 0.3s ease;
}}

.carousel-dot.active {{ background: {PRIMARY_COLOR}; width: 18px; border-radius: 3px; }}

.product-content {{
    padding: 1.25rem; display: flex; flex-direction: column;
    flex-grow: 1; gap: 0.4rem;
}}

@media (min-width: 768px) {{ .product-content {{ padding: 1.5rem; }} }}

.product-name {{
    font-family: 'Playfair Display', serif; font-size: 1.05rem;
    font-weight: 600; color: {TEXT_PRIMARY}; line-height: 1.3;
    margin-bottom: 0.3rem; display: -webkit-box;
    -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    overflow: hidden; min-height: 2.6rem;
}}

@media (min-width: 768px) {{ .product-name {{ font-size: 1.15rem; }} }}

.product-description {{
    font-size: 0.8rem; color: {TEXT_SECONDARY}; line-height: 1.5;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
    margin-bottom: 0.5rem; flex-grow: 1;
}}

.product-meta {{
    display: flex; justify-content: space-between; align-items: center;
    margin-top: auto; padding-top: 0.75rem;
    border-top: 1px solid {BORDER_COLOR};
}}

.product-price {{
    font-size: 1.15rem; color: {PRICE_COLOR}; font-weight: 700;
    display: flex; align-items: baseline; gap: 0.2rem;
}}

@media (min-width: 768px) {{ .product-price {{ font-size: 1.25rem; }} }}

.price-currency {{ font-size: 0.8rem; color: {TEXT_MUTED}; font-weight: 500; }}

.variant-badge {{
    font-size: 0.7rem; color: {TEXT_SECONDARY}; background: {SURFACE_COLOR};
    padding: 0.25rem 0.7rem; border-radius: 12px;
    font-weight: 500; border: 1px solid {BORDER_COLOR};
}}

/* Buttons */
.stButton > button {{
    background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_DARK} 100%) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 0.875rem 1.5rem !important; font-weight: 600 !important;
    font-size: 0.9rem !important; transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25) !important;
    width: 100% !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(217, 119, 6, 0.35) !important;
}}

.stButton > button:disabled {{
    background: #e5e7eb !important; color: #9ca3af !important;
    box-shadow: none !important; cursor: not-allowed !important;
}}

/* Admin */
.admin-card {{
    background: rgba(255,255,255,0.95); backdrop-filter: blur(20px);
    border-radius: 24px; padding: 2rem; margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    border: 1px solid rgba(255,255,255,0.6);
}}

.stat-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;
}}

@media (min-width: 768px) {{ .stat-grid {{ gap: 1.5rem; }} }}

.stat-box {{
    background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
    color: white; padding: 1.5rem 1rem; border-radius: 20px;
    text-align: center; box-shadow: 0 15px 35px {SHADOW_COLOR};
    transition: all 0.4s ease; position: relative; overflow: hidden;
}}

.stat-box:hover {{ transform: translateY(-5px) scale(1.02); }}

.stat-number {{
    font-size: 1.8rem; font-weight: 700; margin-bottom: 0.3rem;
    line-height: 1; font-family: 'Playfair Display', serif;
}}

@media (min-width: 768px) {{ .stat-number {{ font-size: 2.2rem; }} }}

.stat-label {{
    font-size: 0.75rem; opacity: 0.95; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
}}

/* Order Management */
.order-card {{
    background: white; border-radius: 16px; padding: 1.5rem;
    margin-bottom: 1rem; border: 1px solid {BORDER_COLOR};
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}}

.order-card:hover {{
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}}

.status-badge {{
    display: inline-block; padding: 0.3rem 0.8rem;
    border-radius: 20px; font-size: 0.75rem;
    font-weight: 600; text-transform: uppercase;
}}

.status-pending {{ background: #fef3c7; color: #92400e; }}
.status-approved {{ background: #d1fae5; color: #065f46; }}
.status-completed {{ background: #dbeafe; color: #1e40af; }}
.status-cancelled {{ background: #fee2e2; color: #991b1b; }}

/* Forms */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {{
    background-color: {CARD_BACKGROUND} !important; color: {TEXT_PRIMARY} !important;
    border: 2px solid {BORDER_COLOR} !important; border-radius: 16px !important;
    padding: 1rem 1.2rem !important; font-size: 1rem !important;
    transition: all 0.4s ease !important;
}}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {{
    border-color: {PRIMARY_COLOR} !important;
    box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.15) !important;
    outline: none !important;
}}

/* Checkout */
.order-container {{
    background: rgba(255,255,255,0.95); backdrop-filter: blur(20px);
    border-radius: 32px; padding: 2rem 1.5rem; margin: 2rem auto;
    max-width: 800px; box-shadow: 0 20px 60px rgba(0,0,0,0.1);
    border: 2px solid {BORDER_COLOR};
}}

.order-summary {{
    background: linear-gradient(135deg, {SURFACE_COLOR} 0%, {BACKGROUND_COLOR} 100%);
    border: 2px solid {BORDER_COLOR}; border-radius: 20px;
    padding: 1.5rem; margin: 1.5rem 0;
}}

.order-summary-title {{
    font-family: 'Playfair Display', serif; font-size: 1.1rem;
    font-weight: 600; color: {TEXT_PRIMARY};
    margin-bottom: 1rem; padding-bottom: 0.8rem;
    border-bottom: 2px solid {BORDER_COLOR};
}}

.order-summary-total {{
    font-size: 1.5rem; font-weight: 700; color: {PRICE_COLOR};
    margin-top: 1rem; padding-top: 1rem;
    border-top: 2px solid {BORDER_COLOR};
    font-family: 'Playfair Display', serif;
}}

/* Success */
.success-message {{
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border: 3px solid {SUCCESS_COLOR}; color: #065f46;
    padding: 2.5rem 2rem; border-radius: 24px;
    margin: 2rem 0; text-align: center;
    box-shadow: 0 20px 50px rgba(16,185,129,0.2);
    animation: successPop 0.6s ease forwards;
}}

@keyframes successPop {{
    0% {{ transform: scale(0.8); opacity: 0; }}
    100% {{ transform: scale(1); opacity: 1; }}
}}

/* Footer */
.footer {{
    background: linear-gradient(135deg, {TEXT_SECONDARY} 0%, {PRIMARY_COLOR} 100%);
    color: white; padding: 3rem 2rem;
    border-radius: 40px 40px 0 0; margin-top: 4rem;
    text-align: center; border-top: 4px solid {BORDER_COLOR};
}}

.footer-title {{
    font-family: 'Playfair Display', serif; font-size: 1.5rem;
    font-weight: 600; margin-bottom: 1.5rem;
}}

.footer-links {{
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 1.5rem; margin-bottom: 1.5rem;
}}

.footer-link {{
    color: rgba(255,255,255,0.9); text-decoration: none;
    font-size: 0.95rem; font-weight: 500;
    transition: all 0.3s ease;
    display: flex; align-items: center; gap: 0.5rem;
}}

.footer-link:hover {{ color: {PRIMARY_LIGHT}; transform: translateY(-3px); }}

/* Admin Login */
.admin-login-box {{
    max-width: 450px; margin: 3rem auto;
    background: rgba(255,255,255,0.95); backdrop-filter: blur(20px);
    border-radius: 32px; padding: 2.5rem;
    box-shadow: 0 25px 80px rgba(0,0,0,0.12);
    border: 2px solid {BORDER_COLOR};
}}

/* Empty State */
.empty-state {{ text-align: center; padding: 4rem 2rem; color: {TEXT_SECONDARY}; }}
.empty-state-icon {{ font-size: 4rem; margin-bottom: 1rem; opacity: 0.5; }}

/* Responsive */
@media (max-width: 640px) {{
    .section-title {{ font-size: 1.6rem; }}
    .hero-title {{ font-size: 1.5rem; }}
    .stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .product-grid {{ grid-template-columns: repeat(2, 1fr); gap: 1rem; }}
}}
</style>
"""

st.markdown(ALL_CSS, unsafe_allow_html=True)

# ==========================================
# UI RENDERING
# ==========================================

# Background Effects
st.markdown("""
    <div class="gold-particles">
        <div class="gold-particle"></div><div class="gold-particle"></div>
        <div class="gold-particle"></div><div class="gold-particle"></div>
        <div class="gold-particle"></div><div class="gold-particle"></div>
        <div class="gold-particle"></div><div class="gold-particle"></div>
        <div class="gold-particle"></div><div class="gold-particle"></div>
    </div>
    <div class="pink-orb"></div>
    <div class="pink-orb"></div>
    <div class="pink-orb"></div>
""", unsafe_allow_html=True)

# Hero
st.markdown(f"""
    <div class="hero-section">
        <div class="hero-shimmer"></div>
        <div class="hero-content">
            <div class="hero-logo">{LOGO_TEXT}</div>
            <div class="hero-text">
                <div class="hero-title">{STORE_NAME}</div>
                <div class="hero-tagline">{STORE_TAGLINE}</div>
                <div class="hero-badge">💎 Premium Quality</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# ==========================================
# ADMIN ACCESS
# ==========================================

# Admin toggle button
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("🔐 Admin", key="admin_toggle"):
        st.session_state.show_admin_login = not st.session_state.get('show_admin_login', False)
        st.rerun()

# Admin login form
if st.session_state.get('show_admin_login') and not st.session_state.admin_logged:
    st.markdown("<div class='admin-login-box'>", unsafe_allow_html=True)
    st.markdown(f"### 🔐 {TEXT_ADMIN_LOGIN}")
    st.markdown("Enter admin credentials")
    
    # Rate limit check
    if not check_rate_limit():
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()
    
    with st.form("admin_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        csrf = st.text_input("CSRF", value=generate_csrf_token(), label_visibility="collapsed")
        
        cols = st.columns([1, 1])
        with cols[0]:
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if not verify_csrf_token(csrf):
                    st.error("⚠️ Security token invalid")
                else:
                    # Verify credentials against secrets
                    admin_user = get_secret("admin.username")
                    admin_pass = get_secret("admin.password")
                    
                    if username == admin_user and password == admin_pass:
                        st.session_state.admin_logged = True
                        st.session_state.admin_user = username
                        st.session_state.login_attempts = 0
                        st.session_state.show_admin_login = False
                        st.cache_data.clear()
                        st.success("✅ Access granted!")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        st.session_state.last_attempt = time.time()
                        st.error("❌ Invalid credentials")
        
        with cols[1]:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_admin_login = False
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# ADMIN DASHBOARD
# ==========================================

if st.session_state.admin_logged:
    # Navigation
    st.markdown("<div style='display:flex; gap:1rem; margin-bottom:2rem; justify-content:center;'>", unsafe_allow_html=True)
    nav_cols = st.columns(4)
    pages = [
        ("📊", "Dashboard", "dashboard"),
        ("🛍️", "Products", "products"),
        ("📦", "Orders", "orders"),
        ("⚙️", "Settings", "settings")
    ]
    for i, (icon, label, page) in enumerate(pages):
        with nav_cols[i]:
            is_active = st.session_state.admin_page == page
            if st.button(f"{icon} {label}", use_container_width=True, 
                        type="primary" if is_active else "secondary"):
                st.session_state.admin_page = page
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Logout
    _, logout_col = st.columns([6, 1])
    with logout_col:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.session_state.admin_user = None
            st.cache_data.clear()
            st.rerun()
    
    page = st.session_state.admin_page
    
    # DASHBOARD PAGE
    if page == "dashboard":
        st.markdown(f"<div class='section-title'>{TEXT_ADMIN_DASHBOARD}</div>", unsafe_allow_html=True)
        
        products_df = load_products()
        orders_df = load_orders()
        
        # Calculate metrics
        total_revenue = orders_df['amount'].sum() if not orders_df.empty and 'amount' in orders_df.columns else 0
        pending_count = len(orders_df[orders_df['status'] == STATUS_PENDING]) if not orders_df.empty and 'status' in orders_df.columns else 0
        low_stock = len(products_df[products_df['stock'].astype(int) < 5]) if not products_df.empty and 'stock' in products_df.columns else 0
        
        # Stats
        st.markdown(f"""
            <div class='stat-grid'>
                <div class='stat-box'>
                    <div class='stat-number'>{len(products_df)}</div>
                    <div class='stat-label'>Products</div>
                </div>
                <div class='stat-box'>
                    <div class='stat-number'>{len(orders_df)}</div>
                    <div class='stat-label'>Total Orders</div>
                </div>
                <div class='stat-box'>
                    <div class='stat-number'>{pending_count}</div>
                    <div class='stat-label'>Pending</div>
                </div>
                <div class='stat-box'>
                    <div class='stat-number'>{CURRENCY_SYMBOL}{total_revenue:,.0f}</div>
                    <div class='stat-label'>Revenue</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Recent Orders
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        st.markdown("### 📦 Recent Orders")
        if not orders_df.empty:
            recent = orders_df.tail(5).iloc[::-1]
            for _, order in recent.iterrows():
                status = order.get('status', STATUS_PENDING)
                status_class = f"status-{status.lower().replace(' ', '-')}"
                st.markdown(f"""
                    <div class='order-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <strong>{order.get('product_name', 'Unknown')}</strong><br>
                                <small>{order.get('name', 'Unknown')} • {order.get('timestamp', 'N/A')}</small>
                            </div>
                            <div style='text-align:right;'>
                                <span class='status-badge {status_class}'>{status}</span><br>
                                <strong style='color:{PRICE_COLOR};'>{CURRENCY_SYMBOL}{order.get('amount', 0)}</strong>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No orders yet")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # PRODUCTS PAGE
    elif page == "products":
        st.markdown("<div class='section-title'>Product Management</div>", unsafe_allow_html=True)
        
        products_df = load_products()
        
        # Add Product
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        st.markdown("### ➕ Add New Product")
        
        with st.form("add_product", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Product Name *", placeholder="e.g., Gold Necklace Set")
                price = st.number_input(f"Price ({CURRENCY_SYMBOL}) *", min_value=0, value=50)
            with c2:
                stock = st.number_input("Stock *", min_value=0, value=10)
                variants = st.text_input("Variants", placeholder="Small:50, Medium:75")
            
            description = st.text_area("Description", height=100)
            images = st.file_uploader(f"Images (Max {MAX_PRODUCT_IMAGES})", 
                                     type=["png", "jpg", "jpeg"], 
                                     accept_multiple_files=True)
            
            if st.form_submit_button("🚀 Add Product", use_container_width=True):
                if name and images:
                    urls = []
                    for i, img in enumerate(images[:MAX_PRODUCT_IMAGES], 1):
                        try:
                            urls.append(upload_to_cloudinary(img, f"{name}_{i}"))
                        except Exception as e:
                            st.error(f"Upload failed: {e}")
                            break
                    
                    if len(urls) == len(images[:MAX_PRODUCT_IMAGES]):
                        while len(urls) < MAX_PRODUCT_IMAGES:
                            urls.append("")
                        
                        try:
                            client = get_sheets_client()
                            sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                            new_id = int(products_df["id"].max()) + 1 if not products_df.empty and 'id' in products_df.columns else 1
                            status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK
                            
                            sheet.append_row([new_id, name, price, stock, urls[0], urls[1], urls[2], description, status, variants])
                            st.cache_data.clear()
                            st.success("✅ Product added!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("⚠️ Name and images required")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Manage Products
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        st.markdown("### 🗂️ Manage Products")
        
        if not products_df.empty:
            for i in range(0, len(products_df), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(products_df):
                        row = products_df.iloc[i + j]
                        with col:
                            if row.get("image1"):
                                st.image(str(row["image1"]), use_container_width=True)
                            st.markdown(f"**{row['name']}**")
                            st.markdown(f"<span style='color:{PRICE_COLOR};font-weight:700;'>{CURRENCY_SYMBOL}{row['price']}</span>", 
                                      unsafe_allow_html=True)
                            st.caption(f"Stock: {row.get('stock', 0)}")
                            
                            if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                                for key in ['image1', 'image2', 'image3']:
                                    if row.get(key):
                                        delete_from_cloudinary(str(row[key]))
                                try:
                                    client = get_sheets_client()
                                    sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                                    sheet.delete_rows(int(row["_row"]))
                                    st.cache_data.clear()
                                    st.success("Deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
        else:
            st.info("No products")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ORDERS PAGE
    elif page == "orders":
        st.markdown("<div class='section-title'>Order Management</div>", unsafe_allow_html=True)
        
        orders_df = load_orders()
        
        # Filters
        st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        with f1:
            status_filter = st.selectbox("Status", ["All", STATUS_PENDING, STATUS_APPROVED, STATUS_COMPLETED, STATUS_CANCELLED])
        with f2:
            search = st.text_input("Search", placeholder="Name, phone, reference...")
        with f3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Filter logic
        if not orders_df.empty:
            filtered = orders_df.copy()
            if status_filter != "All":
                filtered = filtered[filtered['status'] == status_filter]
            if search:
                mask = (
                    filtered['name'].str.contains(search, case=False, na=False) |
                    filtered['phone'].str.contains(search, case=False, na=False) |
                    filtered['reference'].str.contains(search, case=False, na=False)
                )
                filtered = filtered[mask]
            
            # Display orders
            for _, order in filtered.iterrows():
                status = order.get('status', STATUS_PENDING)
                status_class = f"status-{status.lower().replace(' ', '-')}"
                
                with st.container():
                    st.markdown(f"""
                        <div class='order-card'>
                            <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;'>
                                <div>
                                    <h4 style='margin:0; font-family:Playfair Display,serif;'>{order.get('product_name', 'Unknown')}</h4>
                                    <p style='margin:0.25rem 0; color:{TEXT_SECONDARY};'>
                                        👤 {order.get('name', 'Unknown')} • 📱 {order.get('phone', 'N/A')}
                                    </p>
                                    <p style='margin:0; color:{TEXT_MUTED}; font-size:0.85rem;'>
                                        📍 {order.get('location', 'N/A')} • 🕐 {order.get('timestamp', 'N/A')}
                                    </p>
                                </div>
                                <div style='text-align:right;'>
                                    <span class='status-badge {status_class}'>{status}</span>
                                    <h3 style='margin:0.5rem 0 0 0; color:{PRICE_COLOR}; font-family:Playfair Display,serif;'>
                                        {CURRENCY_SYMBOL}{order.get('amount', 0)}
                                    </h3>
                                    <p style='margin:0; font-size:0.8rem; color:{TEXT_MUTED};'>
                                        Ref: {order.get('reference', 'N/A')}
                                    </p>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    a1, a2, a3, a4 = st.columns([1, 1, 1, 2])
                    with a1:
                        if status == STATUS_PENDING:
                            if st.button("✓ Approve", key=f"app_{order['_row']}", use_container_width=True):
                                try:
                                    client = get_sheets_client()
                                    sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                                    sheet.update_cell(order['_row'], 9, STATUS_APPROVED)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    with a2:
                        if status in [STATUS_PENDING, STATUS_APPROVED]:
                            if st.button("✓ Complete", key=f"comp_{order['_row']}", use_container_width=True):
                                try:
                                    client = get_sheets_client()
                                    sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                                    sheet.update_cell(order['_row'], 9, STATUS_COMPLETED)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    with a3:
                        if status != STATUS_CANCELLED:
                            if st.button("✕ Cancel", key=f"can_{order['_row']}", use_container_width=True):
                                try:
                                    client = get_sheets_client()
                                    sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                                    sheet.update_cell(order['_row'], 9, STATUS_CANCELLED)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    
                    with a4:
                        phone = order.get('phone', '')
                        if phone:
                            st.markdown(f'<a href="tel:{phone}" style="text-decoration:none;">', unsafe_allow_html=True)
                            if st.button("📞 Call", key=f"call_{order['_row']}", use_container_width=True):
                                pass
        else:
            st.info("No orders found")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# PUBLIC SHOP
# ==========================================

products_df = load_products()

st.markdown(f"<div class='section-title'>{TEXT_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

# Search
if True:  # ENABLE_SEARCH
    _, search_col, _ = st.columns([1, 3, 1])
    with search_col:
        search_term = st.text_input("Search products", placeholder="🔍 Search jewelry...", label_visibility="collapsed")
        if search_term and not products_df.empty:
            products_df = products_df[
                products_df['name'].str.contains(search_term, case=False, na=False) |
                products_df['description'].str.contains(search_term, case=False, na=False)
            ]

# Categories
cats = ["All", "Necklaces", "Earrings", "Bracelets", "Rings"]
cat_cols = st.columns(len(cats))
for i, cat in enumerate(cats):
    with cat_cols[i]:
        active = st.session_state.active_category == cat
        if st.button(cat, use_container_width=True, type="primary" if active else "secondary"):
            st.session_state.active_category = cat
            st.rerun()

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# Products Grid
if products_df.empty:
    st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💎</div>
            <h3>No products found</h3>
            <p>New arrivals coming soon!</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='product-grid'>", unsafe_allow_html=True)
    
    for idx, row in products_df.iterrows():
        pid = int(row['id'])
        images = [str(row[f"image{i}"]) for i in range(1, 4) if row.get(f"image{i}") and str(row[f"image{i}"]).strip()]
        
        ckey = f"carousel_{pid}"
        if ckey not in st.session_state.carousel_indices:
            st.session_state.carousel_indices[ckey] = 0
        
        cidx = st.session_state.carousel_indices[ckey] % len(images) if images else 0
        has_variants = row.get('variants') and str(row['variants']).strip()
        in_stock = row.get('status') == STATUS_IN_STOCK
        
        # Card
        html = f"""
            <div class='product-card'>
                <div class='product-image-wrapper'>
                    {f"<div class='stock-badge {'badge-in-stock' if in_stock else 'badge-out-stock'}'>{row.get('status', 'In Stock')}</div>" if True else ""}
                    {f"<div class='product-image-container'><img src='{images[cidx]}' class='product-image' loading='lazy'></div>" if images else "<div style='padding:2rem;text-align:center;color:#9ca3af;'>No Image</div>"}
                    {f"<div class='carousel-dots'>{''.join([f'<div class=\"carousel-dot {'active' if i == cidx else ''}\"></div>' for i in range(len(images))])}</div>" if len(images) > 1 else ""}
                </div>
                <div class='product-content'>
                    <h3 class='product-name'>{row['name']}</h3>
                    {f"<p class='product-description'>{str(row['description'])[:60]}...</p>" if row.get('description') else ""}
                    <div class='product-meta'>
                        <div class='product-price'><span class='price-currency'>{CURRENCY_SYMBOL}</span>{row['price']}</div>
                        {f"<span class='variant-badge'>Options</span>" if has_variants else ""}
                    </div>
                </div>
            </div>
        """
        st.markdown(html, unsafe_allow_html=True)
        
        # Carousel controls
        if len(images) > 1:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("‹", key=f"prev_{pid}_{idx}", use_container_width=True):
                    st.session_state.carousel_indices[ckey] = (cidx - 1) % len(images)
                    st.rerun()
            with c2:
                st.markdown(f"<div style='text-align:center;font-size:0.8rem;color:{TEXT_MUTED};'>{cidx + 1} / {len(images)}</div>", 
                          unsafe_allow_html=True)
            with c3:
                if st.button("›", key=f"next_{pid}_{idx}", use_container_width=True):
                    st.session_state.carousel_indices[ckey] = (cidx + 1) % len(images)
                    st.rerun()
        
        # Order button
        if in_stock:
            if st.button(TEXT_ADD_TO_CART, key=f"order_{pid}", use_container_width=True):
                st.session_state.selected_product = row.to_dict()
                st.rerun()
        else:
            st.button(TEXT_OUT_OF_STOCK, key=f"out_{pid}", disabled=True, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# CHECKOUT
# ==========================================

if st.session_state.selected_product:
    p = st.session_state.selected_product
    
    st.markdown("<div class='order-container'>", unsafe_allow_html=True)
    st.markdown(f"### {TEXT_CHECKOUT}")
    st.markdown(f"<p style='color:{TEXT_SECONDARY};margin-bottom:1.5rem;'><strong>Product:</strong> {p['name']}</p>", 
              unsafe_allow_html=True)
    
    # Parse variants
    variants = {}
    if p.get('variants'):
        try:
            for pair in str(p['variants']).split(','):
                if ':' in pair:
                    k, v = pair.strip().split(':')
                    variants[k.strip()] = int(v.strip())
        except:
            pass
    
    with st.form("checkout"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", placeholder="Your name")
            phone = st.text_input("Phone *", placeholder="0541234567")
        with c2:
            location = st.text_input("Location *", placeholder="Accra, Kumasi")
            qty = st.number_input("Quantity *", min_value=1, max_value=50, value=1)
        
        variant = "Standard"
        price = int(p["price"])
        
        if variants:
            opts = list(variants.items())
            sel = st.radio("Select option:", options=range(len(opts)),
                         format_func=lambda x: f"{opts[x][0]} — {CURRENCY_SYMBOL}{opts[x][1]}",
                         horizontal=True)
            variant = opts[sel][0]
            price = opts[sel][1]
        
        total = price * qty
        
        st.markdown(f"""
            <div class='order-summary'>
                <div class='order-summary-title'>Order Summary</div>
                <div class='order-summary-row'><span>Product</span><span>{p['name']}</span></div>
                <div class='order-summary-row'><span>Variant</span><span>{variant}</span></div>
                <div class='order-summary-row'><span>Price</span><span>{CURRENCY_SYMBOL}{price}</span></div>
                <div class='order-summary-row'><span>Qty</span><span>{qty}</span></div>
                <div class='order-summary-total'>Total: {CURRENCY_SYMBOL}{total}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.form_submit_button(TEXT_PLACE_ORDER, use_container_width=True):
            if all([name, phone, location]):
                try:
                    ref = generate_reference(p["name"], location)
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    client = get_sheets_client()
                    sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                    sheet.append_row([name, phone, location, p["name"], qty, total, ref, ts, STATUS_PENDING, variant])
                    
                    send_notifications_async(p["name"], variant, name, phone, location, qty, total, ref, ts)
                    
                    st.markdown(f"""
                        <div class='success-message'>
                            <div class='success-title'>✅ Order Confirmed!</div>
                            <p>Reference: <strong>{ref}</strong></p>
                            <p>Total: <strong>{CURRENCY_SYMBOL}{total}</strong></p>
                            <p>We'll contact you soon!</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.selected_product = None
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Fill all required fields")
    
    if st.button("← Continue Shopping", use_container_width=True, type="secondary"):
        st.session_state.selected_product = None
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# FOOTER
# ==========================================

links_html = "".join([f"<a href='{l['url']}' class='footer-link'>{l['icon']} {l['text']}</a>" for l in FOOTER_LINKS])

st.markdown(f"""
    <div class='footer'>
        <div class='footer-title'>💎 {STORE_NAME}</div>
        <div class='footer-links'>{links_html}</div>
        <div class='footer-copyright'>{COPYRIGHT_TEXT}</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
