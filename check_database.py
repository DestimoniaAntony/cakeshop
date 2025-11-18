"""
Quick database check script
Run this to verify your database has the necessary data for orders to work
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cakeshop.settings')
django.setup()

from admin_app.models import Product, Size, Flavor, ProductPrice, Customer, Order

print("=" * 70)
print("DATABASE CHECK - Order System Requirements")
print("=" * 70)

# Check Products
products = Product.objects.filter(is_active=True)
print(f"\n📦 PRODUCTS: {products.count()} active")
if products.count() == 0:
    print("   ⚠️  WARNING: No products found! Add products in admin first.")
else:
    for p in products[:5]:
        print(f"   ✅ {p.name} (ID: {p.id})")
    if products.count() > 5:
        print(f"   ... and {products.count() - 5} more")

# Check Sizes
sizes = Size.objects.filter(is_active=True)
print(f"\n📏 SIZES: {sizes.count()} active")
if sizes.count() == 0:
    print("   ⚠️  WARNING: No sizes found! Add sizes in admin first.")
else:
    for s in sizes:
        print(f"   ✅ {s.name} ({s.weight_in_kg} kg)")

# Check Flavors
flavors = Flavor.objects.filter(is_active=True)
print(f"\n🎨 FLAVORS: {flavors.count()} active")
if flavors.count() == 0:
    print("   ⚠️  WARNING: No flavors found! Add flavors in admin first.")
else:
    for f in flavors[:10]:
        flavor_type = "Premium ⭐" if f.flavor_type == 'premium' else "Normal"
        print(f"   ✅ {f.name} ({flavor_type}, ×{f.price_modifier})")
    if flavors.count() > 10:
        print(f"   ... and {flavors.count() - 10} more")

# Check ProductPrices
product_prices = ProductPrice.objects.all()
print(f"\n💰 PRODUCT PRICES: {product_prices.count()} combinations")
if product_prices.count() == 0:
    print("   ❌ CRITICAL: No product prices found!")
    print("   Orders will FAIL without ProductPrice entries!")
    print("\n   📝 HOW TO FIX:")
    print("   1. Go to Admin → Products → Product Prices")
    print("   2. Click 'Add Product Price'")
    print("   3. For EACH product:")
    print("      - Select Product")
    print("      - Select Size")  
    print("      - Select Flavor")
    print("      - Enter Price (e.g., 1200)")
    print("   4. Save")
    print("\n   You need prices for ALL combinations!")
else:
    print(f"   ✅ Price combinations available")
    for pp in product_prices[:10]:
        print(f"   - {pp.product.name} | {pp.size.name} | {pp.flavor.name}: ₹{pp.price}")
    if product_prices.count() > 10:
        print(f"   ... and {product_prices.count() - 10} more")
    
    # Check coverage
    if products.count() > 0 and sizes.count() > 0 and flavors.count() > 0:
        expected_combinations = products.count() * sizes.count() * flavors.count()
        coverage = (product_prices.count() / expected_combinations) * 100
        print(f"\n   📊 Coverage: {product_prices.count()}/{expected_combinations} combinations ({coverage:.1f}%)")
        if coverage < 100:
            print(f"   ⚠️  WARNING: Not all combinations have prices!")
            print(f"   Missing combinations will cause 'Price not available' errors")

# Check Customers
customers = Customer.objects.all()
print(f"\n👤 CUSTOMERS: {customers.count()} registered")
if customers.count() > 0:
    for c in customers[:5]:
        print(f"   - {c.name} ({c.phone_number})")
    if customers.count() > 5:
        print(f"   ... and {customers.count() - 5} more")

# Check Orders
orders = Order.objects.all()
print(f"\n📋 ORDERS: {orders.count()} total")
if orders.count() > 0:
    recent_orders = orders.order_by('-created_at')[:5]
    for o in recent_orders:
        print(f"   - {o.order_number}: {o.product.name} | {o.customer.name} | ₹{o.total_price}")
    if orders.count() > 5:
        print(f"   ... and {orders.count() - 5} more")

print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

issues = []
if products.count() == 0:
    issues.append("❌ No products")
if sizes.count() == 0:
    issues.append("❌ No sizes")
if flavors.count() == 0:
    issues.append("❌ No flavors")
if product_prices.count() == 0:
    issues.append("❌ No product prices (CRITICAL!)")

if issues:
    print("⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print("\n💡 FIX THESE ISSUES IN ADMIN PANEL BEFORE TESTING ORDERS!")
else:
    print("✅ ALL REQUIRED DATA EXISTS")
    print("✅ SYSTEM READY TO ACCEPT ORDERS!")
    print("\n🧪 TO TEST:")
    print("   1. Visit: http://127.0.0.1:8000/products/")
    print("   2. Click any product")
    print("   3. Select size AND flavor (both required!)")
    print("   4. Fill customer details")
    print("   5. Click 'Send to WhatsApp'")
    print("\n✅ Order will be saved to database")
    print("✅ Confirmation page will open")
    print("✅ WhatsApp will open automatically")
    print("✅ Message sent to: 9946588352")

print("=" * 70)

