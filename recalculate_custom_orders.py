"""
Script to recalculate all custom cake orders after updating flavor prices.
Run this after updating flavor prices in the admin panel.

Usage:
    python recalculate_custom_orders.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cakeshop.settings')
django.setup()

from admin_app.models import CustomCakeOrder, Flavor
from decimal import Decimal

def recalculate_all_orders():
    """Recalculate all pending/quoted custom cake orders"""
    
    print("🔄 Starting recalculation of custom cake orders...\n")
    
    # Get all non-completed orders
    orders = CustomCakeOrder.objects.filter(
        status__in=['pending', 'quoted', 'customer_approved']
    ).select_related('flavor', 'shape', 'tier')
    
    total_orders = orders.count()
    
    if total_orders == 0:
        print("✅ No pending orders to recalculate.")
        return
    
    print(f"📊 Found {total_orders} order(s) to recalculate\n")
    print("=" * 70)
    
    recalculated = 0
    errors = 0
    
    for order in orders:
        try:
            # Get old price
            old_price = order.estimated_price
            
            # Recalculate
            order.update_estimate()
            
            # Get new price
            new_price = order.estimated_price
            
            # Calculate difference
            difference = new_price - old_price
            difference_percent = (difference / old_price * 100) if old_price > 0 else 0
            
            # Display info
            flavor_info = ""
            if order.flavor:
                flavor_info = f" | Flavor: {order.flavor.name} (₹{order.flavor.price_per_kg}/kg)"
            elif order.flavor_description:
                if order.custom_flavor_price_per_kg:
                    flavor_info = f" | Custom: {order.flavor_description} (₹{order.custom_flavor_price_per_kg}/kg)"
                else:
                    flavor_info = f" | Custom: {order.flavor_description} (⚠️ Price not set)"
            
            print(f"Order #{order.order_number}")
            print(f"  Customer: {order.customer.name}")
            print(f"  Shape: {order.shape.name} | Weight: {order.total_weight}kg | Tier: {order.tier.name}")
            print(f"  {flavor_info}")
            print(f"  Old Price: ₹{old_price:,.2f}")
            print(f"  New Price: ₹{new_price:,.2f}")
            
            if difference != 0:
                sign = "+" if difference > 0 else ""
                print(f"  Change: {sign}₹{difference:,.2f} ({sign}{difference_percent:.1f}%)")
                print(f"  ✅ UPDATED")
            else:
                print(f"  ⚪ No change")
            
            print("-" * 70)
            recalculated += 1
            
        except Exception as e:
            print(f"❌ Error recalculating Order #{order.order_number}: {str(e)}")
            print("-" * 70)
            errors += 1
    
    print("=" * 70)
    print(f"\n✅ Recalculation complete!")
    print(f"   Total orders processed: {total_orders}")
    print(f"   Successfully recalculated: {recalculated}")
    if errors > 0:
        print(f"   Errors: {errors}")
    print()

def show_flavor_prices():
    """Display current flavor prices"""
    print("\n💰 Current Flavor Prices:")
    print("=" * 70)
    
    flavors = Flavor.objects.filter(is_active=True).order_by('display_order', 'name')
    
    for flavor in flavors:
        print(f"  {flavor.name}: ₹{flavor.price_per_kg}/kg")
    
    print("=" * 70)
    print()

if __name__ == "__main__":
    print("\n🎂 Custom Cake Order Recalculation Tool")
    print("=" * 70)
    
    # Show current flavor prices
    show_flavor_prices()
    
    # Confirm before proceeding
    response = input("Do you want to recalculate all pending orders? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        recalculate_all_orders()
    else:
        print("\n❌ Recalculation cancelled.")

