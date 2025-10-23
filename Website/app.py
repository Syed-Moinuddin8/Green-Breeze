from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
import sqlite3
import hashlib
import os
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add datetime to template globals
def inject_datetime():
    return {'datetime': datetime}

app = Flask(__name__)
app.secret_key = 'green_breeze_secret_key_2024'

# Configure upload folder
UPLOAD_FOLDER = 'static/images/services'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email_notification(customer_name, phone, email, address, service_name, booking_date, booking_time):
    try:
        # Email configuration - Update these with your email settings
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        admin_email = "gbs.green9@gmail.com"
        admin_password = "wszbippcytwrcyvx"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = admin_email
        msg['To'] = admin_email
        msg['Subject'] = f"New Booking - {service_name}"
        
        # Format booking time
        time_slots = {
            '09:00': '09:00 AM - 10:00 AM',
            '10:00': '10:00 AM - 11:00 AM',
            '11:00': '11:00 AM - 12:00 PM',
            '12:00': '12:00 PM - 01:00 PM',
            '14:00': '02:00 PM - 03:00 PM',
            '15:00': '03:00 PM - 04:00 PM',
            '16:00': '04:00 PM - 05:00 PM',
            '17:00': '05:00 PM - 06:00 PM'
        }
        formatted_time = time_slots.get(booking_time, booking_time)
        
        # Email body
        body = f"""
New Booking Received!

Customer Details:
Name: {customer_name}
Phone: {phone}
Email: {email or 'Not provided'}
Address: {address}

Booking Details:
Service: {service_name}
Date: {booking_date}
Time: {formatted_time}

Please contact the customer to confirm the appointment.

Green Breeze Admin Panel
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(admin_email, admin_password)
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        print(f"Failed to send email: {e}")



# Register template globals
app.context_processor(inject_datetime)

# Database initialization
def init_db():
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    # Services table
    c.execute('''CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        duration TEXT,
        category TEXT DEFAULT 'AC',
        image TEXT,
        active INTEGER DEFAULT 1
    )''')
    
    # Add category column if it doesn't exist
    try:
        c.execute('ALTER TABLE services ADD COLUMN category TEXT DEFAULT "AC"')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Add image column if it doesn't exist
    try:
        c.execute('ALTER TABLE services ADD COLUMN image TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Bookings table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        address TEXT NOT NULL,
        service_id INTEGER,
        booking_date TEXT NOT NULL,
        booking_time TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        revenue REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id)
    )''')
    
    # Add revenue column if it doesn't exist
    try:
        c.execute('ALTER TABLE bookings ADD COLUMN revenue REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    
    # Offers table
    c.execute('''CREATE TABLE IF NOT EXISTS offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        discount_percent REAL,
        valid_until TEXT,
        active INTEGER DEFAULT 1
    )''')
    
    # Website settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT
    )''')
    
    # Revenue table
    c.execute('''CREATE TABLE IF NOT EXISTS revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER,
        amount REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings (id)
    )''')
    
    # Insert default data
    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        default_services = [
            ('AC Installation', 'Professional AC installation service', 2500.0, '2-3 hours', 'AC'),
            ('AC Repair', 'Expert AC repair and maintenance', 800.0, '1-2 hours', 'AC'),
            ('AC Cleaning', 'Deep cleaning and sanitization', 600.0, '1 hour', 'AC'),
            ('AC Gas Refilling', 'Gas refilling and pressure check', 1200.0, '30 minutes', 'AC'),
            ('AC Servicing', 'Complete AC servicing package', 1000.0, '1.5 hours', 'AC'),
            ('Fridge Repair', 'Complete refrigerator repair service', 900.0, '1-2 hours', 'Fridge'),
            ('Fridge Gas Refilling', 'Refrigerant gas refilling service', 1500.0, '1 hour', 'Fridge'),
            ('Fridge Cleaning', 'Deep cleaning and maintenance', 500.0, '45 minutes', 'Fridge'),
            ('Washing Machine Repair', 'Complete washing machine repair', 700.0, '1-2 hours', 'Washing Machine'),
            ('Washing Machine Installation', 'Professional installation service', 400.0, '30 minutes', 'Washing Machine'),
            ('Washing Machine Cleaning', 'Deep cleaning and maintenance', 350.0, '30 minutes', 'Washing Machine')
        ]
        c.executemany("INSERT INTO services (name, description, price, duration, category) VALUES (?, ?, ?, ?, ?)", default_services)
    
    # Insert default admin
    c.execute("SELECT COUNT(*) FROM admin")
    if c.fetchone()[0] == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', admin_password))
    
    # Insert default settings
    default_settings = [
        ('site_title', 'Green Breeze AC Services'),
        ('site_description', 'Professional AC Services in Your City'),
        ('contact_phone', '+91 9876543210'),
        ('contact_email', 'info@greenbreeze.com'),
        ('address', '123 Service Street, Your City - 560001'),
        ('show_prices', '1')
    ]
    
    for key, value in default_settings:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    
    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("SELECT * FROM services WHERE active = 1 ORDER BY category, name")
    all_services = c.fetchall()
    
    # Group services by category
    services_by_category = {}
    for service in all_services:
        category = service[5] if len(service) > 5 and service[5] else 'AC'  # category is at index 5
        if category not in services_by_category:
            services_by_category[category] = []
        services_by_category[category].append(service)
    
    c.execute("SELECT * FROM offers WHERE active = 1 AND date(valid_until) >= date('now')")
    offers = c.fetchall()
    
    c.execute("SELECT value FROM settings WHERE key = 'show_prices'")
    show_prices = c.fetchone()
    show_prices = show_prices[0] == '1' if show_prices else True
    
    c.execute("SELECT key, value FROM settings")
    settings_data = c.fetchall()
    settings = {key: value for key, value in settings_data}
    
    conn.close()
    return render_template('index.html', services_by_category=services_by_category, offers=offers, show_prices=show_prices, settings=settings)

@app.route('/book', methods=['GET', 'POST'])
def book_service():
    if request.method == 'POST':
        conn = sqlite3.connect('green_breeze.db')
        c = conn.cursor()
        
        customer_name = request.form['customer_name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        service_id = request.form['service_id']
        booking_date = request.form['booking_date']
        booking_time = request.form['booking_time']
        
        c.execute("""INSERT INTO bookings 
                    (customer_name, phone, email, address, service_id, booking_date, booking_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                 (customer_name, phone, email, address, service_id, booking_date, booking_time))
        
        # Get service name for notification
        c.execute("SELECT name FROM services WHERE id = ?", (service_id,))
        service_name = c.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        # Store admin notification
        admin_message = f"New booking: {customer_name} ({phone}) booked {service_name} for {booking_date} at {booking_time}"
        session['admin_notification'] = admin_message
        
        # Send email to admin
        send_email_notification(customer_name, phone, email, address, service_name, booking_date, booking_time)
        
        flash('Booking confirmed! We will contact you soon.', 'success')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("SELECT * FROM services WHERE active = 1 ORDER BY category, name")
    all_services = c.fetchall()
    
    # Group services by category
    services_by_category = {}
    for service in all_services:
        category = service[5] if len(service) > 5 and service[5] else 'AC'
        if category not in services_by_category:
            services_by_category[category] = []
        services_by_category[category].append(service)
    
    c.execute("SELECT value FROM settings WHERE key = 'show_prices'")
    show_prices = c.fetchone()
    show_prices = show_prices[0] == '1' if show_prices else True
    
    c.execute("SELECT key, value FROM settings")
    settings_data = c.fetchall()
    settings = {key: value for key, value in settings_data}
    
    conn.close()
    
    return render_template('book.html', services_by_category=services_by_category, show_prices=show_prices, settings=settings)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('green_breeze.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        admin = c.fetchone()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin_redirect():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Show admin notification if exists
    if 'admin_notification' in session:
        flash(session.pop('admin_notification'), 'info')
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM bookings WHERE date(created_at) = date('now')")
    today_bookings = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM bookings WHERE status = 'pending'")
    pending_bookings = c.fetchone()[0]
    
    # Get monthly revenue from completed bookings
    c.execute("""SELECT SUM(revenue) FROM bookings 
                 WHERE status = 'completed' 
                 AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')""")
    monthly_revenue = c.fetchone()[0] or 0
    
    # Get recent bookings
    c.execute("""SELECT b.*, s.name as service_name 
                FROM bookings b 
                JOIN services s ON b.service_id = s.id 
                ORDER BY b.created_at DESC LIMIT 5""")
    recent_bookings = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_bookings=total_bookings,
                         today_bookings=today_bookings,
                         pending_bookings=pending_bookings,
                         monthly_revenue=monthly_revenue,
                         recent_bookings=recent_bookings)

@app.route('/admin/bookings')
def admin_bookings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    status = request.args.get('status', 'all')
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    if status == 'all':
        c.execute("""SELECT b.*, s.name as service_name 
                    FROM bookings b 
                    JOIN services s ON b.service_id = s.id 
                    WHERE strftime('%Y-%m', b.created_at) = ?
                    ORDER BY b.created_at DESC""", (month,))
    else:
        c.execute("""SELECT b.*, s.name as service_name 
                    FROM bookings b 
                    JOIN services s ON b.service_id = s.id 
                    WHERE strftime('%Y-%m', b.created_at) = ? AND b.status = ?
                    ORDER BY b.created_at DESC""", (month, status))
    
    bookings = c.fetchall()
    conn.close()
    
    return render_template('admin_bookings.html', bookings=bookings, selected_month=month, selected_status=status)

@app.route('/admin/services')
def admin_services():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("SELECT * FROM services ORDER BY id")
    services = c.fetchall()
    conn.close()
    
    return render_template('admin_services.html', services=services)

@app.route('/admin/offers')
def admin_offers():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("SELECT * FROM offers ORDER BY id DESC")
    offers = c.fetchall()
    conn.close()
    
    return render_template('admin_offers.html', offers=offers)

@app.route('/admin/settings')
def admin_settings():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("SELECT * FROM settings")
    settings = c.fetchall()
    
    # Get actual stats
    c.execute("SELECT COUNT(*) FROM services WHERE active = 1")
    total_services = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM offers WHERE active = 1 AND date(valid_until) >= date('now')")
    active_offers = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM bookings WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')")
    monthly_bookings = c.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_settings.html', settings=settings, total_services=total_services, active_offers=active_offers, monthly_bookings=monthly_bookings)

# API Routes
@app.route('/api/delete_booking/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    # Check if booking has revenue recorded
    c.execute("SELECT status, revenue FROM bookings WHERE id = ?", (booking_id,))
    booking = c.fetchone()
    
    if booking and booking[0] == 'completed' and booking[1] > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Cannot delete completed booking with revenue'})
    
    # Delete the booking
    c.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    
    # Get all remaining bookings ordered by created_at
    c.execute("SELECT * FROM bookings ORDER BY created_at")
    bookings = c.fetchall()
    
    # Delete all bookings and recreate with new IDs
    c.execute("DELETE FROM bookings")
    
    # Reset auto-increment
    c.execute("DELETE FROM sqlite_sequence WHERE name='bookings'")
    
    # Reinsert bookings with new sequential IDs
    for booking in bookings:
        c.execute("""INSERT INTO bookings 
                    (customer_name, phone, email, address, service_id, booking_date, booking_time, status, created_at, revenue)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (booking[1], booking[2], booking[3], booking[4], booking[5], booking[6], booking[7], booking[8], booking[9], booking[10]))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_service', methods=['POST'])
def update_service():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Handle form data with file upload
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    duration = request.form.get('duration')
    category = request.form.get('category')
    service_id = request.form.get('id')
    
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            image_filename = timestamp + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    if service_id:
        if image_filename:
            c.execute("UPDATE services SET name=?, description=?, price=?, duration=?, category=?, image=? WHERE id=?",
                     (name, description, price, duration, category, image_filename, service_id))
        else:
            c.execute("UPDATE services SET name=?, description=?, price=?, duration=?, category=? WHERE id=?",
                     (name, description, price, duration, category, service_id))
    else:
        c.execute("INSERT INTO services (name, description, price, duration, category, image) VALUES (?, ?, ?, ?, ?, ?)",
                 (name, description, price, duration, category, image_filename))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_offer', methods=['POST'])
def update_offer():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    if data.get('id'):
        c.execute("UPDATE offers SET title=?, description=?, discount_percent=?, valid_until=? WHERE id=?",
                 (data['title'], data['description'], data['discount_percent'], data['valid_until'], data['id']))
    else:
        c.execute("INSERT INTO offers (title, description, discount_percent, valid_until) VALUES (?, ?, ?, ?)",
                 (data['title'], data['description'], data['discount_percent'], data['valid_until']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/delete_offer/<int:offer_id>', methods=['DELETE'])
def delete_offer(offer_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    # Handle checkbox for show_prices
    show_prices_value = '1' if data.get('show_prices') else '0'
    c.execute("UPDATE settings SET value = ? WHERE key = ?", (show_prices_value, 'show_prices'))
    
    for key, value in data.items():
        if key != 'show_prices':
            c.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/update_booking_statuses', methods=['POST'])
def update_booking_statuses():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    updates = data.get('updates', [])
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    for update in updates:
        if update['status'] == 'completed' and 'revenue' in update:
            c.execute("UPDATE bookings SET status = ?, revenue = ? WHERE id = ?", 
                     (update['status'], update['revenue'], update['id']))
        else:
            c.execute("UPDATE bookings SET status = ? WHERE id = ?", (update['status'], update['id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/toggle_service/<int:service_id>', methods=['POST'])
def toggle_service(service_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    c.execute("UPDATE services SET active = 1 - active WHERE id = ?", (service_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/backup_data')
def backup_data():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    c.execute("""SELECT b.id, b.customer_name, b.phone, b.email, b.address, 
                        s.name as service_name, b.booking_date, 
                        CASE 
                            WHEN b.booking_time = '09:00' THEN '09:00 AM - 10:00 AM'
                            WHEN b.booking_time = '10:00' THEN '10:00 AM - 11:00 AM'
                            WHEN b.booking_time = '11:00' THEN '11:00 AM - 12:00 PM'
                            WHEN b.booking_time = '12:00' THEN '12:00 PM - 01:00 PM'
                            WHEN b.booking_time = '14:00' THEN '02:00 PM - 03:00 PM'
                            WHEN b.booking_time = '15:00' THEN '03:00 PM - 04:00 PM'
                            WHEN b.booking_time = '16:00' THEN '04:00 PM - 05:00 PM'
                            WHEN b.booking_time = '17:00' THEN '05:00 PM - 06:00 PM'
                            ELSE b.booking_time
                        END as booking_time,
                        b.status, b.created_at
                 FROM bookings b 
                 JOIN services s ON b.service_id = s.id 
                 ORDER BY b.created_at DESC""")
    bookings = c.fetchall()
    conn.close()
    
    # Create CSV content
    csv_content = "ID,Customer Name,Phone,Email,Address,Service,Booking Date,Booking Time,Status,Created At\n"
    for booking in bookings:
        csv_content += f'"{booking[0]}","{booking[1]}","{booking[2]}","{booking[3] or ""}","{booking[4]}","{booking[5]}","{booking[6]}","{booking[7]}","{booking[8]}","{booking[9]}"\n'
    
    from flask import Response
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=bookings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.route('/admin/revenue')
def admin_revenue():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    filter_type = request.args.get('filter', 'all')
    filter_value = request.args.get('value', '')
    
    conn = sqlite3.connect('green_breeze.db')
    c = conn.cursor()
    
    # Build query based on filter
    base_query = """SELECT b.id, b.customer_name, b.revenue, s.name as service_name, b.created_at
                     FROM bookings b
                     JOIN services s ON b.service_id = s.id
                     WHERE b.status = 'completed' AND b.revenue > 0"""
    
    if filter_type == 'day' and filter_value:
        where_clause = " AND date(b.created_at) = ?"
        c.execute(base_query + where_clause + " ORDER BY b.created_at DESC", (filter_value,))
        revenue_records = c.fetchall()
        c.execute("SELECT SUM(b.revenue) FROM bookings b WHERE b.status = 'completed' AND b.revenue > 0" + where_clause, (filter_value,))
    elif filter_type == 'month' and filter_value:
        where_clause = " AND strftime('%Y-%m', b.created_at) = ?"
        c.execute(base_query + where_clause + " ORDER BY b.created_at DESC", (filter_value,))
        revenue_records = c.fetchall()
        c.execute("SELECT SUM(b.revenue) FROM bookings b WHERE b.status = 'completed' AND b.revenue > 0" + where_clause, (filter_value,))
    elif filter_type == 'year' and filter_value:
        where_clause = " AND strftime('%Y', b.created_at) = ?"
        c.execute(base_query + where_clause + " ORDER BY b.created_at DESC", (filter_value,))
        revenue_records = c.fetchall()
        c.execute("SELECT SUM(b.revenue) FROM bookings b WHERE b.status = 'completed' AND b.revenue > 0" + where_clause, (filter_value,))
    else:
        c.execute(base_query + " ORDER BY b.created_at DESC")
        revenue_records = c.fetchall()
        c.execute("SELECT SUM(revenue) FROM bookings WHERE status = 'completed' AND revenue > 0")
    
    total_revenue = c.fetchone()[0] or 0
    conn.close()
    
    return render_template('admin_revenue.html', revenue_records=revenue_records, total_revenue=total_revenue, filter_type=filter_type, filter_value=filter_value)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)