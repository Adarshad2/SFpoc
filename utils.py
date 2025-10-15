
import pandas as pd, os, bcrypt

def ensure_user_db(users_csv):
    if os.path.exists(users_csv):
        try:
            df = pd.read_csv(users_csv)
            if not df.empty and 'password' in df.columns and str(df.iloc[0]['password']).startswith('$2b$'):
                return
        except Exception:
            pass
    users = [
        {'email':'novak@example.com','name':'Novak Djokovic','password':hash_password('novakpass')},
        {'email':'alice@example.com','name':'Alice Smith','password':hash_password('alicepass')},
        {'email':'bob@example.com','name':'Bob Johnson','password':hash_password('bobpass')},
        {'email':'carol@example.com','name':'Carol Lee','password':hash_password('carolpass')},
    ]
    df = pd.DataFrame(users)
    os.makedirs(os.path.dirname(users_csv), exist_ok=True)
    df.to_csv(users_csv, index=False)

def hash_password(plain):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode('utf-8'), salt).decode('utf-8')

def verify_user(users_csv, email, plain_password):
    if not os.path.exists(users_csv):
        return False, None
    df = pd.read_csv(users_csv)
    row = df[df['email'] == email]
    if row.empty:
        return False, None
    hashed = str(row.iloc[0]['password'])
    try:
        ok = bcrypt.checkpw(plain_password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        ok = False
    if ok:
        return True, {'email': email, 'name': row.iloc[0]['name']}
    return False, None

def create_user(users_csv, email, plain_password, name):
    if os.path.exists(users_csv):
        df = pd.read_csv(users_csv)
        if email in df['email'].values:
            return False, 'Email already registered'
    else:
        df = pd.DataFrame(columns=['email','name','password'])
    hashed = hash_password(plain_password)
    new = pd.DataFrame([{'email':email,'name':name,'password':hashed}])
    df = pd.concat([df, new], ignore_index=True)
    os.makedirs(os.path.dirname(users_csv), exist_ok=True)
    df.to_csv(users_csv, index=False)
    return True, 'OK'

def load_products(products_csv):
    if os.path.exists(products_csv):
        return pd.read_csv(products_csv, dtype={'product_id':str}).fillna('')
    return pd.DataFrame([])

def load_transactions(tx_csv):
    if os.path.exists(tx_csv):
        return pd.read_csv(tx_csv)
    return pd.DataFrame(columns=['order_id','user_email','product_id','product_name','quantity','price','total','order_date','status'])

def save_transaction(tx_csv, tx_obj):
    df = load_transactions(tx_csv)
    df = pd.concat([df, pd.DataFrame([tx_obj])], ignore_index=True)
    os.makedirs(os.path.dirname(tx_csv), exist_ok=True)
    df.to_csv(tx_csv, index=False)

def get_user_orders(tx_csv, user_email):
    df = load_transactions(tx_csv)
    if df.empty:
        return df
    return df[df['user_email'] == user_email]
