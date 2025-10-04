from flask import Flask, render_template, request, redirect, url_for, flash, session
import re

app = Flask(__name__)
app.secret_key = "harvestiq_secret_key_change_in_production"

# Dummy user database (replace with a real database later)
USERS = {
    "admin@test.com": {"password": "1234", "name": "Admin User", "role": "admin"},
    "farmer@test.com": {"password": "abcd", "name": "Farmer User", "role": "farmer"},
    "buyer@test.com": {"password": "pass", "name": "Buyer User", "role": "buyer"}
}

# Helper function to validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to validate password strength
def is_valid_password(password):
    return len(password) >= 8

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect to dashboard
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validate input
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return redirect(url_for("login"))

        # Check credentials
        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = email
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}! 👋", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # If user is already logged in, redirect to dashboard
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip()
        terms = request.form.get("terms")

        # Validation
        if not all([name, email, password, confirm_password, role]):
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if role not in ["farmer", "buyer"]:
            flash("Please select a valid role (Farmer or Buyer).", "error")
            return redirect(url_for("register"))

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if email in USERS:
            flash("This email is already registered. Please login instead.", "error")
            return redirect(url_for("register"))

        if not is_valid_password(password):
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if not terms:
            flash("You must agree to the Terms & Conditions.", "error")
            return redirect(url_for("register"))

        # Register the new user with selected role
        USERS[email] = {
            "password": password,
            "name": name,
            "role": role
        }

        flash(f"Account created successfully! Welcome, {name}! 🎉", "success")
        
        # Auto-login after registration
        session["user"] = email
        session["name"] = name
        session["role"] = role
        
        return redirect(url_for("dashboard"))
    
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please login to access the dashboard.", "error")
        return redirect(url_for("login"))
    
    return render_template("dashboard.html", 
                         user=session["user"], 
                         name=session.get("name", "User"),
                         role=session["role"])

@app.route("/logout")
def logout():
    name = session.get("name", "User")
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out successfully. 👋", "success")
    return redirect(url_for("login"))

@app.route("/forgot_password")
def forgot_password():
    # Placeholder for forgot password functionality
    flash("Password reset functionality coming soon! Contact admin for now.", "error")
    return redirect(url_for("login"))

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)