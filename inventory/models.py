from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class FoodItem(models.Model):
    """
    Reference database of common food items with their properties.
    This is a seeded database, not user-specific inventory.
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
        ('spice', 'Spice'),
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
        ('bunch', 'Bunch'),
    ]
    
    name = models.CharField(max_length=255, unique=True, help_text="Name of the food item")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, help_text="Food category")
    typical_expiration_days = models.PositiveIntegerField(
        help_text="Typical expiration period in days",
        null=True,
        blank=True
    )
    sample_cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Sample cost per unit (for reference)",
        null=True,
        blank=True
    )
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece', help_text="Unit of measurement")
    description = models.TextField(blank=True, null=True, help_text="Description of the food item")
    storage_tips = models.TextField(blank=True, null=True, help_text="Tips for storing this item")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Item"
        verbose_name_plural = "Food Items"
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def get_expiration_info(self):
        """Get human-readable expiration information."""
        if self.typical_expiration_days:
            if self.typical_expiration_days < 7:
                return f"{self.typical_expiration_days} days (Short-term)"
            elif self.typical_expiration_days < 30:
                return f"{self.typical_expiration_days} days (~{self.typical_expiration_days // 7} weeks)"
            else:
                return f"{self.typical_expiration_days} days (~{self.typical_expiration_days // 30} months)"
        return "Not specified"


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
