from django import forms
from django.core.validators import FileExtensionValidator

class UploadForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter a descriptive title',
            'class': 'form-input border border-violet-400 p-1 rounded w-full mt-0.5'
        }),
        help_text="A descriptive title for your wallpaper"
    )
    category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Nature, Abstract, Minimalist',
            'class': 'form-input border border-violet-400 p-1 rounded w-full mt-0.5'
        }),
        help_text="Optional category for organization"
    )
    file = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-file',
            'accept': 'image/jpeg, image/png, image/webp'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Upload high-quality images (JPEG, PNG, WEBP)"
    )

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long")
        return title

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 20 * 1024 * 1024:  # 20MB limit
            raise forms.ValidationError("File size must be less than 20MB")
        return file


