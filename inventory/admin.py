from django.contrib import admin
from .models import InventoryItem, FoodItem, ExpirationEmailNotification


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'typical_expiration_days', 'sample_cost_per_unit', 'unit', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'storage_tips')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'name')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'user', 'quantity', 'unit', 'category', 'status', 'expiration_date', 'purchase_date')
    list_filter = ('category', 'status', 'expiration_date', 'purchase_date', 'user')
    search_fields = ('item_name', 'user__username', 'user__email', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'expiration_date'
    ordering = ('expiration_date', 'item_name')


@admin.register(ExpirationEmailNotification)
class ExpirationEmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'user', 'sent_date', 'days_before_expiry', 'email_sent', 'created_at')
    list_filter = ('sent_date', 'days_before_expiry', 'email_sent', 'user')
    search_fields = ('inventory_item__item_name', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'sent_date'
    ordering = ('-sent_date', '-created_at')
