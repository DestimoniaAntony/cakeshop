from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from . import utils
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Import models from admin_app
from admin_app.models import (
    Category, Subcategory, Product, Size, ProductPrice,
    Event, EventSuggestion, Customer, Order,
    Enquiry, Gallery, Review, CarouselSlide, OfferBanner,
    CakeShape, CakeTier, Decoration, CustomCakeOrder,
    Flavor, CustomCakeOrderDecoration, CustomCakeReferenceImage,
    GiftBox, GiftBoxItem, GiftBoxOrder,
    LoyaltyCard, LoyaltyReward, PointsTransaction, Referral, Achievement, CustomerAchievement
)

# ===========================
# CART (Session-based)
# ===========================

def _get_cart(session):
    cart = session.get('cart')
    if cart is None:
        cart = []
        session['cart'] = cart
    return cart

def add_to_cart(request):
    if request.method != 'POST':
        return redirect('products')
    product_id = request.POST.get('product_id')
    size_id = request.POST.get('size_id')
    quantity = int(request.POST.get('quantity', 1))
    delivery_date = request.POST.get('delivery_date')
    delivery_time = request.POST.get('delivery_time', '')
    custom_message = request.POST.get('custom_message', '')
    special_instructions = request.POST.get('special_instructions', '')

    product = get_object_or_404(Product, id=product_id, is_active=True)
    size = get_object_or_404(Size, id=size_id, is_active=True)
    price = ProductPrice.objects.filter(product=product, size=size).first()
    if not price:
        messages.error(request, 'Selected size not priced for this product.')
        return redirect('product_detail', product_id=product.id)

    cart = _get_cart(request.session)
    # Merge with identical line (product+size+delivery_date)
    merged = False
    for line in cart:
        if line.get('type') == 'product' and line['product_id'] == product.id and line['size_id'] == size.id and line.get('delivery_date') == delivery_date:
            line['quantity'] += quantity
            merged = True
            break
    if not merged:
        cart.append({
            'type': 'product',
            'product_id': product.id,
            'product_name': product.name,
            'size_id': size.id,
            'size_name': size.name,
            'unit_price': float(price.price),
            'quantity': quantity,
            'delivery_date': delivery_date,
            'delivery_time': delivery_time,
            'custom_message': custom_message,
            'special_instructions': special_instructions,
        })
    request.session.modified = True
    messages.success(request, 'Added to cart.')
    return redirect('view_cart')

def add_custom_to_cart(request):
    if request.method != 'POST':
        return redirect('custom_cakes')
    
    # Collect all custom cake details
    shape_id = request.POST.get('shape_id')
    tier_id = request.POST.get('tier_id')
    total_weight = request.POST.get('total_weight')
    flavor_option = request.POST.get('flavor_option')
    
    # Product/Size (if product option chosen)
    product_id = request.POST.get('product_id')
    size_id = request.POST.get('size_id')
    
    # Flavor (if custom option chosen)
    flavor_id = request.POST.get('flavor_id')
    flavor_description = request.POST.get('flavor_description', '')
    
    # Decorations
    decoration_ids = request.POST.getlist('decoration_ids')
    decoration_quantities = request.POST.getlist('decoration_quantities')
    
    # Get names for display
    shape = get_object_or_404(CakeShape, id=shape_id)
    tier = get_object_or_404(CakeTier, id=tier_id)
    
    flavor_display = 'Not specified'
    if flavor_option == 'product' and product_id and size_id:
        product = Product.objects.get(id=product_id)
        size = Size.objects.get(id=size_id)
        flavor_display = f"{product.name} - {size.name}"
        total_weight = str(size.weight_in_kg)
    elif flavor_id:
        flavor = Flavor.objects.get(id=flavor_id)
        flavor_display = flavor.name
    elif flavor_description:
        flavor_display = flavor_description
    
    # Build decoration summary
    decoration_summary = []
    if decoration_ids:
        for i, dec_id in enumerate(decoration_ids):
            try:
                decoration = Decoration.objects.get(id=dec_id)
                qty = decoration_quantities[i] if i < len(decoration_quantities) else 1
                decoration_summary.append({
                    'id': dec_id,
                    'name': decoration.name,
                    'quantity': qty,
                    'price': float(decoration.price)
                })
            except:
                pass
    
    cart = _get_cart(request.session)
    cart.append({
        'type': 'custom_cake',
        'shape_id': shape_id,
        'shape_name': shape.name,
        'tier_id': tier_id,
        'tier_name': tier.name,
        'total_weight': total_weight,
        'flavor_option': flavor_option,
        'product_id': product_id,
        'size_id': size_id,
        'flavor_id': flavor_id,
        'flavor_description': flavor_description,
        'flavor_display': flavor_display,
        'decorations': decoration_summary,
        'decoration_ids': decoration_ids,
        'decoration_quantities': decoration_quantities,
        'unit_price': 0,  # Custom cakes quoted later
        'quantity': 1,
    })
    
    request.session.modified = True
    messages.success(request, 'Custom cake added to cart.')
    return redirect('view_cart')

def view_cart(request):
    cart = _get_cart(request.session)
    # compute line totals
    for line in cart:
        try:
            if line.get('type') == 'custom_cake':
                # Custom cakes - show "Quote Required"
                line['line_total'] = 0
                line['display_price'] = 'Quote Required'
            else:
                line['line_total'] = float(line['unit_price']) * int(line['quantity'])
                line['display_price'] = f"₹{int(line['line_total'])}"
        except Exception:
            line['line_total'] = 0
            line['display_price'] = '₹0'
    
    total = sum(line.get('line_total', 0) for line in cart)
    has_custom_cakes = any(line.get('type') == 'custom_cake' for line in cart)
    
    return render(request, 'customer/cart.html', {
        'cart': cart,
        'cart_total': total,
        'has_custom_cakes': has_custom_cakes,
    })

def update_cart_item(request):
    if request.method != 'POST':
        return redirect('view_cart')
    idx = int(request.POST.get('index', -1))
    qty = int(request.POST.get('quantity', 1))
    cart = _get_cart(request.session)
    if 0 <= idx < len(cart):
        cart[idx]['quantity'] = max(1, qty)
        request.session.modified = True
    return redirect('view_cart')

def remove_cart_item(request):
    if request.method != 'POST':
        return redirect('view_cart')
    idx = int(request.POST.get('index', -1))
    cart = _get_cart(request.session)
    if 0 <= idx < len(cart):
        cart.pop(idx)
        request.session.modified = True
    return redirect('view_cart')

def checkout_submit(request):
    if request.method != 'POST':
        return redirect('view_cart')

    # Collect customer details once for all orders
    customer_name = request.POST.get('customer_name')
    customer_phone = request.POST.get('customer_phone')
    customer_email = request.POST.get('customer_email', '')
    customer_address = request.POST.get('delivery_address', '')

    customer, _ = Customer.objects.get_or_create(
        phone_number=customer_phone,
        defaults={'name': customer_name, 'email': customer_email, 'address': customer_address}
    )
    if customer.name != customer_name or (customer_email and customer.email != customer_email) or (customer_address and customer.address != customer_address):
        customer.name = customer_name
        if customer_email:
            customer.email = customer_email
        if customer_address:
            customer.address = customer_address
        customer.save()

    # Consider customer as logged-in for loyalty (required for redemption)
    request.session['customer_phone'] = customer.phone_number
    request.session.modified = True

    # Optional global delivery and notes
    order_delivery_date = request.POST.get('delivery_date')
    order_delivery_time = request.POST.get('delivery_time')
    order_custom_message = request.POST.get('custom_message', '')
    order_special_instructions = request.POST.get('special_instructions', '')

    cart = _get_cart(request.session)
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('products')

    created_orders = []
    created_custom_orders = []
    
    for line in cart:
        if line.get('type') == 'custom_cake':
            # Create CustomCakeOrder
            shape = CakeShape.objects.get(id=line['shape_id'])
            tier = CakeTier.objects.get(id=line['tier_id'])
            
            custom_order = CustomCakeOrder(
                customer=customer,
                shape=shape,
                tier=tier,
                total_weight=Decimal(line['total_weight']),
                delivery_date=order_delivery_date or (timezone.now().date() + timedelta(days=2)),
                delivery_time=order_delivery_time or None,
                delivery_address=customer_address,
                custom_message=order_custom_message or '',
                special_instructions=order_special_instructions or '',
            )
            
            # Set flavor based on option
            if line.get('flavor_option') == 'product' and line.get('product_id') and line.get('size_id'):
                custom_order.product_id = line['product_id']
                custom_order.size_id = line['size_id']
            elif line.get('flavor_id'):
                custom_order.flavor_id = line['flavor_id']
            elif line.get('flavor_description'):
                custom_order.flavor_description = line['flavor_description']
            
            custom_order.save()
            
            # Add decorations
            if line.get('decorations'):
                for dec in line['decorations']:
                    CustomCakeOrderDecoration.objects.create(
                        custom_order=custom_order,
                        decoration_id=dec['id'],
                        quantity=int(dec['quantity'])
                    )
            
            created_custom_orders.append(custom_order)
            
        else:
            # Regular product order
            product = Product.objects.get(id=line['product_id'])
            size = Size.objects.get(id=line['size_id'])
            order = Order(
                customer=customer,
                product=product,
                size=size,
                quantity=line['quantity'],
                delivery_date=order_delivery_date or line.get('delivery_date') or (timezone.now().date() + timedelta(days=1)),
                delivery_time=order_delivery_time or line.get('delivery_time') or None,
                custom_message=order_custom_message or line.get('custom_message') or '',
                special_instructions=order_special_instructions or line.get('special_instructions') or '',
            )
            order.unit_price = order.calculate_unit_price()
            order.total_price = order.unit_price * order.quantity
            order.save()
            created_orders.append(order)

    # Apply staged loyalty selections to the first created regular order (simple flow)
    # We apply reward first, then points, and record transactions. This operates post-order creation.
    selected_reward_id = request.session.get('selected_reward_id')
    pending_points = int(request.session.get('pending_points_redeem', 0) or 0)

    if created_orders:
        order_to_apply = created_orders[0]
        # Fetch loyalty card with row lock to avoid race conditions
        from django.db import transaction
        with transaction.atomic():
            customer_refreshed = Customer.objects.select_for_update().get(id=customer.id)
            try:
                loyalty_card = LoyaltyCard.objects.select_for_update().get(customer=customer_refreshed)
            except LoyaltyCard.DoesNotExist:
                loyalty_card = None

            order_payable = order_to_apply.total_price

            # Apply reward (percentage) if selected and valid
            if selected_reward_id and loyalty_card:
                reward = LoyaltyReward.objects.filter(id=selected_reward_id, loyalty_card=loyalty_card, status='active').first()
                if reward and reward.is_valid() and reward.used_on_order is None:
                    try:
                        discount_percent = Decimal(reward.discount_percentage)
                    except Exception:
                        discount_percent = Decimal('0')
                    if discount_percent > 0:
                        discount_amount = (order_payable * discount_percent) / Decimal('100')
                        # Reduce payable
                        order_payable = max(Decimal('0'), order_payable - discount_amount)
                        # Mark reward as used
                        reward.status = 'used'
                        reward.used_on_order = order_to_apply
                        reward.used_date = timezone.now()
                        reward.save()

            # Apply points redemption, capped by balance and remaining payable
            if pending_points and loyalty_card:
                try:
                    points_balance = int(loyalty_card.points_balance)
                except Exception:
                    points_balance = 0
                max_points_by_payable = _calculate_max_points_redeemable(order_payable, points_balance)
                points_to_redeem = max(0, min(int(pending_points), max_points_by_payable))
                if points_to_redeem > 0 and loyalty_card.points_balance >= points_to_redeem:
                    # Deduct points and reduce payable
                    loyalty_card.points_balance -= points_to_redeem
                    loyalty_card.save()
                    order_payable = max(Decimal('0'), order_payable - Decimal(points_to_redeem))
                    # Log points redemption
                    PointsTransaction.objects.create(
                        loyalty_card=loyalty_card,
                        points=points_to_redeem,
                        transaction_type='redeemed',
                        reason=f'Redeemed on order {order_to_apply.order_number}',
                        order=order_to_apply
                    )

            # Optionally, store final payable on order special_instructions note (non-invasive)
            try:
                if order_payable != order_to_apply.total_price:
                    note = order_to_apply.special_instructions or ''
                    suffix = f"\n[Loyalty Applied] Final payable after rewards/points: ₹{order_payable}"
                    order_to_apply.special_instructions = (note + suffix).strip()
                    order_to_apply.save()
            except Exception:
                pass

    # Clear cart and staged loyalty selections
    request.session['cart'] = []
    request.session.pop('selected_reward_id', None)
    request.session.pop('pending_points_redeem', None)
    request.session.modified = True

    # Redirect to first order confirmation
    if created_orders:
        return redirect('order_confirmation', order_id=created_orders[0].id)
    elif created_custom_orders:
        return redirect('custom_order_confirmation', order_number=created_custom_orders[0].order_number)
    return redirect('products')

# ===========================
# HELPER FUNCTIONS
# ===========================

def generate_order_whatsapp_message(order, customer):
    """Generate formatted WhatsApp message for regular order"""
    message = f"""🎂 *NEW ORDER - {order.product.name}*

📋 *Order Details:*
━━━━━━━━━━━━━━━━━
Order #: {order.order_number}
🍰 Product: {order.product.name}
📏 Size: {order.size.name}
🔢 Quantity: {order.quantity}
💰 Unit Price: ₹{order.unit_price}
💵 Total Price: ₹{order.total_price}

👤 *Customer Details:*
━━━━━━━━━━━━━━━━━
Name: {customer.name}
📱 WhatsApp: {customer.phone_number}
📧 Email: {customer.email or 'Not provided'}
📍 Address: {customer.address or 'Not provided'}

📅 *Delivery:*
━━━━━━━━━━━━━━━━━
Date: {order.delivery_date.strftime('%d %B, %Y') if hasattr(order.delivery_date, 'strftime') else order.delivery_date}
Time: {order.delivery_time.strftime('%I:%M %p') if order.delivery_time and hasattr(order.delivery_time, 'strftime') else (order.delivery_time if order.delivery_time else 'Not specified')}
"""
    
    if order.event:
        message += f"🎉 Event: {order.event.event_name}\n"
    
    if order.custom_message:
        message += f"\n✉️ *Message on Cake:*\n{order.custom_message}\n"
    
    if order.special_instructions:
        message += f"\n📝 *Special Instructions:*\n{order.special_instructions}\n"
    
    message += "\n━━━━━━━━━━━━━━━━━\nPlease confirm this order. Thank you! 🙏"
    
    return message


def generate_custom_cake_whatsapp_message(custom_order, customer):
    """Generate formatted WhatsApp message for custom cake order"""
    # Get decorations with quantities
    order_decorations = custom_order.order_decorations.all()
    if order_decorations:
        decorations_list = ', '.join([f"{od.quantity}× {od.decoration.name}" for od in order_decorations])
    else:
        decorations_list = 'None'
    
    # Get flavor info
    flavor_info = custom_order.flavor.name if custom_order.flavor else (custom_order.flavor_description or 'Not specified')
    
    # Get price range
    price_range = custom_order.price_range_display
    
    message = f"""🎂 *NEW CUSTOM CAKE ORDER*

📋 *Order Details:*
━━━━━━━━━━━━━━━━━
Order #: {custom_order.order_number}
⭕ Shape: {custom_order.shape.name}
🎂 Tier: {custom_order.tier.name}
⚖️ Weight: {custom_order.total_weight} kg
🍰 Flavor: {flavor_info}
✨ Decorations: {decorations_list}

👤 *Customer Details:*
━━━━━━━━━━━━━━━━━
Name: {customer.name}
📱 WhatsApp: {customer.phone_number}
📧 Email: {customer.email or 'Not provided'}
"""
    
    if custom_order.event:
        message += f"🎉 Event: {custom_order.event.event_name}\n"
    
    # Format delivery date safely
    if hasattr(custom_order.delivery_date, 'strftime'):
        delivery_date_str = custom_order.delivery_date.strftime('%d %B, %Y')
    else:
        delivery_date_str = str(custom_order.delivery_date)
    
    # Format delivery time safely
    if custom_order.delivery_time and hasattr(custom_order.delivery_time, 'strftime'):
        delivery_time_str = custom_order.delivery_time.strftime('%I:%M %p')
    else:
        delivery_time_str = str(custom_order.delivery_time) if custom_order.delivery_time else 'Not specified'
    
    message += f"""
📅 *Delivery:*
━━━━━━━━━━━━━━━━━
Date: {delivery_date_str}
Time: {delivery_time_str}
📍 Address: {custom_order.delivery_address}
"""
    
    if custom_order.custom_message:
        message += f"\n✉️ *Message on Cake:*\n{custom_order.custom_message}\n"
    
    if custom_order.special_instructions:
        message += f"\n📝 *Special Instructions:*\n{custom_order.special_instructions}\n"
    
    message += f"""
💰 *Estimated Price Range:*
{price_range}
(Base estimate: ₹{custom_order.estimated_price:,.2f})
(Final price will be confirmed)

━━━━━━━━━━━━━━━━━
Please confirm this custom order. Thank you! 🙏"""
    
    return message


def auto_send_whatsapp_message(custom_order, customer, whatsapp_message):
    """
    Automatically send WhatsApp message when order is placed.
    This function can be extended to use WhatsApp Business API in the future.
    For now, it prepares the message and could trigger client-side sending.
    """
    # Business WhatsApp number
    business_whatsapp = '919946588352'
    
    # Generate PDF URL
    pdf_url = f"https://cakesbydesti.com/generate-custom-cake-pdf/{custom_order.order_number}/"
    
    # Enhanced message with PDF link
    enhanced_message = whatsapp_message + f"\n\n📄 *Order PDF Download:*\n{pdf_url}"
    
    # For now, we'll store this in session to be used by client-side JavaScript
    # In the future, this could be extended to use WhatsApp Business API
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    
    # Store WhatsApp data in session for client-side processing
    session_data = {
        'auto_whatsapp': {
            'message': enhanced_message,
            'business_number': business_whatsapp,
            'customer_number': customer.phone_number,
            'order_number': custom_order.order_number,
            'timestamp': timezone.now().isoformat()
        }
    }
    
    # This could be extended to actually send via API
    # For now, we'll let the client-side handle the WhatsApp opening
    return session_data


# ===========================
# HOME PAGE
# ===========================

def home(request):
    """Homepage with carousel, featured products, and reviews"""
    today = timezone.now().date()
    
    # Get active carousel slides
    banners = CarouselSlide.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).order_by('display_order', '-created_at')[:5]  # Max 5 slides
    
    # Get active promotional offers
    offers = OfferBanner.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).order_by('-created_at')[:3]
    
    # Featured products (latest 8) - prefetch prices for better performance
    featured_products = Product.objects.filter(
        is_active=True
    ).prefetch_related('prices', 'sizes').order_by('-created_at')[:8]
    
    # Categories
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    )[:6]
    
    # Featured gallery images
    featured_gallery = Gallery.objects.filter(is_featured=True).order_by('-uploaded_at')[:6]
    
    # Approved reviews
    reviews = Review.objects.filter(is_approved=True).order_by('-created_at')[:6]
    
    # Events for quick order
    events = Event.objects.filter(is_active=True).order_by('event_name')
    
    context = {
        'banners': banners,  # Carousel slides
        'offers': offers,  # Promotional offers
        'featured_products': featured_products,
        'categories': categories,
        'featured_gallery': featured_gallery,
        'reviews': reviews,
        'events': events,
    }
    
    return render(request, 'customer/home.html', context)




def about(request):
    return render(request, 'customer/about-us.html')
# ===========================
# PRODUCTS
# ===========================

def products(request):
    """Product listing with filtering"""
    category_slug = request.GET.get('category', '')
    subcategory_slug = request.GET.get('subcategory', '')
    search = request.GET.get('search', '')
    
    products = Product.objects.filter(is_active=True).select_related('category', 'subcategory').prefetch_related('prices', 'sizes')
    
    if category_slug:
        products = products.filter(category__id=category_slug)
    
    if subcategory_slug:
        products = products.filter(subcategory__id=subcategory_slug)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    products = products.order_by('-created_at')
    
    # Get categories and subcategories for filter
    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    )
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search': search,
    }
    
    return render(request, 'customer/products.html', context)


def product_detail(request, product_id):
    """Product detail page"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    # Get product reviews
    reviews = Review.objects.filter(
        product=product,
        is_approved=True
    ).order_by('-created_at')
    
    # Get available sizes
    sizes = product.sizes.filter(is_active=True).order_by('display_order', 'weight_in_kg')
    
    # Get events for order form
    events = Event.objects.filter(is_active=True).order_by('event_name')
    
    # Get additional images
    additional_images = product.additional_images.all()
    
    context = {
        'product': product,
        'sizes': sizes,
        'events': events,
        'related_products': related_products,
        'reviews': reviews,
        'additional_images': additional_images,
    }
    
    return render(request, 'customer/product_detail.html', context)


# ===========================
# ORDERS
# ===========================

def place_order(request):
    """Place a new order"""
    if request.method == 'POST':
        # Get customer info
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', '')
        customer_address = request.POST.get('customer_address', '')
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            phone_number=customer_phone,
            defaults={
                'name': customer_name,
                'email': customer_email,
                'address': customer_address
            }
        )
        
        # Update customer info if not new
        if not created:
            customer.name = customer_name
            customer.email = customer_email
            customer.address = customer_address
            customer.save()
        
        # Get order details
        product_id = request.POST.get('product_id')
        size_id = request.POST.get('size_id')
        quantity = int(request.POST.get('quantity', 1))
        event_id = request.POST.get('event_id')
        custom_message = request.POST.get('custom_message', '')
        special_instructions = request.POST.get('special_instructions', '')
        delivery_date_str = request.POST.get('delivery_date')
        delivery_time = request.POST.get('delivery_time', '')
        
        # Convert delivery_date string to date object
        from datetime import datetime
        delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        
        # Get product and size
        product = get_object_or_404(Product, id=product_id)
        size = get_object_or_404(Size, id=size_id)
        
        # Calculate price from ProductPrice table (without flavor)
        unit_price = Decimal('0.00')
        from admin_app.models import ProductPrice
        product_price = ProductPrice.objects.filter(
            product=product,
            size=size
        ).first()
        
        if not product_price:
            messages.error(request, 'Price not available for this product and size combination. Please contact us.')
            return redirect('product_detail', product_id=product_id)
        
        unit_price = product_price.price
        
        # Create order
        order = Order.objects.create(
            customer=customer,
            product=product,
            size=size,
            quantity=quantity,
            event_id=event_id if event_id else None,
            custom_message=custom_message,
            special_instructions=special_instructions,
            delivery_date=delivery_date,
            delivery_time=delivery_time if delivery_time else None,
            unit_price=unit_price,
            status='pending'
        )
        
        # Generate WhatsApp message
        whatsapp_message = generate_order_whatsapp_message(order, customer)
        
        messages.success(request, f'Order placed successfully! Order #{order.order_number}')
        
        # Return with WhatsApp data
        context = {
            'order': order,
            'whatsapp_message': whatsapp_message,
            'customer_whatsapp': customer.phone_number,
        }
        return render(request, 'customer/order_confirmation.html', context)
    
    # GET request - show order form
    product_id = request.GET.get('product')
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id, is_active=True)
    
    products = Product.objects.filter(is_active=True).order_by('name')
    events = Event.objects.filter(is_active=True).order_by('event_name')
    
    context = {
        'products': products,
        'events': events,
        'selected_product': product,
    }
    
    return render(request, 'customer/place_order.html', context)


def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {'order': order}
    return render(request, 'customer/order_confirmation.html', context)


# def track_order(request):
#     """Track order by phone number - includes both regular and custom cake orders"""
#     context = {}
    
#     if request.method == 'POST':
#         phone_number = request.POST.get('phone_number')
        
#         if not phone_number:
#             messages.error(request, 'Please enter a phone number.')
#             return render(request, 'customer/track_order.html', context)
        
#         try:
#             # Clean up phone number (remove spaces, dashes, etc.)
#             phone_number_cleaned = ''.join(filter(str.isdigit, phone_number))
            
#             customer = Customer.objects.get(phone_number=phone_number_cleaned)
            
#             # Get both regular orders and custom cake orders
#             regular_orders = list(Order.objects.filter(customer=customer).order_by('-created_at'))
#             custom_orders = list(CustomCakeOrder.objects.filter(customer=customer).order_by('-created_at'))
            
#             # Combine and sort by creation date
#             all_orders = regular_orders + custom_orders
#             all_orders.sort(key=lambda x: x.created_at, reverse=True)
            
#             total_orders = len(regular_orders) + len(custom_orders)
            
#             context = {
#                 'customer': customer,
#                 'orders': regular_orders,
#                 'custom_orders': custom_orders,
#                 'all_orders': all_orders,
#                 'phone_number': phone_number_cleaned,
#                 'has_searched': True,
#             }
            
#             if total_orders == 0:
#                 messages.info(request, f'No orders found for this phone number. You can place a new order!')
#             else:
#                 messages.success(request, f'Found {total_orders} order(s) for {customer.name}!')
            
#             return render(request, 'customer/track_order.html', context)
#         except Customer.DoesNotExist:
#             messages.error(request, 'No customer found with this phone number.')
#             context['has_searched'] = True
#             return render(request, 'customer/track_order.html', context)
    
#     return render(request, 'customer/track_order.html', context)



def track_order(request):
    """Track order by phone number - includes both regular and custom cake orders"""
    context = {}

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')

        if not phone_number:
            messages.error(request, 'Please enter a phone number.')
            return render(request, 'customer/track_order.html', context)

        # Clean up phone number (remove spaces, dashes, etc.)
        phone_number_cleaned = ''.join(filter(str.isdigit, phone_number))

        try:
            customer = Customer.objects.get(phone_number=phone_number_cleaned)

            regular_orders = list(Order.objects.filter(customer=customer).order_by('-created_at'))
            custom_orders = list(CustomCakeOrder.objects.filter(customer=customer).order_by('-created_at'))

            # Combined and sorted list
            all_orders = regular_orders + custom_orders
            all_orders.sort(key=lambda x: x.created_at, reverse=True)

            total_orders = len(all_orders)

            context.update({
                'customer': customer,
                'orders': regular_orders,
                'custom_orders': custom_orders,
                'all_orders': all_orders,
                'phone_number': phone_number_cleaned,
                'has_searched': True,
            })

            if total_orders == 0:
                messages.info(request, 'No orders found for this phone number. You can place a new order!')
            else:
                messages.success(request, f'Found {total_orders} order(s) for {customer.name}!')

            return render(request, 'customer/track_order.html', context)

        except Customer.DoesNotExist:
            messages.error(request, 'No customer found with this phone number.')
            context['has_searched'] = True
            return render(request, 'customer/track_order.html', context)

    return render(request, 'customer/track_order.html', context)


def order_detail_customer(request, order_number):
    """View order details (customer view)"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {'order': order}
    return render(request, 'customer/order_detail.html', context)


def order_detail_customer_by_id(request, order_id):
    """View order details by ID (customer view)"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {'order': order}
    return render(request, 'customer/order_detail.html', context)

def custom_order_detail_customer(request, order_number):
    """Customer view for detailed custom cake order"""
    order = get_object_or_404(CustomCakeOrder, order_number=order_number)
    order_decorations = CustomCakeOrderDecoration.objects.filter(custom_order=order).select_related('decoration')
    reference_images = CustomCakeReferenceImage.objects.filter(custom_order=order)
    
    # Use your model's built-in breakdown property for detailed pricing
    price_breakdown = order.price_breakdown if hasattr(order, 'price_breakdown') else None
    
    context = {
        'order': order,
        'order_decorations': order_decorations,
        'reference_images': reference_images,
        'price_breakdown': price_breakdown,
    }
    return render(request, 'customer/custom_order_detail.html', context)

# ===========================
# GALLERY
# ===========================

def gallery(request):
    """Gallery page with event-based filtering"""
    # Get active events for the filter menu
    events = Event.objects.filter(is_active=True).annotate(
        image_count=Count('gallery_images')
    ).order_by('event_name')
    
    # Base queryset
    images = Gallery.objects.select_related('event_type').all()
    
    # Apply event filter if selected
    event_filter = request.GET.get('event', '')
    if event_filter:
        images = images.filter(event_type__id=event_filter)
    
    # Order images by upload date (newest first)
    images = images.order_by('-uploaded_at')
    
    context = {
        'images': images,
        'events': events,
        'selected_event': event_filter,
        'page_title': 'Gallery'
    }
    
    return render(request, 'customer/gallery.html', context)


# ===========================
# CONTACT & ENQUIRIES
# ===========================

def contact(request):
    """Contact page with enquiry form"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        message = request.POST.get('message')
        
        Enquiry.objects.create(
            name=name,
            phone=phone,
            email=email,
            message=message
        )
        
        messages.success(request, 'Thank you for your enquiry! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'customer/contact.html')


# ===========================
# REVIEWS
# ===========================

def submit_review(request):
    """Submit a review"""
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        product_id = request.POST.get('product_id')
        
        Review.objects.create(
            customer_name=customer_name,
            rating=rating,
            comment=comment,
            product_id=product_id if product_id else None,
            is_approved=False  # Requires admin approval
        )
        
        messages.success(request, 'Thank you for your review! It will be published after moderation.')
        return redirect('home')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    context = {'products': products}
    return render(request, 'customer/submit_review.html', context)


# ===========================
# ABOUT PAGE
# ===========================

def search(request):
    """Simple search functionality - redirects to products page with search parameter"""
    if request.method == 'POST':
        search_query = request.POST.get('search', '').strip()
        if search_query:
            return redirect(f"{reverse('products')}?search={search_query}")
    return redirect('products')


def about(request):
    """About us page"""
    # Get some statistics
    total_orders = Order.objects.filter(status='completed').count()
    happy_customers = Customer.objects.count()
    
    context = {
        'total_orders': total_orders,
        'happy_customers': happy_customers,
    }
    
    return render(request, 'customer/about-us.html', context)


# ===========================
# SIMPLE CUSTOMER AUTH (SESSION-BASED)
# ===========================

def login_view(request):
    """Two-step customer login using phone + email OTP verification."""
    context = {}
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        stage = request.POST.get('stage')
        
        if not phone:
            messages.error(request, 'Phone number is required.')
            return redirect('customer_login')
            
        if stage == 'request_otp':
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, 'Email is required for OTP verification.')
                return redirect('customer_login')
                
            # Generate and send OTP
            otp = utils.generate_otp()
            if utils.send_otp_email(email, otp):
                utils.store_otp(phone, email, otp)
                context.update({
                    'show_otp_form': True,
                    'phone': phone,
                    'email': email
                })
                messages.success(request, 'OTP has been sent to your email.')
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
                context.update({'phone': phone, 'email': email})
                
        elif stage == 'verify_otp':
            entered_otp = request.POST.get('otp', '').strip()
            email = request.POST.get('email', '').strip()
            
            if not entered_otp:
                messages.error(request, 'Please enter the OTP.')
                context.update({
                    'show_otp_form': True,
                    'phone': phone,
                    'email': email
                })
            else:
                is_valid, stored_email = utils.verify_otp(phone, entered_otp)
                
                if is_valid and stored_email == email:
                    # Create/update customer with verified email
                    customer, created = Customer.objects.get_or_create(
                        phone_number=phone,
                        defaults={
                            'name': phone,
                            'email': email
                        }
                    )
                    
                    if not created and not customer.email:
                        customer.email = email
                        customer.save()
                    
                    # Set session
                    request.session['customer_phone'] = customer.phone_number
                    # Cache customer name in session to avoid DB lookup on every request
                    request.session['customer_name'] = customer.name
                    request.session.modified = True
                    messages.success(request, f'Welcome, {customer.name}!')
                    
                    # Handle redirect
                    next_url = request.POST.get('next') or request.GET.get('next') or 'home'
                    return redirect(next_url)
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
                    context.update({
                        'show_otp_form': True,
                        'phone': phone,
                        'email': email
                    })

    # Either initial GET or form submission with context for re-rendering
    return render(request, 'customer/login.html', context)


def logout_view(request):
    """Clear customer session; does not affect Django admin auth."""
    request.session.pop('customer_phone', None)
    request.session.pop('customer_name', None)
    request.session.modified = True
    messages.success(request, 'You have been logged out.')
    return redirect('home')


# ===========================
# ADMIN AUTH (USERNAME/PASSWORD)
# ===========================

def admin_login_view(request):
    """Custom admin login that authenticates against Django auth User table.
    Only staff/superusers are allowed to proceed.
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            auth_login(request, user)
            next_url = request.GET.get('next') or '/admin/'
            return redirect(next_url)
        messages.error(request, 'Invalid credentials or no admin access.')
        return redirect('admin_login')

    return render(request, 'admin/admin_login.html')


def admin_logout_view(request):
    """Log out the Django admin user session."""
    auth_logout(request)
    messages.success(request, 'Admin logged out.')
    return redirect('admin_login')


# ===========================
# ERROR HANDLERS
# ===========================

def custom_404(request, exception):
    """
    Custom 404 error handler.
    Returns a customized 404 page when a page is not found.
    """
    # Get the current URL for display
    current_path = request.path
    
    # Add context that may be helpful for the error page
    context = {
        'page_title': 'Page Not Found',
        'current_path': current_path,
        'error_code': 404,
        'error_message': 'The page you are looking for could not be found.',
        'suggestion': 'You may have mistyped the address or the page may have moved.',
        'back_url': request.META.get('HTTP_REFERER', '/'),
    }
    return render(request, 'errors/404.html', context, status=404)


def custom_500(request):
    """
    Custom 500 error handler.
    Returns a customized 500 page when a server error occurs.
    """
    # Add context with error details
    context = {
        'page_title': 'Server Error',
        'error_code': 500,
        'error_message': 'Sorry, something went wrong on our end.',
        'suggestion': 'Please try again later or contact our support team if the problem persists.',
        'back_url': request.META.get('HTTP_REFERER', '/'),
    }
    return render(request, 'errors/500.html', context, status=500)


# ===========================
# AJAX APIs FOR CUSTOMER
# ===========================

def get_product_details_ajax(request):
    """Get product details including sizes, flavors (AJAX)"""
    product_id = request.GET.get('product_id')
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Get sizes with their ordering
        sizes = list(product.sizes.filter(is_active=True).order_by('display_order', 'weight_in_kg').values(
            'id', 'name', 'weight_in_kg'
        ))
        
        data = {
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'image': product.main_image.url if product.main_image else None,
            },
            'sizes': sizes,
        }
        
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})


def get_event_suggestions_ajax(request):
    """Get suggestions for an event (AJAX)"""
    event_id = request.GET.get('event_id')
    
    suggestions = EventSuggestion.objects.filter(
        event_id=event_id
    ).values('id', 'suggested_item', 'note')
    
    return JsonResponse({
        'success': True,
        'suggestions': list(suggestions)
    })


def calculate_price_ajax(request):
    """Calculate order price (AJAX) - product + size only"""
    product_id = request.GET.get('product_id')
    size_id = request.GET.get('size_id')
    quantity = int(request.GET.get('quantity', 1))
    
    try:
        if not product_id or not size_id:
            return JsonResponse({
                'success': False,
                'error': 'Please select product and size'
            })
        
        from admin_app.models import ProductPrice
        
        product = Product.objects.get(id=product_id, is_active=True)
        size = Size.objects.get(id=size_id, is_active=True)
        
        # Get price from ProductPrice table (without flavor)
        # Use .first() instead of .get() to handle potential duplicates
        product_price = ProductPrice.objects.filter(
            product=product,
            size=size
        ).first()
        
        if not product_price:
            return JsonResponse({
                'success': False,
                'error': 'Price not available for this combination. Please contact us.'
            })
        
        unit_price = float(product_price.price)
        total_price = unit_price * quantity
        
        return JsonResponse({
            'success': True,
            'unit_price': unit_price,
            'total_price': total_price,
            'size_name': size.name,
        })
            
    except (Product.DoesNotExist, Size.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid selection'})
    except ProductPrice.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Price not available for this combination. Please contact us.'
        })


# ===========================
# CUSTOM CAKES
# ===========================

def custom_cakes(request):
    """Custom cakes page - display options and take orders"""
    shapes = CakeShape.objects.filter(is_active=True).order_by('display_order', 'name')
    tiers = CakeTier.objects.filter(is_active=True).order_by('display_order', 'tiers_count')
    decorations = Decoration.objects.filter(is_active=True).order_by('category', 'display_order', 'name')
    flavors = Flavor.objects.filter(is_active=True).order_by('display_order', 'name')
    events = Event.objects.filter(is_active=True).order_by('event_name')
    products = Product.objects.filter(is_active=True, category__is_cake=True).order_by('name')
    
    # Group decorations by category
    decorations_by_category = {}
    for decoration in decorations:
        category = decoration.get_category_display()
        if category not in decorations_by_category:
            decorations_by_category[category] = []
        decorations_by_category[category].append(decoration)
    
    context = {
        'shapes': shapes,
        'tiers': tiers,
        'decorations': decorations,
        'decorations_by_category': decorations_by_category,
        'flavors': flavors,
        'events': events,
        'products': products,
    }
    
    return render(request, 'customer/custom_cakes.html', context)


def place_custom_order(request):
    """Place a custom cake order"""
    if request.method == 'POST':
        # Get customer info
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        customer_email = request.POST.get('customer_email', '')
        customer_address = request.POST.get('delivery_address')
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            phone_number=customer_phone,
            defaults={
                'name': customer_name,
                'email': customer_email,
                'address': customer_address
            }
        )
        
        # Update customer info if not new
        if not created:
            customer.name = customer_name
            customer.email = customer_email if customer_email else customer.email
            customer.save()
        
        # Get order details
        shape_id = request.POST.get('shape_id')
        tier_id = request.POST.get('tier_id')
        total_weight = request.POST.get('total_weight')
        
        # Get product/size (if customer selected existing product)
        product_id = request.POST.get('product_id')
        size_id = request.POST.get('size_id')
        
        # Get flavor (either from dropdown or custom text)
        flavor_id = request.POST.get('flavor_id')
        flavor_description = request.POST.get('flavor_description', '')
        
        # Get decorations with quantities
        # Format: decoration_ids[] and decoration_quantities[]
        decoration_ids = request.POST.getlist('decoration_ids')
        decoration_quantities = request.POST.getlist('decoration_quantities')
        
        reference_images = request.FILES.getlist('reference_images')  # Multiple images
        
        # Convert total_weight to Decimal
        from decimal import Decimal
        total_weight = Decimal(total_weight) if total_weight else Decimal('1.0')
        event_id = request.POST.get('event_id')
        custom_message = request.POST.get('custom_message', '')
        special_instructions = request.POST.get('special_instructions', '')
        delivery_date = request.POST.get('delivery_date')
        delivery_time = request.POST.get('delivery_time', '')
        
        # Convert delivery_date string to date object
        from datetime import datetime
        if delivery_date and delivery_date.strip():  # Check if not empty or just whitespace
            try:
                delivery_date = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            except ValueError:
                # If date format is different, try alternative formats
                try:
                    delivery_date = datetime.strptime(delivery_date, '%d/%m/%Y').date()
                except ValueError:
                    delivery_date = datetime.strptime(delivery_date, '%m/%d/%Y').date()
        else:
            # If no delivery date provided, this should be an error
            messages.error(request, 'Delivery date is required.')
            return redirect('custom_cakes')
        
        # Convert delivery_time string to time object if provided
        if delivery_time and delivery_time.strip():  # Check if not empty or just whitespace
            try:
                delivery_time = datetime.strptime(delivery_time, '%H:%M').time()
            except ValueError:
                # If time format is different, try alternative formats
                try:
                    delivery_time = datetime.strptime(delivery_time, '%I:%M %p').time()
                except ValueError:
                    delivery_time = None
        else:
            delivery_time = None  # Set to None if empty or just whitespace
        
        # Create custom order
        custom_order = CustomCakeOrder.objects.create(
            customer=customer,
            product_id=product_id if product_id else None,
            size_id=size_id if size_id else None,
            shape_id=shape_id,
            tier_id=tier_id,
            total_weight=total_weight,
            flavor_id=flavor_id if flavor_id else None,
            flavor_description=flavor_description,
            event_id=event_id if event_id else None,
            custom_message=custom_message,
            special_instructions=special_instructions,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            delivery_address=customer_address,
            estimated_price=0  # Will be calculated automatically
        )
        
        # Add decorations with quantities
        if decoration_ids and decoration_quantities:
            for dec_id, quantity_str in zip(decoration_ids, decoration_quantities):
                try:
                    quantity = int(quantity_str) if quantity_str else 1
                    if quantity > 0:  # Only add if quantity is positive
                        CustomCakeOrderDecoration.objects.create(
                            custom_order=custom_order,
                            decoration_id=dec_id,
                            quantity=quantity
                        )
                except (ValueError, TypeError):
                    # Skip invalid quantities
                    continue
        
        # Handle reference images
        from admin_app.models import CustomCakeReferenceImage
        for image in reference_images:
            if image.size <= 5 * 1024 * 1024:  # 5MB limit
                CustomCakeReferenceImage.objects.create(
                    custom_order=custom_order,
                    image=image
                )
        
        # Recalculate estimate after adding decorations
        custom_order.update_estimate()
        
        # Generate WhatsApp message
        whatsapp_message = generate_custom_cake_whatsapp_message(custom_order, customer)
        
        # Auto-send WhatsApp message (opens WhatsApp with pre-filled message)
        whatsapp_data = auto_send_whatsapp_message(custom_order, customer, whatsapp_message)
        
        messages.success(request, f'Custom cake order placed successfully! Order #{custom_order.order_number}')
        
        # Return with WhatsApp data
        context = {
            'order': custom_order,
            'whatsapp_message': whatsapp_message,
            'customer_whatsapp': customer.phone_number,
            'auto_sent': True,  # Flag to indicate WhatsApp was auto-sent
            'whatsapp_data': whatsapp_data,  # Additional WhatsApp data
        }
        return render(request, 'customer/custom_order_confirmation.html', context)
    
    return redirect('custom_cakes')


def custom_order_confirmation(request, order_number):
    """Custom order confirmation page"""
    order = get_object_or_404(CustomCakeOrder, order_number=order_number)
    
    context = {'order': order}
    return render(request, 'customer/custom_order_confirmation.html', context)


# ===========================
# PDF GENERATION VIEWS
# ===========================

def generate_order_pdf(request, order_number):
    """Generate professional invoice PDF for regular product order"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Create PDF with watermark
    buffer = BytesIO()
    from reportlab.platypus import PageTemplate, Frame
    from reportlab.lib.pagesizes import A4
    
    def add_watermark(canvas, doc):
        """Add watermark (no borders for clean look)"""
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setFillColor(colors.HexColor('#FFF3F8'))
        canvas.setFillAlpha(0.2)
        canvas.translate(A4[0]/2, A4[1]/2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "CAKES BY DESTI")
        canvas.rotate(-45)
        canvas.translate(-A4[0]/2, -A4[1]/2)
        canvas.restoreState()
    
    frame = Frame(0.75*inch, 0.75*inch, A4[0]-1.5*inch, A4[1]-1.5*inch, id='normal')
    template = PageTemplate(id='invoice', frames=frame, onPage=add_watermark)
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    doc.addPageTemplates([template])
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Styles
    from_content_style = ParagraphStyle(
        'FromContent',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=14
    )
    
    # Dark blue header with INVOICE
    header_data = [[
        Paragraph("<b style='color: white; font-size: 12pt'>🎂 CAKES BY DESTI & SIMI</b><br/>"
                 "<font size='8' color='white'>Made by our family for your family</font>", from_content_style),
        Paragraph("<b style='color: white; font-size: 32pt'>INVOICE</b>", from_content_style)
    ]]
    
    header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A5490')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # Client Info and Invoice Details
    info_data = [[
        Paragraph(f"<b>Client Name:</b> {order.customer.name}<br/>"
                 f"<b>Invoice#:</b> {order.order_number}<br/>"
                 f"<b>Date:</b> {order.created_at.strftime('%m/%d/%Y')}", from_content_style),
        Paragraph(f"<b>Client Address</b><br/>"
                 f"{order.customer.address or 'N/A'}<br/>"
                 f"Ph: {order.customer.phone_number}<br/>"
                 f"Email: {order.customer.email or 'N/A'}", from_content_style)
    ]]
    
    info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # Items Table
    product_description = f"{order.product.name} - {order.size.name}"
    if order.custom_message:
        product_description += f"<br/>Message: {order.custom_message}"
    if order.event:
        product_description += f"<br/>Event: {order.event.event_name}"
    
    items_data = [
        ['SL.', 'Item Description', 'Price', 'Qty', 'Total']
    ]
    
    items_data.append([
        '1',
        Paragraph(product_description, from_content_style),
        f'₹{order.unit_price:,.0f}',
        str(order.quantity),
        f'₹{order.total_price:,.0f}'
    ])
    
    # Add empty rows for clean look
    for i in range(4):
        items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 0.6*inch, 0.9*inch])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        
        # Data rows
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5))
    
    # Summary Section (aligned right)
    summary_data = [
        ['', '', '', 'Sub Total:', f'₹{order.total_price:,.0f}'],
        ['', '', '', 'Total:', f'₹{order.total_price:,.0f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[0.5*inch, 3.5*inch, 1*inch, 0.6*inch, 0.9*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONT', (3, 0), (3, 0), 'Helvetica', 10),
        ('FONT', (4, 0), (4, 0), 'Helvetica', 10),
        ('FONT', (3, 1), (-1, 1), 'Helvetica-Bold', 12),
        ('BACKGROUND', (3, 1), (-1, 1), colors.HexColor('#E8F5E9')),
        ('TEXTCOLOR', (3, 1), (-1, 1), colors.HexColor('#4CAF50')),
        ('PADDING', (3, 0), (-1, -1), 8),
        ('LINEABOVE', (3, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),
        ('LINEABOVE', (3, 1), (-1, 1), 2, colors.HexColor('#4CAF50')),
        ('TOPPADDING', (3, 1), (-1, 1), 12),
        ('BOTTOMPADDING', (3, 1), (-1, 1), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 25))
    
    # Additional notes if any
    if order.special_instructions:
        note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, 
                                    textColor=colors.HexColor('#666666'), leading=12)
        elements.append(Paragraph(f"<b>Special Instructions:</b><br/>{order.special_instructions}", note_style))
        elements.append(Spacer(1, 15))
    
    # Terms and Conditions
    terms_heading_style = ParagraphStyle('TermsHeading', parent=styles['Normal'], fontSize=11,
                                        textColor=colors.HexColor('#1A5490'), fontName='Helvetica-Bold',
                                        spaceAfter=8)
    terms_style = ParagraphStyle('Terms', parent=styles['Normal'], fontSize=9,
                                 textColor=colors.HexColor('#333333'), leading=13, spaceAfter=3)
    
    elements.append(Paragraph("Terms & Conditions", terms_heading_style))
    elements.append(Paragraph("Payment is due on delivery", terms_style))
    elements.append(Paragraph("Delivery date and time must be confirmed 24 hours in advance", terms_style))
    elements.append(Paragraph("Thank you for your business!", terms_style))
    elements.append(Spacer(1, 15))
    
    # Simple Footer
    footer_data = [[
        'Tel: +91 9946588352',
        'Email: cakesbydesti@example.com',
        'Web: www.cakesbydesti.com'
    ]]
    
    footer_table = Table(footer_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
    footer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Order_{order.order_number}.pdf"'
    
    return response


def generate_custom_cake_pdf(request, order_number):
    """Generate PDF for custom cake order with enhanced styling and watermark"""
    order = get_object_or_404(CustomCakeOrder, order_number=order_number)
    
    # Create PDF with custom page template for watermark
    buffer = BytesIO()
    
    # Custom page template class for watermark
    from reportlab.platypus import PageTemplate, Frame
    from reportlab.lib.pagesizes import A4
    
    def add_watermark(canvas, doc):
        """Add watermark (no borders for clean look)"""
        canvas.saveState()
        
        # Add watermark text in center
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setFillColor(colors.HexColor('#FFF3F8'))
        canvas.setFillAlpha(0.2)
        canvas.translate(A4[0]/2, A4[1]/2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "CAKES BY DESTI")
        canvas.rotate(-45)
        canvas.translate(-A4[0]/2, -A4[1]/2)
        
        canvas.restoreState()
    
    # Build document with custom page template
    frame = Frame(0.75*inch, 0.75*inch, A4[0]-1.5*inch, A4[1]-1.5*inch, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=add_watermark)
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    doc.addPageTemplates([template])
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Enhanced custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#FF1493'),
        spaceAfter=5,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=38
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#C06C84'),
        spaceAfter=5,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=25,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=colors.HexColor('#FF6B9D'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#FF6B9D'),
        borderWidth=0,
        borderPadding=5
    )
    
    # Styles
    from_content_style = ParagraphStyle(
        'FromContent',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leading=14
    )
    
    # Dark blue header with ESTIMATE
    header_data = [[
        Paragraph("<b style='color: white; font-size: 12pt'>🎂 CAKES BY DESTI & SIMI</b><br/>"
                 "<font size='8' color='white'>Made by our family for your family</font>", from_content_style),
        Paragraph("<b style='color: white; font-size: 32pt'>ESTIMATE</b>", from_content_style)
    ]]
    
    header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A5490')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    
    # Client Info and Estimate Details
    info_data = [[
        Paragraph(f"<b>Client Name:</b> {order.customer.name}<br/>"
                 f"<b>Estimate#:</b> {order.order_number}<br/>"
                 f"<b>Date:</b> {order.created_at.strftime('%m/%d/%Y')}", from_content_style),
        Paragraph(f"<b>Client Address</b><br/>"
                 f"{order.delivery_address[:80]}<br/>"
                 f"Ph: {order.customer.phone_number}<br/>"
                 f"Email: {order.customer.email or 'N/A'}", from_content_style)
    ]]
    
    info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # Items Table (Like the template)
    # Get flavor name
    flavor_name = order.flavor.name if order.flavor else (order.flavor_description or 'Not specified')
    
    # Get decorations
    order_decorations = order.order_decorations.all()
    decorations_text = ', '.join([f"{od.quantity}× {od.decoration.name}" for od in order_decorations]) if order_decorations else 'None'
    
    # Build description
    cake_description = f"Custom Cake - {order.shape.name}, {order.tier.name}, {order.total_weight}kg, {flavor_name}"
    if decorations_text != 'None':
        cake_description += f"<br/>Decorations: {decorations_text}"
    if order.custom_message:
        cake_description += f"<br/>Message: {order.custom_message}"
    
    # Create items table with header
    items_data = [
        ['QTY', 'Description', 'Unit Price', 'Amount']
    ]
    
    # Add cake item
    items_data.append([
        '1',
        Paragraph(cake_description, from_content_style),
        f'₹{order.price_range["min"]:,}',
        f'₹{order.price_range["min"]:,}'
    ])
    
    # Add a few empty rows for clean look
    for i in range(2):
        items_data.append(['', '', '', ''])
    
    items_table = Table(items_data, colWidths=[0.7*inch, 3.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        # Header row styling - Dark blue
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (-1, 0), 'CENTER'),
        
        # Data rows styling
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Grid and padding
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5))
    
    # Subtotal and Total Section (aligned to right like template)
    price_range = order.price_range
    summary_data = [
        ['', '', 'Subtotal', f'₹{price_range["min"]:,}'],
        ['', '', 'Price Range', f'₹{price_range["min"]:,} - ₹{price_range["max"]:,}'],
        ['', '', Paragraph('<b>Total (Estimated)</b>', from_content_style), 
         Paragraph(f'<b>₹{price_range["max"]:,}</b>', from_content_style)],
    ]
    
    summary_table = Table(summary_data, colWidths=[0.7*inch, 3.8*inch, 1*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONT', (2, 0), (2, 1), 'Helvetica', 10),
        ('FONT', (3, 0), (3, 1), 'Helvetica', 10),
        ('FONT', (2, 2), (-1, 2), 'Helvetica-Bold', 12),
        ('BACKGROUND', (2, 2), (-1, 2), colors.HexColor('#E8F5E9')),
        ('TEXTCOLOR', (2, 2), (-1, 2), colors.HexColor('#4CAF50')),
        ('PADDING', (2, 0), (-1, -1), 8),
        ('LINEABOVE', (2, 0), (-1, 0), 1, colors.HexColor('#CCCCCC')),
        ('LINEABOVE', (2, 2), (-1, 2), 2, colors.HexColor('#4CAF50')),
        ('TOPPADDING', (2, 2), (-1, 2), 12),
        ('BOTTOMPADDING', (2, 2), (-1, 2), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Final Price (if different)
    if order.final_price and order.final_price != order.estimated_price:
        final_data = [['FINAL PRICE:', f'₹{order.final_price:,.2f}']]
        final_table = Table(final_data, colWidths=[5*inch, 1.5*inch])
        final_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
            ('FONT', (0, 0), (0, 0), 'Helvetica-Bold', 14),
            ('FONT', (1, 0), (1, 0), 'Helvetica-Bold', 16),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#4CAF50')),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#4CAF50')),
        ]))
        elements.append(final_table)
        
        if order.price_note:
            note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#666666'), alignment=TA_LEFT)
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(f"<i>Note: {order.price_note}</i>", note_style))
    
    elements.append(Spacer(1, 20))
    
    # Additional Information
    if order.custom_message or order.special_instructions:
        elements.append(Paragraph("Additional Information", heading_style))
        
        info_data = []
        if order.custom_message:
            info_data.append(['Message on Cake:', order.custom_message])
        if order.special_instructions:
            info_data.append(['Special Instructions:', order.special_instructions])
        
        info_table = Table(info_data, colWidths=[2*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF9E6')),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FFE5A3')),
        ]))
        elements.append(info_table)
    
    elements.append(Spacer(1, 30))
    
    # Terms and Conditions Section
    terms_heading_style = ParagraphStyle(
        'TermsHeading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1A5490'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    
    terms_style = ParagraphStyle(
        'Terms',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        leading=13,
        spaceAfter=3
    )
    
    elements.append(Paragraph("Terms & Conditions", terms_heading_style))
    elements.append(Paragraph("This is an estimated quotation. Final price will be confirmed after design discussion.", terms_style))
    elements.append(Paragraph("50% advance payment required to confirm the order.", terms_style))
    elements.append(Paragraph("Balance payment to be made at the time of delivery.", terms_style))
    elements.append(Paragraph("Thank you for your business!", terms_style))
    elements.append(Spacer(1, 15))
    
    # Simple Footer (like template)
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=0
    )
    
    # Create footer table with 3 columns
    footer_data = [[
        'Tel: +91 9946588352',
        'Email: cakesbydesti@example.com',
        'Web: www.cakesbydesti.com'
    ]]
    
    footer_table = Table(footer_data, colWidths=[2.2*inch, 2.2*inch, 2.1*inch])
    footer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="CustomCake_{order.order_number}.pdf"'
    
    return response


# ===========================
# AJAX API ENDPOINTS
# ===========================

def get_product_sizes_prices(request):
    """Get sizes and prices for a product (AJAX)"""
    product_id = request.GET.get('product_id')
    
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
    # Get sizes with their custom prices from ProductPrice table
    sizes_data = []
    for size in product.sizes.filter(is_active=True).order_by('display_order'):
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


# ===========================
# GIFT BOXES (Customer Side)
# ===========================

def gift_boxes(request):
    """Display all gift boxes"""
    gift_boxes = GiftBox.objects.filter(is_active=True).prefetch_related('items__product', 'items__size')
    
    context = {
        'gift_boxes': gift_boxes,
        'page_title': 'Gift Boxes'
    }
    return render(request, 'customer/gift_boxes.html', context)


def gift_box_detail(request, gift_box_id):
    """Display gift box details"""
    gift_box = get_object_or_404(GiftBox, id=gift_box_id, is_active=True)
    items = gift_box.items.all().select_related('product', 'size')
    
    context = {
        'gift_box': gift_box,
        'items': items,
        'page_title': gift_box.name
    }
    return render(request, 'customer/gift_box_detail.html', context)


def gift_box_order(request, gift_box_id):
    """Place order for a gift box"""
    gift_box = get_object_or_404(GiftBox, id=gift_box_id, is_active=True)
    events = Event.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Get customer info
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        whatsapp_number = request.POST.get('whatsapp_number', phone_number)
        email = request.POST.get('email')
        
        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'name': customer_name,
                'whatsapp_number': whatsapp_number,
                'email': email
            }
        )
        
        # Get order details
        quantity = int(request.POST.get('quantity', 1))
        event_id = request.POST.get('event')
        delivery_date = request.POST.get('delivery_date')
        delivery_time = request.POST.get('delivery_time')
        special_instructions = request.POST.get('special_instructions', '')
        
        event = None
        if event_id:
            event = Event.objects.get(id=event_id)
        
        # Create order
        order = GiftBoxOrder.objects.create(
            customer=customer,
            gift_box=gift_box,
            quantity=quantity,
            event=event,
            delivery_date=delivery_date,
            delivery_time=delivery_time or None,
            special_instructions=special_instructions,
            unit_price=gift_box.total_price
        )
        
        messages.success(request, f'Gift Box order #{order.order_number} placed successfully!')
        return redirect('gift_box_order_confirmation', order_number=order.order_number)
    
    context = {
        'gift_box': gift_box,
        'events': events,
        'page_title': f'Order {gift_box.name}'
    }
    return render(request, 'customer/gift_box_order.html', context)


def gift_box_order_confirmation(request, order_number):
    """Gift box order confirmation page"""
    order = get_object_or_404(GiftBoxOrder, order_number=order_number)
    items = order.gift_box.items.all().select_related('product', 'size')
    
    context = {
        'order': order,
        'items': items,
        'page_title': 'Order Confirmation'
    }
    return render(request, 'customer/gift_box_order_confirmation.html', context)


# ===========================
# LOYALTY & REWARDS
# ===========================

def loyalty_dashboard(request):
    """Main loyalty dashboard showing stamps, points, tier, and rewards"""
    # Get or create customer (for demo, using phone number from session)
    phone = request.session.get('customer_phone')
    
    if not phone:
        # For now, redirect to home with message
        messages.info(request, 'Please place an order first to access loyalty rewards!')
        return redirect('home')
    
    try:
        customer = Customer.objects.get(phone_number=phone)
        loyalty_card, created = LoyaltyCard.objects.get_or_create(customer=customer)
        
        # Get active rewards
        active_rewards = LoyaltyReward.objects.filter(
            loyalty_card=loyalty_card,
            status='active'
        ).order_by('expiry_date')
        
        # Get recent points transactions
        recent_transactions = PointsTransaction.objects.filter(
            loyalty_card=loyalty_card
        ).order_by('-created_at')[:10]
        
        # Get unlocked achievements
        achievements = CustomerAchievement.objects.filter(
            loyalty_card=loyalty_card
        ).select_related('achievement').order_by('-unlocked_at')[:6]
        
        # Calculate progress to next tier
        current_orders = loyalty_card.total_orders
        if current_orders < 10:
            next_tier = 'Silver'
            orders_needed = 10 - current_orders
            progress_percentage = int((current_orders / 10) * 100)
        elif current_orders < 25:
            next_tier = 'Gold'
            orders_needed = 25 - current_orders
            progress_percentage = int(((current_orders - 10) / 15) * 100)
        elif current_orders < 50:
            next_tier = 'Platinum'
            orders_needed = 50 - current_orders
            progress_percentage = int(((current_orders - 25) / 25) * 100)
        else:
            next_tier = None
            orders_needed = 0
            progress_percentage = 100
        
        context = {
            'customer': customer,
            'loyalty_card': loyalty_card,
            'active_rewards': active_rewards,
            'recent_transactions': recent_transactions,
            'achievements': achievements,
            'next_tier': next_tier,
            'orders_needed': orders_needed,
            'tier_progress': progress_percentage,
            'page_title': 'My Loyalty Rewards'
        }
        
        return render(request, 'customer/loyalty_dashboard.html', context)
        
    except Customer.DoesNotExist:
        messages.error(request, 'Customer not found. Please place an order first.')
        return redirect('home')


def my_rewards(request):
    """View all rewards (active, used, expired)"""
    phone = request.session.get('customer_phone')
    
    if not phone:
        messages.info(request, 'Please place an order first to access loyalty rewards!')
        return redirect('home')
    
    try:
        customer = Customer.objects.get(phone_number=phone)
        loyalty_card = customer.loyalty_card
        
        # Get all rewards
        active_rewards = LoyaltyReward.objects.filter(
            loyalty_card=loyalty_card,
            status='active'
        ).order_by('expiry_date')
        
        used_rewards = LoyaltyReward.objects.filter(
            loyalty_card=loyalty_card,
            status='used'
        ).order_by('-used_date')
        
        expired_rewards = LoyaltyReward.objects.filter(
            loyalty_card=loyalty_card,
            status='expired'
        ).order_by('-expiry_date')
        
        context = {
            'customer': customer,
            'loyalty_card': loyalty_card,
            'active_rewards': active_rewards,
            'used_rewards': used_rewards,
            'expired_rewards': expired_rewards,
            'page_title': 'My Rewards'
        }
        
        return render(request, 'customer/my_rewards.html', context)
        
    except (Customer.DoesNotExist, LoyaltyCard.DoesNotExist):
        messages.error(request, 'Loyalty card not found.')
        return redirect('home')


def referral_program(request):
    """Referral program page with unique code and referral history"""
    phone = request.session.get('customer_phone')
    
    if not phone:
        messages.info(request, 'Please place an order first to access referral program!')
        return redirect('home')
    
    try:
        customer = Customer.objects.get(phone_number=phone)
        loyalty_card = customer.loyalty_card
        
        # Get all referrals made by this customer
        referrals = Referral.objects.filter(referrer=customer).order_by('-created_at')
        
        # Count successful referrals
        successful_referrals = referrals.filter(status='completed').count()
        pending_referrals = referrals.filter(status='pending').count()
        
        # Calculate potential points from pending referrals
        potential_points = pending_referrals * 100
        
        context = {
            'customer': customer,
            'loyalty_card': loyalty_card,
            'referrals': referrals,
            'successful_referrals': successful_referrals,
            'pending_referrals': pending_referrals,
            'potential_points': potential_points,
            'page_title': 'Referral Program'
        }
        
        return render(request, 'customer/referral_program.html', context)
        
    except (Customer.DoesNotExist, LoyaltyCard.DoesNotExist):
        messages.error(request, 'Customer not found.')
        return redirect('home')


def create_referral(request):
    """Create a new referral"""
    if request.method == 'POST':
        phone = request.session.get('customer_phone')
        
        if not phone:
            messages.error(request, 'Please login first.')
            return redirect('home')
        
        try:
            customer = Customer.objects.get(phone_number=phone)
            
            referred_name = request.POST.get('referred_name')
            referred_phone = request.POST.get('referred_phone')
            
            # Create referral
            referral = Referral.objects.create(
                referrer=customer,
                referred_name=referred_name,
                referred_phone=referred_phone
            )
            
            messages.success(request, f'Referral created! Share code: {referral.referral_code}')
            return redirect('referral_program')
            
        except Customer.DoesNotExist:
            messages.error(request, 'Customer not found.')
            return redirect('home')
    
    return redirect('referral_program')


# ===========================
# LOYALTY HELPERS & HISTORY/SELECTION ENDPOINTS
# ===========================

def _get_current_customer(request):
    """Get current customer using session phone."""
    phone = request.session.get('customer_phone')
    if not phone:
        return None
    try:
        return Customer.objects.get(phone_number=phone)
    except Customer.DoesNotExist:
        return None


def _calculate_max_points_redeemable(amount_after_voucher: Decimal, points_balance: int) -> int:
    """Cap points to integer rupees available and points balance."""
    if amount_after_voucher <= 0:
        return 0
    try:
        remaining_rupees = int(Decimal(amount_after_voucher).quantize(Decimal('1'), rounding='ROUND_FLOOR'))
    except Exception:
        remaining_rupees = 0
    return max(0, min(points_balance, remaining_rupees))


def loyalty_history(request):
    """Customer loyalty history across orders, rewards, points, achievements."""
    customer = _get_current_customer(request)
    if not customer:
        messages.info(request, 'Please place an order first to access loyalty history!')
        return redirect('home')
    try:
        loyalty_card = customer.loyalty_card
    except LoyaltyCard.DoesNotExist:
        messages.info(request, 'No loyalty activity yet.')
        return redirect('loyalty_dashboard')

    # Orders (latest first)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')

    # Rewards
    rewards_active = LoyaltyReward.objects.filter(loyalty_card=loyalty_card, status='active').order_by('expiry_date')
    rewards_used = LoyaltyReward.objects.filter(loyalty_card=loyalty_card, status='used').order_by('-used_date')
    rewards_expired = LoyaltyReward.objects.filter(loyalty_card=loyalty_card, status='expired').order_by('-expiry_date')

    # Points
    transactions = PointsTransaction.objects.filter(loyalty_card=loyalty_card).order_by('-created_at')

    # Achievements
    unlocked = CustomerAchievement.objects.filter(loyalty_card=loyalty_card).select_related('achievement').order_by('-unlocked_at')

    context = {
        'customer': customer,
        'loyalty_card': loyalty_card,
        'orders': orders,
        'rewards_active': rewards_active,
        'rewards_used': rewards_used,
        'rewards_expired': rewards_expired,
        'transactions': transactions,
        'achievements_unlocked': unlocked,
        'page_title': 'Loyalty History'
    }
    return render(request, 'customer/loyalty_history.html', context)


def set_points_redemption(request):
    """Stage points redemption amount in session prior to checkout."""
    if request.method != 'POST':
        return redirect('loyalty_dashboard')
    customer = _get_current_customer(request)
    if not customer:
        messages.error(request, 'Please login or place an order first.')
        return redirect('home')
    try:
        loyalty_card = customer.loyalty_card
    except LoyaltyCard.DoesNotExist:
        messages.error(request, 'No loyalty card found.')
        return redirect('loyalty_dashboard')

    try:
        points_requested = int(request.POST.get('points', '0'))
    except ValueError:
        points_requested = 0

    # Cap to points balance (final cap relative to payable will be done at checkout)
    points_to_stage = max(0, min(points_requested, int(loyalty_card.points_balance)))
    request.session['pending_points_redeem'] = points_to_stage
    request.session.modified = True

    if points_to_stage > 0:
        messages.success(request, f'{points_to_stage} points will be redeemed at checkout.')
    else:
        messages.info(request, 'No points selected for redemption.')
    return redirect('loyalty_dashboard')


def set_reward_selection(request):
    """Stage a selected active reward in session prior to checkout."""
    if request.method != 'POST':
        return redirect('loyalty_dashboard')
    customer = _get_current_customer(request)
    if not customer:
        messages.error(request, 'Please login or place an order first.')
        return redirect('home')
    try:
        loyalty_card = customer.loyalty_card
    except LoyaltyCard.DoesNotExist:
        messages.error(request, 'No loyalty card found.')
        return redirect('loyalty_dashboard')

    reward_id = request.POST.get('reward_id')
    if not reward_id:
        messages.error(request, 'Please select a reward to apply.')
        return redirect('loyalty_dashboard')

    reward = LoyaltyReward.objects.filter(id=reward_id, loyalty_card=loyalty_card, status='active').first()
    if not reward or not reward.is_valid():
        messages.error(request, 'Selected reward is not valid.')
        return redirect('loyalty_dashboard')

    request.session['selected_reward_id'] = reward.id
    request.session.modified = True
    messages.success(request, f'{reward.discount_percentage}% reward selected. It will be applied at checkout.')
    return redirect('loyalty_dashboard')


def clear_loyalty_selection(request):
    """Clear pending points and selected reward from session."""
    if request.method != 'POST':
        return redirect('loyalty_dashboard')
    request.session.pop('pending_points_redeem', None)
    request.session.pop('selected_reward_id', None)
    request.session.modified = True
    messages.success(request, 'Cleared selected reward and points redemption.')
    return redirect('loyalty_dashboard')
