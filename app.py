# ==========================================
# E-COMMERCE STORE TEMPLATE
# Powered by Streamlit + Google Sheets
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

# Import configuration
try:
    from config import *
except ImportError:
    st.error("⚠️ config.py file not found! Please ensure config.py is in the same folder as app.py")
    st.stop()

# ---------------- REFERENCE GENERATOR ----------------
def generate_reference(product_name, location):
    product_code = product_name[:3].upper()
    location_code = location[:3].upper()
    min_rand = 10 ** (REFERENCE_LENGTH - 1)
    max_rand = (10 ** REFERENCE_LENGTH) - 1
    rand = random.randint(min_rand, max_rand)
    return f"{REFERENCE_PREFIX}-{product_code}-{location_code}-{rand}"

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
    except:
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

# ---------------- DYNAMIC THEME BASED ON CONFIG ----------------
logo_border_radius = "50%" if LOGO_SHAPE == "circle" else "8px"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, .stApp {{ 
    background: {BACKGROUND_COLOR};
    color: {TEXT_PRIMARY};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

h1, h2, h3, h4 {{ 
    color: {TEXT_PRIMARY};
    font-weight: 600;
}}

/* Top Navigation Bar */
.top-nav {{
    background: {NAV_BACKGROUND};
    padding: 16px 40px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    margin-bottom: 0;
    display: flex;
    align-items: center;
    gap: 30px;
    position: sticky;
    top: 0;
    z-index: 1000;
}}

.logo-container {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.logo-icon {{
    width: 46px;
    height: 46px;
    background: {PRIMARY_COLOR};
    border-radius: {logo_border_radius};
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 20px;
}}

.logo-text {{
    font-size: 22px;
    font-weight: 700;
    color: {NAV_TEXT_COLOR};
    margin: 0;
}}

.nav-tagline {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
    margin: 0;
    font-style: italic;
}}

.content-wrapper {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 30px 20px;
    background: {BACKGROUND_COLOR};
}}

.section-header {{
    font-size: 24px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin: 30px 0 20px 0;
    padding-bottom: 12px;
    border-bottom: 2px solid #e7e9ec;
}}

.product-card {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.2s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}}

.product-card:hover {{
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    border-color: #c7c9cc;
}}

.product-image-wrapper {{
    width: 100%;
    height: {PRODUCT_IMAGE_HEIGHT};
    background: {CARD_BACKGROUND};
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    border-bottom: 1px solid #e7e9ec;
    position: relative;
}}

.product-image-wrapper img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
}}

.stock-badge {{
    position: absolute;
    top: 12px;
    right: 12px;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}}

.badge-in-stock {{
    background: #e7f5e9;
    color: #067d62;
}}

.badge-out-stock {{
    background: #fce8e8;
    color: #c7254e;
}}

.product-info {{
    padding: 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
}}

.product-title {{
    font-size: 16px;
    font-weight: 500;
    color: {PRIMARY_COLOR};
    margin-bottom: 8px;
    line-height: 1.4;
}}

.product-description {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    line-height: 1.5;
    margin-bottom: 12px;
    flex: 1;
}}

.product-price {{
    font-size: 24px;
    font-weight: 700;
    color: {PRICE_COLOR};
    margin-bottom: 12px;
}}

.price-currency {{
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
    margin-right: 2px;
}}

.stButton>button {{
    background: {BUTTON_COLOR};
    color: {BUTTON_TEXT_COLOR};
    border: 1px solid {BUTTON_COLOR};
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 14px;
    width: 100%;
    transition: all 0.2s ease;
    box-shadow: 0 2px 5px rgba(213, 217, 217, 0.5);
}}

.stButton>button:hover {{
    opacity: 0.9;
}}

.stButton>button:disabled {{
    background: #f0f2f2;
    color: {TEXT_SECONDARY};
    border-color: #d5d9d9;
}}

.admin-container {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}}

.stat-card {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
}}

.stat-number {{
    font-size: 32px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    margin-bottom: 8px;
}}

.stat-label {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
    font-weight: 500;
}}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stNumberInput>div>div>input {{
    border-radius: 4px;
    border: 1px solid #d5d9d9;
    padding: 10px 12px;
    font-size: 14px;
}}

.stTextInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stNumberInput>div>div>input:focus {{
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 0 0 3px rgba(40, 116, 240, 0.1);
}}

.order-container {{
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 8px;
    padding: 30px;
    margin: 30px 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}}

.order-summary {{
    background: #f0f2f2;
    padding: 20px;
    border-radius: 8px;
    margin-top: 20px;
}}

.success-message {{
    background: #dff0d8;
    border: 1px solid #d6e9c6;
    color: #3c763d;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}}

.footer-section {{
    background: {FOOTER_BACKGROUND};
    color: {FOOTER_TEXT_COLOR};
    padding: 40px 20px;
    margin-top: 60px;
    text-align: center;
}}

.footer-links {{
    display: flex;
    justify-content: center;
    gap: 30px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}

.footer-link {{
    color: {FOOTER_TEXT_COLOR};
    font-size: 14px;
    text-decoration: none;
}}

.footer-link:hover {{
    text-decoration: underline;
}}

.footer-copyright {{
    color: #999;
    font-size: 12px;
    margin-top: 20px;
}}

.admin-login-box {{
    max-width: 400px;
    margin: 60px auto;
    background: {CARD_BACKGROUND};
    border: 1px solid #e7e9ec;
    border-radius: 8px;
    padding: 40px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}}

.info-box {{
    background: #e7f5ff;
    border: 1px solid #b3d9ff;
    border-radius: 8px;
    padding: 16px;
    margin: 20px 0;
    font-size: 14px;
    color: {PRIMARY_COLOR};
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
        "description","status"
    ])
    rows = []
    for i, r in enumerate(records, start=2):
        r["_row"] = i
        rows.append(r)
    return pd.DataFrame(rows)

products_df = load_products()

# ==============================
# TOP NAVIGATION
# ==============================
st.markdown(f"""
<div class='top-nav'>
    <div class='logo-container'>
        <div class='logo-icon'>{LOGO_TEXT}</div>
        <div>
            <div class='logo-text'>{STORE_NAME}</div>
            <div class='nav-tagline'>{STORE_TAGLINE}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='content-wrapper'>", unsafe_allow_html=True)

# ==============================
# 🔐 ADMIN LOGIN
# ==============================
if st.session_state.show_admin_login and not st.session_state.admin_logged:
    st.markdown("<div class='admin-login-box'>", unsafe_allow_html=True)
    st.markdown("### 🔐 Admin Login")
    st.markdown("Enter your credentials to access the dashboard")
    
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
# 📊 ADMIN DASHBOARD
# ==============================
if st.session_state.admin_logged:
    
    st.markdown(f"<h1 style='color:{TEXT_PRIMARY}; margin-bottom:10px;'>{HEADER_ADMIN_DASHBOARD}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{TEXT_SECONDARY}; margin-bottom:30px;'>Manage your store products and orders</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.admin_logged = False
            st.rerun()
    
    # Telegram configuration check
    telegram_configured = bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    
    if not telegram_configured:
        st.markdown("""
        <div class='info-box'>
            ⚠️ <strong>Telegram notifications not configured!</strong><br>
            Set up your Telegram bot to receive instant order notifications.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#e7f5e9; border:1px solid #c6e9d0; border-radius:8px; padding:16px; margin:20px 0;'>
            ✅ <strong>Telegram notifications active!</strong> You'll receive instant alerts for new orders.
        </div>
        """, unsafe_allow_html=True)
    
    # Statistics
    orders_df = pd.DataFrame(
        orders_sheet.get_all_records(expected_headers=[
            "name","phone","location","items",
            "qty","amount","reference","timestamp","status"
        ])
    )
    
    if SHOW_STATISTICS:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(products_df)}</div>
                <div class='stat-label'>Total Products</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{len(orders_df)}</div>
                <div class='stat-label'>Total Orders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_revenue = orders_df['amount'].sum() if not orders_df.empty else 0
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-number'>{CURRENCY_SYMBOL} {total_revenue:,.0f}</div>
                <div class='stat-label'>Total Revenue</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    # ADD PRODUCT
    st.markdown("<div class='admin-container'>", unsafe_allow_html=True)
    st.markdown("### ➕ Add New Product")
    with st.form("add_product"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product Name *")
            price = st.number_input(f"Price ({CURRENCY}) *", min_value=0)
        with col2:
            stock = st.number_input("Stock Quantity *", min_value=0)
            
        desc = st.text_area("Product Description")
        images = st.file_uploader(
            "Upload Product Images (Up to 3)",
            type=["png","jpg","jpeg"],
            accept_multiple_files=True
        )
        add = st.form_submit_button("Add Product", use_container_width=True)
        
        if add and name and images:
            encoded = []
            for img in images[:3]:
                encoded.append(
                    f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
                )
            while len(encoded) < 3:
                encoded.append("")
            
            new_id = int(products_df["id"].max()) + 1 if not products_df.empty else 1
            status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK
            
            products_sheet.append_row([
                new_id, name, price, stock,
                encoded[0], encoded[1], encoded[2],
                desc, status
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
                st.image(row["image1"], use_column_width=True)
                st.markdown(f"**{row['name']}**")
                st.markdown(f"Stock: {row['stock']} | {CURRENCY_SYMBOL} {row['price']}")
                
                if st.button(f"Delete Product", key=f"del_{row['id']}", use_container_width=True):
                    products_sheet.delete_rows(row["_row"])
                    st.success("Product deleted!")
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
    
    st.stop()

# ==============================
# 🛍️ PUBLIC SHOP
# ==============================

# Admin button
if SHOW_ADMIN_BUTTON:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col3:
        if st.button("🔐 Admin", use_container_width=True):
            st.session_state.show_admin_login = True
            st.rerun()

st.markdown(f"<div class='section-header'>{HEADER_FEATURED_PRODUCTS}</div>", unsafe_allow_html=True)

if products_df.empty:
    st.info("🏗️ No products available at the moment. Check back soon!")
else:
    cols = st.columns(PRODUCTS_PER_ROW)
    for idx, row in products_df.iterrows():
        with cols[idx % PRODUCTS_PER_ROW]:
            badge_class = "badge-in-stock" if row["status"] == STATUS_IN_STOCK else "badge-out-stock"
            
            badge_html = f"<div class='stock-badge {badge_class}'>{row['status']}</div>" if SHOW_STOCK_BADGE else ""
            desc_html = f"<div class='product-description'>{row['description']}</div>" if ENABLE_PRODUCT_DESCRIPTION else ""
            
            st.markdown(f"""
            <div class='product-card'>
                <div class='product-image-wrapper'>
                    <img src='{row["image1"]}' alt='{row["name"]}'>
                    {badge_html}
                </div>
                <div class='product-info'>
                    <div class='product-title'>{row['name']}</div>
                    {desc_html}
                    <div class='product-price'>
                        <span class='price-currency'>{CURRENCY_SYMBOL}</span>{row['price']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
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
        
        total = int(p["price"]) * int(qty)
        
        st.markdown(f"""
        <div class='order-summary'>
            <strong>{HEADER_ORDER_SUMMARY}</strong><br>
            Item: {p['name']}<br>
            Quantity: {qty}<br>
            <strong style='font-size:18px; color:{PRICE_COLOR};'>Total: {CURRENCY_SYMBOL} {total}</strong>
        </div>
        """, unsafe_allow_html=True)
        
        send = st.form_submit_button(BUTTON_PLACE_ORDER, use_container_width=True)
        
        if send and name and phone and location:
            reference = generate_reference(p["name"], location)
            
            orders_sheet.append_row([
                name,
                phone,
                location,
                p["name"],
                qty,
                total,
                reference,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                STATUS_PENDING
            ])
            
            # Send Telegram notification
            telegram_message = TELEGRAM_NOTIFICATION_TEMPLATE.format(
                product_name=p['name'],
                customer_name=name,
                phone=phone,
                location=location,
                quantity=qty,
                currency=CURRENCY_SYMBOL,
                total=total,
                reference=reference,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            send_telegram_notification(telegram_message)
            
            st.markdown(f"""
            <div class='success-message'>
                <h3 style='margin:0 0 10px 0;'>✅ {ORDER_SUCCESS_TITLE}</h3>
                <p style='margin:0;'>
                    {ORDER_SUCCESS_MESSAGE}
                </p>
                <p style='margin:10px 0 0 0;'><strong>Total: {CURRENCY_SYMBOL} {total}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            del st.session_state.selected
    
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ==============================
# FOOTER
# ==============================
footer_links_html = " <span style='color:#999;'>|</span> ".join([
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
