from django import forms
from .models import Car, CarImage, Comment, Hashtag, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea)
    favorite_brand = forms.ChoiceField(choices=UserProfile._meta.get_field('favorite_brand').choices)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'address', 'favorite_brand']