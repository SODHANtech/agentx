import subprocess
import sys
import os
import threading
import time
from flask import Flask, render_template, request, redirect, flash
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "simple_secret_key")

def shutdown_server():
    # Wait 1 second so the redirect response finishes sending to the browser
    time.sleep(1)
    os._exit(0)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    admin_user = os.getenv("ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")

    if username == admin_user and password == admin_pass:
        # 1. Start Uvicorn backend
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
            cwd=os.getcwd()
        )

        # 2. Start Vite/npm frontend
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=os.path.join(os.getcwd(), "frontend"),
            shell=True
        )

        # 3. Schedule Flask process exit after redirecting
        threading.Thread(target=shutdown_server).start()

        # Redirect user to the Vite application
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return redirect(frontend_url)
    
    flash("Invalid username or password.")
    return redirect('/')

if __name__ == '__main__':
    launcher_port = int(os.getenv("LAUNCHER_PORT", 5000))
    app.run(port=launcher_port)