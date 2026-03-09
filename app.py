import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import lru_cache

# Must be first Streamlit command
st.set_page_config(
    page_title="Accessorize with Yvon | Shop Like a Billionaire",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# ==========================================
# TEMU-STYLE HIDE ALL STREAMLIT CHROME
# ==========================================
HIDE_STREAMLIT_STYLE = """
<style>
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .stSpinner > div > div {border-top-color: #d97706 !important;}
    [data-testid="stBottomBlockContainer"] {display: none !important;}
    .stAppViewBlockContainer {padding: 0 !important; max-width: 100% !important;}
    .block-container {padding: 0 !important; max-width: 100% !important;}
    section[data-testid="stSidebar"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    div[data-testid="stToolbarActions"] {display: none !important;}
</style>
"""
st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# ==========================================
# CONFIGURATION - TEMU STYLE WITH YOUR COLORS
# ==========================================

# Store Identity
STORE_NAME = "Accessorize with Yvon"
STORE_TAGLINE = "Shop like a billionaire"
LOGO_TEXT = "AY"

# Temu-inspired Color Palette mixed with your brand
BACKGROUND_COLOR = "#f5f5f5"  # Temu light gray
SURFACE_COLOR = "#ffffff"
PRIMARY_ORANGE = "#fb7701"  # Temu orange
PRIMARY_GOLD = "#d97706"    # Your gold
ACCENT_PINK = "#ec4899"     # Your pink
TEXT_PRIMARY = "#1a1a1a"
TEXT_SECONDARY = "#666666"
TEXT_MUTED = "#999999"
PRICE_COLOR = "#fb7701"     # Temu price orange
DISCOUNT_COLOR = "#ff4757"
SUCCESS_COLOR = "#00c851"
ERROR_COLOR = "#ff4757"

# Functional
CURRENCY_SYMBOL = "GHS"
FLASH_SALE_END = datetime.now() + timedelta(hours=4)

# ==========================================
# SESSION STATE MANAGEMENT
# ==========================================

def init_session():
    defaults = {
        'cart': [],
        'wishlist': [],
        'viewed_products': set(),
        'current_page': 'home',
        'selected_product': None,
        'search_query': '',
        'selected_category': 'All',
        'show_coupon': True,
        'spin_result': None,
        'admin_logged': False,
        'orders': [],
        'carousel_index': 0,
        'flash_sale_index': 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ==========================================
# MOCK DATA - REALISTIC PRODUCT DATABASE
# ==========================================

@st.cache_data(ttl=300)
def load_products():
    """Load product data - in production, this comes from your Google Sheets"""
    products = [
        {
            "id": 1,
            "name": "18K Gold Plated Cuban Link Chain",
            "price": 85,
            "original_price": 150,
            "rating": 4.8,
            "reviews": 234,
            "sold": 1200,
            "category": "Necklaces",
            "image": "https://images.unsplash.com/photo-1599643478518-17488fbbcd75?w=400",
            "badge": "Best Seller",
            "flash_sale": True
        },
        {
            "id": 2,
            "name": "Crystal Drop Earrings Set",
            "price": 45,
            "original_price": 89,
            "rating": 4.6,
            "reviews": 189,
            "sold": 856,
            "category": "Earrings",
            "image": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?w=400",
            "badge": "Flash Sale",
            "flash_sale": True
        },
        {
            "id": 3,
            "name": "Luxury Rose Gold Watch",
            "price": 120,
            "original_price": 250,
            "rating": 4.9,
            "reviews": 567,
            "sold": 2300,
            "category": "Watches",
            "image": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400",
            "badge": "Trending",
            "flash_sale": False
        },
        {
            "id": 4,
            "name": "Pearl Statement Necklace",
            "price": 65,
            "original_price": 120,
            "rating": 4.7,
            "reviews": 145,
            "sold": 678,
            "category": "Necklaces",
            "image": "https://images.unsplash.com/photo-1599643477877-530eb83abc8e?w=400",
            "badge": None,
            "flash_sale": True
        },
        {
            "id": 5,
            "name": "Adjustable Gold Ring Set",
            "price": 35,
            "original_price": 70,
            "rating": 4.5,
            "reviews": 312,
            "sold": 1500,
            "category": "Rings",
            "image": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=400",
            "badge": "Hot",
            "flash_sale": False
        },
        {
            "id": 6,
            "name": "Designer Sunglasses",
            "price": 55,
            "original_price": 110,
            "rating": 4.4,
            "reviews": 89,
            "sold": 445,
            "category": "Accessories",
            "image": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=400",
            "badge": "New",
            "flash_sale": True
        },
        {
            "id": 7,
            "name": "Silver Hoop Earrings",
            "price": 25,
            "original_price": 50,
            "rating": 4.3,
            "reviews": 567,
            "sold": 3200,
            "category": "Earrings",
            "image": "https://images.unsplash.com/photo-1630019852942-f89202989a59?w=400",
            "badge": "Best Seller",
            "flash_sale": False
        },
        {
            "id": 8,
            "name": "Charm Bracelet Collection",
            "price": 40,
            "original_price": 80,
            "rating": 4.6,
            "reviews": 234,
            "sold": 890,
            "category": "Bracelets",
            "image": "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=400",
            "badge": None,
            "flash_sale": True
        }
    ]
    return pd.DataFrame(products)

# ==========================================
# TEMU-STYLE PROFESSIONAL CSS
# ==========================================

TEMU_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    
    /* Hide Streamlit elements */
    #root > div:nth-child(1) > div > div > div > div > section > div {{padding-top: 0 !important;}}
    .stApp {{background: {BACKGROUND_COLOR} !important;}}
    
    /* Temu-style Header */
    .temu-header {{
        background: linear-gradient(135deg, {PRIMARY_ORANGE} 0%, {PRIMARY_GOLD} 100%);
        padding: 0.5rem 1rem;
        position: sticky;
        top: 0;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    
    .header-content {{
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .logo-section {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: white;
        font-weight: 800;
        font-size: 1.5rem;
        text-decoration: none;
    }}
    
    .search-bar {{
        flex: 1;
        max-width: 600px;
        position: relative;
    }}
    
    .search-input {{
        width: 100%;
        padding: 0.75rem 1rem;
        border-radius: 25px;
        border: none;
        background: white;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    .header-actions {{
        display: flex;
        gap: 1rem;
        color: white;
        align-items: center;
    }}
    
    .header-icon {{
        position: relative;
        cursor: pointer;
        font-size: 1.2rem;
        padding: 0.5rem;
    }}
    
    .cart-badge {{
        position: absolute;
        top: -5px;
        right: -5px;
        background: {DISCOUNT_COLOR};
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        font-size: 0.7rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
    }}
    
    /* Category Pills */
    .category-nav {{
        background: white;
        padding: 1rem;
        border-bottom: 1px solid #eee;
        overflow-x: auto;
        white-space: nowrap;
        -webkit-overflow-scrolling: touch;
    }}
    
    .category-pills {{
        display: flex;
        gap: 0.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    
    .category-pill {{
        padding: 0.5rem 1.25rem;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        background: white;
        color: {TEXT_SECONDARY};
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }}
    
    .category-pill.active {{
        background: {PRIMARY_ORANGE};
        color: white;
        border-color: {PRIMARY_ORANGE};
    }}
    
    /* Flash Sale Banner */
    .flash-sale-banner {{
        background: linear-gradient(90deg, {DISCOUNT_COLOR} 0%, #ff6b6b 100%);
        color: white;
        padding: 1rem;
        margin: 1rem;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3);
    }}
    
    .flash-text {{
        font-weight: 700;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .countdown {{
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }}
    
    .time-box {{
        background: rgba(255,255,255,0.2);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 700;
        font-size: 0.9rem;
    }}
    
    /* Product Grid - Temu Style Dense Grid */
    .product-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
        padding: 0.75rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    
    @media (min-width: 768px) {{
        .product-grid {{
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            padding: 1rem;
        }}
    }}
    
    @media (min-width: 1024px) {{
        .product-grid {{
            grid-template-columns: repeat(5, 1fr);
        }}
    }}
    
    /* Product Card */
    .product-card {{
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
    }}
    
    .product-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }}
    
    .product-image-container {{
        position: relative;
        aspect-ratio: 1;
        overflow: hidden;
        background: #f8f8f8;
    }}
    
    .product-image {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.3s;
    }}
    
    .product-card:hover .product-image {{
        transform: scale(1.05);
    }}
    
    .product-badge {{
        position: absolute;
        top: 8px;
        left: 8px;
        background: {DISCOUNT_COLOR};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }}
    
    .wishlist-btn {{
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(255,255,255,0.9);
        border: none;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.2s;
    }}
    
    .wishlist-btn:hover {{
        background: white;
        transform: scale(1.1);
    }}
    
    .product-info {{
        padding: 0.75rem;
    }}
    
    .product-title {{
        font-size: 0.85rem;
        color: {TEXT_PRIMARY};
        margin-bottom: 0.5rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 2.4em;
    }}
    
    .price-section {{
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
    }}
    
    .current-price {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {PRICE_COLOR};
    }}
    
    .original-price {{
        font-size: 0.8rem;
        color: {TEXT_MUTED};
        text-decoration: line-through;
    }}
    
    .discount-tag {{
        background: #ffe0e0;
        color: {DISCOUNT_COLOR};
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
    }}
    
    .product-meta {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        margin-top: 0.5rem;
    }}
    
    .rating {{
        display: flex;
        align-items: center;
        gap: 0.25rem;
        color: #ffa500;
    }}
    
    .sold-count {{
        color: {TEXT_MUTED};
    }}
    
    /* Spin Wheel Modal */
    .spin-wheel-container {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        z-index: 2000;
        text-align: center;
        max-width: 350px;
        width: 90%;
    }}
    
    .wheel {{
        width: 250px;
        height: 250px;
        border-radius: 50%;
        background: conic-gradient(
            {PRIMARY_ORANGE} 0deg 45deg,
            {ACCENT_PINK} 45deg 90deg,
            {PRIMARY_GOLD} 90deg 135deg,
            {PRIMARY_ORANGE} 135deg 180deg,
            {ACCENT_PINK} 180deg 225deg,
            {PRIMARY_GOLD} 225deg 270deg,
            {PRIMARY_ORANGE} 270deg 315deg,
            {DISCOUNT_COLOR} 315deg 360deg
        );
        margin: 1rem auto;
        position: relative;
        transition: transform 3s cubic-bezier(0.17, 0.67, 0.12, 0.99);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }}
    
    .wheel-center {{
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 60px;
        height: 60px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: {PRIMARY_ORANGE};
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
    
    .pointer {{
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 15px solid transparent;
        border-right: 15px solid transparent;
        border-top: 20px solid {DISCOUNT_COLOR};
        z-index: 10;
    }}
    
    /* Bottom Navigation */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #eee;
        display: flex;
        justify-content: space-around;
        padding: 0.5rem 0;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }}
    
    .nav-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
        color: {TEXT_MUTED};
        font-size: 0.7rem;
        cursor: pointer;
        padding: 0.25rem 1rem;
        transition: all 0.2s;
    }}
    
    .nav-item.active {{
        color: {PRIMARY_ORANGE};
    }}
    
    .nav-icon {{
        font-size: 1.3rem;
    }}
    
    /* Coupon Banner */
    .coupon-banner {{
        background: linear-gradient(90deg, {PRIMARY_GOLD} 0%, {PRIMARY_ORANGE} 100%);
        color: white;
        padding: 0.75rem 1rem;
        margin: 0.75rem;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
    }}
    
    .coupon-code {{
        background: rgba(255,255,255,0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-weight: 700;
        border: 2px dashed white;
    }}
    
    /* Product Detail Page */
    .product-detail {{
        background: white;
        min-height: 100vh;
    }}
    
    .detail-image {{
        width: 100%;
        aspect-ratio: 1;
        object-fit: cover;
    }}
    
    .detail-info {{
        padding: 1.5rem;
    }}
    
    .detail-price-row {{
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin: 1rem 0;
    }}
    
    .detail-price {{
        font-size: 2rem;
        font-weight: 800;
        color: {PRICE_COLOR};
    }}
    
    .detail-original {{
        font-size: 1.1rem;
        color: {TEXT_MUTED};
        text-decoration: line-through;
    }}
    
    .detail-discount {{
        background: {DISCOUNT_COLOR};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-weight: 700;
    }}
    
    .buy-button {{
        background: linear-gradient(90deg, {PRIMARY_ORANGE} 0%, {PRIMARY_GOLD} 100%);
        color: white;
        border: none;
        padding: 1rem;
        border-radius: 25px;
        font-size: 1.1rem;
        font-weight: 700;
        width: 100%;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(251, 119, 1, 0.4);
        transition: all 0.3s;
    }}
    
    .buy-button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(251, 119, 1, 0.5);
    }}
    
    /* Cart Drawer */
    .cart-drawer {{
        position: fixed;
        top: 0;
        right: -400px;
        width: 400px;
        height: 100vh;
        background: white;
        box-shadow: -5px 0 30px rgba(0,0,0,0.1);
        transition: right 0.3s ease;
        z-index: 2000;
        overflow-y: auto;
    }}
    
    .cart-drawer.open {{
        right: 0;
    }}
    
    /* Animations */
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
    
    .pulse {{
        animation: pulse 2s infinite;
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateY(20px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    .slide-in {{
        animation: slideIn 0.5s ease forwards;
    }}
    
    /* Responsive */
    @media (max-width: 640px) {{
        .product-grid {{
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            padding: 0.5rem;
        }}
        .temu-header {{
            padding: 0.5rem;
        }}
        .header-content {{
            gap: 0.5rem;
        }}
        .logo-section {{
            font-size: 1.2rem;
        }}
    }}
    
    /* Hide default Streamlit containers */
    .stAppViewContainer {{
        padding-bottom: 60px !important;
    }}
</style>
"""
st.markdown(TEMU_CSS, unsafe_allow_html=True)

# ==========================================
# TEMU-STYLE COMPONENTS
# ==========================================

def render_header():
    """Temu-style sticky header with search"""
    cart_count = len(st.session_state.cart)
    
    st.markdown(f"""
        <div class="temu-header">
            <div class="header-content">
                <div class="logo-section" onclick="window.location.reload()">
                    <span style="font-size: 2rem;">💎</span>
                    <span>{STORE_NAME}</span>
                </div>
                <div class="search-bar">
                    <input type="text" class="search-input" placeholder="Search for jewelry, watches, accessories..." 
                           id="searchInput" onkeypress="handleSearch(event)">
                </div>
                <div class="header-actions">
                    <div class="header-icon" onclick="toggleCart()">
                        🛒
                        {f'<span class="cart-badge">{cart_count}</span>' if cart_count > 0 else ''}
                    </div>
                    <div class="header-icon">👤</div>
                </div>
            </div>
        </div>
        
        <script>
            function handleSearch(e) {{
                if (e.key === 'Enter') {{
                    const query = document.getElementById('searchInput').value;
                    window.parent.postMessage({{type: 'streamlit:setComponentValue', value: query}}, '*');
                }}
            }}
            function toggleCart() {{
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'toggle_cart'}}, '*');
            }}
        </script>
    """, unsafe_allow_html=True)

def render_category_nav():
    """Horizontal scrolling category pills"""
    categories = ['All', 'Necklaces', 'Earrings', 'Rings', 'Bracelets', 'Watches', 'Accessories', 'New Arrivals', 'Flash Sale']
    
    cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        with cols[i]:
            is_active = st.session_state.selected_category == cat
            if st.button(cat, key=f"cat_{cat}", 
                        type="primary" if is_active else "secondary",
                        use_container_width=True):
                st.session_state.selected_category = cat
                st.rerun()

def render_flash_sale_banner():
    """Temu-style urgency banner"""
    time_remaining = FLASH_SALE_END - datetime.now()
    hours = int(time_remaining.seconds // 3600)
    minutes = int((time_remaining.seconds % 3600) // 60)
    seconds = int(time_remaining.seconds % 60)
    
    st.markdown(f"""
        <div class="flash-sale-banner slide-in">
            <div class="flash-text">
                ⚡ Flash Sale
                <span style="font-size: 0.85rem; opacity: 0.9;">Up to 70% off</span>
            </div>
            <div class="countdown">
                <span style="font-size: 0.8rem; margin-right: 0.5rem;">Ends in:</span>
                <div class="time-box">{hours:02d}</div>:
                <div class="time-box">{minutes:02d}</div>:
                <div class="time-box">{seconds:02d}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_coupon_banner():
    """Gamified coupon banner"""
    if st.session_state.show_coupon:
        st.markdown("""
            <div class="coupon-banner slide-in">
                <div>
                    <strong>🎁 Spin & Win!</strong> Get up to 50% off
                </div>
                <div class="coupon-code" style="cursor: pointer;" onclick="spinWheel()">
                    SPIN NOW
                </div>
            </div>
            <script>
                function spinWheel() {
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'spin_wheel'}, '*');
                }
            </script>
        """, unsafe_allow_html=True)

def render_product_card(product):
    """Temu-style dense product card"""
    discount = int(((product['original_price'] - product['price']) / product['original_price']) * 100)
    is_wishlisted = product['id'] in st.session_state.wishlist
    
    card_html = f"""
        <div class="product-card slide-in" onclick="selectProduct({product['id']})">
            <div class="product-image-container">
                <img src="{product['image']}" class="product-image" alt="{product['name']}">
                {f'<div class="product-badge">{product["badge"]}</div>' if product['badge'] else ''}
                <button class="wishlist-btn" onclick="event.stopPropagation(); toggleWishlist({product['id']})">
                    {'❤️' if is_wishlisted else '🤍'}
                </button>
            </div>
            <div class="product-info">
                <div class="product-title">{product['name']}</div>
                <div class="price-section">
                    <span class="current-price">{CURRENCY_SYMBOL}{product['price']}</span>
                    <span class="original-price">{CURRENCY_SYMBOL}{product['original_price']}</span>
                    <span class="discount-tag">-{discount}%</span>
                </div>
                <div class="product-meta">
                    <div class="rating">
                        ⭐ {product['rating']}
                    </div>
                    <div class="sold-count">{product['sold']}+ sold</div>
                </div>
            </div>
        </div>
        <script>
            function selectProduct(id) {{
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'product_' + id}}, '*');
            }}
            function toggleWishlist(id) {{
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'wishlist_' + id}}, '*');
            }}
        </script>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_product_grid(products_df):
    """Dense product grid layout"""
    if products_df.empty:
        st.markdown("""
            <div style="text-align: center; padding: 4rem 2rem; color: #666;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
                <h3>No products found</h3>
                <p>Try adjusting your search or category filter</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Filter by category
    if st.session_state.selected_category != 'All':
        if st.session_state.selected_category == 'Flash Sale':
            products_df = products_df[products_df['flash_sale'] == True]
        else:
            products_df = products_df[products_df['category'] == st.session_state.selected_category]
    
    # Filter by search
    if st.session_state.search_query:
        products_df = products_df[products_df['name'].str.contains(st.session_state.search_query, case=False, na=False)]
    
    st.markdown('<div class="product-grid">', unsafe_allow_html=True)
    
    for _, product in products_df.iterrows():
        col1, col2 = st.columns(2)
        with col1:
            render_product_card(product)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_product_detail(product):
    """Full product detail page"""
    discount = int(((product['original_price'] - product['price']) / product['original_price']) * 100)
    
    st.markdown(f"""
        <div class="product-detail">
            <img src="{product['image']}" class="detail-image">
            <div class="detail-info">
                <h1 style="font-size: 1.5rem; margin-bottom: 1rem; line-height: 1.3;">{product['name']}</h1>
                
                <div class="detail-price-row">
                    <span class="detail-price">{CURRENCY_SYMBOL}{product['price']}</span>
                    <span class="detail-original">{CURRENCY_SYMBOL}{product['original_price']}</span>
                    <span class="detail-discount">-{discount}%</span>
                </div>
                
                <div style="display: flex; gap: 1rem; margin: 1rem 0; color: #666; font-size: 0.9rem;">
                    <span>⭐ {product['rating']} ({product['reviews']} reviews)</span>
                    <span>|</span>
                    <span>🔥 {product['sold']}+ sold</span>
                </div>
                
                <div style="background: #f8f8f8; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                    <strong>🚚 Free Shipping</strong> on orders over GHS 100<br>
                    <small style="color: #666;">Estimated delivery: 3-5 business days</small>
                </div>
                
                <div style="margin: 1.5rem 0;">
                    <h3 style="font-size: 1rem; margin-bottom: 0.5rem;">Description</h3>
                    <p style="color: #666; line-height: 1.6;">
                        Premium quality {product['category'].lower()} crafted with attention to detail. 
                        Perfect for any occasion. Limited stock available.
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns([1, 3])
    with col1:
        qty = st.number_input("Qty", min_value=1, max_value=10, value=1, label_visibility="collapsed")
    with col2:
        if st.button("🛒 Add to Cart", use_container_width=True, type="primary"):
            cart_item = {
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'qty': qty,
                'image': product['image']
            }
            st.session_state.cart.append(cart_item)
            st.success("Added to cart!")
            time.sleep(0.5)
            st.rerun()
    
    if st.button("← Back to Shopping", use_container_width=True):
        st.session_state.selected_product = None
        st.rerun()

def render_spin_wheel():
    """Gamification spin wheel"""
    if st.session_state.get('show_spin_wheel'):
        st.markdown("""
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                        background: rgba(0,0,0,0.5); z-index: 1999;" 
                 onclick="closeWheel()"></div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class="spin-wheel-container">
                <h2 style="color: #fb7701; margin-bottom: 0.5rem;">🎰 Spin to Win!</h2>
                <p style="color: #666; margin-bottom: 1rem;">Win exclusive discounts</p>
                <div class="wheel" id="wheel">
                    <div class="pointer"></div>
                    <div class="wheel-center">SPIN</div>
                </div>
                <button class="buy-button" onclick="spin()">SPIN NOW</button>
            </div>
            <script>
                function spin() {
                    const wheel = document.getElementById('wheel');
                    const deg = 2000 + Math.random() * 2000;
                    wheel.style.transform = 'rotate(' + deg + 'deg)';
                    setTimeout(() => {
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'spin_complete'}, '*');
                    }, 3000);
                }
                function closeWheel() {
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'close_wheel'}, '*');
                }
            </script>
        """, unsafe_allow_html=True)

def render_cart_drawer():
    """Slide-out cart"""
    if st.session_state.get('show_cart'):
        cart_items = st.session_state.cart
        total = sum(item['price'] * item['qty'] for item in cart_items)
        
        st.markdown(f"""
            <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                        background: rgba(0,0,0,0.5); z-index: 1999;" 
                 onclick="closeCart()"></div>
            <div class="cart-drawer open">
                <div style="padding: 1.5rem; border-bottom: 1px solid #eee; 
                            display: flex; justify-content: space-between; align-items: center;">
                    <h2 style="margin: 0;">🛒 Your Cart ({len(cart_items)})</h2>
                    <button onclick="closeCart()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer;">×</button>
                </div>
                <div style="padding: 1.5rem;">
        """, unsafe_allow_html=True)
        
        if not cart_items:
            st.markdown("""
                <div style="text-align: center; padding: 3rem 1rem; color: #999;">
                    <div style="font-size: 4rem; margin-bottom: 1rem;">🛒</div>
                    <p>Your cart is empty</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            for item in cart_items:
                st.markdown(f"""
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem; 
                                padding-bottom: 1rem; border-bottom: 1px solid #f0f0f0;">
                        <img src="{item['image']}" style="width: 80px; height: 80px; 
                                object-fit: cover; border-radius: 8px;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; margin-bottom: 0.25rem;">{item['name']}</div>
                            <div style="color: #fb7701; font-weight: 700;">
                                {CURRENCY_SYMBOL}{item['price']} x {item['qty']}
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div style="margin-top: 2rem; padding-top: 1rem; 
                            border-top: 2px solid #eee;">
                    <div style="display: flex; justify-content: space-between; 
                                font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem;">
                        <span>Total:</span>
                        <span style="color: #fb7701;">{CURRENCY_SYMBOL}{total}</span>
                    </div>
                    <button class="buy-button">Checkout</button>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
                </div>
            </div>
            <script>
                function closeCart() {
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'close_cart'}, '*');
                }
            </script>
        """, unsafe_allow_html=True)

def render_bottom_nav():
    """Mobile-style bottom navigation"""
    st.markdown("""
        <div class="bottom-nav">
            <div class="nav-item active" onclick="setPage('home')">
                <span class="nav-icon">🏠</span>
                <span>Home</span>
            </div>
            <div class="nav-item" onclick="setPage('categories')">
                <span class="nav-icon">📑</span>
                <span>Categories</span>
            </div>
            <div class="nav-item" onclick="setPage('deals')">
                <span class="nav-icon">🏷️</span>
                <span>Deals</span>
            </div>
            <div class="nav-item" onclick="setPage('cart')">
                <span class="nav-icon">🛒</span>
                <span>Cart</span>
            </div>
            <div class="nav-item" onclick="setPage('profile')">
                <span class="nav-icon">👤</span>
                <span>Me</span>
            </div>
        </div>
        <script>
            function setPage(page) {
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'nav_' + page}, '*');
            }
        </script>
    """, unsafe_allow_html=True)

# ==========================================
# MAIN APP LOGIC
# ==========================================

def main():
    products_df = load_products()
    
    # Handle custom actions
    if st.session_state.get('action'):
        action = st.session_state.action
        
        if action.startswith('product_'):
            pid = int(action.split('_')[1])
            product = products_df[products_df['id'] == pid].iloc[0].to_dict()
            st.session_state.selected_product = product
            st.session_state.action = None
            
        elif action.startswith('wishlist_'):
            pid = int(action.split('_')[1])
            if pid in st.session_state.wishlist:
                st.session_state.wishlist.remove(pid)
            else:
                st.session_state.wishlist.append(pid)
            st.session_state.action = None
            
        elif action == 'spin_wheel':
            st.session_state.show_spin_wheel = True
            st.session_state.action = None
            
        elif action == 'spin_complete':
            discounts = [10, 15, 20, 25, 30, 50]
            result = random.choice(discounts)
            st.session_state.spin_result = result
            st.session_state.show_spin_wheel = False
            st.success(f"🎉 You won {result}% off! Use code: SPIN{result}")
            st.session_state.action = None
            
        elif action == 'close_wheel':
            st.session_state.show_spin_wheel = False
            st.session_state.action = None
            
        elif action == 'toggle_cart':
            st.session_state.show_cart = True
            st.session_state.action = None
            
        elif action == 'close_cart':
            st.session_state.show_cart = False
            st.session_state.action = None
    
    # Render UI
    render_header()
    
    if st.session_state.selected_product:
        render_product_detail(st.session_state.selected_product)
    else:
        render_category_nav()
        render_flash_sale_banner()
        render_coupon_banner()
        
        # Search handling
        search_col, _ = st.columns([3, 1])
        with search_col:
            search = st.text_input("Search", placeholder="Search products...", 
                                  label_visibility="collapsed", key="search")
            if search:
                st.session_state.search_query = search
        
        render_product_grid(products_df)
    
    render_spin_wheel()
    render_cart_drawer()
    render_bottom_nav()
    
    # CSS injection for action handling
    st.markdown("""
        <script>
            window.addEventListener('message', function(e) {
                if (e.data.type === 'streamlit:setComponentValue') {
                    const value = e.data.value;
                    const input = window.parent.document.querySelector('input[data-testid="stTextInput"]');
                    if (input) {
                        input.value = value;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            });
        </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
