from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from .utils import resize_and_optimize_image, get_image_dimensions_for_model

# ===========================
# 1. Category & Subcategory
# ===========================



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        help_text='Optional. Image will be automatically resized to 500×281 pixels'
    )
    is_active = models.BooleanField(default=True)
    # NEW: Marks categories that are valid for cake flavor selection in custom cake builder
    is_cake = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            width, height = get_image_dimensions_for_model('Category', 'image')
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(
        upload_to='subcategories/',
        blank=True,
        null=True,
        help_text='Optional. Image will be automatically resized to 500×281 pixels'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Subcategories"
        ordering = ['name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            width, height = get_image_dimensions_for_model('Subcategory', 'image')
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)


# ===========================
# 2. Sizes
# ===========================

class Size(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "½ kg", "1 kg", "2 kg"
    weight_in_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Weight in kilograms (e.g., 0.5, 1.0, 2.0)',
        default=1.0
    )
    display_order = models.IntegerField(default=0, help_text='Order of display (lower numbers first)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # NEW FIELD: link size(s) to one or more categories
    categories = models.ManyToManyField('Category', related_name='sizes', blank=True)

    class Meta:
        ordering = ['display_order', 'weight_in_kg']
    
    def __str__(self):
        return self.name


# ===========================
# 3. Products
# ===========================

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    main_image = models.ImageField(
        upload_to='products/',
        help_text='Image will be automatically resized to 500×281 pixels for best display'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Available sizes (many-to-many)
    sizes = models.ManyToManyField(Size, related_name='products')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def min_price(self):
        """Get minimum price from all ProductPrice combinations"""
        min_price_obj = self.prices.order_by('price').first()
        return min_price_obj.price if min_price_obj else None
    
    def save(self, *args, **kwargs):
        # Process main image if it's being uploaded/changed
        if self.main_image:
            width, height = get_image_dimensions_for_model('Product', 'main_image')
            self.main_image = resize_and_optimize_image(self.main_image, width, height)
        super().save(*args, **kwargs)
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(
        upload_to='products/additional/',
        help_text='Image will be automatically resized to 500×281 pixels'
    )
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        if self.image:
            width, height = get_image_dimensions_for_model('ProductImage', 'image')
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)


class ProductPrice(models.Model):
    """Custom pricing for each Product + Size combination"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='product_prices')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Price for this specific product and size combination'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'size']
        ordering = ['product', 'size__display_order']
        verbose_name = 'Product Price'
        verbose_name_plural = 'Product Prices'

    def __str__(self):
        return f"{self.product.name} - {self.size.name}: ₹{self.price}"


# ===========================
# 4. Inventory
# ===========================

class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('dozen', 'Dozen'),
        ('packet', 'Packet'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.current_quantity} {self.unit})"
    
    @property
    def is_low_stock(self):
        return self.current_quantity <= self.reorder_level


# ===========================
# 5. Purchase Bills (Expenses)
# ===========================

class PurchaseBill(models.Model):
    supplier_name = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True, null=True)
    bill_upload = models.FileField(upload_to='purchase_bills/', blank=True, null=True)  # PDF or image
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.supplier_name} - ₹{self.total_amount} ({self.date})"


# ===========================
# 6. Events & Suggestions
# ===========================

class Event(models.Model):
    event_name = models.CharField(max_length=100, unique=True)  # Birthday, Wedding, etc.
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome icon class
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['event_name']
    
    def __str__(self):
        return self.event_name


class EventSuggestion(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='suggestions')
    suggested_item = models.CharField(max_length=200)  # Cake/add-on name
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.event.event_name} - {self.suggested_item}"


# ===========================
# 7. Customers
# ===========================

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15, unique=True)
    whatsapp_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text='WhatsApp number for order communication (with country code, e.g., 919876543210)'
    )
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text='Date of birth for birthday rewards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    @property
    def whatsapp_link(self):
        """Generate WhatsApp link"""
        number = self.whatsapp_number or self.phone_number
        # Remove any special characters and add country code if not present
        clean_number = ''.join(filter(str.isdigit, number))
        if not clean_number.startswith('91'):
            clean_number = '91' + clean_number
        return f"https://wa.me/{clean_number}"


# ===========================
# 8. Orders
# ===========================

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    custom_message = models.TextField(blank=True, null=True)  # Message on cake
    special_instructions = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateField()
    delivery_time = models.TimeField(blank=True, null=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def calculate_unit_price(self):
        """Calculate unit price from ProductPrice table"""
        try:
            product_price = ProductPrice.objects.get(
                product=self.product,
                size=self.size
            )
            return product_price.price
        except ProductPrice.DoesNotExist:
            # Fallback: return 0 or raise error
            return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            today = timezone.now()
            prefix = f"CK{today.strftime('%Y%m%d')}"
            last_order = Order.objects.filter(order_number__startswith=prefix).order_by('-order_number').first()
            if last_order:
                last_num = int(last_order.order_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_number = f"{prefix}{new_num:04d}"
        
        # Auto-calculate unit price from ProductPrice if not set
        if not self.unit_price or self.unit_price == 0:
            self.unit_price = self.calculate_unit_price()
        
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.name}"


# ===========================
# 9. Enquiries
# ===========================

class Enquiry(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_responded = models.BooleanField(default=False)
    response = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Enquiries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d')}"


# ===========================
# 10. Gallery
# ===========================

class Gallery(models.Model):
    image = models.ImageField(
        upload_to='gallery/',
        help_text='Image will be automatically resized to 500×281 pixels'
    )
    caption = models.CharField(max_length=200, blank=True, null=True)
    event_type = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='gallery_images')
    is_featured = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Gallery"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.caption if self.caption else f"Gallery Image {self.id}"
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            width, height = get_image_dimensions_for_model('Gallery', 'image')
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)


# ===========================
# 11. Reviews
# ===========================

class Review(models.Model):
    customer_name = models.CharField(max_length=200)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.rating}★"


# ===========================
# 12. Homepage Carousel/Slider
# ===========================

class CarouselSlide(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True, help_text='Main heading for the slide')
    subtitle = models.CharField(max_length=200, blank=True, null=True, help_text='Subheading or tagline (optional)')
    description = models.TextField(blank=True, null=True,help_text='Description text for the slide')
    image = models.ImageField(
        upload_to='carousel/',
        help_text='Image will be automatically resized to 1920×1080 pixels (Full HD)'
    )
    
    # Button/CTA
    button_text = models.CharField(max_length=50, blank=True, null=True, default='Order Now', help_text='Text for the call-to-action button')
    button_link = models.CharField(max_length=200, blank=True, null=True, default='/order/', help_text='URL for the button (e.g., /products/, /order/)')
    
    # Display Settings
    display_order = models.IntegerField(default=0, help_text='Order of appearance (lower numbers appear first)')
    is_active = models.BooleanField(default=True, help_text='Check to display this slide')
    
    # Validity Period
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text='Leave blank for no end date')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Carousel Slide'
        verbose_name_plural = 'Homepage Carousel'
    
    def __str__(self):
        return f"{self.start_date} (Order: {self.display_order})"
    
    @property
    def is_valid(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
    
    def save(self, *args, **kwargs):
        # Process carousel image if it's being uploaded/changed
        if self.image:
            width, height = get_image_dimensions_for_model('CarouselSlide', 'image')
            self.image = resize_and_optimize_image(self.image, width, height, quality=90)
        super().save(*args, **kwargs)


class PageTitleBanner(models.Model):
    """A banner used for the page-title / hero area across site pages.

    Admins can create banners and set validity periods. The context
    processor will pick the first active banner (by display order) to show
    on templates that render the page-title area.
    """

    name = models.CharField(max_length=100, blank=True, null=True, help_text='Optional friendly name for this banner')
    page_key = models.CharField(max_length=50, blank=True, null=True, help_text='Optional key to target a specific page')
    title_text = models.CharField(max_length=200, blank=True, null=True, help_text='Main heading to show on the banner')
    subtitle_text = models.CharField(max_length=200, blank=True, null=True, help_text='Optional subheading')

    image = models.ImageField(
        upload_to='page_banners/',
        help_text='Image will be automatically resized for the page title area'
    )

    display_order = models.IntegerField(default=0, help_text='Order of appearance (lower numbers appear first)')
    is_active = models.BooleanField(default=True, help_text='Check to display this banner')

    # Validity Period
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text='Leave blank for no end date')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Page Title Banner'
        verbose_name_plural = 'Page Title Banners'

    def __str__(self):
        return self.name or f"Banner {self.pk}"

    @property
    def is_valid(self):
        today = timezone.now().date()
        if not self.is_active:
            return False
        if self.start_date and self.end_date:
            return self.start_date <= today <= self.end_date
        if self.start_date and not self.end_date:
            return self.start_date <= today
        return True

    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            try:
                width, height = get_image_dimensions_for_model('PageTitleBanner', 'image')
            except Exception:
                width, height = (1600, 400)
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)




# ===========================
# 13. Offers & Promotional Banners
# ===========================

class OfferBanner(models.Model):
    title = models.CharField(max_length=200, help_text='Offer title (e.g., "20% Off Wedding Cakes")')
    description = models.TextField(help_text='Offer details and terms')
    image = models.ImageField(
        upload_to='offers/',
        help_text='Image will be automatically resized to 800×400 pixels'
    )
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text='Discount percentage (e.g., 10, 20, 25)'
    )
    
    # Validity
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True, help_text='Check to display this offer')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promotional Offer'
        verbose_name_plural = 'Promotional Offers'
    
    def __str__(self):
        return self.title
    
    @property
    def is_valid(self):
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
    
    def save(self, *args, **kwargs):
        # Process offer banner image if it's being uploaded/changed
        if self.image:
            width, height = get_image_dimensions_for_model('OfferBanner', 'image')
            self.image = resize_and_optimize_image(self.image, width, height)
        super().save(*args, **kwargs)


# ===========================
# 14. Custom Cake Builder
# ===========================

class CakeShape(models.Model):
    """Round, Square, Heart, Rectangle, Custom"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    base_price_per_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Base price per kilogram for this shape'
    )
    image = models.ImageField(
        upload_to='cake_shapes/', 
        blank=True, 
        null=True,
        help_text='Image will be automatically resized to 400×400 pixels'
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Cake Shape'
        verbose_name_plural = 'Cake Shapes'
    
    def __str__(self):
        return f"{self.name} (₹{self.base_price_per_kg}/kg)"
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            self.image = resize_and_optimize_image(self.image, 400, 400)
        super().save(*args, **kwargs)


class CakeTier(models.Model):
    """1-Tier, 2-Tier, 3-Tier"""
    name = models.CharField(max_length=50, unique=True)
    tiers_count = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True, null=True)
    price_multiplier = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.1)],
        help_text='Multiplier for pricing (e.g., 1-tier=1.0, 2-tier=1.8, 3-tier=2.5)'
    )
    image = models.ImageField(
        upload_to='cake_tiers/', 
        blank=True, 
        null=True,
        help_text='Image will be automatically resized to 400×400 pixels'
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'tiers_count']
        verbose_name = 'Cake Tier'
        verbose_name_plural = 'Cake Tiers'
    
    def __str__(self):
        return f"{self.name} ({self.tiers_count} tier{'s' if self.tiers_count > 1 else ''})"
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            self.image = resize_and_optimize_image(self.image, 400, 400)
        super().save(*args, **kwargs)


class Flavor(models.Model):
    """Cake flavors with pricing"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Additional price per kg for this flavor (base price is from shape)'
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Flavor'
        verbose_name_plural = 'Flavors'
    
    def __str__(self):
        return f"{self.name} (+₹{self.price_per_kg}/kg)"


class Decoration(models.Model):
    """Fresh Flowers, Fondant Figures, Edible Gold, etc."""
    CATEGORY_CHOICES = [
        ('flowers', 'Flowers'),
        ('fondant', 'Fondant Figures'),
        ('edible', 'Edible Decorations'),
        ('topping', 'Toppings'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Price per unit of this decoration (e.g., per flower, per figure)'
    )
    image = models.ImageField(
        upload_to='decorations/', 
        blank=True, 
        null=True,
        help_text='Image will be automatically resized to 300×300 pixels'
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'display_order', 'name']
        verbose_name = 'Decoration'
        verbose_name_plural = 'Decorations'
    
    def __str__(self):
        return f"{self.name} (₹{self.price})"
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.image:
            self.image = resize_and_optimize_image(self.image, 300, 300)
        super().save(*args, **kwargs)


class CustomCakeOrderDecoration(models.Model):
    """Intermediate model to track decoration quantities for custom orders"""
    custom_order = models.ForeignKey('CustomCakeOrder', on_delete=models.CASCADE, related_name='order_decorations')
    decoration = models.ForeignKey(Decoration, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Number of units (e.g., 5 flowers, 2 figures)'
    )
    
    class Meta:
        unique_together = ['custom_order', 'decoration']
        verbose_name = 'Custom Order Decoration'
        verbose_name_plural = 'Custom Order Decorations'
    
    def __str__(self):
        return f"{self.quantity}× {self.decoration.name}"
    
    @property
    def total_price(self):
        """Calculate total price for this decoration"""
        return self.decoration.price * self.quantity


class CustomCakeReferenceImage(models.Model):
    """Reference images for custom cake orders"""
    custom_order = models.ForeignKey('CustomCakeOrder', on_delete=models.CASCADE, related_name='reference_images')
    image = models.ImageField(
        upload_to='custom_orders/references/',
        help_text='Reference image (max 5MB)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Reference image for {self.custom_order.order_number}"


class CustomCakeOrder(models.Model):
    """Custom cake orders - separate from regular orders"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('quoted', 'Estimate Sent'),
        ('customer_approved', 'Customer Approved'),
        ('confirmed', 'Order Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='custom_orders')
    
    # Product Selection (optional - if customer selects existing product)
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='If customer selected an existing product for flavor'
    )
    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Size if product was selected'
    )
    
    # Cake Structure
    shape = models.ForeignKey(CakeShape, on_delete=models.PROTECT)
    tier = models.ForeignKey(CakeTier, on_delete=models.PROTECT)
    total_weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.1)],
        help_text='Total weight in kg'
    )
    
    # Flavor (now using Flavor model instead of text field)
    flavor = models.ForeignKey(
        'Flavor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Selected flavor for the cake'
    )
    
    # Keep old flavor_description field for backward compatibility and custom flavors
    flavor_description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Custom flavor description if not using predefined flavors'
    )
    
    # Custom flavor pricing (when customer types custom flavor instead of selecting)
    custom_flavor_price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Price per kg for custom flavor (set by admin if flavor not from list)'
    )
    
    # Decorations - removed M2M, now handled through CustomCakeOrderDecoration with quantities
    
    # Customization
    reference_image = models.ImageField(
        upload_to='custom_orders/references/', 
        blank=True, 
        null=True,
        help_text='Customer reference image (max 5MB)'
    )
    special_instructions = models.TextField(
        blank=True,
        help_text='Customer requirements, design details, color preferences, etc.'
    )
    custom_message = models.TextField(
        blank=True, 
        null=True,
        help_text='Message to write on cake'
    )
    
    # Event & Delivery
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_date = models.DateField()
    delivery_time = models.TimeField(blank=True, null=True)
    delivery_address = models.TextField()
    
    # Pricing
    estimated_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='Auto-calculated estimate shown to customer'
    )
    final_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Final price set by owner (may differ from estimate)'
    )
    price_note = models.TextField(
        blank=True,
        null=True,
        help_text='Explanation if final price differs from estimate'
    )
    
    # Status & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text='Internal notes for preparation')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Custom Cake Order'
        verbose_name_plural = 'Custom Cake Orders'
    
    def __str__(self):
        return f"Custom Order #{self.order_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Generate unique order number
        if not self.order_number:
            today = timezone.now()
            prefix = f"CSTM{today.strftime('%Y%m%d')}"
            last_order = CustomCakeOrder.objects.filter(
                order_number__startswith=prefix
            ).order_by('-order_number').first()
            if last_order:
                last_num = int(last_order.order_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_number = f"{prefix}{new_num:04d}"
        
        # Auto-calculate estimated price if not set
        if not self.estimated_price or self.estimated_price == 0:
            self.estimated_price = self.calculate_estimate()
        
        # Process reference image if uploaded
        if self.reference_image:
            self.reference_image = resize_and_optimize_image(self.reference_image, 1200, 1200, quality=85)
        
        super().save(*args, **kwargs)
    
    def calculate_estimate(self):
        """Auto-calculate estimated price"""
        from decimal import Decimal
        
        # Ensure total_weight is a Decimal
        if isinstance(self.total_weight, str):
            total_weight = Decimal(self.total_weight)
        else:
            total_weight = Decimal(str(self.total_weight))
        
        # Determine base price based on what customer selected
        # Always start with shape base price
        shape_cost = self.shape.base_price_per_kg * total_weight
        flavor_cost = Decimal('0.00')
        
        if self.product and self.size:
            # Customer selected existing product - use ProductPrice as flavor cost
            try:
                product_price = ProductPrice.objects.get(
                    product=self.product,
                    size=self.size
                )
                # ProductPrice is the FLAVOR/RECIPE cost, add it to shape cost
                flavor_cost = product_price.price
            except ProductPrice.DoesNotExist:
                # No product price found, flavor_cost remains 0
                flavor_cost = Decimal('0.00')
        else:
            # Customer built custom cake from scratch
            # Add flavor cost (per kg)
            if self.flavor:
                # Use predefined flavor price
                flavor_cost = self.flavor.price_per_kg * total_weight
            elif self.custom_flavor_price_per_kg:
                # Use admin-set custom flavor price - ensure it's Decimal
                custom_price = Decimal(str(self.custom_flavor_price_per_kg))
                flavor_cost = custom_price * total_weight
            # else: if neither set, flavor_cost remains 0 (admin needs to set price)
        
        # Subtotal before tier multiplier
        subtotal = shape_cost + flavor_cost
        
        # Apply tier multiplier
        tier_price = subtotal * self.tier.price_multiplier
        
        # Add decoration costs with quantities
        decoration_total = Decimal('0.00')
        if self.pk:  # Only if already saved (so we can access related decorations)
            decoration_total = sum(
                Decimal(str(order_dec.total_price)) 
                for order_dec in self.order_decorations.all()
            )
        
        # Total estimate
        total = tier_price + decoration_total
        
        return round(total, 2)
    
    def update_estimate(self):
        """Recalculate and update estimate"""
        self.estimated_price = self.calculate_estimate()
        self.save(update_fields=['estimated_price', 'updated_at'])
    
    @property
    def display_price(self):
        """Return final price if set, otherwise estimated price"""
        return self.final_price if self.final_price else self.estimated_price
    
    @property
    def price_range(self):
        """Calculate price range for display (round up to nearest 200, then +500)"""
        from decimal import Decimal
        import math
        
        base_estimate = self.estimated_price if self.estimated_price else self.calculate_estimate()
        
        # Round UP to nearest 200
        min_price = math.ceil(float(base_estimate) / 200) * 200
        
        # Max is min + 500
        max_price = min_price + 500
        
        return {
            'min': int(min_price),
            'max': int(max_price),
            'estimate': int(base_estimate)
        }
    
    @property
    def price_range_display(self):
        """Get formatted price range string"""
        range_data = self.price_range
        return f"₹{range_data['min']:,} - ₹{range_data['max']:,}"
    
    @property
    def price_breakdown(self):
        """Get detailed price breakdown for display"""
        from decimal import Decimal
        
        total_weight = self.total_weight if isinstance(self.total_weight, Decimal) else Decimal(str(self.total_weight))
        
        # Always calculate shape cost first
        shape_cost = self.shape.base_price_per_kg * total_weight
        flavor_cost = Decimal('0.00')
        flavor_source = "Not set"
        pricing_method = "shape_based"
        
        if self.product and self.size:
            # Customer selected existing product - use ProductPrice as flavor addon
            try:
                product_price = ProductPrice.objects.get(
                    product=self.product,
                    size=self.size
                )
                # ProductPrice is the flavor/recipe cost, added to shape cost
                flavor_cost = product_price.price
                flavor_source = f"{self.product.name} - {self.size.name} (Product)"
                pricing_method = "product_based"
            except ProductPrice.DoesNotExist:
                flavor_source = "Product price not found"
                flavor_cost = Decimal('0.00')
        else:
            # Custom build
            if self.flavor:
                flavor_cost = self.flavor.price_per_kg * total_weight
                flavor_source = f"{self.flavor.name} (₹{self.flavor.price_per_kg}/kg)"
            elif self.custom_flavor_price_per_kg:
                custom_price = Decimal(str(self.custom_flavor_price_per_kg))
                flavor_cost = custom_price * total_weight
                flavor_source = f"{self.flavor_description} (₹{custom_price}/kg)"
        
        subtotal = shape_cost + flavor_cost
        with_tier = subtotal * self.tier.price_multiplier
        
        decorations = Decimal('0.00')
        if self.pk:
            decorations = sum(
                Decimal(str(order_dec.total_price)) 
                for order_dec in self.order_decorations.all()
            )
        
        return {
            'shape': round(shape_cost, 2),
            'flavor': round(flavor_cost, 2),
            'flavor_source': flavor_source,
            'subtotal': round(subtotal, 2),
            'with_tier': round(with_tier, 2),
            'decorations': round(decorations, 2),
            'total': round(with_tier + decorations, 2),
            'pricing_method': pricing_method
        }


# ===========================
# 15. Gift Boxes
# ===========================

class GiftBox(models.Model):
    """Gift box that can contain multiple products"""
    PRICING_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('calculated', 'Sum of Items'),
        ('discounted', 'Sum with Discount'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    main_image = models.ImageField(
        upload_to='gift_boxes/',
        help_text='Image will be automatically resized to 500×281 pixels'
    )
    
    # Pricing options
    pricing_type = models.CharField(
        max_length=20, 
        choices=PRICING_TYPE_CHOICES, 
        default='calculated',
        help_text='How to calculate the price of this gift box'
    )
    fixed_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Fixed price (only for Fixed Price type)'
    )
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount % (only for Sum with Discount type)'
    )
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text='Order of display (lower numbers first)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = 'Gift Box'
        verbose_name_plural = 'Gift Boxes'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Process image if it's being uploaded/changed
        if self.main_image:
            width, height = get_image_dimensions_for_model('Product', 'main_image')
            self.main_image = resize_and_optimize_image(self.main_image, width, height)
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total price based on pricing type"""
        if self.pricing_type == 'fixed' and self.fixed_price:
            return self.fixed_price
        
        # Calculate sum of all items
        items_total = sum(item.subtotal for item in self.items.all())
        
        if self.pricing_type == 'discounted' and self.discount_percentage:
            discount_amount = items_total * (self.discount_percentage / 100)
            return items_total - discount_amount
        
        return items_total
    
    @property
    def items_count(self):
        """Get total count of items in the gift box"""
        return sum(item.quantity for item in self.items.all())


class GiftBoxItem(models.Model):
    """Individual items in a gift box"""
    gift_box = models.ForeignKey(GiftBox, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    size = models.ForeignKey(Size, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        default=1, 
        validators=[MinValueValidator(1)],
        help_text='Quantity of this product in the gift box'
    )
    display_order = models.IntegerField(default=0, help_text='Order of display')
    
    class Meta:
        unique_together = ['gift_box', 'product', 'size']
        ordering = ['display_order', 'product__name']
        verbose_name = 'Gift Box Item'
        verbose_name_plural = 'Gift Box Items'
    
    def __str__(self):
        return f"{self.quantity}× {self.product.name} ({self.size.name})"
    
    @property
    def unit_price(self):
        """Get price for this product-size combination"""
        try:
            product_price = ProductPrice.objects.get(product=self.product, size=self.size)
            return product_price.price
        except ProductPrice.DoesNotExist:
            return Decimal('0.00')
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.unit_price * self.quantity


class GiftBoxOrder(models.Model):
    """Orders for gift boxes"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup/Delivery'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='gift_box_orders')
    gift_box = models.ForeignKey(GiftBox, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    # Standard order fields
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateField()
    delivery_time = models.TimeField(blank=True, null=True)
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gift Box Order'
        verbose_name_plural = 'Gift Box Orders'
    
    def save(self, *args, **kwargs):
        # Generate unique order number
        if not self.order_number:
            today = timezone.now()
            prefix = f"GB{today.strftime('%Y%m%d')}"
            last_order = GiftBoxOrder.objects.filter(
                order_number__startswith=prefix
            ).order_by('-order_number').first()
            if last_order:
                last_num = int(last_order.order_number[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.order_number = f"{prefix}{new_num:04d}"
        
        # Set prices if not already set
        if not self.unit_price or self.unit_price == 0:
            self.unit_price = self.gift_box.total_price
        
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Gift Box Order #{self.order_number} - {self.customer.name}"


# ===========================
# 11. Loyalty & Rewards System
# ===========================

class LoyaltyCard(models.Model):
    """Customer loyalty card for tracking order stamps and rewards"""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]
    
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='loyalty_card')
    card_number = models.CharField(max_length=20, unique=True, editable=False)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    
    # Stamp Card System
    current_stamps = models.IntegerField(default=0, help_text='Current stamps collected (resets after reward)')
    total_stamps = models.IntegerField(default=0, help_text='Lifetime total stamps')
    stamps_to_reward = models.IntegerField(default=5, help_text='Stamps needed for next reward')
    
    # Points System
    points_balance = models.IntegerField(default=0, help_text='Current redeemable points')
    lifetime_points = models.IntegerField(default=0, help_text='Total points earned ever')
    
    # Statistics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rewards_claimed = models.IntegerField(default=0)
    referrals_made = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_stamps']
        verbose_name = 'Loyalty Card'
        verbose_name_plural = 'Loyalty Cards'
    
    def save(self, *args, **kwargs):
        if not self.card_number:
            # Generate unique card number: LC{YYYYMMDD}{XXX}
            today = timezone.now()
            prefix = f"LC{today.strftime('%Y%m%d')}"
            last_card = LoyaltyCard.objects.filter(card_number__startswith=prefix).order_by('-card_number').first()
            if last_card:
                last_num = int(last_card.card_number[-3:])
                new_num = last_num + 1
            else:
                new_num = 1
            self.card_number = f"{prefix}{new_num:03d}"
        
        # Auto-update tier based on lifetime orders
        if self.total_orders >= 50:
            self.tier = 'platinum'
        elif self.total_orders >= 25:
            self.tier = 'gold'
        elif self.total_orders >= 10:
            self.tier = 'silver'
        else:
            self.tier = 'bronze'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.customer.name} - {self.card_number} ({self.get_tier_display()})"
    
    @property
    def progress_percentage(self):
        """Calculate progress towards next reward"""
        if self.stamps_to_reward == 0:
            return 100
        return int((self.current_stamps / self.stamps_to_reward) * 100)
    
    @property
    def tier_benefits(self):
        """Get benefits for current tier"""
        benefits = {
            'bronze': {
                'discount': 5,
                'points_multiplier': 1.0,
                'birthday_bonus': 50,
                'free_delivery_threshold': 1000,
            },
            'silver': {
                'discount': 10,
                'points_multiplier': 1.5,
                'birthday_bonus': 100,
                'free_delivery_threshold': 800,
            },
            'gold': {
                'discount': 15,
                'points_multiplier': 2.0,
                'birthday_bonus': 150,
                'free_delivery_threshold': 500,
            },
            'platinum': {
                'discount': 20,
                'points_multiplier': 2.5,
                'birthday_bonus': 200,
                'free_delivery_threshold': 0,
            }
        }
        return benefits.get(self.tier, benefits['bronze'])
    
    def add_stamp(self):
        """Add a stamp and check if reward is earned"""
        self.current_stamps += 1
        self.total_stamps += 1
        
        if self.current_stamps >= self.stamps_to_reward:
            # Reward earned! Reset current stamps
            self.current_stamps = 0
            self.rewards_claimed += 1
            return True  # Reward earned
        return False  # No reward yet
    
    def add_points(self, points, reason=''):
        """Add points to customer's balance"""
        multiplier = self.tier_benefits['points_multiplier']
        bonus_points = int(points * multiplier)
        self.points_balance += bonus_points
        self.lifetime_points += bonus_points
        self.save()
        
        # Log the transaction
        PointsTransaction.objects.create(
            loyalty_card=self,
            points=bonus_points,
            transaction_type='earned',
            reason=reason
        )
        return bonus_points
    
    def redeem_points(self, points, reason=''):
        """Redeem points (deduct from balance)"""
        if self.points_balance >= points:
            self.points_balance -= points
            self.save()
            
            PointsTransaction.objects.create(
                loyalty_card=self,
                points=points,
                transaction_type='redeemed',
                reason=reason
            )
            return True
        return False


class LoyaltyReward(models.Model):
    """Rewards earned by customers"""
    REWARD_TYPE_CHOICES = [
        ('stamp_card', 'Stamp Card Completion'),
        ('birthday', 'Birthday Reward'),
        ('referral', 'Referral Bonus'),
        ('milestone', 'Milestone Achievement'),
        ('special', 'Special Promotion'),
        ('points', 'Points Redemption'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='rewards')
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPE_CHOICES)
    
    # Reward Details
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text='Discount percentage (e.g., 10.00 for 10%)'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Fixed discount amount (if applicable)'
    )
    
    # Validity
    issued_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Usage
    used_on_order = models.ForeignKey(
        'Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reward_used'
    )
    used_date = models.DateTimeField(null=True, blank=True)
    
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-issued_date']
        verbose_name = 'Loyalty Reward'
        verbose_name_plural = 'Loyalty Rewards'
    
    def __str__(self):
        return f"{self.loyalty_card.customer.name} - {self.get_reward_type_display()} ({self.discount_percentage}%)"
    
    def is_valid(self):
        """Check if reward is still valid"""
        from django.utils import timezone
        if self.status != 'active':
            return False
        if self.expiry_date < timezone.now().date():
            self.status = 'expired'
            self.save()
            return False
        return True


class PointsTransaction(models.Model):
    """Log of all points transactions"""
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('adjusted', 'Manual Adjustment'),
    ]
    
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='transactions')
    points = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reason = models.CharField(max_length=255)
    
    # Related objects
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Points Transaction'
        verbose_name_plural = 'Points Transactions'
    
    def __str__(self):
        sign = '+' if self.transaction_type == 'earned' else '-'
        return f"{self.loyalty_card.customer.name}: {sign}{self.points} pts - {self.reason}"


class Referral(models.Model):
    """Track customer referrals"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rewarded', 'Rewarded'),
    ]
    
    referrer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='referrals_made'
    )
    referred_customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='referred_by',
        null=True,
        blank=True
    )
    
    # Referral details
    referred_phone = models.CharField(max_length=15)
    referred_name = models.CharField(max_length=200, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, editable=False)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Rewards
    referrer_reward_points = models.IntegerField(default=100)
    referred_reward_discount = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            # Generate unique referral code
            import random
            import string
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Referral.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.referrer.name} → {self.referred_name or self.referred_phone} ({self.status})"
    
    def mark_completed(self):
        """Mark referral as completed and award rewards"""
        if self.status == 'pending':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            
            # Award points to referrer
            if hasattr(self.referrer, 'loyalty_card'):
                self.referrer.loyalty_card.add_points(
                    self.referrer_reward_points,
                    f'Referral bonus for {self.referred_name or self.referred_phone}'
                )
                self.referrer.loyalty_card.referrals_made += 1
                self.referrer.loyalty_card.save()


class Achievement(models.Model):
    """Gamification achievements/badges"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text='Font Awesome icon class (e.g., fa-trophy)')
    
    # Unlock criteria
    criteria_type = models.CharField(max_length=50, choices=[
        ('orders', 'Total Orders'),
        ('spent', 'Total Amount Spent'),
        ('referrals', 'Referrals Made'),
        ('reviews', 'Reviews Given'),
        ('stamps', 'Stamps Collected'),
    ])
    criteria_value = models.IntegerField(help_text='Value needed to unlock')
    
    # Reward
    points_reward = models.IntegerField(default=0)
    
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'criteria_value']
        verbose_name = 'Achievement'
        verbose_name_plural = 'Achievements'
    
    def __str__(self):
        return f"{self.name} - {self.criteria_value} {self.criteria_type}"


class CustomerAchievement(models.Model):
    """Track which achievements customers have unlocked"""
    loyalty_card = models.ForeignKey(LoyaltyCard, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['loyalty_card', 'achievement']
        ordering = ['-unlocked_at']
        verbose_name = 'Customer Achievement'
        verbose_name_plural = 'Customer Achievements'
    
    def __str__(self):
        return f"{self.loyalty_card.customer.name} - {self.achievement.name}"