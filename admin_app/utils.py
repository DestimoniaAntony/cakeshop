"""
Utility functions for image processing and optimization
"""
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def resize_and_optimize_image(image_field, target_width, target_height, quality=85):
    """
    Resize and optimize an uploaded image to target dimensions
    
    Args:
        image_field: Django ImageField object
        target_width: Target width in pixels
        target_height: Target height in pixels
        quality: JPEG quality (1-100, default 85)
    
    Returns:
        InMemoryUploadedFile: Optimized image ready for saving
    """
    if not image_field:
        return None
    
    try:
        # Open the image
        img = Image.open(image_field)
        
        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate aspect ratios
        original_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        # Smart crop to maintain aspect ratio
        if original_ratio > target_ratio:
            # Image is wider than target - crop width
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        elif original_ratio < target_ratio:
            # Image is taller than target - crop height
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Resize to target dimensions
        img = img.resize((target_width, target_height), Image.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Create a new InMemoryUploadedFile
        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image_field.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return image_field  # Return original if processing fails


def get_image_dimensions_for_model(model_name, field_name):
    """
    Get recommended dimensions for different image types
    
    Returns:
        tuple: (width, height)
    """
    dimensions = {
        'Product': {'main_image': (800, 800)},  # Square aspect ratio for products
        'ProductImage': {'image': (800, 800)},  # Square aspect ratio for additional product images
        'Category': {'image': (500, 281)},
        'Subcategory': {'image': (500, 281)},
        'Gallery': {'image': (800, 800)},  # Square aspect ratio for gallery
        'CarouselSlide': {'image': (1920, 1080)},
        'OfferBanner': {'image': (800, 400)},
    }
    
    return dimensions.get(model_name, {}).get(field_name, (800, 600))

