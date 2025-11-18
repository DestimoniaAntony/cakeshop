"""Utility functions for the cakeshop app."""
import random
import string
from datetime import datetime, timedelta
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    """Generate a numeric OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def store_otp(phone, email, otp):
    """Store OTP in cache with 5-minute expiry."""
    cache_key = f"otp_{phone}"
    cache.set(cache_key, {
        'otp': otp,
        'email': email,
        'created_at': datetime.now().isoformat()
    }, timeout=300)  # 5 minutes

def verify_otp(phone, entered_otp):
    """Verify the OTP for given phone number."""
    cache_key = f"otp_{phone}"
    stored_data = cache.get(cache_key)
    
    if not stored_data:
        return False, "OTP has expired. Please request a new one."
    
    if stored_data['otp'] != entered_otp:
        return False, "Invalid OTP. Please try again."
    
    # Clear the OTP after successful verification
    cache.delete(cache_key)
    return True, stored_data.get('email', '')

def send_otp_email(email, otp):
    """Send OTP via email."""
    subject = 'Your OTP for Cakes by Desti'
    message = f'''
    Hello!
    
    Your OTP for Cakes by Desti is: {otp}
    
    This OTP will expire in 5 minutes.
    If you didn't request this OTP, please ignore this email.
    
    Best regards,
    Cakes by Desti Team
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False