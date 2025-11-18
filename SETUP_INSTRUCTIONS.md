# Setup Instructions - Custom Cake Pricing Improvements

## Quick Start Guide

### Step 1: Apply Database Migrations
```bash
cd "D:\Python Projects\Live Project\cakesbydesti\cakeshop"
python manage.py migrate admin_app
```

### Step 2: Add Sample Flavors (via Django Admin)
After migration, login to admin panel and add flavors:

```
/admin/admin_app/flavor/add/

Example Flavors:
1. Vanilla
   - Price per kg: ₹50
   - Display Order: 1
   
2. Chocolate
   - Price per kg: ₹80
   - Display Order: 2
   
3. Strawberry
   - Price per kg: ₹100
   - Display Order: 3
   
4. Red Velvet
   - Price per kg: ₹120
   - Display Order: 4
   
5. Black Forest
   - Price per kg: ₹150
   - Display Order: 5
```

### Step 3: Update Existing Decorations (Optional)
Review decoration prices to ensure they are per-unit:
```
/admin/admin_app/decoration/

Example:
- Fresh Rose: ₹50 (per flower)
- Butterfly Topper: ₹30 (per piece)
- Gold Leaf: ₹200 (per sheet)
- Edible Flowers: ₹40 (per piece)
```

### Step 4: Test the System

#### Test Custom Order Flow:
1. Go to `/custom-cakes/`
2. Fill order form:
   - Select shape, tier, weight
   - Choose flavor from dropdown
   - Add decorations with quantities
3. Submit order
4. Verify price range displays correctly

#### Test Admin Interface:
1. View custom order in admin
2. Check price breakdown display
3. Verify decoration inline shows quantities
4. Test adding/editing decorations with quantities

---

## What Changed?

### Database Changes
✅ New `Flavor` table
✅ New `CustomCakeOrderDecoration` table (with quantity field)
✅ Removed old `decorations` M2M relationship
✅ Added `flavor` FK to `CustomCakeOrder`

### Code Changes
✅ Updated models (`admin_app/models.py`)
✅ Updated admin interface (`admin_app/admin.py`)
✅ Updated views (`cakeshop_app/views.py`)
✅ Updated price calculation logic
✅ Updated WhatsApp message generation
✅ Updated PDF generation

### Features Added
✅ Flavor selection with per-kg pricing
✅ Decoration quantity support
✅ Price range display (±15%)
✅ Enhanced admin price breakdown

---

## Frontend Updates Needed (If Applicable)

### Custom Cake Order Form Template
The form should include:

1. **Flavor Dropdown:**
```html
<select name="flavor_id" id="flavor_id">
    <option value="">-- Select Flavor --</option>
    {% for flavor in flavors %}
    <option value="{{ flavor.id }}" data-price="{{ flavor.price_per_kg }}">
        {{ flavor.name }} (+₹{{ flavor.price_per_kg }}/kg)
    </option>
    {% endfor %}
</select>
```

2. **Custom Flavor Input:**
```html
<input type="text" name="flavor_description" placeholder="Or enter custom flavor">
```

3. **Decoration with Quantity:**
```html
<div class="decoration-item">
    <input type="checkbox" name="decoration_ids" value="{{ decoration.id }}">
    <label>{{ decoration.name }} (₹{{ decoration.price }})</label>
    <input type="number" name="decoration_quantities" min="1" value="1" class="quantity-input">
</div>
```

4. **Price Display Area:**
```html
<div class="price-display">
    <p class="price-range">Estimated Price: <span id="priceRange">₹0 - ₹0</span></p>
    <p class="base-estimate"><small>Base estimate: ₹<span id="baseEstimate">0</span></small></p>
</div>
```

### JavaScript for Live Price Calculation (Optional)
```javascript
function calculatePrice() {
    // Get form values
    const shapePrice = parseFloat($('#shape_id option:selected').data('price'));
    const weight = parseFloat($('#total_weight').val()) || 0;
    const flavorPrice = parseFloat($('#flavor_id option:selected').data('price')) || 0;
    const tierMultiplier = parseFloat($('#tier_id option:selected').data('multiplier')) || 1;
    
    // Calculate base + flavor
    const basePrice = shapePrice * weight;
    const flavorCost = flavorPrice * weight;
    const subtotal = basePrice + flavorCost;
    
    // Apply tier multiplier
    const withTier = subtotal * tierMultiplier;
    
    // Calculate decorations
    let decorationTotal = 0;
    $('.decoration-item input[type="checkbox"]:checked').each(function() {
        const price = parseFloat($(this).data('price'));
        const qty = parseInt($(this).closest('.decoration-item').find('.quantity-input').val()) || 1;
        decorationTotal += price * qty;
    });
    
    // Total estimate
    const total = withTier + decorationTotal;
    
    // Calculate range (±15%)
    const minPrice = Math.round((total * 0.85) / 100) * 100;
    const maxPrice = Math.round((total * 1.15) / 100) * 100;
    
    // Update display
    $('#baseEstimate').text(total.toFixed(2));
    $('#priceRange').text('₹' + minPrice.toLocaleString() + ' - ₹' + maxPrice.toLocaleString());
}

// Bind events
$('#shape_id, #tier_id, #total_weight, #flavor_id').on('change', calculatePrice);
$('.decoration-item input').on('change input', calculatePrice);
```

---

## Backward Compatibility

### Existing Orders
- ✅ Old orders without flavor will work fine (flavor is optional)
- ✅ Old orders with old decoration structure remain readable
- ⚠️ Can't edit old order decorations with new system (minor issue)

### Migration Safety
- ✅ No data loss
- ✅ Removed M2M field (decorations) - old data preserved in DB
- ✅ Added new fields as nullable/optional

---

## Verification Checklist

After setup, verify:

- [ ] Migration applied successfully
- [ ] Admin can add/edit flavors
- [ ] Admin can view flavor list
- [ ] Custom order form shows flavor dropdown
- [ ] Custom order form accepts decoration quantities
- [ ] Price calculation includes flavor cost
- [ ] Decorations multiply by quantity correctly
- [ ] Price range displays (±15% of estimate)
- [ ] WhatsApp message shows correct breakdown
- [ ] PDF shows flavor and decoration quantities
- [ ] Admin price breakdown is detailed and accurate

---

## Rollback Plan (If Needed)

If issues arise, you can rollback:

```bash
# Rollback migration
python manage.py migrate admin_app 0003_remove_primary_flavor_field

# Restore old code from git
git checkout HEAD~1 admin_app/models.py
git checkout HEAD~1 admin_app/admin.py
git checkout HEAD~1 cakeshop_app/views.py
```

---

## Support

For issues or questions:
1. Check `CUSTOM_CAKE_PRICING_IMPROVEMENTS.md` for detailed documentation
2. Review migration file: `admin_app/migrations/0004_flavor_remove_customcakeorder_decorations_and_more.py`
3. Test in development environment first
4. Keep backup before applying to production

---

## Next Steps

1. ✅ Apply migration
2. ✅ Add sample flavors
3. ✅ Update decoration prices if needed
4. ✅ Test custom order flow
5. ⏳ Update frontend template (if custom template exists)
6. ⏳ Add JavaScript for live price calculation (optional)
7. ⏳ Train staff on new system
8. ⏳ Monitor first few orders for accuracy

Good luck! 🎂
