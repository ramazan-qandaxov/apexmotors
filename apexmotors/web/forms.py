from django import forms
from .models import Car, CarImage, Comment, Hashtag

class CommentForm(forms.ModelForm):
    hashtags = forms.ModelMultipleChoiceField(
        queryset=Hashtag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Comment
        fields = ['text', 'hashtags']

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'description', 'price', 'category',
            'new_or_used', 'year', 'mileage', 'color', 'available_colors',
            'engine', 'fuel_type', 'drivetrain', 'horsepower',
            'torque', 'transmission', 'top_speed', 'acceleration',
            'document'
        ]
        widgets = {
            'available_colors': forms.CheckboxSelectMultiple,
        }
