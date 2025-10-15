import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_float import float_init
from utils import ensure_user_db, verify_user, create_user, load_products, load_transactions, save_transaction, get_user_orders
float_init()

from utils import ensure_user_db, verify_user, create_user, load_products, load_transactions, save_transaction, get_user_orders

st.set_page_config(page_title='Shopee-like V3', layout='wide')
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
IMG_DIR = os.path.join(DATA_DIR, 'images')

PRODUCTS_CSV = os.path.join(DATA_DIR, 'ProductDetails.csv')
TX_CSV = os.path.join(DATA_DIR, 'OrderTransactions.csv')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')

ensure_user_db(USERS_CSV)

# session defaults
ss = st.session_state
if 'page' not in ss:
    ss.page = 'login'
if 'auth' not in ss:
    ss.auth = {'logged_in': False, 'email': None, 'name': None}
if 'cart' not in ss:
    ss.cart = []
if 'chat_history' not in ss:
    ss.chat_history = []
if 'signup_mode' not in ss:
    ss.signup_mode = False
if 'banner_shown' not in ss:
    ss.banner_shown = True

ORANGE = '#EE4D2D'

# Enhanced CSS (no chatbot here)
st.markdown(f"""
<style>
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
.header {{background:#fff; padding:12px 24px; display:flex; align-items:center; gap:12px; box-shadow:0 2px 6px rgba(0,0,0,0.06);}}
.logo {{height:48px;}}
.search-box {{flex:1;}}
.product-grid {{
    display: grid; 
    grid-template-columns: repeat(3, 1fr); 
    gap: 20px; 
    padding: 20px 40px;
    max-width: 1400px;
    margin: 0 auto;
}}
.product-card {{
    background: #fff; 
    border-radius: 8px; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}}
.product-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}}
.banner {{
    background: #FFF7F5; 
    border-left: 4px solid {ORANGE}; 
    padding: 12px 16px; 
    border-radius: 8px; 
    margin: 16px 40px;
    display: flex; 
    justify-content: space-between; 
    align-items: center;
}}
@media (max-width: 1200px) {{
    .product-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 768px) {{
    .product-grid {{ grid-template-columns: 1fr; }}
}}
</style>
""", unsafe_allow_html=True)

# ---------- helper functions to post messages to parent page ----------
def post_to_parent_show(name: str):
    """Send a postMessage to the parent page to show the chat overlay."""
    # this HTML will execute inside the Streamlit iframe and post to parent
    components.html(f"""
        <script>
            if (window.parent) {{
                try {{
                    window.parent.postMessage({{type:'SHOW_CHAT', name: {repr(name)}}}, "*");
                }} catch(e) {{
                    console.log("postMessage error", e);
                }}
            }}
        </script>
    """, height=0, width=0)

def post_to_parent_hide():
    components.html("""
        <script>
            if (window.parent) {
                try {
                    window.parent.postMessage({type:'HIDE_CHAT'}, "*");
                } catch(e) { console.log("postMessage error", e); }
            }
        </script>
    """, height=0, width=0)

# ------------------- load data -------------------
products_df = load_products(PRODUCTS_CSV)
tx_df = load_transactions(TX_CSV)

# --------------- UI functions (unchanged, minor adjustments) ----------------
def show_login():
    st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)
    cols = st.columns([1,2,1])
    with cols[1]:
        st.markdown('<div style="background:#fff; padding:28px; border-radius:12px; max-width:520px; margin:auto; box-shadow:0 8px 24px rgba(0,0,0,0.08);">', unsafe_allow_html=True)
        logo = os.path.join(IMG_DIR, 'logo.png')
        if os.path.exists(logo):
            st.image(logo, width=180)
        st.header('Welcome to Shopee Demo')
        st.write('Please login or sign up to continue.')
        if not ss.signup_mode:
            email = st.text_input('Email', key='login_email')
            pwd = st.text_input('Password', type='password', key='login_pwd')
            c1, c2 = st.columns(2)
            with c1:
                if st.button('Login', use_container_width=True):
                    if not email or not pwd:
                        st.error('Please enter email and password')
                    else:
                        ok, user = verify_user(USERS_CSV, email, pwd)
                        if ok:
                            ss.auth = {'logged_in': True, 'email': user['email'], 'name': user['name']}
                            # inform parent to show chat
                            post_to_parent_show(user['name'])
                            ss.page = 'store'
                            st.rerun()
                        else:
                            st.error('Invalid credentials')
            with c2:
                if st.button('Sign Up', use_container_width=True):
                    ss.signup_mode = True
                    st.rerun()
        else:
            name = st.text_input('Full name', key='signup_name')
            email = st.text_input('Email', key='signup_email')
            pwd = st.text_input('Password', type='password', key='signup_pwd')
            pwd2 = st.text_input('Confirm Password', type='password', key='signup_pwd2')
            c1, c2 = st.columns(2)
            with c1:
                if st.button('Create Account', use_container_width=True):
                    if not all([name, email, pwd, pwd2]):
                        st.error('Fill all fields')
                    elif pwd != pwd2:
                        st.error('Passwords do not match')
                    else:
                        ok, msg = create_user(USERS_CSV, email, pwd, name)
                        if ok:
                            st.success('Account created! Please login.')
                            ss.signup_mode = False
                            st.rerun()
                        else:
                            st.error(msg)
            with c2:
                if st.button('Back to Login', use_container_width=True):
                    ss.signup_mode = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def header_bar():
    cols = st.columns([1,6,2])
    with cols[0]:
        logo = os.path.join(IMG_DIR, 'logo.png')
        if os.path.exists(logo):
            st.image(logo, width=140)
    with cols[1]:
        st.text_input('Search products...', key='search', placeholder='Search for headphones, TV, clothes...')
    with cols[2]:
        if st.button(f'🛒 Cart ({len(ss.cart)})'):
            ss.page = 'cart'
            st.rerun()
        if st.button('Logout'):
            # hide chat in parent
            post_to_parent_hide()
            ss.auth = {'logged_in': False, 'email': None, 'name': None}
            ss.page = 'login'
            st.rerun()

def show_store():
    header_bar()
    if ss.auth['logged_in'] and ss.banner_shown:
        col1, col2 = st.columns([20,1])
        with col1:
            st.markdown(f'<div class="banner"> <div>🎉 Hi {ss.auth["name"]}! Based on your recent headphone purchase, enjoy <strong>25% off</strong> your next electronics order.</div></div>', unsafe_allow_html=True)
        with col2:
            if st.button('✖', key='close_banner'):
                ss.banner_shown = False
                st.rerun()
    search_query = st.session_state.get('search', '').lower()
    shown = products_df.copy()
    if search_query:
        shown = shown[shown['name'].str.lower().str.contains(search_query) | shown['description'].str.lower().str.contains(search_query)]
        if shown.empty:
            st.warning('No products found - showing all.')
            shown = products_df
    cols_per_row = 3
    rows = [shown.iloc[i:i+cols_per_row] for i in range(0, len(shown), cols_per_row)]
    for row_data in rows:
        cols = st.columns(cols_per_row)
        for idx, (_, product) in enumerate(row_data.iterrows()):
            with cols[idx]:
                imgp = os.path.join(IMG_DIR, product['image'])
                if os.path.exists(imgp):
                    st.image(imgp, use_container_width=True)
                else:
                    st.markdown('<div style="width:100%;padding-top:100%;background:#f0f0f0;border-radius:8px;"></div>', unsafe_allow_html=True)
                st.markdown(f"<div style='padding:8px;'>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:14px;font-weight:500;margin-bottom:8px;height:36px;overflow:hidden;'>{product['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:{ORANGE};font-weight:700;font-size:18px;margin-bottom:8px;'>${product['price']}</div>", unsafe_allow_html=True)
                st.caption(product['description'][:60] + '...' if len(product['description']) > 60 else product['description'])
                qty = st.number_input('Qty', min_value=1, max_value=int(product.get('stock',10)), value=1, key=f"qty_{product['product_id']}", label_visibility="collapsed")
                if st.button('🛒 Add to Cart', key=f"add_{product['product_id']}", use_container_width=True):
                    ss.cart.append({
                        'product_id': product['product_id'],
                        'product_name': product['name'],
                        'price': float(product['price']),
                        'quantity': int(qty)
                    })
                    st.success(f"Added {qty} x {product['name']}")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

def show_cart():
    header_bar()
    st.header('Your Shopping Cart')
    if ss.cart:
        df = pd.DataFrame(ss.cart)
        df['total'] = df['price'] * df['quantity']
        st.dataframe(df[['product_name','price','quantity','total']], use_container_width=True)
        grand = df['total'].sum()
        st.markdown(f"### Grand Total: ${grand:.2f}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button('✅ Checkout', use_container_width=True):
                if not ss.auth['logged_in']:
                    st.error('Please login to checkout')
                else:
                    order_id = 'ORD' + uuid.uuid4().hex[:8].upper()
                    for item in ss.cart:
                        save_transaction(TX_CSV, {
                            'order_id': order_id,
                            'user_email': ss.auth['email'],
                            'product_id': item['product_id'],
                            'product_name': item['product_name'],
                            'quantity': item['quantity'],
                            'price': item['price'],
                            'total': item['price'] * item['quantity'],
                            'order_date': datetime.utcnow().isoformat(),
                            'status': 'confirmed'
                        })
                    st.success(f'Order {order_id} confirmed! Total: ${grand:.2f}')
                    ss.cart = []
                    st.rerun()
        with c2:
            if st.button('🗑️ Clear Cart', use_container_width=True):
                ss.cart = []
                st.rerun()
    else:
        st.info('Your cart is empty.')
        if st.button('← Back to Store'):
            ss.page = 'store'
            st.rerun()

# ----------------- router -----------------
if ss.page == 'login':
    show_login()
elif ss.page == 'store':
    show_store()
elif ss.page == 'cart':
    show_cart()
if ss.auth.get("logged_in"):
    # floating chat container
    with st.container():
        components.html(
            """
            <style>
            .floating-chat {
              position: fixed;
              bottom: 20px;
              right: 20px;
              z-index: 9999;
              font-family: system-ui,sans-serif;
            }
            .chat-btn {
              background:#EE4D2D;color:white;border:none;border-radius:50%;
              width:60px;height:60px;font-size:26px;cursor:pointer;
              box-shadow:0 4px 15px rgba(238,77,45,0.5);
            }
            .chat-box {
              position:fixed;bottom:90px;right:20px;width:360px;height:480px;
              background:white;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,0.25);
              display:none;flex-direction:column;overflow:hidden;
            }
            .chat-box.show{display:flex;}
            .chat-header{background:#EE4D2D;color:white;padding:10px;
                         display:flex;justify-content:space-between;align-items:center;}
            .chat-body{flex:1;padding:10px;background:#f5f5f5;overflow-y:auto;}
            .chat-footer{padding:8px;display:flex;gap:8px;background:#fff;}
            .chat-input{flex:1;padding:8px;border-radius:20px;border:1px solid #ddd;}
            </style>

            <div class="floating-chat">
              <button class="chat-btn" id="chat-toggle">💬</button>
              <div class="chat-box" id="chatBox">
                <div class="chat-header">
                  <span>🤖 Shopee Assistant</span>
                  <button id="closeChat" style="background:none;border:none;color:white;font-size:18px;">✕</button>
                </div>
                <div class="chat-body" id="chatBody">
                  <div>👋 Hi there! How can I help you today?</div>
                </div>
                <div class="chat-footer">
                  <input id="chatInput" class="chat-input" placeholder="Type your message..." />
                  <button id="sendMsg">📤</button>
                </div>
              </div>
            </div>

            <script>
              const toggle=document.getElementById('chat-toggle');
              const box=document.getElementById('chatBox');
              const close=document.getElementById('closeChat');
              const send=document.getElementById('sendMsg');
              const body=document.getElementById('chatBody');
              const input=document.getElementById('chatInput');
              toggle.addEventListener('click',()=>box.classList.toggle('show'));
              close.addEventListener('click',()=>box.classList.remove('show'));
              send.addEventListener('click',()=>{
                const t=input.value.trim();if(!t)return;
                const u=document.createElement('div');
                u.textContent=t;u.style.cssText='align-self:flex-end;background:#EE4D2D;color:#fff;padding:8px 12px;border-radius:16px;margin:4px 0;';
                body.appendChild(u);input.value='';
                const b=document.createElement('div');
                b.textContent='🤖 Got it!';b.style.cssText='align-self:flex-start;background:#fff;padding:8px 12px;border-radius:16px;margin:4px 0;';
                body.appendChild(b);body.scrollTop=body.scrollHeight;
              });
              input.addEventListener('keypress',e=>{if(e.key==='Enter')send.click();});
            </script>
            """,
            height=600,
            width=400,
            scrolling=False,
        ).float()
