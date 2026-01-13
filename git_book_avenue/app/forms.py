from django import forms
from django.contrib.auth.models import User
from .models import Review, Book  # Added Book to imports

# 1. YOUR EXISTING REVIEW FORM (Keep this!)
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control', 'id': 'rating-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your review here...'})
        }

# 2. NEW: PUBLISHER SIGNUP FORM
class PublisherSignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    # This checkbox lets them choose to be a publisher
    is_publisher = forms.BooleanField(required=False, label="Sign up as a Publisher (I want to sell books)")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

# 3. NEW: ADD BOOK FORM (For Publishers)
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        # We exclude 'publisher' because we will fill that automatically in the view
        # We exclude 'created_at'/updated_at as they are automatic
        exclude = ['publisher', 'created_at', 'updated_at', 'is_bestseller'] 
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            # Image widget usually handles itself, but you can add class if needed
        }