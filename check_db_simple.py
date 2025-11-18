"""Database Check Script - Simple Version"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cakeshop.settings')
django.setup()

from admin_app.models import Product, Size, Flavor, ProductPrice, Customer, Order

print("=" * 70)
print("DATABASE CHECK - Order System Requirements")
print("=" * 70)

# Check Products
products = Product.objects.filter(is_active=True)
print(f"\nPRODUCTS: {products.count()} active")
for p in products[:5]:
    print(f"  - {p.name}")

# Check Sizes
sizes = Size.objects.filter(is_active=True)
print(f"\nSIZES: {sizes.count()} active")
for s in sizes:
    print(f"  - {s.name} ({s.weight_in_kg} kg)")

# Check Flavors
flavors = Flavor.objects.filter(is_active=True)
print(f"\nFLAVORS: {flavors.count()} active")
for f in flavors[:10]:
    print(f"  - {f.name} ({f.flavor_type})")

# Check ProductPrices
product_prices = ProductPrice.objects.all()
print(f"\nPRODUCT PRICES: {product_prices.count()} combinations")
if product_prices.count() == 0:
    print("  ** CRITICAL: No product prices found! **")
    print("  ** Orders will FAIL without ProductPrice entries! **")
else:
    for pp in product_prices[:10]:
        print(f"  - {pp.product.name} | {pp.size.name} | {pp.flavor.name}: Rs.{pp.price}")

# Check Customers
customers = Customer.objects.all()
print(f"\nCUSTOMERS: {customers.count()} registered")
for c in customers[:5]:
    print(f"  - {c.name} ({c.phone_number})")

# Check Orders
orders = Order.objects.all()
print(f"\nORDERS: {orders.count()} total")
for o in orders.order_by('-created_at')[:5]:
    print(f"  - {o.order_number}: {o.product.name} | {o.customer.name}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if product_prices.count() == 0:
    print("** ERROR: No ProductPrice entries! **")
    print("** Add them in Admin -> Products -> Product Prices **")
else:
    print("Status: READY TO ACCEPT ORDERS")
    print(f"Test URL: http://127.0.0.1:8000/products/")

print("=" * 70)

