from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# --- MOCK DATA ---
USERS = {"admin": "password123", "user1": "securehome"}
VALID_PIN = "123456"

# This list will act as your "Database" for now
# It stores dictionaries: {'time': '...', 'user': '...', 'status': '...'}
audit_logs = []

# --- HTML TEMPLATES ---
LOGIN_PAGE = """
<style>
    body { font-family: sans-serif; max-width: 400px; margin: 50px auto; text-align: center; }
    input { padding: 10px; margin: 5px; width: 100%; box-sizing: border-box;}
    button { background-color: #007bff; color: white; padding: 10px; width: 100%; border: none; cursor: pointer;}
    button:hover { background-color: #0056b3; }
</style>
<h2>Secure Home V Login</h2>
<form method="post">
    <input type="text" name="username" placeholder="Username" required><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button type="submit">Login</button>
</form>
{% if error %} <p style="color:red">{{ error }}</p> {% endif %}
"""

DASHBOARD_PAGE = """
<style>
    body { font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 20px;}
    .status-box { border: 2px solid #333; padding: 20px; text-align: center; margin-bottom: 20px; border-radius: 10px;}
    .log-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .log-table th, .log-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .log-table th { background-color: #f2f2f2; }
    .success { color: green; font-weight: bold; }
    .failed { color: red; font-weight: bold; }
</style>

<div style="display:flex; justify-content:space-between; align-items:center;">
    <h2>Welcome, {{ username }}</h2>
    <a href="/logout" style="color:red; text-decoration:none;">Logout</a>
</div>

<div class="status-box">
    <h3>Vault Control</h3>
    <p>Current Status: <strong>LOCKED</strong></p>
    
    <form action="/unlock" method="post">
        <label>Enter MFA PIN:</label>
        <input type="text" name="pin" maxlength="6" style="width: 100px; text-align:center;" required>
        <button type="submit" style="background-color: #28a745; color: white; padding: 10px 20px; border: none; cursor: pointer;">UNLOCK</button>
    </form>
    {% if message %} <p style="color: blue;">{{ message }}</p> {% endif %}
</div>

<h3>Audit Logs (FR-05)</h3>
<table class="log-table">
    <tr>
        <th>Timestamp</th>
        <th>User</th>
        <th>Action</th>
        <th>Result</th>
    </tr>
    {% for log in logs|reverse %}
    <tr>
        <td>{{ log.time }}</td>
        <td>{{ log.user }}</td>
        <td>{{ log.action }}</td>
        <td class="{{ 'success' if log.result == 'Success' else 'failed' }}">{{ log.result }}</td>
    </tr>
    {% endfor %}
</table>
"""

# --- ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user in USERS and USERS[user] == pw:
            session['user'] = user
            return redirect(url_for('dashboard'))
        error = "Invalid Username or Password"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(DASHBOARD_PAGE, username=session['user'], logs=audit_logs)

@app.route('/unlock', methods=['POST'])
def unlock():
    if 'user' not in session: return redirect(url_for('login'))
    
    pin = request.form['pin']
    user = session['user']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if pin == VALID_PIN:
        # LOG SUCCESS
        audit_logs.append({'time': timestamp, 'user': user, 'action': 'Remote Unlock', 'result': 'Success'})
        print(f"[{timestamp}] UNLOCK COMMAND SENT for {user}")
        return render_template_string(DASHBOARD_PAGE, username=user, logs=audit_logs, message="✅ Unlock Command Sent!")
    else:
        # LOG FAILURE
        audit_logs.append({'time': timestamp, 'user': user, 'action': 'Remote Unlock', 'result': 'Failed (Wrong PIN)'})
        return render_template_string(DASHBOARD_PAGE, username=user, logs=audit_logs, message="❌ Wrong PIN!")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)