from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = "harvestiq_secret_key_change_in_production"

# Upload configuration
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///harvestiq.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Session configurations
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_email = db.Column(db.String(120), nullable=False)
    farmer_name = db.Column(db.String(120), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    harvest_date = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    image_filename = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    sender_email = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(120), nullable=False)
    sender_role = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read_by_farmer = db.Column(db.Boolean, default=False)
    read_by_admin = db.Column(db.Boolean, default=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_email = db.Column(db.String(120), nullable=False)
    buyer_name = db.Column(db.String(120), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    farmer_email = db.Column(db.String(120), nullable=False)
    farmer_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database and create test data
def initialize_database():
    with app.app_context():
        db.create_all()
        
        # Create test users
        if not User.query.filter_by(email='admin@test.com').first():
            admin = User(email='admin@test.com', password='1234', name='Admin User', role='admin')
            db.session.add(admin)
        
        if not User.query.filter_by(email='farmer@test.com').first():
            farmer = User(email='farmer@test.com', password='abcd', name='Farmer User', role='farmer')
            db.session.add(farmer)
        
        if not User.query.filter_by(email='buyer@test.com').first():
            buyer = User(email='buyer@test.com', password='pass', name='Buyer User', role='buyer')
            db.session.add(buyer)
        
        db.session.commit()
        
        # Create test products (Approved so they show in marketplace)
        if Product.query.count() == 0:
            test_products = [
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Organic Rice',
                    category='grains',
                    description='Premium organic rice grown without pesticides. Perfect for daily consumption.',
                    quantity=150.0,
                    unit='kg',
                    price=45.50,
                    harvest_date='2025-01-15',
                    duration=30,
                    status='Approved'
                ),
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Fresh Tomatoes',
                    category='vegetables',
                    description='Juicy red tomatoes, pesticide-free. Great for salads and cooking.',
                    quantity=50.0,
                    unit='kg',
                    price=35.00,
                    harvest_date='2025-01-20',
                    duration=15,
                    status='Approved'
                ),
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Sweet Corn',
                    category='vegetables',
                    description='Fresh sweet corn perfect for grilling. Harvested at peak sweetness.',
                    quantity=100.0,
                    unit='kg',
                    price=25.00,
                    harvest_date='2025-01-18',
                    duration=20,
                    status='Approved'
                ),
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Organic Carrots',
                    category='vegetables',
                    description='Crunchy organic carrots, rich in vitamins. No chemicals used.',
                    quantity=75.0,
                    unit='kg',
                    price=40.00,
                    harvest_date='2025-01-22',
                    duration=25,
                    status='Approved'
                ),
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Fresh Mangoes',
                    category='fruits',
                    description='Sweet and juicy Philippine mangoes. Perfect ripeness guaranteed.',
                    quantity=60.0,
                    unit='kg',
                    price=80.00,
                    harvest_date='2025-01-25',
                    duration=10,
                    status='Approved'
                ),
                Product(
                    farmer_email='farmer@test.com',
                    farmer_name='Farmer User',
                    product_name='Fresh Basil',
                    category='herbs',
                    description='Aromatic fresh basil leaves. Perfect for Italian dishes.',
                    quantity=20.0,
                    unit='kg',
                    price=120.00,
                    harvest_date='2025-01-19',
                    duration=7,
                    status='Approved'
                )
            ]
            
            for product in test_products:
                db.session.add(product)
            
            db.session.commit()

initialize_database()

# Helper functions
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    return len(password) >= 8

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session.clear()
            session["user"] = user.email
            session["name"] = user.name
            session["role"] = user.role
            session.permanent = False
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return render_template("login.html")
    
    if "user" in session:
        return redirect(url_for("dashboard"))
    
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

        if User.query.filter_by(email=email).first():
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

        new_user = User(email=email, password=password, name=name, role=role)
        db.session.add(new_user)
        db.session.commit()

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

# FARMER ROUTES
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

        # Handle file upload
        image_filename = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    image_filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                else:
                    flash("Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WEBP).", "error")
                    return render_template("product_submission.html")

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
            flash("Please enter valid numeric values.", "error")
            return render_template("product_submission.html")
        
        new_product = Product(
            farmer_email=session["user"],
            farmer_name=session["name"],
            product_name=product_name,
            category=category,
            description=description,
            quantity=quantity,
            unit=unit,
            price=price,
            harvest_date=harvest_date,
            duration=duration,
            status='Pending',
            image_filename=image_filename
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash("Product submitted successfully!", "success")
        return redirect(url_for("my_submissions"))

    return render_template("product_submission.html")

@app.route("/my_submissions")
def my_submissions():
    if "user" not in session or session["role"] != "farmer":
        flash("Only farmers can view submissions.", "error")
        return redirect(url_for("dashboard"))
    
    submissions = Product.query.filter_by(farmer_email=session["user"]).order_by(Product.id.desc()).all()
    
    for submission in submissions:
        unread_count = ChatMessage.query.filter_by(
            product_id=submission.id,
            sender_role='admin',
            read_by_farmer=False
        ).count()
        submission.unread_count = unread_count
    
    return render_template("my_submissions.html", submissions=submissions)

@app.route("/farmer/chat/<int:product_id>", methods=["GET", "POST"])
def farmer_chat(product_id):
    if "user" not in session or session["role"] != "farmer":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    product = Product.query.filter_by(id=product_id, farmer_email=session["user"]).first()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("my_submissions"))
    
    ChatMessage.query.filter_by(
        product_id=product_id,
        sender_role='admin',
        read_by_farmer=False
    ).update({'read_by_farmer': True})
    db.session.commit()
    
    if request.method == "POST":
        message_text = request.form.get("message", "").strip()
        
        if message_text:
            new_message = ChatMessage(
                product_id=product_id,
                sender_email=session["user"],
                sender_name=session["name"],
                sender_role='farmer',
                message=message_text,
                read_by_farmer=True,
                read_by_admin=False
            )
            db.session.add(new_message)
            db.session.commit()
            flash("Message sent!", "success")
            return redirect(url_for("farmer_chat", product_id=product_id))
    
    messages = ChatMessage.query.filter_by(product_id=product_id).order_by(ChatMessage.timestamp).all()
    return render_template("farmer_chat.html", product=product, messages=messages)

# ADMIN ROUTES
@app.route("/admin/review")
def admin_review():
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    pending_products = Product.query.filter_by(status='Pending').order_by(Product.id.desc()).all()
    
    for product in pending_products:
        unread_count = ChatMessage.query.filter_by(
            product_id=product.id,
            sender_role='farmer',
            read_by_admin=False
        ).count()
        product.unread_count = unread_count
    
    return render_template("admin_review.html", pending_products=pending_products)

@app.route("/admin/manage_listings")
def admin_manage_listings():
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    approved_products = Product.query.filter_by(status='Approved').order_by(Product.created_at.desc()).all()
    rejected_products = Product.query.filter_by(status='Rejected').order_by(Product.created_at.desc()).all()
    
    return render_template("admin_manage_listings.html", 
                         approved_products=approved_products,
                         rejected_products=rejected_products)

@app.route("/admin/remove_listing/<int:product_id>", methods=["POST"])
def admin_remove_listing(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    product = Product.query.get(product_id)
    if product:
        # Delete the image file if it exists
        if product.image_filename:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete all chat messages for this product
        ChatMessage.query.filter_by(product_id=product_id).delete()
        
        # Delete from database
        db.session.delete(product)
        db.session.commit()
        flash(f"Product '{product.product_name}' has been removed.", "success")
    else:
        flash("Product not found.", "error")
    
    return redirect(url_for("admin_manage_listings"))

@app.route("/admin/chat/<int:product_id>", methods=["GET", "POST"])
def admin_chat(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    product = Product.query.filter_by(id=product_id, status='Pending').first()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin_review"))
    
    ChatMessage.query.filter_by(
        product_id=product_id,
        sender_role='farmer',
        read_by_admin=False
    ).update({'read_by_admin': True})
    db.session.commit()
    
    if request.method == "POST":
        message_text = request.form.get("message", "").strip()
        
        if message_text:
            new_message = ChatMessage(
                product_id=product_id,
                sender_email=session["user"],
                sender_name=session["name"],
                sender_role='admin',
                message=message_text,
                read_by_admin=True,
                read_by_farmer=False
            )
            db.session.add(new_message)
            db.session.commit()
            flash("Message sent!", "success")
            return redirect(url_for("admin_chat", product_id=product_id))
    
    messages = ChatMessage.query.filter_by(product_id=product_id).order_by(ChatMessage.timestamp).all()
    return render_template("admin_chat.html", product=product, messages=messages)

@app.route("/admin/approve/<int:product_id>", methods=["POST"])
def admin_approve(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    product = Product.query.get(product_id)
    if product:
        product.status = 'Approved'
        db.session.commit()
        flash(f"Product '{product.product_name}' approved!", "success")
    
    return redirect(url_for("admin_review"))

@app.route("/admin/reject/<int:product_id>", methods=["POST"])
def admin_reject(product_id):
    if "user" not in session or session["role"] != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))
    
    product = Product.query.get(product_id)
    if product:
        product.status = 'Rejected'
        db.session.commit()
        flash(f"Product '{product.product_name}' rejected.", "success")
    
    return redirect(url_for("admin_review"))

# BUYER ROUTES
@app.route("/marketplace")
def marketplace():
    if "user" not in session or session["role"] != "buyer":
        flash("Only buyers can access the marketplace.", "error")
        return redirect(url_for("dashboard"))
    
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    # Query only APPROVED products
    products_query = Product.query.filter_by(status='Approved')
    
    if search_query:
        products_query = products_query.filter(
            db.or_(
                Product.product_name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%'),
                Product.farmer_name.ilike(f'%{search_query}%')
            )
        )
    
    if category_filter:
        products_query = products_query.filter_by(category=category_filter)
    
    products = products_query.order_by(Product.created_at.desc()).all()
    
    return render_template("marketplace.html", 
                         products=products,
                         search_query=search_query,
                         category_filter=category_filter)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session or session["role"] != "buyer":
        flash("Only buyers can checkout.", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        cart_data = request.form.get("cart_data", "")
        payment_method = request.form.get("payment_method", "").strip()
        delivery_address = request.form.get("delivery_address", "").strip()
        contact_number = request.form.get("contact_number", "").strip()
        
        if not all([cart_data, payment_method, delivery_address, contact_number]):
            flash("Please fill out all required fields.", "error")
            return render_template("checkout.html")
        
        try:
            cart = json.loads(cart_data)
        except:
            flash("Invalid cart data.", "error")
            return redirect(url_for("marketplace"))
        
        # Create orders for each item in cart
        order_count = 0
        for item in cart:
            product = Product.query.get(item['id'])
            if not product or product.status != 'Approved':
                continue
            
            if item['quantity'] > product.quantity:
                flash(f"Sorry, only {product.quantity} {product.unit} of {product.product_name} available.", "error")
                continue
            
            total_amount = item['quantity'] * product.price
            
            new_order = Order(
                buyer_email=session["user"],
                buyer_name=session["name"],
                product_id=product.id,
                product_name=product.product_name,
                farmer_email=product.farmer_email,
                farmer_name=product.farmer_name,
                quantity=item['quantity'],
                unit=product.unit,
                price_per_unit=product.price,
                total_amount=total_amount,
                payment_method=payment_method,
                delivery_address=delivery_address,
                contact_number=contact_number,
                status='Pending'
            )
            
            product.quantity -= item['quantity']
            if product.quantity == 0:
                product.status = 'Sold Out'
            
            db.session.add(new_order)
            order_count += 1
        
        db.session.commit()
        
        if order_count > 0:
            flash(f"{order_count} order(s) placed successfully! The farmers will contact you soon.", "success")
        else:
            flash("No orders were placed. Please check product availability.", "error")
        
        return redirect(url_for("my_orders"))
    
    return render_template("checkout.html")

@app.route("/my_orders")
def my_orders():
    if "user" not in session or session["role"] != "buyer":
        flash("Only buyers can view orders.", "error")
        return redirect(url_for("dashboard"))
    
    orders = Order.query.filter_by(buyer_email=session["user"]).order_by(Order.created_at.desc()).all()
    
    return render_template("buyer_orders.html", orders=orders)

# API ROUTES
@app.route("/api/chat/<int:product_id>/messages")
def get_chat_messages(product_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    messages = ChatMessage.query.filter_by(product_id=product_id).order_by(ChatMessage.timestamp).all()
    
    messages_data = [{
        'sender_name': msg.sender_name,
        'sender_role': msg.sender_role,
        'message': msg.message,
        'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for msg in messages]
    
    return jsonify(messages_data)

# DEBUG ROUTE (Remove in production)
@app.route("/debug/products")
def debug_products():
    products = Product.query.all()
    result = f"<h2>Total products: {len(products)}</h2><br>"
    for p in products:
        result += f"ID: {p.id}, Name: {p.product_name}, Status: {p.status}, Quantity: {p.quantity}<br>"
    return result

# GENERAL ROUTES
@app.route("/logout")
def logout():
    name = session.get("name", "User")
    for key in list(session.keys()):
        session.pop(key)
    session.modified = True
    flash(f"Goodbye, {name}!", "success")
    response = redirect(url_for("login"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Password reset link sent!", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)