# ==========================================
# STORE CONFIGURATION - ACCESSORIZE WITH YVON
# ==========================================

# ==========================================
# STORE INFORMATION
# ==========================================
STORE_NAME = "Accessorize with Yvon & Knottycrafts Shop"
STORE_TAGLINE = "Curated jewelry, beauty & handmade treasures"
STORE_DESCRIPTION = "High-quality jewelry • Body splashes • Hair accessories • Crocheted fashion"

# Logo settings
LOGO_TEXT = "AYK"  # Accessorize Yvon
LOGO_SHAPE = "circle"  # Options: "square", "circle"

# ==========================================
# CONTACT INFORMATION
# ==========================================
PHONE_NUMBER = "0545651573"
WHATSAPP_NUMBER = "0545651573"
SNAPCHAT_HANDLE = "@yvonisdark"
LOCATION = "Accra, Ghana"
EMAIL = "accessorize@yvon.com"
TIKTOK_HANDLE = "@knottycrafts"

# ==========================================
# COLOR SCHEME - Elegant Pink & Gold
# ==========================================

# Background colors
BACKGROUND_COLOR = "#fef3f2"  # Soft pink/peach
CARD_BACKGROUND = "#ffffff"   # White

# Primary colors (gold/rose gold theme)
PRIMARY_COLOR = "#d97706"      # Gold/amber
BUTTON_COLOR = "#f59e0b"       # Golden yellow
BUTTON_TEXT_COLOR = "#ffffff"  # White text

# Text colors
TEXT_PRIMARY = "#78350f"       # Dark brown
TEXT_SECONDARY = "#92400e"     # Medium brown
PRICE_COLOR = "#dc2626"        # Red

# Navigation bar
NAV_BACKGROUND = "#ffffff"
NAV_TEXT_COLOR = "#78350f"

# Footer
FOOTER_BACKGROUND = "#78350f"  # Dark brown
FOOTER_TEXT_COLOR = "#ffffff"

# ==========================================
# CURRENCY
# ==========================================
CURRENCY = "GHS"
CURRENCY_SYMBOL = "GHS"

# ==========================================
# FEATURE TOGGLES
# ==========================================
SHOW_ADMIN_BUTTON = True
ENABLE_SEARCH = True
ENABLE_PRODUCT_DESCRIPTION = True
SHOW_STOCK_BADGE = True
SHOW_STATISTICS = True

# ==========================================
# PRODUCT DISPLAY
# ==========================================
PRODUCTS_PER_ROW = 3
PRODUCT_IMAGE_HEIGHT = "300px"
CARD_STYLE = "modern"

# ==========================================
# ORDER SETTINGS
# ==========================================
REQUIRE_PHONE = True
REQUIRE_LOCATION = True
MIN_ORDER_QUANTITY = 1
MAX_ORDER_QUANTITY = 50

# ==========================================
# NOTIFICATION SETTINGS
# ==========================================
ORDER_SUCCESS_TITLE = "Order Placed Successfully!"
ORDER_SUCCESS_MESSAGE = "Thank you for your order! We'll contact you via WhatsApp to confirm and arrange delivery."

TELEGRAM_NOTIFICATION_TEMPLATE = """
🛍️ <b>NEW ORDER - ACCESSORIZE WITH YVON</b>

📦 <b>Product:</b> {product_name}
👤 <b>Customer:</b> {customer_name}
📱 <b>Phone:</b> {phone}
📍 <b>Location:</b> {location}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Total:</b> {currency} {total}
🔖 <b>Reference:</b> {reference}
⏰ <b>Time:</b> {timestamp}

Status: ⏳ Pending
"""

# ==========================================
# GOOGLE SHEETS SETTINGS
# ==========================================
SHEET_NAME = "accessorize_with_yvon"
PRODUCTS_WORKSHEET = "products"
ORDERS_WORKSHEET = "orders"

# ==========================================
# TEXT CUSTOMIZATION
# ==========================================
BUTTON_ADD_TO_CART = "Order Now"
BUTTON_PLACE_ORDER = "Place Order"
BUTTON_OUT_OF_STOCK = "Sold Out"
BUTTON_ADMIN_LOGIN = "Login to Dashboard"

HEADER_FEATURED_PRODUCTS = "Our Collection"
HEADER_CHECKOUT = "Complete Your Order"
HEADER_ORDER_SUMMARY = "Order Summary"
HEADER_ADMIN_DASHBOARD = "Admin Dashboard"

LABEL_CUSTOMER_NAME = "Your Name"
LABEL_PHONE = "Phone / WhatsApp"
LABEL_LOCATION = "Delivery Location"
LABEL_QUANTITY = "Quantity"

STATUS_IN_STOCK = "In Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"
STATUS_PENDING = "Pending"

# ==========================================
# ADVANCED CUSTOMIZATION
# ==========================================
CUSTOM_CSS = """
/* Elegant feminine styling */
.product-card {
    border: 2px solid #fed7aa !important;
}
.product-card:hover {
    border-color: #f59e0b !important;
}
"""

# Footer links
FOOTER_LINKS = [
    {"icon": "📞", "text": "0545651573 / 0507262613", "url": "tel:0545651573"},
    {"icon": "👻", "text": f"Snapchat: {SNAPCHAT_HANDLE}", "url": "#"},
    {"icon": "🎵", "text": f"TikTok: {TIKTOK_HANDLE}", "url": "#"},
    {"icon": "📍", "text": LOCATION, "url": "#"},
]

# ==========================================
# BUSINESS INFORMATION
# ==========================================
BUSINESS_NAME = STORE_NAME
BUSINESS_ADDRESS = f"{LOCATION}"
BUSINESS_REG_NUMBER = ""
TAX_ID = ""

# ==========================================
# REFERENCE CODE FORMAT
# ==========================================
REFERENCE_PREFIX = "AYK"  # Accessorize Yvon
REFERENCE_LENGTH = 4
