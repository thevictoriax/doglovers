from django.urls import path
from . import views


urlpatterns = [
   path('', views.index, name='index'), 
   path('post/<slug:slug>', views.post_page, name='post_page'),
   path('tag/<slug:slug>', views.tag_page, name='tag_page'),
   # path('post/index.html', views.index, name='index'),
   # path('tag/index.html', views.index, name='index'),
   # path('author/index.html', views.index, name='index'),
   path('author/<slug:slug>', views.author_page, name='author_page'),
   path('search/', views.search_posts, name='search'),
   path('about/', views.about, name='about'),
   path('accounts/register/', views.register_user, name='register'),
   path('bookmark_post/<slug:slug>', views.bookmark_post, name='bookmark_post'),
   path('like_post/<slug:slug>', views.like_post, name='like_post'),
   path('all_bookmarked_posts', views.all_bookmarked_posts, name='all_bookmarked_posts'),
   path('all_posts', views.all_posts, name='all_posts'),
   path('all_liked_posts', views.all_liked_posts, name='all_liked_posts'),
   path('post/<slug:slug>/delete/', views.delete_post, name='delete_post'),
   path('add_post/', views.add_post, name='add_post'),  
   path('user-posts/', views.user_posts, name='user_posts'),
   path('tag_posts/<slug:slug>', views.tag_posts, name='tag_posts'),
   path('map/', views.dog_walking_map, name='map'),
   path('my_dogs/', views.list_dogs, name='list_dogs'),
   path('add_dog', views.add_dog, name='add_dog'),
   path('dog/<int:pk>/edit/', views.edit_dog, name='edit_dog'),
   path('delete_dog/<int:pk>/', views.delete_dog, name='delete_dog'),
   path('calendar/', views.user_calendar, name='user_calendar'),
   path('all_events/', views.all_events, name='all_events'),
   path('add_event/', views.add_event, name='add_event'),
   path('update/', views.update, name='update'),
   path('remove/', views.remove, name='remove'),





]