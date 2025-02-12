from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from app.models import Post, Comments, Tag, Profile, WebsiteMeta, Dog, Event
from app.forms import CommentForm, SubscribeForm, NewUserForm, PostForm, DogForm, EventForm
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
import json
from pathlib import Path
from dateutil.relativedelta import relativedelta
from django.utils.timezone import is_naive, make_aware
import pytz

BREEDS_FILE = Path(__file__).resolve().parent / "dog_breeds.json"
with open(BREEDS_FILE, encoding="utf-8") as f:
    DOG_BREEDS = json.load(f).get("dogs", [])
    DOG_BREEDS_CHOICES = [(breed, breed) for breed in DOG_BREEDS]

# Create your views here.
def index(request):
    posts = Post.objects.all()
    top_posts = Post.objects.all().order_by('-view_count')[0:3]
    recent_posts = Post.objects.all().order_by('-last_updated')[0:3]
    featured_blog = Post.objects.filter(is_featured = True)
    subscribe_form = SubscribeForm()
    subscribe_successful = None
    website_info = None

    if WebsiteMeta.objects.all().exists():
        website_info = WebsiteMeta.objects.all()[0]

    if featured_blog:
        featured_blog = featured_blog[0]

    if request.POST:
        subscribe_form = SubscribeForm(request.POST)
        if subscribe_form.is_valid():
            subscribe_form.save()
            request.session['subscribed'] = True
            subscribe_successful = "Subscribed successfully"
            subscribe_form = SubscribeForm()

    context = {'posts':posts, 'top_posts': top_posts, 'website_info': website_info, 'recent_posts':recent_posts, 'subscribe_form':subscribe_form, 'subscribe_successful':subscribe_successful, 'featured_blog':featured_blog}
    return render(request, 'app/index.html', context)

def post_page(request, slug):
    post = Post.objects.get(slug=slug)
    comments = Comments.objects.filter(post=post, parent=None)
    form = CommentForm()
    

    bookmarked = False
    if post.bookmarks.filter(id=request.user.id).exists():
        bookmarked = True
    is_bookmarked = bookmarked

    liked = False
    if post.likes.filter(id=request.user.id).exists():
        liked = True
    number_of_likes = post.number_of_likes()
    post_is_liked = liked

    if request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid:
            parent_obj = None
            if request.POST.get('parent'):
                # save reply
                parent=request.POST.get('parent')
                parent_obj = Comments.objects.get(id=parent)
                if parent_obj:
                    comment_reply = comment_form.save(commit=False)
                    comment_reply.parent = parent_obj
                    comment_reply.post = post
                    comment_reply.save()
                    return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))
            else:
                comment = comment_form.save(commit=False)
                postid = request.POST.get('post_id')
                post = Post.objects.get(id = postid)
                comment.post = post
                comment.save()
                return HttpResponseRedirect(reverse('post_page', kwargs={'slug':slug}))

    comments_count = comments.count()
    # Check if the user has viewed the post
    if 'viewed_posts' not in request.session:
        request.session['viewed_posts'] = []
    
    if post.id not in request.session['viewed_posts']:
        post.view_count += 1
        post.save(update_fields=['view_count'])
        request.session['viewed_posts'].append(post.id)
        request.session.modified = True
    
    # sidebar
    recent_posts= Post.objects.exclude(id=post.id).order_by('-last_updated')[0:3]
    top_authors = User.objects.annotate(number=Count('post')).order_by('-number')
    tags = Tag.objects.all()
    related_posts = Post.objects.exclude(id = post.id).filter(author=post.author)[0:3]

    context = {'post':post, 'form':form, 'comments':comments, 'is_bookmarked':is_bookmarked, 'post_is_liked':  post_is_liked, 'number_of_likes':number_of_likes, 'recent_posts': recent_posts, 'top_authors':top_authors, 'tags':tags, 'related_posts':related_posts, 'comments_count':comments_count}
    return render(request, 'app/post.html', context)

def tag_page(request, slug):
    tag = Tag.objects.get(slug=slug)
    top_posts = Post.objects.filter(tags__in = [tag.id]).order_by('-view_count')[0:2]
    recent_posts = Post.objects.filter(tags__in = [tag.id]).order_by('-last_updated')[0:2]

    tags = Tag.objects.all()
    context = {'tag':tag, 'top_posts':top_posts, 'recent_posts': recent_posts, 'tags':tags}
    return render(request, 'app/tag.html', context)

def author_page(request, slug):
    profile = Profile.objects.get(slug=slug)
    top_posts = Post.objects.filter(author=profile.user).order_by('-view_count')[0:2]
    recent_posts = Post.objects.filter(author=profile.user).order_by('-last_updated')[0:2]
    top_authors = User.objects.annotate(number=Count('post')).order_by('number')

    context = {'profile':profile, 'top_posts':top_posts, 'recent_posts': recent_posts, 'top_authors':top_authors}
    return render(request, 'app/author.html', context)

def search_posts(request):
    search_query = ''
    if request.GET.get('q'):
        search_query= request.GET.get('q')
    posts = Post.objects.filter(title__icontains=search_query)
    print('Пошук : ', search_query)
    context = {'posts': posts, 'search_query': search_query}
    return render(request, 'app/search.html', context)

def about(request):
    website_info = None

    if WebsiteMeta.objects.all().exists():
        website_info = WebsiteMeta.objects.all()[0]

    context = {'website_info':website_info}
    return render(request, 'app/about.html', context)

def register_user(request):
    form = NewUserForm()
    if request.method == "POST":
        form = NewUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            # Check if a profile already exists for the user
            if not Profile.objects.filter(user=user).exists():
                # Creating a profile for the user
                bio = form.cleaned_data.get('bio')
                profile_image = request.FILES.get('profile_image')
                profile = Profile.objects.create(user=user, bio=bio, profile_image=profile_image)

            login(request, user)
            return redirect("/")
    context = {'form':form}
    return render(request, 'registration/registration.html', context)


def bookmark_post(request, slug):
    print("PRINT", request.POST.get('post_id'))
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user)
    else:
        post.bookmarks.add(request.user)
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def like_post(request, slug):
    print("PRINT", request.POST.get('post_id'))
    post = get_object_or_404(Post, id=request.POST.get('post_id'))
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def all_bookmarked_posts(request):
    all_bookmarked_posts = Post.objects.filter(bookmarks = request.user)
    context = {'all_bookmarked_posts':all_bookmarked_posts}
    return render(request, 'app/all_bookmarked_posts.html', context)

def all_posts(request):
    all_posts = Post.objects.all()
    paginator = Paginator(all_posts, 6)  # Number of posts per page
    page = request.GET.get('page')
    try:
        all_posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        all_posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        all_posts = paginator.page(paginator.num_pages)
    return render(request, 'app/all_posts.html', {'all_posts': all_posts})

@login_required
def user_posts(request):
    user_posts = Post.objects.filter(author=request.user)
    paginator = Paginator(user_posts, 6)  # Number of posts per page
    page = request.GET.get('page')
    try:
        user_posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        user_posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        user_posts = paginator.page(paginator.num_pages)
    return render(request, 'app/user_posts.html', {'user_posts': user_posts})

def all_liked_posts(request):
    all_liked_posts = Post.objects.filter(likes = request.user)
    context = {'all_liked_posts':all_liked_posts}
    return render(request, 'app/all_liked_posts.html', context)

@login_required
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Assign the author field with the authenticated user
            post.save()
            form.save_m2m()  # Save many-to-many fields, like tags
            return HttpResponseRedirect(reverse('post_page', kwargs={'slug': post.slug}))
    else:
        form = PostForm()
    return render(request, 'app/add_post.html', {'form': form})

@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    
    # Check if the logged-in user is the author of the post
    if request.user == post.author:
        post.delete()
        return HttpResponseRedirect(reverse('index'))  # Redirect to home page or any other desired URL after deletion
    else:
        # Handle unauthorized access (Optional: You may raise a PermissionDenied exception or show an error message)
        return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    tag_posts = Post.objects.filter(tags=tag)
    paginator = Paginator(tag_posts, 6)  # Number of posts per page
    page = request.GET.get('page')
    try:
        tag_posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tag_posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        tag_posts = paginator.page(paginator.num_pages)
    return render(request, 'app/tag_posts.html', {'tag_posts': tag_posts, 'tag': tag})

def dog_walking_map(request):
    return render(request, 'app/map.html')

@login_required
def list_dogs(request):
    # Fetch only the dogs for the logged-in user
    dogs = Dog.objects.filter(owner=request.user)

    context = {
        'dogs': dogs,
    }
    return render(request, 'app/list_dogs.html', context)

@login_required
def add_dog(request):
    if request.method == 'POST':
        form = DogForm(request.POST, request.FILES)
        if form.is_valid():
            dog = form.save(commit=False)
            dog.owner = request.user  # Прив'язуємо собаку до авторизованого користувача
            dog.save()
            return HttpResponseRedirect('my_dogs')
    else:
        form = DogForm()
    return render(request, 'app/add_dog.html', {'form': form})

@login_required
def edit_dog(request, pk):
    # Отримуємо об'єкт собаки за ідентифікатором (або повертаємо 404)
    dog = get_object_or_404(Dog, pk=pk)

    if request.method == "POST":
        form = DogForm(request.POST, request.FILES, instance=dog)
        if form.is_valid():
            form.save()
            return redirect('/my_dogs/')  # Повернення на сторінку з усіма собаками
    else:
        form = DogForm(instance=dog)  # Існуючі дані передаються у форму

    return render(request, 'app/edit_dog.html', {'form': form, 'dog': dog})


@login_required
def delete_dog(request, pk):
    # Get the dog object (or return a 404 if not found)
    dog = get_object_or_404(Dog, pk=pk)

    if request.method == 'POST':
        # Delete the dog and provide feedback
        dog_name = dog.name  # Save the dog's name for a success message
        dog.delete()
        messages.success(request, f'Анкету собаки "{dog_name}" успішно видалено.')
        return redirect('/my_dogs/')  # Redirect to the list of dogs

    # If not POST, return a 405 (method not allowed)
    return HttpResponseNotAllowed(['POST'])


@login_required
def user_calendar(request):
    user_dogs = Dog.objects.filter(owner=request.user).order_by('id')  # Упорядкування для послідовності

    # Фіксований список кольорів для собак
    static_colors = ['#4cb4c7', '#598eeb', '#8e65f0', '#a24cc7', '#bfc74c', '#c79e4c', '#98c74c']
    dog_colors = {dog.id: static_colors[index % len(static_colors)] for index, dog in enumerate(user_dogs)}

    context = {
        "dogs": user_dogs,  # Усі собаки користувача
        "dog_colors": [{"name": dog.name, "color": dog_colors[dog.id]} for dog in user_dogs],  # Для легенди
        "dog_color_map": dog_colors,  # Мапа собака -> колір для передачі подій
    }
    return render(request, 'app/user_calendar.html', context)


@login_required
def all_events(request):
    dog_id = request.GET.get("dog_id")  # Отримання ID собаки з GET-запиту
    event_type = request.GET.get("event_type")  # Отримання типу події з GET-запиту

    # Список всіх собак користувача
    user_dogs = Dog.objects.filter(owner=request.user).order_by('id')

    # Фіксований список кольорів
    static_colors = ['#4cb4c7', '#598eeb', '#8e65f0', '#a24cc7', '#bfc74c', '#c79e4c', '#98c74c']
    dog_colors = {dog.id: static_colors[index % len(static_colors)] for index, dog in enumerate(user_dogs)}  # Генеруємо кольори для кожної собаки

    # Фільтруємо події
    all_events = Event.objects.filter(dog__owner=request.user)

    # Фільтр по собаці
    if dog_id:
        all_events = all_events.filter(dog_id=dog_id)

    # Фільтр по типу події
    if event_type:
        all_events = all_events.filter(event_type=event_type)

    # Формуємо список подій
    out = []
    for event in all_events:
        out.append({
            'title': f"{event.name} - {event.get_event_type_display()} ({event.dog.name})",
            'id': event.id,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'color': dog_colors[event.dog.id],  # Використання кольору з фіксованої мапи
        })

    return JsonResponse(out, safe=False)

@login_required
def update_event(request, event_id):
    event = Event.objects.get(id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.name = form.cleaned_data['name']
            event.event_type = form.cleaned_data['event_type']
            event.save()
            return redirect('/calendar/')
        else:
            return render(request, 'app/edit_event.html', {'form': form, 'errors': form.errors, 'event_id': event_id})
    else:
        form = EventForm(instance=event, user=request.user)
        return render(request, 'app/edit_event.html', {'form': form, 'event_id': event_id})


@login_required
def remove_event(request):
    if request.method == "POST":
        event_id = request.POST.get("event_id")
        delete_all = request.POST.get("delete_all") == "on"

        try:
            event = Event.objects.get(id=event_id)

            if delete_all:
                # Видаляємо поточну подію і всі наступні в серії
                Event.objects.filter(
                    series_id=event.series_id,  # Видаляємо події з тієї ж серії
                    start__gte=event.start  # Тільки події, що є поточною або пізніше за часом
                ).delete()
            else:
                # Видаляємо тільки поточну подію
                event.delete()

            return redirect('/calendar/')  # Після видалення перенаправляємо на календар
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Подія не знайдена'}, status=404)

    return JsonResponse({'error': 'Недопустимий метод запиту'}, status=400)

@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.name = form.cleaned_data['name']  # Встановлюємо назву події
            event.event_type = form.cleaned_data['event_type']  # Записуємо тип події
            event.save()

            # Генеруємо повторювані події
            series_id = event.series_id
            repeat_interval = event.repeat_interval
            if repeat_interval and repeat_interval != 'none':
                start = event.start
                end = event.end
                for i in range(1, 12):  # 12 повторень
                    if repeat_interval == 'daily':
                        start += timedelta(days=1)
                        end += timedelta(days=1)
                    elif repeat_interval == 'weekly':
                        start += timedelta(weeks=1)
                        end += timedelta(weeks=1)
                    elif repeat_interval == 'monthly':
                        start += relativedelta(months=1)
                        end += relativedelta(months=1)
                    elif repeat_interval == 'yearly':
                        start += relativedelta(years=1)
                        end += relativedelta(years=1)

                    Event.objects.create(
                        name=event.name,
                        start=start,
                        end=end,
                        dog=event.dog,
                        repeat_interval=repeat_interval,
                        series_id=series_id,
                        event_type=event.event_type  # Встановлюємо тип події
                    )
            return redirect('/calendar/')
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = EventForm(user=request.user)
        return render(request, 'app/add_event.html', {'form': form})