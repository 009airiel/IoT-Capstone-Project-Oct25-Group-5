from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import requests
import json

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session'

# --- CONFIGURATION ---
MOBIUS_BASE = "http://localhost:7579/Mobius/SmartLock/data"
MOBIUS_HEADERS_GET = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Accept': 'application/json'
}

# --- FIXED HEADERS FOR UNLOCKING ---
MOBIUS_HEADERS_POST = {
    'X-M2M-RI': '12345',
    'X-M2M-Origin': 'S',
    'Content-Type': 'application/vnd.onem2m-res+json; ty=4' 
}

USERS = { "admin": "password123", "user": "unikl2025" }
SECURE_PIN = "123456"

# --- HTML ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Secure Home V - Login</title>
<style>
body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #eee; }
.box { background: white; padding: 40px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
input { padding: 10px; margin: 10px 0; width: 100%; box-sizing: border-box; }
button { padding: 10px; background-color: #007bff; color: white; border: none; width: 100%; cursor: pointer; }
</style>
</head>
<body>
<div class="box">
    <h2>Secure Home V</h2>
    {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Login</button>
    </form>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Secure Home V - Dashboard</title>
    <meta http-equiv="refresh" content="60"> 
    <style>
        body { font-family: sans-serif; text-align: center; background-color: #f0f2f5; padding-top: 50px; }
        .status-box { background: white; padding: 40px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .LOCKED { color: red; font-size: 24px; font-weight: bold; }
        .UNLOCKED { color: green; font-size: 24px; font-weight: bold; }
        
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 300px; border-radius: 10px; }
    </style>
    <script>
        function openPinModal() { document.getElementById('pinModal').style.display = 'block'; }
        function closePinModal() { document.getElementById('pinModal').style.display = 'none'; }
    </script>
</head>
<body>
    <div class="status-box">
        <h1>Smart Vault Status</h1>
        <div class="{{ current_status }}">Current State: {{ current_status }}</div>
        <p>Last Updated: {{ last_time }}</p>
        
        {% if current_status == 'LOCKED' %}
            <button onclick="openPinModal()" style="background-color: green; color: white; padding: 15px 30px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer;">UNLOCK VAULT</button>
        {% else %}
             <button disabled style="background-color: grey; color: white; padding: 15px 30px; border: none; border-radius: 5px;">VAULT IS OPEN</button>
        {% endif %}
        <br><br><a href="/logout">Logout</a>
    </div>

    <div id="pinModal" class="modal">
        <div class="modal-content">
            <h3>Security Verification</h3>
            <p>Enter 6-digit PIN to unlock:</p>
            <form method="POST" action="/unlock">
                <input type="password" name="pin" maxlength="6" style="padding: 10px; width: 80%; text-align: center; letter-spacing: 5px;" required>
                <br><br>
                <button type="submit" style="background-color: red; color: white; padding: 10px;">CONFIRM</button>
                <button type="button" onclick="closePinModal()" style="padding: 10px;">Cancel</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] in USERS and USERS[request.form['username']] == request.form['password']:
            session['user'] = request.form['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error='Invalid Credentials')
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    
    # READ FROM MOBIUS
    try:
        response = requests.get(MOBIUS_BASE + "/la", headers=MOBIUS_HEADERS_GET)
        if response.status_code == 200:
            data = response.json()
            content = data['m2m:cin']['con']
            ct = data['m2m:cin']['ct']
            formatted_time = f"{ct[0:4]}-{ct[4:6]}-{ct[6:8]} {ct[9:11]}:{ct[11:13]}"
        else:
            content = "UNKNOWN"
            formatted_time = "N/A"
    except:
        content = "CONNECTION ERROR"
        formatted_time = "N/A"

    return render_template_string(DASHBOARD_HTML, current_status=content, last_time=formatted_time)

@app.route('/unlock', methods=['POST'])
def unlock_command():
    if 'user' not in session: return redirect(url_for('login'))
    
    if request.form['pin'] == SECURE_PIN:
        print("PIN CORRECT. SENDING UNLOCK COMMAND...")
        
        # --- THE FIX IS HERE (Correct Headers) ---
        payload = { "m2m:cin": { "con": "UNLOCKED" } }
        
        try:
            r = requests.post(MOBIUS_BASE, headers=MOBIUS_HEADERS_POST, json=payload)
            print("Mobius Response:", r.status_code) # DEBUG PRINT
        except Exception as e:
            print("Error sending to Mobius:", e)

        return redirect(url_for('dashboard'))
    else:
        return "<h1>WRONG PIN!</h1><a href='/dashboard'>Back</a>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)