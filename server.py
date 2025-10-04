from flask import Flask, render_template, request, redirect, url_for, flash, session
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "harvestiq_secret_key_change_in_production"

# Dummy user database
USERS = {
    "admin@test.com": {"password": "1234", "name": "Admin User", "role": "admin"},
    "farmer@test.com": {"password": "abcd", "name": "Farmer User", "role": "farmer"},
    "buyer@test.com": {"password": "pass", "name": "Buyer User", "role": "buyer"}
}

# Dummy database for products awaiting admin review
PENDING_PRODUCTS = []

# Approved products that will be shown in marketplace
APPROVED_PRODUCTS = []

# Chat messages database - structure: {product_id: [messages]}
CHAT_MESSAGES = {}

# Add test data on startup (REMOVE THIS AFTER TESTING)
def initialize_test_data():
    PENDING_PRODUCTS.append({
        "id": 1,
        "farmer_email": "farmer@test.com",
        "farmer_name": "Farmer User",
        "product_name": "Organic Rice",
        "category": "grains",
        "description": "Premium organic rice grown without pesticides. Fresh harvest from our farm.",
        "quantity": 150.0,
        "unit": "kg",
        "price": 45.50,
        "harvest_date": "2025-01-15",
        "duration": 30,
        "status": "Pending"
    })
    
    PENDING_PRODUCTS.append({
        "id": 2,
        "farmer_email": "farmer@test.com",
        "farmer_name": "Farmer User",
        "product_name": "Fresh Tomatoes",
        "category": "vegetables",
        "description": "Juicy red tomatoes, perfect for salads and cooking. Pesticide-free.",
        "quantity": 50.0,
        "unit": "kg",
        "price": 35.00,
        "harvest_date": "2025-01-20",
        "duration": 15,
        "status": "Pending"
    })
    
    # Initialize empty chat for test products
    CHAT_MESSAGES[1] = []
    CHAT_MESSAGES[2] = []

# Call this when app starts
initialize_test_data()

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
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = email
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip()
        terms = request.form.get("terms")

        if not all([name, email, password, confirm_password, role]):
            flash("All fields are required.", "error")
            return render_template("register.html")

        if role not in ["farmer", "buyer"]:
            flash("Please select a valid role (Farmer or Buyer).", "error")
            return render_template("register.html")

        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if email in USERS:
            flash("This email is already registered. Please login instead.", "error")
            return render_template("register.html")

        if not is_valid_password(password):
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if not terms:
            flash("You must agree to the Terms & Conditions.", "error")
            return render_template("register.html")

        USERS[email] = {
            "password": password,
            "name": name,
            "role": role
        }

        flash(f"Account created successfully! Please login to continue.", "success")
        return redirect(url_for("login"))
    
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

@app.route("/submit_product", methods=["GET", "POST"])
def submit_product():
    if "user" not in session or session["role"] != "farmer":
        flash("Only farmers can submit products.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "").strip()
        price = request.form.get("price", "").strip()
        harvest_date = request.form.get("harvest_date", "").strip()
        duration = request.form.get("duration", "").strip()

        if not all([product_name, category, description, quantity, unit, price, harvest_date, duration]):
            flash("Please fill out all required fields.", "error")
            return render_template("product_submission.html")
        
        try:
            quantity = float(quantity)
            price = float(price)
            duration = int(duration)
            
            if quantity <= 0 or price <= 0 or duration <= 0:
                flash("Quantity, price, and duration must be positive values.", "error")
                return render_template("product_submission.html")
        except ValueError:
            flash("Please enter valid numeric values for quantity, price, and duration.", "error")
            return render_template("product_submission.html")
        
        # Generate new product ID
        all_products = PENDING_PRODUCTS + APPROVED_PRODUCTS
        product_id = max([p["id"] for p in all_products], default=0) + 1
        
        submission = {
            "id": product_id,
            "farmer_email": session["user"],
            "farmer_name": session["name"],
            "product_name": product_name,
            "category": category,
            "description": description,
            "quantity": quantity,
            "unit": unit,
            "price": price,
            "harvest_date": harvest_date,
            "duration": duration,
            "status": "Pending"
        }
        
        PENDING_PRODUCTS.append(submission)
        
        # Initialize empty chat for this product
        CHAT_MESSAGES[product_id] = []
        
        flash("Product submission successful! The Admin will review your listing shortly.", "success")
        return redirect(url_for("my_submissions"))

    return render_template("product_submission.html")

@app.route("/my_submissions")
def my_submissions():
    if "user" not in session or session["role"] != "farmer":
        flash("Only farmers can view submissions.", "error")
        return redirect(url_for("dashboard"))
    
    farmer_email = session["user"]
    submissions = [p for p in PENDING_PRODUCTS if p["farmer_email"] == farmer_email]
    submissions += [p for p in APPROVED_PRODUCTS if p["farmer_email"] == farmer_email]
    
    submissions.sort(key=lambda x: x["id"], reverse=True)
    
    # Add unread message count for each submission
    for submission in submissions:
        unread_count = 0
        if submission["id"] in CHAT_MESSAGES:
            for msg in CHAT_MESSAGES[submission["id"]]:
                if msg["sender_role"] == "admin" and not msg.get("read_by_farmer", False):
                    unread_count += 1
        submission["unread_count"] = unread_count
    
    return render_template("my_submissions.html", submissions=submissions)

@app.route("/admin/review")
def admin_review():
    if "user" not in session or session["role"] != "admin":
        flash("Access denied. Only admins can review products.", "error")
        return redirect(url_for("dashboard"))
    
    # Add unread message count for each pending product
    for product in PENDING_PRODUCTS:
        unread_count = 0
        if product["id"] in CHAT_MESSAGES:
            for msg in CHAT_MESSAGES[product["id"]]:
                if msg["sender_role"] == "farmer" and not msg.get("read_by_admin", False):
                    unread_count += 1
        product["unread_count"] = unread_count
    
    return render_template("admin_review.html", pending_products=PENDING_PRODUCTS)

@app.route("/admin/chat/<int:product_id>", methods=["GET", "POST"])
def admin_chat(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied. Only admins can access this chat.", "error")
        return redirect(url_for("dashboard"))
    
    # Find the product
    product = None
    for p in PENDING_PRODUCTS:
        if p["id"] == product_id:
            product = p
            break
    
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin_review"))
    
    # Mark all farmer messages as read by admin
    if product_id in CHAT_MESSAGES:
        for msg in CHAT_MESSAGES[product_id]:
            if msg["sender_role"] == "farmer":
                msg["read_by_admin"] = True
    
    if request.method == "POST":
        message_text = request.form.get("message", "").strip()
        
        if message_text:
            if product_id not in CHAT_MESSAGES:
                CHAT_MESSAGES[product_id] = []
            
            message = {
                "sender_email": session["user"],
                "sender_name": session["name"],
                "sender_role": "admin",
                "message": message_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "read_by_farmer": False,
                "read_by_admin": True
            }
            
            CHAT_MESSAGES[product_id].append(message)
            flash("Message sent!", "success")
            return redirect(url_for("admin_chat", product_id=product_id))
    
    messages = CHAT_MESSAGES.get(product_id, [])
    
    return render_template("admin_chat.html", product=product, messages=messages)

@app.route("/farmer/chat/<int:product_id>", methods=["GET", "POST"])
def farmer_chat(product_id):
    if "user" not in session or session["role"] != "farmer":
        flash("Access denied. Only farmers can access this chat.", "error")
        return redirect(url_for("dashboard"))
    
    # Find the product (check both pending and approved)
    product = None
    for p in PENDING_PRODUCTS + APPROVED_PRODUCTS:
        if p["id"] == product_id and p["farmer_email"] == session["user"]:
            product = p
            break
    
    if not product:
        flash("Product not found or you don't have access.", "error")
        return redirect(url_for("my_submissions"))
    
    # Mark all admin messages as read by farmer
    if product_id in CHAT_MESSAGES:
        for msg in CHAT_MESSAGES[product_id]:
            if msg["sender_role"] == "admin":
                msg["read_by_farmer"] = True
    
    if request.method == "POST":
        message_text = request.form.get("message", "").strip()
        
        if message_text:
            if product_id not in CHAT_MESSAGES:
                CHAT_MESSAGES[product_id] = []
            
            message = {
                "sender_email": session["user"],
                "sender_name": session["name"],
                "sender_role": "farmer",
                "message": message_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "read_by_farmer": True,
                "read_by_admin": False
            }
            
            CHAT_MESSAGES[product_id].append(message)
            flash("Message sent!", "success")
            return redirect(url_for("farmer_chat", product_id=product_id))
    
    messages = CHAT_MESSAGES.get(product_id, [])
    
    return render_template("farmer_chat.html", product=product, messages=messages)

@app.route("/admin/approve/<int:product_id>", methods=["POST"])
def admin_approve(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied. Only admins can approve products.", "error")
        return redirect(url_for("dashboard"))
    
    product = None
    for i, p in enumerate(PENDING_PRODUCTS):
        if p["id"] == product_id:
            product = PENDING_PRODUCTS.pop(i)
            break
    
    if product:
        product["status"] = "Approved"
        APPROVED_PRODUCTS.append(product)
        flash(f"Product '{product['product_name']}' has been approved and added to the marketplace!", "success")
    else:
        flash("Product not found.", "error")
    
    return redirect(url_for("admin_review"))

@app.route("/admin/reject/<int:product_id>", methods=["POST"])
def admin_reject(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied. Only admins can reject products.", "error")
        return redirect(url_for("dashboard"))
    
    product = None
    for i, p in enumerate(PENDING_PRODUCTS):
        if p["id"] == product_id:
            product = PENDING_PRODUCTS.pop(i)
            break
    
    if product:
        product["status"] = "Rejected"
        APPROVED_PRODUCTS.append(product)
        flash(f"Product '{product['product_name']}' has been rejected.", "success")
    else:
        flash("Product not found.", "error")
    
    return redirect(url_for("admin_review"))

@app.route("/logout")
def logout():
    name = session.get("name", "User")
    session.clear()
    flash(f"Goodbye, {name}! You have been logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email or not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("forgot_password"))

        flash("If an account associated with that email exists, a password reset link has been sent. Check your inbox!", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

# Debug route - remove in production
@app.route("/debug")
def debug():
    return f"""
    <h2>Debug Info</h2>
    <p>Pending Products: {len(PENDING_PRODUCTS)}</p>
    <p>Approved Products: {len(APPROVED_PRODUCTS)}</p>
    <p>Chat Messages: {len(CHAT_MESSAGES)}</p>
    <p>Products: {PENDING_PRODUCTS}</p>
    """

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)