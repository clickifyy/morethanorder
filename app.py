import streamlit as st
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="TikTok Auto-Order", page_icon="🚀")

# --- SECRETS & AUTH ---
try:
    SECRET_CODE = st.secrets["PASSWORD"]
    MTP_API_KEY = st.secrets["SMM_KEY"]
    # Try to get JAP key, handle gracefully if missing
    try:
        JAP_API_KEY = st.secrets["JAP_KEY"]
    except KeyError:
        JAP_API_KEY = None
except FileNotFoundError:
    st.error("Secrets not found. Please set PASSWORD, SMM_KEY, and JAP_KEY in your .streamlit/secrets.toml or Streamlit Cloud settings.")
    st.stop()

# Check query parameters (The "Special Link" logic)
query_params = st.query_params
url_code = query_params.get("secret", None)

# Initialize session state for login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Logic: If URL has correct code OR user previously logged in
if url_code == SECRET_CODE:
    st.session_state.authenticated = True

# --- LOGIN SCREEN ---
if not st.session_state.authenticated:
    st.title("🔒 Restricted Access")
    user_input = st.text_input("Enter Access Code:", type="password")
    
    if st.button("Enter"):
        if user_input == SECRET_CODE:
            st.session_state.authenticated = True
            st.rerun() # Refresh to show the tool
        else:
            st.error("Wrong Code.")
    
    # Stop the script here if not authenticated
    st.stop()

# --- API CONSTANTS ---
MTP_API_URL = "https://morethanpanel.com/api/v2"
JAP_API_URL = "https://godofpanel.com/api/v2"

# --- HELPER FUNCTIONS ---

def place_order(api_url, api_key, service_id, link, quantity=None, comments=None):
    payload = {
        'key': api_key,
        'action': 'add',
        'service': service_id,
        'link': link
    }
    
    if comments:
        payload['comments'] = comments
        # For custom comments, quantity is usually calculated automatically by the server 
        # based on lines, but some panels require sending the count explicitly.
        # However, typical SMM API for 'custom_comments' type often ignores 'quantity' field 
        # or expects it to match the line count. We'll rely on the comments field primarily.
    elif quantity:
        payload['quantity'] = quantity

    try:
        response = requests.post(api_url, data=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# --- MAIN APP UI ---

st.title("🚀 TikTok Bulk Order Tool")
st.markdown("Configure your order below.")

# 1. Video Link
video_link = st.text_input("TikTok Video Link", placeholder="https://www.tiktok.com/@user/video/...")

st.divider()

# 2. Comments Configuration
st.subheader("💬 Comments Configuration")

col1, col2 = st.columns(2)

with col1:
    comment_panel_choice = st.radio(
        "Select Panel for Comments:",
        ("MoreThanPanel", "JustAnotherPanel"),
        help="Choose which provider to use for the comments service."
    )

with col2:
    st.info("Note: All other services (Likes, Shares, Saves) will use MoreThanPanel.")

# Manual Comment Input
raw_comments = st.text_area(
    "Enter Comments (One per line):", 
    height=200,
    placeholder="Wow amazing!\nGreat video\nLove this content"
)

# Calculate quantity based on non-empty lines
comment_lines = [line for line in raw_comments.split('\n') if line.strip()]
comment_qty = len(comment_lines)

if comment_qty > 0:
    st.caption(f"✅ Detected {comment_qty} comments.")
else:
    st.caption("⚠️ Please enter comments to enable the comments service.")

st.divider()

# 3. Service Selection
st.subheader("🛠️ Select Services to Order")

# Standard Services Config (MoreThanPanel)
# Format: ID, Name, Default Qty, Type
standard_services = [
    {"id": 2572, "name": "Shares (S. Fast)", "qty": 100, "type": "default"},
    {"id": 7724, "name": "Shares (Real)", "qty": 20, "type": "default"},
    {"id": 5827, "name": "Saves (Never Stuck)", "qty": 100, "type": "default"},
    {"id": 1116, "name": "Saves/Favorites", "qty": 100, "type": "default"},
    {"id": 5735, "name": "Likes + Views", "qty": 50, "type": "default"},
    {"id": 1127, "name": "Likes (Female)", "qty": 20, "type": "default"},
]

# We will store user selections here
selected_orders = []

# A. Comment Service Selection
use_comments = st.checkbox(f"Order Custom Comments ({comment_qty})", value=True)
if use_comments:
    if not comment_qty > 0:
        st.warning("You selected Comments, but the text box is empty.")
    
    # Determine ID and Keys based on panel choice
    if comment_panel_choice == "JustAnotherPanel":
        if not JAP_API_KEY:
            st.error("JAP_KEY not found in secrets. Cannot use JustAnotherPanel.")
            cm_api_key = None
            cm_url = None
        else:
            cm_service_id = 353
            cm_api_key = JAP_API_KEY
            cm_url = JAP_API_URL
    else:
        # MoreThanPanel
        cm_service_id = 4650
        cm_api_key = MTP_API_KEY
        cm_url = MTP_API_URL

    if cm_api_key:
        selected_orders.append({
            "name": f"Custom Comments ({comment_panel_choice})",
            "id": cm_service_id,
            "qty": None, # Sent as comments string
            "type": "comments",
            "api_key": cm_api_key,
            "api_url": cm_url,
            "comments_data": "\n".join(comment_lines)
        })

# B. Standard Services Selection
for service in standard_services:
    if st.checkbox(f"{service['name']} (Qty: {service['qty']})", value=True):
        selected_orders.append({
            "name": service['name'],
            "id": service['id'],
            "qty": service['qty'],
            "type": "default",
            "api_key": MTP_API_KEY, # Always MTP
            "api_url": MTP_API_URL, # Always MTP
            "comments_data": None
        })

st.divider()

# --- EXECUTION BUTTON ---

if st.button("Place Selected Orders", type="primary"):
    if not video_link:
        st.error("❌ Please enter a valid TikTok video link.")
    elif len(selected_orders) == 0:
        st.warning("⚠️ No services selected.")
    elif use_comments and comment_qty == 0:
         st.error("❌ You selected comments but didn't write any. Please enter comments or uncheck the box.")
    else:
        st.write("---")
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        total_orders = len(selected_orders)
        
        for index, order in enumerate(selected_orders):
            status_text.text(f"Processing: {order['name']} (ID: {order['id']})...")
            
            # Prepare arguments
            resp = place_order(
                api_url=order['api_url'],
                api_key=order['api_key'],
                service_id=order['id'],
                link=video_link,
                quantity=order['qty'],
                comments=order['comments_data']
            )
            
            # Check success
            is_success = 'order' in resp
            
            # Format result for table
            results.append({
                "Service": order['name'],
                "Provider": "JAP" if "JustAnotherPanel" in order.get('api_url', '') else "MTP",
                "Status": "✅ Success" if is_success else "❌ Failed",
                "Order ID / Error": resp.get('order', resp)
            })
            
            # Update progress
            progress_bar.progress((index + 1) / total_orders)

        status_text.text("Done!")
        st.success("All requests processed.")
        st.table(results)
