
from typing import Any
from django import forms
from app.models import Comments, Subscribe
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from app.models import Post,  Tag, Profile, Dog, Event
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from ckeditor.widgets import CKEditorWidget
from django.utils.text import slugify
from django.utils.translation import gettext as _
from unidecode import unidecode
from django.core.exceptions import ValidationError
from datetime import date
import json
from pathlib import Path
from django.forms.widgets import DateTimeInput
from django.contrib.auth.hashers import check_password

BREEDS_FILE = Path(__file__).resolve().parent / "dog_breeds.json"
with open(BREEDS_FILE, encoding="utf-8") as f:
    DOG_BREEDS = json.load(f).get("dogs", [])
    DOG_BREEDS_CHOICES = [(breed, breed) for breed in DOG_BREEDS]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Напишіть свій коментар...',
                'rows': 5,
            }),
        }
        labels = {
            'content': '',  # Встановлюємо порожній ярлик
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields.pop('name', None)
            self.fields.pop('email', None)

class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscribe
        fields = ['email']
        labels = {'email': ''}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['placeholder'] = 'Введіть свій email...'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        
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
    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'tags']  # БЕЗ slug
        labels = {
            'title': 'Заголовок',
            'content': 'Зміст',
            'image': 'Зображення',
            'tags': 'Теги',
        }
        widgets = {
            'content': CKEditorWidget(),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:  # створюємо slug тільки якщо ще нема
            translated_title = _(instance.title)
            instance.slug = slugify(unidecode(translated_title))
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class DogForm(forms.ModelForm):
    name = forms.CharField(label="Ім'я собаки", max_length=100)
    breed = forms.ChoiceField(
        label="Порода",
        choices=DOG_BREEDS_CHOICES,  # Використовуємо список порід
        required=False
    )
    birth_date = forms.DateField(
        label="Дата народження",
        widget=forms.DateInput(attrs={
            'type': 'date',
        }),
        required=True,
        input_formats=['%Y-%m-%d']  # Дата у форматі, який очікує поле
    )
    weight = forms.FloatField(
        label="Вага (кг)",
        required=True,
        widget=forms.NumberInput(attrs={'step': '0.1'})
    )
    profile_image = forms.ImageField(label="Зображення", required=False)  # Зображення не обов'язкове

    class Meta:
        model = Dog
        fields = ['name', 'breed', 'birth_date', 'weight', 'profile_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ініціалізуємо значення поля birth_date у форматі YYYY-MM-DD
        if self.instance.pk and self.instance.birth_date:
            self.initial['birth_date'] = self.instance.birth_date.strftime('%Y-%m-%d')

    def clean(self):
        """
        Загальна валідація (для всіх полів форми).
        """
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        weight = cleaned_data.get('weight')

        errors = []

        # Валідація поля "Дата народження"
        if birth_date and birth_date > date.today():
            errors.append("Дата народження не може бути в майбутньому.")

        # Валідація поля "Вага"
        if weight is not None and weight <= 0:
            errors.append("Вага повинна бути додатньою.")

        # Якщо є помилки, додаємо їх як non_field_errors
        if errors:
            raise ValidationError(errors)

        return cleaned_data


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['start', 'end', 'dog', 'repeat_interval', 'repeat_until', 'event_type']
        widgets = {
            'start': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'repeat_until': DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
        labels = {
            'start': 'Початок',
            'end': 'Завершення',
            'dog': 'Собака',
            'repeat_interval': 'Інтервал повторення',
            'repeat_until': 'Кінцева дата повторення',
            'event_type': 'Тип події',
        }

    custom_name = forms.CharField(
        required=False,
        label="Назва події (необов'язково)",
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EventForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['dog'].queryset = Dog.objects.filter(owner=user)

        # Форматуємо значення для datetime-local
        if self.instance.pk:
            if self.instance.start:
                self.initial['start'] = self.instance.start.strftime('%Y-%m-%dT%H:%M')
            if self.instance.end:
                self.initial['end'] = self.instance.end.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        event_type = cleaned_data.get('event_type')  # Отримуємо вибране значення
        custom_name = cleaned_data.get('custom_name')

        # Якщо обрано "Інше", вимагаємо введення назви події
        if event_type == 'other' and not custom_name:
            raise ValidationError("Для обраного варіанту 'Інше' необхідно вказати власну назву події.")

        # Якщо "Інше", використовуємо власну назву як "name"
        if event_type == 'other' and custom_name:
            cleaned_data['name'] = custom_name
        else:
            # Назва використовується з вибору EVENT_CHOICES
            cleaned_data['name'] = dict(Event.TYPE_CHOICES).get(event_type)

        return cleaned_data





class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Ім'я", max_length=30, required=True)
    last_name = forms.CharField(label="Прізвище", max_length=30, required=True)
    email = forms.EmailField(label="Email", required=True)
    current_password = forms.CharField(
        label="Старий пароль",
        widget=forms.PasswordInput(),
        required=False,
    )
    new_password = forms.CharField(
        label="Новий пароль",
        widget=forms.PasswordInput(),
        required=False,
    )
    profile_image = forms.ImageField(label="Фото профілю", required=False)
    bio = forms.CharField(label="Біографія", widget=forms.Textarea, required=False)

    class Meta:
        model = Profile
        fields = ['profile_image', 'bio']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email

    def clean(self):
        """
        Перевіряємо, чи старий пароль правильний, якщо користувач вказує новий пароль.
        """
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')

        if new_password:  # Користувач намагається змінити пароль
            if not current_password:
                raise forms.ValidationError("Необхідно вказати старий пароль для зміни пароля.")

            if not check_password(current_password, self.user.password):  # Перевірка старого пароля
                raise forms.ValidationError("Старий пароль введено неправильно.")

        return cleaned_data

    def save(self, commit=True):
        """
        Збереження даних профілю та користувача.
        """
        profile = super().save(commit=False)
        user = self.user

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        new_password = self.cleaned_data.get('new_password')
        if new_password:  # Якщо новий пароль введений
            user.set_password(new_password)

        if commit:
            user.save()
            profile.save()
        return profile