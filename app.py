# ==========================================
# ACCESSORIZE WITH YVON - ANIMATED E-COMMERCE
# Feminine Gold & Pink with Animated Background
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

# Import configuration
from config import *

# ==========================================
# INITIALIZATION - Must be first
# ==========================================
st.set_page_config(
    page_title=f"{STORE_NAME} | {STORE_TAGLINE}",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': f"{STORE_NAME} - {STORE_DESCRIPTION}"
    }
)

# Cloudinary Setup
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
    """Generate unique order reference"""
    product_code = product_name[:3].upper() if len(product_name) >= 3 else product_name.upper()
    location_code = location[:3].upper() if len(location) >= 3 else location.upper()
    random_num = random.randint(10 ** (REFERENCE_LENGTH - 1), (10 ** REFERENCE_LENGTH) - 1)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{random_num}"

def upload_to_cloudinary(file, filename):
    """Upload image with optimization"""
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
    """Delete image from Cloudinary"""
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

# ==========================================
# ASYNC NOTIFICATIONS (Non-blocking)
# ==========================================

def send_notifications_async(product_name, variant, customer_name, phone, location, qty, total, reference, timestamp):
    """Send notifications in background thread"""
    def _send():
        # Telegram
        try:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID")
            if token and chat_id:
                message = TELEGRAM_TEMPLATE.format(
                    product_name=product_name,
                    variant=variant,
                    customer_name=customer_name,
                    phone=phone,
                    location=location,
                    quantity=qty,
                    currency=CURRENCY_SYMBOL,
                    total=total,
                    reference=reference,
                    timestamp=timestamp
                )
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                    timeout=5
                )
        except:
            pass
        
        # Email
        try:
            admin_email = os.environ.get("ADMIN_EMAIL")
            password = os.environ.get("EMAIL_APP_PASSWORD")
            if admin_email and password:
                msg = MIMEMultipart('alternative')
                msg['From'] = admin_email
                msg['To'] = admin_email
                msg['Subject'] = f"🛍️ New Order: {reference}"
                
                html = f"""
                <html>
                <body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
                    <div style='background:linear-gradient(135deg,{PRIMARY_COLOR},{PRIMARY_LIGHT});color:white;padding:30px;text-align:center;border-radius:15px 15px 0 0;'>
                        <h1>🛍️ New Order!</h1>
                    </div>
                    <div style='background:#fff5f5;padding:30px;border:1px solid {BORDER_COLOR};'>
                        <p><strong>Product:</strong> {product_name}</p>
                        <p><strong>Variant:</strong> {variant}</p>
                        <p><strong>Customer:</strong> {customer_name}</p>
                        <p><strong>Phone:</strong> {phone}</p>
                        <p><strong>Location:</strong> {location}</p>
                        <p><strong>Quantity:</strong> {qty}</p>
                        <p><strong>Total:</strong> {CURRENCY_SYMBOL} {total}</p>
                        <p><strong>Reference:</strong> {reference}</p>
                    </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(html, 'html'))
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(admin_email, password)
                server.send_message(msg)
                server.quit()
        except:
            pass
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

# ==========================================
# SEO & META TAGS
# ==========================================

st.markdown(f"""
    <!-- Preconnect for Performance -->
    <link rel="preconnect" href="https://res.cloudinary.com" crossorigin>
    <link rel="dns-prefetch" href="https://res.cloudinary.com">
    
    <!-- Mobile Optimization -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="theme-color" content="{PRIMARY_COLOR}">
    
    <!-- SEO -->
    <meta name="description" content="{STORE_DESCRIPTION}. Shop high-quality jewelry, body splashes, hair accessories & crocheted fashion in Ghana. Fast delivery in Accra & nationwide.">
    <meta name="keywords" content="jewelry ghana, hair accessories accra, body splash ghana, crocheted fashion, handmade jewelry, beauty products ghana, accessories shop">
    <meta name="author" content="{STORE_NAME}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://accessorizewithyvon.com">
    
    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{STORE_NAME}">
    <meta property="og:description" content="{STORE_TAGLINE}. {STORE_DESCRIPTION}">
    <meta property="og:site_name" content="{STORE_NAME}">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Store",
      "name": "{STORE_NAME}",
      "description": "{STORE_TAGLINE}",
      "address": {{
        "@type": "PostalAddress",
        "addressLocality": "{LOCATION}",
        "addressCountry": "GH"
      }},
      "telephone": "+233{PHONE_NUMBER[1:]}",
      "priceRange": "{CURRENCY_SYMBOL}50-500"
    }}
    </script>
    
    <!-- Favicon -->
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💎</text></svg>">
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE - FIXED INITIALIZATION
# ==========================================

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None
if "cart" not in st.session_state:
    st.session_state.cart = []
if "carousel_indices" not in st.session_state:
    st.session_state.carousel_indices = {}

if "page" in st.query_params and st.query_params["page"] == "admin":
    st.session_state.show_admin_login = True

# ==========================================
# HIDE STREAMLIT BRANDING - FIXED PADDING
# ==========================================

st.markdown("""
<style>
    #MainMenu, footer, header, .stDeployButton,
    .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_,
    [data-testid="stToolbar"], [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    /* FIX: Remove excessive padding that causes huge gaps */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* FIX: Remove gap between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    /* FIX: Tighten up vertical spacing */
    [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ANIMATED FEMININE THEME - FIXED Z-INDEX
# ==========================================

logo_border_radius = "50%" if LOGO_SHAPE == "circle" else "16px"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* ==========================================
       MAIN BACKGROUND - Fixed to show content
       ========================================== */
    .stApp {{
        background: linear-gradient(135deg, {BACKGROUND_COLOR} 0%, #fff5f5 50%, #fef3f2 100%);
        background-attachment: fixed;
    }}
    
    /* ==========================================
       FLOATING PARTICLES - Fixed z-index
       ========================================== */
    .floating-particles {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }}
    
    .particle {{
        position: absolute;
        width: 6px;
        height: 6px;
        background: radial-gradient(circle, {PRIMARY_LIGHT} 0%, {PRIMARY_COLOR} 100%);
        border-radius: 50%;
        opacity: 0.4;
        animation: float 20s infinite linear;
        box-shadow: 0 0 8px {PRIMARY_COLOR};
    }}
    
    .particle:nth-child(1) {{ left: 10%; animation-delay: 0s; animation-duration: 25s; }}
    .particle:nth-child(2) {{ left: 20%; animation-delay: 5s; animation-duration: 20s; width: 8px; height: 8px; }}
    .particle:nth-child(3) {{ left: 30%; animation-delay: 10s; animation-duration: 30s; }}
    .particle:nth-child(4) {{ left: 40%; animation-delay: 2s; animation-duration: 22s; width: 4px; height: 4px; }}
    .particle:nth-child(5) {{ left: 50%; animation-delay: 8s; animation-duration: 28s; }}
    .particle:nth-child(6) {{ left: 60%; animation-delay: 15s; animation-duration: 24s; width: 10px; height: 10px; }}
    .particle:nth-child(7) {{ left: 70%; animation-delay: 3s; animation-duration: 26s; }}
    .particle:nth-child(8) {{ left: 80%; animation-delay: 12s; animation-duration: 21s; width: 5px; height: 5px; }}
    .particle:nth-child(9) {{ left: 90%; animation-delay: 7s; animation-duration: 29s; }}
    .particle:nth-child(10) {{ left: 95%; animation-delay: 18s; animation-duration: 23s; width: 7px; height: 7px; }}
    
    @keyframes float {{
        0% {{
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }}
        10% {{
            opacity: 0.4;
        }}
        90% {{
            opacity: 0.4;
        }}
        100% {{
            transform: translateY(-100vh) rotate(720deg);
            opacity: 0;
        }}
    }}
    
    /* Pink Orbs Background */
    .pink-orb {{
        position: fixed;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.3;
        pointer-events: none;
        z-index: 0;
        animation: orbFloat 20s ease-in-out infinite;
    }}
    
    .pink-orb:nth-child(1) {{
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(236, 72, 153, 0.4) 0%, transparent 70%);
        top: 10%;
        left: -100px;
        animation-delay: 0s;
    }}
    
    .pink-orb:nth-child(2) {{
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(244, 114, 182, 0.3) 0%, transparent 70%);
        bottom: 10%;
        right: -150px;
        animation-delay: 5s;
    }}
    
    @keyframes orbFloat {{
        0%, 100% {{ transform: translate(0, 0) scale(1); }}
        33% {{ transform: translate(30px, -30px) scale(1.1); }}
        66% {{ transform: translate(-20px, 20px) scale(0.9); }}
    }}
    
    /* ==========================================
       CONTENT WRAPPER - Ensure content is visible
       ========================================== */
    .main-content {{
        position: relative;
        z-index: 10;
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 1rem 2rem 1rem;
    }}
    
    @media (min-width: 768px) {{
        .main-content {{
            padding: 0 2rem 3rem 2rem;
        }}
    }}
    
    /* ==========================================
       HEADER - ELEGANT NAVIGATION
       ========================================== */
    .header {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 1rem 1.5rem;
        border-radius: 0 0 24px 24px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 20px {SHADOW_COLOR};
        position: sticky;
        top: 0;
        z-index: 100;
        border-bottom: 3px solid {PRIMARY_COLOR};
        animation: slideDown 0.6s ease-out;
    }}
    
    @keyframes slideDown {{
        from {{
            transform: translateY(-100%);
            opacity: 0;
        }}
        to {{
            transform: translateY(0);
            opacity: 1;
        }}
    }}
    
    .logo-container {{
        display: flex;
        align-items: center;
        gap: 1rem;
        flex: 1;
    }}
    
    .logo-icon {{
        width: 55px;
        height: 55px;
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        border-radius: {logo_border_radius};
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.4rem;
        color: white;
        box-shadow: 0 4px 15px {SHADOW_COLOR};
        flex-shrink: 0;
        transition: all 0.3s ease;
    }}
    
    .logo-icon:hover {{
        transform: scale(1.05) rotate(-5deg);
    }}
    
    .brand-text {{
        flex: 1;
    }}
    
    .brand-name {{
        font-size: 1.3rem;
        font-weight: 800;
        color: {TEXT_PRIMARY};
        line-height: 1.2;
        letter-spacing: -0.02em;
        font-family: 'Playfair Display', serif;
    }}
    
    .brand-tagline {{
        font-size: 0.75rem;
        color: {TEXT_SECONDARY};
        margin-top: 4px;
        font-weight: 500;
    }}
    
    @media (min-width: 768px) {{
        .header {{
            padding: 1.2rem 2.5rem;
            border-radius: 0 0 32px 32px;
        }}
        .logo-icon {{
            width: 65px;
            height: 65px;
            font-size: 1.6rem;
        }}
        .brand-name {{
            font-size: 1.6rem;
        }}
        .brand-tagline {{
            font-size: 0.85rem;
        }}
    }}
    
    /* ==========================================
       SECTION HEADERS
       ========================================== */
    .section-title {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {TEXT_PRIMARY};
        margin: 1.5rem 0 1rem 0;
        text-align: center;
        position: relative;
        display: inline-block;
        width: 100%;
        font-family: 'Playfair Display', serif;
    }}
    
    .section-title::after {{
        content: '';
        display: block;
        width: 80px;
        height: 4px;
        background: linear-gradient(90deg, {PRIMARY_COLOR}, {PRIMARY_LIGHT});
        margin: 0.5rem auto 0;
        border-radius: 2px;
    }}
    
    @media (min-width: 768px) {{
        .section-title {{
            font-size: 2rem;
            margin: 2rem 0 1.5rem 0;
        }}
    }}
    
    /* ==========================================
       PRODUCT CARDS - TIGHTENED SPACING
       ========================================== */
    .product-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.8rem;
        margin-top: 0.5rem;
    }}
    
    @media (min-width: 768px) {{
        .product-grid {{
            grid-template-columns: repeat(3, 1fr);
            gap: 1.2rem;
        }}
    }}
    
    .product-card {{
        background: {CARD_BACKGROUND};
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 2px solid {BORDER_COLOR};
        position: relative;
    }}
    
    .product-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 12px 30px {SHADOW_COLOR};
        border-color: {PRIMARY_COLOR};
    }}
    
    .product-image-wrapper {{
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        background: linear-gradient(135deg, {SURFACE_COLOR} 0%, {BACKGROUND_COLOR} 100%);
        overflow: hidden;
    }}
    
    .product-image-container {{
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 8px;
    }}
    
    .product-image {{
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        object-fit: contain;
        transition: transform 0.3s ease;
        border-radius: 10px;
    }}
    
    .product-card:hover .product-image {{
        transform: scale(1.05);
    }}
    
    .stock-badge {{
        position: absolute;
        top: 8px;
        right: 8px;
        padding: 0.4rem 0.8rem;
        border-radius: 16px;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        z-index: 10;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    .badge-in-stock {{
        background: linear-gradient(135deg, {SUCCESS_COLOR}, #059669);
        color: white;
    }}
    
    .badge-out-stock {{
        background: linear-gradient(135deg, {ERROR_COLOR}, #dc2626);
        color: white;
    }}
    
    .product-content {{
        padding: 1rem;
        background: {CARD_BACKGROUND};
    }}
    
    .product-name {{
        font-size: 0.95rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.3rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.4rem;
    }}
    
    @media (min-width: 768px) {{
        .product-name {{
            font-size: 1.05rem;
        }}
    }}
    
    .product-description {{
        font-size: 0.75rem;
        color: {TEXT_SECONDARY};
        line-height: 1.4;
        margin-bottom: 0.5rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.1rem;
    }}
    
    .product-price {{
        font-size: 1.2rem;
        color: {PRICE_COLOR};
        font-weight: 800;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.2rem;
    }}
    
    .price-currency {{
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        font-weight: 600;
    }}
    
    .variant-hint {{
        font-size: 0.7rem;
        color: {PRIMARY_COLOR};
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding: 3px 6px;
        background: {SURFACE_COLOR};
        border-radius: 4px;
        display: inline-block;
    }}
    
    /* ==========================================
       CAROUSEL CONTROLS - COMPACT
       ========================================== */
    .carousel-controls {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 6px;
        background: {CARD_BACKGROUND};
        border-top: 1px solid {BORDER_COLOR};
    }}
    
    .carousel-btn {{
        background: linear-gradient(135deg, {PRIMARY_COLOR}, {PRIMARY_LIGHT});
        border: none;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 0.8rem;
        color: white;
        transition: all 0.2s;
        box-shadow: 0 2px 6px {SHADOW_COLOR};
    }}
    
    .carousel-btn:hover {{
        transform: scale(1.1);
        box-shadow: 0 3px 10px {SHADOW_COLOR};
    }}
    
    .carousel-indicator {{
        color: {TEXT_SECONDARY};
        font-size: 0.75rem;
        font-weight: 700;
        min-width: 35px;
        text-align: center;
        background: {SURFACE_COLOR};
        padding: 3px 8px;
        border-radius: 10px;
    }}
    
    /* ==========================================
       BUTTONS - GOLDEN THEME
       ========================================== */
    .stButton > button {{
        background: linear-gradient(135deg, {PRIMARY_LIGHT} 0%, {PRIMARY_COLOR} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.2rem !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 3px 12px {SHADOW_COLOR} !important;
        width: 100% !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 18px {SHADOW_COLOR} !important;
    }}
    
    .stButton > button:disabled {{
        background: #e5e7eb !important;
        color: #9ca3af !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
    }}
    
    /* Admin button smaller */
    .admin-btn-container button {{
        padding: 0.4rem 0.8rem !important;
        font-size: 0.75rem !important;
        width: auto !important;
        min-width: 90px !important;
    }}
    
    /* ==========================================
       FORMS - ELEGANT INPUTS
       ========================================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        background-color: {CARD_BACKGROUND} !important;
        color: {TEXT_PRIMARY} !important;
        border: 2px solid {BORDER_COLOR} !important;
        border-radius: 10px !important;
        padding: 0.7rem 0.9rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {PRIMARY_COLOR} !important;
        box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1) !important;
        outline: none !important;
    }}
    
    .stTextInput > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stSelectbox > label {{
        color: {TEXT_PRIMARY} !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        margin-bottom: 0.3rem !important;
    }}
    
    /* ==========================================
       ADMIN CARDS
       ========================================== */
    .admin-card {{
        background: {CARD_BACKGROUND};
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 2px solid {BORDER_COLOR};
    }}
    
    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.8rem;
        margin-bottom: 1.5rem;
    }}
    
    @media (min-width: 768px) {{
        .stat-grid {{
            gap: 1.2rem;
        }}
    }}
    
    .stat-box {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_LIGHT} 100%);
        color: white;
        padding: 1.2rem 0.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 8px 20px {SHADOW_COLOR};
        transition: transform 0.3s ease;
    }}
    
    .stat-box:hover {{
        transform: translateY(-3px);
    }}
    
    .stat-number {{
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        line-height: 1;
    }}
    
    @media (min-width: 768px) {{
        .stat-number {{
            font-size: 2rem;
        }}
    }}
    
    .stat-label {{
        font-size: 0.7rem;
        opacity: 0.95;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* ==========================================
       ORDER FORM & CHECKOUT - COMPACT
       ========================================== */
    .order-container {{
        background: {CARD_BACKGROUND};
        border-radius: 20px;
        padding: 1.5rem 1.2rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        border: 2px solid {BORDER_COLOR};
    }}
    
    @media (min-width: 768px) {{
        .order-container {{
            padding: 2rem;
            margin: 2rem 0;
        }}
    }}
    
    .order-summary {{
        background: linear-gradient(135deg, {SURFACE_COLOR} 0%, {BACKGROUND_COLOR} 100%);
        border: 2px solid {BORDER_COLOR};
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
    }}
    
    .order-summary-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid {BORDER_COLOR};
    }}
    
    .order-summary-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.4rem;
        font-size: 0.9rem;
        color: {TEXT_SECONDARY};
    }}
    
    .order-summary-total {{
        font-size: 1.3rem;
        font-weight: 800;
        color: {PRICE_COLOR};
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 2px solid {BORDER_COLOR};
    }}
    
    /* Variant Selector */
    .variant-selector {{
        background: {SURFACE_COLOR};
        border: 2px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.8rem 0;
    }}
    
    .variant-label {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* ==========================================
       SUCCESS MESSAGE
       ========================================== */
    .success-message {{
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 2px solid {SUCCESS_COLOR};
        color: #065f46;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        text-align: center;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.2);
        position: relative;
        overflow: hidden;
    }}
    
    .success-message::before {{
        content: '✨';
        position: absolute;
        top: -10px;
        right: -10px;
        font-size: 60px;
        opacity: 0.2;
    }}
    
    .success-title {{
        font-size: 1.3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
    }}
    
    /* ==========================================
       LOADING OVERLAY
       ========================================== */
    .loading-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(254, 243, 242, 0.98);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(10px);
    }}
    
    .loading-spinner {{
        width: 50px;
        height: 50px;
        border: 4px solid {BORDER_COLOR};
        border-top: 4px solid {PRIMARY_COLOR};
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .loading-text {{
        margin-top: 1rem;
        font-size: 1rem;
        color: {PRIMARY_COLOR};
        font-weight: 700;
    }}
    
    /* ==========================================
       FOOTER - COMPACT
       ========================================== */
    .footer {{
        background: linear-gradient(135deg, {TEXT_PRIMARY} 0%, {TEXT_SECONDARY} 100%);
        color: white;
        padding: 2rem 1rem;
        border-radius: 20px 20px 0 0;
        margin-top: 3rem;
        text-align: center;
        border-top: 3px solid {PRIMARY_COLOR};
    }}
    
    .footer-title {{
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: white;
        font-family: 'Playfair Display', serif;
    }}
    
    .footer-links {{
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    
    .footer-link {{
        color: rgba(255,255,255,0.9);
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    
    .footer-link:hover {{
        color: {PRIMARY_LIGHT};
        transform: translateY(-2px);
    }}
    
    .footer-copyright {{
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.2);
    }}
    
    /* ==========================================
       STATUS BADGES
       ========================================== */
    .status-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .status-approved {{
        background: linear-gradient(135deg, {SUCCESS_COLOR}, #059669);
        color: white;
    }}
    .status-pending {{
        background: linear-gradient(135deg, {WARNING_COLOR}, #d97706);
        color: white;
    }}
    
    /* ==========================================
       ADMIN LOGIN - COMPACT
       ========================================== */
    .admin-login-box {{
        max-width: 400px;
        margin: 2rem auto;
        background: {CARD_BACKGROUND};
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 15px 50px rgba(0,0,0,0.1);
        border: 2px solid {BORDER_COLOR};
    }}
    
    /* Info Box */
    .info-box {{
        background: linear-gradient(135deg, {SURFACE_COLOR} 0%, {BACKGROUND_COLOR} 100%);
        border: 2px solid {BORDER_COLOR};
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.8rem 0;
        font-size: 0.85rem;
        color: {TEXT_SECONDARY};
    }}
    
    .info-box.success {{
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        border-color: {SUCCESS_COLOR};
        color: #065f46;
    }}
    
    .info-box.warning {{
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-color: {WARNING_COLOR};
        color: #92400e;
    }}
    
    /* Search bar compact */
    [data-testid="stTextInput"] {{
        margin-bottom: 0.5rem !important;
    }}
</style>

<!-- Floating Particles HTML - Fixed positioning -->
<div class="floating-particles">
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
    <div class="particle"></div>
</div>

<!-- Pink Orbs -->
<div class="pink-orb"></div>
<div class="pink-orb"></div>
""", unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS CONNECTION (Cached) - FIXED
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
# HEADER COMPONENT
# ==========================================

st.markdown(f"""
<div class='header'>
    <div class='logo-container'>
        <div class='logo-icon'>{LOGO_TEXT}</div>
        <div class='brand-text'>
            <div class='brand-name'>{STORE_NAME}</div>
            <div class='brand-tagline'>{STORE_TAGLINE}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# MAIN CONTENT WRAPPER - Ensures visibility
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
    
    # Stats
    total_revenue = orders_df['amount'].sum() if not orders_df.empty else 0
    
    st.markdown(f"""
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
    """, unsafe_allow_html=True)
    
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
        
        col_img, col_vid = st.columns(2)
        with col_img:
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
                        
                        sheet.append_row([new_id, name, price, stock, *image_urls, description, status, variants])
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
                        # Show first image
                        if row.get("image1") and str(row["image1"]).strip():
                            st.image(row["image1"], use_container_width=True)
                        else:
                            st.info("No image")
                        
                        st.markdown(f"**{row['name']}**")
                        st.markdown(f"<span style='color:{PRICE_COLOR};font-weight:700;'>{CURRENCY_SYMBOL}{row['price']}</span>", unsafe_allow_html=True)
                        st.caption(f"Stock: {row.get('stock', 0)}")
                        
                        # FIXED: Convert to Python int for JSON serialization
                        delete_row = int(row["_row"])
                        product_id = int(row["id"])
                        
                        if st.button("🗑️ Delete", key=f"del_{product_id}", use_container_width=True):
                            # Delete images from Cloudinary
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
    
    # Orders Management
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.markdown("### 📦 Recent Orders")
    
    if not orders_df.empty:
        for idx, order in orders_df.iterrows():
            # Emoji status for expander label
            status_icon = "✅" if order.get('status') == STATUS_APPROVED else "⏳"
            status_text = order.get('status', STATUS_PENDING)
            
            # FIXED: Convert numpy types to native Python types
            order_ref = str(order['reference'])
            order_name = str(order['name'])
            order_amount = float(order['amount']) if pd.notna(order['amount']) else 0
            
            expander_label = f"📦 {order_ref} - {order_name} - {CURRENCY_SYMBOL}{order_amount:.0f} - {status_icon} {status_text}"
            
            with st.expander(expander_label):
                col1, col2 = st.columns([2, 1])
                with col1:
                    status_class = "status-approved" if order.get('status') == STATUS_APPROVED else "status-pending"
                    st.markdown(f"""
                        <div style='margin-bottom:15px;'>
                            <span class='status-badge {status_class}'>{order.get('status', STATUS_PENDING)}</span>
                        </div>
                        <div style='line-height:1.8;'>
                            <b style='color:{PRIMARY_COLOR};'>Customer:</b> {order['name']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Phone:</b> {order['phone']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Location:</b> {order['location']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Product:</b> {order['items']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Variant:</b> {order.get('variant', 'Standard')}<br>
                            <b style='color:{PRIMARY_COLOR};'>Quantity:</b> {order['qty']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Amount:</b> {CURRENCY_SYMBOL}{order['amount']}<br>
                            <b style='color:{PRIMARY_COLOR};'>Date:</b> {order['timestamp']}
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # WhatsApp button - FIXED URL spacing
                    clean_phone = ''.join(filter(str.isdigit, str(order['phone'])))
                    if not clean_phone.startswith('233'):
                        clean_phone = '233' + clean_phone.lstrip('0')
                    
                    msg = f"Hi {order['name']}! Your order {order['reference']} for {order['items']} ({CURRENCY_SYMBOL}{order['amount']}) is confirmed! ✨"
                    wa_url = f"https://wa.me/{clean_phone}?text={quote(msg)}"
                    
                    st.markdown(f"""
                        <a href="{wa_url}" target="_blank" style="display:block;background:linear-gradient(135deg,#25D366,#128C7E);color:white;padding:12px;border-radius:10px;text-align:center;text-decoration:none;margin-bottom:12px;font-weight:600;box-shadow:0 4px 15px rgba(37,211,102,0.3);">
                            📱 WhatsApp
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # Approve button
                    order_row = int(order["_row"])
                    if order.get('status') == STATUS_PENDING:
                        if st.button("✅ Approve", key=f"app_{idx}", use_container_width=True):
                            try:
                                client = get_sheets_client()
                                sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                                sheet.update_cell(order_row, 9, STATUS_APPROVED)
                                st.cache_data.clear()
                                st.success("Approved!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    else:
                        st.markdown(f"<div style='text-align:center;padding:12px;background:linear-gradient(135deg,{SUCCESS_COLOR},#059669);color:white;border-radius:10px;font-weight:600;'>✅ Approved</div>", unsafe_allow_html=True)
    else:
        st.info("No orders yet")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# PUBLIC SHOP - PRODUCT GRID WITH CAROUSEL FIX
# ==========================================

products_df = load_products()

st.markdown(f"<div class='section-title'>{TEXT_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

if products_df.empty:
    st.info("✨ New arrivals coming soon! Check back later.")
else:
    # Search - COMPACT SPACING
    if ENABLE_SEARCH:
        search_term = st.text_input("🔍 Search products...", placeholder="Search jewelry, accessories...", label_visibility="collapsed")
        if search_term:
            products_df = products_df[products_df['name'].str.contains(search_term, case=False, na=False)]
    
    # Product Grid - TIGHTENED GAP
    st.markdown("<div class='product-grid'>", unsafe_allow_html=True)
    
    for idx, row in products_df.iterrows():
        # Get images
        images = []
        for img_idx in range(1, 4):
            img_key = f"image{img_idx}"
            if img_key in row and row[img_key] and str(row[img_key]).strip():
                images.append(str(row[img_key]))
        
        # FIX: Use separate session state storage for carousel indices
        product_id = int(row['id'])
        carousel_key = f"carousel_{product_id}"
        
        # Initialize carousel index if not exists
        if carousel_key not in st.session_state.carousel_indices:
            st.session_state.carousel_indices[carousel_key] = 0
        
        # Ensure index is within bounds
        if images:
            st.session_state.carousel_indices[carousel_key] = st.session_state.carousel_indices[carousel_key] % len(images)
        
        # Variant check
        has_variants = row.get('variants') and str(row['variants']).strip()
        
        st.markdown("<div class='product-card'>", unsafe_allow_html=True)
        
        # Image Section
        st.markdown("<div class='product-image-wrapper'>", unsafe_allow_html=True)
        
        if SHOW_STOCK_BADGE:
            badge_class = "badge-in-stock" if row.get('status') == STATUS_IN_STOCK else "badge-out-stock"
            badge_text = STATUS_IN_STOCK if row.get('status') == STATUS_IN_STOCK else STATUS_OUT_OF_STOCK
            st.markdown(f"<div class='stock-badge {badge_class}'>{badge_text}</div>", unsafe_allow_html=True)
        
        # Display image
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
        
        # Carousel Controls - FIX: Use unique keys and proper state management
        if len(images) > 1:
            col_l, col_m, col_r = st.columns([1, 2, 1])
            with col_l:
                # FIX: Unique key using product_id and position
                if st.button("◀", key=f"prev_{product_id}_{idx}", use_container_width=True):
                    new_idx = (st.session_state.carousel_indices[carousel_key] - 1) % len(images)
                    st.session_state.carousel_indices[carousel_key] = new_idx
                    st.rerun()
            with col_m:
                st.markdown(f"<div style='text-align:center;padding:8px 0;font-size:0.8rem;color:#6b7280;font-weight:600;'>{st.session_state.carousel_indices[carousel_key] + 1} / {len(images)}</div>", unsafe_allow_html=True)
            with col_r:
                # FIX: Unique key using product_id and position
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
                    
                    # FIX: Properly clear selected product
                    st.session_state.selected_product = None
                    
                    time.sleep(3)
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
