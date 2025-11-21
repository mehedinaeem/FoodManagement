from django.contrib import admin
from .models import Upload


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'upload_type', 'associated_inventory', 'associated_log', 'created_at')
    list_filter = ('upload_type', 'created_at', 'user')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'get_file_size', 'get_file_extension')
    fields = ('user', 'image', 'upload_type', 'title', 'description', 
              'associated_inventory', 'associated_log', 
              'get_file_size', 'get_file_extension', 'created_at', 'updated_at')
    
    def get_file_size(self, obj):
        return obj.get_file_size()
    get_file_size.short_description = 'File Size'
    
    def get_file_extension(self, obj):
        return obj.get_file_extension()
    get_file_extension.short_description = 'File Type'
