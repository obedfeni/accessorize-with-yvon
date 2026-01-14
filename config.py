# ==========================================
# STORE CONFIGURATION FILE
# ==========================================
# Edit this file to customize your store!
# No coding knowledge required - just change the values below
# ==========================================

# ==========================================
# STORE INFORMATION
# ==========================================
STORE_NAME = "Retro Jersey Shop"
STORE_TAGLINE = "Authentic vintage jerseys"
STORE_DESCRIPTION = "Premium Vintage Jerseys • Authentic Heritage • Delivered Nationwide"

# Logo settings
LOGO_TEXT = "RJ"  # 1-2 letters work best
LOGO_SHAPE = "square"  # Options: "square", "circle"

# ==========================================
# CONTACT INFORMATION
# ==========================================
PHONE_NUMBER = "0541468102"
WHATSAPP_NUMBER = "0541468102"  # Can be same as phone
SNAPCHAT_HANDLE = "@retroshop"
LOCATION = "Accra, Ghana"
EMAIL = "info@retrojersey.shop"  # Optional

# ==========================================
# COLOR SCHEME
# ==========================================
# You can use color names or hex codes (e.g., #FF5733)

# Background colors
BACKGROUND_COLOR = "#f7f9fc"  # Light blue-gray (easy on eyes)
CARD_BACKGROUND = "#ffffff"   # White

# Primary colors (buttons, accents)
PRIMARY_COLOR = "#2874f0"      # Blue
BUTTON_COLOR = "#ffd814"       # Amazon-style yellow
BUTTON_TEXT_COLOR = "#0f1111"  # Dark text on yellow button

# Text colors
TEXT_PRIMARY = "#232f3e"       # Dark text
TEXT_SECONDARY = "#565959"     # Gray text
PRICE_COLOR = "#b12704"        # Red (Amazon style)

# Navigation bar
NAV_BACKGROUND = "#ffffff"
NAV_TEXT_COLOR = "#232f3e"

# Footer
FOOTER_BACKGROUND = "#232f3e"
FOOTER_TEXT_COLOR = "#ffffff"

# ==========================================
# CURRENCY
# ==========================================
CURRENCY = "GHS"  # Change to: USD, EUR, NGN, etc.
CURRENCY_SYMBOL = "GHS"  # What shows before price

# ==========================================
# FEATURE TOGGLES
# ==========================================
# Turn features ON (True) or OFF (False)

SHOW_ADMIN_BUTTON = True          # Show admin button on shop page
ENABLE_SEARCH = True              # Show search box
ENABLE_PRODUCT_DESCRIPTION = True # Show product descriptions
SHOW_STOCK_BADGE = True           # Show "In Stock" badge on products
SHOW_STATISTICS = True            # Show stats in admin dashboard

# ==========================================
# PRODUCT DISPLAY
# ==========================================
PRODUCTS_PER_ROW = 3              # How many products per row (1-4)
PRODUCT_IMAGE_HEIGHT = "300px"    # Height of product images
CARD_STYLE = "modern"             # Options: "modern", "minimal", "premium"

# ==========================================
# ORDER SETTINGS
# ==========================================
REQUIRE_PHONE = True              # Make phone number required
REQUIRE_LOCATION = True           # Make location required
MIN_ORDER_QUANTITY = 1            # Minimum items per order
MAX_ORDER_QUANTITY = 100          # Maximum items per order

# ==========================================
# NOTIFICATION SETTINGS
# ==========================================
# Order confirmation messages
ORDER_SUCCESS_TITLE = "Order Placed Successfully!"
ORDER_SUCCESS_MESSAGE = "Thank you for your order! We'll contact you via WhatsApp or SMS with your payment reference code."

# Admin notification message format (Telegram)
TELEGRAM_NOTIFICATION_TEMPLATE = """
🛒 <b>NEW ORDER RECEIVED!</b>

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
SHEET_NAME = "retro_jersey_shop"  # Your Google Sheet name
PRODUCTS_WORKSHEET = "products"
ORDERS_WORKSHEET = "orders"

# ==========================================
# TEXT CUSTOMIZATION
# ==========================================
# Button labels
BUTTON_ADD_TO_CART = "Add to Cart"
BUTTON_PLACE_ORDER = "Place Order"
BUTTON_OUT_OF_STOCK = "Unavailable"
BUTTON_ADMIN_LOGIN = "Login to Dashboard"

# Section headers
HEADER_FEATURED_PRODUCTS = "Featured Products"
HEADER_CHECKOUT = "Checkout"
HEADER_ORDER_SUMMARY = "Order Summary"
HEADER_ADMIN_DASHBOARD = "Admin Dashboard"

# Form labels
LABEL_CUSTOMER_NAME = "Full Name"
LABEL_PHONE = "Phone / WhatsApp"
LABEL_LOCATION = "Delivery Location"
LABEL_QUANTITY = "Quantity"

# Status messages
STATUS_IN_STOCK = "In Stock"
STATUS_OUT_OF_STOCK = "Out of Stock"
STATUS_PENDING = "Pending"

# ==========================================
# ADVANCED CUSTOMIZATION
# ==========================================

# Custom CSS (for advanced users)
CUSTOM_CSS = """
/* Add your custom CSS here */
"""

# Footer links (add your social media)
FOOTER_LINKS = [
    {"icon": "📞", "text": f"{PHONE_NUMBER}", "url": f"tel:{PHONE_NUMBER}"},
    {"icon": "📱", "text": f"Snapchat: {SNAPCHAT_HANDLE}", "url": "#"},
    {"icon": "📍", "text": LOCATION, "url": "#"},
]

# ==========================================
# BUSINESS INFORMATION (for invoices/receipts)
# ==========================================
BUSINESS_NAME = STORE_NAME
BUSINESS_ADDRESS = f"{LOCATION}"
BUSINESS_REG_NUMBER = ""  # Optional: Your business registration number
TAX_ID = ""  # Optional: Tax ID if applicable

# ==========================================
# REFERENCE CODE FORMAT
# ==========================================
# How order reference codes are generated
# Format: PREFIX-PRODUCT-LOCATION-RANDOM
REFERENCE_PREFIX = "RJ"  # Change to your store initials
REFERENCE_LENGTH = 4      # Length of random number (4 = 1000-9999)
