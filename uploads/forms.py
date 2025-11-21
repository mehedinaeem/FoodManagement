from django import forms
from .models import Upload
from inventory.models import InventoryItem
from logs.models import FoodLog


class UploadForm(forms.ModelForm):
    """
    Form for uploading images.
    """
    image = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/jpg,image/png',
        }),
        help_text="Upload JPG or PNG image (max 10MB)"
    )
    
    class Meta:
        model = Upload
        fields = ['image', 'upload_type', 'title', 'description']
        widgets = {
            'upload_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional title (e.g., Grocery Receipt)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (10MB limit)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image file too large. Maximum size is 10MB.")
            
            # Check file extension
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise forms.ValidationError("Only JPG and PNG files are allowed.")
        
        return image


class AssociateUploadForm(forms.Form):
    """
    Form for associating an upload with inventory or log.
    """
    ASSOCIATION_CHOICES = [
        ('', 'Select association type...'),
        ('inventory', 'Associate with Inventory Item'),
        ('log', 'Associate with Food Log'),
        ('none', 'Remove Association'),
    ]
    
    association_type = forms.ChoiceField(
        choices=ASSOCIATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_association_type',
            'onchange': 'toggleAssociationFields()'
        })
    )
    
    inventory_item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_inventory_item',
            'style': 'display: none;'
        })
    )
    
    food_log = forms.ModelChoiceField(
        queryset=FoodLog.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_food_log',
            'style': 'display: none;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.upload = kwargs.pop('upload', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Set querysets for user's items
            self.fields['inventory_item'].queryset = InventoryItem.objects.filter(
                user=self.user
            ).order_by('-created_at')
            self.fields['food_log'].queryset = FoodLog.objects.filter(
                user=self.user
            ).order_by('-date_consumed', '-created_at')
        
        if self.upload:
            # Pre-fill current associations
            if self.upload.associated_inventory:
                self.fields['association_type'].initial = 'inventory'
                self.fields['inventory_item'].initial = self.upload.associated_inventory.pk
            elif self.upload.associated_log:
                self.fields['association_type'].initial = 'log'
                self.fields['food_log'].initial = self.upload.associated_log.pk
    
    def clean(self):
        cleaned_data = super().clean()
        association_type = cleaned_data.get('association_type')
        inventory_item = cleaned_data.get('inventory_item')
        food_log = cleaned_data.get('food_log')
        
        if association_type == 'inventory' and not inventory_item:
            raise forms.ValidationError("Please select an inventory item.")
        if association_type == 'log' and not food_log:
            raise forms.ValidationError("Please select a food log.")
        
        return cleaned_data

