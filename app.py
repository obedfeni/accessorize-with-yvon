# ==========================================
# ACCESSORIZE WITH YVON — FULL STACK CINEMATIC E-COMMERCE
# Python + Streamlit + Cloudinary + Google Sheets
# ==========================================

import streamlit as st
import gspread
import pandas as pd
import os
import random
import requests
import smtplib
import threading
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cloudinary
import cloudinary.uploader

from config import *

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title=f"{STORE_NAME} | {STORE_TAGLINE}",
    page_icon="💎",
    layout="wide",
    initial_sidebar_bar="collapsed",
    menu_items={}  # Hides the default Streamlit hamburger menu items
)

# Hide ALL Streamlit chrome: menu, footer, deploy button, toolbar
st.markdown("""
<style>
#MainMenu { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
header { visibility: hidden !important; display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
.styles_viewerBadge__1yB5_ { display: none !important; }
#stDecoration { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CLOUDINARY CONFIG
# ==========================================

cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"],
    secure=True
)

# ==========================================
# SECURE ADMIN CREDENTIALS
# ==========================================

_ADMIN_USERNAME = st.secrets["admin"]["username"]
_ADMIN_PASSWORD = st.secrets["admin"]["password"]

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def generate_reference(product_name: str, location: str) -> str:
    """Generate unique order reference."""
    product_code = (product_name[:3]).upper()
    location_code = (location[:3]).upper()
    random_num = random.randint(10 ** (REFERENCE_LENGTH - 1), (10 ** REFERENCE_LENGTH) - 1)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{random_num}"


def upload_to_cloudinary(file, filename: str) -> str:
    """Upload image to Cloudinary; raises RuntimeError on failure."""
    file.seek(0)
    clean = "".join(
        c for c in filename.replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
        if c.isalnum() or c in ("_", "-")
    )
    public_id = f"accessorize_yvon/{clean}_{int(time.time())}"
    result = cloudinary.uploader.upload(
        file,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    url = result.get("secure_url")
    if not url:
        raise RuntimeError("Cloudinary returned no URL.")
    return url


def delete_from_cloudinary(image_url: str) -> bool:
    """Delete image from Cloudinary by its URL."""
    try:
        if "cloudinary.com" not in image_url:
            return False
        parts = image_url.split("/")
        upload_idx = parts.index("upload")
        public_id = "/".join(parts[upload_idx + 2:]).rsplit(".", 1)[0]
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as exc:
        print(f"Cloudinary delete error: {exc}")
        return False


def send_notifications_async(
    product_name, variant, customer_name, phone,
    location, qty, total, reference, timestamp
):
    """Fire-and-forget Telegram + Email notifications."""
    def _send():
        # Telegram
        try:
            token = st.secrets.get("telegram", {}).get("bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = st.secrets.get("telegram", {}).get("chat_id") or os.environ.get("TELEGRAM_CHAT_ID")
            if token and chat_id:
                message = TELEGRAM_TEMPLATE.format(
                    product_name=product_name, variant=variant,
                    customer_name=customer_name, phone=phone,
                    location=location, quantity=qty, currency=CURRENCY_SYMBOL,
                    total=total, reference=reference, timestamp=timestamp,
                )
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                    timeout=5,
                )
        except Exception as exc:
            print(f"Telegram error: {exc}")

        # Email
        try:
            admin_email = st.secrets.get("email", {}).get("address") or os.environ.get("ADMIN_EMAIL")
            password = st.secrets.get("email", {}).get("app_password") or os.environ.get("EMAIL_APP_PASSWORD")
            if admin_email and password:
                msg = MIMEMultipart("alternative")
                msg["From"] = admin_email
                msg["To"] = admin_email
                msg["Subject"] = f"New Order: {reference}"
                html_body = f"""
                <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
                <div style='background:linear-gradient(135deg,{PRIMARY_COLOR},{PRIMARY_LIGHT});
                            color:white;padding:30px;text-align:center;border-radius:15px 15px 0 0;'>
                    <h1>🛍️ New Order Received!</h1>
                </div>
                <div style='background:#fff5f5;padding:30px;border:1px solid {BORDER_COLOR};'>
                    <p><strong>Product:</strong> {product_name}</p>
                    <p><strong>Variant:</strong> {variant}</p>
                    <p><strong>Customer:</strong> {customer_name}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Quantity:</strong> {qty}</p>
                    <p><strong>Total:</strong> {CURRENCY_SYMBOL}{total}</p>
                    <p><strong>Reference:</strong> {reference}</p>
                    <p><strong>Time:</strong> {timestamp}</p>
                </div></body></html>
                """
                msg.attach(MIMEText(html_body, "html"))
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(admin_email, password)
                    server.send_message(msg)
        except Exception as exc:
            print(f"Email error: {exc}")

    threading.Thread(target=_send, daemon=True).start()

# ==========================================
# SESSION STATE DEFAULTS
# ==========================================

_defaults = {
    "admin_logged": False,
    "show_admin_login": False,
    "selected_product": None,
    "carousel_indices": {},
    "active_category": "All",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# URL-param admin trigger
if st.query_params.get("page") == "admin":
    st.session_state.show_admin_login = True

# ==========================================
# FULL CSS
# ==========================================

_logo_radius = "50%" if LOGO_SHAPE == "circle" else "16px"

ALL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

.stAppViewBlockContainer, .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}

body, .stApp {{
    background: {BACKGROUND_COLOR} !important;
    font-family: 'Inter', sans-serif;
    overflow-x: hidden;
    color: {TEXT_PRIMARY};
}}

/* PARTICLES */
.gold-particles {{ position:fixed; top:0; left:0; width:100%; height:100%;
    pointer-events:none; z-index:0; overflow:hidden; }}
.gold-particle {{ position:absolute; width:6px; height:6px;
    background:radial-gradient(circle,{PRIMARY_LIGHT},{PRIMARY_COLOR});
    border-radius:50%; animation:floatParticle linear infinite; opacity:0; }}
.gold-particle:nth-child(1)  {{ left:10%; animation-duration:8s;  animation-delay:0s;   width:4px; height:4px; }}
.gold-particle:nth-child(2)  {{ left:20%; animation-duration:12s; animation-delay:2s;   width:6px; height:6px; }}
.gold-particle:nth-child(3)  {{ left:30%; animation-duration:9s;  animation-delay:4s;   width:3px; height:3px; }}
.gold-particle:nth-child(4)  {{ left:40%; animation-duration:15s; animation-delay:1s;   width:5px; height:5px; }}
.gold-particle:nth-child(5)  {{ left:50%; animation-duration:10s; animation-delay:3s;   width:4px; height:4px; }}
.gold-particle:nth-child(6)  {{ left:60%; animation-duration:13s; animation-delay:5s;   width:7px; height:7px; }}
.gold-particle:nth-child(7)  {{ left:70%; animation-duration:11s; animation-delay:0.5s; width:3px; height:3px; }}
.gold-particle:nth-child(8)  {{ left:80%; animation-duration:14s; animation-delay:2.5s; width:5px; height:5px; }}
.gold-particle:nth-child(9)  {{ left:90%; animation-duration:8s;  animation-delay:1.5s; width:4px; height:4px; }}
.gold-particle:nth-child(10) {{ left:25%; animation-duration:16s; animation-delay:3.5s; width:6px; height:6px; }}
@keyframes floatParticle {{
    0%   {{ transform:translateY(100vh) rotate(0deg);   opacity:0; }}
    10%  {{ opacity:0.8; }}
    90%  {{ opacity:0.6; }}
    100% {{ transform:translateY(-100px) rotate(720deg); opacity:0; }}
}}

/* ORBS */
.pink-orb {{ position:fixed; border-radius:50%; filter:blur(80px);
    pointer-events:none; z-index:0; animation:orbPulse 6s ease-in-out infinite; }}
.pink-orb:nth-child(1) {{ width:400px; height:400px;
    background:radial-gradient(circle,rgba(236,72,153,.15),transparent);
    top:-100px; right:-100px; }}
.pink-orb:nth-child(2) {{ width:300px; height:300px;
    background:radial-gradient(circle,rgba(217,119,6,.1),transparent);
    bottom:200px; left:-80px; animation-delay:3s; }}
.pink-orb:nth-child(3) {{ width:250px; height:250px;
    background:radial-gradient(circle,rgba(245,158,11,.1),transparent);
    top:50%; left:50%; animation-delay:1.5s; }}
@keyframes orbPulse {{
    0%,100% {{ transform:scale(1);   opacity:0.8; }}
    50%      {{ transform:scale(1.2); opacity:1;   }}
}}

/* HERO */
.hero-section {{
    position:relative;
    background:linear-gradient(135deg,{PRIMARY_DARK} 0%,{PRIMARY_COLOR} 40%,{ACCENT_COLOR} 100%);
    padding:3rem 1.5rem 4rem; text-align:center; overflow:hidden; z-index:1;
}}
.hero-shimmer {{
    position:absolute; top:0; left:-100%; width:100%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.15),transparent);
    animation:heroShimmer 4s ease-in-out infinite;
}}
@keyframes heroShimmer {{ 0% {{ left:-100%; }} 100% {{ left:200%; }} }}
.hero-content {{
    position:relative; z-index:2;
    display:flex; flex-direction:column; align-items:center; gap:1.5rem;
}}
@media(min-width:768px) {{
    .hero-content {{ flex-direction:row; justify-content:center; gap:2.5rem; }}
    .hero-section {{ padding:4rem 3rem 5rem; }}
}}
.hero-logo {{
    width:90px; height:90px;
    background:rgba(255,255,255,.2); backdrop-filter:blur(10px);
    border-radius:{_logo_radius};
    display:flex; align-items:center; justify-content:center;
    font-size:2rem; font-weight:700; color:white;
    border:3px solid rgba(255,255,255,.4);
    box-shadow:0 10px 40px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.3);
    animation:logoFloat 4s ease-in-out infinite; flex-shrink:0;
    font-family:'Playfair Display',serif;
}}
@media(min-width:768px) {{ .hero-logo {{ width:110px; height:110px; font-size:2.5rem; }} }}
@keyframes logoFloat {{
    0%,100% {{ transform:translateY(0) rotate(-2deg); }}
    50%      {{ transform:translateY(-10px) rotate(2deg); }}
}}
.hero-text {{ color:white; text-align:center; }}
@media(min-width:768px) {{ .hero-text {{ text-align:left; }} }}
.hero-title {{
    font-size:1.8rem; font-weight:700; margin-bottom:.5rem;
    font-family:'Playfair Display',serif;
    text-shadow:0 2px 10px rgba(0,0,0,.2); line-height:1.2;
}}
@media(min-width:768px) {{ .hero-title {{ font-size:2.8rem; }} }}
.hero-tagline {{ font-size:1rem; opacity:.9; margin-bottom:1rem; font-weight:500; }}
@media(min-width:768px) {{ .hero-tagline {{ font-size:1.2rem; }} }}
.hero-badge {{
    display:inline-block;
    background:rgba(255,255,255,.2); backdrop-filter:blur(10px);
    border:1px solid rgba(255,255,255,.4);
    padding:.5rem 1.5rem; border-radius:50px;
    font-size:.9rem; font-weight:600; letter-spacing:1px;
    animation:badgePulse 2s ease-in-out infinite;
}}
@keyframes badgePulse {{
    0%,100% {{ box-shadow:0 0 0 0 rgba(255,255,255,.3); }}
    50%      {{ box-shadow:0 0 0 8px rgba(255,255,255,0); }}
}}

/* MAIN */
.main-content {{ max-width:1400px; margin:0 auto; padding:0 1rem; position:relative; z-index:1; }}
@media(min-width:768px) {{ .main-content {{ padding:0 2rem; }} }}

/* SECTION TITLE */
.section-title {{
    font-family:'Playfair Display',serif; font-size:2rem; font-weight:600;
    color:{TEXT_PRIMARY}; text-align:center; margin:3rem 0 2rem;
    position:relative; letter-spacing:-.5px;
}}
.section-title::after {{
    content:''; display:block; width:60px; height:3px;
    background:linear-gradient(90deg,{PRIMARY_COLOR},{PRIMARY_LIGHT});
    margin:1rem auto 0; border-radius:2px;
}}
@media(min-width:768px) {{ .section-title {{ font-size:2.5rem; margin:4rem 0 3rem; }} }}

/* PRODUCT GRID */
.product-grid {{
    display:grid; grid-template-columns:repeat(2,1fr);
    gap:1.5rem; padding:0 0 3rem;
}}
@media(min-width:640px)  {{ .product-grid {{ gap:2rem; }} }}
@media(min-width:768px)  {{ .product-grid {{ grid-template-columns:repeat(3,1fr); gap:2.5rem; }} }}
@media(min-width:1200px) {{ .product-grid {{ grid-template-columns:repeat(4,1fr); gap:3rem; }} }}

/* PRODUCT CARD */
.product-card {{
    background:{CARD_BACKGROUND}; border-radius:20px; overflow:hidden;
    box-shadow:0 4px 20px rgba(0,0,0,.04);
    transition:all .5s cubic-bezier(.22,1,.36,1);
    border:1px solid {BORDER_COLOR};
    position:relative; display:flex; flex-direction:column; height:100%;
    animation:fadeInUp .6s ease forwards; opacity:0;
}}
.product-grid > div:nth-child(1) .product-card {{ animation-delay:.05s; }}
.product-grid > div:nth-child(2) .product-card {{ animation-delay:.10s; }}
.product-grid > div:nth-child(3) .product-card {{ animation-delay:.15s; }}
.product-grid > div:nth-child(4) .product-card {{ animation-delay:.20s; }}
.product-grid > div:nth-child(5) .product-card {{ animation-delay:.25s; }}
.product-grid > div:nth-child(6) .product-card {{ animation-delay:.30s; }}
@keyframes fadeInUp {{
    from {{ opacity:0; transform:translateY(20px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
.product-card:hover {{
    transform:translateY(-8px);
    box-shadow:0 20px 40px rgba(217,119,6,.12);
    border-color:rgba(217,119,6,.3);
}}
.product-image-wrapper {{
    position:relative; width:100%; aspect-ratio:1/1;
    background:linear-gradient(135deg,#fafafa 0%,#f5f5f5 100%);
    overflow:hidden; border-bottom:1px solid {BORDER_COLOR};
}}
.product-image-container {{
    width:100%; height:100%;
    display:flex; align-items:center; justify-content:center; padding:1.5rem;
    transition:transform .6s cubic-bezier(.22,1,.36,1);
}}
.product-card:hover .product-image-container {{ transform:scale(1.05); }}
.product-image {{
    max-width:100%; max-height:100%; width:auto; height:auto;
    object-fit:contain; border-radius:12px;
    transition:all .5s ease;
    filter:drop-shadow(0 8px 16px rgba(0,0,0,.08));
}}
.product-card:hover .product-image {{ filter:drop-shadow(0 12px 24px rgba(0,0,0,.12)); }}

/* STOCK BADGE */
.stock-badge {{
    position:absolute; top:12px; left:12px;
    padding:.4rem .9rem; border-radius:20px;
    font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.5px;
    z-index:10; backdrop-filter:blur(10px); border:1px solid rgba(255,255,255,.3);
}}
.badge-in-stock  {{ background:rgba(16,185,129,.9);  color:white; }}
.badge-out-stock {{ background:rgba(239,68,68,.9);   color:white; }}

/* CAROUSEL */
.carousel-dots {{
    position:absolute; bottom:12px; left:50%; transform:translateX(-50%);
    display:flex; gap:6px; z-index:10;
    background:rgba(255,255,255,.9); padding:6px 10px; border-radius:20px;
    backdrop-filter:blur(4px); border:1px solid rgba(0,0,0,.05);
}}
.carousel-dot {{
    width:6px; height:6px; border-radius:50%;
    background:rgba(0,0,0,.2); border:none; cursor:pointer;
    transition:all .3s ease; padding:0;
}}
.carousel-dot.active {{ background:{PRIMARY_COLOR}; width:18px; border-radius:3px; }}

/* PRODUCT CONTENT */
.product-content {{
    padding:1.25rem; display:flex; flex-direction:column;
    flex-grow:1; gap:.4rem;
}}
@media(min-width:768px) {{ .product-content {{ padding:1.5rem; }} }}
.product-category {{
    font-size:.7rem; color:{PRIMARY_COLOR}; font-weight:600;
    text-transform:uppercase; letter-spacing:1px;
}}
.product-name {{
    font-family:'Playfair Display',serif; font-size:1.05rem; font-weight:600;
    color:{TEXT_PRIMARY}; line-height:1.3; margin-bottom:.3rem;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
    overflow:hidden; min-height:2.6rem;
}}
@media(min-width:768px) {{ .product-name {{ font-size:1.15rem; }} }}
.product-description {{
    font-size:.8rem; color:{TEXT_SECONDARY}; line-height:1.5;
    display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
    overflow:hidden; margin-bottom:.5rem; flex-grow:1;
}}
.product-meta {{
    display:flex; justify-content:space-between; align-items:center;
    margin-top:auto; padding-top:.75rem; border-top:1px solid {BORDER_COLOR};
}}
.product-price {{
    font-size:1.15rem; color:{PRICE_COLOR}; font-weight:700;
    display:flex; align-items:baseline; gap:.2rem;
}}
@media(min-width:768px) {{ .product-price {{ font-size:1.25rem; }} }}
.price-currency {{ font-size:.8rem; color:{TEXT_MUTED}; font-weight:500; }}
.variant-badge {{
    font-size:.7rem; color:{TEXT_SECONDARY}; background:{SURFACE_COLOR};
    padding:.25rem .7rem; border-radius:12px; font-weight:500; border:1px solid {BORDER_COLOR};
}}
.product-cta {{ margin-top:1rem; }}

/* BUTTONS */
.stButton > button {{
    background:linear-gradient(135deg,{PRIMARY_COLOR} 0%,{PRIMARY_DARK} 100%) !important;
    color:white !important; border:none !important; border-radius:12px !important;
    padding:.875rem 1.5rem !important; font-weight:600 !important; font-size:.9rem !important;
    transition:all .3s cubic-bezier(.22,1,.36,1) !important;
    box-shadow:0 4px 12px rgba(217,119,6,.25) !important;
    width:100% !important; text-transform:none !important; letter-spacing:.5px !important;
}}
.stButton > button:hover {{
    transform:translateY(-2px) !important;
    box-shadow:0 8px 20px rgba(217,119,6,.35) !important;
}}
.stButton > button:active {{ transform:translateY(0) !important; }}
.stButton > button:disabled {{
    background:#e5e7eb !important; color:#9ca3af !important;
    box-shadow:none !important; cursor:not-allowed !important;
}}
.admin-btn-container button {{
    padding:.6rem 1.2rem !important; font-size:.85rem !important;
    width:auto !important; min-width:120px !important;
    background:rgba(255,255,255,.9) !important; color:{TEXT_PRIMARY} !important;
    border:1px solid {BORDER_COLOR} !important; border-radius:25px !important; font-weight:500 !important;
}}
.admin-btn-container button:hover {{
    background:{PRIMARY_COLOR} !important; color:white !important;
    border-color:{PRIMARY_COLOR} !important;
}}

/* FORM INPUTS */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {{
    background-color:{CARD_BACKGROUND} !important; color:{TEXT_PRIMARY} !important;
    border:2px solid {BORDER_COLOR} !important; border-radius:16px !important;
    padding:1rem 1.2rem !important; font-size:1rem !important;
    transition:all .4s cubic-bezier(.22,1,.36,1) !important;
    font-family:'Inter',sans-serif;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {{
    border-color:{PRIMARY_COLOR} !important;
    box-shadow:0 0 0 4px rgba(217,119,6,.15) !important;
    outline:none !important; transform:translateY(-2px);
}}
.stTextInput > label, .stNumberInput > label,
.stTextArea > label, .stSelectbox > label {{
    color:{TEXT_PRIMARY} !important; font-weight:600 !important;
    font-size:.95rem !important; margin-bottom:.5rem !important;
    font-family:'Inter',sans-serif;
}}

/* ADMIN DASHBOARD */
.admin-card {{
    background:rgba(255,255,255,.95); backdrop-filter:blur(20px);
    border-radius:24px; padding:2rem; margin-bottom:2rem;
    box-shadow:0 10px 40px rgba(0,0,0,.08); border:1px solid rgba(255,255,255,.6);
}}
.stat-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-bottom:2rem; }}
@media(min-width:768px) {{ .stat-grid {{ gap:1.5rem; }} }}
.stat-box {{
    background:linear-gradient(135deg,{PRIMARY_COLOR} 0%,{PRIMARY_LIGHT} 100%);
    color:white; padding:1.5rem 1rem; border-radius:20px; text-align:center;
    box-shadow:0 15px 35px {SHADOW_COLOR};
    transition:all .4s cubic-bezier(.22,1,.36,1);
    position:relative; overflow:hidden;
}}
.stat-box::before {{
    content:''; position:absolute; top:-50%; left:-50%; width:200%; height:200%;
    background:radial-gradient(circle,rgba(255,255,255,.3) 0%,transparent 70%);
    animation:statPulse 3s ease-in-out infinite;
}}
@keyframes statPulse {{
    0%,100% {{ transform:scale(1);   opacity:.5; }}
    50%      {{ transform:scale(1.1); opacity:.8; }}
}}
.stat-box:hover {{ transform:translateY(-5px) scale(1.02); }}
.stat-number {{
    font-size:1.8rem; font-weight:700; margin-bottom:.3rem;
    line-height:1; position:relative; z-index:2;
    font-family:'Playfair Display',serif;
}}
@media(min-width:768px) {{ .stat-number {{ font-size:2.2rem; }} }}
.stat-label {{
    font-size:.75rem; opacity:.95; font-weight:600;
    text-transform:uppercase; letter-spacing:1px; position:relative; z-index:2;
}}

/* ORDER FORM */
.order-container {{
    background:rgba(255,255,255,.95); backdrop-filter:blur(20px);
    border-radius:32px; padding:2rem 1.5rem; margin:2rem auto;
    max-width:800px;
    box-shadow:0 20px 60px rgba(0,0,0,.1); border:2px solid {BORDER_COLOR};
    animation:slideUp .6s ease;
}}
@keyframes slideUp {{
    from {{ opacity:0; transform:translateY(30px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
@media(min-width:768px) {{ .order-container {{ padding:3rem; margin:3rem auto; }} }}
.order-summary {{
    background:linear-gradient(135deg,{SURFACE_COLOR} 0%,{BACKGROUND_COLOR} 100%);
    border:2px solid {BORDER_COLOR}; border-radius:20px;
    padding:1.5rem; margin:1.5rem 0; position:relative; overflow:hidden;
}}
.order-summary::before {{ content:'✨'; position:absolute; top:10px; right:20px;
    font-size:40px; opacity:.1; }}
.order-summary-title {{
    font-family:'Playfair Display',serif; font-size:1.1rem; font-weight:600;
    color:{TEXT_PRIMARY}; margin-bottom:1rem; padding-bottom:.8rem;
    border-bottom:2px solid {BORDER_COLOR};
}}
.order-summary-row {{
    display:flex; justify-content:space-between;
    margin-bottom:.6rem; font-size:.95rem; color:{TEXT_SECONDARY};
}}
.order-summary-total {{
    font-size:1.5rem; font-weight:700; color:{PRICE_COLOR};
    margin-top:1rem; padding-top:1rem; border-top:2px solid {BORDER_COLOR};
    font-family:'Playfair Display',serif;
}}

/* SUCCESS */
.success-message {{
    background:linear-gradient(135deg,#d1fae5 0%,#a7f3d0 100%);
    border:3px solid {SUCCESS_COLOR}; color:#065f46;
    padding:2.5rem 2rem; border-radius:24px; margin:2rem 0; text-align:center;
    box-shadow:0 20px 50px rgba(16,185,129,.2);
    position:relative; overflow:hidden;
    animation:successPop .6s cubic-bezier(.22,1,.36,1) forwards;
}}
@keyframes successPop {{
    0%   {{ transform:scale(.8); opacity:0; }}
    100% {{ transform:scale(1);  opacity:1; }}
}}
.success-message::before {{ content:'🎉'; position:absolute; top:-20px; right:-20px;
    font-size:100px; opacity:.15; animation:floatEmoji 3s ease-in-out infinite; }}
.success-message::after  {{ content:'✨'; position:absolute; bottom:-10px; left:-10px;
    font-size:60px;  opacity:.15; animation:floatEmoji 3s ease-in-out infinite reverse; }}
@keyframes floatEmoji {{
    0%,100% {{ transform:translateY(0) rotate(0deg); }}
    50%      {{ transform:translateY(-20px) rotate(10deg); }}
}}
.success-title {{
    font-family:'Playfair Display',serif; font-size:1.6rem; font-weight:700;
    margin-bottom:1rem; position:relative; z-index:1;
}}

/* ADMIN LOGIN */
.admin-login-box {{
    max-width:450px; margin:3rem auto;
    background:rgba(255,255,255,.95); backdrop-filter:blur(20px);
    border-radius:32px; padding:2.5rem;
    box-shadow:0 25px 80px rgba(0,0,0,.12); border:2px solid {BORDER_COLOR};
    animation:loginEntrance .8s cubic-bezier(.22,1,.36,1) forwards;
}}
@keyframes loginEntrance {{
    0%   {{ opacity:0; transform:translateY(40px) scale(.95); }}
    100% {{ opacity:1; transform:translateY(0)    scale(1);   }}
}}

/* VARIANT SELECTOR */
.variant-selector {{
    margin:1.5rem 0; padding:1.5rem;
    background:{SURFACE_COLOR}; border-radius:16px; border:1px solid {BORDER_COLOR};
}}
.variant-label {{ font-size:.95rem; font-weight:600; color:{TEXT_PRIMARY}; margin-bottom:1rem; display:block; }}

/* EMPTY STATE */
.empty-state {{ text-align:center; padding:4rem 2rem; color:{TEXT_SECONDARY}; }}
.empty-state-icon {{ font-size:4rem; margin-bottom:1rem; opacity:.5; }}

/* FOOTER */
.footer {{
    background:linear-gradient(135deg,{TEXT_SECONDARY} 0%,{PRIMARY_COLOR} 100%);
    color:white; padding:3rem 2rem; border-radius:40px 40px 0 0;
    margin-top:4rem; text-align:center;
    border-top:4px solid {BORDER_COLOR}; position:relative; overflow:hidden;
}}
.footer::before {{
    content:''; position:absolute; top:0; left:0; width:100%; height:100%;
    background-image:radial-gradient(circle,rgba(255,255,255,.05) 1px,transparent 1px);
    background-size:30px 30px; opacity:.5;
}}
.footer-title {{ font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:600;
    margin-bottom:1.5rem; color:white; position:relative; z-index:1; }}
.footer-links {{ display:flex; flex-wrap:wrap; justify-content:center; gap:1.5rem;
    margin-bottom:1.5rem; position:relative; z-index:1; }}
.footer-link {{ color:rgba(255,255,255,.9); text-decoration:none; font-size:.95rem;
    font-weight:500; transition:all .3s cubic-bezier(.22,1,.36,1);
    display:flex; align-items:center; gap:.5rem; }}
.footer-link:hover {{ color:{PRIMARY_LIGHT}; transform:translateY(-3px); }}
.footer-copyright {{ font-size:.85rem; opacity:.7; margin-top:1.5rem; padding-top:1.5rem;
    border-top:1px solid rgba(255,255,255,.2); position:relative; z-index:1; }}

@media(max-width:640px) {{
    .section-title {{ font-size:1.6rem; margin:2rem 0 1.5rem; }}
    .hero-title {{ font-size:1.5rem; }} .hero-tagline {{ font-size:.9rem; }}
    .hero-logo {{ width:70px; height:70px; font-size:1.5rem; }}
    .product-content {{ padding:1rem; }}
    .product-name {{ font-size:.95rem; min-height:2.4rem; }}
    .product-price {{ font-size:1.05rem; }}
    .stat-number {{ font-size:1.5rem; }} .stat-label {{ font-size:.7rem; }}
}}
</style>
"""

st.markdown(ALL_CSS, unsafe_allow_html=True)

# ==========================================
# BACKGROUND DECORATIONS
# ==========================================

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

# ==========================================
# HERO
# ==========================================

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

# ==========================================
# MAIN CONTENT WRAPPER
# ==========================================

st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# ==========================================
# ADMIN TOGGLE BUTTON
# ==========================================

if SHOW_ADMIN_BUTTON:
    _c1, _c2, _c3 = st.columns([6, 1, 1])
    with _c3:
        st.markdown("<div class='admin-btn-container'>", unsafe_allow_html=True)
        if st.button("🔐 Admin", key="admin_toggle"):
            st.session_state.show_admin_login = not st.session_state.show_admin_login
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ADMIN LOGIN FORM
# ==========================================

if st.session_state.show_admin_login and not st.session_state.admin_logged:
    st.markdown("<div class='admin-login-box'>", unsafe_allow_html=True)
    st.markdown(f"### 🔐 {TEXT_ADMIN_LOGIN}")
    st.markdown("Enter your credentials to access the dashboard.")

    with st.form("admin_login_form", clear_on_submit=True):
        username_input = st.text_input("Username", placeholder="admin")
        password_input = st.text_input("Password", type="password", placeholder="••••••••")
        col_login, col_cancel = st.columns(2)
        with col_login:
            login_submitted = st.form_submit_button("🔓 Login", use_container_width=True)
        with col_cancel:
            cancel_submitted = st.form_submit_button("Cancel", use_container_width=True)

        if login_submitted:
            # Constant-time comparison to prevent timing attacks
            import hmac
            user_match = hmac.compare_digest(username_input.strip(), _ADMIN_USERNAME)
            pass_match = hmac.compare_digest(password_input, _ADMIN_PASSWORD)
            if user_match and pass_match:
                st.session_state.admin_logged = True
                st.session_state.show_admin_login = False
                st.success("✅ Welcome back!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Access denied.")

        if cancel_submitted:
            st.session_state.show_admin_login = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # close main-content
    st.stop()

# ==========================================
# GOOGLE SHEETS CONNECTION
# ==========================================

@st.cache_resource(ttl=3600, show_spinner=False)
def get_sheets_client():
    """Initialize Google Sheets client."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
        return gspread.authorize(creds)
    except Exception as exc:
        st.error(f"Failed to connect to Google Sheets: {exc}")
        st.stop()


@st.cache_data(ttl=CACHE_TTL_PRODUCTS, show_spinner=False)
def load_products():
    """Load products from Google Sheets."""
    try:
        client = get_sheets_client()
        sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
        records = sheet.get_all_records()
        for i, r in enumerate(records, start=2):
            r["_row"] = i
        return pd.DataFrame(records)
    except Exception as exc:
        st.error(f"Failed to load products: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def load_orders():
    """Load orders from Google Sheets."""
    try:
        client = get_sheets_client()
        sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as exc:
        st.error(f"Failed to load orders: {exc}")
        return pd.DataFrame()

# ==========================================
# ADMIN DASHBOARD
# ==========================================

if st.session_state.admin_logged:
    st.markdown(f"<div class='section-title'>{TEXT_ADMIN_DASHBOARD}</div>", unsafe_allow_html=True)

    products_df = load_products()
    orders_df = load_orders()
    total_revenue = (
        orders_df["amount"].sum()
        if not orders_df.empty and "amount" in orders_df.columns
        else 0
    )

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

    # Orders table
    if not orders_df.empty:
        st.markdown("### 📋 Recent Orders")
        st.dataframe(orders_df, use_container_width=True)

    # Logout
    _, _logout_col = st.columns([3, 1])
    with _logout_col:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.cache_data.clear()
            st.rerun()

    # ---- ADD PRODUCT ----
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.markdown("### ➕ Add New Product")

    with st.form("add_product", clear_on_submit=True):
        _a1, _a2 = st.columns(2)
        with _a1:
            name = st.text_input("Product Name *", placeholder="e.g., Gold Necklace Set")
            price = st.number_input(f"Base Price ({CURRENCY_SYMBOL}) *", min_value=0, value=50)
        with _a2:
            stock = st.number_input("Stock Quantity *", min_value=0, value=10)
            variants = st.text_input("Variants (Optional)", placeholder="Small:50, Medium:75, Large:100")

        description = st.text_area("Description", placeholder="Describe your product...", height=100)
        images = st.file_uploader(
            f"Product Images (Max {MAX_PRODUCT_IMAGES})",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
        )

        add_submitted = st.form_submit_button("🚀 Add Product", use_container_width=True)

        if add_submitted:
            if not name:
                st.warning("⚠️ Product name is required.")
            elif not images:
                st.warning("⚠️ At least one image is required.")
            else:
                image_urls = []
                upload_ok = True
                with st.spinner("Uploading images to Cloudinary..."):
                    for i, img in enumerate(images[:MAX_PRODUCT_IMAGES], 1):
                        try:
                            url = upload_to_cloudinary(img, f"{name.replace(' ', '_')}_{i}")
                            image_urls.append(url)
                        except RuntimeError as exc:
                            st.error(f"Image {i} upload failed: {exc}")
                            upload_ok = False
                            break

                if upload_ok and image_urls:
                    while len(image_urls) < MAX_PRODUCT_IMAGES:
                        image_urls.append("")
                    try:
                        client = get_sheets_client()
                        sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                        new_id = 1
                        if not products_df.empty and "id" in products_df.columns:
                            try:
                                new_id = int(products_df["id"].max()) + 1
                            except Exception:
                                pass
                        status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK
                        sheet.append_row([
                            new_id, name, price, stock,
                            image_urls[0], image_urls[1], image_urls[2],
                            description, status, variants,
                        ])
                        st.cache_data.clear()
                        st.success("✅ Product added successfully!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to save product: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- MANAGE PRODUCTS ----
    st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
    st.markdown("### 🗂️ Manage Products")

    if not products_df.empty:
        for _i in range(0, len(products_df), 3):
            _cols = st.columns(3)
            for _j, _col in enumerate(_cols):
                if _i + _j < len(products_df):
                    _row = products_df.iloc[_i + _j]
                    with _col:
                        if _row.get("image1") and str(_row["image1"]).strip():
                            st.image(str(_row["image1"]).strip(), use_container_width=True)
                        else:
                            st.info("No image")
                        st.markdown(f"**{_row['name']}**")
                        st.markdown(
                            f"<span style='color:{PRICE_COLOR};font-weight:700;'>"
                            f"{CURRENCY_SYMBOL}{_row['price']}</span>",
                            unsafe_allow_html=True,
                        )
                        st.caption(f"Stock: {_row.get('stock', 0)} | {_row.get('status', 'Unknown')}")
                        if st.button("🗑️ Delete", key=f"del_{int(_row['id'])}"):
                            for _img_key in ["image1", "image2", "image3"]:
                                if _row.get(_img_key) and "cloudinary.com" in str(_row[_img_key]):
                                    delete_from_cloudinary(str(_row[_img_key]))
                            try:
                                client = get_sheets_client()
                                sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
                                sheet.delete_rows(int(_row["_row"]))
                                st.cache_data.clear()
                                st.success("Deleted!")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Delete error: {exc}")
    else:
        st.info("No products yet. Add your first product above!")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # close main-content
    st.stop()

# ==========================================
# PUBLIC SHOP
# ==========================================

products_df = load_products()

st.markdown(f"<div class='section-title'>{TEXT_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

# Search
if ENABLE_SEARCH:
    _s1, _s2, _s3 = st.columns([1, 3, 1])
    with _s2:
        search_term = st.text_input(
            "Search",
            placeholder="🔍 Search for jewelry, necklaces, earrings...",
            label_visibility="collapsed",
        )
    if search_term and not products_df.empty:
        products_df = products_df[
            products_df["name"].str.contains(search_term, case=False, na=False)
            | products_df["description"].str.contains(search_term, case=False, na=False)
        ]

# Category filter
_categories = ["All", "Necklaces", "Earrings", "Bracelets", "Rings"]
_filter_cols = st.columns(len(_categories))
for _i, _cat in enumerate(_categories):
    with _filter_cols[_i]:
        _is_active = st.session_state.active_category == _cat
        if st.button(
            _cat,
            key=f"cat_{_cat}",
            use_container_width=True,
            type="primary" if _is_active else "secondary",
        ):
            st.session_state.active_category = _cat
            st.rerun()

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# Product Grid
if products_df.empty:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">💎</div>
        <h3>No products found</h3>
        <p>New arrivals coming soon! Check back later.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='product-grid'>", unsafe_allow_html=True)

    for _idx, _row in products_df.iterrows():
        _product_id = int(_row["id"])
        _images = []
        for _n in range(1, MAX_PRODUCT_IMAGES + 1):
            _key = f"image{_n}"
            if _key in _row and _row[_key] and str(_row[_key]).strip():
                _images.append(str(_row[_key]).strip())

        _carousel_key = f"carousel_{_product_id}"
        if _carousel_key not in st.session_state.carousel_indices:
            st.session_state.carousel_indices[_carousel_key] = 0

        _current_idx = (
            st.session_state.carousel_indices[_carousel_key] % len(_images)
            if _images else 0
        )
        _has_variants = _row.get("variants") and str(_row["variants"]).strip()
        _is_in_stock = _row.get("status") == STATUS_IN_STOCK

        # Card HTML
        _card = "<div class='product-card'>"
        _card += "<div class='product-image-wrapper'>"
        if SHOW_STOCK_BADGE:
            _badge_cls = "badge-in-stock" if _is_in_stock else "badge-out-stock"
            _badge_txt = STATUS_IN_STOCK if _is_in_stock else STATUS_OUT_OF_STOCK
            _card += f"<div class='stock-badge {_badge_cls}'>{_badge_txt}</div>"
        if _images:
            _card += f"""
            <div class='product-image-container'>
                <img src='{_images[_current_idx]}' class='product-image'
                     loading='lazy' alt='{_row['name']}'>
            </div>"""
            if len(_images) > 1:
                _card += "<div class='carousel-dots'>"
                for _di in range(len(_images)):
                    _dc = "active" if _di == _current_idx else ""
                    _card += f"<div class='carousel-dot {_dc}'></div>"
                _card += "</div>"
        else:
            _card += "<div class='product-image-container' style='color:#9ca3af;font-size:.9rem;'>📷 No Image</div>"
        _card += "</div>"  # image-wrapper

        _card += "<div class='product-content'>"
        if _row.get("category"):
            _card += f"<div class='product-category'>{_row['category']}</div>"
        _card += f"<h3 class='product-name'>{_row['name']}</h3>"
        if _row.get("description"):
            _desc = str(_row["description"])
            if len(_desc) > 60:
                _desc = _desc[:60] + "…"
            _card += f"<p class='product-description'>{_desc}</p>"
        _card += "<div class='product-meta'>"
        _card += f"<div class='product-price'><span class='price-currency'>{CURRENCY_SYMBOL}</span>{_row['price']}</div>"
        if _has_variants:
            _card += "<span class='variant-badge'>Options Available</span>"
        _card += "</div></div></div>"  # meta / content / card

        st.markdown(_card, unsafe_allow_html=True)

        # Carousel nav
        if len(_images) > 1:
            _cc1, _cc2, _cc3 = st.columns([1, 2, 1])
            with _cc1:
                if st.button("‹", key=f"prev_{_product_id}_{_idx}", use_container_width=True):
                    st.session_state.carousel_indices[_carousel_key] = (_current_idx - 1) % len(_images)
                    st.rerun()
            with _cc2:
                st.markdown(
                    f"<div style='text-align:center;font-size:.8rem;color:{TEXT_MUTED};padding:.5rem;'>"
                    f"{_current_idx + 1} / {len(_images)}</div>",
                    unsafe_allow_html=True,
                )
            with _cc3:
                if st.button("›", key=f"next_{_product_id}_{_idx}", use_container_width=True):
                    st.session_state.carousel_indices[_carousel_key] = (_current_idx + 1) % len(_images)
                    st.rerun()

        # CTA
        if _is_in_stock:
            if st.button(TEXT_ADD_TO_CART, key=f"order_{_product_id}", use_container_width=True):
                st.session_state.selected_product = _row.to_dict()
                st.rerun()
        else:
            st.button(
                TEXT_OUT_OF_STOCK,
                key=f"out_{_product_id}",
                disabled=True,
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)  # product-grid

# ==========================================
# CHECKOUT FORM
# ==========================================

if st.session_state.selected_product is not None:
    _p = st.session_state.selected_product

    st.markdown("<div class='order-container'>", unsafe_allow_html=True)
    st.markdown(f"### {TEXT_CHECKOUT}")
    st.markdown(
        f"<p style='color:{TEXT_SECONDARY};margin-bottom:1.5rem;'>"
        f"<strong>Product:</strong> {_p['name']}</p>",
        unsafe_allow_html=True,
    )

    # Parse variants
    _variants_dict = {}
    if _p.get("variants") and ENABLE_VARIANTS:
        try:
            for _pair in str(_p["variants"]).split(","):
                if ":" in _pair:
                    _sz, _vp = _pair.strip().split(":")
                    _variants_dict[_sz.strip()] = int(_vp.strip())
        except Exception:
            pass

    with st.form("checkout_form", clear_on_submit=True):
        _o1, _o2 = st.columns(2)
        with _o1:
            _cust_name = st.text_input(f"{TEXT_LABEL_NAME} *", placeholder="Your full name")
            _cust_phone = st.text_input(f"{TEXT_LABEL_PHONE} *", placeholder="0541234567")
        with _o2:
            _cust_location = st.text_input(f"{TEXT_LABEL_LOCATION} *", placeholder="Accra, Kumasi, etc.")
            _qty = st.number_input(
                f"{TEXT_LABEL_QUANTITY} *",
                min_value=MIN_ORDER_QUANTITY,
                max_value=MAX_ORDER_QUANTITY,
                value=MIN_ORDER_QUANTITY,
            )

        _selected_variant = "Standard"
        _unit_price = int(_p["price"])

        if _variants_dict:
            st.markdown("<div class='variant-selector'>", unsafe_allow_html=True)
            st.markdown(f"<span class='variant-label'>{TEXT_LABEL_VARIANT}</span>", unsafe_allow_html=True)
            _variant_opts = list(_variants_dict.items())
            _sel_idx = st.radio(
                "",
                options=range(len(_variant_opts)),
                format_func=lambda x: f"{_variant_opts[x][0]} — {CURRENCY_SYMBOL}{_variant_opts[x][1]}",
                horizontal=True,
                label_visibility="collapsed",
            )
            _selected_variant = _variant_opts[_sel_idx][0]
            _unit_price = _variant_opts[_sel_idx][1]
            st.markdown("</div>", unsafe_allow_html=True)

        _total = _unit_price * int(_qty)

        st.markdown(f"""
        <div class='order-summary'>
            <div class='order-summary-title'>Order Summary</div>
            <div class='order-summary-row'><span>Product</span><span>{_p['name']}</span></div>
            <div class='order-summary-row'><span>Variant</span><span>{_selected_variant}</span></div>
            <div class='order-summary-row'><span>Unit Price</span><span>{CURRENCY_SYMBOL}{_unit_price}</span></div>
            <div class='order-summary-row'><span>Quantity</span><span>{_qty}</span></div>
            <div class='order-summary-total'>Total: {CURRENCY_SYMBOL}{_total}</div>
        </div>
        """, unsafe_allow_html=True)

        _order_submitted = st.form_submit_button(TEXT_PLACE_ORDER, use_container_width=True)

        if _order_submitted:
            if not all([_cust_name, _cust_phone, _cust_location]):
                st.warning("⚠️ Please fill in all required fields.")
            else:
                _loading = st.empty()
                _loading.markdown("""
                <div class='loading-overlay'>
                    <div style='width:60px;height:60px;border:3px solid #fde68a;
                         border-top:3px solid #d97706;border-right:3px solid #f59e0b;
                         border-radius:50%;animation:spin 1s linear infinite;
                         box-shadow:0 0 20px rgba(217,119,6,.3);'></div>
                    <div style='margin-top:1.5rem;font-size:1.1rem;font-weight:600;
                         color:#1f2937;animation:pulse 1.5s ease-in-out infinite;'>
                         Processing your order...</div>
                </div>
                <style>
                .loading-overlay{position:fixed;top:0;left:0;width:100%;height:100%;
                    background:rgba(254,243,242,.98);display:flex;flex-direction:column;
                    align-items:center;justify-content:center;z-index:9999;backdrop-filter:blur(10px);}
                @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
                @keyframes pulse{0%,100%{opacity:1;}50%{opacity:.5;}}
                </style>
                """, unsafe_allow_html=True)

                try:
                    _ref = generate_reference(_p["name"], _cust_location)
                    _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    _client = get_sheets_client()
                    _sheet = _client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
                    _sheet.append_row([
                        _cust_name, _cust_phone, _cust_location,
                        _p["name"], _qty, _total,
                        _ref, _ts, STATUS_PENDING, _selected_variant,
                    ])
                    send_notifications_async(
                        _p["name"], _selected_variant, _cust_name,
                        _cust_phone, _cust_location, _qty, _total, _ref, _ts,
                    )
                    _loading.empty()
                    st.markdown(f"""
                    <div class='success-message'>
                        <div class='success-title'>✅ {ORDER_SUCCESS_TITLE}</div>
                        <p style='font-size:1.1rem;margin-bottom:.5rem;'>
                            Reference: <strong>{_ref}</strong></p>
                        <p style='font-size:1.2rem;margin-bottom:1rem;'>
                            Total: <strong>{CURRENCY_SYMBOL}{_total}</strong></p>
                        <p style='font-size:.95rem;opacity:.9;'>{ORDER_SUCCESS_MESSAGE}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.selected_product = None
                    time.sleep(12)
                    st.rerun()
                except Exception as exc:
                    _loading.empty()
                    st.error(f"❌ Error processing order: {exc}")

    if st.button("← Continue Shopping", use_container_width=True, type="secondary"):
        st.session_state.selected_product = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # order-container

# ==========================================
# FOOTER
# ==========================================

_footer_links_html = "".join(
    f"<a href='{_lnk['url']}' class='footer-link' target='_blank' rel='noopener noreferrer'>"
    f"{_lnk['icon']} {_lnk['text']}</a>"
    for _lnk in FOOTER_LINKS
)

st.markdown(f"""
<div class='footer'>
    <div class='footer-title'>💎 {STORE_NAME}</div>
    <div class='footer-links'>{_footer_links_html}</div>
    <div class='footer-copyright'>{COPYRIGHT_TEXT}</div>
</div>
""", unsafe_allow_html=True)

# Close main content wrapper
st.markdown("</div>", unsafe_allow_html=True)
