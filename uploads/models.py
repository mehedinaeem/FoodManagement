from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


def upload_to(instance, filename):
    """
    Generate upload path for images.
    """
    import os
    from django.utils import timezone
    
    # Get file extension
    ext = filename.split('.')[-1]
    # Generate unique filename with timestamp
    filename = f"{instance.user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return f"uploads/{instance.user.id}/{filename}"


class Upload(models.Model):
    """
    Model for storing uploaded images (receipts, food labels, etc.).
    """
    UPLOAD_TYPE_CHOICES = [
        ('receipt', 'Receipt'),
        ('food_label', 'Food Label'),
        ('barcode', 'Barcode'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    image = models.ImageField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Upload JPG or PNG image (max 10MB)"
    )
    upload_type = models.CharField(
        max_length=20,
        choices=UPLOAD_TYPE_CHOICES,
        default='other',
        help_text="Type of upload"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional title for the upload"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description"
    )
    # Associations with inventory or logs
    associated_inventory = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploads',
        help_text="Associated inventory item (if any)"
    )
    associated_log = models.ForeignKey(
        'logs.FoodLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploads',
        help_text="Associated food log (if any)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['upload_type']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Untitled'} - {self.get_upload_type_display()}"
    
    def get_file_size(self):
        """Get human-readable file size."""
        try:
            size = self.image.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"
        except:
            return "Unknown"
    
    def get_file_extension(self):
        """Get file extension."""
        if self.image:
            return self.image.name.split('.')[-1].upper()
        return ""
