
from typing import Any
from django import forms
from app.models import Comments, Subscribe
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from app.models import Post,  Tag
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor.widgets import CKEditorWidget
from django.utils.text import slugify


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
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Введіть ваш нік'
        self.fields['email'].widget.attrs['placeholder'] = 'Введіть ваш email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Введіть ваш пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторіть ваш пароль'
    
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
        instance.slug = slugify(instance.title)  # Generate slug based on title
        if commit:
            instance.save()
        return instance