from datetime import datetime, timedelta, time
from uuid import uuid4
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from app.models import Post, Comments, Tag, Profile, WebsiteMeta, Dog, Event
from app.forms import CommentForm, SubscribeForm, NewUserForm, PostForm, DogForm, EventForm, EditProfileForm
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, JsonResponse, Http404
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
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from PIL import Image
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from PIL import Image
from pathlib import Path


def generate_thumbnail(image_path, size=(150, 150), quality=85):
    image = Image.open(image_path)
    image.thumbnail(size)
    image_path = Path(image_path)
    thumbnail_name = f"{image_path.stem[:50]}_thumbnail{image_path.suffix}"
    thumbnail_path = image_path.parent / thumbnail_name

    if image.format == 'JPEG':
        image.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
    else:
        image.save(thumbnail_path, optimize=True)
    return str(thumbnail_path)

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

def delete_nested_comments(comment):
    replies = Comments.objects.filter(parent=comment)
    for reply in replies:
        delete_nested_comments(reply)
    comment.delete()

def post_page(request, slug):
    try:
        post = Post.objects.get(slug=slug)
    except Post.DoesNotExist:
        raise Http404("Допис не знайдено")

    comments = Comments.objects.filter(post=post, parent=None)
    form = CommentForm(user=request.user if request.user.is_authenticated else None)

    is_bookmarked = post.bookmarks.filter(id=request.user.id).exists() if request.user.is_authenticated else False
    post_is_liked = post.likes.filter(id=request.user.id).exists() if request.user.is_authenticated else False
    number_of_likes = post.number_of_likes()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Тільки авторизовані користувачі можуть залишати коментарі.")
            return HttpResponseRedirect(reverse('login'))

        comment_form = CommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            parent_obj = None
            if request.POST.get('parent'):
                parent_id = request.POST.get('parent')
                try:
                    parent_obj = Comments.objects.get(id=parent_id)
                except Comments.DoesNotExist:
                    parent_obj = None

                if parent_obj:
                    reply = comment_form.save(commit=False)
                    reply.parent = parent_obj
                    reply.post = post
                    reply.author = request.user
                    if 'image' in request.FILES:
                        reply.image = request.FILES['image']
                    reply.save()
            else:
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                if 'image' in request.FILES:
                    comment.image = request.FILES['image']
                comment.save()

            comments = Comments.objects.filter(post=post, parent=None)
            return render(request, 'app/post.html', {
                'post': post,
                'form': form,
                'comments': comments,
                'is_bookmarked': is_bookmarked,
                'post_is_liked': post_is_liked,
                'number_of_likes': number_of_likes,
                'recent_posts': Post.objects.exclude(id=post.id).order_by('-last_updated')[:3],
                'top_authors': User.objects.annotate(post_count=Count('post')).order_by('-post_count')[:5],
                'tags': Tag.objects.all(),
                'related_posts': Post.objects.exclude(id=post.id).filter(author=post.author)[:3]
            })

    if request.method == "POST":
        if "delete_comment" in request.POST:
            comment_id = request.POST.get("comment_id")
            try:
                comment = Comments.objects.get(id=comment_id, author=request.user)
                comment.delete()
                messages.success(request, "Коментар і всі його відповіді успішно видалено.")
            except Comments.DoesNotExist:
                messages.error(request, "Ви не можете видалити цей коментар.")
            return HttpResponseRedirect(reverse('post_page', args=[slug]))
    if 'viewed_posts' not in request.session:
        request.session['viewed_posts'] = []
    if post.id not in request.session['viewed_posts']:
        post.view_count = post.view_count + 1 if post.view_count else 1
        post.save(update_fields=['view_count'])
        request.session['viewed_posts'].append(post.id)
        request.session.modified = True

    context = {
        'post': post, 'form': form, 'comments': comments, 'is_bookmarked': is_bookmarked, 'post_is_liked': post_is_liked,
        'number_of_likes': number_of_likes, 'recent_posts': Post.objects.exclude(id=post.id).order_by('-last_updated')[:3],
        'top_authors': User.objects.annotate(post_count=Count('post')).order_by('-post_count')[:5],'tags': Tag.objects.all(),
        'related_posts': Post.objects.exclude(id=post.id).filter(author=post.author)[:3]
    }
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
            bio = form.cleaned_data.get('bio')
            profile_image = request.FILES.get('profile_image', None)

            if not profile_image:
                profile_image = None

            profile = Profile.objects.create(
                user=user,
                bio=bio,
                profile_image=profile_image
            )

            login(request, user)
            return redirect("/")
    context = {'form': form}
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
    paginator = Paginator(all_posts, 6)
    page = request.GET.get('page')
    try:
        all_posts = paginator.page(page)
    except PageNotAnInteger:
        all_posts = paginator.page(1)
    except EmptyPage:
        all_posts = paginator.page(paginator.num_pages)
    return render(request, 'app/all_posts.html', {'all_posts': all_posts})

@login_required
def user_posts(request):
    user_posts = Post.objects.filter(author=request.user)
    paginator = Paginator(user_posts, 6)
    page = request.GET.get('page')
    try:
        user_posts = paginator.page(page)
    except PageNotAnInteger:
        user_posts = paginator.page(1)
    except EmptyPage:
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
            post.author = request.user
            post.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('post_page', kwargs={'slug': post.slug}))
    else:
        form = PostForm()
    return render(request, 'app/add_post.html', {'form': form})

@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user == post.author:
        post.delete()
        return HttpResponseRedirect(reverse('index'))
    else:
        return HttpResponseRedirect(reverse('post_page', args=[str(slug)]))

def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    tag_posts = Post.objects.filter(tags=tag)
    paginator = Paginator(tag_posts, 6)
    page = request.GET.get('page')
    try:
        tag_posts = paginator.page(page)
    except PageNotAnInteger:
        tag_posts = paginator.page(1)
    except EmptyPage:
        tag_posts = paginator.page(paginator.num_pages)
    return render(request, 'app/tag_posts.html', {'tag_posts': tag_posts, 'tag': tag})

def dog_walking_map(request):
    return render(request, 'app/map.html')

@login_required
def list_dogs(request):
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
            dog.owner = request.user
            dog.save()
            if dog.birth_date:
                birthday_datetime = datetime.combine(dog.birth_date, time(10, 0))  # 10:00 ранку
                event = Event.objects.create(
                    name=f"День народження {dog.name}",
                    start=birthday_datetime,
                    end=birthday_datetime + timedelta(hours=1),
                    dog=dog,
                    repeat_interval='yearly',
                    series_id=uuid4(),
                    event_type='birthday'
                )
            return HttpResponseRedirect('my_dogs')
    else:
        form = DogForm()
    return render(request, 'app/add_dog.html', {'form': form})

@login_required
def edit_dog(request, pk):
    dog = get_object_or_404(Dog, pk=pk)
    old_birth_date = dog.birth_date

    if request.method == "POST":
        form = DogForm(request.POST, request.FILES, instance=dog)
        if form.is_valid():
            dog = form.save()

            if dog.birth_date != old_birth_date and dog.birth_date is not None:
                Event.objects.filter(
                    dog=dog,
                    event_type='birthday',
                    repeat_interval='yearly'
                ).delete()

                start = datetime.combine(dog.birth_date, time(10, 0))
                end = start + timedelta(hours=1)
                series_id = uuid4()

                for i in range(10):
                    Event.objects.create(
                        name=f"День народження {dog.name}",
                        start=start + relativedelta(years=i),
                        end=end + relativedelta(years=i),
                        dog=dog,
                        repeat_interval='yearly',
                        series_id=series_id,
                        event_type='birthday'
                    )

            return redirect('/my_dogs/')
    else:
        form = DogForm(instance=dog)

    return render(request, 'app/edit_dog.html', {'form': form, 'dog': dog})


@login_required
def delete_dog(request, pk):
    dog = get_object_or_404(Dog, pk=pk)

    if request.method == 'POST':
        dog_name = dog.name
        dog.delete()
        messages.success(request, f'Анкету собаки "{dog_name}" успішно видалено.')
        return redirect('/my_dogs/')

    return HttpResponseNotAllowed(['POST'])


@login_required
def user_calendar(request):
    user_dogs = Dog.objects.filter(owner=request.user).order_by('id')
    static_colors = ['#4cb4c7', '#598eeb', '#8e65f0', '#a24cc7', '#bfc74c', '#c79e4c', '#98c74c']
    dog_colors = {dog.id: static_colors[index % len(static_colors)] for index, dog in enumerate(user_dogs)}

    context = {
        "dogs": user_dogs,  # Усі собаки користувача
        "dog_colors": [{"name": dog.name, "color": dog_colors[dog.id]} for dog in user_dogs],
        "dog_color_map": dog_colors,
    }
    return render(request, 'app/user_calendar.html', context)


@login_required
def all_events(request):
    dog_id = request.GET.get("dog_id")
    event_type = request.GET.get("event_type")
    user_dogs = Dog.objects.filter(owner=request.user).order_by('id')
    static_colors = ['#4cb4c7', '#598eeb', '#8e65f0', '#a24cc7', '#bfc74c', '#c79e4c', '#98c74c']
    dog_colors = {dog.id: static_colors[index % len(static_colors)] for index, dog in enumerate(user_dogs)}  # Генеруємо кольори для кожної собаки

    all_events = Event.objects.filter(dog__owner=request.user)
    if dog_id:
        all_events = all_events.filter(dog_id=dog_id)
    if event_type:
        all_events = all_events.filter(event_type=event_type)

    out = []
    for event in all_events:
        out.append({
            'title': f"{event.name} - {event.get_event_type_display()} ({event.dog.name})",
            'id': event.id,
            'start': event.start.isoformat(),
            'end': event.end.isoformat(),
            'color': dog_colors[event.dog.id],
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
                Event.objects.filter(
                    series_id=event.series_id,
                    start__gte=event.start
                ).delete()
            else:
                event.delete()
            return redirect('/calendar/')
        except Event.DoesNotExist:
            return JsonResponse({'error': 'Подія не знайдена'}, status=404)
    return JsonResponse({'error': 'Недопустимий метод запиту'}, status=400)

@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.name = form.cleaned_data['name']
            event.event_type = form.cleaned_data['event_type']
            event.save()
            series_id = event.series_id
            repeat_interval = event.repeat_interval
            repeat_until = event.repeat_until
            if repeat_interval and repeat_interval != 'none' and repeat_until:
                start = event.start
                end = event.end
                for i in range(1, 12):
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

                    if start > repeat_until:
                        break

                    Event.objects.create(
                        name=event.name,
                        start=start,
                        end=end,
                        dog=event.dog,
                        repeat_interval=repeat_interval,
                        series_id=series_id,
                        event_type=event.event_type
                    )
            return redirect('/calendar/')
        else:
            return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = EventForm(user=request.user)
        return render(request, 'app/add_event.html', {'form': form})




@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Ваш профіль успішно оновлено!")

            if form.cleaned_data.get('new_password'):
                update_session_auth_hash(request, request.user)

            return redirect('author_page', slug=request.user.profile.slug)
    else:
        form = EditProfileForm(instance=profile, user=request.user)

    return render(request, 'app/edit_profile.html', {'form': form})

def all_tags(request):
    all_tags = Tag.objects.all()
    return render(request, 'app/all_tags.html', {'all_tags': all_tags})



def send_event_reminder(to_email, event, when_label):
    subject = f"🔔 {when_label.capitalize()} подія: {event.name}"

    html_content = render_to_string('app/email.html', {
        'user_name': event.dog.owner.first_name,
        'event_name': event.name,
        'event_type': event.get_event_type_display(),
        'dog_name': event.dog.name,
        'event_date': event.start.strftime('%d.%m.%Y'),
        'event_time': event.start.strftime('%H:%M'),
        'when_label': when_label,
        'calendar_url': 'http://localhost:8000/calendar/'
    })
    text_content = (
        f"Привіт, {event.dog.owner.first_name}!\n\n"
        f"Нагадуємо, що {when_label} відбудеться подія '{event.name}' "
        f"({event.get_event_type_display()}) для собаки {event.dog.name}.\n"
        f"Початок: {event.start.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"З найкращими побажаннями,\n"
        f"Любителі собак 🐾"
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[to_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
