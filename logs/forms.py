from django import forms
from .models import FoodLog


class FoodLogForm(forms.ModelForm):
    """
    Form for creating and editing food logs.
    """
    date_consumed = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=True
    )
    
    class Meta:
        model = FoodLog
        fields = ['item_name', 'quantity', 'unit', 'category', 'date_consumed', 'notes']
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
                'placeholder': 'Optional notes about this consumption...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today if creating new log
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date_consumed'].initial = timezone.now().date()


class FoodLogFilterForm(forms.Form):
    """
    Form for filtering food logs.
    """
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + FoodLog.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'this.form.submit()'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

