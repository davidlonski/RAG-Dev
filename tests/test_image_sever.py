import streamlit as st
import io
import base64
from PIL import Image
import os
from pptx_rag_quizzer.Image_server import ImageServer

def create_test_image():
    """Create a test image for demonstration."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple test image
    img = Image.new('RGB', (400, 300), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Add some text to the image
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "Test Image", fill='black', font=font)
    draw.text((50, 100), "Created for ImageServer Test", fill='black', font=font)
    draw.text((50, 150), "Upload this image to test", fill='black', font=font)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr

def image_to_base64(image_bytes):
    """Convert image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

def base64_to_image(base64_string):
    """Convert base64 string to PIL Image."""
    image_bytes = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_bytes))

def main():
    st.title("🖼️ Image Server Test Interface")
    st.write("Test the ImageServer singleton with image upload, storage, and display capabilities")
    
    # Initialize session state
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []
    if 'image_server' not in st.session_state:
        st.session_state.image_server = ImageServer()
    
    # Display singleton info
    st.header("🔧 Singleton Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ImageServer Instance ID", id(st.session_state.image_server))
    with col2:
        st.metric("Database Connection", "✅ Connected" if st.session_state.image_server.mydb else "❌ Not Connected")
    
    # Connection status
    if st.session_state.image_server.mydb:
        try:
            is_connected = st.session_state.image_server.mydb.is_connected()
            st.success(f"✅ Database connection is {'active' if is_connected else 'inactive'}")
        except Exception as e:
            st.error(f"❌ Error checking connection: {e}")
    else:
        st.error("❌ No database connection available")
    
    # Image Upload Section
    st.header("📤 Image Upload")
    
    upload_method = st.radio(
        "Choose upload method:",
        ["Upload Image File", "Use Test Image", "Upload from URL"],
        horizontal=True
    )
    
    image_bytes = None
    image_name = None
    
    if upload_method == "Upload Image File":
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            help="Upload an image file to test the ImageServer"
        )
        
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            image_name = uploaded_file.name
            st.success(f"✅ File uploaded: {image_name} ({len(image_bytes)} bytes)")
            
            # Display uploaded image
            st.image(uploaded_file, caption=f"Uploaded: {image_name}", use_container_width=True)
    
    elif upload_method == "Use Test Image":
        if st.button("Generate Test Image"):
            image_bytes = create_test_image()
            image_name = "test_image.png"
            st.success(f"✅ Test image generated ({len(image_bytes)} bytes)")
            
            # Display test image
            st.image(image_bytes, caption="Generated Test Image", use_container_width=True)
    
    elif upload_method == "Upload from URL":
        image_url = st.text_input("Enter image URL:", placeholder="https://example.com/image.jpg")
        if image_url and st.button("Load from URL"):
            try:
                import requests
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_bytes = response.content
                    image_name = image_url.split('/')[-1] or "url_image.jpg"
                    st.success(f"✅ Image loaded from URL ({len(image_bytes)} bytes)")
                    
                    # Display image from URL
                    st.image(image_bytes, caption=f"Loaded from: {image_url}", use_container_width=True)
                else:
                    st.error(f"❌ Failed to load image from URL (Status: {response.status_code})")
            except Exception as e:
                st.error(f"❌ Error loading image from URL: {e}")
    
    # Upload to Database
    if image_bytes is not None:
        st.subheader("💾 Upload to Database")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Upload Image to Database"):
                with st.spinner("Uploading image to database..."):
                    try:
                        image_id = st.session_state.image_server.upload_image(image_bytes)
                        if image_id:
                            st.success(f"✅ Image uploaded successfully! ID: {image_id}")
                            
                            # Add to session state
                            image_info = {
                                'id': image_id,
                                'name': image_name,
                                'size': len(image_bytes),
                                'uploaded_at': st.session_state.image_server.mydb.get_warnings() if st.session_state.image_server.mydb else None
                            }
                            st.session_state.uploaded_images.append(image_info)
                            
                            # Display success info
                            st.info(f"📊 Image Details:")
                            st.json(image_info)
                        else:
                            st.error("❌ Failed to upload image to database")
                    except Exception as e:
                        st.error(f"❌ Error uploading image: {e}")
        
        with col2:
            if st.button("🔄 Test Singleton Pattern"):
                # Create another instance to test singleton
                test_server = ImageServer()
                st.info(f"New instance ID: {id(test_server)}")
                st.info(f"Same as original: {test_server is st.session_state.image_server}")
    
    # Display Stored Images
    st.header("📋 Stored Images")
    
    if st.session_state.uploaded_images:
        st.subheader(f"📊 Total Images: {len(st.session_state.uploaded_images)}")
        
        for i, image_info in enumerate(st.session_state.uploaded_images):
            with st.expander(f"Image {image_info['id']} - {image_info['name']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Retrieve and display image
                    if st.button(f"🖼️ Load Image {image_info['id']}", key=f"load_{i}"):
                        try:
                            retrieved_data = st.session_state.image_server.get_image(image_info['id'])
                            if retrieved_data and len(retrieved_data) > 0:
                                image_data = retrieved_data[0]  # get_image returns tuple
                                st.image(image_data, caption=f"Image {image_info['id']}", use_container_width=True)
                                st.success(f"✅ Image {image_info['id']} loaded successfully!")
                            else:
                                st.error(f"❌ Failed to load image {image_info['id']}")
                        except Exception as e:
                            st.error(f"❌ Error loading image: {e}")
                
                with col2:
                    st.write(f"**ID:** {image_info['id']}")
                    st.write(f"**Name:** {image_info['name']}")
                    st.write(f"**Size:** {image_info['size']} bytes")
                    
                    # Delete button
                    if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                        try:
                            result = st.session_state.image_server.delete_image(image_info['id'])
                            if result:
                                st.success(f"✅ Image {image_info['id']} deleted successfully!")
                                # Remove from session state
                                st.session_state.uploaded_images.pop(i)
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to delete image {image_info['id']}")
                        except Exception as e:
                            st.error(f"❌ Error deleting image: {e}")
    else:
        st.info("📝 No images uploaded yet. Upload an image to see it here!")
    
    # Get Image Test Section
    st.header("🔍 Get Image Test")
    st.write("Test retrieving images by their ID from the database")
    
    # Get image by ID
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📥 Retrieve by ID")
        
        # Input for image ID
        image_id_input = st.number_input(
            "Enter Image ID:",
            min_value=1,
            value=1,
            step=1,
            help="Enter the ID of the image you want to retrieve"
        )
        
        # Get image button
        if st.button("🔍 Get Image", key="get_image_by_id"):
            if image_id_input:
                with st.spinner(f"Retrieving image {image_id_input}..."):
                    try:
                        retrieved_data = st.session_state.image_server.get_image(image_id_input)
                        if retrieved_data and len(retrieved_data) > 0:
                            image_data = retrieved_data[0]  # get_image returns tuple
                            
                            # Store the retrieved image in session state for display
                            st.session_state.retrieved_image = {
                                'id': image_id_input,
                                'data': image_data,
                                'size': len(image_data),
                                'retrieved_at': True
                            }
                            
                            st.success(f"✅ Image {image_id_input} retrieved successfully!")
                        else:
                            st.error(f"❌ Image {image_id_input} not found in database")
                            st.session_state.retrieved_image = None
                    except Exception as e:
                        st.error(f"❌ Error retrieving image: {e}")
                        st.session_state.retrieved_image = None
    
    with col2:
        st.subheader("📊 Image Information")
        
        if 'retrieved_image' in st.session_state and st.session_state.retrieved_image:
            image_info = st.session_state.retrieved_image
            
            # Display image information
            st.write(f"**Image ID:** {image_info['id']}")
            st.write(f"**Size:** {image_info['size']:,} bytes")
            st.write(f"**Format:** Detected from data")
            st.write(f"**Status:** ✅ Retrieved successfully")
            
            # Calculate image dimensions if possible
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_info['data']))
                st.write(f"**Dimensions:** {img.size[0]} x {img.size[1]} pixels")
                st.write(f"**Mode:** {img.mode}")
            except Exception as e:
                st.write(f"**Dimensions:** Unable to determine ({e})")
    
    # Display retrieved image
    if 'retrieved_image' in st.session_state and st.session_state.retrieved_image:
        st.subheader("🖼️ Retrieved Image")
        
        image_info = st.session_state.retrieved_image
        
        # Create tabs for different display options
        tab1, tab2, tab3 = st.tabs(["Display Image", "Image Details", "Download"])
        
        with tab1:
            st.write("**Image Display:**")
            try:
                st.image(image_info['data'], caption=f"Image {image_info['id']}", use_container_width=True)
                
                # Add some display options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Refresh Display", key="refresh_display"):
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Clear Display", key="clear_display"):
                        st.session_state.retrieved_image = None
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error displaying image: {e}")
        
        with tab2:
            st.write("**Detailed Information:**")
            
            # Show raw data info
            st.write(f"**Raw Data Size:** {len(image_info['data'])} bytes")
            st.write(f"**Data Type:** {type(image_info['data'])}")
            
            # Try to get more image details
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_info['data']))
                
                st.write("**Image Properties:**")
                st.write(f"- Format: {img.format}")
                st.write(f"- Mode: {img.mode}")
                st.write(f"- Size: {img.size}")
                st.write(f"- Palette: {img.palette if img.palette else 'None'}")
                
                # Show histogram if possible
                if img.mode in ['RGB', 'L']:
                    st.write("**Color Information:**")
                    if img.mode == 'RGB':
                        r, g, b = img.split()
                        st.write(f"- Red channel range: {r.getextrema()}")
                        st.write(f"- Green channel range: {g.getextrema()}")
                        st.write(f"- Blue channel range: {b.getextrema()}")
                    else:
                        st.write(f"- Grayscale range: {img.getextrema()}")
                        
            except Exception as e:
                st.write(f"**Error analyzing image:** {e}")
        
        with tab3:
            st.write("**Download Options:**")
            
            # Create download button
            import base64
            b64 = base64.b64encode(image_info['data']).decode()
            href = f'data:image/png;base64,{b64}'
            st.markdown(f'<a href="{href}" download="image_{image_info["id"]}.png">📥 Download Image</a>', unsafe_allow_html=True)
            
            # Show data as base64
            with st.expander("📋 Base64 Data"):
                st.code(b64[:200] + "..." if len(b64) > 200 else b64)
    
    # Batch Get Test
    st.subheader("📦 Batch Get Test")
    st.write("Test retrieving multiple images at once")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Input for multiple IDs
        id_list_input = st.text_area(
            "Enter Image IDs (one per line):",
            value="1\n2\n3",
            height=100,
            help="Enter multiple image IDs, one per line"
        )
        
        if st.button("🔍 Get Multiple Images", key="get_multiple_images"):
            if id_list_input:
                try:
                    # Parse IDs
                    id_list = [int(x.strip()) for x in id_list_input.split('\n') if x.strip().isdigit()]
                    
                    if id_list:
                        st.session_state.batch_results = []
                        
                        with st.spinner(f"Retrieving {len(id_list)} images..."):
                            for img_id in id_list:
                                try:
                                    retrieved_data = st.session_state.image_server.get_image(img_id)
                                    if retrieved_data and len(retrieved_data) > 0:
                                        st.session_state.batch_results.append({
                                            'id': img_id,
                                            'data': retrieved_data[0],
                                            'size': len(retrieved_data[0]),
                                            'status': 'success'
                                        })
                                    else:
                                        st.session_state.batch_results.append({
                                            'id': img_id,
                                            'data': None,
                                            'size': 0,
                                            'status': 'not_found'
                                        })
                                except Exception as e:
                                    st.session_state.batch_results.append({
                                        'id': img_id,
                                        'data': None,
                                        'size': 0,
                                        'status': f'error: {e}'
                                    })
                        
                        st.success(f"✅ Batch retrieval completed!")
                    else:
                        st.error("❌ No valid IDs found")
                except Exception as e:
                    st.error(f"❌ Error in batch retrieval: {e}")
    
    with col2:
        # Display batch results
        if 'batch_results' in st.session_state and st.session_state.batch_results:
            st.write("**Batch Results:**")
            
            for result in st.session_state.batch_results:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                st.write(f"{status_icon} ID {result['id']}: {result['status']}")
                
                if result['status'] == 'success':
                    st.write(f"   Size: {result['size']:,} bytes")
                    
                    # Show thumbnail
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(result['data']))
                        # Resize for thumbnail
                        img.thumbnail((100, 100))
                        st.image(img, caption=f"ID {result['id']}", width=100)
                    except Exception as e:
                        st.write(f"   Error displaying: {e}")
    
    # Database Operations
    st.header("🗄️ Database Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Test Connection"):
            try:
                connection = st.session_state.image_server.get_connection()
                if connection:
                    st.success("✅ Database connection is working!")
                else:
                    st.error("❌ Database connection failed!")
            except Exception as e:
                st.error(f"❌ Connection test failed: {e}")
    
    with col2:
        if st.button("🔄 Reconnect"):
            try:
                st.session_state.image_server.close_connection()
                connection = st.session_state.image_server.get_connection()
                if connection:
                    st.success("✅ Reconnected successfully!")
                else:
                    st.error("❌ Reconnection failed!")
            except Exception as e:
                st.error(f"❌ Reconnection error: {e}")
    
    with col3:
        if st.button("🧹 Clear All Images"):
            if st.session_state.uploaded_images:
                try:
                    for image_info in st.session_state.uploaded_images:
                        st.session_state.image_server.delete_image(image_info['id'])
                    st.session_state.uploaded_images = []
                    st.success("✅ All images cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error clearing images: {e}")
            else:
                st.info("📝 No images to clear")
    
    # Performance Metrics
    st.header("📈 Performance Metrics")
    
    if st.session_state.uploaded_images:
        total_size = sum(img['size'] for img in st.session_state.uploaded_images)
        avg_size = total_size / len(st.session_state.uploaded_images)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Images", len(st.session_state.uploaded_images))
        with col2:
            st.metric("Total Size", f"{total_size:,} bytes")
        with col3:
            st.metric("Average Size", f"{avg_size:,.0f} bytes")
    
    # Debug Information
    with st.expander("🔧 Debug Information"):
        st.write("**ImageServer Instance Details:**")
        st.json({
            "instance_id": id(st.session_state.image_server),
            "database_connected": st.session_state.image_server.mydb is not None,
            "connection_status": st.session_state.image_server.mydb.is_connected() if st.session_state.image_server.mydb else False,
            "uploaded_images_count": len(st.session_state.uploaded_images)
        })

if __name__ == "__main__":
    main()







