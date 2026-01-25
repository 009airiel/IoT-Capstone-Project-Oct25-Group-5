from flask import Flask, request, render_template, redirect, url_for, session
from datetime import datetime, timedelta
import requests
import hashlib

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session'

# --- CONFIGURATION ---
# MAKE SURE THIS MATCHES YOUR MOBIUS SETUP
MOBIUS_BASE = "http://localhost:7579/Mobius/SmartLock/data"

MOBIUS_HEADERS_GET = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Accept': 'application/json'
}

MOBIUS_HEADERS_POST = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Content-Type': 'application/vnd.onem2m-res+json; ty=4'
}

# Users Config
USERS = {
    # Password admin SHA 256
    "admin": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
    # Password user SHA 256
    "user": "e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446"
}

# --- HELPER: TIMEZONE FIXER (UTC -> Malaysia Time) ---
def fix_time(mobius_time):
    try:
        # Mobius format: YYYYMMDDTHHMMSS (e.g., 20260115T003926)
        utc_dt = datetime.strptime(mobius_time, "%Y%m%dT%H%M%S")
        local_dt = utc_dt + timedelta(hours=8) # Add 8 hours
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return mobius_time

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        
        if username in USERS:
            input_hash = hashlib.sha256(password_input.encode()).hexdigest()
            # --- ADD THIS DEBUG BLOCK ---
            print(f"DEBUG: Typed Username: '{username}'")
            print(f"DEBUG: Typed Password: '{password_input}'")
            print(f"DEBUG: Generated Hash: {input_hash}")
            print(f"DEBUG: Required Hash:  {USERS[username]}")
            # ----------------------------
            input_hash = hashlib.sha256(password_input.encode()).hexdigest()
            if input_hash == USERS[username]:
                session['user'] = username
                return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html', error=None)

# --- PASTE THIS INTO APP.PY (REPLACING THE OLD DASHBOARD FUNCTION) ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    
    current_status = "LOCKED"
    formatted_time = "Ready"
    access_logs = [] 

    # --- 1. GET STATUS ---
    try:
        r_latest = requests.get(MOBIUS_BASE + "/la", headers=MOBIUS_HEADERS_GET)
        if r_latest.status_code == 200:
            latest_data = r_latest.json()
            if 'm2m:cin' in latest_data:
                raw_status = latest_data['m2m:cin']['con']
                raw_time = latest_data['m2m:cin']['ct']
                formatted_time = fix_time(raw_time)

                if "UNLOCKED" in raw_status:
                    current_status = "UNLOCKED" 
                else:
                    current_status = "LOCKED"
    except Exception as e:
        print("Status Error:", e)

    # --- 2. GET ACCESS LOGS (THE FIX) ---
    if session['user'] == 'admin':
        try:
            r_all = requests.get(MOBIUS_BASE + "?rcn=4", headers=MOBIUS_HEADERS_GET)
            
            if r_all.status_code == 200:
                all_data = r_all.json()
                
                # --- NEW LOGIC: Look in BOTH places ---
                items = []
                
                # Case A: Standard Container
                if 'm2m:cnt' in all_data and 'm2m:cin' in all_data['m2m:cnt']:
                    items = all_data['m2m:cnt']['m2m:cin']
                
                # Case B: Your Mobius (The Fix!)
                elif 'm2m:rsp' in all_data and 'm2m:cin' in all_data['m2m:rsp']:
                    items = all_data['m2m:rsp']['m2m:cin']
                
                # Handle Single Item vs List
                if isinstance(items, dict):
                    items = [items]
                
                for item in items:
                    t = item.get('ct', '')
                    val = item.get('con', 'Unknown')
                    final_time = fix_time(t)
                    access_logs.append({'time': final_time, 'val': val})
                
                access_logs.reverse()
                print(f"DEBUG: Found {len(access_logs)} logs.")
            else:
                print(f"DEBUG: Log Fetch Failed. Code: {r_all.status_code}")

        except Exception as e:
            print("DEBUG: Log Error:", e)

        if len(access_logs) == 0:
            access_logs.append({'time': formatted_time, 'val': 'System Online (Waiting for Data...)'})

    return render_template('dashboard.html', 
                           current_status=current_status, 
                           last_time=formatted_time, 
                           logs=access_logs, 
                           user=session['user'])


@app.route('/unlock', methods=['POST'])
def unlock_command():
    if 'user' not in session: return redirect(url_for('login'))
    
    input_pin = request.form['pin']
    
    # Simple PIN check (You can switch to Hash if you want)
    if input_pin == "123456":
        
        # --- SEND TO MOBIUS ---
        payload = { "m2m:cin": { "con": "UNLOCKED" } }
        
        try:
            print("DEBUG: Sending UNLOCK command to Mobius...")
            r = requests.post(MOBIUS_BASE, headers=MOBIUS_HEADERS_POST, json=payload)
            print(f"DEBUG: Mobius Response Code: {r.status_code}") # Look for 201
            print(f"DEBUG: Mobius Response Body: {r.text}")
        except Exception as e:
            print("DEBUG: Failed to send to Mobius:", e)

        return redirect(url_for('dashboard'))
    else:
        return "<h1>WRONG PIN!</h1><a href='/dashboard'>Back</a>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)