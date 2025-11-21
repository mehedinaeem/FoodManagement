from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class FoodLog(models.Model):
    """
    Model for logging daily food consumption.
    """
    CATEGORY_CHOICES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('dairy', 'Dairy'),
        ('meat', 'Meat'),
        ('grain', 'Grain'),
        ('beverage', 'Beverage'),
        ('snack', 'Snack'),
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
        ('serving', 'Serving'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    item_name = models.CharField(max_length=255, help_text="Name of the food item")
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text="Quantity consumed"
    )
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    date_consumed = models.DateField(help_text="Date when the food was consumed")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the consumption")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Food Log"
        verbose_name_plural = "Food Logs"
        ordering = ['-date_consumed', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date_consumed']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit} on {self.date_consumed}"
