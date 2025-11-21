from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ConsumptionPattern(models.Model):
    """
    Stores AI-analyzed consumption patterns for users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consumption_patterns')
    pattern_type = models.CharField(
        max_length=50,
        choices=[
            ('weekly_trend', 'Weekly Trend'),
            ('category_imbalance', 'Category Imbalance'),
            ('over_consumption', 'Over Consumption'),
            ('under_consumption', 'Under Consumption'),
            ('waste_risk', 'Waste Risk'),
        ]
    )
    category = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    detected_date = models.DateField(auto_now_add=True)
    data = models.JSONField(default=dict, help_text="Additional pattern data in JSON format")
    
    class Meta:
        verbose_name = "Consumption Pattern"
        verbose_name_plural = "Consumption Patterns"
        ordering = ['-detected_date', '-severity']
        indexes = [
            models.Index(fields=['user', '-detected_date']),
            models.Index(fields=['pattern_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_pattern_type_display()}"


class WastePrediction(models.Model):
    """
    Stores AI predictions for items likely to be wasted.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waste_predictions')
    inventory_item = models.ForeignKey(
        'inventory.InventoryItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='waste_predictions'
    )
    item_name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    predicted_waste_probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Probability of waste (0-100%)"
    )
    predicted_waste_date = models.DateField(help_text="Predicted date when item will be wasted")
    reasoning = models.TextField(help_text="AI reasoning for the prediction")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Waste Prediction"
        verbose_name_plural = "Waste Predictions"
        ordering = ['-predicted_waste_probability', 'predicted_waste_date']
        indexes = [
            models.Index(fields=['user', '-predicted_waste_probability']),
            models.Index(fields=['predicted_waste_date']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.predicted_waste_probability}% waste risk"


class NutrientGap(models.Model):
    """
    Stores detected nutrient gaps in user's consumption.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nutrient_gaps')
    nutrient_name = models.CharField(max_length=100, help_text="e.g., Vitamin C, Iron, Protein")
    current_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Current estimated level"
    )
    recommended_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Recommended level"
    )
    gap_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Gap percentage (0-100%)"
    )
    suggested_foods = models.JSONField(
        default=list,
        help_text="List of foods that can fill this gap"
    )
    detected_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Nutrient Gap"
        verbose_name_plural = "Nutrient Gaps"
        ordering = ['-gap_percentage', '-detected_date']
        indexes = [
            models.Index(fields=['user', '-gap_percentage']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.nutrient_name} ({self.gap_percentage}% gap)"


class SDGImpactScore(models.Model):
    """
    Stores user's SDG impact scores over time.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sdg_scores')
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall SDG score (0-100)"
    )
    waste_reduction_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    nutrition_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    sustainability_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    week_start_date = models.DateField(help_text="Start date of the week this score represents")
    insights = models.JSONField(default=dict, help_text="AI-generated insights")
    actionable_steps = models.JSONField(
        default=list,
        help_text="List of actionable steps to improve score"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "SDG Impact Score"
        verbose_name_plural = "SDG Impact Scores"
        ordering = ['-week_start_date', '-created_at']
        unique_together = ['user', 'week_start_date']
        indexes = [
            models.Index(fields=['user', '-week_start_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Week {self.week_start_date} - Score: {self.overall_score}"


class ChatSession(models.Model):
    """
    Stores chatbot conversation sessions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    session_id = models.CharField(max_length=100, unique=True)
    context = models.JSONField(
        default=dict,
        help_text="Session context (user preferences, recent activity, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class ChatMessage(models.Model):
    """
    Stores individual chat messages in a session.
    """
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User'),
            ('assistant', 'Assistant'),
            ('system', 'System'),
        ]
    )
    content = models.TextField()
    metadata = models.JSONField(default=dict, help_text="Additional message metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.session.user.username} - {self.role} - {self.created_at}"
