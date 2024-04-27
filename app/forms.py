
from typing import Any
from django import forms
from app.models import Comments, Subscribe
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from app.models import Post,  Tag, Profile
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor.widgets import CKEditorWidget
from django.utils.text import slugify
from django.utils.translation import gettext as _
from unidecode import unidecode


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = {'content', 'email', 'name', 'website'}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['placeholder'] = 'Напишіть свій коментар...'
        self.fields['email'].widget.attrs['placeholder'] = 'Електронна пошта'
        self.fields['name'].widget.attrs['placeholder'] = "Ім'я"
        self.fields['website'].widget.attrs['placeholder'] = 'Веб-сайт'


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscribe
        fields = '__all__'
        labels = {'email': _ ('')}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'Введіть свій email...'

class NewUserForm(UserCreationForm):
    profile_image = forms.ImageField(label="Profile Image", required=False)
    bio = forms.CharField(label="Біографія", widget=forms.Textarea(attrs={'placeholder': 'Напишіть про себе...'}))  # Add profile image field
    first_name = forms.CharField(label="First Name", max_length=30, required=True)
    last_name = forms.CharField(label="Last Name", max_length=30, required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "bio", "profile_image","first_name", "last_name")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Введіть ваше ім\'я'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Введіть ваше прізвище'
        self.fields['username'].widget.attrs['placeholder'] = 'Введіть ваш нік'
        self.fields['email'].widget.attrs['placeholder'] = 'Введіть ваш email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Введіть ваш пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторіть ваш пароль'
    
    def clean_profile_image(self):
        profile_image = self.cleaned_data.get('profile_image')
        if profile_image:
            if profile_image.size > 5 * 1024 * 1024:  # Limit file size to 5MB
                raise forms.ValidationError("The image file size should not exceed 5MB.")
        return profile_image
    
    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        new = User.objects.filter(username = username)
        if new.count():
            raise forms.ValidationError("Такий користувач вже існує")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        new = User.objects.filter(email = email)
        if new.count():
            raise forms.ValidationError("Цей email вже використаний")
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Паролі не збігаються")
        return password2
    
    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile_image = self.cleaned_data.get('profile_image')
            if profile_image:
                profile = Profile.objects.create(user=user, profile_image=profile_image, bio=self.cleaned_data['bio'])
            else:
                profile = Profile.objects.create(user=user, bio=self.cleaned_data['bio'])
        return user


class PostForm(forms.ModelForm):
    title = forms.CharField(label="Заголовок")
    content = forms.CharField(label="Зміст", widget=CKEditorWidget())
    image = forms.ImageField(label="Зображення")
    tags = forms.ModelMultipleChoiceField(label="Теги", queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple)
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)  
    # author_username = forms.CharField(widget=forms.HiddenInput())  


    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'tags']
    
    def save(self, commit=True):
        instance = super(PostForm, self).save(commit=False)
        translated_title = _(instance.title)  # Translate the title
        slug = slugify(unidecode(translated_title))  # Generate slug based on translated title
        instance.slug = slug
        if commit:
            instance.save()
        return instance