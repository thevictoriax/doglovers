from django.contrib import admin
from app.models import Post, Tag, Comments, Profile, WebsiteMeta, Dog
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

from app.models import Post

class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Post
        fields = '__all__'

class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm

admin.site.register(Post, PostAdmin)
# Register your models here.
admin.site.register(Tag)
admin.site.register(Comments)
admin.site.register(Profile)
admin.site.register(WebsiteMeta)
admin.site.register(Dog)

