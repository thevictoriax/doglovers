from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(null=True, blank=True, upload_to="images/")
    slug = models.SlugField(max_length=200, unique=True)
    bio = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        if not self.id:
            # Generate unique slug based on username
            self.slug = self.generate_unique_slug(self.user.username)
        return super(Profile, self).save(*args, **kwargs)

    def generate_unique_slug(self, username):
        slug = slugify(username)
        unique_slug = slug
        counter = 1
        while Profile.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{counter}"
            counter += 1
        return unique_slug

    def __str__(self):
        return self.user.first_name

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
    content = models.TextField()
    date = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    website = models.CharField(max_length=200)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='replies')

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

# class Event(models.Model):
#     EVENT_TYPES = [
#         ('deworming', 'Таблетка від глистів'),
#         ('ticks', 'Таблетка від кліщів'),
#         ('vet_visit', 'Візит до ветеринара'),
#         ('vaccination', 'Вакцинація'),
#     ]
#
#     title = models.CharField(max_length=255)  # Назва події
#     date = models.DateField()  # Дата події
#     event_type = models.CharField(
#         max_length=20,
#         choices=EVENT_TYPES,
#         default='vet_visit'
#     )  # Тип події
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # Власник
#     dog = models.ForeignKey('Dog', on_delete=models.CASCADE)  # Звʼязок із собакою
#     description = models.TextField(blank=True, null=True)  # Опис події
#
#     def __str__(self):
#         return f"{self.title} - {self.date}"
class Event(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tblevents"