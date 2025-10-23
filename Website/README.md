# Green Breeze AC Services Website

A professional AC service booking website with comprehensive admin panel.

## Features

### Customer Features
- Responsive design for all devices
- Service browsing and booking
- Real-time pricing display
- Contact information and location

### Admin Features
- Dashboard with statistics
- Booking management with monthly filtering
- Service management (add/edit/delete)
- Offers management with expiry dates
- Website settings customization
- Export functionality for bookings

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the website:
- Main website: http://localhost:5000
- Admin panel: http://localhost:5000/admin/login

## Default Admin Credentials
- Username: admin
- Password: admin123

## Database
The application uses SQLite database (green_breeze.db) which is created automatically on first run.

## Technologies Used
- Backend: Flask (Python)
- Frontend: Bootstrap 5, HTML5, CSS3, JavaScript
- Database: SQLite
- Icons: Font Awesome

## File Structure
```
Website/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── book.html
│   ├── admin_base.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_bookings.html
│   ├── admin_services.html
│   ├── admin_offers.html
│   └── admin_settings.html
└── static/              # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```