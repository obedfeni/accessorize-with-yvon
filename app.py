import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# ============================================
# CLOUDINARY SETUP (Add near top of app.py)
# ============================================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ============================================
# CLOUDINARY IMAGE UPLOAD FUNCTION
# ============================================
def upload_to_cloudinary(image_file, filename):
    """
    Upload image to Cloudinary with automatic optimization
    Returns the secure URL or None if failed
    """
    try:
        # Reset file pointer
        image_file.seek(0)
        
        # Create a unique public_id using filename
        public_id = f"{STORE_NAME.replace(' ', '_')}/{filename.replace('.jpg', '')}"
        
        # Upload with optimization settings
        result = cloudinary.uploader.upload(
            image_file,
            public_id=public_id,
            folder=STORE_NAME.replace(' ', '_'),  # Organize by store name
            overwrite=True,
            resource_type="image",
            format="jpg",
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},  # Max dimensions
                {'quality': 'auto:good'},  # Automatic quality optimization
                {'fetch_format': 'auto'}  # Automatic format selection (WebP, etc.)
            ]
        )
        
        # Return the secure URL
        secure_url = result.get('secure_url')
        print(f"✅ Uploaded to Cloudinary: {secure_url}")
        return secure_url
    
    except Exception as e:
        print(f"❌ Cloudinary upload error: {e}")
        return None

# ============================================
# DELETE FROM CLOUDINARY (Optional)
# ============================================
def delete_from_cloudinary(image_url):
    """
    Delete image from Cloudinary using its URL
    """
    try:
        # Extract public_id from URL
        # Example: https://res.cloudinary.com/demo/image/upload/v1234/folder/image.jpg
        parts = image_url.split('/')
        if 'cloudinary.com' in image_url:
            # Find the public_id (everything after /upload/vXXXX/)
            upload_idx = parts.index('upload')
            public_id_parts = parts[upload_idx + 2:]  # Skip version number
            public_id = '/'.join(public_id_parts).replace('.jpg', '')
            
            result = cloudinary.uploader.destroy(public_id)
            print(f"🗑️ Deleted from Cloudinary: {public_id}")
            return result.get('result') == 'ok'
    except Exception as e:
        print(f"❌ Cloudinary delete error: {e}")
    return False

# ============================================
# UPDATED ADD PRODUCT SECTION
# ============================================
# Replace your current "ADD PRODUCT" section with this:

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
        image_urls = []
        
        with st.spinner("☁️ Uploading images to Cloudinary..."):
            for idx, img in enumerate(images[:3], 1):
                # Create unique filename
                filename = f"{name.replace(' ', '_')}_{idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                
                # Upload to Cloudinary
                url = upload_to_cloudinary(img, filename)
                
                if url:
                    image_urls.append(url)
                    st.success(f"✅ Image {idx} uploaded successfully")
                else:
                    st.error(f"❌ Failed to upload image {idx}")
                    st.stop()
        
        # Pad with empty strings if less than 3 images
        while len(image_urls) < 3:
            image_urls.append("")
        
        # Generate new product ID
        new_id = int(products_df["id"].max()) + 1 if not products_df.empty else 1
        status = STATUS_IN_STOCK if stock > 0 else STATUS_OUT_OF_STOCK
        
        # Save to Google Sheets (just URLs now - no size limit!)
        products_sheet.append_row([
            new_id, name, price, stock,
            image_urls[0], image_urls[1], image_urls[2],
            desc, status
        ])
        
        st.success("✅ Product added successfully!")
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# UPDATED DELETE PRODUCT (WITH CLOUDINARY CLEANUP)
# ============================================
# Replace your current "MANAGE PRODUCTS" section with this:

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
            
            if st.button(f"Delete", key=f"del_{row['id']}", use_container_width=True):
                # Delete images from Cloudinary
                for img_col in ['image1', 'image2', 'image3']:
                    img_url = row.get(img_col, '')
                    if img_url and 'cloudinary.com' in img_url:
                        delete_from_cloudinary(img_url)
                
                # Delete from Google Sheets
                products_sheet.delete_rows(row["_row"])
                st.success("Product and images deleted!")
                st.rerun()
else:
    st.info("No products yet")

st.markdown("</div>", unsafe_allow_html=True)
