import streamlit as st
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="TikTok Auto-Order", page_icon="🚀")

try:
    SECRET_CODE = st.secrets["PASSWORD"]
    API_KEY = st.secrets["SMM_KEY"]
except FileNotFoundError:
    st.error("Secrets not found. Please set ACCESS_PASSWORD and SMM_API_KEY in your .streamlit/secrets.toml or Streamlit Cloud settings.")
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



API_URL = "https://morethanpanel.com/api/v2"

# 28 Pre-filled positive comments
COMMENTS_LIST = [
    "its finally here😭😭",
    "strangersecret.com",
    "I AM CHECKING IT RIGHT NOW",
    "OMG",
    "For anyone wondering the site is strangersecret . com",
    "NO WAY NO WAY NO WAY 😭😭😭",
    "MY HANDS ARE LITERALLY SHAKING TYPING THIS",
    "if this is a prank i am suing you for emotional damage 💀",
    "RUNNING TO STRANGERSECRET.COM 🏃‍♀️💨",
    "I CANT BREATHE THIS IS REAL????",
    "SCREAMING CRYING THROWING UP",
    "BRO I WAS ABT TO GO TO SLEEP AND NOW THIS??",
    "The way I visited that link faster than I’ve ever moved in my life 👁️👄👁️",
    "ITS HAPPENING EVERYBODY STAY CALM",
    "GUYS I CHECKED IT AND… 😳",
    "wait… why does it actually look legit??",
    "I am on the site right now and I am losing my mind",
    "YALL IT WORKS IM WATCHING THE INTRO RN",
    "Confirming for everyone: IT IS NOT A DRILL 🚨",
    "My wifi is too slow for this i’m gonna cry hurry up and load 😭",
    "IF EDDIE ISN’T IN IT I DON’T WANT IT",
    "vecna is shaking rn",
    "Not me thinking we had to wait until 2027 💀",
    "Eleven better go off in this one",
    "PROTECT STEVE AT ALL COSTS",
    "Checking the site just to see if Max wakes up 🕯️"
]

def place_order(service_id, link, quantity=None, comments=None):
    payload = {
        'key': API_KEY,
        'action': 'add',
        'service': service_id,
        'link': link
    }
    if comments:
        payload['comments'] = comments
    elif quantity:
        payload['quantity'] = quantity

    try:
        response = requests.post(API_URL, data=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

st.title("🚀  MORE THAN PANEL TikTok Bulk Order Tool")
st.markdown("Enter a TikTok link below to automatically place all 7 service orders.")

video_link = st.text_input("TikTok Video Link", placeholder="https://www.tiktok.com/@user/video/...")

orders_config = [
    {"id": 4650, "name": "Custom Comments", "qty": 26, "type": "comments"},
    {"id": 2572, "name": "Shares (S. Fast)", "qty": 100, "type": "default"},
    {"id": 7724, "name": "Shares (Real)", "qty": 20, "type": "default"},
    {"id": 5827,  "name": "Saves (Never Stuck)", "qty": 100, "type": "default"},
    {"id": 1116, "name": "Saves/Favorites", "qty": 100, "type": "default"},
    {"id": 5735, "name": "Likes + Views", "qty": 50, "type": "default"},
    {"id": 1127, "name": "Likes (Female)", "qty": 20, "type": "default"},
]

if st.button("Place Orders", type="primary"):
    if not video_link:
        st.error("Please enter a valid link first.")
    else:
        st.write("---")
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        for index, order in enumerate(orders_config):
            status_text.text(f"Processing: {order['name']} (ID: {order['id']})...")
            
            if order['type'] == 'comments':
                comments_string = "\n".join(COMMENTS_LIST)
                resp = place_order(service_id=order['id'], link=video_link, comments=comments_string)
            else:
                resp = place_order(service_id=order['id'], link=video_link, quantity=order['qty'])
            
            is_success = 'order' in resp
            results.append({
                "Service": order['name'],
                "ID": order['id'],
                "Status": "✅ Success" if is_success else "❌ Failed",
                "Order ID / Error": resp.get('order', resp)
            })
            progress_bar.progress((index + 1) / len(orders_config))

        status_text.text("Done!")
        st.success("All requests processed.")
        st.table(results)
