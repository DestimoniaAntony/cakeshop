"""
URL configuration for admin_app
"""
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('index/', views.index, name='index'),  # Legacy

    # Orders
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/pending/', views.admin_orders_pending, name='admin_orders_pending'),
    path('orders/confirmed/', views.admin_orders_confirmed, name='admin_orders_confirmed'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('orders/<int:order_id>/pdf/', views.admin_order_generate_pdf, name='admin_order_generate_pdf'),
    
    # Customers
    path('customers/', views.admin_customers, name='admin_customers'),
    path('customers/<int:customer_id>/', views.admin_customer_detail, name='admin_customer_detail'),
    
    # Products
    path('products/', views.admin_products, name='admin_products'),
    path('products/add/', views.admin_product_add, name='admin_product_add'),
    path('products/<int:product_id>/edit/', views.admin_product_edit, name='admin_product_edit'),
    path('products/<int:product_id>/delete/', views.admin_product_delete, name='admin_product_delete'),
    
    # Categories
    path('categories/', views.admin_categories, name='admin_categories'),
    path('categories/add/', views.admin_category_add, name='admin_category_add'),
    path('categories/<int:category_id>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('categories/<int:category_id>/delete/', views.admin_category_delete, name='admin_category_delete'),
    
    # Subcategories
    path('subcategories/', views.admin_subcategories, name='admin_subcategories'),
    path('subcategories/add/', views.admin_subcategory_add, name='admin_subcategory_add'),
    path('subcategories/<int:subcategory_id>/edit/', views.admin_subcategory_edit, name='admin_subcategory_edit'),
    path('subcategories/<int:subcategory_id>/delete/', views.admin_subcategory_delete, name='admin_subcategory_delete'),
    
    # Flavors
    path('flavors/', views.admin_flavors, name='admin_flavors'),
    path('flavors/add/', views.admin_flavor_add, name='admin_flavor_add'),
    path('flavors/<int:flavor_id>/edit/', views.admin_flavor_edit, name='admin_flavor_edit'),
    path('flavors/<int:flavor_id>/delete/', views.admin_flavor_delete, name='admin_flavor_delete'),
    
    # Sizes
    path('sizes/', views.admin_sizes, name='admin_sizes'),
    path('sizes/add/', views.admin_size_add, name='admin_size_add'),
    path('sizes/<int:size_id>/edit/', views.admin_size_edit, name='admin_size_edit'),
    path('sizes/<int:size_id>/delete/', views.admin_size_delete, name='admin_size_delete'),
    
    # Inventory / Ingredients
    path('ingredients/', views.admin_ingredients, name='admin_ingredients'),
    path('ingredients/add/', views.admin_ingredient_add, name='admin_ingredient_add'),
    path('ingredients/<int:ingredient_id>/edit/', views.admin_ingredient_edit, name='admin_ingredient_edit'),
    path('ingredients/<int:ingredient_id>/delete/', views.admin_ingredient_delete, name='admin_ingredient_delete'),
    path('ingredients/<int:ingredient_id>/update-quantity/', views.admin_ingredient_update_quantity, name='admin_ingredient_update_quantity'),
    
    # Purchase Bills / Expenses
    path('purchase-bills/', views.admin_purchase_bills, name='admin_purchase_bills'),
    path('purchase-bills/add/', views.admin_purchase_bill_add, name='admin_purchase_bill_add'),
    path('purchase-bills/<int:bill_id>/edit/', views.admin_purchase_bill_edit, name='admin_purchase_bill_edit'),
    path('purchase-bills/<int:bill_id>/delete/', views.admin_purchase_bill_delete, name='admin_purchase_bill_delete'),
    
    # Events
    path('events/', views.admin_events, name='admin_events'),
    path('events/add/', views.admin_event_add, name='admin_event_add'),
    path('events/<int:event_id>/edit/', views.admin_event_edit, name='admin_event_edit'),
    path('events/<int:event_id>/delete/', views.admin_event_delete, name='admin_event_delete'),
    
    # Enquiries
    path('enquiries/', views.admin_enquiries, name='admin_enquiries'),
    path('enquiries/<int:enquiry_id>/', views.admin_enquiry_detail, name='admin_enquiry_detail'),
    path('enquiries/<int:enquiry_id>/delete/', views.admin_enquiry_delete, name='admin_enquiry_delete'),
    
    # Gallery
    path('gallery/', views.admin_gallery, name='admin_gallery'),
    path('gallery/add/', views.admin_gallery_add, name='admin_gallery_add'),
    path('gallery/<int:image_id>/edit/', views.admin_gallery_edit, name='admin_gallery_edit'),
    path('gallery/<int:image_id>/delete/', views.admin_gallery_delete, name='admin_gallery_delete'),
    
    # Reviews
    path('reviews/', views.admin_reviews, name='admin_reviews'),
    path('reviews/<int:review_id>/approve/', views.admin_review_approve, name='admin_review_approve'),
    path('reviews/<int:review_id>/delete/', views.admin_review_delete, name='admin_review_delete'),
    
    # Homepage Carousel
    path('carousel/', views.admin_carousel, name='admin_carousel'),
    path('carousel/add/', views.admin_carousel_add, name='admin_carousel_add'),
    path('carousel/<int:slide_id>/edit/', views.admin_carousel_edit, name='admin_carousel_edit'),
    path('carousel/<int:slide_id>/delete/', views.admin_carousel_delete, name='admin_carousel_delete'),
    
    # Promotional Offers
    path('offers/', views.admin_offers, name='admin_offers'),
    path('offers/add/', views.admin_offer_add, name='admin_offer_add'),
    path('offers/<int:offer_id>/edit/', views.admin_offer_edit, name='admin_offer_edit'),
    path('offers/<int:offer_id>/delete/', views.admin_offer_delete, name='admin_offer_delete'),

    # Page Title Banners
    path('page-banners/', views.admin_page_banners, name='admin_page_banners'),
    path('page-banners/add/', views.admin_page_banner_add, name='admin_page_banner_add'),
    path('page-banners/edit/<int:banner_id>/', views.admin_page_banner_edit, name='admin_page_banner_edit'),
    path('page-banners/delete/<int:banner_id>/', views.admin_page_banner_delete, name='admin_page_banner_delete'),
    
    # Reports
    path('reports/sales/', views.admin_sales_report, name='admin_sales_report'),
    path('reports/expenses/', views.admin_expense_report, name='admin_expense_report'),
    
    # Custom Cake Builder
    path('custom-orders/', views.admin_custom_orders, name='admin_custom_orders'),
    path('custom-orders/<int:order_id>/', views.admin_custom_order_detail, name='admin_custom_order_detail'),
    path('custom-orders/<int:order_id>/edit/', views.admin_custom_order_edit, name='admin_custom_order_edit'),
    path('cake-shapes/', views.admin_cake_shapes, name='admin_cake_shapes'),
    path('cake-shapes/add/', views.admin_cake_shape_add, name='admin_cake_shape_add'),
    path('cake-shapes/<int:shape_id>/edit/', views.admin_cake_shape_edit, name='admin_cake_shape_edit'),
    path('cake-shapes/<int:shape_id>/delete/', views.admin_cake_shape_delete, name='admin_cake_shape_delete'),
    path('cake-tiers/', views.admin_cake_tiers, name='admin_cake_tiers'),
    path('cake-tiers/add/', views.admin_cake_tier_add, name='admin_cake_tier_add'),
    path('cake-tiers/<int:tier_id>/edit/', views.admin_cake_tier_edit, name='admin_cake_tier_edit'),
    path('cake-tiers/<int:tier_id>/delete/', views.admin_cake_tier_delete, name='admin_cake_tier_delete'),
    path('decorations/', views.admin_decorations, name='admin_decorations'),
    path('decorations/add/', views.admin_decoration_add, name='admin_decoration_add'),
    path('decorations/<int:decoration_id>/edit/', views.admin_decoration_edit, name='admin_decoration_edit'),
    path('decorations/<int:decoration_id>/delete/', views.admin_decoration_delete, name='admin_decoration_delete'),
    
    # Gift Boxes
    path('gift-boxes/', views.admin_gift_boxes, name='admin_gift_boxes'),
    path('gift-boxes/add/', views.admin_gift_box_add, name='admin_gift_box_add'),
    path('gift-boxes/<int:gift_box_id>/edit/', views.admin_gift_box_edit, name='admin_gift_box_edit'),
    path('gift-boxes/<int:gift_box_id>/delete/', views.admin_gift_box_delete, name='admin_gift_box_delete'),
    path('gift-boxes/<int:gift_box_id>/add-item/', views.admin_gift_box_add_item, name='admin_gift_box_add_item'),
    path('gift-boxes/items/<int:item_id>/remove/', views.admin_gift_box_remove_item, name='admin_gift_box_remove_item'),
    
    # Gift Box Orders
    path('gift-box-orders/', views.admin_gift_box_orders, name='admin_gift_box_orders'),
    path('gift-boxes/orders/<int:order_id>/', views.admin_gift_box_order_detail, name='admin_gift_box_order_detail'),
    path('gift-boxes/orders/<int:order_id>/accept/', views.admin_accept_gift_box_order, name='admin_accept_gift_box_order'),
    path('gift-boxes/orders/<int:order_id>/delete/', views.admin_delete_gift_box_order, name='admin_delete_gift_box_order'),
    
    # AJAX APIs
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('api/sizes/', views.get_sizes_for_category, name='get_sizes_for_category'),
    path('api/event-suggestions/', views.get_event_suggestions, name='get_event_suggestions'),
    path('api/product-sizes-prices/', views.get_product_sizes_prices, name='get_product_sizes_prices'),
    
    # Gift Box AJAX APIs
    path('api/gift-box/products/', views.get_products_by_category, name='get_products_by_category'),
    path('api/gift-box/sizes/', views.get_sizes_for_product, name='get_sizes_for_product'),
    path('api/gift-box/create-product/', views.create_product_inline, name='create_product_inline'),
    path('api/gift-box/create-size-price/', views.create_product_size_price, name='create_product_size_price'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
