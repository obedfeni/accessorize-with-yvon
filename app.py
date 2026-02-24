# ==========================================
# ACCESSORIZE WITH YVON - CINEMATIC E-COMMERCE
# Full Stack: Python + Streamlit + CSS Animations
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
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote
import cloudinary
import cloudinary.uploader

from config import *

# ==========================================
# INITIALIZATION
# ==========================================
st.set_page_config(
    page_title=f"{STORE_NAME} | {STORE_TAGLINE}",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def generate_reference(product_name, location):
    product_code = product_name[:3].upper() if len(product_name) >= 3 else product_name.upper()
    location_code = location[:3].upper() if len(location) >= 3 else location.upper()
    random_num = random.randint(10 ** (REFERENCE_LENGTH - 1), (10 ** REFERENCE_LENGTH) - 1)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{random_num}"

def upload_to_cloudinary(file, filename):
    try:
        file.seek(0)
        clean_filename = ''.join(c for c in filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '') if c.isalnum() or c in ['_', '-'])
        public_id = f"accessorize_yvon/{clean_filename}_{int(time.time())}"
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': PRODUCT_IMAGE_QUALITY},
                {'fetch_format': 'auto'}
            ]
        )
        return result.get('secure_url')
    except Exception as e:
        print(f"Upload error: {e}")
        return None

def delete_from_cloudinary(image_url):
    try:
        if 'cloudinary.com' in image_url:
            parts = image_url.split('/')
            upload_idx = parts.index('upload')
            public_id = '/'.join(parts[upload_idx + 2:]).rsplit('.', 1)[0]
            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
    except Exception as e:
        print(f"Delete error: {e}")
    return False

def send_notifications_async(product_name, variant, customer_name, phone, location, qty, total, reference, timestamp):
    def _send():
        try:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID")
            if token and chat_id:
                message = TELEGRAM_TEMPLATE.format(
                    product_name=product_name, variant=variant, customer_name=customer_name,
                    phone=phone, location=location, quantity=qty, currency=CURRENCY_SYMBOL,
                    total=total, reference=reference, timestamp=timestamp
                )
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                    timeout=5
                )
        except:
            pass

        try:
            admin_email = os.environ.get("ADMIN_EMAIL")
            password = os.environ.get("EMAIL_APP_PASSWORD")
            if admin_email and password:
                msg = MIMEMultipart('alternative')
                msg['From'] = admin_email
                msg['To'] = admin_email
                msg['Subject'] = f"🛍️ New Order: {reference}"
                html = f"""
                <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
                    <div style='background:linear-gradient(135deg,{PRIMARY_COLOR},{PRIMARY_LIGHT});color:white;padding:30px;text-align:center;border-radius:15px 15px 0 0;'>
                        <h1>🛍️ New Order!</h1></div>
                    <div style='background:#fff5f5;padding:30px;border:1px solid {BORDER_COLOR};'>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p><strong>Customer:</strong> {customer_name}</p>
                        <p><strong>Total:</strong> {CURRENCY_SYMBOL} {total}</p>
                        <p><strong>Reference:</strong> {reference}</p>
                    </div></body></html>
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
# SESSION STATE
# ==========================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "carousel_indices" not in st.session_state:
    st.session_state.carousel_indices = {}

if "page" in st.query_params and st.query_params["page"] == "admin":
    st.session_state.show_admin_login = True

# ==========================================
# HIDE STREAMLIT BRANDING
# ==========================================

st.markdown("""
<style>
    #MainMenu, footer, header, .stDeployButton,
    [data-testid="stToolbar"] { display: none !important; }
    .stAppViewBlockContainer, .block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# Continue CSS
css_part2 = """
    .section-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: %s;
        margin: 2rem 0 1.5rem 0;
        text-align: center;
        position: relative;
        font-family: 'Playfair Display', serif;
    }

    .section-title::after {
        content: '';
        display: block;
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, %s, %s, %s);
        margin: 1rem auto 0;
        border-radius: 2px;
    }

    @media (min-width: 768px) {
        .section-title { font-size: 2.5rem; margin: 3rem 0 2rem 0; }
    }

    .product-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.2rem;
        perspective: 1000px;
    }

    @media (min-width: 768px) {
        .product-grid { grid-template-columns: repeat(3, 1fr); gap: 2rem; }
    }

    .product-card {
        background: %s;
        border-radius: 24px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05), 0 10px 30px rgba(0,0,0,0.1);
        transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        border: 2px solid %s;
        position: relative;
        transform-style: preserve-3d;
    }

    .product-card:hover {
        transform: translateY(-12px) scale(1.02);
        box-shadow: 0 30px 60px %s, 0 0 0 2px %s;
        border-color: %s;
    }

    .product-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%%;
        width: 100%%;
        height: 100%%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
        transition: left 0.7s;
        z-index: 10;
        pointer-events: none;
    }

    .product-card:hover::before {
        left: 100%%;
    }

    .product-image-wrapper {
        position: relative;
        width: 100%%;
        aspect-ratio: 1 / 1;
        background: linear-gradient(135deg, %s 0%%, %s 100%%);
        overflow: hidden;
    }

    .product-image-container {
        width: 100%%;
        height: 100%%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 16px;
        transition: transform 0.5s cubic-bezier(0.22, 1, 0.36, 1);
    }

    .product-card:hover .product-image-container {
        transform: scale(1.1);
    }

    .product-image {
        max-width: 100%%;
        max-height: 100%%;
        width: auto;
        height: auto;
        object-fit: contain;
        border-radius: 16px;
        transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
        filter: drop-shadow(0 10px 20px rgba(0,0,0,0.1));
    }

    .product-card:hover .product-image {
        filter: drop-shadow(0 20px 30px rgba(0,0,0,0.15));
        transform: scale(1.05);
    }

    .stock-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        padding: 0.6rem 1.2rem;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        z-index: 10;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: badgeFloat 3s ease-in-out infinite;
    }

    @keyframes badgeFloat {
        0%%, 100%% { transform: translateY(0); }
        50%% { transform: translateY(-5px); }
    }

    .badge-in-stock {
        background: linear-gradient(135deg, %s, #059669);
        color: white;
    }

    .badge-out-stock {
        background: linear-gradient(135deg, %s, #dc2626);
        color: white;
    }

    .product-content {
        padding: 1.5rem;
        background: %s;
        position: relative;
    }

    .product-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: %s;
        margin-bottom: 0.6rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.8rem;
    }

    @media (min-width: 768px) {
        .product-name { font-size: 1.2rem; }
    }

    .product-description {
        font-size: 0.85rem;
        color: %s;
        line-height: 1.5;
        margin-bottom: 1rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.5rem;
    }

    .product-price {
        font-size: 1.4rem;
        color: %s;
        font-weight: 800;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }

    .price-currency {
        font-size: 0.9rem;
        color: %s;
        font-weight: 600;
    }

    .variant-hint {
        font-size: 0.8rem;
        color: %s;
        font-weight: 700;
        margin-bottom: 1rem;
        padding: 6px 12px;
        background: linear-gradient(135deg, %s, #fff);
        border-radius: 20px;
        display: inline-block;
        border: 1px solid %s;
    }
"""

st.markdown(css_part2 % (
    TEXT_PRIMARY, PRIMARY_COLOR, PRIMARY_LIGHT, ACCENT_COLOR,
    CARD_BACKGROUND, BORDER_COLOR, SHADOW_COLOR, PRIMARY_COLOR, PRIMARY_COLOR,
    SURFACE_COLOR, BACKGROUND_COLOR, SUCCESS_COLOR, ERROR_COLOR, CARD_BACKGROUND,
    TEXT_PRIMARY, TEXT_SECONDARY, PRICE_COLOR, TEXT_MUTED, PRIMARY_COLOR, SURFACE_COLOR, BORDER_COLOR
), unsafe_allow_html=True)

# Final CSS parts
css_part4 = """
    .order-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 32px;
        padding: 2.5rem 2rem;
        margin: 3rem 0;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        border: 2px solid %s;
    }

    @media (min-width: 768px) {
        .order-container { padding: 3rem; margin: 4rem 0; }
    }

    .order-summary {
        background: linear-gradient(135deg, %s 0%%, %s 100%%);
        border: 2px solid %s;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }

    .order-summary::before {
        content: '✨';
        position: absolute;
        top: 10px;
        right: 20px;
        font-size: 60px;
        opacity: 0.1;
    }

    .order-summary-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: %s;
        margin-bottom: 1.2rem;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid %s;
    }

    .order-summary-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.8rem;
        font-size: 1rem;
        color: %s;
    }

    .order-summary-total {
        font-size: 1.8rem;
        font-weight: 800;
        color: %s;
        margin-top: 1.2rem;
        padding-top: 1.2rem;
        border-top: 2px solid %s;
    }

    .success-message {
        background: linear-gradient(135deg, #d1fae5 0%%, #a7f3d0 100%%);
        border: 3px solid %s;
        color: #065f46;
        padding: 3rem 2rem;
        border-radius: 24px;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 20px 50px rgba(16, 185, 129, 0.3);
        position: relative;
        overflow: hidden;
        animation: successPop 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }

    @keyframes successPop {
        0%% { transform: scale(0.8); opacity: 0; }
        100%% { transform: scale(1); opacity: 1; }
    }

    .success-message::before {
        content: '🎉';
        position: absolute;
        top: -20px;
        right: -20px;
        font-size: 120px;
        opacity: 0.15;
        animation: floatEmoji 3s ease-in-out infinite;
    }

    .success-message::after {
        content: '✨';
        position: absolute;
        bottom: -10px;
        left: -10px;
        font-size: 80px;
        opacity: 0.15;
        animation: floatEmoji 3s ease-in-out infinite reverse;
    }

    @keyframes floatEmoji {
        0%%, 100%% { transform: translateY(0) rotate(0deg); }
        50%% { transform: translateY(-20px) rotate(10deg); }
    }

    .success-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }

    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%%;
        height: 100%%;
        background: rgba(254, 243, 242, 0.98);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(10px);
    }

    .loading-spinner {
        width: 70px;
        height: 70px;
        border: 4px solid %s;
        border-top: 4px solid %s;
        border-right: 4px solid %s;
        border-radius: 50%%;
        animation: spin 1s linear infinite;
        box-shadow: 0 0 20px %s;
    }

    @keyframes spin {
        0%% { transform: rotate(0deg); }
        100%% { transform: rotate(360deg); }
    }

    .loading-text {
        margin-top: 2rem;
        font-size: 1.2rem;
        color: %s;
        font-weight: 700;
        animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
        0%%, 100%% { opacity: 1; }
        50%% { opacity: 0.5; }
    }

    .footer {
        background: linear-gradient(135deg, %s 0%%, %s 100%%);
        color: white;
        padding: 4rem 2rem;
        border-radius: 40px 40px 0 0;
        margin-top: 5rem;
        text-align: center;
        border-top: 4px solid %s;
        position: relative;
        overflow: hidden;
    }

    .footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%%;
        height: 100%%;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        opacity: 0.5;
    }

    .footer-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
        color: white;
        font-family: 'Playfair Display', serif;
        position: relative;
        z-index: 1;
    }

    .footer-links {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
    }

    .footer-link {
        color: rgba(255,255,255,0.9);
        text-decoration: none;
        font-size: 1rem;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .footer-link:hover {
        color: %s;
        transform: translateY(-3px);
    }

    .footer-copyright {
        font-size: 0.9rem;
        opacity: 0.7;
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 1px solid rgba(255,255,255,0.2);
        position: relative;
        z-index: 1;
    }

    .admin-login-box {
        max-width: 450px;
        margin: 4rem auto;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 32px;
        padding: 3rem;
        box-shadow: 0 25px 80px rgba(0,0,0,0.15);
        border: 2px solid %s;
        animation: loginEntrance 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }

    @keyframes loginEntrance {
        0%% { opacity: 0; transform: translateY(40px) scale(0.95); }
        100%% { opacity: 1; transform: translateY(0) scale(1); }
    }
</style>

<div class="gold-particles">
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
    <div class="gold-particle"></div>
</div>

<div class="pink-orb"></div>
<div class="pink-orb"></div>
<div class="pink-orb"></div>
"""

st.markdown(css_part4 % (
    BORDER_COLOR, SURFACE_COLOR, BACKGROUND_COLOR, BORDER_COLOR, TEXT_PRIMARY, BORDER_COLOR,
    TEXT_SECONDARY, PRICE_COLOR, BORDER_COLOR, SUCCESS_COLOR, BORDER_COLOR, PRIMARY_COLOR,
    PRIMARY_LIGHT, SHADOW_COLOR, PRIMARY_COLOR, TEXT_PRIMARY, TEXT_SECONDARY, PRIMARY_COLOR,
    PRIMARY_LIGHT, BORDER_COLOR
), unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS CONNECTION
# ==========================================

@st.cache_resource(ttl=3600, show_spinner=False)
def get_sheets_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = json.loads(os.environ.get("GCP_SERVICE_ACCOUNT"))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        st.stop()

@st.cache_data(ttl=CACHE_TTL_PRODUCTS, show_spinner=False)
def load_products():
    try:
        client = get_sheets_client()
        sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
        records = sheet.get_all_records(expected_headers=PRODUCT_COLUMNS)
        for i, r in enumerate(records, start=2):
            r["_row"] = i
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Failed to load products: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=CACHE_TTL_ORDERS, show_spinner=False)
def load_orders():
    try:
        client = get_sheets_client()
        sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
        records = sheet.get_all_records(expected_headers=ORDER_COLUMNS)
        for i, r in enumerate(records, start=2):
            r["_row"] = i
        return pd.DataFrame(records)
    except:
        return pd.DataFrame()

# ==========================================
# HERO COMPONENT
# ==========================================

hero_html = f"""
<div class='hero-section'>
    <div class='hero-shimmer'></div>
    <div class='hero-content'>
        <div class='hero-logo'>{LOGO_TEXT}</div>
        <div class='hero-text'>
            <div class='hero-title'>{STORE_NAME}</div>
            <div class='hero-tagline'>{STORE_TAGLINE}</div>
            <div class='hero-badge'>💎 Premium Quality</div>
        </div>
    </div>
</div>
"""

st.markdown(hero_html, unsafe_allow_html=True)

# ==========================================
# MAIN CONTENT WRAPPER
# ==========================================

st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# ==========================================
# ADMIN ACCESS TOGGLE
# ==========================================

if SHOW_ADMIN_BUTTON:
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        st.markdown("<div class='admin-btn-container'>", unsafe_allow_html=True)
        if st.button("🔐 Admin", key="admin_toggle"):
            st.session_state.show_admin_login = not st.session_state.show_admin_login
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ADMIN LOGIN
# ==========================================

if st.session_state.show_admin_login and not st.session_state.admin_logged:
    st.markdown("<div class='admin-login-box'>", unsafe_allow_html=True)
    st.markdown(f"### 🔐 {TEXT_ADMIN_LOGIN}")
    st.markdown("Enter your password to access the dashboard")

    with st.form("admin_login"):
        password = st.text_input("Password", type="password")
        cols = st.columns([1, 1])
        with cols[0]:
            if st.form_submit_button("Login", use_container_width=True):
                if password == os.environ.get("ADMIN_PASSWORD", "change_me"):
                    st.session_state.admin_logged = True
                    st.session_state.show_admin_login = False
                    st.cache_data.clear()
                    st.success("✅ Access granted!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        with cols[1]:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.show_admin_login = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# ADMIN DASHBOARD
# ==========================================

if st.session_state.admin_logged:
    st.markdown(f"<div class='section-title'>{TEXT_ADMIN_DASHBOARD}</div>", unsafe_allow_html=True)

    products_df = load_products()
    orders_df = load_orders()

    total_revenue = orders_df['amount'].sum() if not orders_df.empty else 0

    stats_html = f"""
    <div class='stat-grid'>
        <div class='stat-box'>
            <div class='stat-number'>{len(products_df)}</div>
            <div class='stat-label'>Products</div>
        </div>
        <div class='stat-box'>
            <div class='stat-number'>{len(orders_df)}</div>
            <div class='stat-label'>Orders</div>
        </div>
        <div class='stat-box'>
            <div class='stat-number'>{CURRENCY_SYMBOL}{total_revenue:,.0f}</div>
            <div class='stat-label'>Revenue</div>
        </div>
    </div>
    """
    st.markdown(stats_html, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.cache_data.clear()
            st.rerun()

    # Add Product
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.markdown("### ➕ Add New Product")

    with st.form("add_product", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product Name *", placeholder="e.g., Gold Necklace Set")
            price = st.number_input(f"Base Price ({CURRENCY_SYMBOL}) *", min_value=0, value=50)
        with col2:
            stock = st.number_input("Stock Quantity *", min_value=0, value=10)
            variants = st.text_input("Variants (Optional)", placeholder="Small:50, Medium:75, Large:100")

        description = st.text_area("Description", placeholder="Describe your product...")
        images = st.file_uploader("Product Images (Max 3)", type=["png","jpg","jpeg"], accept_multiple_files=True)

        if st.form_submit_button("🚀 Add Product", use_container_width=True):
            if name and images:
                with st.spinner("Uploading images..."):
                    image_urls = []
                    for idx, img in enumerate(images[:MAX_PRODUCT_IMAGES], 1):
                        filename = f"{name.replace(' ', '_')}_{idx}_{int(time.time())}.jpg"
                        url = upload_to_cloudinary(img, filename)
                        if url:
                            image_urls.append(url)

                    while len(image_urls) < MAX_PRODUCT_IMAGES:
                        image_urls.append("")

                    try:
                        client = get_sheets_client()
                        sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                        new_id = int(products_df["id"].max()) + 1 if not products_df.empty and "id" in products_df.columns else 1
                        status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK

                        sheet.append_row([new_id, name, price, stock] + image_urls + [description, status, variants])
                        st.cache_data.clear()
                        st.success("✅ Product added!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("⚠️ Please provide name and images")

    st.markdown("</div>", unsafe_allow_html=True)

    # Manage Products
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.markdown("### 🗂️ Manage Products")

    if not products_df.empty:
        for idx in range(0, len(products_df), 3):
            cols = st.columns(3)
            for i, col in enumerate(cols):
                if idx + i < len(products_df):
                    row = products_df.iloc[idx + i]
                    with col:
                        if row.get("image1") and str(row["image1"]).strip():
                            st.image(row["image1"], use_container_width=True)
                        else:
                            st.info("No image")

                        st.markdown(f"**{row['name']}**")
                        st.markdown(f"<span style='color:{PRICE_COLOR};font-weight:700;'>{CURRENCY_SYMBOL}{row['price']}</span>", unsafe_allow_html=True)
                        st.caption(f"Stock: {row.get('stock', 0)}")

                        delete_row = int(row["_row"])
                        product_id = int(row["id"])

                        if st.button("🗑️ Delete", key=f"del_{product_id}", use_container_width=True):
                            for img_col in ['image1', 'image2', 'image3']:
                                if row.get(img_col) and 'cloudinary.com' in str(row[img_col]):
                                    delete_from_cloudinary(str(row[img_col]))

                            try:
                                client = get_sheets_client()
                                sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                                sheet.delete_rows(delete_row)
                                st.cache_data.clear()
                                st.success("Deleted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
    else:
        st.info("No products found")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Buttons and Forms CSS
css_part3 = """
    .stButton > button {
        background: linear-gradient(135deg, %s 0%%, %s 100%%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1) !important;
        box-shadow: 0 6px 20px %s !important;
        width: 100%% !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%%;
        width: 100%%;
        height: 100%%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        transition: left 0.6s;
    }

    .stButton > button:hover::before {
        left: 100%%;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 30px %s !important;
    }

    .stButton > button:disabled {
        background: #e5e7eb !important;
        color: #9ca3af !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }

    .admin-btn-container button {
        padding: 0.6rem 1.2rem !important;
        font-size: 0.85rem !important;
        width: auto !important;
        min-width: 120px !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: %s !important;
        color: %s !important;
        border: 2px solid %s !important;
        border-radius: 16px !important;
        padding: 1rem 1.2rem !important;
        font-size: 1rem !important;
        transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1) !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: %s !important;
        box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.15) !important;
        outline: none !important;
        transform: translateY(-2px);
    }

    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        color: %s !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }

    .admin-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.5);
    }

    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.2rem;
        margin-bottom: 2rem;
    }

    @media (min-width: 768px) {
        .stat-grid { gap: 1.5rem; }
    }

    .stat-box {
        background: linear-gradient(135deg, %s 0%%, %s 100%%);
        color: white;
        padding: 1.8rem 1rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 15px 35px %s;
        transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
        position: relative;
        overflow: hidden;
    }

    .stat-box::before {
        content: '';
        position: absolute;
        top: -50%%;
        left: -50%%;
        width: 200%%;
        height: 200%%;
        background: radial-gradient(circle, rgba(255,255,255,0.3) 0%%, transparent 70%%);
        animation: statPulse 3s ease-in-out infinite;
    }

    @keyframes statPulse {
        0%%, 100%% { transform: scale(1); opacity: 0.5; }
        50%% { transform: scale(1.1); opacity: 0.8; }
    }

    .stat-box:hover {
        transform: translateY(-5px) scale(1.02);
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        line-height: 1;
        position: relative;
        z-index: 2;
    }

    @media (min-width: 768px) {
        .stat-number { font-size: 2.5rem; }
    }

    .stat-label {
        font-size: 0.8rem;
        opacity: 0.95;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        position: relative;
        z-index: 2;
    }
"""

st.markdown(css_part3 % (
    PRIMARY_LIGHT, PRIMARY_COLOR, SHADOW_COLOR, SHADOW_COLOR,
    CARD_BACKGROUND, TEXT_PRIMARY, BORDER_COLOR, PRIMARY_COLOR, TEXT_PRIMARY,
    PRIMARY_COLOR, PRIMARY_LIGHT, SHADOW_COLOR
), unsafe_allow_html=True)

# ==========================================
# CHECKOUT FORM
# ==========================================

if st.session_state.selected_product is not None:
    p = st.session_state.selected_product

    st.markdown("<div class='order-container'>", unsafe_allow_html=True)
    st.markdown(f"### {TEXT_CHECKOUT}")
    st.markdown(f"<p style='color:{TEXT_SECONDARY};margin-bottom:1rem;'><strong>Product:</strong> {p['name']}</p>", unsafe_allow_html=True)

    # Parse variants
    variants_dict = {}
    if p.get('variants') and ENABLE_VARIANTS:
        try:
            for pair in str(p['variants']).split(','):
                if ':' in pair:
                    size, price = pair.strip().split(':')
                    variants_dict[size.strip()] = int(price.strip())
        except:
            pass

    with st.form("checkout", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"{TEXT_LABEL_NAME} *", placeholder="Your full name")
            phone = st.text_input(f"{TEXT_LABEL_PHONE} *", placeholder="0541234567")
        with col2:
            location = st.text_input(f"{TEXT_LABEL_LOCATION} *", placeholder="Accra, Kumasi, etc.")
            qty = st.number_input(f"{TEXT_LABEL_QUANTITY} *", min_value=MIN_ORDER_QUANTITY, max_value=MAX_ORDER_QUANTITY, value=MIN_ORDER_QUANTITY)

        # Variant selector
        selected_variant = "Standard"
        unit_price = int(p["price"])

        if variants_dict:
            st.markdown("<div class='variant-selector'>", unsafe_allow_html=True)
            st.markdown(f"<div class='variant-label'>{TEXT_LABEL_VARIANT}</div>", unsafe_allow_html=True)

            variant_options = list(variants_dict.items())
            selected_idx = st.radio(
                "",
                options=range(len(variant_options)),
                format_func=lambda x: f"{variant_options[x][0]} - {CURRENCY_SYMBOL}{variant_options[x][1]}",
                horizontal=True,
                label_visibility="collapsed"
            )

            selected_variant = variant_options[selected_idx][0]
            unit_price = variant_options[selected_idx][1]
            st.markdown("</div>", unsafe_allow_html=True)

        total = unit_price * int(qty)

        st.markdown(f"""
            <div class='order-summary'>
                <div class='order-summary-title'>Order Summary</div>
                <div class='order-summary-row'><span>Product:</span><span>{p['name']}</span></div>
                <div class='order-summary-row'><span>Variant:</span><span>{selected_variant}</span></div>
                <div class='order-summary-row'><span>Unit Price:</span><span>{CURRENCY_SYMBOL}{unit_price}</span></div>
                <div class='order-summary-row'><span>Quantity:</span><span>{qty}</span></div>
                <div class='order-summary-total'>Total: {CURRENCY_SYMBOL}{total}</div>
            </div>
        """, unsafe_allow_html=True)

        submitted = st.form_submit_button(TEXT_PLACE_ORDER, use_container_width=True)

        if submitted:
            if not all([name, phone, location]):
                st.warning("⚠️ Please fill in all required fields")
            else:
                loading = st.empty()
                loading.markdown("""
                    <div class='loading-overlay'>
                        <div class='loading-spinner'></div>
                        <div class='loading-text'>Processing your order...</div>
                    </div>
                """, unsafe_allow_html=True)

                try:
                    ref = generate_reference(p["name"], location)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Save to sheets
                    client = get_sheets_client()
                    sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                    sheet.append_row([name, phone, location, p["name"], qty, total, ref, timestamp, STATUS_PENDING, selected_variant])

                    # Send notifications async
                    send_notifications_async(
                        p["name"], selected_variant, name, phone, location, 
                        qty, total, ref, timestamp
                    )

                    loading.empty()

                    st.markdown(f"""
                        <div class='success-message'>
                            <div class='success-title'>✅ {ORDER_SUCCESS_TITLE}</div>
                            <p>Reference: <strong>{ref}</strong></p>
                            <p>Total: <strong>{CURRENCY_SYMBOL}{total}</strong></p>
                            <p style='font-size:0.9rem;opacity:0.9;'>{ORDER_SUCCESS_MESSAGE}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    st.session_state.selected_product = None

                    time.sleep(15)
                    st.rerun()

                except Exception as e:
                    loading.empty()
                    st.error(f"❌ Error: {str(e)}")

    if st.button("← Continue Shopping", use_container_width=True):
        st.session_state.selected_product = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # Close main-content

# ==========================================
# FOOTER
# ==========================================

footer_links_html = "".join([
    f"<a href='{link['url']}' class='footer-link'>{link['icon']} {link['text']}</a>"
    for link in FOOTER_LINKS
])

st.markdown(f"""
<div class='footer'>
    <div class='footer-title'>💎 {STORE_NAME}</div>
    <div class='footer-links'>
        {footer_links_html}
    </div>
    <div class='footer-copyright'>
        {COPYRIGHT_TEXT}
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PUBLIC SHOP - PRODUCT GRID
# ==========================================

products_df = load_products()

st.markdown(f"<div class='section-title'>{TEXT_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

if products_df.empty:
    st.info("✨ New arrivals coming soon! Check back later.")
else:
    # Search
    if ENABLE_SEARCH:
        search_term = st.text_input("🔍 Search products...", placeholder="Search jewelry, accessories...", label_visibility="collapsed")
        if search_term:
            products_df = products_df[products_df['name'].str.contains(search_term, case=False, na=False)]

    # Product Grid
    st.markdown("<div class='product-grid'>", unsafe_allow_html=True)

    for idx, row in products_df.iterrows():
        # Get images
        images = []
        for img_idx in range(1, 4):
            img_key = f"image{img_idx}"
            if img_key in row and row[img_key] and str(row[img_key]).strip():
                images.append(str(row[img_key]))

        product_id = int(row['id'])
        carousel_key = f"carousel_{product_id}"

        if carousel_key not in st.session_state.carousel_indices:
            st.session_state.carousel_indices[carousel_key] = 0

        if images:
            st.session_state.carousel_indices[carousel_key] = st.session_state.carousel_indices[carousel_key] % len(images)

        has_variants = row.get('variants') and str(row['variants']).strip()

        st.markdown("<div class='product-card'>", unsafe_allow_html=True)

        # Image Section
        st.markdown("<div class='product-image-wrapper'>", unsafe_allow_html=True)

        if SHOW_STOCK_BADGE:
            badge_class = "badge-in-stock" if row.get('status') == STATUS_IN_STOCK else "badge-out-stock"
            badge_text = STATUS_IN_STOCK if row.get('status') == STATUS_IN_STOCK else STATUS_OUT_OF_STOCK
            st.markdown(f"<div class='stock-badge {badge_class}'>{badge_text}</div>", unsafe_allow_html=True)

        if images:
            current_img_idx = st.session_state.carousel_indices[carousel_key]
            current_img = images[current_img_idx]
            st.markdown(f"""
                <div class='product-image-container'>
                    <img src='{current_img}' class='product-image' loading='lazy' alt='{row['name']}'>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='product-image-container'><div style='color:#9ca3af;font-size:0.9rem;'>No Image</div></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Carousel Controls
        if len(images) > 1:
            col_l, col_m, col_r = st.columns([1, 2, 1])
            with col_l:
                if st.button("◀", key=f"prev_{product_id}_{idx}", use_container_width=True):
                    new_idx = (st.session_state.carousel_indices[carousel_key] - 1) % len(images)
                    st.session_state.carousel_indices[carousel_key] = new_idx
                    st.rerun()
            with col_m:
                st.markdown(f"<div style='text-align:center;padding:8px 0;font-size:0.8rem;color:#6b7280;font-weight:600;'>{st.session_state.carousel_indices[carousel_key] + 1} / {len(images)}</div>", unsafe_allow_html=True)
            with col_r:
                if st.button("▶", key=f"next_{product_id}_{idx}", use_container_width=True):
                    new_idx = (st.session_state.carousel_indices[carousel_key] + 1) % len(images)
                    st.session_state.carousel_indices[carousel_key] = new_idx
                    st.rerun()

        # Product Info
        st.markdown(f"""
            <div class='product-content'>
                <div class='product-name'>{row['name']}</div>
        """, unsafe_allow_html=True)

        if row.get('description'):
            st.markdown(f"<div class='product-description'>{row['description']}</div>", unsafe_allow_html=True)

        st.markdown(f"""
                <div class='product-price'>
                    <span class='price-currency'>{CURRENCY_SYMBOL}</span>{row['price']}
                </div>
        """, unsafe_allow_html=True)

        if has_variants:
            st.markdown("<div class='variant-hint'>✨ Multiple sizes available</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Button
        if row.get('status') == STATUS_OUT_OF_STOCK:
            st.button(TEXT_OUT_OF_STOCK, key=f"out_{product_id}", disabled=True, use_container_width=True)
        else:
            if st.button(TEXT_ADD_TO_CART, key=f"order_{product_id}", use_container_width=True):
                st.session_state.selected_product = row
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
