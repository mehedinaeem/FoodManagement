from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class InventoryItem(models.Model):
    """
    Model for managing user's food inventory.
    """
    CATEGORY_CHOICES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('dairy', 'Dairy'),
        ('meat', 'Meat'),
        ('grain', 'Grain'),
        ('beverage', 'Beverage'),
        ('snack', 'Snack'),
        ('frozen', 'Frozen'),
        ('canned', 'Canned'),
        ('other', 'Other'),
    ]
    
    UNIT_CHOICES = [
        ('kg', 'Kilogram (kg)'),
        ('g', 'Gram (g)'),
        ('lb', 'Pound (lb)'),
        ('oz', 'Ounce (oz)'),
        ('l', 'Liter (l)'),
        ('ml', 'Milliliter (ml)'),
        ('cup', 'Cup'),
        ('piece', 'Piece'),
        ('pack', 'Pack'),
    ]
    
    STATUS_CHOICES = [
        ('fresh', 'Fresh'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('consumed', 'Consumed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')
    item_name = models.CharField(max_length=255, help_text="Name of the food item")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Current quantity"
    )
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    purchase_date = models.DateField(help_text="Date when the item was purchased")
    expiration_date = models.DateField(
        blank=True, 
        null=True, 
        help_text="Expected expiration date (optional)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='fresh')
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Inventory Item"
        verbose_name_plural = "Inventory Items"
        ordering = ['expiration_date', 'item_name']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit}"
    
    def is_expiring_soon(self):
        """Check if item is expiring within 3 days."""
        if self.expiration_date:
            days_until_expiry = (self.expiration_date - timezone.now().date()).days
            return 0 <= days_until_expiry <= 3
        return False
    
    def is_expired(self):
        """Check if item has expired."""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    def update_status(self):
        """Update status based on expiration date."""
        if self.is_expired():
            self.status = 'expired'
        elif self.is_expiring_soon():
            self.status = 'expiring_soon'
        elif self.status != 'consumed':
            self.status = 'fresh'
        self.save()
