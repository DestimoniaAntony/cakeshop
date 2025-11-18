"""
URL configuration for cakeshop_app (Customer-facing)
"""
from django.urls import path
from . import views
from django.views.static import serve
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # About
    path('about/', views.about, name='about'),
    # Products
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    
    # Orders
    path('track/custom-order/<str:order_number>/', views.custom_order_detail_customer, name='custom_order_detail_customer'),

    path('order/', views.place_order, name='place_order'),
    path('order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('track/', views.track_order, name='track_order'),
    path('order/<int:order_id>/detail/', views.order_detail_customer_by_id, name='order_detail_customer_by_id'),
    path('order/<str:order_number>/detail/', views.order_detail_customer, name='order_detail_customer'),
    
    # Custom Cakes
    path('custom-cakes/', views.custom_cakes, name='custom_cakes'),
    path('custom-order/place/', views.place_custom_order, name='place_custom_order'),
    path('custom-order/<str:order_number>/confirmation/', views.custom_order_confirmation, name='custom_order_confirmation'),
    
    # PDF Generation
    path('order/<str:order_number>/pdf/', views.generate_order_pdf, name='generate_order_pdf'),
    path('custom-order/<str:order_number>/pdf/', views.generate_custom_cake_pdf, name='generate_custom_cake_pdf'),
    
    # Gallery
    path('gallery/', views.gallery, name='gallery'),
    
    # Contact
    path('contact/', views.contact, name='contact'),
    
    # Reviews
    path('review/submit/', views.submit_review, name='submit_review'),
    
    # About
    path('about/', views.about, name='about'),
    
    # Search
    path('search/', views.search, name='search'),
    
    # Gift Boxes
    path('gift-boxes/', views.gift_boxes, name='gift_boxes'),
    path('gift-boxes/<int:gift_box_id>/', views.gift_box_detail, name='gift_box_detail'),
    path('gift-boxes/<int:gift_box_id>/order/', views.gift_box_order, name='gift_box_order'),
    path('gift-box-order/<str:order_number>/confirmation/', views.gift_box_order_confirmation, name='gift_box_order_confirmation'),
    
    # AJAX APIs
    path('api/product-details/', views.get_product_details_ajax, name='get_product_details_ajax'),
    path('api/event-suggestions/', views.get_event_suggestions_ajax, name='get_event_suggestions_ajax'),
    path('api/calculate-price/', views.calculate_price_ajax, name='calculate_price_ajax'),
    path('api/product-sizes-prices/', views.get_product_sizes_prices, name='get_product_sizes_prices'),

    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/checkout/', views.checkout_submit, name='checkout_submit'),
    path('cart/add-custom/', views.add_custom_to_cart, name='add_custom_to_cart'),
    
    # Loyalty & Rewards
    path('loyalty/', views.loyalty_dashboard, name='loyalty_dashboard'),
    path('loyalty/rewards/', views.my_rewards, name='my_rewards'),
    path('loyalty/referral/', views.referral_program, name='referral_program'),
    path('loyalty/create-referral/', views.create_referral, name='create_referral'),
    path('loyalty/history/', views.loyalty_history, name='loyalty_history'),
    path('loyalty/redeem/points/', views.set_points_redemption, name='set_points_redemption'),
    path('loyalty/apply/reward/', views.set_reward_selection, name='set_reward_selection'),
    path('loyalty/clear-selection/', views.clear_loyalty_selection, name='clear_loyalty_selection'),

    # Auth (Customer)
    path('login/', views.login_view, name='customer_login'),
    path('logout/', views.logout_view, name='customer_logout'),

    # Admin auth (custom form authenticating against Django auth User)
    path('admin/signin/', views.admin_login_view, name='admin_login'),
    path('admin/signout/', views.admin_logout_view, name='admin_logout'),

    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]
