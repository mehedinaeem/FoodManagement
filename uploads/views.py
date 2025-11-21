from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Upload
from .forms import UploadForm, AssociateUploadForm


@login_required
def upload_list(request):
    """
    Display list of user's uploads.
    """
    uploads = Upload.objects.filter(user=request.user)
    
    # Filter by type if provided
    upload_type = request.GET.get('type')
    if upload_type:
        uploads = uploads.filter(upload_type=upload_type)
    
    # Statistics
    total_uploads = uploads.count()
    uploads_by_type = uploads.values('upload_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Group by type
    uploads_by_type_dict = {}
    for upload in uploads:
        type_name = upload.get_upload_type_display()
        if type_name not in uploads_by_type_dict:
            uploads_by_type_dict[type_name] = []
        uploads_by_type_dict[type_name].append(upload)
    
    context = {
        'uploads': uploads,
        'total_uploads': total_uploads,
        'uploads_by_type': uploads_by_type,
        'uploads_by_type_dict': uploads_by_type_dict,
    }
    
    return render(request, 'uploads/list.html', context)


@login_required
def upload_create(request):
    """
    Create a new upload.
    """
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.user = request.user
            upload.save()
            messages.success(request, 'Image uploaded successfully!')
            return redirect('uploads:list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UploadForm(user=request.user)
    
    return render(request, 'uploads/form.html', {
        'form': form,
        'title': 'Upload Image',
        'action': 'Upload'
    })


@login_required
def upload_detail(request, pk):
    """
    View details of an upload and manage associations.
    """
    upload = get_object_or_404(Upload, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AssociateUploadForm(request.POST, user=request.user, upload=upload)
        if form.is_valid():
            association_type = form.cleaned_data.get('association_type')
            
            if association_type == 'none':
                upload.associated_inventory = None
                upload.associated_log = None
                messages.success(request, 'Association removed successfully!')
            elif association_type == 'inventory':
                upload.associated_inventory = form.cleaned_data.get('inventory_item')
                upload.associated_log = None
                messages.success(request, 'Upload associated with inventory item!')
            elif association_type == 'log':
                upload.associated_log = form.cleaned_data.get('food_log')
                upload.associated_inventory = None
                messages.success(request, 'Upload associated with food log!')
            
            upload.save()
            return redirect('uploads:detail', pk=upload.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AssociateUploadForm(user=request.user, upload=upload)
    
    context = {
        'upload': upload,
        'form': form,
    }
    
    return render(request, 'uploads/detail.html', context)


@login_required
def upload_delete(request, pk):
    """
    Delete an upload.
    """
    upload = get_object_or_404(Upload, pk=pk, user=request.user)
    
    if request.method == 'POST':
        title = upload.title or 'Upload'
        # Delete the file
        if upload.image:
            upload.image.delete(save=False)
        upload.delete()
        messages.success(request, f'"{title}" deleted successfully!')
        return redirect('uploads:list')
    
    return render(request, 'uploads/delete.html', {'upload': upload})
