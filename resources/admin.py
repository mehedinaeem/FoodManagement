from django.contrib import admin
from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resource_type', 'featured', 'created_at')
    list_filter = ('category', 'resource_type', 'featured', 'created_at')
    search_fields = ('title', 'description', 'url')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-featured', 'category', 'title')
    list_editable = ('featured',)
