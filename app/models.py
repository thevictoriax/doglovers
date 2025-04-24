import re
from django.utils.html import escape
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
import uuid
import requests




class NameGender(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Ім'я користувача
    gender = models.CharField(max_length=10)  # male, female або unknown

    def __str__(self):
        return f"{self.name}: {self.gender}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        null=True,
        blank=True,
        upload_to="images/",
    )
    slug = models.SlugField(max_length=200, unique=True)
    bio = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = self.generate_unique_slug(self.user.username)

        # Встановлюємо дефолтну фотографію, якщо фото не завантажено
        if not self.profile_image:
            gender = self.detect_gender(self.user.first_name)  # Визначення статі з імені
            if gender == 'female':
                self.profile_image = 'images/female.png'
            elif gender == 'male':
                self.profile_image = 'images/male.png'
            else:
                self.profile_image = 'images/male-1.png'

        super(Profile, self).save(*args, **kwargs)

    def detect_gender(self, name):
        # Перевіряємо, чи є ім'я в кеші
        try:
            cached_gender = NameGender.objects.get(name=name.lower())
            return cached_gender.gender
        except NameGender.DoesNotExist:
            # Якщо немає в кеші, робимо API-запит
            api_url = f"https://api.genderize.io/?name={name}"
            try:
                response = requests.get(api_url)
                data = response.json()
                gender = data.get('gender', 'unknown')

                # Зберігаємо в кеші
                NameGender.objects.create(name=name.lower(), gender=gender)
                return gender
            except requests.RequestException:
                return 'unknown'

    def generate_unique_slug(self, username):
        slug = slugify(username)
        unique_slug = slug
        counter = 1
        while Profile.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1
        return unique_slug

class Subscribe(models.Model):
    email = models.EmailField(max_length=100)
    date = models.DateTimeField(auto_now=True)

class Tag(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = slugify(self.name)
        return super(Tag, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.name

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=200, unique=True)
    image = models.ImageField(null=True, blank=True, upload_to="images/")
    tags = models.ManyToManyField(Tag, blank=True, related_name='post')
    view_count = models.IntegerField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    bookmarks = models.ManyToManyField(User, related_name="bookmarks", default=None, blank=True)
    likes = models.ManyToManyField(User, related_name="post_like", default=None, blank=True)

    def number_of_likes(self):
        return self.likes.count()

class Comments(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Це поле вже у вас є
    content = models.TextField()
    date = models.DateTimeField(auto_now=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='comments/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='comments/thumbnails/', null=True, blank=True, max_length=255)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )

    @property
    def author_name(self):
        return self.author.first_name if self.author else self.name

    @property
    def author_image(self):
        if self.author and hasattr(self.author, 'profile') and self.author.profile.profile_image:
            return self.author.profile.profile_image.url
        return "images/default-avatar.png"

    def convert_links(self):
        """
        Автоматично конвертує URL у тексті коментаря в клікабельні посилання.
        """
        url_pattern = r'(https?://[^\s]+)'  # Пошук "http://" або "https://"
        linked_text = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener">\1</a>', escape(self.content))
        return linked_text

    def save(self, *args, **kwargs):
        from pathlib import Path  # Локальний імпорт модуля Path
        from app.views import generate_thumbnail  # Локальний імпорт будь-якої функції або допоміжного коду

        super().save(*args, **kwargs)

        if self.image:
            image_path = self.image.path
            thumbnail_path = generate_thumbnail(image_path)
            self.thumbnail.name = thumbnail_path.replace(str(Path(self.image.path).parent) + "/", "")
            super().save(*args, **kwargs)

class WebsiteMeta(models.Model):
   title = models.CharField(max_length=200)
   description = models.CharField(max_length=500)
   about = models.TextField()


class Dog(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="dogs")
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)  # Weight in kg
    profile_image = models.ImageField(upload_to="dog_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class Event(models.Model):
    TYPE_CHOICES = [
        ('tick_tablet', 'Таблетка від кліщів'),
        ('worm_tablet', 'Таблетка від глистів'),
        ('vet_visit', 'Візит до ветеринара'),
        ('vitamins', 'Вітаміни'),
        ('treatment_tablet', 'Лікувальні таблетки'),
        ('grooming', 'Грумінг'),
        ('vaccination', 'Вакцинація'),
        ('other', 'Інше'),
    ]
    dog = models.ForeignKey(
        Dog,
        on_delete=models.CASCADE,
        related_name="events",
        default=1
    )
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    repeat_interval = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[('none', 'Без повторень'), ('daily', 'Щодня'), ('weekly', 'Щотижня'), ('monthly', 'Щомісяця'), ('yearly', 'Щороку')]
    )
    series_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)  # Унікальний ідентифікатор серії

    class Meta:
        db_table = "tblevents"

    def __str__(self):
        return f"{self.name} - {self.event_type} - {self.dog.name}"


