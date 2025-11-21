from django import forms
from .models import InventoryItem, FoodItem


class InventoryItemForm(forms.ModelForm):
    """
    Form for creating and editing inventory items.
    """
    purchase_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )
    
    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    class Meta:
        model = InventoryItem
        fields = ['item_name', 'quantity', 'unit', 'category', 'purchase_date', 'expiration_date', 'notes']
        widgets = {
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Apple, Milk, Bread'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this item...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default purchase date to today if creating new item
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['purchase_date'].initial = timezone.now().date()


class InventoryFilterForm(forms.Form):
    """
    Form for filtering inventory items.
    """
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + InventoryItem.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + InventoryItem.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )


class FoodItemFilterForm(forms.Form):
    """
    Form for filtering food items (reference database).
    """
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + FoodItem.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search food items...'
        })
    )
