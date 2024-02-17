
from django import forms
from app.models import Comments

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = {'content', 'email', 'name', 'website'}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs['placeholder'] = 'Напишіть свій коментар...'
        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['name'].widget.attrs['placeholder'] = 'Нікнейм'
        self.fields['website'].widget.attrs['placeholder'] = 'Веб-сайт'