"""
Custom widgets for admin forms with image cropping functionality
"""
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe


class ImageCropWidget(forms.ClearableFileInput):
    """
    Custom widget that provides image cropping interface
    using Cropper.js library
    """
    
    template_name = 'admin/widgets/image_crop_widget.html'
    
    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.css',
                'admin/css/image-crop-widget.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.1/cropper.min.js',
            'admin/js/image-crop-widget.js',
        )
    
    def __init__(self, attrs=None, aspect_ratio=None, target_width=None, target_height=None):
        """
        Initialize widget with cropping parameters
        
        Args:
            aspect_ratio: Aspect ratio for crop box (e.g., 16/9, 1, 2/1)
            target_width: Target width in pixels
            target_height: Target height in pixels
        """
        super().__init__(attrs)
        self.aspect_ratio = aspect_ratio or 16/9
        self.target_width = target_width or 500
        self.target_height = target_height or 281
        
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget with crop interface"""
        html = super().render(name, value, attrs, renderer)
        
        # Add crop interface HTML
        crop_html = f'''
        <div class="image-crop-container" style="margin-top: 15px;">
            <input type="hidden" id="id_{name}_crop_data" name="{name}_crop_data" value="">
            <input type="hidden" id="id_{name}_aspect_ratio" value="{self.aspect_ratio}">
            <input type="hidden" id="id_{name}_target_width" value="{self.target_width}">
            <input type="hidden" id="id_{name}_target_height" value="{self.target_height}">
            
            <div class="crop-preview-section" style="display:none; margin-top: 20px;">
                <h3 style="color: #333; margin-bottom: 10px;">
                    📐 Crop Your Image - Drag to Select Area
                </h3>
                <p style="color: #666; margin-bottom: 15px;">
                    Target size: {self.target_width}×{self.target_height} pixels | 
                    Aspect ratio: {self.aspect_ratio:.2f}
                </p>
                
                <div class="crop-actions" style="margin-bottom: 15px;">
                    <button type="button" class="btn-crop-apply" 
                            style="background: #28a745; color: white; padding: 10px 20px; 
                                   border: none; border-radius: 4px; cursor: pointer; 
                                   font-weight: bold; margin-right: 10px;">
                        ✓ Apply Crop
                    </button>
                    <button type="button" class="btn-crop-reset" 
                            style="background: #6c757d; color: white; padding: 10px 20px; 
                                   border: none; border-radius: 4px; cursor: pointer;">
                        ↺ Reset
                    </button>
                    <button type="button" class="btn-crop-cancel" 
                            style="background: #dc3545; color: white; padding: 10px 20px; 
                                   border: none; border-radius: 4px; cursor: pointer; margin-left: 10px;">
                        ✕ Cancel
                    </button>
                </div>
                
                <div class="crop-image-wrapper" style="max-width: 100%; max-height: 600px; overflow: hidden; 
                                                       background: #f5f5f5; border: 2px solid #ddd; 
                                                       border-radius: 8px; position: relative;">
                    <img id="crop-image-{name}" style="max-width: 100%; display: block;">
                </div>
                
                <div class="crop-info" style="margin-top: 15px; padding: 15px; 
                                               background: #f8f9fa; border-radius: 4px; 
                                               border-left: 4px solid #007bff;">
                    <p style="margin: 0; color: #333; font-size: 14px;">
                        <strong>Instructions:</strong><br>
                        • Drag the corners to resize the crop area<br>
                        • Drag inside the box to move it<br>
                        • Scroll to zoom in/out<br>
                        • Click "Apply Crop" when done
                    </p>
                </div>
                
                <div class="crop-preview-result" style="margin-top: 20px; display: none;">
                    <h4 style="color: #333; margin-bottom: 10px;">Preview (Final Result):</h4>
                    <div style="border: 2px solid #28a745; border-radius: 8px; padding: 10px; 
                                display: inline-block; background: white;">
                        <img id="crop-preview-{name}" style="max-width: {self.target_width}px; 
                                                              max-height: {self.target_height}px;">
                    </div>
                    <p style="color: #28a745; margin-top: 10px;">
                        ✓ Crop applied! This is how your image will appear.
                    </p>
                </div>
            </div>
        </div>
        '''
        
        return mark_safe(html + crop_html)

