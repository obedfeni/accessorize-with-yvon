
# ==========================================
# E-COMMERCE STORE TEMPLATE
# Powered by Streamlit + Google Sheets + Cloudinary
# ==========================================
# To customize: Edit config.py file!
# ==========================================

import streamlit as st
import gspread
import pandas as pd
import os, json, base64
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import random
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import io
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Import configuration
try:
    from config import *
except ImportError:
    st.error("⚠️ config.py file not found! Please ensure config.py is in the same folder as app.py")
    st.stop()

# ---------------- CLOUDINARY SETUP ----------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ---------------- REFERENCE GENERATOR ----------------
def generate_reference(product_name, location):
    product_code = product_name[:3].upper()
    location_code = location[:3].upper()
    min_rand = 10 ** (REFERENCE_LENGTH - 1)
    max_rand = (10 ** REFERENCE_LENGTH) - 1
    rand = random.randint(min_rand, max_rand)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{rand}"

# ---------------- CLOUDINARY IMAGE UPLOAD ----------------
def upload_to_cloudinary(image_file, filename):
    """
    Upload image to Cloudinary with automatic optimization
    Returns the secure URL or None if failed
    """
    try:
        image_file.seek(0)
        file_bytes = image_file.read()
        image_file.seek(0)
        
        clean_filename = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
        clean_filename = ''.join(c for c in clean_filename if c.isalnum() or c in ['_', '-'])
        
        public_id = f"accessorize_yvon/{clean_filename}"
        
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto:good'},
                {'fetch_format': 'auto'}
            ]
        )
        
        secure_url = result.get('secure_url')
        if secure_url:
            print(f"✅ Uploaded to Cloudinary: {secure_url}")
            return secure_url
        else:
            print(f"❌ No URL returned from Cloudinary")
            return None
    
    except Exception as e:
        print(f"❌ Cloudinary upload error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

# ---------------- DELETE FROM CLOUDINARY ----------------
def delete_from_cloudinary(image_url):
    """Delete image from Cloudinary using its URL"""
    try:
        parts = image_url.split('/')
        if 'cloudinary.com' in image_url:
            upload_idx = parts.index('upload')
            public_id_parts = parts[upload_idx + 2:]
            public_id = '/'.join(public_id_parts).replace('.jpg', '').replace('.png', '').replace('.jpeg', '')
            
            result = cloudinary.uploader.destroy(public_id)
            print(f"🗑️ Deleted from Cloudinary: {public_id}")
            return result.get('result') == 'ok'
    except Exception as e:
        print(f"❌ Cloudinary delete error: {e}")
    return False

# ---------------- EMAIL NOTIFICATION ----------------
def send_email_notification(subject, message):
    """Send email notification using Gmail SMTP"""
    admin_email = os.environ.get("ADMIN_EMAIL")
    email_password = os.environ.get("EMAIL_APP_PASSWORD")
    
    if not admin_email or not email_password:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = admin_email
        msg['To'] = admin_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(admin_email, email_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ---------------- TELEGRAM NOTIFICATION ----------------
def send_telegram_notification(message):
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not telegram_bot_token or not telegram_chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        data = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title=STORE_NAME,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- SESSION STATE ----------------
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False

# ---------------- CHECK FOR ADMIN ROUTE ----------------
query_params = st.query_params
if "page" in query_params and query_params["page"] == "admin":
    st.session_state.show_admin_login = True

# ---------------- HIDE STREAMLIT UI ----------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# ---------------- PROFESSIONAL THEME (Mobile Optimized) ----------------
logo_border_radius = "50%" if LOGO_SHAPE == "circle" else "12px"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stApp {{ 
    background: {BACKGROUND_COLOR};
    color: {TEXT_PRIMARY};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

h1, h2, h3, h4 {{ 
    color: {TEXT_PRIMARY};
    font-weight: 600;
}}

/* Professional Navigation Bar */
.top-nav {{
    background: {NAV_BACKGROUND};
    padding: 20px 40px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    margin-bottom: 0;
    display: flex;
    align-items: center;
    gap: 20px;
    position: sticky;
    top: 0;
    z-index: 1000;
}}

.logo-container {{
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;
}}

.logo-icon {{
    width: 65px;
    height: 65px;
    background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {BUTTON_COLOR} 100%);
    border-radius: {logo_border_radius};
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 28px;
    flex-shrink: 0;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}}

.logo-text-container {{
    flex: 1;
}}

.logo-text {{
    font-size: 26px;
    font-weight: 800;
    color: {NAV_TEXT_COLOR};
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.5px;
}}

.nav-tagline {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    margin: 4px 0 0 0;
    font-weight: 500;
}}

/* Mobile responsive */
@media (max-width: 768px) {{
    .top-nav {{
        padding: 15px 20px;
    }}
    .logo-icon {{
        width: 55px;
        height: 55px;
        font-size: 24px;
    }}
    .logo-text {{
        font-size: 20px;
    }}
    .nav-tagline {{
        font-size: 11px;
    }}
}}

/* Content Wrapper */
.content-wrapper {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 40px 20px;
    background: {BACKGROUND_COLOR};
}}

@media (max-width: 768px) {{
    .content-wrapper {{
        padding: 25px 15px;
    }}
}}

/* Section Headers */
.section-header {{
    font-size: 28px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin: 40px 0 25px 0;
    padding-bottom: 15px;
    border-bottom: 3px solid {PRIMARY_COLOR};
}}

/* Premium Product Cards */
.product-card {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}}

.product-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
    border-color: {PRIMARY_COLOR};
}}

.stock-badge {{
    position: absolute;
    top: 15px;
    right: 15px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    z-index: 5;
}}

.badge-in-stock {{
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
}}

.badge-out-stock {{
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
}}

.product-info {{
    padding: 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
    background: linear-gradient(to bottom, #ffffff 0%, #fafafa 100%);
    min-height: 200px;
}}

.product-title {{
    font-size: 17px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin: 0 0 12px 0;
    line-height: 1.4;
    min-height: 48px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.product-description {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    line-height: 1.6;
    margin: 0 0 15px 0;
    min-height: 44px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.product-price {{
    font-size: 26px;
    font-weight: 800;
    color: {PRICE_COLOR};
    margin: 0 0 12px 0;
    padding: 8px 0;
    display: flex;
    align-items: baseline;
    gap: 5px;
}}

.price-currency {{
    font-size: 16px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
}}

.variant-selector {{
    background: #f9fafb;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 15px;
}}

.variant-option {{
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 5px;
    cursor: pointer;
    display: inline-block;
    transition: all 0.3s ease;
    font-size: 13px;
    font-weight: 600;
}}

.variant-option:hover {{
    border-color: {PRIMARY_COLOR};
    background: #fef3c7;
}}

.variant-option.selected {{
    border-color: {PRIMARY_COLOR};
    background: {PRIMARY_COLOR};
    color: white;
}}

/* Premium Buttons */
.stButton>button {{
    background: linear-gradient(135deg, {BUTTON_COLOR} 0%, {PRIMARY_COLOR} 100%);
    color: {BUTTON_TEXT_COLOR};
    border: none;
    border-radius: 10px;
    padding: 13px 24px;
    font-weight: 700;
    font-size: 15px;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.stButton>button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}}

.stButton>button:disabled {{
    background: #e5e7eb;
    color: #9ca3af;
    box-shadow: none;
}}

/* Small Admin Button */
.admin-btn-small button {{
    padding: 8px 16px !important;
    font-size: 13px !important;
    width: auto !important;
    min-width: 110px !important;
}}

/* Admin Container */
.admin-container {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}}

/* Stats Cards */
.stat-card {{
    background: linear-gradient(135deg, {CARD_BACKGROUND} 0%, #fafafa 100%);
    border: 1px solid #e7e9ec;
    border-radius: 12px;
    padding: 28px;
    text-align: center;
    transition: all 0.3s ease;
}}

.stat-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}}

.stat-number {{
    font-size: 36px;
    font-weight: 800;
    background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {BUTTON_COLOR} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}}

.stat-label {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* Forms */
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {{
    border-radius: 8px;
    border: 2px solid #e5e7eb;
    padding: 12px 16px;
    font-size: 15px;
    transition: all 0.3s ease;
}}

.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stNumberInput>div>div>input:focus {{
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.1);
}}

/* Order Container */
.order-container {{
    background: {CARD_BACKGROUND};
    border: 2px solid #e7e9ec;
    border-radius: 16px;
    padding: 35px;
    margin: 40px 0;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}}

.order-summary {{
    background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    padding: 25px;
    border-radius: 12px;
    margin-top: 20px;
    border: 1px solid #e5e7eb;
}}

/* Success Message */
.success-message {{
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border: 2px solid #6ee7b7;
    color: #065f46;
    padding: 25px;
    border-radius: 12px;
    margin: 25px 0;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}}

/* Footer */
.footer-section {{
    background: {FOOTER_BACKGROUND};
    color: {FOOTER_TEXT_COLOR};
    padding: 50px 20px;
    margin-top: 80px;
    text-align: center;
    border-top: 4px solid {PRIMARY_COLOR};
}}

.footer-links {{
    display: flex;
    justify-content: center;
    gap: 35px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}}

.footer-link {{
    color: {FOOTER_TEXT_COLOR};
    font-size: 15px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s ease;
}}

.footer-link:hover {{
    color: {BUTTON_COLOR};
    transform: translateY(-2px);
}}

.footer-copyright {{
    color: rgba(255, 255, 255, 0.7);
    font-size: 13px;
    margin-top: 25px;
    font-weight: 500;
}}

/* Admin Login */
.admin-login-box {{
    max-width: 420px;
    margin: 80px auto;
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 16px;
    padding: 45px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}}

/* Info Box */
.info-box {{
    background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    border: 1px solid #93c5fd;
    border-radius: 10px;
    padding: 18px;
    margin: 20px 0;
    font-size: 14px;
    color: #1e40af;
    font-weight: 500;
}}

{CUSTOM_CSS}
</style>
""", unsafe_allow_html=True)

# ---------------- GOOGLE SHEETS AUTH ----------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

raw_creds = os.environ.get("GCP_SERVICE_ACCOUNT")
if not raw_creds:
    st.error("⚠️ Server configuration error")
    st.stop()

try:
    creds_dict = json.loads(raw_creds)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"⚠️ Google Sheets connection error: {str(e)}")
    st.stop()

# ---------------- LOAD SHEETS ----------------
try:
    products_sheet = client.open(SHEET_NAME).worksheet(PRODUCTS_WORKSHEET)
    orders_sheet = client.open(SHEET_NAME).worksheet(ORDERS_WORKSHEET)
except Exception as e:
    st.error(f"⚠️ Could not find Google Sheet '{SHEET_NAME}' or worksheets. Error: {str(e)}")
    st.stop()

def load_products():
    records = products_sheet.get_all_records(expected_headers=[
        "id","name","price","stock",
        "image1","image2","image3",
        "description","status","variants"
    ])
    rows = []
    for i, r in enumerate(records, start=2):
        r["_row"] = i
        rows.append(r)
    return pd.DataFrame(rows)

products_df = load_products()

# ==============================
# PROFESSIONAL NAVIGATION
# ==============================
st.markdown(f"""
<div class='top-nav'>
    <div class='logo-container'>
        <div class='logo-icon'>{LOGO_TEXT}</div>
        <div class='logo-text-container'>
            <div class='logo-text'>{STORE_NAME}</div>
            <div class='nav-tagline'>{STORE_TAGLINE}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)

# ==============================
# ADMIN LOGIN
# ==============================
if st.session_state.show_admin_login and not st.session_state.admin_logged:
    st.markdown("<div class='admin-login-box'>", unsafe_allow_html=True)
    st.markdown("### 🔐 Admin Login")
    st.markdown("Enter credentials to access dashboard")
    
    password = st.text_input("Password", type="password")
    
    if st.button(BUTTON_ADMIN_LOGIN, use_container_width=True):
        if password == os.environ.get("ADMIN_PASSWORD", "change_me"):
            st.session_state.admin_logged = True
            st.session_state.show_admin_login = False
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("← Back to Shop"):
        st.session_state.show_admin_login = False
        st.rerun()
    
    st.stop()

# ==============================
# ADMIN DASHBOARD
# ==============================
if st.session_state.admin_logged:
    
    st.markdown(f"<h1 style='color:{TEXT_PRIMARY}; margin-bottom:10px;'>{HEADER_ADMIN_DASHBOARD}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{TEXT_SECONDARY}; margin-bottom:30px; font-size:16px;'>Manage products, orders & notifications</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.rerun()
    
    # Check notifications
    telegram_configured = bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    email_configured = bool(os.environ.get("ADMIN_EMAIL") and os.environ.get("EMAIL_APP_PASSWORD"))
    cloudinary_configured = bool(os.environ.get("CLOUDINARY_CLOUD_NAME") and os.environ.get("CLOUDINARY_API_KEY") and os.environ.get("CLOUDINARY_API_SECRET"))
    
    if not cloudinary_configured:
        st.markdown("""
        <div class='info-box' style='background:linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-color:#fca5a5; color:#991b1b;'>
            ⚠️ <strong>Cloudinary not configured!</strong> Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to environment variables.
        </div>
        """, unsafe_allow_html=True)
    
    if not telegram_configured and not email_configured:
        st.markdown("""
        <div class='info-box'>
            ⚠️ <strong>No notifications configured!</strong> Set up Telegram or Email to receive order alerts.
        </div>
        """, unsafe_allow_html=True)
    else:
        notif_status = []
        if telegram_configured:
            notif_status.append("Telegram")
        if email_configured:
            notif_status.append("Email")
        
        st.markdown(f"""
        <div style='background:linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border:2px solid #6ee7b7; border-radius:10px; padding:18px; margin:20px 0;'>
            ✅ <strong>Notifications active via: {', '.join(notif_status)}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Statistics
    orders_df = pd.DataFrame(
        orders_sheet.get_all_records(expected_headers=[
            "name","phone","location","items",
            "qty","amount","reference","timestamp","status","variant"
        ])
    )
    
    if SHOW_STATISTICS:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(products_df)}</div>
                <div class='stat-label'>Products</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(orders_df)}</div>
                <div class='stat-label'>Orders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_revenue = orders_df['amount'].sum() if not orders_df.empty else 0
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{CURRENCY_SYMBOL} {total_revenue:,.0f}</div>
                <div class='stat-label'>Revenue</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # ADD PRODUCT
    st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
    st.markdown("### ➕ Add New Product")
    
    st.info("💡 **Variants:** Add different sizes/options with different prices (e.g., Small:100, Medium:150, Large:200). Leave empty if product has single price.")
    
    with st.form("add_product"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product Name *")
            price = st.number_input(f"Base Price ({CURRENCY}) *", min_value=0, help="Default price if no variants")
        with col2:
            stock = st.number_input("Stock Quantity *", min_value=0)
            variants_input = st.text_input("Variants (Optional)", placeholder="Small:100, Medium:150, Large:200", help="Format: Size:Price, Size:Price")
            
        desc = st.text_area("Product Description")
        images = st.file_uploader(
            "Upload Product Images (Up to 3)",
            type=["png","jpg","jpeg"],
            accept_multiple_files=True
        )
        add = st.form_submit_button("Add Product", use_container_width=True)
        
        if add and name and images:
            image_urls = []
            
            with st.spinner("☁️ Uploading images to Cloudinary..."):
                for idx, img in enumerate(images[:3], 1):
                    filename = f"{name.replace(' ', '_')}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                    url = upload_to_cloudinary(img, filename)
                    
                    if url:
                        image_urls.append(url)
                        st.success(f"✅ Image {idx} uploaded successfully")
                    else:
                        st.error(f"❌ Failed to upload image {idx}")
                        st.stop()
            
            while len(image_urls) < 3:
                image_urls.append("")
            
            new_id = int(products_df["id"].max()) + 1 if not products_df.empty else 1
            status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK
            
            products_sheet.append_row([
                new_id, name, price, stock,
                image_urls[0], image_urls[1], image_urls[2],
                desc, status, variants_input
            ])
            
            st.success("✅ Product added successfully!")
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # MANAGE PRODUCTS
    st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
    st.markdown("### 🗂️ Manage Products")
    products_df = load_products()
    
    if not products_df.empty:
        cols = st.columns(3)
        for idx, row in products_df.iterrows():
            with cols[idx % 3]:
                # Show all images
                images_to_show = [row["image1"], row["image2"], row["image3"]]
                images_to_show = [img for img in images_to_show if img]
                
                if images_to_show:
                    st.image(images_to_show[0], use_column_width=True)
                    if len(images_to_show) > 1:
                        st.caption(f"📸 {len(images_to_show)} images")
                
                st.markdown(f"**{row['name']}**")
                st.markdown(f"Stock: {row['stock']} | {CURRENCY_SYMBOL} {row['price']}")
                
                if row.get('variants'):
                    st.caption(f"🎯 Variants: {row['variants']}")
                
                if st.button(f"Delete", key=f"del_{row['id']}", use_container_width=True):
                    for img_col in ['image1', 'image2', 'image3']:
                        img_url = row.get(img_col, '')
                        if img_url and 'cloudinary.com' in img_url:
                            delete_from_cloudinary(img_url)
                    
                    products_sheet.delete_rows(row["_row"])
                    st.success("Product and images deleted!")
                    st.rerun()
    else:
        st.info("No products yet")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ORDERS
    st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
    st.markdown("### 📦 Recent Orders")
    if not orders_df.empty:
        st.dataframe(orders_df, use_container_width=True, height=400)
    else:
        st.info("No orders yet")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # SETUP GUIDE
    st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
    st.markdown("### 🔔 Notification Setup")
    
    tab1, tab2, tab3 = st.tabs(["📧 Email", "📱 Telegram", "☁️ Cloudinary"])
    
    with tab1:
        st.markdown("""
        **Gmail Setup (5 min)**
        1. [Google Account](https://myaccount.google.com) → Security
        2. Enable 2-Step Verification
        3. App passwords → Mail → Generate
        4. Add to Render: `ADMIN_EMAIL` & `EMAIL_APP_PASSWORD`
        """)
    
    with tab2:
        st.markdown("""
        **Telegram Setup (5 min)**
        1. Search `@BotFather` → `/newbot`
        2. Search `@userinfobot` → get Chat ID
        3. Add to Render: `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`
        4. Send `/start` to your bot
        """)
    
    with tab3:
        st.markdown("""
        **Cloudinary Setup (5 min)**
        1. Sign up at [Cloudinary](https://cloudinary.com)
        2. Go to Dashboard → Copy credentials
        3. Add to Render:
           - `CLOUDINARY_CLOUD_NAME`
           - `CLOUDINARY_API_KEY`
           - `CLOUDINARY_API_SECRET`
        4. Free tier: 25GB storage + 25GB bandwidth/month
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# ==============================
# PUBLIC SHOP
# ==============================

# Small admin button
if SHOW_ADMIN_BUTTON:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        st.markdown("<div class='admin-btn-small'>", unsafe_allow_html=True)
        if st.button("🔐 Admin"):
            st.session_state.show_admin_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"<div class='section-header'>{HEADER_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

if products_df.empty:
    st.info("🏗️ No products available. Check back soon!")
else:
    cols = st.columns(PRODUCTS_PER_ROW)
    for idx, row in products_df.iterrows():
        with cols[idx % PRODUCTS_PER_ROW]:
            # Get all images
            images = [row["image1"], row["image2"], row["image3"]]
            images = [img for img in images if img]
            
            # Create unique key for this product's carousel
            carousel_key = f"carousel_{row['id']}"
            if carousel_key not in st.session_state:
                st.session_state[carousel_key] = 0
            
            # Start product card
            st.markdown(f"""
            <div class='product-card'>
                <div class='product-image-wrapper' style='position:relative;'>
            """, unsafe_allow_html=True)
            
            # Show stock badge
            if SHOW_STOCK_BADGE:
                badge_class = "badge-in-stock" if row["status"] == STATUS_IN_STOCK else "badge-out-stock"
                st.markdown(f"<div class='stock-badge {badge_class}'>{row['status']}</div>", unsafe_allow_html=True)
            
            # Display current image
            if images:
                st.image(images[st.session_state[carousel_key]], use_container_width=True)
                
                # Image counter and navigation
                if len(images) > 1:
                    col_left, col_mid, col_right = st.columns([1, 2, 1])
                    with col_left:
                        if st.button("◀", key=f"prev_{row['id']}", use_container_width=True):
                            st.session_state[carousel_key] = (st.session_state[carousel_key] - 1) % len(images)
                            st.rerun()
                    with col_mid:
                        st.markdown(f"<div style='text-align:center; padding:8px 0; font-size:12px; color:#6b7280;'>{st.session_state[carousel_key] + 1} / {len(images)}</div>", unsafe_allow_html=True)
                    with col_right:
                        if st.button("▶", key=f"next_{row['id']}", use_container_width=True):
                            st.session_state[carousel_key] = (st.session_state[carousel_key] + 1) % len(images)
                            st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Product info
            st.markdown(f"""
                <div class='product-info'>
                    <div class='product-title'>{row['name']}</div>
            """, unsafe_allow_html=True)
            
            if ENABLE_PRODUCT_DESCRIPTION and row.get('description'):
                st.markdown(f"<div class='product-description'>{row['description']}</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
                    <div class='product-price'>
                        <span class='price-currency'>{CURRENCY_SYMBOL}</span>{row['price']}
                    </div>
            """, unsafe_allow_html=True)
            
            # Show variants if available
            if row.get('variants'):
                variants_dict = {}
                try:
                    variant_pairs = row['variants'].split(',')
                    for pair in variant_pairs:
                        if ':' in pair:
                            size, price = pair.strip().split(':')
                            variants_dict[size.strip()] = int(price.strip())
                except:
                    pass
                
                if variants_dict:
                    st.markdown("<div style='margin:12px 0 6px 0; font-size:12px; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;'>Available Sizes:</div>", unsafe_allow_html=True)
                    variant_options = " • ".join([f"{size} ({CURRENCY_SYMBOL}{price})" for size, price in variants_dict.items()])
                    st.markdown(f"<div style='font-size:13px; color:#4b5563; margin:0 0 12px 0; line-height:1.8; font-weight:500;'>{variant_options}</div>", unsafe_allow_html=True)
            
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Product button
            if row["status"] == STATUS_OUT_OF_STOCK:
                st.button(BUTTON_OUT_OF_STOCK, key=f"out_{row['id']}", disabled=True, use_container_width=True)
            else:
                if st.button(BUTTON_ADD_TO_CART, key=f"order_{row['id']}", use_container_width=True):
                    st.session_state.selected = row

# ==============================
# ORDER FORM
# ==============================
if "selected" in st.session_state:
    p = st.session_state.selected
    
    st.markdown("<div class='order-container'>", unsafe_allow_html=True)
    st.markdown(f"### {HEADER_CHECKOUT}")
    st.markdown(f"**Product:** {p['name']}")
    
    # Parse variants
    variants_dict = {}
    
    if p.get('variants'):
        try:
            variant_pairs = p['variants'].split(',')
            for pair in variant_pairs:
                if ':' in pair:
                    size, price = pair.strip().split(':')
                    variants_dict[size.strip()] = int(price.strip())
        except:
            pass
    
    with st.form("order"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(f"{LABEL_CUSTOMER_NAME} *")
            phone = st.text_input(f"{LABEL_PHONE} *")
        with col2:
            location = st.text_input(f"{LABEL_LOCATION} *")
            qty = st.number_input(f"{LABEL_QUANTITY} *", 
                                 min_value=MIN_ORDER_QUANTITY, 
                                 max_value=MAX_ORDER_QUANTITY, 
                                 value=MIN_ORDER_QUANTITY)
        
        # Show variant selector if variants exist
        selected_variant_name = "Standard"
        unit_price = int(p["price"])
        
        if variants_dict:
            st.markdown("---")
            st.markdown("### 🎯 Select Size/Option")
            
            # Create visual variant selector
            variant_options = list(variants_dict.items())
            
            # Display as radio buttons with prices
            selected_option = st.radio(
                "Choose your size:",
                options=range(len(variant_options)),
                format_func=lambda x: f"{variant_options[x][0]} - {CURRENCY_SYMBOL}{variant_options[x][1]}",
                horizontal=True
            )
            
            selected_variant_name = variant_options[selected_option][0]
            unit_price = variant_options[selected_option][1]
        
        total = unit_price * int(qty)
        
        st.markdown(f"""
        <div class='order-summary'>
            <strong>{HEADER_ORDER_SUMMARY}</strong><br>
            Item: {p['name']}<br>
            Size/Option: <strong>{selected_variant_name}</strong><br>
            Unit Price: {CURRENCY_SYMBOL} {unit_price}<br>
            Quantity: {qty}<br>
            <strong style='font-size:20px; color:{PRICE_COLOR};'>Total: {CURRENCY_SYMBOL} {total}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        send = st.form_submit_button(BUTTON_PLACE_ORDER, use_container_width=True)
        
        if send and name and phone and location:
            reference = generate_reference(p["name"], location)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            orders_sheet.append_row([
                name, phone, location, p["name"],
                qty, total, reference, timestamp, STATUS_PENDING, selected_variant_name
            ])
            
            # Notifications
            telegram_msg = f"""
🛒 <b>New Order!</b>

📦 Product: {p['name']}
🎯 Size/Option: {selected_variant_name}
💵 Unit Price: {CURRENCY_SYMBOL} {unit_price}
👤 Customer: {name}
📞 Phone: {phone}
📍 Location: {location}
🔢 Quantity: {qty}
💰 Total: {CURRENCY_SYMBOL} {total}
🔖 Reference: {reference}
📅 Time: {timestamp}
            """
            telegram_sent = send_telegram_notification(telegram_msg)
            
            email_subject = f"🛒 New Order: {reference}"
            email_body = f"""
            <html><body style='font-family:Arial,sans-serif;'>
                <h2 style='color:#d97706;'>New Order Received!</h2>
                <table style='border-collapse:collapse;width:100%;'>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Product:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{p['name']}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Size/Option:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{selected_variant_name}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Unit Price:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{CURRENCY_SYMBOL} {unit_price}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Customer:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{name}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Phone:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{phone}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Location:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{location}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Quantity:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{qty}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Total:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{CURRENCY_SYMBOL} {total}</td></tr>
                    <tr><td style='padding:10px;border-bottom:1px solid #ddd;'><strong>Reference:</strong></td><td style='padding:10px;border-bottom:1px solid #ddd;'>{reference}</td></tr>
                </table>
                <p style='margin-top:20px;color:#666;'>Status: Pending</p>
            </body></html>
            """
            email_sent = send_email_notification(email_subject, email_body)
            
            notif_info = []
            if telegram_sent:
                notif_info.append("Telegram")
            if email_sent:
                notif_info.append("Email")
            notif_text = f" (Sent via {', '.join(notif_info)})" if notif_info else ""
            
            st.markdown(f"""
            <div class='success-message'>
                <h3 style='margin:0 0 12px 0;'>✅ {ORDER_SUCCESS_TITLE}{notif_text}</h3>
                <p style='margin:0; font-size:15px;'>{ORDER_SUCCESS_MESSAGE}</p>
                <p style='margin:8px 0 0 0;'>Size/Option: <strong>{selected_variant_name}</strong></p>
                <p style='margin:15px 0 0 0;'><strong style='font-size:18px;'>Total: {CURRENCY_SYMBOL} {total}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            del st.session_state.selected
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# FOOTER
# ==============================
footer_links_html = " <span style='color:rgba(255,255,255,0.5);'>|</span> ".join([
    f"<a href='{link['url']}' class='footer-link'>{link['icon']} {link['text']}</a>"
    for link in FOOTER_LINKS
])

st.markdown(f"""
<div class='footer-section'>
    <div class='footer-links'>
        {footer_links_html}
    </div>
    <div class='footer-copyright'>
        © 2026 {BUSINESS_NAME} • All Rights Reserved
    </div>
</div>
""", unsafe_allow_html=True)
