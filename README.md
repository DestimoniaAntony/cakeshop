# 🎂 Cakes by Desti - Complete Business Management System

A comprehensive Django-based web application for managing a homemade cake business with customer ordering, inventory tracking, and financial management.

## ✨ Features

### For Customers
- 🛍️ Browse products by category
- 🔍 Search and filter cakes
- 📝 **Place orders without login** (account auto-created)
- 💰 Dynamic price calculation
- 🎉 Event-based cake suggestions
- 📦 Track orders by phone number
- 💬 Contact via WhatsApp
- 📱 Fully mobile-responsive design

### For Admin
- 📊 Dashboard with analytics & charts
- 📋 Complete order management
- 📄 PDF estimate generation
- 🎂 Product catalog management
- 📦 Inventory tracking with low-stock alerts
- 💵 Purchase bill uploads & expense tracking
- 📈 Sales & expense reports with profit calculation
- 👥 Customer database with order history
- 📸 Gallery management
- ⭐ Review moderation system
- 🎁 Offer/banner management
- 📞 WhatsApp integration
- 🖼️ **Automatic image resizing & optimization**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL Server
- pip package manager

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Create Database**
```sql
CREATE DATABASE cake_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **Configure Database** (already done in `settings.py`)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cake_db',
        'USER': 'root',
        'PASSWORD': '',  # Add your password if any
        'HOST': 'localhost',
    }
}
```

4. **Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create Superuser**
```bash
python manage.py createsuperuser
```

6. **Run Development Server**
```bash
python manage.py runserver
```

7. **Access the System**
- Customer Website: http://localhost:8000/
- Admin Panel: http://localhost:8000/admin/

## 📁 Project Structure

```
cakeshop/
├── admin_app/              # Admin panel functionality
│   ├── models.py          # Database models
│   ├── views.py           # Admin views (1400+ lines)
│   ├── admin.py           # Django admin config
│   └── urls.py            # Admin URL patterns
│
├── cakeshop_app/          # Customer-facing functionality
│   ├── views.py           # Customer views
│   └── urls.py            # Customer URL patterns
│
├── templates/
│   ├── admin/             # Admin templates
│   │   ├── base.html      # Admin layout
│   │   ├── dashboard.html # Dashboard with charts
│   │   ├── orders/        # Order templates
│   │   ├── products/      # Product CRUD templates
│   │   ├── inventory/     # Inventory templates
│   │   └── customers/     # Customer templates
│   │
│   └── customer/          # Customer templates
│       ├── base.html      # Customer layout
│       ├── home.html      # Homepage
│       ├── products.html  # Product listing
│       ├── place_order.html  # Order form
│       ├── track_order.html  # Order tracking
│       └── contact.html   # Contact form
│
├── static/                # CSS, JS, Images (KaiAdmin template)
├── media/                 # User uploads
├── requirements.txt       # Python dependencies
└── manage.py             # Django management script
```

## 💾 Database Models

1. **Category & Subcategory** - Product organization
2. **Product & ProductImage** - Cake catalog
3. **Flavor & Size** - Product variants with pricing
4. **Ingredient** - Inventory management
5. **PurchaseBill** - Expense tracking
6. **Customer** - Customer database (auto-created on order)
7. **Order** - Order management with auto-generated IDs
8. **Event & EventSuggestion** - Event-based recommendations
9. **Enquiry** - Customer enquiries
10. **Gallery** - Showcase images
11. **Review** - Customer reviews with moderation
12. **OfferBanner** - Promotional banners

## 🎯 Key Workflows

### Customer Orders Flow
1. Customer browses products
2. Selects product → views details
3. Chooses size, flavor, event
4. Enters personal details (no login required)
5. Customer account auto-created in backend
6. Order placed with unique order number
7. Can track order anytime by phone number

### Admin Order Processing
1. View order in dashboard
2. Contact customer via WhatsApp
3. Confirm order & generate PDF estimate
4. Update order status
5. Track until delivery
6. Mark as completed
7. All data available in reports

## 📊 Reports & Analytics

### Dashboard Metrics
- Total orders (all time)
- Pending orders
- Monthly sales
- Monthly expenses
- Monthly profit (auto-calculated)
- Low stock alerts
- New customers
- Pending enquiries
- 7-day sales chart

### Available Reports
- **Sales Report**: Date range filtering, monthly breakdown, CSV export
- **Expense Report**: Purchase bills tracking, monthly analysis, CSV export
- **Profit Summary**: Auto-calculated (Sales - Expenses)

## 🎨 Admin Templates Created

### Fully Custom Templates
- ✅ Dashboard with charts
- ✅ Orders (list & detail)
- ✅ Products (list & form)
- ✅ Categories (list & form)
- ✅ Subcategories (list & form)
- ✅ Flavors (list & form)
- ✅ Sizes (list & form)
- ✅ Inventory (list & form)
- ✅ Customers (list & detail)

### Using Django Admin (Fully Functional)
- Finance (Purchase Bills)
- Events & Suggestions
- Gallery
- Reviews
- Enquiries
- Offers & Banners

## 🛠️ Tech Stack

- **Backend**: Django 4.2
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript
- **Admin Template**: KaiAdmin
- **PDF Generation**: ReportLab
- **Image Handling**: Pillow
- **Icons**: Font Awesome

## 📱 Configuration

### Update WhatsApp Number
Replace `91XXXXXXXXXX` in these files:
- `templates/customer/base.html`
- `templates/customer/contact.html`
- `templates/customer/order_confirmation.html`

### Customize Colors
Edit CSS in `templates/customer/base.html`:
- Primary: `#FF6B9D` (Pink)
- Secondary: `#C06C84` (Rose)
- Background: `#FFF9F5` (Cream)

### Add Email Notifications (Optional)
Add to `settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🔐 Security Notes

### For Production
1. Change `SECRET_KEY` in `settings.py`
2. Set `DEBUG = False`
3. Update `ALLOWED_HOSTS`
4. Run `python manage.py collectstatic`
5. Use Gunicorn + Nginx
6. Enable HTTPS
7. Regular database backups

## 📝 Initial Setup Checklist

After first run:
- [ ] Add categories (Birthday Cakes, Wedding Cakes, etc.)
- [ ] Add sizes with prices (½ kg - ₹500, 1 kg - ₹900, etc.)
- [ ] Add flavors (Chocolate, Vanilla, Red Velvet, etc.)
- [ ] Create events (Birthday, Wedding, Anniversary, etc.)
- [ ] Add products with images
- [ ] Upload gallery images
- [ ] Test order placement
- [ ] Update WhatsApp number
- [ ] Customize company info in templates

## 🆘 Troubleshooting

### mysqlclient won't install
Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient

### Static files not loading
```bash
python manage.py collectstatic
```

### Can't connect to MySQL
- Check MySQL is running
- Verify credentials in `settings.py`
- Ensure database `cake_db` exists

## 📸 Image Upload & Processing

### 🆕 Visual Crop Tool ✨ NEW!

**Manual image cropping with drag-and-drop interface!**

- 📐 **Visual crop interface** - See exactly what you're cropping
- 🖱️ **Drag to select** - Choose the perfect portion of your image
- 🔄 **Real-time preview** - See the result before saving
- ✂️ **Precise control** - Perfect for off-center subjects
- 📱 **Touch support** - Works on mobile/tablet too!

```
Upload → Drag crop box → Apply → Save = Perfect composition!
```

📖 **User Guide**: See `IMAGE_CROP_FEATURE.md` for complete tutorial

### Automatic Image Optimization ✨

All uploaded images are **automatically resized and optimized** for perfect display:

- **Products**: 500×281 pixels (landscape)
- **Gallery**: 500×281 pixels (landscape)
- **Categories**: 500×281 pixels (landscape)
- **Carousel**: 1920×1080 pixels (Full HD)
- **Offers**: 800×400 pixels (wide banner)

**Just upload any image - crop it (optional), and the system optimizes everything!**

📖 **Upload Guide**: See `IMAGE_UPLOAD_GUIDE.md` for tips and best practices  
📖 **Technical Details**: See `AUTOMATIC_IMAGE_PROCESSING.md` for full documentation

### Benefits:
- ✅ **Visual crop tool** - Perfect image composition
- ✅ Upload any image size (no manual resizing needed)
- ✅ 85-95% smaller file sizes
- ✅ Faster page loading
- ✅ Consistent professional appearance
- ✅ Better SEO performance

## 📚 Documentation

- `PROJECT_SUMMARY.md` - Detailed feature documentation
- `SETUP_INSTRUCTIONS.md` - Step-by-step setup guide
- `IMPLEMENTATION_COMPLETE.md` - Implementation details
- `ADMIN_TEMPLATES_STATUS.md` - Template completion status
- `FINAL_PROJECT_STATUS.md` - Complete project overview
- **`IMAGE_CROP_FEATURE.md`** - Visual crop tool guide (NEW!)
- **`IMAGE_CROP_IMPLEMENTATION_SUMMARY.md`** - Crop tool technical docs (NEW!)
- **`IMAGE_UPLOAD_GUIDE.md`** - Simple image upload guide
- **`AUTOMATIC_IMAGE_PROCESSING.md`** - Auto-processing documentation

## 🎓 How Customers Order Without Login

1. Customer fills order form with personal details
2. System checks if phone number exists
3. If exists: Update customer info, create order
4. If new: Create customer account, then create order
5. Customer gets order number immediately
6. Can track orders anytime by entering phone number
7. Admin sees customer in database with all orders

**Benefits:**
- ✅ No registration friction
- ✅ Faster checkout
- ✅ Still maintains customer database
- ✅ Order history tracked
- ✅ Can send notifications later

## 🌟 Special Features

1. **Auto Order Numbers**: Format `CK20250122001` (CK + Date + Sequence)
2. **Low Stock Alerts**: Automatic warnings when ingredients run low
3. **Dynamic Pricing**: Price updates as customer selects size/quantity
4. **Event Suggestions**: Show relevant cakes based on event type
5. **PDF Estimates**: Professional bills with company branding
6. **WhatsApp Links**: One-click customer contact
7. **CSV Exports**: Download reports for accounting
8. **Mobile Responsive**: Works perfectly on all devices
9. **🆕 Visual Crop Tool**: Drag-and-drop interface to crop images precisely!
10. **🆕 Automatic Image Processing**: Upload any image size - automatically resized and optimized!

## 📞 Support

For issues or questions:
- Check documentation files in project root
- Review Django documentation
- Check model definitions in `admin_app/models.py`
- Review views in `admin_app/views.py` and `cakeshop_app/views.py`

## 📄 License

This project is created for Cakes by Desti.

## 🎉 You're Ready!

Everything is set up and working. Just:
1. Run the server
2. Add your products
3. Start taking orders!

**Happy Baking! 🎂**

---

Made with ❤️ for your cake business success

