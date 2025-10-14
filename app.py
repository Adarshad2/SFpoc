
import streamlit as st
import pandas as pd, os, uuid
from datetime import datetime
from utils import ensure_user_db, verify_user, create_user, load_products, load_transactions, save_transaction, get_user_orders

st.set_page_config(page_title='Shopee-like Demo', layout='wide', initial_sidebar_state='collapsed')
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
IMG_DIR = os.path.join(DATA_DIR, 'images')

PRODUCTS_CSV = os.path.join(DATA_DIR, 'ProductDetails.csv')
TX_CSV = os.path.join(DATA_DIR, 'OrderTransactions.csv')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')

ensure_user_db(USERS_CSV)

# session state defaults
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'auth' not in st.session_state:
    st.session_state.auth = {'logged_in': False, 'email': None, 'name': None}
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'show_chat' not in st.session_state:
    st.session_state.show_chat = False
if 'signup_mode' not in st.session_state:
    st.session_state.signup_mode = False

ORANGE = '#EE4D2D'

st.markdown(f"""
<style>
body {{background: linear-gradient(180deg, {ORANGE}, #FF7247);}}
.login-card {{background: white; border-radius:12px; padding:24px; box-shadow:0 8px 24px rgba(0,0,0,0.12); max-width:480px; margin:auto;}}
.header {{background:white; padding:10px 20px; display:flex; align-items:center; justify-content:space-between;}}
.product-card {{background:white; border-radius:10px; padding:12px; box-shadow:0 6px 18px rgba(0,0,0,0.06); margin-bottom:12px;}}
.float-chat-btn {{position:fixed; right:20px; bottom:20px; background:{ORANGE}; color:white; border-radius:50%; width:56px; height:56px; display:flex; align-items:center; justify-content:center; box-shadow:0 6px 18px rgba(0,0,0,0.2); z-index:9999;}}
.float-chat-box {{position:fixed; right:20px; bottom:88px; width:360px; max-height:500px; z-index:9999; background:white; border-radius:8px; box-shadow:0 6px 18px rgba(0,0,0,0.2); overflow:auto; padding:8px;}}
</style>
""", unsafe_allow_html=True)

products_df = load_products(PRODUCTS_CSV)
tx_df = load_transactions(TX_CSV)

def show_login():
    st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        logo = os.path.join(IMG_DIR, 'logo.png')
        if os.path.exists(logo):
            st.image(logo, width=160)
        st.markdown('<h2 style="color:#EE4D2D; margin-top:8px;">Welcome to Shopee Demo</h2>', unsafe_allow_html=True)
        st.write('Please login or sign up to continue.')
        if not st.session_state.signup_mode:
            email = st.text_input('Email', key='login_email')
            pwd = st.text_input('Password', type='password', key='login_pwd')
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Login', use_container_width=True):
                    if not email or not pwd:
                        st.error('Enter both email and password')
                    else:
                        ok, user = verify_user(USERS_CSV, email, pwd)
                        if ok:
                            st.session_state.auth = {'logged_in': True, 'email': user['email'], 'name': user['name']}
                            st.session_state.page = 'store'
                            st.rerun()
                        else:
                            st.error('Invalid credentials')
            with col2:
                if st.button('Sign Up', use_container_width=True):
                    st.session_state.signup_mode = True
                    st.rerun()
        else:
            name = st.text_input('Full name', key='signup_name')
            email = st.text_input('Email', key='signup_email')
            pwd = st.text_input('Password', type='password', key='signup_pwd')
            pwd2 = st.text_input('Confirm Password', type='password', key='signup_pwd2')
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Create Account', use_container_width=True):
                    if not all([name, email, pwd, pwd2]):
                        st.error('Fill all fields')
                    elif pwd != pwd2:
                        st.error('Passwords do not match')
                    else:
                        ok, msg = create_user(USERS_CSV, email, pwd, name)
                        if ok:
                            st.success('Account created! Please login.')
                            st.session_state.signup_mode = False
                            st.rerun()
                        else:
                            st.error(msg)
            with col2:
                if st.button('Back to Login', use_container_width=True):
                    st.session_state.signup_mode = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def header_bar():
    st.markdown('<div class="header">', unsafe_allow_html=True)
    cols = st.columns([1,6,1])
    with cols[0]:
        logo = os.path.join(IMG_DIR, 'logo.png')
        if os.path.exists(logo):
            st.image(logo, width=140)
    with cols[1]:
        st.text_input('Search products...', key='search')
    with cols[2]:
        if st.button('Cart (' + str(len(st.session_state.cart)) + ')'):
            st.session_state.page = 'cart'
        if st.button('Logout'):
            st.session_state.auth = {'logged_in': False, 'email': None, 'name': None}
            st.session_state.page = 'login'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_store():
    header_bar()
    if st.session_state.auth['logged_in'] and st.session_state.auth['name'] == 'Novak Djokovic':
        st.info(f"Hi {st.session_state.auth['name']}! Based on your recent headphone purchase, enjoy 25% off your next electronics order.")
    tabs = st.tabs(['All','Electronics','Clothes'])
    for t in tabs:
        with t:
            cat = t._caption
            if cat == 'All':
                shown = products_df
            else:
                shown = products_df[products_df['category'] == cat]
            cols = st.columns(3)
            i=0
            for _, row in shown.iterrows():
                c = cols[i%3]
                with c:
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    imgp = os.path.join(IMG_DIR, row['image'])
                    if os.path.exists(imgp):
                        st.image(imgp, use_column_width=True)
                    else:
                        st.write('[Image missing]')
                    st.markdown(f"**{row['name']}**")
                    st.write(row['description'])
                    st.markdown(f"<div style='color:{ORANGE}; font-weight:700;'>${row['price']}</div>", unsafe_allow_html=True)
                    qty = st.number_input('Qty', min_value=1, max_value=int(row.get('stock',10)), key=f"q_{row['product_id']}")
                    if st.button('Add to cart', key=f"add_{row['product_id']}"):
                        st.session_state.cart.append({'product_id': row['product_id'], 'product_name': row['name'], 'price': float(row['price']), 'quantity': int(qty)})
                        st.success(f"Added {qty} x {row['name']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                i+=1

def show_cart():
    header_bar()
    st.header('Your cart')
    if st.session_state.cart:
        df = pd.DataFrame(st.session_state.cart)
        df['total'] = df['price'] * df['quantity']
        st.table(df[['product_name','price','quantity','total']])
        total = df['total'].sum()
        st.markdown(f"### Total: ${total:.2f}")
        col1,col2=st.columns([1,1])
        with col1:
            if st.button('Checkout'):
                if not st.session_state.auth['logged_in']:
                    st.error('Please login to checkout')
                else:
                    order_id = 'ORD' + uuid.uuid4().hex[:8].upper()
                    for item in st.session_state.cart:
                        save_transaction(TX_CSV, {
                            'order_id': order_id,
                            'user_email': st.session_state.auth['email'],
                            'product_id': item['product_id'],
                            'product_name': item['product_name'],
                            'quantity': item['quantity'],
                            'price': item['price'],
                            'total': item['price']*item['quantity'],
                            'order_date': datetime.utcnow().isoformat(),
                            'status': 'confirmed'
                        })
                    st.success(f"Order {order_id} confirmed. Total: ${total:.2f}")
                    st.session_state.cart = []
        with col2:
            if st.button('Clear Cart'):
                st.session_state.cart=[]
    else:
        st.info('Cart is empty')

def show_chatbox():
    st.markdown('<div class="float-chat-btn">💬</div>', unsafe_allow_html=True)
    if st.session_state.show_chat:
        st.markdown('<div class="float-chat-box">', unsafe_allow_html=True)
        for m in st.session_state.chat_history:
            if m['from']=='user':
                st.markdown(f"**You:** {m['text']}")
            else:
                st.markdown(f"**Agent:** {m['text']}")
        txt = st.text_input('Message', key='chat_msg')
        if st.button('Send', key='send_chat'):
            if txt:
                st.session_state.chat_history.append({'from':'user','text':txt})
                q=txt.lower()
                if 'camera' in q:
                    resp='Here are camera options: Mirrorless Camera — $2499.99'
                elif 'recent orders' in q or 'my recent orders' in q:
                    if st.session_state.auth['logged_in']:
                        orders = get_user_orders(TX_CSV, st.session_state.auth['email'])
                        if orders.empty:
                            resp='No recent orders found.'
                        else:
                            resp='; '.join(orders['product_name'].tolist())
                    else:
                        resp='Please login to view orders.'
                elif 'warrant' in q or 'warranty' in q:
                    resp='I will escalate you to a live agent with full context.'
                else:
                    resp='Sorry, I did not understand. Ask about products, orders, or warranty.'
                st.session_state.chat_history.append({'from':'agent','text':resp})
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.page == 'login':
    show_login()
else:
    if st.session_state.page == 'store':
        show_store()
    elif st.session_state.page == 'cart':
        show_cart()
    if st.session_state.auth['logged_in']:
        show_chatbox()
