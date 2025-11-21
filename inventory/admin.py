from django.contrib import admin
from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'user', 'quantity', 'unit', 'category', 'status', 'expiration_date', 'purchase_date')
    list_filter = ('category', 'status', 'expiration_date', 'purchase_date', 'user')
    search_fields = ('item_name', 'user__username', 'user__email', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'expiration_date'
    ordering = ('expiration_date', 'item_name')
