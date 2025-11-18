from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth, TruncDate
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.contrib.auth.decorators import login_required



from .models import (
    Category, Subcategory, Size, Product, ProductImage, ProductPrice,
    Ingredient, PurchaseBill, Event, EventSuggestion, Customer, Order,
    Enquiry, Gallery, Review, CarouselSlide, OfferBanner,
    CakeShape, CakeTier, Flavor, Decoration, CustomCakeOrder,
    CustomCakeOrderDecoration, CustomCakeReferenceImage,
    GiftBox, GiftBoxItem, GiftBoxOrder
)
from .models import PageTitleBanner
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import ModelForm


class PageTitleBannerForm(ModelForm):
    class Meta:
        model = PageTitleBanner
        fields = ['name', 'page_key', 'title_text', 'subtitle_text', 'image', 'display_order', 'is_active', 'start_date', 'end_date']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to form widgets for consistent admin styling
        for field_name, field in self.fields.items():
            widget = field.widget
            css = widget.attrs.get('class', '')
            # Use form-control for most inputs, form-check-input for boolean
            if field_name == 'is_active':
                widget.attrs['class'] = (css + ' form-check-input').strip()
            else:
                widget.attrs['class'] = (css + ' form-control').strip()


@login_required(login_url='admin_login')
def admin_page_banners(request):
    """List all page title banners"""
    banners = PageTitleBanner.objects.order_by('display_order', '-created_at')
    context = {'banners': banners}
    return render(request, 'admin/page_banners/banner_list.html', context)


@login_required(login_url='admin_login')
def admin_page_banner_add(request):
    if request.method == 'POST':
        form = PageTitleBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page title banner added successfully!')
            return redirect('admin_page_banners')
    else:
        form = PageTitleBannerForm()
    # pass banner=None so template checks like `{% if banner and banner.image %}` are safe
    return render(request, 'admin/page_banners/banner_form.html', {'form': form, 'action': 'Add', 'banner': None})


@login_required(login_url='admin_login')
def admin_page_banner_edit(request, banner_id):
    banner = get_object_or_404(PageTitleBanner, id=banner_id)
    if request.method == 'POST':
        form = PageTitleBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Page title banner updated successfully!')
            return redirect('admin_page_banners')
    else:
        form = PageTitleBannerForm(instance=banner)
    return render(request, 'admin/page_banners/banner_form.html', {'form': form, 'action': 'Edit', 'banner': banner})


@login_required(login_url='admin_login')
def admin_page_banner_delete(request, banner_id):
    banner = get_object_or_404(PageTitleBanner, id=banner_id)
    banner.delete()
    messages.success(request, 'Page title banner deleted successfully!')
    return redirect('admin_page_banners')



# ===========================
# DASHBOARD
# ===========================


@login_required(login_url='admin_login')
@login_required(login_url='admin_login')
def admin_dashboard(request):
    """Main admin dashboard with statistics and analytics"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Sales statistics
    total_sales = Order.objects.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    monthly_sales = Order.objects.filter(
        status__in=['confirmed', 'completed'],
        created_at__gte=this_month_start
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Expense statistics
    total_expenses = PurchaseBill.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    monthly_expenses = PurchaseBill.objects.filter(
        date__gte=this_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Profit calculation
    total_profit = total_sales - total_expenses
    monthly_profit = monthly_sales - monthly_expenses
    
    # Low stock alerts
    low_stock_items = Ingredient.objects.filter(
        current_quantity__lte=F('reorder_level')
    ).count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('customer', 'product').order_by('-created_at')[:10]
    
    # Customer statistics
    total_customers = Customer.objects.count()
    new_customers_this_month = Customer.objects.filter(
        created_at__gte=this_month_start
    ).count()
    
    # Pending enquiries
    pending_enquiries = Enquiry.objects.filter(is_responded=False).count()
    
    # Chart data - Last 7 days sales
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    daily_sales_data = []
    for day in last_7_days:
        day_sales = Order.objects.filter(
            status__in=['confirmed', 'completed'],
            created_at__date=day
        ).aggregate(total=Sum('total_price'))['total'] or 0
        daily_sales_data.append({
            'date': day.strftime('%d %b'),
            'amount': float(day_sales)
        })
    
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
        'total_profit': total_profit,
        'monthly_profit': monthly_profit,
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'total_customers': total_customers,
        'new_customers_this_month': new_customers_this_month,
        'pending_enquiries': pending_enquiries,
        'daily_sales_data': daily_sales_data,
    }
    
    return render(request, 'admin/dashboard.html', context)

# Legacy index view for backward compatibility
@login_required(login_url='admin_login')
def index(request):
    return redirect('admin_dashboard')


# ===========================
# ORDERS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
@login_required(login_url='admin_login')
def admin_orders(request):
    """List all orders"""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    orders = Order.objects.select_related('customer', 'product', 'size').all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__phone_number__icontains=search)
        )
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'admin/orders/order_list.html', context)


@login_required(login_url='admin_login')
def admin_orders_pending(request):
    """Pending orders only"""
    orders = Order.objects.filter(status='pending').select_related('customer', 'product').order_by('-created_at')
    context = {'orders': orders, 'page_title': 'Pending Orders'}
    return render(request, 'admin/orders/order_list.html', context)


@login_required(login_url='admin_login')
def admin_orders_confirmed(request):
    """Confirmed orders only"""
    orders = Order.objects.filter(status='confirmed').select_related('customer', 'product').order_by('-created_at')
    context = {'orders': orders, 'page_title': 'Confirmed Orders'}
    return render(request, 'admin/orders/order_list.html', context)


@login_required(login_url='admin_login')
def admin_order_detail(request, order_id):
    """View and update order details"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {order.get_status_display()}')
            return redirect('admin_order_detail', order_id=order.id)
    
    context = {'order': order}
    return render(request, 'admin/orders/order_detail.html', context)


@login_required(login_url='admin_login')
def admin_order_generate_pdf(request, order_id):
    """Generate estimate PDF for an order"""
    order = get_object_or_404(Order, id=order_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#FF1493'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("🎂 Cakes by Desti", title_style))
    elements.append(Paragraph("ORDER ESTIMATE", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    # Order details
    order_data = [
        ['Order Number:', order.order_number],
        ['Customer Name:', order.customer.name],
        ['Phone:', order.customer.phone_number],
        ['Order Date:', order.created_at.strftime('%d %b %Y')],
        ['Delivery Date:', order.delivery_date.strftime('%d %b %Y')],
        ['Status:', order.get_status_display()],
    ]
    
    order_table = Table(order_data, colWidths=[2*inch, 4*inch])
    order_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 20))
    
    # Product details
    product_data = [
        ['Product', 'Size', 'Flavor', 'Qty', 'Price', 'Total'],
        [
            order.product.name,
            order.size.name,
            order.flavor.name if order.flavor else 'N/A',
            str(order.quantity),
            f'₹{order.unit_price}',
            f'₹{order.total_price}'
        ]
    ]
    
    product_table = Table(product_data, colWidths=[2*inch, 1*inch, 1.5*inch, 0.5*inch, 1*inch, 1*inch])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 20))
    
    # Special instructions
    if order.custom_message or order.special_instructions:
        elements.append(Paragraph("<b>Special Instructions:</b>", styles['Normal']))
        if order.custom_message:
            elements.append(Paragraph(f"Message on cake: {order.custom_message}", styles['Normal']))
        if order.special_instructions:
            elements.append(Paragraph(f"Notes: {order.special_instructions}", styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    elements.append(Paragraph("Thank you for your order! 🎉", footer_style))
    elements.append(Paragraph("Contact: +91 XXXXXXXXXX | Email: info@cakesbydesti.com", footer_style))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="estimate_{order.order_number}.pdf"'
    
    return response


# ===========================
# CUSTOMERS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_customers(request):
    """List all customers"""
    search = request.GET.get('search', '')
    customers = Customer.objects.annotate(
        total_orders=Count('orders')
    ).all()
    
    if search:
        customers = customers.filter(
            Q(name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(email__icontains=search)
        )
    
    customers = customers.order_by('-created_at')
    
    context = {
        'customers': customers,
        'search': search,
    }
    return render(request, 'admin/customers/customer_list.html', context)


@login_required(login_url='admin_login')
def admin_customer_detail(request, customer_id):
    """View customer details and order history"""
    customer = get_object_or_404(Customer, id=customer_id)
    orders = customer.orders.all().order_by('-created_at')
    
    context = {
        'customer': customer,
        'orders': orders,
    }
    return render(request, 'admin/customers/customer_detail.html', context)


# ===========================
# PRODUCTS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_products(request):
    """List all products"""
    search = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    products = Product.objects.select_related('category', 'subcategory').all()
    
    if search:
        products = products.filter(Q(name__icontains=search))
    
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    products = products.order_by('-created_at')
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'categories': categories,
        'search': search,
        'category_filter': category_filter,
    }
    return render(request, 'admin/products/product_list.html', context)


@login_required(login_url='admin_login')
def admin_product_add(request):
    """Add new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        main_image = request.FILES.get('main_image')
        is_active = request.POST.get('is_active') == 'on'
        
        product = Product.objects.create(
            name=name,
            description=description,
            category_id=category_id,
            subcategory_id=subcategory_id if subcategory_id else None,
            main_image=main_image,
            is_active=is_active
        )
        
        # Add sizes
        size_ids = request.POST.getlist('sizes')
        product.sizes.set(size_ids)
        
        # Handle pricing for each size
        for size_id in size_ids:
            price_key = f'price_size_{size_id}'
            price = request.POST.get(price_key)
            if price:
                ProductPrice.objects.create(
                    product=product,
                    size_id=size_id,
                    price=Decimal(price)
                )
        
        messages.success(request, f'Product "{name}" added successfully with pricing!')
        return redirect('admin_products')
    
    categories = Category.objects.filter(is_active=True)
    # flavors = Flavor.objects.filter(is_active=True)
    sizes = Size.objects.filter(is_active=True).order_by('display_order', 'weight_in_kg')
    
    context = {
        'categories': categories,
        # 'flavors': flavors,
        'sizes': sizes,
    }
    return render(request, 'admin/products/product_form.html', context)


@login_required(login_url='admin_login')
def admin_product_edit(request, product_id):
    """Edit product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.category_id = request.POST.get('category')
        product.subcategory_id = request.POST.get('subcategory') or None
        product.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('main_image'):
            product.main_image = request.FILES.get('main_image')
        
        product.save()
        
        # Update sizes
        size_ids = request.POST.getlist('sizes')
        product.sizes.set(size_ids)
        
        # Update pricing for each size
        for size_id in size_ids:
            price_key = f'price_size_{size_id}'
            price = request.POST.get(price_key)
            if price:
                ProductPrice.objects.update_or_create(
                    product=product,
                    size_id=size_id,
                    defaults={'price': Decimal(price)}
                )
        
        # Remove prices for sizes that are no longer selected
        ProductPrice.objects.filter(product=product).exclude(size_id__in=size_ids).delete()
        
        messages.success(request, f'Product "{product.name}" updated successfully with pricing!')
        return redirect('admin_products')
    
    categories = Category.objects.filter(is_active=True)
    subcategories = Subcategory.objects.filter(category=product.category, is_active=True)
    sizes = Size.objects.filter(is_active=True).order_by('display_order', 'weight_in_kg')
    
    # Get existing prices for this product
    product_prices = {pp.size_id: pp.price for pp in ProductPrice.objects.filter(product=product)}
    
    context = {
        'product': product,
        'categories': categories,
        'subcategories': subcategories,
        'sizes': sizes,
        'product_prices': product_prices,
    }
    return render(request, 'admin/products/product_form.html', context)


@login_required(login_url='admin_login')
def admin_product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f'Product "{product_name}" deleted successfully!')
    return redirect('admin_products')


# ===========================
# CATEGORIES MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_categories(request):
    """List all categories"""
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    context = {'categories': categories}
    return render(request, 'admin/products/category_list.html', context)


@login_required(login_url='admin_login')
def admin_category_add(request):
    """Add category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        is_cake = request.POST.get('is_cake') == 'on'
        
        Category.objects.create(
            name=name,
            description=description,
            image=image,
            is_active=is_active,
            is_cake=is_cake
        )
        
        messages.success(request, f'Category "{name}" added successfully!')
        return redirect('admin_categories')
    
    return render(request, 'admin/products/category_form.html')


@login_required(login_url='admin_login')
def admin_category_edit(request, category_id):
    """Edit category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description', '')
        category.is_active = request.POST.get('is_active') == 'on'
        category.is_cake = request.POST.get('is_cake') == 'on'
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        
        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully!')
        return redirect('admin_categories')
    
    context = {'category': category}
    return render(request, 'admin/products/category_form.html', context)


@login_required(login_url='admin_login')
def admin_category_delete(request, category_id):
    """Delete category"""
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    category.delete()
    messages.success(request, f'Category "{category_name}" deleted successfully!')
    return redirect('admin_categories')


# ===========================
# SUBCATEGORIES MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_subcategories(request):
    """List all subcategories"""
    subcategories = Subcategory.objects.select_related('category').annotate(
        product_count=Count('products')
    ).order_by('category__name', 'name')
    
    context = {'subcategories': subcategories}
    return render(request, 'admin/products/subcategory_list.html', context)


@login_required(login_url='admin_login')
def admin_subcategory_add(request):
    """Add subcategory"""
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        Subcategory.objects.create(
            name=name,
            category_id=category_id,
            description=description,
            image=image,
            is_active=is_active
        )
        
        messages.success(request, f'Subcategory "{name}" added successfully!')
        return redirect('admin_subcategories')
    
    categories = Category.objects.filter(is_active=True)
    context = {'categories': categories}
    return render(request, 'admin/products/subcategory_form.html', context)
@login_required(login_url='admin_login')
def admin_subcategory_edit(request, subcategory_id):
    """Edit subcategory"""
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    
    if request.method == 'POST':
        subcategory.name = request.POST.get('name')
        subcategory.category_id = request.POST.get('category')
        subcategory.description = request.POST.get('description', '')
        subcategory.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            subcategory.image = request.FILES.get('image')
        
        subcategory.save()
        messages.success(request, f'Subcategory "{subcategory.name}" updated successfully!')
        return redirect('admin_subcategories')
    
    categories = Category.objects.filter(is_active=True)
    context = {
        'subcategory': subcategory,
        'categories': categories
    }
    return render(request, 'admin/products/subcategory_form.html', context)


@login_required(login_url='admin_login')
def admin_subcategory_delete(request, subcategory_id):
    """Delete subcategory"""
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    subcategory_name = subcategory.name
    subcategory.delete()
    messages.success(request, f'Subcategory "{subcategory_name}" deleted successfully!')
    return redirect('admin_subcategories')


# ===========================
# FLAVORS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_flavors(request):
    """List all flavors"""
    # Annotate with count of custom cake orders using this flavor
    flavors = Flavor.objects.annotate(
        order_count=Count('customcakeorder')
    ).order_by('display_order', 'name')
    context = {'flavors': flavors}
    return render(request, 'admin/products/flavor_list.html', context)


@login_required(login_url='admin_login')
def admin_flavor_add(request):
    """Add flavor"""
    if request.method == 'POST':
        name = request.POST.get('name')
        price_per_kg = request.POST.get('price_per_kg', 0)
        display_order = request.POST.get('display_order', 0)
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Check if flavor already exists
        if Flavor.objects.filter(name=name).exists():
            messages.error(request, f'Flavor "{name}" already exists! Please use a different name or edit the existing one.')
            return render(request, 'admin/products/flavor_form.html', {
                'name': name,
                'price_per_kg': price_per_kg,
                'display_order': display_order,
                'description': description,
                'is_active': is_active,
            })
        
        try:
            Flavor.objects.create(
                name=name,
                price_per_kg=price_per_kg,
                display_order=display_order,
                description=description,
                is_active=is_active
            )
            messages.success(request, f'Flavor "{name}" added successfully!')
            return redirect('admin_flavors')
        except Exception as e:
            messages.error(request, f'Error adding flavor: {str(e)}')
    
    return render(request, 'admin/products/flavor_form.html')


@login_required(login_url='admin_login')
def admin_flavor_edit(request, flavor_id):
    """Edit flavor"""
    flavor = get_object_or_404(Flavor, id=flavor_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        
        # Check if name changed and if new name already exists
        if name != flavor.name and Flavor.objects.filter(name=name).exists():
            messages.error(request, f'Flavor "{name}" already exists! Please use a different name.')
            context = {'flavor': flavor}
            return render(request, 'admin/products/flavor_form.html', context)
        
        try:
            flavor.name = name
            flavor.price_per_kg = request.POST.get('price_per_kg', 0)
            flavor.display_order = request.POST.get('display_order', 0)
            flavor.description = request.POST.get('description', '')
            flavor.is_active = request.POST.get('is_active') == 'on'
            flavor.save()
            
            messages.success(request, f'Flavor "{flavor.name}" updated successfully!')
            return redirect('admin_flavors')
        except Exception as e:
            messages.error(request, f'Error updating flavor: {str(e)}')
    
    context = {'flavor': flavor}
    return render(request, 'admin/products/flavor_form.html', context)


@login_required(login_url='admin_login')
def admin_flavor_delete(request, flavor_id):
    """Delete flavor"""
    flavor = get_object_or_404(Flavor, id=flavor_id)
    flavor_name = flavor.name
    flavor.delete()
    messages.success(request, f'Flavor "{flavor_name}" deleted successfully!')
    return redirect('admin_flavors')


# ===========================
# SIZES MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_sizes(request):
    """List all sizes"""
    sizes = Size.objects.annotate(product_count=Count('products')).order_by('display_order', 'weight_in_kg')
    context = {'sizes': sizes}
    return render(request, 'admin/products/size_list.html', context)


@login_required(login_url='admin_login')
def admin_size_add(request):
    """Add size (with categories)"""
    from .models import Category, Size
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        weight_in_kg = request.POST.get('weight_in_kg')
        display_order = request.POST.get('display_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        category_ids = request.POST.getlist('categories')

        size = Size.objects.create(
            name=name,
            weight_in_kg=weight_in_kg,
            display_order=display_order,
            is_active=is_active
        )
        # Assign selected categories
        if category_ids:
            size.categories.set(category_ids)
        messages.success(request, f'Size "{name}" added successfully!')
        return redirect('admin_sizes')
    return render(request, 'admin/products/size_form.html', {'categories': categories})


@login_required(login_url='admin_login')
def admin_size_edit(request, size_id):
    """Edit size (with categories)"""
    from .models import Category, Size
    size = get_object_or_404(Size, id=size_id)
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        size.name = request.POST.get('name')
        size.weight_in_kg = request.POST.get('weight_in_kg')
        size.display_order = request.POST.get('display_order', 0)
        size.is_active = request.POST.get('is_active') == 'on'
        category_ids = request.POST.getlist('categories')
        size.save()
        # Update ManyToMany categories
        if category_ids:
            size.categories.set(category_ids)
        else:
            size.categories.clear()
        messages.success(request, f'Size "{size.name}" updated successfully!')
        return redirect('admin_sizes')
    context = {'size': size, 'categories': categories, 'selected_categories': size.categories.values_list('id', flat=True)}
    return render(request, 'admin/products/size_form.html', context)


@login_required(login_url='admin_login')
def admin_size_delete(request, size_id):
    """Delete size"""
    size = get_object_or_404(Size, id=size_id)
    size_name = size.name
    size.delete()
    messages.success(request, f'Size "{size_name}" deleted successfully!')
    return redirect('admin_sizes')


# ===========================
# INVENTORY / INGREDIENTS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_ingredients(request):
    """List all ingredients with low stock alerts"""
    search = request.GET.get('search', '')
    show_low_stock = request.GET.get('low_stock', False)
    
    ingredients = Ingredient.objects.all()
    
    if search:
        ingredients = ingredients.filter(name__icontains=search)
    
    if show_low_stock:
        ingredients = ingredients.filter(current_quantity__lte=F('reorder_level'))
    
    ingredients = ingredients.order_by('name')
    
    low_stock_count = Ingredient.objects.filter(
        current_quantity__lte=F('reorder_level')
    ).count()
    
    context = {
        'ingredients': ingredients,
        'search': search,
        'show_low_stock': show_low_stock,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'admin/inventory/ingredient_list.html', context)


@login_required(login_url='admin_login')
def admin_ingredient_add(request):
    """Add ingredient"""
    if request.method == 'POST':
        name = request.POST.get('name')
        current_quantity = request.POST.get('current_quantity')
        unit = request.POST.get('unit')
        reorder_level = request.POST.get('reorder_level')
        notes = request.POST.get('notes', '')
        
        Ingredient.objects.create(
            name=name,
            current_quantity=current_quantity,
            unit=unit,
            reorder_level=reorder_level,
            notes=notes
        )
        
        messages.success(request, f'Ingredient "{name}" added successfully!')
        return redirect('admin_ingredients')
    
    context = {'unit_choices': Ingredient.UNIT_CHOICES}
    return render(request, 'admin/inventory/ingredient_form.html', context)


@login_required(login_url='admin_login')
def admin_ingredient_edit(request, ingredient_id):
    """Edit ingredient"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        ingredient.name = request.POST.get('name')
        ingredient.current_quantity = request.POST.get('current_quantity')
        ingredient.unit = request.POST.get('unit')
        ingredient.reorder_level = request.POST.get('reorder_level')
        ingredient.notes = request.POST.get('notes', '')
        ingredient.save()
        
        messages.success(request, f'Ingredient "{ingredient.name}" updated successfully!')
        return redirect('admin_ingredients')
    
    context = {
        'ingredient': ingredient,
        'unit_choices': Ingredient.UNIT_CHOICES
    }
    return render(request, 'admin/inventory/ingredient_form.html', context)


@login_required(login_url='admin_login')
def admin_ingredient_delete(request, ingredient_id):
    """Delete ingredient"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    ingredient_name = ingredient.name
    ingredient.delete()
    messages.success(request, f'Ingredient "{ingredient_name}" deleted successfully!')
    return redirect('admin_ingredients')


@login_required(login_url='admin_login')
def admin_ingredient_update_quantity(request, ingredient_id):
    """Quick update ingredient quantity"""
    if request.method == 'POST':
        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        action = request.POST.get('action')  # 'add' or 'subtract'
        quantity = Decimal(request.POST.get('quantity', 0))
        
        if action == 'add':
            ingredient.current_quantity += quantity
        elif action == 'subtract':
            ingredient.current_quantity -= quantity
        
        ingredient.save()
        messages.success(request, f'Quantity updated for "{ingredient.name}"')
        
    return redirect('admin_ingredients')


# ===========================
# PURCHASE BILLS / EXPENSES
# ===========================

@login_required(login_url='admin_login')
def admin_purchase_bills(request):
    """List all purchase bills"""
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    bills = PurchaseBill.objects.all()
    
    if search:
        bills = bills.filter(Q(supplier_name__icontains=search) | Q(notes__icontains=search))
    
    if date_from:
        bills = bills.filter(date__gte=date_from)
    
    if date_to:
        bills = bills.filter(date__lte=date_to)
    
    bills = bills.order_by('-date')
    
    total_amount = bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'bills': bills,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'total_amount': total_amount,
    }
    return render(request, 'admin/finance/purchase_bill_list.html', context)


@login_required(login_url='admin_login')
def admin_purchase_bill_add(request):
    """Add purchase bill"""
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        date = request.POST.get('date')
        total_amount = request.POST.get('total_amount')
        notes = request.POST.get('notes', '')
        bill_upload = request.FILES.get('bill_upload')
        
        PurchaseBill.objects.create(
            supplier_name=supplier_name,
            date=date,
            total_amount=total_amount,
            notes=notes,
            bill_upload=bill_upload
        )
        
        messages.success(request, 'Purchase bill added successfully!')
        return redirect('admin_purchase_bills')
    
    context = {'today': timezone.now().date()}
    return render(request, 'admin/finance/purchase_bill_form.html', context)


@login_required(login_url='admin_login')
def admin_purchase_bill_edit(request, bill_id):
    """Edit purchase bill"""
    bill = get_object_or_404(PurchaseBill, id=bill_id)
    
    if request.method == 'POST':
        bill.supplier_name = request.POST.get('supplier_name')
        bill.date = request.POST.get('date')
        bill.total_amount = request.POST.get('total_amount')
        bill.notes = request.POST.get('notes', '')
        
        if request.FILES.get('bill_upload'):
            bill.bill_upload = request.FILES.get('bill_upload')
        
        bill.save()
        messages.success(request, 'Purchase bill updated successfully!')
        return redirect('admin_purchase_bills')
    
    context = {'bill': bill}
    return render(request, 'admin/finance/purchase_bill_form.html', context)


@login_required(login_url='admin_login')
def admin_purchase_bill_delete(request, bill_id):
    """Delete purchase bill"""
    bill = get_object_or_404(PurchaseBill, id=bill_id)
    bill.delete()
    messages.success(request, 'Purchase bill deleted successfully!')
    return redirect('admin_purchase_bills')


# ===========================
# EVENTS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_events(request):
    """List all events"""
    events = Event.objects.annotate(
        suggestion_count=Count('suggestions')
    ).order_by('event_name')
    
    context = {'events': events}
    return render(request, 'admin/events/event_list.html', context)


@login_required(login_url='admin_login')
def admin_event_add(request):
    """Add event"""
    if request.method == 'POST':
        event_name = request.POST.get('event_name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', '')
        is_active = request.POST.get('is_active') == 'on'
        
        event = Event.objects.create(
            event_name=event_name,
            description=description,
            icon=icon,
            is_active=is_active
        )
        
        # Add suggestions
        suggestions = request.POST.getlist('suggestions[]')
        for suggestion_text in suggestions:
            if suggestion_text.strip():
                EventSuggestion.objects.create(
                    event=event,
                    suggested_item=suggestion_text.strip()
                )
        
        messages.success(request, f'Event "{event_name}" added successfully!')
        return redirect('admin_events')
    
    return render(request, 'admin/events/event_form.html')


@login_required(login_url='admin_login')
def admin_event_edit(request, event_id):
    """Edit event"""
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event.event_name = request.POST.get('event_name')
        event.description = request.POST.get('description', '')
        event.icon = request.POST.get('icon', '')
        event.is_active = request.POST.get('is_active') == 'on'
        event.save()
        
        messages.success(request, f'Event "{event.event_name}" updated successfully!')
        return redirect('admin_events')
    
    context = {'event': event}
    return render(request, 'admin/events/event_form.html', context)


@login_required(login_url='admin_login')
def admin_event_delete(request, event_id):
    """Delete event"""
    event = get_object_or_404(Event, id=event_id)
    event_name = event.event_name
    event.delete()
    messages.success(request, f'Event "{event_name}" deleted successfully!')
    return redirect('admin_events')


# ===========================
# ENQUIRIES MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_enquiries(request):
    """List all enquiries"""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    enquiries = Enquiry.objects.all()
    
    if status_filter == 'pending':
        enquiries = enquiries.filter(is_responded=False)
    elif status_filter == 'responded':
        enquiries = enquiries.filter(is_responded=True)
    
    if search:
        enquiries = enquiries.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(message__icontains=search)
        )
    
    enquiries = enquiries.order_by('-created_at')
    
    pending_count = Enquiry.objects.filter(is_responded=False).count()
    
    context = {
        'enquiries': enquiries,
        'status_filter': status_filter,
        'search': search,
        'pending_count': pending_count,
    }
    return render(request, 'admin/enquiries/enquiry_list.html', context)


@login_required(login_url='admin_login')
def admin_enquiry_detail(request, enquiry_id):
    """View and respond to enquiry"""
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    
    if request.method == 'POST':
        response = request.POST.get('response')
        enquiry.response = response
        enquiry.is_responded = True
        enquiry.save()
        
        messages.success(request, 'Enquiry marked as responded!')
        return redirect('admin_enquiries')
    
    # Generate WhatsApp link
    whatsapp_message = f"Hi {enquiry.name}, thank you for your enquiry. We'd love to help you!"
    whatsapp_link = f"https://wa.me/{enquiry.phone.replace('+', '')}?text={whatsapp_message.replace(' ', '%20')}"
    
    context = {
        'enquiry': enquiry,
        'whatsapp_link': whatsapp_link,
    }
    return render(request, 'admin/enquiries/enquiry_detail.html', context)


@login_required(login_url='admin_login')
def admin_enquiry_delete(request, enquiry_id):
    """Delete enquiry"""
    enquiry = get_object_or_404(Enquiry, id=enquiry_id)
    enquiry.delete()
    messages.success(request, 'Enquiry deleted successfully!')
    return redirect('admin_enquiries')


# ===========================
# GALLERY MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_gallery(request):
    """List all gallery images"""
    event_filter = request.GET.get('event', '')
    featured_only = request.GET.get('featured', False)
    
    images = Gallery.objects.select_related('event_type').all()
    
    if event_filter:
        images = images.filter(event_type_id=event_filter)
    
    if featured_only:
        images = images.filter(is_featured=True)
    
    images = images.order_by('-uploaded_at')
    
    events = Event.objects.filter(is_active=True)
    
    context = {
        'images': images,
        'events': events,
        'event_filter': event_filter,
        'featured_only': featured_only,
    }
    return render(request, 'admin/gallery/gallery_list.html', context)


@login_required(login_url='admin_login')
def admin_gallery_add(request):
    """Add gallery image"""
    if request.method == 'POST':
        image = request.FILES.get('image')
        caption = request.POST.get('caption', '')
        event_type_id = request.POST.get('event_type')
        is_featured = request.POST.get('is_featured') == 'on'
        
        Gallery.objects.create(
            image=image,
            caption=caption,
            event_type_id=event_type_id if event_type_id else None,
            is_featured=is_featured
        )
        
        messages.success(request, 'Image added to gallery!')
        return redirect('admin_gallery')
    
    events = Event.objects.filter(is_active=True)
    context = {'events': events}
    return render(request, 'admin/gallery/gallery_form.html', context)


@login_required(login_url='admin_login')
def admin_gallery_edit(request, image_id):
    """Edit gallery image"""
    gallery_image = get_object_or_404(Gallery, id=image_id)
    
    if request.method == 'POST':
        gallery_image.caption = request.POST.get('caption', '')
        gallery_image.event_type_id = request.POST.get('event_type') or None
        gallery_image.is_featured = request.POST.get('is_featured') == 'on'
        
        if request.FILES.get('image'):
            gallery_image.image = request.FILES.get('image')
        
        gallery_image.save()
        messages.success(request, 'Gallery image updated!')
        return redirect('admin_gallery')
    
    events = Event.objects.filter(is_active=True)
    context = {
        'gallery_image': gallery_image,
        'events': events
    }
    return render(request, 'admin/gallery/gallery_form.html', context)


@login_required(login_url='admin_login')
def admin_gallery_delete(request, image_id):
    """Delete gallery image"""
    gallery_image = get_object_or_404(Gallery, id=image_id)
    gallery_image.delete()
    messages.success(request, 'Gallery image deleted!')
    return redirect('admin_gallery')


# ===========================
# REVIEWS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_reviews(request):
    """List all reviews"""
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    reviews = Review.objects.select_related('product').all()
    
    if status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)
    
    if search:
        reviews = reviews.filter(
            Q(customer_name__icontains=search) |
            Q(comment__icontains=search)
        )
    
    reviews = reviews.order_by('-created_at')
    
    pending_count = Review.objects.filter(is_approved=False).count()
    
    context = {
        'reviews': reviews,
        'status_filter': status_filter,
        'search': search,
        'pending_count': pending_count,
    }
    return render(request, 'admin/reviews/review_list.html', context)


@login_required(login_url='admin_login')
def admin_review_approve(request, review_id):
    """Approve review"""
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = True
    review.save()
    messages.success(request, f'Review by {review.customer_name} approved!')
    return redirect('admin_reviews')


@login_required(login_url='admin_login')
def admin_review_delete(request, review_id):
    """Delete review"""
    review = get_object_or_404(Review, id=review_id)
    customer_name = review.customer_name
    review.delete()
    messages.success(request, f'Review by {customer_name} deleted!')
    return redirect('admin_reviews')


# ===========================
# HOMEPAGE CAROUSEL MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_carousel(request):
    """List all carousel slides"""
    active_only = request.GET.get('active', False)
    
    slides = CarouselSlide.objects.all()
    
    if active_only:
        today = timezone.now().date()
        slides = slides.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
    
    slides = slides.order_by('display_order', '-created_at')
    
    context = {
        'slides': slides,
        'active_only': active_only,
    }
    return render(request, 'admin/carousel/carousel_list.html', context)


@login_required(login_url='admin_login')
def admin_carousel_add(request):
    """Add carousel slide"""
    if request.method == 'POST':
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        button_text = request.POST.get('button_text', 'Order Now')
        button_link = request.POST.get('button_link', '/order/')
        display_order = request.POST.get('display_order', 0)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        
        CarouselSlide.objects.create(
            title=title,
            subtitle=subtitle,
            description=description,
            image=image,
            button_text=button_text,
            button_link=button_link,
            display_order=display_order,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        
        messages.success(request, f'Carousel slide "{title}" added successfully!')
        return redirect('admin_carousel')
    
    context = {'today': timezone.now().date()}
    return render(request, 'admin/carousel/carousel_form.html', context)


@login_required(login_url='admin_login')
def admin_carousel_edit(request, slide_id):
    """Edit carousel slide"""
    slide = get_object_or_404(CarouselSlide, id=slide_id)
    
    if request.method == 'POST':
        slide.title = request.POST.get('title')
        slide.subtitle = request.POST.get('subtitle')
        slide.description = request.POST.get('description')
        slide.button_text = request.POST.get('button_text', 'Order Now')
        slide.button_link = request.POST.get('button_link', '/order/')
        slide.display_order = request.POST.get('display_order', 0)
        slide.start_date = request.POST.get('start_date')
        slide.end_date = request.POST.get('end_date')
        slide.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            slide.image = request.FILES.get('image')
        
        slide.save()
        messages.success(request, f'Carousel slide "{slide.title}" updated successfully!')
        return redirect('admin_carousel')
    
    context = {'slide': slide}
    return render(request, 'admin/carousel/carousel_form.html', context)


@login_required(login_url='admin_login')
def admin_carousel_delete(request, slide_id):
    """Delete carousel slide"""
    slide = get_object_or_404(CarouselSlide, id=slide_id)
    slide_title = slide.title
    slide.delete()
    messages.success(request, f'Carousel slide "{slide_title}" deleted successfully!')
    return redirect('admin_carousel')


# ===========================
# OFFERS & BANNERS MANAGEMENT
# ===========================

@login_required(login_url='admin_login')
def admin_offers(request):
    """List all offers and banners"""
    active_only = request.GET.get('active', False)
    
    offers = OfferBanner.objects.all()
    
    if active_only:
        today = timezone.now().date()
        offers = offers.filter(
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        )
    
    offers = offers.order_by('-created_at')
    
    context = {
        'offers': offers,
        'active_only': active_only,
    }
    return render(request, 'admin/offers/offer_list.html', context)


@login_required(login_url='admin_login')
def admin_offer_add(request):
    """Add promotional offer"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        discount_percentage = request.POST.get('discount_percentage')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        
        OfferBanner.objects.create(
            title=title,
            description=description,
            image=image,
            discount_percentage=discount_percentage if discount_percentage else None,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        
        messages.success(request, f'Offer "{title}" added successfully!')
        return redirect('admin_offers')
    
    context = {'today': timezone.now().date()}
    return render(request, 'admin/offers/offer_form.html', context)


@login_required(login_url='admin_login')
def admin_offer_edit(request, offer_id):
    """Edit promotional offer"""
    offer = get_object_or_404(OfferBanner, id=offer_id)
    
    if request.method == 'POST':
        offer.title = request.POST.get('title')
        offer.description = request.POST.get('description')
        offer.discount_percentage = request.POST.get('discount_percentage') or None
        offer.start_date = request.POST.get('start_date')
        offer.end_date = request.POST.get('end_date')
        offer.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            offer.image = request.FILES.get('image')
        
        offer.save()
        messages.success(request, f'Offer "{offer.title}" updated successfully!')
        return redirect('admin_offers')
    
    context = {'offer': offer}
    return render(request, 'admin/offers/offer_form.html', context)


@login_required(login_url='admin_login')
def admin_offer_delete(request, offer_id):
    """Delete promotional offer"""
    offer = get_object_or_404(OfferBanner, id=offer_id)
    offer_title = offer.title
    offer.delete()
    messages.success(request, f'Offer "{offer_title}" deleted successfully!')
    return redirect('admin_offers')


# ===========================
# REPORTS
# ===========================

@login_required(login_url='admin_login')
def admin_sales_report(request):
    """Generate sales report"""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')
    export_format = request.GET.get('export', '')
    
    orders = Order.objects.select_related('customer', 'product', 'size').filter(
        status__in=['confirmed', 'completed']
    )
    
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    if status:
        orders = orders.filter(status=status)
    
    orders = orders.order_by('-created_at')
    
    # Calculate totals
    total_orders = orders.count()
    total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Export to CSV
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Date', 'Customer', 'Product', 'Size', 'Quantity', 'Amount', 'Status'])
        
        for order in orders:
            writer.writerow([
                order.order_number,
                order.created_at.strftime('%Y-%m-%d'),
                order.customer.name,
                order.product.name,
                order.size.name,
                order.quantity,
                order.total_price,
                order.get_status_display()
            ])
        
        return response
    
    # Monthly breakdown
    monthly_data = orders.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_sales=Sum('total_price'),
        order_count=Count('id')
    ).order_by('month')
    
    context = {
        'orders': orders[:100],  # Limit to 100 for display
        'total_orders': total_orders,
        'total_sales': total_sales,
        'date_from': date_from,
        'date_to': date_to,
        'status': status,
        'monthly_data': monthly_data,
    }
    return render(request, 'admin/reports/sales_report.html', context)


@login_required(login_url='admin_login')
def admin_expense_report(request):
    """Generate expense report"""
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    export_format = request.GET.get('export', '')
    
    bills = PurchaseBill.objects.all()
    
    if date_from:
        bills = bills.filter(date__gte=date_from)
    
    if date_to:
        bills = bills.filter(date__lte=date_to)
    
    bills = bills.order_by('-date')
    
    # Calculate totals
    total_bills = bills.count()
    total_expenses = bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Export to CSV
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Supplier', 'Amount', 'Notes'])
        
        for bill in bills:
            writer.writerow([
                bill.date.strftime('%Y-%m-%d'),
                bill.supplier_name,
                bill.total_amount,
                bill.notes
            ])
        
        return response
    
    # Monthly breakdown
    monthly_data = bills.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total_expenses=Sum('total_amount'),
        bill_count=Count('id')
    ).order_by('month')
    
    context = {
        'bills': bills[:100],  # Limit to 100 for display
        'total_bills': total_bills,
        'total_expenses': total_expenses,
        'date_from': date_from,
        'date_to': date_to,
        'monthly_data': monthly_data,
    }
    return render(request, 'admin/reports/expense_report.html', context)


# ===========================
# AJAX / API ENDPOINTS
# ===========================

@login_required(login_url='admin_login')
def get_subcategories(request):
    """Get subcategories for a category (AJAX)"""
    category_id = request.GET.get('category_id')
    subcategories = Subcategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values('id', 'name')
    
    return JsonResponse(list(subcategories), safe=False)


@login_required(login_url='admin_login')
def get_event_suggestions(request):
    """Get suggestions for an event (AJAX)"""
    event_id = request.GET.get('event_id')
    suggestions = EventSuggestion.objects.filter(
        event_id=event_id
    ).values('id', 'suggested_item', 'note')
    
    return JsonResponse(list(suggestions), safe=False)


@login_required(login_url='admin_login')
def get_product_sizes_prices(request):
    """Get sizes and prices for a product (AJAX)"""
    product_id = request.GET.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    
    # Get sizes with their custom prices from ProductPrice table
    sizes_data = []
    for size in product.sizes.filter(is_active=True):
        try:
            product_price = ProductPrice.objects.get(product=product, size=size)
            price = product_price.price
        except ProductPrice.DoesNotExist:
            price = 0
        
        sizes_data.append({
            'id': size.id,
            'name': size.name,
            'price': float(price),
            'weight_in_kg': float(size.weight_in_kg)
        })
    
    return JsonResponse(sizes_data, safe=False)


@login_required(login_url='admin_login')
def get_sizes_for_category(request):
    """Get sizes available for a category (AJAX)"""
    category_id = request.GET.get('category_id')
    from .models import Category
    try:
        category = Category.objects.get(id=category_id)
        sizes = category.sizes.filter(is_active=True).order_by('display_order', 'weight_in_kg')
    except (Category.DoesNotExist, ValueError, TypeError):
        sizes = []

    sizes_data = [
        {
            'id': size.id,
            'name': size.name,
            'weight_in_kg': float(size.weight_in_kg),
        }
        for size in sizes
    ]
    return JsonResponse(sizes_data, safe=False)


# ===========================
# CUSTOM CAKE BUILDER
# ===========================

@login_required(login_url='admin_login')
def admin_custom_orders(request):
    """List all custom cake orders"""
    orders = CustomCakeOrder.objects.select_related('customer', 'shape', 'tier', 'flavor').order_by('-created_at')
    
    context = {'orders': orders}
    return render(request, 'admin/custom_cakes/order_list.html', context)


@login_required(login_url='admin_login')
def admin_custom_order_detail(request, order_id):
    """View custom order details"""
    order = get_object_or_404(CustomCakeOrder, id=order_id)
    order_decorations = CustomCakeOrderDecoration.objects.filter(custom_order=order).select_related('decoration')
    reference_images = CustomCakeReferenceImage.objects.filter(custom_order=order)
    
    context = {
        'order': order,
        'order_decorations': order_decorations,
        'reference_images': reference_images,
    }
    return render(request, 'admin/custom_cakes/order_detail.html', context)


@login_required(login_url='admin_login')
def admin_custom_order_edit(request, order_id):
    """Edit custom order"""
    order = get_object_or_404(CustomCakeOrder, id=order_id)
    
    if request.method == 'POST':
        # Update order fields
        order.status = request.POST.get('status', order.status)
        order.final_price = request.POST.get('final_price') or None
        order.custom_flavor_price_per_kg = request.POST.get('custom_flavor_price_per_kg') or None
        order.special_instructions = request.POST.get('special_instructions', '')
        order.custom_message = request.POST.get('custom_message', '')
        order.delivery_date = request.POST.get('delivery_date')
        order.delivery_time = request.POST.get('delivery_time') or None
        
        order.save()
        
        # Recalculate estimate if custom flavor price was changed
        if order.custom_flavor_price_per_kg and not order.flavor:
            order.update_estimate()
        
        messages.success(request, f'Custom order {order.order_number} updated successfully!')
        return redirect('admin_custom_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'shapes': CakeShape.objects.filter(is_active=True).order_by('display_order'),
        'tiers': CakeTier.objects.filter(is_active=True).order_by('display_order'),
        'flavors': Flavor.objects.filter(is_active=True).order_by('display_order'),
        'decorations': Decoration.objects.filter(is_active=True).order_by('category', 'display_order'),
        'order_decorations': CustomCakeOrderDecoration.objects.filter(custom_order=order).select_related('decoration'),
    }
    return render(request, 'admin/custom_cakes/order_edit.html', context)


@login_required(login_url='admin_login')
def admin_cake_shapes(request):
    """List all cake shapes"""
    shapes = CakeShape.objects.all().order_by('display_order', 'name')
    context = {'shapes': shapes}
    return render(request, 'admin/custom_cakes/shape_list.html', context)


@login_required(login_url='admin_login')
def admin_cake_tiers(request):
    """List all cake tiers"""
    tiers = CakeTier.objects.all().order_by('display_order', 'tiers_count')
    context = {'tiers': tiers}
    return render(request, 'admin/custom_cakes/tier_list.html', context)


@login_required(login_url='admin_login')
def admin_decorations(request):
    """List all decorations"""
    decorations = Decoration.objects.all().order_by('category', 'display_order', 'name')
    context = {'decorations': decorations}
    return render(request, 'admin/custom_cakes/decoration_list.html', context)


@login_required(login_url='admin_login')
def admin_cake_shape_add(request):
    """Add cake shape"""
    if request.method == 'POST':
        name = request.POST.get('name')
        base_price_per_kg = request.POST.get('base_price_per_kg')
        description = request.POST.get('description', '')
        display_order = request.POST.get('display_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        shape = CakeShape.objects.create(
            name=name,
            base_price_per_kg=base_price_per_kg,
            description=description,
            display_order=display_order,
            is_active=is_active
        )
        
        # Handle image upload
        if request.FILES.get('image'):
            shape.image = request.FILES.get('image')
            shape.save()
        
        messages.success(request, f'Cake shape "{name}" added successfully!')
        return redirect('admin_cake_shapes')
    
    return render(request, 'admin/custom_cakes/shape_form.html')


@login_required(login_url='admin_login')
def admin_cake_shape_edit(request, shape_id):
    """Edit cake shape"""
    shape = get_object_or_404(CakeShape, id=shape_id)
    
    if request.method == 'POST':
        shape.name = request.POST.get('name')
        shape.base_price_per_kg = request.POST.get('base_price_per_kg')
        shape.description = request.POST.get('description', '')
        shape.display_order = request.POST.get('display_order', 0)
        shape.is_active = request.POST.get('is_active') == 'on'
        
        # Handle image upload
        if request.FILES.get('image'):
            shape.image = request.FILES.get('image')
        
        shape.save()
        messages.success(request, f'Cake shape "{shape.name}" updated successfully!')
        return redirect('admin_cake_shapes')
    
    context = {'shape': shape}
    return render(request, 'admin/custom_cakes/shape_form.html', context)


@login_required(login_url='admin_login')
def admin_cake_shape_delete(request, shape_id):
    """Delete cake shape"""
    shape = get_object_or_404(CakeShape, id=shape_id)
    shape_name = shape.name
    shape.delete()
    messages.success(request, f'Cake shape "{shape_name}" deleted successfully!')
    return redirect('admin_cake_shapes')


@login_required(login_url='admin_login')
def admin_cake_tier_add(request):
    """Add cake tier"""
    if request.method == 'POST':
        name = request.POST.get('name')
        tiers_count = request.POST.get('tiers_count')
        price_multiplier = request.POST.get('price_multiplier')
        description = request.POST.get('description', '')
        display_order = request.POST.get('display_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        tier = CakeTier.objects.create(
            name=name,
            tiers_count=tiers_count,
            price_multiplier=price_multiplier,
            description=description,
            display_order=display_order,
            is_active=is_active
        )
        
        # Handle image upload
        if request.FILES.get('image'):
            tier.image = request.FILES.get('image')
            tier.save()
        
        messages.success(request, f'Cake tier "{name}" added successfully!')
        return redirect('admin_cake_tiers')
    
    return render(request, 'admin/custom_cakes/tier_form.html')


@login_required(login_url='admin_login')
def admin_cake_tier_edit(request, tier_id):
    """Edit cake tier"""
    tier = get_object_or_404(CakeTier, id=tier_id)
    
    if request.method == 'POST':
        tier.name = request.POST.get('name')
        tier.tiers_count = request.POST.get('tiers_count')
        tier.price_multiplier = request.POST.get('price_multiplier')
        tier.description = request.POST.get('description', '')
        tier.display_order = request.POST.get('display_order', 0)
        tier.is_active = request.POST.get('is_active') == 'on'
        
        # Handle image upload
        if request.FILES.get('image'):
            tier.image = request.FILES.get('image')
        
        tier.save()
        messages.success(request, f'Cake tier "{tier.name}" updated successfully!')
        return redirect('admin_cake_tiers')
    
    context = {'tier': tier}
    return render(request, 'admin/custom_cakes/tier_form.html', context)


@login_required(login_url='admin_login')
def admin_cake_tier_delete(request, tier_id):
    """Delete cake tier"""
    tier = get_object_or_404(CakeTier, id=tier_id)
    tier_name = tier.name
    tier.delete()
    messages.success(request, f'Cake tier "{tier_name}" deleted successfully!')
    return redirect('admin_cake_tiers')


@login_required(login_url='admin_login')
def admin_decoration_add(request):
    """Add decoration"""
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description', '')
        display_order = request.POST.get('display_order', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        decoration = Decoration.objects.create(
            name=name,
            category=category,
            price=price,
            description=description,
            display_order=display_order,
            is_active=is_active
        )
        
        # Handle image upload
        if request.FILES.get('image'):
            decoration.image = request.FILES.get('image')
            decoration.save()
        
        messages.success(request, f'Decoration "{name}" added successfully!')
        return redirect('admin_decorations')
    
    return render(request, 'admin/custom_cakes/decoration_form.html')


@login_required(login_url='admin_login')
def admin_decoration_edit(request, decoration_id):
    """Edit decoration"""
    decoration = get_object_or_404(Decoration, id=decoration_id)
    
    if request.method == 'POST':
        decoration.name = request.POST.get('name')
        decoration.category = request.POST.get('category')
        decoration.price = request.POST.get('price')
        decoration.description = request.POST.get('description', '')
        decoration.display_order = request.POST.get('display_order', 0)
        decoration.is_active = request.POST.get('is_active') == 'on'
        
        # Handle image upload
        if request.FILES.get('image'):
            decoration.image = request.FILES.get('image')
        
        decoration.save()
        messages.success(request, f'Decoration "{decoration.name}" updated successfully!')
        return redirect('admin_decorations')
    
    context = {'decoration': decoration}
    return render(request, 'admin/custom_cakes/decoration_form.html', context)


@login_required(login_url='admin_login')
def admin_decoration_delete(request, decoration_id):
    """Delete decoration"""
    decoration = get_object_or_404(Decoration, id=decoration_id)
    decoration_name = decoration.name
    decoration.delete()
    messages.success(request, f'Decoration "{decoration_name}" deleted successfully!')
    return redirect('admin_decorations')


# ===========================
# GIFT BOXES
# ===========================

@login_required(login_url='admin_login')
def admin_gift_boxes(request):
    """List all gift boxes"""
    gift_boxes = GiftBox.objects.all().prefetch_related('items__product', 'items__size')
    
    context = {
        'gift_boxes': gift_boxes
    }
    return render(request, 'admin/gift_boxes.html', context)


@login_required(login_url='admin_login')
def admin_gift_box_add(request):
    """Add new gift box"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        main_image = request.FILES.get('main_image')
        pricing_type = request.POST.get('pricing_type')
        fixed_price = request.POST.get('fixed_price') or None
        discount_percentage = request.POST.get('discount_percentage') or None
        is_active = request.POST.get('is_active') == 'on'
        display_order = request.POST.get('display_order', 0)
        
        gift_box = GiftBox.objects.create(
            name=name,
            description=description,
            main_image=main_image,
            pricing_type=pricing_type,
            fixed_price=fixed_price,
            discount_percentage=discount_percentage,
            is_active=is_active,
            display_order=display_order
        )
        
        messages.success(request, f'Gift box "{name}" created successfully! Now add items to it.')
        return redirect('admin_gift_box_edit', gift_box_id=gift_box.id)
    
    context = {
        'products': Product.objects.filter(is_active=True).select_related('category', 'subcategory'),
        'sizes': Size.objects.filter(is_active=True),
        'categories': Category.objects.filter(is_active=True)
    }
    return render(request, 'admin/gift_box_form.html', context)


@login_required(login_url='admin_login')
def admin_gift_box_edit(request, gift_box_id):
    """Edit gift box"""
    gift_box = get_object_or_404(GiftBox, id=gift_box_id)
    
    if request.method == 'POST':
        gift_box.name = request.POST.get('name')
        gift_box.description = request.POST.get('description')
        
        if request.FILES.get('main_image'):
            gift_box.main_image = request.FILES.get('main_image')
        
        gift_box.pricing_type = request.POST.get('pricing_type')
        gift_box.fixed_price = request.POST.get('fixed_price') or None
        gift_box.discount_percentage = request.POST.get('discount_percentage') or None
        gift_box.is_active = request.POST.get('is_active') == 'on'
        gift_box.display_order = request.POST.get('display_order', 0)
        gift_box.save()
        
        messages.success(request, f'Gift box "{gift_box.name}" updated successfully!')
        return redirect('admin_gift_boxes')
    
    context = {
        'gift_box': gift_box,
        'products': Product.objects.filter(is_active=True).select_related('category', 'subcategory'),
        'sizes': Size.objects.filter(is_active=True),
        'categories': Category.objects.filter(is_active=True),
        'items': gift_box.items.all()
    }
    return render(request, 'admin/gift_box_form.html', context)


@login_required(login_url='admin_login')
def admin_gift_box_add_item(request, gift_box_id):
    """Add item to gift box"""
    gift_box = get_object_or_404(GiftBox, id=gift_box_id)
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        size_id = request.POST.get('size')
        quantity = request.POST.get('quantity', 1)
        display_order = request.POST.get('display_order', 0)
        
        product = get_object_or_404(Product, id=product_id)
        size = get_object_or_404(Size, id=size_id)
        
        # Check if this combination already exists
        existing = GiftBoxItem.objects.filter(
            gift_box=gift_box,
            product=product,
            size=size
        ).first()
        
        if existing:
            messages.warning(request, 'This product-size combination already exists in this gift box!')
        else:
            GiftBoxItem.objects.create(
                gift_box=gift_box,
                product=product,
                size=size,
                quantity=quantity,
                display_order=display_order
            )
            messages.success(request, f'Added {product.name} ({size.name}) to gift box!')
    
    return redirect('admin_gift_box_edit', gift_box_id=gift_box_id)


@login_required(login_url='admin_login')
def admin_gift_box_remove_item(request, item_id):
    """Remove item from gift box"""
    item = get_object_or_404(GiftBoxItem, id=item_id)
    gift_box_id = item.gift_box.id
    item.delete()
    messages.success(request, 'Item removed from gift box!')
    return redirect('admin_gift_box_edit', gift_box_id=gift_box_id)


@login_required(login_url='admin_login')
def admin_gift_box_delete(request, gift_box_id):
    """Delete gift box"""
    gift_box = get_object_or_404(GiftBox, id=gift_box_id)
    gift_box_name = gift_box.name
    gift_box.delete()
    messages.success(request, f'Gift box "{gift_box_name}" deleted successfully!')
    return redirect('admin_gift_boxes')


@login_required(login_url='admin_login')
def admin_gift_box_orders(request):
    """List all gift box orders"""
    orders = GiftBoxOrder.objects.all().select_related('customer', 'gift_box', 'event')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_filter': status_filter
    }
    return render(request, 'admin/gift_box_orders.html', context)


@login_required(login_url='admin_login')
def admin_gift_box_order_detail(request, order_id):
    """View gift box order details"""
    order = get_object_or_404(GiftBoxOrder, id=order_id)
    
    context = {
        'order': order,
        'items': order.gift_box.items.all()
    }
    return render(request, 'admin/gift_box_order_detail.html', context)


@login_required(login_url='admin_login')
def admin_accept_gift_box_order(request, order_id):
    """Accept/Confirm a gift box order"""
    if request.method == 'POST':
        order = get_object_or_404(GiftBoxOrder, id=order_id)
        
        if order.status == 'pending':
            order.status = 'confirmed'
            order.save()
            messages.success(request, f'Order {order.order_number} has been confirmed successfully!')
        else:
            messages.warning(request, f'Order {order.order_number} is already {order.get_status_display()}.')
    
    return redirect('admin_gift_box_orders')


@login_required(login_url='admin_login')
def admin_delete_gift_box_order(request, order_id):
    """Delete a gift box order"""
    if request.method == 'POST':
        order = get_object_or_404(GiftBoxOrder, id=order_id)
        order_number = order.order_number
        
        # Prevent deletion of completed or cancelled orders
        if order.status in ['completed', 'cancelled']:
            messages.error(request, f'Cannot delete {order.get_status_display()} order {order_number}.')
        else:
            order.delete()
            messages.success(request, f'Order {order_number} has been deleted successfully!')
    
    return redirect('admin_gift_box_orders')


# ===========================
# GIFT BOX AJAX ENDPOINTS
# ===========================

@login_required(login_url='admin_login')
def get_products_by_category(request):
    """Get products filtered by category and subcategory (AJAX)"""
    category_id = request.GET.get('category_id')
    subcategory_id = request.GET.get('subcategory_id')
    
    products = Product.objects.filter(is_active=True).select_related('category', 'subcategory')
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if subcategory_id:
        products = products.filter(subcategory_id=subcategory_id)
    
    products_list = []
    for product in products:
        products_list.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else '',
            'subcategory': product.subcategory.name if product.subcategory else ''
        })
    
    return JsonResponse(products_list, safe=False)


@login_required(login_url='admin_login')
def get_sizes_for_product(request):
    """Get sizes available for a specific product (AJAX)"""
    product_id = request.GET.get('product_id')
    
    if not product_id:
        return JsonResponse([], safe=False)
    
    try:
        product = Product.objects.get(id=product_id)
        sizes = product.sizes.filter(is_active=True).order_by('display_order', 'weight_in_kg')
        
        sizes_list = []
        for size in sizes:
            # Get price for this product-size combination
            try:
                price = ProductPrice.objects.get(product=product, size=size).price
            except ProductPrice.DoesNotExist:
                price = 0
            
            sizes_list.append({
                'id': size.id,
                'name': size.name,
                'price': str(price)
            })
        
        return JsonResponse(sizes_list, safe=False)
    except Product.DoesNotExist:
        return JsonResponse([], safe=False)


@login_required(login_url='admin_login')
def create_product_inline(request):
    """Create a new product inline from gift box form (AJAX)"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id') or None
        main_image = request.FILES.get('main_image')
        
        if not name or not category_id:
            return JsonResponse({'success': False, 'error': 'Name and Category are required'})
        
        try:
            category = Category.objects.get(id=category_id)
            subcategory = None
            if subcategory_id:
                subcategory = Subcategory.objects.get(id=subcategory_id)
            
            product = Product.objects.create(
                name=name,
                description=description,
                category=category,
                subcategory=subcategory,
                main_image=main_image if main_image else None,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'category': category.name,
                    'subcategory': subcategory.name if subcategory else ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required(login_url='admin_login')
def create_product_size_price(request):
    """Create size and price for a product inline (AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        size_name = request.POST.get('size_name')
        size_weight = request.POST.get('size_weight', '1.0')
        price = request.POST.get('price')
        
        if not product_id or not size_name or not price:
            return JsonResponse({'success': False, 'error': 'Product, Size name, and Price are required'})
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Create or get size
            size, created = Size.objects.get_or_create(
                name=size_name,
                defaults={
                    'weight_in_kg': Decimal(size_weight),
                    'is_active': True
                }
            )
            
            # Link size to product if not already linked
            if size not in product.sizes.all():
                product.sizes.add(size)
            
            # Create or update product price
            product_price, created = ProductPrice.objects.update_or_create(
                product=product,
                size=size,
                defaults={'price': Decimal(price)}
            )
            
            return JsonResponse({
                'success': True,
                'size': {
                    'id': size.id,
                    'name': size.name,
                    'price': str(product_price.price)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

