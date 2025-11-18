from django.contrib import admin
from django import forms
from .models import (
    Category, Subcategory, Size, Product, ProductImage, ProductPrice,
    Ingredient, PurchaseBill, Event, EventSuggestion, Customer, Order,
    Enquiry, Gallery, Review, CarouselSlide, OfferBanner,
    PageTitleBanner,
    CakeShape, CakeTier, Flavor, Decoration, CustomCakeOrder, CustomCakeOrderDecoration,
    GiftBox, GiftBoxItem, GiftBoxOrder,
    LoyaltyCard, LoyaltyReward, PointsTransaction, Referral, Achievement, CustomerAchievement
)
from .widgets import ImageCropWidget


# ===========================
# Admin Forms with Crop Widget
# ===========================

class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }


class SubcategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'main_image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter sizes queryset if a category is present
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                from .models import Category
                category = Category.objects.get(id=category_id)
                self.fields['sizes'].queryset = category.sizes.all()
            except (ValueError, TypeError, Category.DoesNotExist):
                pass
        elif self.instance.pk and self.instance.category:
            # Editing an existing product
            self.fields['sizes'].queryset = self.instance.category.sizes.all()


class ProductImageAdminForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }


class GalleryAdminForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }


class CarouselSlideAdminForm(forms.ModelForm):
    class Meta:
        model = CarouselSlide
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=16/9, target_width=1920, target_height=1080),
        }


class OfferBannerAdminForm(forms.ModelForm):
    class Meta:
        model = OfferBanner
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=2/1, target_width=800, target_height=400),
        }


# ===========================
# Category & Subcategory
# ===========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ['name', 'is_cake', 'is_active', 'created_at']
    list_filter = ['is_cake', 'is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    form = SubcategoryAdminForm
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']


# ===========================
# Sizes
# ===========================

class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'weight_in_kg', 'is_active')
    filter_horizontal = ('categories',)  # Makes ManyToMany editable with a nice widget
    search_fields = ('name',)
    list_filter = ('is_active', 'categories')

admin.site.register(Size, SizeAdmin)


# ===========================
# Products
# ===========================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    form = ProductImageAdminForm
    extra = 1


class ProductPriceInline(admin.TabularInline):
    model = ProductPrice
    extra = 0
    fields = ['size', 'price']
    verbose_name = 'Price for Size'
    verbose_name_plural = '💰 Set Prices for Each Size'
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            # Allow deletion of price entries
            formset.can_delete = True
        return formset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ['name', 'category', 'subcategory', 'is_active', 'created_at']
    list_filter = ['category', 'subcategory', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['sizes']
    inlines = [ProductPriceInline, ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'subcategory', 'main_image')
        }),
        ('Product Options', {
            'fields': ('sizes', 'is_active'),
            'description': 'Select available sizes first, then set prices for each size below.'
        }),
    )


# ===========================
# Inventory
# ===========================

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_quantity', 'unit', 'reorder_level', 'is_low_stock', 'last_updated']
    list_filter = ['unit', 'last_updated']
    search_fields = ['name']
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True


# ===========================
# Purchase Bills
# ===========================

@admin.register(PurchaseBill)
class PurchaseBillAdmin(admin.ModelAdmin):
    list_display = ['supplier_name', 'date', 'total_amount', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['supplier_name', 'notes']
    date_hierarchy = 'date'


# ===========================
# Events
# ===========================

class EventSuggestionInline(admin.TabularInline):
    model = EventSuggestion
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['event_name', 'description']
    inlines = [EventSuggestionInline]


# ===========================
# Customers
# ===========================

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'email', 'loyalty_tier', 'loyalty_points', 'total_orders', 'created_at']
    search_fields = ['name', 'phone_number', 'email']
    date_hierarchy = 'created_at'
    list_filter = ['created_at']
    
    def loyalty_tier(self, obj):
        """Display customer's loyalty tier"""
        try:
            if hasattr(obj, 'loyalty_card'):
                return f"{obj.loyalty_card.get_tier_display()}"
            return "No Card"
        except:
            return "No Card"
    loyalty_tier.short_description = 'Tier'
    
    def loyalty_points(self, obj):
        """Display customer's points balance"""
        try:
            if hasattr(obj, 'loyalty_card'):
                return f"{obj.loyalty_card.points_balance} pts"
            return "0 pts"
        except:
            return "0 pts"
    loyalty_points.short_description = 'Points'
    
    def total_orders(self, obj):
        """Display total completed orders"""
        try:
            if hasattr(obj, 'loyalty_card'):
                return obj.loyalty_card.total_orders
            return 0
        except:
            return 0
    total_orders.short_description = 'Orders'


# ===========================
# Orders
# ===========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'product', 'size', 'status', 'delivery_date', 'total_price', 'reward_used_percent', 'points_redeemed', 'created_at']
    list_filter = ['status', 'delivery_date', 'created_at', 'event']
    search_fields = ['order_number', 'customer__name', 'customer__phone_number', 'product__name']
    date_hierarchy = 'delivery_date'
    readonly_fields = ['order_number', 'total_price', 'created_at', 'updated_at']

    def reward_used_percent(self, obj):
        reward = LoyaltyReward.objects.filter(used_on_order=obj).first()
        if reward and reward.discount_percentage:
            return f"{reward.discount_percentage}%"
        return '-'
    reward_used_percent.short_description = 'Reward Used'

    def points_redeemed(self, obj):
        pts = PointsTransaction.objects.filter(order=obj, transaction_type='redeemed').aggregate(total=admin.models.Sum('points'))
        total = pts.get('total') or 0
        return f"{total}"
    points_redeemed.short_description = 'Points Redeemed'


# ===========================
# Enquiries
# ===========================

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_responded', 'created_at']
    list_filter = ['is_responded', 'created_at']
    search_fields = ['name', 'phone', 'email', 'message']
    date_hierarchy = 'created_at'


# ===========================
# Gallery
# ===========================

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    form = GalleryAdminForm
    list_display = ['caption', 'event_type', 'is_featured', 'uploaded_at']
    list_filter = ['is_featured', 'event_type', 'uploaded_at']
    search_fields = ['caption']


# ===========================
# Reviews
# ===========================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'rating', 'product', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['customer_name', 'comment']


# ===========================
# Homepage Carousel
# ===========================

@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    form = CarouselSlideAdminForm
    list_display = ['title', 'subtitle', 'display_order', 'button_text', 'start_date', 'end_date', 'is_active', 'is_valid']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['display_order', 'is_active']
    list_display_links = ['title']
    
    fieldsets = (
        ('Slide Content', {
            'fields': ('title', 'subtitle', 'description', 'image')
        }),
        ('Call to Action', {
            'fields': ('button_text', 'button_link')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date')
        }),
    )
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'


# ===========================
# Promotional Offers
# ===========================

@admin.register(OfferBanner)
class OfferBannerAdmin(admin.ModelAdmin):
    form = OfferBannerAdminForm
    list_display = ['title', 'discount_percentage', 'start_date', 'end_date', 'is_active', 'is_valid']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    list_editable = ['is_active']
    list_display_links = ['title']
    
    fieldsets = (
        ('Offer Details', {
            'fields': ('title', 'description', 'discount_percentage', 'image')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
    )
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'


# ===========================
# Page Title Banners
# ===========================


class PageTitleBannerAdminForm(forms.ModelForm):
    class Meta:
        model = PageTitleBanner
        fields = '__all__'
        widgets = {
            'image': ImageCropWidget(aspect_ratio=16/4, target_width=1600, target_height=400),
        }


@admin.register(PageTitleBanner)
class PageTitleBannerAdmin(admin.ModelAdmin):
    form = PageTitleBannerAdminForm
    list_display = ['name', 'page_key', 'display_order', 'is_active', 'start_date', 'end_date', 'is_valid']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'page_key', 'title_text', 'subtitle_text']
    list_editable = ['display_order', 'is_active']

    fieldsets = (
        ('Content', {
            'fields': ('name', 'page_key', 'title_text', 'subtitle_text', 'image')
        }),
        ('Display', {
            'fields': ('display_order', 'is_active')
        }),
        ('Validity', {
            'fields': ('start_date', 'end_date')
        }),
    )

    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'


# ===========================
# Custom Cake Builder
# ===========================

@admin.register(CakeShape)
class CakeShapeAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price_per_kg', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['base_price_per_kg', 'display_order', 'is_active']
    
    fieldsets = (
        ('Shape Information', {
            'fields': ('name', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('base_price_per_kg',),
            'description': 'Base price per kilogram for this shape (e.g., ₹600/kg)'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )


@admin.register(CakeTier)
class CakeTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'tiers_count', 'price_multiplier', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price_multiplier', 'display_order', 'is_active']
    
    fieldsets = (
        ('Tier Information', {
            'fields': ('name', 'tiers_count', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('price_multiplier',),
            'description': 'Multiplier for pricing: 1-tier=1.0, 2-tier=1.8, 3-tier=2.5'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )


@admin.register(Flavor)
class FlavorAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_kg', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price_per_kg', 'display_order', 'is_active']
    
    fieldsets = (
        ('Flavor Information', {
            'fields': ('name', 'description')
        }),
        ('Pricing', {
            'fields': ('price_per_kg',),
            'description': 'Additional price per kg for this flavor (added to base shape price)'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )


@admin.register(Decoration)
class DecorationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'display_order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'display_order', 'is_active']
    
    fieldsets = (
        ('Decoration Information', {
            'fields': ('name', 'description', 'category', 'image')
        }),
        ('Pricing', {
            'fields': ('price',),
            'description': 'Price per unit of this decoration (e.g., per flower, per figure)'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )


class CustomCakeOrderDecorationInline(admin.TabularInline):
    model = CustomCakeOrderDecoration
    extra = 1
    fields = ['decoration', 'quantity']
    verbose_name = 'Decoration'
    verbose_name_plural = 'Decorations (with quantities)'


@admin.register(CustomCakeOrder)
class CustomCakeOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'shape', 'tier', 'total_weight', 'flavor_display', 'status', 'price_range_display', 'estimated_price', 'final_price', 'delivery_date', 'created_at']
    list_filter = ['status', 'shape', 'tier', 'flavor', 'delivery_date', 'created_at']
    search_fields = ['order_number', 'customer__name', 'customer__phone_number', 'special_instructions']
    date_hierarchy = 'delivery_date'
    readonly_fields = ['order_number', 'estimated_price', 'created_at', 'updated_at', 'price_breakdown_display', 'price_range_display']
    inlines = [CustomCakeOrderDecorationInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'event')
        }),
        ('Cake Specifications', {
            'fields': ('shape', 'tier', 'total_weight', 'flavor', 'flavor_description'),
            'description': 'Select the cake structure and flavor. Use flavor dropdown for predefined flavors, or enter custom flavor in description field.'
        }),
        ('Customization', {
            'fields': ('reference_image', 'special_instructions', 'custom_message')
        }),
        ('Delivery Details', {
            'fields': ('delivery_date', 'delivery_time', 'delivery_address')
        }),
        ('Pricing', {
            'fields': ('estimated_price', 'price_range_display', 'final_price', 'price_note', 'price_breakdown_display'),
            'description': 'Estimated price is auto-calculated. Price range shows customer-facing estimate. You can set a different final price with a note.'
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def flavor_display(self, obj):
        """Display flavor name or description"""
        if obj.flavor:
            return obj.flavor.name
        elif obj.flavor_description:
            return obj.flavor_description
        return 'Not specified'
    flavor_display.short_description = 'Flavor'
    
    def price_breakdown_display(self, obj):
        """Display price calculation breakdown"""
        if not obj.pk:
            return "Save first to see price breakdown"
        
        breakdown = obj.price_breakdown
        
        flavor_text = obj.flavor.name if obj.flavor else (obj.flavor_description or 'Not specified')
        flavor_row = ''
        if obj.flavor and breakdown['flavor'] > 0:
            flavor_row = f"""
            <tr>
                <td style="padding: 8px;">Flavor ({flavor_text}, {obj.total_weight}kg)</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['flavor']}</td>
            </tr>
            """
        
        # Get decoration details
        order_decorations = obj.order_decorations.all()
        decoration_details = ''
        if order_decorations:
            decoration_details = '<br><small>' + ', '.join([f"{od.quantity}× {od.decoration.name}" for od in order_decorations]) + '</small>'
        
        html = f"""
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 8px; text-align: left;">Component</th>
                <th style="padding: 8px; text-align: right;">Amount</th>
            </tr>
            <tr>
                <td style="padding: 8px;">Shape Cost ({obj.shape.name}, {obj.total_weight}kg @ ₹{obj.shape.base_price_per_kg}/kg)</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['shape']}</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Flavor/Product Cost ({breakdown['flavor_source']})</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['flavor']}</td>
            </tr>
            <tr style="background-color: #f0f8ff;">
                <td style="padding: 8px;"><strong>Subtotal (before tier)</strong></td>
                <td style="padding: 8px; text-align: right;"><strong>₹{breakdown['subtotal']}</strong></td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px;">With Tier Multiplier ({obj.tier.name}, ×{obj.tier.price_multiplier})</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['with_tier']}</td>
            </tr>
            <tr>
                <td style="padding: 8px;">Decorations{decoration_details}</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['decorations']}</td>
            </tr>
            <tr style="background-color: #e8f4f8; font-weight: bold;">
                <td style="padding: 8px;">Total Estimate</td>
                <td style="padding: 8px; text-align: right;">₹{breakdown['total']}</td>
            </tr>
            <tr style="background-color: #fff3cd;">
                <td style="padding: 8px;">Customer Price Range (±15%)</td>
                <td style="padding: 8px; text-align: right; font-weight: bold;">{obj.price_range_display}</td>
            </tr>
        </table>
        """
        return html
    
    price_breakdown_display.short_description = 'Price Calculation Breakdown'
    price_breakdown_display.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Recalculate estimate when saving"""
        super().save_model(request, obj, form, change)
        # Recalculate estimate after saving (in case decorations changed)
        if change:
            obj.update_estimate()
    
    actions = ['recalculate_prices', 'mark_as_quoted', 'mark_as_confirmed', 'mark_as_preparing', 'mark_as_completed']
    
    def recalculate_prices(self, request, queryset):
        """Recalculate estimated prices for selected orders"""
        updated = 0
        for order in queryset:
            old_price = order.estimated_price
            order.update_estimate()
            if order.estimated_price != old_price:
                updated += 1
        
        self.message_user(
            request,
            f"Recalculated {queryset.count()} order(s). {updated} price(s) changed."
        )
    recalculate_prices.short_description = "🔄 Recalculate Prices (use after updating flavor prices)"
    
    def mark_as_quoted(self, request, queryset):
        queryset.update(status='quoted')
        self.message_user(request, f"{queryset.count()} orders marked as Quoted")
    mark_as_quoted.short_description = "Mark as Quoted (Estimate Sent)"
    
    def mark_as_confirmed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='confirmed', confirmed_at=timezone.now())
        self.message_user(request, f"{queryset.count()} orders marked as Confirmed")
    mark_as_confirmed.short_description = "Mark as Confirmed"
    
    def mark_as_preparing(self, request, queryset):
        queryset.update(status='preparing')
        self.message_user(request, f"{queryset.count()} orders marked as Preparing")
    mark_as_preparing.short_description = "Mark as Preparing"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} orders marked as Completed")
    mark_as_completed.short_description = "Mark as Completed"


# ===========================
# Gift Box Management
# ===========================

class GiftBoxAdminForm(forms.ModelForm):
    class Meta:
        model = GiftBox
        fields = '__all__'
        widgets = {
            'main_image': ImageCropWidget(aspect_ratio=500/281, target_width=500, target_height=281),
        }


class GiftBoxItemInline(admin.TabularInline):
    model = GiftBoxItem
    extra = 1
    fields = ('product', 'size', 'quantity', 'display_order', 'unit_price_display', 'subtotal_display')
    readonly_fields = ('unit_price_display', 'subtotal_display')
    
    def unit_price_display(self, obj):
        if obj.pk:
            return f"₹{obj.unit_price}"
        return "-"
    unit_price_display.short_description = 'Unit Price'
    
    def subtotal_display(self, obj):
        if obj.pk:
            return f"₹{obj.subtotal}"
        return "-"
    subtotal_display.short_description = 'Subtotal'


@admin.register(GiftBox)
class GiftBoxAdmin(admin.ModelAdmin):
    form = GiftBoxAdminForm
    list_display = ('name', 'pricing_type', 'total_price_display', 'items_count', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'pricing_type', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('display_order', 'is_active')
    inlines = [GiftBoxItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'main_image', 'is_active', 'display_order')
        }),
        ('Pricing Configuration', {
            'fields': ('pricing_type', 'fixed_price', 'discount_percentage'),
            'description': 'Configure how the price is calculated for this gift box'
        }),
    )
    
    def total_price_display(self, obj):
        if obj.pk:
            return f"₹{obj.total_price:.2f}"
        return "-"
    total_price_display.short_description = 'Total Price'
    
    def save_model(self, request, obj, form, change):
        """Save the model and refresh to calculate price"""
        super().save_model(request, obj, form, change)


@admin.register(GiftBoxOrder)
class GiftBoxOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer', 'gift_box', 'quantity',
        'status', 'delivery_date', 'total_price', 'created_at'
    )
    list_filter = ('status', 'delivery_date', 'created_at', 'event')
    search_fields = ('order_number', 'customer__name', 'customer__phone_number', 'gift_box__name')
    readonly_fields = ('order_number', 'unit_price', 'total_price', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'gift_box', 'quantity', 'status')
        }),
        ('Delivery Details', {
            'fields': ('delivery_date', 'delivery_time', 'event')
        }),
        ('Additional Information', {
            'fields': ('special_instructions',)
        }),
        ('Pricing', {
            'fields': ('unit_price', 'total_price'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_preparing', 'mark_as_ready', 'mark_as_completed']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} orders marked as Confirmed")
    mark_as_confirmed.short_description = "Mark as Confirmed"
    
    def mark_as_preparing(self, request, queryset):
        queryset.update(status='preparing')
        self.message_user(request, f"{queryset.count()} orders marked as Preparing")
    mark_as_preparing.short_description = "Mark as Preparing"
    
    def mark_as_ready(self, request, queryset):
        queryset.update(status='ready')
        self.message_user(request, f"{queryset.count()} orders marked as Ready")
    mark_as_ready.short_description = "Mark as Ready for Pickup/Delivery"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} orders marked as Completed")
    mark_as_completed.short_description = "Mark as Completed"


# ===========================
# Loyalty & Rewards Admin
# ===========================

@admin.register(LoyaltyCard)
class LoyaltyCardAdmin(admin.ModelAdmin):
    list_display = (
        'card_number', 'customer', 'tier', 'current_stamps', 'stamps_to_reward',
        'points_balance', 'total_orders', 'total_spent', 'joined_date'
    )
    list_filter = ('tier', 'is_active', 'joined_date')
    search_fields = ('card_number', 'customer__name', 'customer__phone_number')
    readonly_fields = (
        'card_number', 'total_stamps', 'lifetime_points', 'total_orders',
        'total_spent', 'rewards_claimed', 'referrals_made', 'joined_date', 'last_activity'
    )
    
    fieldsets = (
        ('Customer & Card Info', {
            'fields': ('customer', 'card_number', 'tier', 'is_active')
        }),
        ('Stamp Card Progress', {
            'fields': ('current_stamps', 'stamps_to_reward', 'total_stamps', 'rewards_claimed')
        }),
        ('Points Balance', {
            'fields': ('points_balance', 'lifetime_points')
        }),
        ('Statistics', {
            'fields': ('total_orders', 'total_spent', 'referrals_made')
        }),
        ('Timestamps', {
            'fields': ('joined_date', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_stamps', 'add_bonus_points']
    
    def reset_stamps(self, request, queryset):
        for card in queryset:
            card.current_stamps = 0
            card.save()
        self.message_user(request, f"Reset stamps for {queryset.count()} cards")
    reset_stamps.short_description = "Reset current stamps"
    
    def add_bonus_points(self, request, queryset):
        for card in queryset:
            card.add_points(50, 'Admin bonus points')
        self.message_user(request, f"Added 50 bonus points to {queryset.count()} cards")
    add_bonus_points.short_description = "Add 50 bonus points"


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(admin.ModelAdmin):
    list_display = (
        'loyalty_card', 'reward_type', 'discount_percentage',
        'status', 'issued_date', 'expiry_date', 'used_date'
    )
    list_filter = ('reward_type', 'status', 'issued_date', 'expiry_date')
    search_fields = ('loyalty_card__customer__name', 'loyalty_card__card_number')
    readonly_fields = ('issued_date', 'used_date')
    
    fieldsets = (
        ('Reward Information', {
            'fields': ('loyalty_card', 'reward_type', 'status')
        }),
        ('Discount Details', {
            'fields': ('discount_percentage', 'discount_amount', 'description')
        }),
        ('Validity', {
            'fields': ('issued_date', 'expiry_date')
        }),
        ('Usage', {
            'fields': ('used_on_order', 'used_date'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_expired', 'extend_expiry']
    
    def mark_as_expired(self, request, queryset):
        queryset.update(status='expired')
        self.message_user(request, f"{queryset.count()} rewards marked as expired")
    mark_as_expired.short_description = "Mark as Expired"
    
    def extend_expiry(self, request, queryset):
        from datetime import timedelta
        from django.utils import timezone
        for reward in queryset:
            reward.expiry_date = timezone.now().date() + timedelta(days=30)
            reward.save()
        self.message_user(request, f"Extended expiry for {queryset.count()} rewards by 30 days")
    extend_expiry.short_description = "Extend expiry by 30 days"


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'loyalty_card', 'points_display', 'transaction_type', 'reason', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('loyalty_card__customer__name', 'reason')
    readonly_fields = ('created_at',)
    
    def points_display(self, obj):
        sign = '+' if obj.transaction_type == 'earned' else '-'
        return f"{sign}{obj.points}"
    points_display.short_description = 'Points'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = (
        'referrer', 'referred_name', 'referred_phone', 'referral_code',
        'status', 'created_at', 'completed_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = (
        'referrer__name', 'referred_name', 'referred_phone', 'referral_code'
    )
    readonly_fields = ('referral_code', 'created_at', 'completed_at')
    
    fieldsets = (
        ('Referrer', {
            'fields': ('referrer',)
        }),
        ('Referred Person', {
            'fields': ('referred_name', 'referred_phone', 'referred_customer')
        }),
        ('Referral Details', {
            'fields': ('referral_code', 'status')
        }),
        ('Rewards', {
            'fields': ('referrer_reward_points', 'referred_reward_discount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        for referral in queryset:
            referral.mark_completed()
        self.message_user(request, f"{queryset.count()} referrals marked as completed and rewards awarded")
    mark_as_completed.short_description = "Mark as Completed & Award Rewards"


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'criteria_type', 'criteria_value', 'points_reward',
        'display_order', 'is_active'
    )
    list_filter = ('criteria_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('display_order', 'is_active')


@admin.register(CustomerAchievement)
class CustomerAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'loyalty_card', 'achievement', 'unlocked_at', 'is_viewed'
    )
    list_filter = ('unlocked_at', 'is_viewed', 'achievement')
    search_fields = ('loyalty_card__customer__name', 'achievement__name')
    readonly_fields = ('unlocked_at',)