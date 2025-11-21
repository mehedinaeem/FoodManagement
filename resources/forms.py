from django import forms
from .models import Resource


class ResourceFilterForm(forms.Form):
    """
    Form for filtering resources.
    """
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Resource.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )
    
    resource_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Resource.TYPE_CHOICES,
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
            'placeholder': 'Search resources...'
        })
    )

