/**
 * Image Crop Widget - Using Cropper.js
 * Provides drag-and-crop interface for image uploads
 */

(function() {
    'use strict';
    
    let croppers = {};
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCropWidgets);
    } else {
        initializeCropWidgets();
    }
    
    function initializeCropWidgets() {
        // Find all file inputs that need crop functionality
        const fileInputs = document.querySelectorAll('input[type="file"][name*="image"], input[type="file"][name*="main_image"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', handleFileSelect);
        });
    }
    
    function handleFileSelect(event) {
        const input = event.target;
        const file = input.files[0];
        
        if (!file || !file.type.startsWith('image/')) {
            return;
        }
        
        const name = input.name;
        const container = input.closest('.form-row, .field-main_image, .field-image') || input.parentElement;
        const cropSection = container.querySelector('.crop-preview-section');
        const cropImage = container.querySelector(`#crop-image-${name}`);
        const cropDataInput = container.querySelector(`#id_${name}_crop_data`);
        const aspectRatioInput = container.querySelector(`#id_${name}_aspect_ratio`);
        const targetWidthInput = container.querySelector(`#id_${name}_target_width`);
        const targetHeightInput = container.querySelector(`#id_${name}_target_height`);
        
        if (!cropSection || !cropImage) {
            console.warn('Crop elements not found for', name);
            return;
        }
        
        // Read the file
        const reader = new FileReader();
        reader.onload = function(e) {
            // Show crop section
            cropSection.style.display = 'block';
            
            // Set image source
            cropImage.src = e.target.result;
            
            // Destroy existing cropper if any
            if (croppers[name]) {
                croppers[name].destroy();
            }
            
            // Get aspect ratio and target dimensions
            const aspectRatio = parseFloat(aspectRatioInput?.value || 16/9);
            const targetWidth = parseInt(targetWidthInput?.value || 500);
            const targetHeight = parseInt(targetHeightInput?.value || 281);
            
            // Initialize Cropper.js
            croppers[name] = new Cropper(cropImage, {
                aspectRatio: aspectRatio,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: true,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
                minContainerWidth: 200,
                minContainerHeight: 200,
                ready: function() {
                    console.log('Cropper initialized for', name);
                }
            });
            
            // Setup button handlers
            setupCropButtons(name, container, cropDataInput, targetWidth, targetHeight);
        };
        
        reader.readAsDataURL(file);
    }
    
    function setupCropButtons(name, container, cropDataInput, targetWidth, targetHeight) {
        const applyBtn = container.querySelector('.btn-crop-apply');
        const resetBtn = container.querySelector('.btn-crop-reset');
        const cancelBtn = container.querySelector('.btn-crop-cancel');
        const previewResult = container.querySelector('.crop-preview-result');
        const previewImage = container.querySelector(`#crop-preview-${name}`);
        
        // Apply crop button
        if (applyBtn) {
            applyBtn.onclick = function() {
                const cropper = croppers[name];
                if (!cropper) return;
                
                // Get crop data
                const cropData = cropper.getData(true);
                
                // Store crop data
                if (cropDataInput) {
                    cropDataInput.value = JSON.stringify(cropData);
                }
                
                // Get cropped canvas
                const canvas = cropper.getCroppedCanvas({
                    width: targetWidth,
                    height: targetHeight,
                    imageSmoothingEnabled: true,
                    imageSmoothingQuality: 'high',
                });
                
                // Show preview
                if (previewImage && canvas) {
                    canvas.toBlob(function(blob) {
                        const url = URL.createObjectURL(blob);
                        previewImage.src = url;
                        
                        // Show preview section
                        if (previewResult) {
                            previewResult.style.display = 'block';
                        }
                        
                        // Convert blob to file and update input
                        const file = new File([blob], 'cropped-image.jpg', { 
                            type: 'image/jpeg' 
                        });
                        
                        // Create a DataTransfer to update the file input
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        const fileInput = container.querySelector('input[type="file"]');
                        if (fileInput) {
                            fileInput.files = dataTransfer.files;
                        }
                        
                        // Show success message
                        showMessage(container, 'Crop applied successfully! ✓', 'success');
                    }, 'image/jpeg', 0.9);
                }
            };
        }
        
        // Reset button
        if (resetBtn) {
            resetBtn.onclick = function() {
                const cropper = croppers[name];
                if (cropper) {
                    cropper.reset();
                    showMessage(container, 'Crop reset', 'info');
                }
            };
        }
        
        // Cancel button
        if (cancelBtn) {
            cancelBtn.onclick = function() {
                const cropper = croppers[name];
                if (cropper) {
                    cropper.destroy();
                    delete croppers[name];
                }
                
                // Hide crop section
                const cropSection = container.querySelector('.crop-preview-section');
                if (cropSection) {
                    cropSection.style.display = 'none';
                }
                
                // Clear file input
                const fileInput = container.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.value = '';
                }
                
                // Hide preview
                if (previewResult) {
                    previewResult.style.display = 'none';
                }
                
                showMessage(container, 'Crop cancelled', 'info');
            };
        }
    }
    
    function showMessage(container, message, type) {
        // Remove existing messages
        const existingMsg = container.querySelector('.crop-message');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        // Create message element
        const msgDiv = document.createElement('div');
        msgDiv.className = 'crop-message';
        msgDiv.textContent = message;
        
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8'
        };
        
        msgDiv.style.cssText = `
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
            background: ${colors[type] || colors.info};
            color: white;
            font-weight: bold;
            animation: fadeIn 0.3s ease-in;
        `;
        
        // Insert message
        const cropSection = container.querySelector('.crop-preview-section');
        if (cropSection) {
            cropSection.insertBefore(msgDiv, cropSection.firstChild);
        }
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            msgDiv.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => msgDiv.remove(), 300);
        }, 3000);
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        Object.keys(croppers).forEach(name => {
            if (croppers[name]) {
                croppers[name].destroy();
            }
        });
    });
    
})();

