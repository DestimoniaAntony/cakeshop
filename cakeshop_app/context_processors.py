"""
Context processors for cakeshop_app
These make variables available to all templates
"""
from admin_app.models import Category, Product, ProductPrice, Size, Customer, PageTitleBanner
from django.utils import timezone


def categories(request):
    """
    Add categories to all template contexts for navigation menu
    """
    return {
        'categories': Category.objects.filter(is_active=True).order_by('name')
    }


def cart_info(request):
    """
    Add cart information to all template contexts for navbar
    Includes item count, cart items, and total
    """
    cart = request.session.get('cart', [])
    total_items = sum(item.get('quantity', 1) for item in cart if item.get('type') == 'product')
    
    # Build cart items with full details for navbar dropdown
    cart_items = []
    cart_total = 0
    
    for item in cart:
        # Only show regular products in navbar dropdown (not custom cakes)
        if item.get('type') != 'product':
            continue
            
        try:
            product = Product.objects.get(id=item['product_id'])
            size = Size.objects.get(id=item['size_id'])
            size_price = ProductPrice.objects.filter(product=product, size=size).first()
            
            if not size_price:
                continue
            
            cart_items.append({
                'id': item.get('product_id', ''),
                'product': product,
                'size': size,
                'size_price': size_price,
                'quantity': item.get('quantity', 1),
                'subtotal': size_price.price * item.get('quantity', 1)
            })
            cart_total += size_price.price * item.get('quantity', 1)
        except (Product.DoesNotExist, Size.DoesNotExist):
            # Skip invalid cart items
            continue
    
    return {
        'cart_count': total_items,
        'cart_items': cart_items,
        'cart_total': cart_total
    }


def current_customer(request):
    """Add current logged-in customer name to templates when available.

    Uses session['customer_phone'] to look up the Customer and returns a simple
    name string to avoid extra DB hits in templates.
    """
    # Prefer name stored in session (set at login) to avoid DB lookup
    session_name = request.session.get('customer_name')
    if session_name:
        return {'current_customer_name': session_name, 'current_customer': None}

    phone = request.session.get('customer_phone')
    if not phone:
        return {'current_customer_name': None, 'current_customer': None}

    try:
        customer = Customer.objects.filter(phone_number=phone).first()
        if customer:
            return {'current_customer_name': customer.name, 'current_customer': customer}
    except Exception:
        pass

    return {'current_customer_name': None, 'current_customer': None}


def page_title_banner(request):
    """Provide the active page title banner for templates.

    Picks the first `PageTitleBanner` that is currently valid and active
    ordered by `display_order`. Templates can use `page_title_banner`.
    """
    try:
        today = timezone.now().date()
        # Build a mapping of page_key -> active banner ordered by display_order
        banners_qs = PageTitleBanner.objects.filter(is_active=True).order_by('display_order', '-created_at')
        page_banners = {}
        for b in banners_qs:
            # Only include banners that are currently valid
            try:
                if b.is_valid:
                    # prefer the first banner per page_key (ordered by display_order)
                    if b.page_key and b.page_key not in page_banners:
                        page_banners[b.page_key] = b
            except Exception:
                # skip if property access fails for any reason
                continue

        # Provide a single fallback banner (first valid banner) and map by key
        fallback = None
        if page_banners:
            # choose the banner with smallest display_order among mapped ones
            fallback = next(iter(page_banners.values()))
        else:
            # fallback to any valid banner if none keyed
            fallback = PageTitleBanner.objects.filter(is_active=True).order_by('display_order', '-created_at').first()

        return {'page_title_banner': fallback, 'page_title_banners': page_banners}
    except Exception:
        pass
    return {'page_title_banner': None, 'page_title_banners': {}}
