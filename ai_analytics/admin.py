from django.contrib import admin
from .models import (
    ConsumptionPattern, WastePrediction, NutrientGap,
    SDGImpactScore, ChatSession, ChatMessage
)


@admin.register(ConsumptionPattern)
class ConsumptionPatternAdmin(admin.ModelAdmin):
    list_display = ('user', 'pattern_type', 'category', 'severity', 'detected_date')
    list_filter = ('pattern_type', 'severity', 'detected_date', 'user')
    search_fields = ('user__username', 'description', 'category')
    readonly_fields = ('detected_date',)


@admin.register(WastePrediction)
class WastePredictionAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_name', 'predicted_waste_probability', 'predicted_waste_date', 'created_at')
    list_filter = ('category', 'predicted_waste_date', 'created_at', 'user')
    search_fields = ('item_name', 'user__username', 'reasoning')
    readonly_fields = ('created_at',)


@admin.register(NutrientGap)
class NutrientGapAdmin(admin.ModelAdmin):
    list_display = ('user', 'nutrient_name', 'gap_percentage', 'current_level', 'recommended_level', 'detected_date')
    list_filter = ('detected_date', 'user')
    search_fields = ('nutrient_name', 'user__username')
    readonly_fields = ('detected_date',)


@admin.register(SDGImpactScore)
class SDGImpactScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'overall_score', 'waste_reduction_score', 'nutrition_score', 'sustainability_score', 'week_start_date', 'created_at')
    list_filter = ('week_start_date', 'created_at', 'user')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    ordering = ('-week_start_date', '-created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'session_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at', 'session__user')
    search_fields = ('content', 'session__user__username')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
