from django.contrib import admin
from .models import FoodLog


@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'user', 'quantity', 'unit', 'category', 'date_consumed', 'created_at')
    list_filter = ('category', 'date_consumed', 'created_at', 'user')
    search_fields = ('item_name', 'user__username', 'user__email', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_consumed'
    ordering = ('-date_consumed', '-created_at')
