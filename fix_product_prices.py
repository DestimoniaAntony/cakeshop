"""Fix ProductPrice entries - Remove NULL flavors and create proper ones"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cakeshop.settings')
django.setup()

from admin_app.models import Product, Size, Flavor, ProductPrice
from decimal import Decimal

print("=" * 70)
print("FIXING PRODUCT PRICES")
print("=" * 70)

# Step 1: Find and delete broken entries
broken_prices = ProductPrice.objects.filter(flavor__isnull=True)
print(f"\nFound {broken_prices.count()} broken entries (NULL flavor)")
if broken_prices.count() > 0:
    print("Deleting broken entries...")
    broken_prices.delete()
    print("OK - Deleted broken entries")

# Step 2: Check what we have
products = Product.objects.filter(is_active=True)
sizes = Size.objects.filter(is_active=True)
flavors = Flavor.objects.filter(is_active=True)

print(f"\nAvailable data:")
print(f"  Products: {products.count()}")
print(f"  Sizes: {sizes.count()}")
print(f"  Flavors: {flavors.count()}")

if products.count() == 0 or sizes.count() == 0 or flavors.count() == 0:
    print("\n** ERROR: Missing basic data! **")
    print("Add Products, Sizes, and Flavors in admin first!")
    exit(1)

# Step 3: Create ProductPrice for all combinations
print(f"\nCreating ProductPrice entries...")
print(f"Will create {products.count()} x {sizes.count()} x {flavors.count()} = {products.count() * sizes.count() * flavors.count()} combinations")

created_count = 0
existing_count = 0

for product in products:
    for size in sizes:
        for flavor in flavors:
            # Calculate price based on weight and flavor type
            base_price = Decimal('800.00')  # Rs 800 per kg base price
            weight_price = base_price * Decimal(str(size.weight_in_kg))
            flavor_price = weight_price * flavor.price_modifier
            final_price = round(flavor_price, 2)
            
            # Get or create
            pp, created = ProductPrice.objects.get_or_create(
                product=product,
                size=size,
                flavor=flavor,
                defaults={'price': final_price}
            )
            
            if created:
                created_count += 1
                print(f"  CREATED: {product.name} | {size.name} | {flavor.name} = Rs.{final_price}")
            else:
                existing_count += 1

print(f"\nResults:")
print(f"  Created: {created_count} new entries")
print(f"  Existing: {existing_count} entries (already had prices)")
print(f"  Total: {ProductPrice.objects.count()} ProductPrice entries")

print("\n" + "=" * 70)
print("DONE - ProductPrices Fixed!")
print("=" * 70)
print("\nYou can now test orders at:")
print("http://127.0.0.1:8000/products/")
print("\nRemember:")
print("1. Select BOTH size and flavor")
print("2. Fill customer details")
print("3. Click 'Send to WhatsApp'")
print("=" * 70)

