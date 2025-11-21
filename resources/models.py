from django.db import models


class Resource(models.Model):
    """
    Model for storing resources related to sustainable food practices,
    waste reduction, and nutrition tips.
    """
    CATEGORY_CHOICES = [
        ('waste_reduction', 'Waste Reduction'),
        ('budget_tips', 'Budget Tips'),
        ('meal_planning', 'Meal Planning'),
        ('storage_tips', 'Storage Tips'),
        ('nutrition', 'Nutrition'),
        ('sustainability', 'Sustainability'),
        ('cooking_tips', 'Cooking Tips'),
        ('preservation', 'Food Preservation'),
        ('shopping', 'Smart Shopping'),
        ('other', 'Other'),
    ]
    
    TYPE_CHOICES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('guide', 'Guide'),
        ('tip', 'Tip'),
        ('recipe', 'Recipe'),
        ('tool', 'Tool'),
        ('website', 'Website'),
    ]
    
    title = models.CharField(max_length=255, help_text="Title of the resource")
    description = models.TextField(help_text="Description of the resource")
    url = models.URLField(
        blank=True, 
        null=True, 
        help_text="URL to the resource (if applicable)"
    )
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        help_text="Category of the resource"
    )
    resource_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='article',
        help_text="Type of resource"
    )
    featured = models.BooleanField(
        default=False,
        help_text="Mark as featured resource"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        ordering = ['-featured', 'category', 'title']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['featured']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    def get_type_icon(self):
        """Get Bootstrap icon for resource type."""
        icons = {
            'article': 'bi-file-text',
            'video': 'bi-play-circle',
            'guide': 'bi-book',
            'tip': 'bi-lightbulb',
            'recipe': 'bi-egg-fried',
            'tool': 'bi-tools',
            'website': 'bi-globe',
        }
        return icons.get(self.resource_type, 'bi-file')
