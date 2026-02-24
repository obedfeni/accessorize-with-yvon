

# ACCESSORIZE WITH YVON - CONFIGURATION
# Professional E-Commerce Configuration
# ==========================================

# ==========================================
# STORE IDENTITY
# ==========================================
STORE_NAME = "Accessorize with Yvon & Knottycrafts Shop"
STORE_TAGLINE = "Curated jewelry, beauty & handmade treasures"
STORE_DESCRIPTION = "High-quality jewelry • Body splashes • Hair accessories • Crocheted fashion"

LOGO_TEXT = "AYK"
LOGO_SHAPE = "circle"  # Options: "circle", "square"

# ==========================================
# CONTACT & SOCIAL
# ==========================================
PHONE_NUMBER = "0545651573"
WHATSAPP_NUMBER = "0545651573"
SECONDARY_PHONE = "0507262613"
SNAPCHAT_HANDLE = "@yvonisdark"
TIKTOK_HANDLE = "@knottycrafts"
LOCATION = "New Abirem, Eastern Region, Ghana"
EMAIL = "accessorize@yvon.com"

# ==========================================
# COLOR SCHEME - Elegant Feminine Pink & Gold
# ==========================================

# Background
BACKGROUND_COLOR = "#fef3f2"      # Soft pink/peach
CARD_BACKGROUND = "#ffffff"       # Pure white
SURFACE_COLOR = "#fff5f5"         # Lighter pink surface

# Primary Brand Colors (Gold/Rose Gold)
PRIMARY_COLOR = "#d97706"         # Rich gold/amber
PRIMARY_LIGHT = "#f59e0b"         # Golden yellow
PRIMARY_DARK = "#b45309"          # Dark amber

# Accent Colors
ACCENT_COLOR = "#ec4899"          # Pink accent
ACCENT_LIGHT = "#f472b6"          # Light pink

# Text Colors
TEXT_PRIMARY = "#78350f"          # Dark brown
TEXT_SECONDARY = "#92400e"        # Medium brown
TEXT_MUTED = "#a16207"            # Muted gold

# Status Colors
PRICE_COLOR = "#dc2626"           # Vibrant red for prices
SUCCESS_COLOR = "#10b981"         # Emerald green
WARNING_COLOR = "#f59e0b"         # Amber warning
ERROR_COLOR = "#ef4444"           # Red error

# UI Elements
BORDER_COLOR = "#fed7aa"          # Peach border
SHADOW_COLOR = "rgba(217, 119, 6, 0.15)"  # Gold shadow

# ==========================================
# CURRENCY SETTINGS
# ==========================================
CURRENCY = "GHS"
CURRENCY_SYMBOL = "GHS"
CURRENCY_POSITION = "before"      # "before" or "after"

# ==========================================
# PRODUCT DISPLAY
# ==========================================
PRODUCTS_PER_ROW = 3
PRODUCTS_PER_ROW_MOBILE = 2
PRODUCT_IMAGE_QUALITY = "auto:good"
MAX_PRODUCT_IMAGES = 3

# ==========================================
# ORDER SETTINGS
# ==========================================
MIN_ORDER_QUANTITY = 1
MAX_ORDER_QUANTITY = 50
REQUIRE_PHONE = True
REQUIRE_LOCATION = True

# ==========================================
# REFERENCE CODE FORMAT
# ==========================================
REFERENCE_PREFIX = "AYK"
REFERENCE_LENGTH = 4

# ==========================================
# GOOGLE SHEETS CONFIGURATION
# ==========================================
SHEET_NAME = "accessorize_with_yvon"
PRODUCTS_WORKSHEET = "products"
ORDERS_WORKSHEET = "orders"

# Expected columns
PRODUCT_COLUMNS = ["id", "name", "price", "stock", "image1", "image2", "image3", "description", "status", "variants"]
ORDER_COLUMNS = ["name", "phone", "location", "items", "qty", "amount", "reference", "timestamp", "status", "variant"]

# ==========================================
# NOTIFICATION TEMPLATES
# ==========================================
TELEGRAM_TEMPLATE = """
🛍️ <b>NEW ORDER - ACCESSORIZE WITH YVON</b>

📦 <b>Product:</b> {product_name}
🎯 <b>Variant:</b> {variant}
👤 <b>Customer:</b> {customer_name}
📱 <b>Phone:</b> {phone}
📍 <b>Location:</b> {location}
🔢 <b>Quantity:</b> {quantity}
💰 <b>Total:</b> {currency} {total}
🔖 <b>Reference:</b> {reference}
⏰ <b>Time:</b> {timestamp}

Status: ⏳ Pending
"""

ORDER_SUCCESS_TITLE = "Order Placed Successfully!"
ORDER_SUCCESS_MESSAGE = "Thank you for your order! We'll contact you via WhatsApp to confirm and arrange delivery."

# ==========================================
# UI TEXT CUSTOMIZATION
# ==========================================
TEXT_ADD_TO_CART = "Order Now"
TEXT_PLACE_ORDER = "Place Order"
TEXT_OUT_OF_STOCK = "Sold Out"
TEXT_ADMIN_LOGIN = "Login to Dashboard"
TEXT_FEATURED_PRODUCTS = "Our Collection"
TEXT_CHECKOUT = "Complete Your Order"
TEXT_ADMIN_DASHBOARD = "Admin Dashboard"

TEXT_LABEL_NAME = "Your Name"
TEXT_LABEL_PHONE = "Phone / WhatsApp"
TEXT_LABEL_LOCATION = "Delivery Location"
TEXT_LABEL_QUANTITY = "Quantity"
TEXT_LABEL_VARIANT = "Select Size/Option"

STATUS_IN_STOCK = "In Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"
STATUS_PENDING = "Pending"
STATUS_APPROVED = "Approved"

# ==========================================
# FEATURE FLAGS
# ==========================================
SHOW_ADMIN_BUTTON = True
ENABLE_SEARCH = True
ENABLE_CAROUSEL = True
SHOW_STOCK_BADGE = True
SHOW_STATISTICS = True
ENABLE_VARIANTS = True

# ==========================================
# PERFORMANCE SETTINGS
# ==========================================
CACHE_TTL_PRODUCTS = 300      # 5 minutes
CACHE_TTL_ORDERS = 120        # 2 minutes
IMAGE_CACHE_TTL = 3600        # 1 hour

# ==========================================
# FOOTER CONFIGURATION
# ==========================================
FOOTER_LINKS = [
    {"icon": "📞", "text": "0545651573", "url": "tel:0545651573"},
    {"icon": "📱", "text": "0507262613", "url": "tel:0507262613"},
    {"icon": "👻", "text": SNAPCHAT_HANDLE, "url": "#"},
    {"icon": "🎵", "text": TIKTOK_HANDLE, "url": "#"},
    {"icon": "📍", "text": LOCATION, "url": "#"},
]

COPYRIGHT_TEXT = f"© 2026 {STORE_NAME} • All Rights Reserved"



